import {
  useState,
  useEffect,
  useCallback,
  useRef,
  Component,
  type ErrorInfo,
  type ReactNode,
} from "react";
import {
  PanelSection,
  PanelSectionRow,
  ButtonItem,
  DropdownItem,
  TextField,
  staticClasses,
} from "@decky/ui";
import { definePlugin } from "@decky/api";
import { FaWifi } from "react-icons/fa";

import * as backend from "./backend";
import type {
  PluginStatus,
  MethodResult,
  OptimizeSafeResult,
  UpdateCheckResult,
  BadgeStatus,
  BackendSwitchStatus,
} from "./types";
import { ERROR_MESSAGES } from "./types";
import { InfoRow } from "./components/InfoRow";
import { StatsGrid } from "./components/StatsGrid";
import { Banner } from "./components/Banner";
import { BackendToggleRow } from "./components/BackendToggleRow";
import { UpdatesSection } from "./components/UpdatesSection";
import { PanelHeader } from "./components/PanelHeader";
import { PanelFooter } from "./components/PanelFooter";
import { ActionsSection } from "./components/ActionsSection";
import { theme } from "./theme";

const REFRESH_INTERVAL = 3000;
const RECONNECT_DELAY = 4000;
const BACKEND_POLL_INTERVAL = 750;
// Bounded backend-switch poll (D4): 40 ticks x 750ms = 30s. Past this an
// in_progress switch is parked as unknown (outcome unknowable, controls
// stay excluded) instead of spinning forever.
const BACKEND_POLL_MAX_TICKS = 40;
const UPDATE_CHECK_INTERVAL = 5 * 60 * 1000;
const UPDATE_CHECK_DEDUPE_MS = 60 * 1000;
const UPDATE_TIMEOUT_MS = 60 * 1000;

function getBadge(
  driftKey: string | undefined,
  status: PluginStatus | null,
  errorKey: string | null,
): { badge: BadgeStatus; text: string } | null {
  // Only surface a badge when it tells the user something the toggle position
  // doesn't - failure or drift between our setting and the system state.
  // Binary on/off badges are redundant with the toggle itself and are hidden.
  if (errorKey) return { badge: "error", text: "failed" };
  if (driftKey && status?.drift?.[driftKey]) return { badge: "drifted", text: "drifted" };
  return null;
}

const DNS_OPTIONS = [
  { data: "cloudflare", label: "Cloudflare (1.1.1.1)" },
  { data: "google", label: "Google (8.8.8.8)" },
  { data: "quad9", label: "Quad9 (9.9.9.9)" },
  { data: "custom", label: "Custom" },
];

// Catches render-time exceptions in the panel tree so a bad status shape or
// other unexpected error surfaces a recoverable message instead of Decky
// blanking the panel. The child tree is re-entered on next mount (panel
// reopen), so users can recover without a plugin restart.
class ErrorBoundary extends Component<
  { children: ReactNode },
  { err: Error | null }
> {
  state = { err: null as Error | null };

  static getDerivedStateFromError(err: Error) {
    return { err };
  }

  componentDidCatch(err: Error, info: ErrorInfo) {
    console.error("WiFi Optimizer TMS render error:", err, info);
  }

  render() {
    if (this.state.err) {
      return (
        <Banner variant="error">
          WiFi Optimizer TMS hit an unexpected error. Close and reopen the panel to
          recover. If it keeps happening, please report at
          github.com/undefined3491/wifi-optimizer-tms.
        </Banner>
      );
    }
    return this.props.children;
  }
}

// The single component that owns all panel state. It's intentionally flat:
// every section reads from shared state and state setters are passed down to
// leaf components. Organized top-to-bottom as:
//   1. State and refs
//   2. Stable callbacks (setBusy, runUpdateCheck, refreshStatus, poll helpers)
//   3. Lifecycle effects (main refresh, init, connectivity retry, update timeout,
//      update heartbeat)
//   4. User action handlers (toggles, optimize, reset, backend switch, updates)
//   5. Derived render state (connected, supportTier, allSafeActive, etc.)
//   6. JSX for the panel sections in top-to-bottom screen order
function Content() {
  // --- General status and toggle state ---
  const [status, setStatus] = useState<PluginStatus | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isBusy, setIsBusy] = useState(false);
  const [applyingAll, setApplyingAll] = useState(false);
  const [optimizeResult, setOptimizeResult] = useState<OptimizeSafeResult | null>(null);
  const [customDnsInput, setCustomDnsInput] = useState("");
  // DNS draft/applied split (ST0-012/015, D3): the provider dropdown and
  // the custom field edit the draft only. Applied values stay read-only
  // in status.settings.*. providerDraft null = follow applied.
  const [dnsProviderDraft, setDnsProviderDraft] = useState<string | null>(null);
  const [dnsAddressesDraft, setDnsAddressesDraft] = useState("");
  const [dnsDirty, setDnsDirty] = useState(false);
  const [dnsFocused, setDnsFocused] = useState(false);
  // Local empty-custom validation error. Rendered with the field mounted
  // so an error never hides the only way to fix it.
  const [dnsDraftError, setDnsDraftError] = useState<string | null>(null);
  // Visible action outcomes: rejections land in actionError; transfer
  // warnings, setter errors[] and reset errors[] land in actionWarnings.
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionWarnings, setActionWarnings] = useState<string[] | null>(null);
  // Status fetch health: last known status is kept and labeled stale
  // instead of being poisoned or presented as fresh.
  const [statusError, setStatusError] = useState<string | null>(null);
  const [isStale, setIsStale] = useState(false);
  const [statusAt, setStatusAt] = useState<number>(0);

  // --- Update flow state ---
  const [updateInfo, setUpdateInfo] = useState<UpdateCheckResult | null>(null);
  const [checkingUpdate, setCheckingUpdate] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  // --- Backend switch state ---
  const [backendSwitch, setBackendSwitch] = useState<BackendSwitchStatus | null>(null);

  // --- Refs ---
  // busyRef is the synchronous re-entrancy guard; isBusy (above) is the React
  // state mirror so UI can respond. setBusy below writes both together.
  const busyRef = useRef(false);
  const backendPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prevConnectedRef = useRef<boolean | null>(null);
  const statusRef = useRef<PluginStatus | null>(null);
  const lastUpdateCheckAtRef = useRef<number>(0);
  // Ref mirrors for the guarded DNS refresh (D3): refreshStatus is a
  // stable callback, so it reads these instead of closing over state.
  const dnsProviderDraftRef = useRef<string | null>(null);
  const dnsDirtyRef = useRef(false);
  const dnsFocusedRef = useRef(false);
  // Dismount safety (D5): set once on unmount; every async continuation
  // below returns early when set, so no timer or in-flight promise touches
  // state or IPC after dismount.
  const disposedRef = useRef(false);
  // Bounded poll lifecycle (D4): consecutive in_progress ticks, in-flight
  // overlap flag, and remaining reject-retry budget (one extra attempt).
  const backendPollTicksRef = useRef(0);
  const backendPollInFlightRef = useRef(false);
  const backendPollRetriesRef = useRef(0);

  const setBusy = useCallback((val: boolean) => {
    busyRef.current = val;
    setIsBusy(val);
  }, []);

  // Runs checkForUpdate with dedupe - skips if a check was issued within the
  // dedupe window. Lowers GitHub API pressure in CGNAT/dorm scenarios where
  // many devices share an IP. Manual button bypasses this (force=true).
  const runUpdateCheck = useCallback((force: boolean = false) => {
    const now = Date.now();
    if (!force && now - lastUpdateCheckAtRef.current < UPDATE_CHECK_DEDUPE_MS) {
      return;
    }
    lastUpdateCheckAtRef.current = now;
    backend.checkForUpdate().then((r) => {
      if (disposedRef.current) return;
      setUpdateInfo(r);
      if (r && !r.success) {
        setUpdateError(r.message ?? "Couldn't check for updates.");
      } else {
        setUpdateError(null);
      }
    }).catch(() => {
      if (disposedRef.current) return;
      setUpdateError("Couldn't check for updates.");
    });
  }, []);

  const refreshStatus = useCallback(async (force: boolean = false) => {
    // Background interval ticks defer while a user operation is in flight;
    // handler-driven refreshes (at the end of an op) force through so the UI
    // catches up immediately instead of waiting for the next interval tick.
    if (!force && busyRef.current) return;
    try {
      const s = await backend.getStatus();
      if (disposedRef.current) return;
      if (s && s.success !== false) {
        statusRef.current = s;
        setStatus(s);
        setStatusError(null);
        setIsStale(false);
        setStatusAt(Date.now());
        if (s.settings) {
          // Guarded refresh (D3): polling must never eat keystrokes. The
          // applied mirror updates only when no draft is pending, nothing
          // was typed, and the field isn't focused.
          if (!dnsDirtyRef.current && !dnsFocusedRef.current && dnsProviderDraftRef.current === null) {
            if (s.settings.dns_provider === "custom") {
              setCustomDnsInput(s.settings.dns_servers || "");
            }
          }
        }
      } else {
        // Resolved failure: keep last known status, label it stale.
        setStatusError(s?.message ?? "Couldn't load status.");
        if (statusRef.current) setIsStale(true);
      }
    } catch (e) {
      if (disposedRef.current) return;
      console.error("WiFi Optimizer TMS: failed to get status", e);
      setStatusError("Couldn't reach the plugin. It may still be loading.");
      if (statusRef.current) setIsStale(true);
    }
  }, []);

  const stopBackendPoll = () => {
    if (backendPollRef.current) {
      clearInterval(backendPollRef.current);
      backendPollRef.current = null;
    }
  };

  const beginBackendPoll = useCallback(() => {
    stopBackendPoll();
    backendPollTicksRef.current = 0;
    backendPollRetriesRef.current = 0;
    backendPollInFlightRef.current = false;
    backendPollRef.current = setInterval(async () => {
      // Overlap guard (D4): skip the tick when a poll is in flight.
      if (backendPollInFlightRef.current) return;
      backendPollInFlightRef.current = true;
      try {
        const s = await backend.getBackendSwitchStatus();
        if (disposedRef.current) return;
        // Any answered poll resets the reject-retry budget.
        backendPollRetriesRef.current = 0;
        if (s.in_progress) {
          backendPollTicksRef.current += 1;
          if (backendPollTicksRef.current >= BACKEND_POLL_MAX_TICKS) {
            // Tick bound (D4): stop spinning and park as unknown. The
            // phase/in_progress combo (switching phase, no poll in flight)
            // renders the row's unknown representation; the error preserves
            // the exclusion until a Retry reconciles.
            stopBackendPoll();
            await refreshStatus(true);
            if (disposedRef.current) return;
            setBackendSwitch({
              success: false,
              in_progress: false,
              phase: "switching",
              target: s.target ?? null,
              started_at: s.started_at ?? 0,
              result: null,
              error: "The backend switch is taking too long and its outcome is unknown. Retry the switch.",
            });
            setBusy(false);
            return;
          }
          // Mid-switch: update so the subtitle can show the current phase.
          setBackendSwitch(s);
          return;
        }
        // Terminal. Stop polling, then refresh status BEFORE flipping backend
        // state and clearing busy - this keeps the optimistic toggle position
        // steady until live.wifi_backend has caught up AND keeps other toggles
        // disabled until the whole UI has consistent state, avoiding any
        // toggle/untoggle flicker at the end of the switch.
        stopBackendPoll();
        if (s.result && !s.result.success && s.result.message) {
          const detail = s.result.detail ? ` (${s.result.detail})` : "";
          setErrors((prev) => ({
            ...prev,
            wifi_backend: s.result!.message! + detail,
          }));
        } else if (!s.result || s.result.success) {
          // Reconciliation (D4): a successful terminal status clears a
          // stale row error; replacing backendSwitch below clears the lock.
          setErrors((prev) => {
            const next = { ...prev };
            delete next.wifi_backend;
            return next;
          });
        }
        await refreshStatus(true);
        if (disposedRef.current) return;
        setBackendSwitch(s);
        setBusy(false);
      } catch (e) {
        if (disposedRef.current) return;
        // Bounded retry (D4): one extra attempt at the same interval, then
        // the existing error+lock.
        if (backendPollRetriesRef.current < 1) {
          backendPollRetriesRef.current += 1;
          return;
        }
        stopBackendPoll();
        setBusy(false);
        console.error("backend switch poll error", e);
        // Poll rejection: clear in-flight state but keep mutation controls
        // locked via an additive error until a Retry click or the next
        // successful getBackendSwitchStatus reconciles (no retry timers).
        setBackendSwitch((prev) => ({
          success: false,
          in_progress: false,
          phase: "failed",
          target: prev?.target ?? null,
          started_at: prev?.started_at ?? 0,
          result: prev?.result ?? null,
          error: "Lost contact with the backend switch. Reopen the panel or start a new switch.",
        }));
      } finally {
        backendPollInFlightRef.current = false;
      }
    }, BACKEND_POLL_INTERVAL);
  }, [refreshStatus, setBusy]);

  // Main refresh interval, paused when the panel is hidden so we don't burn
  // CPU/battery on ~12 subprocess calls every 3s in the background. On return
  // to visible, run one refresh immediately to catch anything that changed
  // while hidden, then resume the interval.
  useEffect(() => {
    let id: ReturnType<typeof setInterval> | null = null;
    const start = () => {
      if (id) return;
      refreshStatus();
      id = setInterval(refreshStatus, REFRESH_INTERVAL);
    };
    const stop = () => {
      if (id) {
        clearInterval(id);
        id = null;
      }
    };
    const onVis = () => {
      if (document.hidden) stop();
      else start();
    };
    if (!document.hidden) start();
    document.addEventListener("visibilitychange", onVis);
    return () => {
      document.removeEventListener("visibilitychange", onVis);
      stop();
    };
  }, [refreshStatus]);

  // One-time init: initial update check and resume backend polling if a switch
  // was already in flight when the panel opened.
  useEffect(() => {
    // Initial update check. If it fails (e.g., no network yet), the effect
    // below retries on connectivity recovery. QAM tends to cache the panel
    // across close/open, so we can't rely on remount to retry.
    runUpdateCheck();
    // Resume backend-switch polling if one is in flight (panel was reopened mid-switch)
    backend
      .getBackendSwitchStatus()
      .then((s) => {
        if (disposedRef.current) return;
        if (s.in_progress) {
          setBackendSwitch(s);
          setBusy(true);
          beginBackendPoll();
        } else {
          // Reconcile a prior poll-reject lock once the backend answers.
          setBackendSwitch((prev) => (prev?.error ? s : prev));
        }
      })
      .catch(() => {});
    return () => {
      stopBackendPoll();
    };
  }, [beginBackendPoll, runUpdateCheck, setBusy]);

  // Dismount safety (D5): flag every async continuation checks, and null
  // the poll ref via stopBackendPoll above, so a launch→dismount→fire
  // path performs zero IPC and zero setState.
  useEffect(() => {
    return () => {
      disposedRef.current = true;
    };
  }, []);

  // Retry update check when connectivity recovers. The initial one-shot check
  // in the mount effect misses the case where the panel was already open when
  // the network came back. Skip until status has loaded to avoid a spurious
  // null-to-true transition firing an extra check on every mount.
  useEffect(() => {
    if (!status) return;
    const connected = status.connected;
    const prev = prevConnectedRef.current;
    prevConnectedRef.current = connected;
    if (prev === false && connected === true) {
      runUpdateCheck();
    }
  }, [status?.connected, runUpdateCheck]);

  // Safety timeout: if an update was accepted but plugin_loader hasn't
  // killed us within 60s, the worker may have failed or the restart may
  // have stalled. The outcome is unknown — never reported as success.
  // Refresh first so a retry observes the job state (a still-running job
  // answers the retry with an in_progress rejection), then release busy.
  useEffect(() => {
    if (!updating) return;
    const id = setTimeout(() => {
      console.error("WiFi Optimizer TMS: update status unknown after 60s");
      (async () => {
        await refreshStatus(true);
        if (disposedRef.current) return;
        setBusy(false);
        setUpdating(false);
        setUpdateError(
          "Update status unknown — verify version after restart. If the version didn't change, retry the update."
        );
      })();
    }, UPDATE_TIMEOUT_MS);
    return () => clearTimeout(id);
  }, [updating, refreshStatus]);

  // Periodic update re-check - QAM often caches the panel across close/reopen,
  // so the mount-effect check doesn't re-fire. This heartbeat catches new
  // releases when the panel has been left open for a while. Paused when the
  // panel/tab is hidden to avoid pointless GitHub calls accumulating while the
  // user isn't looking; re-fires one check immediately on visibility return.
  useEffect(() => {
    let id: ReturnType<typeof setInterval> | null = null;
    const start = () => {
      if (id) return;
      id = setInterval(() => runUpdateCheck(), UPDATE_CHECK_INTERVAL);
    };
    const stop = () => {
      if (id) {
        clearInterval(id);
        id = null;
      }
    };
    const onVis = () => {
      if (document.hidden) {
        stop();
      } else {
        runUpdateCheck();
        start();
      }
    };
    if (!document.hidden) start();
    document.addEventListener("visibilitychange", onVis);
    return () => {
      document.removeEventListener("visibilitychange", onVis);
      stop();
    };
  }, [runUpdateCheck]);

  // Ref mirrors for the guarded DNS refresh (D3). refreshStatus reads
  // the refs so it stays a stable callback while drafts change.
  useEffect(() => {
    dnsProviderDraftRef.current = dnsProviderDraft;
  }, [dnsProviderDraft]);
  useEffect(() => {
    dnsDirtyRef.current = dnsDirty;
  }, [dnsDirty]);
  useEffect(() => {
    dnsFocusedRef.current = dnsFocused;
  }, [dnsFocused]);

  // ---- User action handlers ----
  //
  // Generic toggle handler used by every setter toggle (power_save, BSSID,
  // auto_fix, buffer_tuning, band_preference, DNS, IPv6) and by the Force
  // Reapply All button. Takes a key for error tracking and a backend fn.
  const handleToggle = async (key: string, fn: () => Promise<MethodResult>): Promise<MethodResult | null> => {
    if (busyRef.current) return null;
    setBusy(true);
    setActionError(null);
    setActionWarnings(null);
    setErrors((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    setOptimizeResult(null);

    try {
      const result = await fn();
      if (disposedRef.current) return null;
      if (!result.success) {
        const detail = result.detail ? ` (${result.detail})` : "";
        const msg = (result.message ?? ERROR_MESSAGES[result.error ?? ""] ?? "Unknown error") + detail;
        setErrors((prev) => ({ ...prev, [key]: msg }));
      }
      // Lossless results: transfer warnings, per-setter errors[] and an
      // unverified reconnect are bannered, never dropped.
      const warnings: string[] = [];
      if (result.transfer_warnings) warnings.push(...result.transfer_warnings);
      if (result.errors) warnings.push(...result.errors);
      const rc = result.reconnect;
      if (rc?.attempted && !rc.verified) {
        const failed = Object.entries(rc.stages ?? {})
          .filter(([, st]) => st && !st.ok)
          .map(([name]) => name);
        warnings.push(
          `WiFi reconnect not verified${failed.length ? ` (${failed.join(", ")})` : ""}. Settings were saved; toggle WiFi off/on if needed.`
        );
      }
      if (warnings.length) setActionWarnings(warnings);
      // Wait for WiFi to reconnect before refreshing status
      if (result.reconnected) {
        await new Promise((r) => setTimeout(r, RECONNECT_DELAY));
        if (disposedRef.current) return null;
      }
      return result;
    } catch (e) {
      if (disposedRef.current) return null;
      console.error(`WiFi Optimizer TMS: toggle ${key} failed`, e);
      setErrors((prev) => ({ ...prev, [key]: "Request failed. Please try again." }));
      return null;
    } finally {
      // Refresh before clearing busy so toggles/badges don't briefly flip to
      // stale pre-operation values in the interim render. Refresh runs even on
      // unexpected errors to keep UI consistent with backend state. Skipped
      // after dismount: zero IPC, zero setState (D5).
      if (!disposedRef.current) {
        await refreshStatus(true);
        setBusy(false);
      }
    }
  };

  const handleOptimize = async () => {
    if (busyRef.current) return;
    setBusy(true);
    setApplyingAll(true);
    setErrors({});
    setActionError(null);
    setActionWarnings(null);
    setOptimizeResult(null);
    try {
      const result = await backend.optimizeSafe();
      if (disposedRef.current) return;
      setOptimizeResult(result);
      if (result.results) {
        const newErrors: Record<string, string> = {};
        for (const [k, v] of Object.entries(result.results)) {
          if (!v.success) {
            const det = v.detail ? ` (${v.detail})` : "";
            newErrors[k] = (v.message ?? ERROR_MESSAGES[v.error ?? ""] ?? "Failed") + det;
          }
        }
        setErrors(newErrors);
      }
      // Lossless results (mirrors handleToggle/handleForceReapply):
      // transfer warnings, per-setter errors[] and an unverified
      // reconnect are bannered, never dropped.
      const optWarnings: string[] = [];
      for (const v of Object.values(result.results ?? {})) {
        if (v.transfer_warnings) optWarnings.push(...v.transfer_warnings);
        if (v.errors) optWarnings.push(...v.errors);
      }
      const optFailedStages: string[] = [];
      let optUnverified = false;
      for (const v of Object.values(result.results ?? {})) {
        const rc = v.reconnect;
        if (rc?.attempted && !rc.verified) {
          optUnverified = true;
          for (const [name, st] of Object.entries(rc.stages ?? {})) {
            if (st && !st.ok) optFailedStages.push(name);
          }
        }
      }
      if (optUnverified) {
        optWarnings.push(
          `WiFi reconnect not verified${optFailedStages.length ? ` (${optFailedStages.join(", ")})` : ""}. Settings were saved; toggle WiFi off/on if needed.`
        );
      }
      if (optWarnings.length) setActionWarnings(optWarnings);
      // optimize_safe contains BSSID lock which reconnects
      if (result.reconnected) {
        await new Promise((r) => setTimeout(r, RECONNECT_DELAY));
        if (disposedRef.current) return;
      }
    } catch (e) {
      if (disposedRef.current) return;
      console.error("optimize error", e);
      setActionError("Couldn't apply optimizations. Please try again.");
    } finally {
      // Refresh before clearing applyingAll so button doesn't briefly flip to
      // "All good" from stale status. Refresh runs on errors too. Skipped
      // after dismount (D5).
      if (!disposedRef.current) {
        await refreshStatus(true);
        setBusy(false);
        setApplyingAll(false);
      }
    }
  };

  // Shared aggregate ingestion for Force Reapply and Fix-now (D1): each
  // failed child maps to its existing errors[child] key, the shared banner
  // shows applied/total/failed, and total==0 renders the result message
  // ("No drifted settings" for repair, "No optimizations enabled" for
  // reapply). The old "reapply" error key is retired since no row renders it.
  const ingestAggregateResult = (result: OptimizeSafeResult) => {
    setOptimizeResult(result);
    const childKeys = Object.keys(result.results ?? {});
    const newErrors: Record<string, string> = {};
    for (const [k, v] of Object.entries(result.results ?? {})) {
      if (!v.success) {
        const det = v.detail ? ` (${v.detail})` : "";
        newErrors[k] = (v.message ?? ERROR_MESSAGES[v.error ?? ""] ?? "Failed") + det;
      }
    }
    setErrors((prev) => {
      const next = { ...prev };
      for (const k of childKeys) delete next[k];
      return { ...next, ...newErrors };
    });
    const warnings: string[] = [];
    for (const v of Object.values(result.results ?? {})) {
      if (v.transfer_warnings) warnings.push(...v.transfer_warnings);
      if (v.errors) warnings.push(...v.errors);
    }
    const failedStages: string[] = [];
    let anyUnverified = false;
    for (const v of Object.values(result.results ?? {})) {
      const rc = v.reconnect;
      if (rc?.attempted && !rc.verified) {
        anyUnverified = true;
        for (const [name, st] of Object.entries(rc.stages ?? {})) {
          if (st && !st.ok) failedStages.push(name);
        }
      }
    }
    if (anyUnverified) {
      warnings.push(
        `WiFi reconnect not verified${failedStages.length ? ` (${failedStages.join(", ")})` : ""}. Settings were saved; toggle WiFi off/on if needed.`
      );
    }
    if (warnings.length) setActionWarnings(warnings);
  };

  // Force Reapply has its own handler (not handleToggle): each failed
  // child maps to its existing errors[child] key, the shared banner shows
  // applied/total/failed, and total==0 renders as info.
  const handleForceReapply = async () => {
    if (busyRef.current) return;
    setBusy(true);
    setActionError(null);
    setActionWarnings(null);
    setOptimizeResult(null);
    try {
      const result = await backend.reapplyAll();
      if (disposedRef.current) return;
      ingestAggregateResult(result);
      if (result.reconnected) {
        await new Promise((r) => setTimeout(r, RECONNECT_DELAY));
        if (disposedRef.current) return;
      }
    } catch (e) {
      if (disposedRef.current) return;
      console.error("force reapply error", e);
      setActionError("Force reapply failed. Please try again.");
    } finally {
      if (!disposedRef.current) {
        await refreshStatus(true);
        setBusy(false);
      }
    }
  };

  // Fix-now repair (ST0-011, D1): re-applies only enabled-and-drifted
  // settings via repair_drifted. One busy window, child→errors[child]
  // mapping, a single RECONNECT_DELAY on result.reconnected, and a forced
  // refresh before busy-clear. A top-level rejection lands in the same
  // visible actionError as other aggregate handlers.
  const handleRepair = async () => {
    if (busyRef.current) return;
    setBusy(true);
    setActionError(null);
    setActionWarnings(null);
    setOptimizeResult(null);
    try {
      const result = await backend.repairDrifted();
      if (disposedRef.current) return;
      ingestAggregateResult(result);
      if (result.reconnected) {
        await new Promise((r) => setTimeout(r, RECONNECT_DELAY));
        if (disposedRef.current) return;
      }
    } catch (e) {
      if (disposedRef.current) return;
      console.error("repair drifted error", e);
      setActionError("Couldn't repair drifted settings. Please try again.");
    } finally {
      if (!disposedRef.current) {
        await refreshStatus(true);
        setBusy(false);
      }
    }
  };

  const handleResetSettings = async () => {
    if (busyRef.current) return;
    setBusy(true);
    setOptimizeResult(null);
    setErrors({});
    setActionError(null);
    setActionWarnings(null);
    try {
      const result = await backend.resetSettings();
      if (disposedRef.current) return;
      const errs = result.errors ?? [];
      if (errs.length) {
        // Non-empty errors[] (possibly with success False) is a warning,
        // not a rejection: defaults were applied with known gaps.
        setActionWarnings([...errs]);
      } else if (!result.success) {
        setActionError(result.message ?? "Reset failed. Please try again.");
      }
    } catch (e) {
      if (disposedRef.current) return;
      console.error("reset error", e);
      setActionError("Reset failed. Please try again.");
    } finally {
      if (!disposedRef.current) {
        await refreshStatus(true);
        setBusy(false);
      }
    }
  };

  // Drop all three DNS draft fields without IPC (D3 Cancel, and the
  // pre-toggle reset so the main on/off toggle never sends a raw draft).
  const dropDnsDraft = () => {
    setDnsProviderDraft(null);
    setDnsAddressesDraft("");
    setDnsDirty(false);
    setDnsDraftError(null);
  };

  // DNS Apply (D3): custom-only validation, then a single toggle. Presets
  // submit their stored servers; a stale draftAddresses is ignored for
  // non-custom. Success clears all three draft fields. Backend rejections
  // land in errors.dns via handleToggle (the last reporting line).
  const handleDnsApply = async () => {
    const applied = status?.settings;
    const provider = dnsProviderDraft ?? applied?.dns_provider ?? "cloudflare";
    if (provider === "custom" && !dnsAddressesDraft.trim()) {
      setDnsDraftError("Enter at least one DNS server address.");
      return;
    }
    setDnsDraftError(null);
    const servers = provider === "custom" ? dnsAddressesDraft : "";
    const r = await handleToggle("dns", () =>
      backend.setDns(true, provider, servers)
    );
    if (disposedRef.current) return;
    if (r?.success) {
      dropDnsDraft();
    }
  };

  const handleBackendToggle = async (on: boolean) => {
    // Re-entrancy guard: drop rapid clicks or clicks that land while another
    // operation is already running. Protects against duplicate backend calls
    // and the Force-Reapply/backend-switch overlap case.
    if (busyRef.current) return;
    const target = on ? "wpa_supplicant" : "iwd";
    setBusy(true);
    setErrors((prev) => {
      const next = { ...prev };
      delete next.wifi_backend;
      return next;
    });
    setOptimizeResult(null);

    try {
      const res = await backend.startBackendSwitch(target);
      if (disposedRef.current) return;
      if (!res.accepted) {
        setErrors((prev) => ({
          ...prev,
          wifi_backend: res.message ?? "Could not start backend switch",
        }));
        // Clear any stale result banner/inline from a prior switch so we don't
        // render old success + new error side-by-side.
        setBackendSwitch(null);
        setBusy(false);
        return;
      }
      setBackendSwitch({
        success: true,
        in_progress: true,
        phase: "switching",
        target,
        started_at: Math.floor(Date.now() / 1000),
        result: null,
      });
      beginBackendPoll();
    } catch (e) {
      if (disposedRef.current) return;
      setBusy(false);
      setErrors((prev) => ({
        ...prev,
        wifi_backend: "Failed to start backend switch",
      }));
      console.error("startBackendSwitch error", e);
    }
  };

  // Divergence retry (ST0-009 D7): re-run the switch toward the configured
  // backend; the gate accepts the same-target start as repair. Blocked
  // while a switch is in progress. Pre-start clearing of
  // wifi_backend/backendSwitch.error is shared with handleBackendToggle
  // (stale error cleared, fresh in-progress state replaces the lock).
  const handleBackendRetry = async (target: "iwd" | "wpa_supplicant") => {
    if (backendSwitch?.in_progress) return;
    await handleBackendToggle(target === "wpa_supplicant");
  };

  // Update-flow handlers, used by the top update banner and the Updates
  // section. Share the updating/updateError state so either surface can
  // initiate a check or apply an update. The backend accepts at most one
  // job: a rejection (in_progress, switch_in_progress, no_update,
  // no_release) means nothing launched, so the UI only reports it; an
  // accept holds busy until the restart kills the connection or the
  // safety timeout fires.
  const handleApplyUpdate = async () => {
    if (busyRef.current) return;
    setUpdateError(null);
    try {
      const r = await backend.applyUpdate();
      if (disposedRef.current) return;
      if (!r || !r.accepted) {
        setUpdateError(
          r?.message ?? "Update couldn't start. Please try again."
        );
        await refreshStatus(true);
        return;
      }
      setBusy(true);
      setUpdating(true);
    } catch {
      if (disposedRef.current) return;
      setUpdateError(
        "Update failed to start. Try again, or reinstall manually from Konsole."
      );
      await refreshStatus(true);
    }
  };

  const handleCheckForUpdate = async () => {
    setCheckingUpdate(true);
    setUpdateError(null);
    lastUpdateCheckAtRef.current = Date.now();
    try {
      const result = await backend.checkForUpdate();
      if (disposedRef.current) return;
      setUpdateInfo(result);
      if (result && !result.success) {
        setUpdateError(result.message ?? "Couldn't check for updates.");
      }
    } catch {
      if (disposedRef.current) return;
      setUpdateError("Couldn't check for updates.");
    }
    if (disposedRef.current) return;
    setCheckingUpdate(false);
  };

  // Don't render content until first status arrives (prevents disconnect flash).
  // A failed first load renders an error with retry instead of hanging blank.
  if (!status) {
    return (
      <>
        <PanelSection title="WiFi Optimizer TMS" />
        {statusError && (
          <>
            <Banner variant="error" icon="✕">
              {statusError}
            </Banner>
            <PanelSection>
              <PanelSectionRow>
                <ButtonItem layout="below" onClick={() => refreshStatus(true)}>
                  Retry
                </ButtonItem>
              </PanelSectionRow>
            </PanelSection>
          </>
        )}
      </>
    );
  }

  const s = status?.settings;
  const connected = status?.connected ?? false;
  const supportTier = status?.support_tier ?? 1;
  const driftCount = status?.drift ? Object.keys(status.drift).length : 0;
  const unknownOwners = status?.unknown_owners ?? [];
  const isDeckLcd = s?.device_family === "deck_lcd";
  // Mutation lock: normal busy state plus a stuck backend-switch poll
  // failure (backendSwitch.error), which holds controls until a Retry click
  // or the next successful getBackendSwitchStatus reconciles. No retry timers.
  const mutationLocked = isBusy || backendSwitch?.error != null;
  // Retry affordance (D4): the error lock never deadlocks its own retry,
  // while busy/in-flight work still blocks everything else.
  const canRetry =
    backendSwitch?.error != null &&
    !backendSwitch?.in_progress &&
    !isBusy;
  // Update/switch mutual exclusion (D7): Update Now is disabled while a
  // backend switch is in flight or other work holds busy; the backend
  // toggle is already disabled while updating via mutationLocked/isBusy,
  // which handleApplyUpdate sets on an accepted start.
  const updateApplyDisabled =
    (backendSwitch?.in_progress ?? false) || isBusy;

  // Check if all safe optimizations are already active
  const allSafeActive =
    connected &&
    status?.live?.power_save_off &&
    !status?.drift?.power_save &&
    s?.bssid_lock_enabled &&
    !status?.drift?.bssid_lock &&
    status?.live?.dispatcher_installed &&
    status?.live?.buffer_tuning_applied &&
    !status?.drift?.buffer_tuning;

  return (
    <>
      <PanelHeader
        driver={s?.driver ?? ""}
        version={status?.version ?? "?"}
        lastApplied={s?.last_applied ?? 0}
        lastEnforced={status?.live?.last_enforced}
        deviceLabel={s?.device_label !== "Unknown Device"
          ? `${s?.device_label} - ${s?.chip_label}`
          : s?.chip_label && s.chip_label !== "unknown"
            ? s.chip_label
            : undefined}
      />

      {/* Unknown hardware info */}
      {supportTier === 3 && (
        <Banner variant="info">
          Unknown WiFi hardware detected. Some optimizations may not apply.
        </Banner>
      )}

      {/* Update available */}
      {updateInfo?.update_available && !updating && (
        <PanelSection>
          <PanelSectionRow>
            <ButtonItem layout="below" disabled={updateApplyDisabled} onClick={handleApplyUpdate}>
              Update to v{updateInfo.latest_version}
            </ButtonItem>
          </PanelSectionRow>
        </PanelSection>
      )}

      {/* Updating */}
      {updating && (
        <PanelSection>
          <PanelSectionRow>
            <div style={{ fontSize: theme.fontSize.body, color: theme.info.text }}>
              Updating... plugin will restart momentarily.
            </div>
          </PanelSectionRow>
        </PanelSection>
      )}

      {/* First-run prompt */}
      {connected && !s?.last_applied && (
        <Banner variant="info">
          Tap <strong>Optimize Safe</strong> to get started.
        </Banner>
      )}

      {/* Drift alert */}
      {connected && !!s?.last_applied && driftCount > 0 && (
        <Banner variant="warning" icon="⚠">
          {driftCount} setting{driftCount > 1 ? "s" : ""} drifted after wake.{" "}
          <span
            style={{ textDecoration: "underline", cursor: "pointer" }}
            onClick={handleRepair}
          >
            Fix now
          </span>
        </Banner>
      )}

      {/* Disconnected banner */}
      {!connected && (
        <Banner variant="error" icon="✕">
          Not connected to WiFi. Connect first, then optimize.
        </Banner>
      )}

      {/* Rejected operations */}
      {actionError && (
        <Banner variant="error" icon="✕">
          {actionError}
        </Banner>
      )}

      {/* Transfer warnings and setter/reset errors[] */}
      {actionWarnings && actionWarnings.length > 0 && (
        <Banner variant="warning" icon="⚠">
          {actionWarnings.map((w, i) => (
            <span key={i}>
              {w}
              {i < actionWarnings.length - 1 && <br />}
            </span>
          ))}
        </Banner>
      )}

      {/* Settings that lost track of their network profile */}
      {unknownOwners.length > 0 && (
        <Banner variant="warning" icon="⚠">
          {unknownOwners.length} setting{unknownOwners.length > 1 ? "s" : ""}{" "}
          lost track of {unknownOwners.length > 1 ? "their" : "its"} network
          ({unknownOwners.join(", ")}). Re-apply on the desired network.
        </Banner>
      )}

      {/* Stale status: last known data with timestamp, never fake-fresh */}
      {isStale && (
        <Banner variant="warning" icon="⚠">
          Showing last known status
          {statusAt ? ` from ${new Date(statusAt).toLocaleTimeString()}` : ""}
          {" "}— refresh failed{statusError ? `: ${statusError}` : ""}.{" "}
          <span
            style={{ textDecoration: "underline", cursor: "pointer" }}
            onClick={() => refreshStatus(true)}
          >
            Retry now
          </span>
        </Banner>
      )}

      {/* Backend switch result banner */}
      {backendSwitch && !backendSwitch.in_progress && backendSwitch.result && (() => {
        const r = backendSwitch.result;
        // Treat reconnect timeout as a warning even when the backend-level
        // switch succeeded - the system is switched but WiFi didn't come back.
        const isWarning = !r.success || r.needs_reboot || r.reconnect_timed_out;
        let text: string;
        if (r.needs_reboot) {
          text = `Backend switched to ${r.target}, but wlan0 didn't come back - reboot required`;
        } else if (!r.success) {
          text = r.message ?? "Backend switch failed";
        } else {
          const parts = [`Switched to ${r.backend}`];
          if (r.recovery_performed) parts.push("recreated wlan0 interface");
          if (r.reconnect_timed_out) parts.push("WiFi didn't reconnect");
          text = parts.join(" · ");
        }
        return (
          <Banner variant={isWarning ? "warning" : "success"} icon={isWarning ? "⚠" : "✓"}>
            {text}
          </Banner>
        );
      })()}

      {/* Optimize result banner */}
      {optimizeResult && (() => {
        const failed = optimizeResult.total - optimizeResult.applied;
        const variant =
          optimizeResult.total === 0
            ? "info"
            : failed > 0
              ? "warning"
              : "success";
        const text =
          optimizeResult.total === 0
            ? (optimizeResult.message ?? "No optimizations enabled")
            : failed > 0
              ? `${optimizeResult.applied}/${optimizeResult.total} applied (${failed} failed)`
              : "All applied";
        return <Banner variant={variant}>{text}</Banner>;
      })()}

      {/* Optimize button */}
      <PanelSection>
        <PanelSectionRow>
          <ButtonItem
            layout="below"
            disabled={!connected || applyingAll || mutationLocked}
            onClick={handleOptimize}
          >
            {applyingAll
              ? "Applying..."
              : allSafeActive
                ? "All good"
                : "Optimize Safe"}
          </ButtonItem>
        </PanelSectionRow>
      </PanelSection>

      {/* Power & stability */}
      <PanelSection title="Power & stability">
        <InfoRow
          label="Prevent lag spikes"
          subtitle="Disables WiFi power save and PCIe power states"
          explanation="The OS enables WiFi power saving at multiple levels - the wireless chip, the PCIe bus connecting it to the CPU, and driver-level low power modes. These cause latency spikes, packet batching, and throughput degradation during sustained streaming. This toggle disables all of them, keeping the WiFi hardware fully awake. Battery impact is minimal."
          {...getBadge("power_save", status, errors.power_save ?? null)}
          checked={s?.power_save_disabled ?? false}
          disabled={mutationLocked}
          error={errors.power_save}
          onChange={(val: boolean) =>
            handleToggle("power_save", () => backend.setPowerSave(val))
          }
        />
        <InfoRow
          label="Stop background scanning"
          subtitle="Locks to current AP - disable to switch networks or roam"
          explanation="Your device scans for other WiFi networks every few minutes even while connected. Each scan causes a brief interruption that can drop packets and stutter game streaming. Locking to your current access point stops these scans entirely. You'll need to disable this before switching to a different network or access point."
          {...getBadge("bssid_lock", status, errors.bssid_lock ?? null)}
          checked={s?.bssid_lock_enabled ?? false}
          disabled={mutationLocked || (!connected && !s?.bssid_lock_enabled)}
          error={errors.bssid_lock}
          onChange={(val: boolean) =>
            handleToggle("bssid_lock", () => backend.setBssidLock(val))
          }
        />
        <InfoRow
          label="Auto-fix on wake"
          subtitle="Reapplies settings after sleep (NM dispatcher)"
          explanation="The OS often resets WiFi settings after sleep or updates. This installs a small script that automatically re-applies your optimizations every time the WiFi reconnects. It runs outside of Decky, so it works even if Decky has issues. Removing the plugin will also remove this script."
          {...getBadge(undefined, status, errors.auto_fix ?? null)}
          checked={s?.auto_fix_on_wake ?? false}
          disabled={mutationLocked}
          error={errors.auto_fix}
          onChange={(val: boolean) =>
            handleToggle("auto_fix", () => backend.setAutoFix(val))
          }
        />
        <InfoRow
          label="Network buffer tuning"
          subtitle="Optimize UDP buffers and TX queue for streaming"
          explanation="Increases kernel network buffer sizes and transmit queue length to handle the bursty UDP traffic that game streaming produces. Without this, packets can be dropped during high-bitrate moments, causing frame drops or brief quality dips. These settings benefit all network interfaces, including ethernet. They reset on every reboot."
          {...getBadge("buffer_tuning", status, errors.buffer_tuning ?? null)}
          checked={s?.buffer_tuning_enabled ?? false}
          disabled={mutationLocked}
          error={errors.buffer_tuning}
          onChange={(val: boolean) =>
            handleToggle("buffer_tuning", () => backend.setBufferTuning(val))
          }
        />
      </PanelSection>

      {/* Advanced */}
      <PanelSection title="Advanced">
        <InfoRow
          label="Force 5 GHz band"
          subtitle='Lock this profile to 5 GHz (NM band "a")'
          explanation={`Sets NetworkManager 802-11-wireless.band to "a" on this saved profile. "a" means 5 GHz only — it will not use 2.4 GHz or 6 GHz for this network. Bluetooth operates on the 2.4 GHz band${
            isDeckLcd ? ", and on the Steam Deck LCD the antennas are shared" : ""
          }. Using 5 GHz for WiFi avoids this interference entirely, giving you a cleaner, faster connection. Only enable this if your router supports 5 GHz. If your network is 2.4 GHz only, this will prevent you from connecting. 6 GHz ("6GHz") is a separate NM value and is not offered here.`}
          {...getBadge("band_preference", status, errors.band_preference ?? null)}
          checked={s?.band_preference_enabled ?? false}
          disabled={mutationLocked || (!connected && !s?.band_preference_enabled)}
          error={errors.band_preference}
          onChange={(val: boolean) =>
            handleToggle("band_preference", () =>
              backend.setBandPreference(val, s?.band_preference ?? "a")
            )
          }
        />
        <InfoRow
          label="Custom DNS"
          subtitle="Override DNS servers for this network"
          explanation="Your internet provider's DNS servers translate domain names into IP addresses. They can be slow or unreliable. Switching to a public DNS like Cloudflare (1.1.1.1) or Google (8.8.8.8) can speed up initial connections and improve reliability. This only affects the current WiFi network."
          {...getBadge("dns", status, errors.dns ?? null)}
          checked={s?.dns_enabled ?? false}
          disabled={mutationLocked || (!connected && !s?.dns_enabled)}
          error={errors.dns}
          onChange={(val: boolean) => {
            // Main toggle uses applied values and drops pending drafts,
            // never the raw draft (D3).
            const ap = s?.dns_provider ?? "cloudflare";
            const as = s?.dns_servers ?? "";
            dropDnsDraft();
            handleToggle("dns", () => backend.setDns(val, ap, as));
          }}
        >
          {s?.dns_enabled && (
            <>
              <PanelSectionRow>
                <DropdownItem
                  label="DNS Provider"
                  rgOptions={DNS_OPTIONS}
                  selectedOption={dnsProviderDraft ?? s?.dns_provider ?? "cloudflare"}
                  disabled={mutationLocked}
                  onChange={(option: { data: string }) => {
                    // Draft only: never submits (D3). Switching to Custom
                    // mounts the field prefilled from applied servers.
                    setDnsDraftError(null);
                    setDnsProviderDraft(option.data);
                    if (option.data === "custom") {
                      setDnsAddressesDraft(customDnsInput || s?.dns_servers || "");
                    }
                    setDnsDirty(false);
                  }}
                />
              </PanelSectionRow>
              {(dnsProviderDraft ?? s?.dns_provider) === "custom" && (
                <PanelSectionRow>
                  <TextField
                    label="DNS servers (space-separated)"
                    value={dnsProviderDraft !== null ? dnsAddressesDraft : customDnsInput}
                    disabled={mutationLocked}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                      // Typing adopts/updates the draft and marks it dirty;
                      // never submits (D3).
                      if (dnsProviderDraft === null) setDnsProviderDraft("custom");
                      setDnsAddressesDraft(e.target.value);
                      setDnsDirty(true);
                    }}
                    onFocus={() => setDnsFocused(true)}
                    onBlur={() => setDnsFocused(false)}
                  />
                </PanelSectionRow>
              )}
              {dnsDraftError && (
                <PanelSectionRow>
                  <div style={{ fontSize: theme.fontSize.small, color: theme.error.text }}>
                    {dnsDraftError}
                  </div>
                </PanelSectionRow>
              )}
              {dnsProviderDraft !== null && (
                <PanelSectionRow>
                  <ButtonItem
                    layout="below"
                    disabled={mutationLocked}
                    onClick={handleDnsApply}
                  >
                    Apply DNS
                  </ButtonItem>
                </PanelSectionRow>
              )}
              {dnsProviderDraft !== null && (
                <PanelSectionRow>
                  <ButtonItem
                    layout="below"
                    disabled={mutationLocked}
                    onClick={dropDnsDraft}
                  >
                    Cancel
                  </ButtonItem>
                </PanelSectionRow>
              )}
            </>
          )}
        </InfoRow>
        <InfoRow
          label="Disable IPv6"
          subtitle="Use IPv4 only on this network"
          explanation="Some networks have poor or misconfigured IPv6 support, which can cause slow DNS resolution, connection timeouts, or routing issues. Disabling IPv6 forces all traffic through IPv4. Only enable this if you're experiencing issues - most modern networks handle IPv6 fine."
          {...getBadge("ipv6", status, errors.ipv6 ?? null)}
          checked={s?.ipv6_disabled ?? false}
          disabled={mutationLocked || (!connected && !s?.ipv6_disabled)}
          error={errors.ipv6}
          onChange={(val: boolean) =>
            handleToggle("ipv6", () => backend.setIpv6(val))
          }
        />
        <InfoRow
          label="Traffic shaping (CAKE)"
          subtitle="Fair queuing and bufferbloat prevention"
          explanation='Replaces the egress qdisc on this device with CAKE "unlimited diffserv4 nat ack-filter" (no bandwidth limit set). It only orders packets leaving this device; it cannot control other devices, the access point, or the ISP bottleneck, and any effect needs measurement under load. Resets on reboot and is reapplied automatically if auto-fix on wake is enabled.'
          {...getBadge("cake", status, errors.cake ?? null)}
          checked={s?.cake_enabled ?? false}
          disabled={mutationLocked || (!connected && !s?.cake_enabled)}
          error={errors.cake}
          onChange={(val: boolean) =>
            handleToggle("cake", () => backend.setCake(val))
          }
        />
        {status?.live?.backend_tool_available && (
          <BackendToggleRow
            status={status}
            backendSwitch={backendSwitch}
            error={errors.wifi_backend ?? backendSwitch?.error}
            isBusy={mutationLocked}
            canRetry={canRetry}
            onToggle={handleBackendToggle}
            onRetry={handleBackendRetry}
          />
        )}
      </PanelSection>

      {/* Live status */}
      <PanelSection title="Live status">
        {connected && status?.live?.ip_address && (
          <PanelSectionRow>
            <div style={{ fontSize: theme.fontSize.tiny, color: theme.text.tertiary }}>
              IP: {status.live.ip_address}
            </div>
          </PanelSectionRow>
        )}
        <PanelSectionRow>
          <StatsGrid live={status?.live ?? {}} connected={connected} />
        </PanelSectionRow>
      </PanelSection>

      <ActionsSection
        connected={connected}
        isBusy={mutationLocked}
        onForceReapply={handleForceReapply}
        onReset={handleResetSettings}
      />

      <UpdatesSection
        updating={updating}
        checkingUpdate={checkingUpdate}
        updateInfo={updateInfo}
        updateError={updateError}
        applyDisabled={updateApplyDisabled}
        onApply={handleApplyUpdate}
        onCheck={handleCheckForUpdate}
      />

      <PanelFooter version={status?.version ?? "?"} />
    </>
  );
}

export default definePlugin(() => {
  let gameLifetimeUnsub: { unregister(): void } | null = null;
  // Reapply timer id + disposed flag (D5): no volatile reapply or state
  // touch after dismount.
  let reapplyTimer: ReturnType<typeof setTimeout> | null = null;
  let reapplyDisposed = false;

  try {
    gameLifetimeUnsub = SteamClient.GameSessions.RegisterForAppLifetimeNotifications(
      (notification: { bRunning: boolean }) => {
        if (notification.bRunning) {
          reapplyTimer = setTimeout(() => {
            if (reapplyDisposed) return;
            backend.reapplyVolatile().catch(() => {});
          }, 3000);
        }
      },
    );
  } catch (e) {
    console.error("WiFi Optimizer TMS: failed to register game launch listener", e);
  }

  return {
    name: "WiFi Optimizer TMS",
    titleView: <div className={staticClasses.Title}>WiFi Optimizer TMS</div>,
    content: (
      <ErrorBoundary>
        <Content />
      </ErrorBoundary>
    ),
    icon: <FaWifi />,
    onDismount() {
      reapplyDisposed = true;
      if (reapplyTimer) {
        clearTimeout(reapplyTimer);
        reapplyTimer = null;
      }
      gameLifetimeUnsub?.unregister();
    },
  };
});

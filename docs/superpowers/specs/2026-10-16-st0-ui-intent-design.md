# ST0-011/012/013/015/020 — Repair flow, DNS draft, poll lifecycle — design

Date: 2026-10-16. Baseline: `674820b` (= `c86c486` + package E), version `0.11.6`.
Scope: findings `ST0-011`, `ST0-012`, `ST0-013` (residual: bounded retry,
mount-independent reconciliation, retry deadlock, poll bounds, overlap guard —
reject/error-lock already done in packages B/C), `ST0-015`, `ST0-020`
(`docs/audits/2026-10-15-stage-0-findings.md`). Stage 0 stays open; no Stable,
no version bump, no Watchdog. Delivery (001/002/003/018) stays separate.

## Intent

- "Fix now" repairs what drifted — never enables what the user left disabled,
  never reconnects for healthy profiles.
- Custom DNS is editable: select, type, validate, Apply/Cancel. Polling never
  eats keystrokes; leaving the field never submits.
- A failed backend poll retries boundedly, then locks with a working retry
  action — never a dead button, never an infinite spinner.
- No timer or in-flight promise touches state or IPC after dismount.

## Non-goals / anti-goals

- No `"6GHz"` support; no v2 reconnect coalescing (documented path only).
- No backend DNS format validation beyond today's non-empty check (local
  pre-check is emptiness only).
- No ST0-003 job machinery / retry timers beyond the bounded poll retry.

## Decisions (binding)

- **D1 — `repair_drifted()` (ST0-011, option b).** New `Plugin` method +
  `export const repairDrifted = callable<[], OptimizeSafeResult>("repair_drifted")`
  in `src/backend.ts` (names match exactly). Zero args in v1. Same result shape
  as `reapply_all`. Result rendering: the aggregate banner is message-aware —
  `total==0` renders exactly `"No drifted settings"` (distinct from reapply's
  `"No optimizations enabled"`), failures/banners reuse the Force-Reapply
  outcome surface, and a top-level rejection lands in the same visible
  `actionError` as other aggregate handlers. Selection (backend, fresh live read with the exact `get_status`
  formulas): re-apply `set_*(True)` iff flag enabled AND drifted now. `auto_fix`
  (no drift key), `dns` (no detection yet — see D2), and `backend` (separate
  switch/repair flow; diverged backend leads to the existing backend retry, not
  a repair error) are excluded and documented. Order and aggregation mirror
  `reapply_all`; `total==0` → `{success: True, total: 0, applied: 0, results: {},
  message: "No drifted settings"}`. Per-child `unknown_owner` fails that child
  only. Top `success = all(children.success)`. `optimize_safe` stays for
  first-run; the drift banner switches `onClick` from `handleOptimize` to a new
  `handleRepair` (one `busy` window, child→`errors[child]` mapping, single
  `RECONNECT_DELAY` on `result.reconnected`, forced refresh before busy-clear).
- **D2 — `drift.dns` detection.** `get_status` sets `drift.dns` iff connected AND
  `dns_enabled` AND the parsed live-DNS IP set lacks any expected server.
  Parsing: live `IP4.DNS` device output (`"IP4.DNS[1]:addr"` multiline) →
  strip index prefixes and whitespace → set of IPs; expected = split of
  `dns_servers` setting; drift iff NOT expected ⊆ live. The formula lives in the
  Task-2 shared helper (no duplication), selection is read-only (shared
  formulas only — never `get_status()` itself, which has mutating paths; pinned
  by a `save_count==0` + zero-`_nmcli_modify` selection test). The DNS row badge
  switches to `getBadge("dns", ...)` (Task 3) so the key renders. Repair covers
  DNS automatically once detected, with no signature change.
- **D3 — DNS draft/applied split (ST0-012/015).** New local state:
  `dnsProviderDraft: string | null` (`null` = follow applied),
  `dnsAddressesDraft: string`, `dnsDirty: boolean`, `dnsFocused: boolean`.
  Applied stays `status.settings.*` (read-only). Dropdown change only sets the
  draft (montuje pole z applied servers, nie pustym); typing sets draft+dirty,
  never submits; blur never submits; Apply validates non-empty-after-trim ONLY
  when `draftProvider==="custom"` (presets submit their stored servers; stale
  `draftAddresses` ignored for non-custom) then one `handleToggle("dns",
  setDns(true, draftProvider, draftProvider==="custom" ? draftAddresses : ""))`,
  success clears all three draft fields (`providerDraft=null`, addresses reset,
  `dirty=false`); Cancel drops all three without IPC. Refresh overwrites
  the draft only when `!dirty && !focused && providerDraft===null`. Main
  on/off toggle uses applied (or post-commit) values and drops pending drafts,
  never the raw draft. Local
  empty-custom error renders with the field mounted (breaks the error/no-field
  loop). Draft controls respect `mutationLocked`; backend `catch` stays the last
  reporting line.
- **D4 — bounded poll retry + reconciliation (ST0-013 residual).** `beginBackendPoll`:
  one bounded retry (1 extra attempt at the same interval), then the existing
  `error`+lock. Retry affordance: `canRetry = backendSwitch.error != null &&
  !backendSwitch.in_progress && !isBusy` — a dedicated prop on `BackendToggleRow`
  (new `canRetry` prop; button enabled by it, not by `mutationLocked`), so the
  error lock never deadlocks its own retry while `busy`/in-flight work still
  blocks everything else (ST0-003 exclusion untouched). Clicking Retry (or the
  next successful `getBackendSwitchStatus`) reconciles/clears the error —
  reconciliation no longer mount-only. `in_progress` gets a tick bound (max
  ticks → `unknown` state with preserved exclusion). Poll ticks get an overlap
  guard (skip when a poll is in flight).
- **D5 — dismount safety (ST0-020).** `reapplyTimer` id + `disposed` flag beside
  the lifetime subscription; callback returns early when disposed; `onDismount`
  sets disposed + `clearTimeout`. A `disposedRef` in `Content` is checked after
  every await in the backend poll, `RECONNECT_DELAY` waits, and
  `runUpdateCheck` continuations; poll cleanup nulls `backendPollRef`; `PanelFooter`
  stores its timeout ids in a ref with unmount `clearTimeout`. `refreshStatus`
  continuations also check `disposedRef` after their await (in-flight status
  poll after dismount). Launch→dismount→advance-time performs zero IPC and zero
  `setState`.

## Acceptance

- Fix-now with only band drifted: BSSID/power/buffers/dispatcher untouched, no
  radio cycle for healthy profiles; backend-only drift → `total: 0` + backend
  retry path.
- Fresh Custom flow: select mounts a prefilled field, typing survives polls,
  blur submits nothing, empty Apply errors locally, Cancel is IPC-free, toggle
  on/off never sends a raw draft.
- Failed poll: one retry, then locked error with a working Retry; infinite
  `in_progress` becomes `unknown`; overlapping ticks impossible.
- Launch→dismount→timer-fire: zero IPC, zero state writes (review-verified
  against the D5 checklist + `tsc` + build; no unit harness exists for timers).

# Stage 0 — Static audit findings

Date: 2026-10-15. Audited product commit: `e957c5b49797ef456cbd8edf093eb83704aac805`, version `0.11.6`. Roadmap commit `7b58d47` and this audit documentation do not change that product code.

**Static review completed; Stage 0 remains open.** Three independent owner-selected `gpt-6.1-sol` reviewers inspected backend state/restoration, installation/update/delivery, and frontend/IPC. The coordinator inspected platform documentation, checked findings against source, calibrated/deduplicated them and assembled this report. No plugin runtime, installer, dispatcher, network setting, device operation or exploit was executed on Windows.

The baseline report recorded **14 Important and 9 Minor findings**, with **no Critical finding established by this review**. Subsequent correction evidence is tracked below; the baseline traces and line numbers remain historical. This is not a guarantee that no additional defect exists. Important findings block the first fork Stable release under the Stage 0 criteria. Dependency database scores and unverified security scenarios are distinguished from demonstrated plugin impact.

## Correction progress — 2026-10-16

- **ST0-010: corrected in source, isolated regression verified.** Switch entry reserves before its first await; an unlaunched exit restores the previous state and closes any unlaunched coroutine. Successful task creation transfers completion ownership to the existing worker. Nine isolated tests cover both routes, overlap, rejection, cancellation, failures and retry; they failed on the baseline defect and pass with the correction. Independent `gpt-6.1-sol` review found no blockers. See the [scoped plan and verification record](../superpowers/plans/2026-10-16-stage-0-backend-reservation.md). This resolves the entry reservation race, not effective-backend detection, worker/thread cancellation or updater exclusion. No live competing switches were attempted; corrected-candidate device validation remains pending.
- **ST0-005/006: corrected in source, isolated regression verified (this branch).**
  `get_status()` is read-only (no settings writes, no NM profile or priority
  mutations; drift stays boolean reports plus additive `unknown_owners`
  `bssid_lock`/`band_preference`/`dns`/`ipv6`). BSSID/band/DNS/IPv6 carry explicit
  owner UUIDs recorded only on verified explicit success; disablers resolve the
  owner offline and never touch a foreign active profile; legacy enabled-without-owner
  splits into enable→`unknown_owner` vs disable→intent-only clear; failed `nmcli`
  retains ownership for retry (`nmcli_failed`, `dns_partial`, `relock_failed`). No
  `autoconnect-priority 100` on any path; pre-existing `100`s untouched for
  ST0-004/016. Sixteen isolated tests (red→green) in `tests/test_profile_ownership.py`;
  full suite 59 tests OK (3 Windows inventory skips, Git Bash on PATH). Independent
  review + scoped re-review clean. See the [design](../superpowers/specs/2026-10-16-st0-005-006-profile-ownership-design.md)
  and [plan](../superpowers/plans/2026-10-16-st0-005-006-profile-ownership.md).
  Corrected-candidate device validation remains pending.
- **ST0-004/016: corrected in source, isolated regression verified (this branch).**
  First mutation of each domain captures the prior value into
  `SETTINGS_DIR/system_snapshot.json` (separate file, atomic, slot-once, never
  in `settings.json`); disablers restore only owned domains with logged
  assumed-default fallback; qdisc restores via del-vs-replace with accepted
  fidelity limits; transfer-clear consults the snapshot. `reset_settings()` is a
  full reconciliation to saved defaults (live `iw` off + NM conf written,
  dispatcher installed, owned profiles cleared before wipe with single
  conditional reconnect, timestamped save, backend out of scope); `_uninstall`
  restores the same plus dispatcher/files/snapshot removal, without service
  restoration. Pre-existing `priority 100`s and pre-plugin baselines untouched
  and disclosed. Twelve isolated tests (red→green) in `tests/test_restoration.py`;
  full suite 71 tests OK (3 Windows inventory skips, Git Bash on PATH).
  Independent review + scoped re-review clean. See the [design](../superpowers/specs/2026-10-16-st0-004-016-restoration-design.md)
  and [plan](../superpowers/plans/2026-10-16-st0-004-016-restoration.md).
  Corrected-candidate device validation remains pending.
- **ST0-007/008/014/017/019 (+013 reject path): corrected in source, isolated
  regression verified (this branch).** `_hard_reconnect` returns per-stage results
  with `verified` (≤2 checks, ≈5s budget, dead-radio signal); `reconnected: True`
  only when verified, aggregates computed from children (top `success: False` on
  any child failure); failed writes block intent with named errors
  (`sysctl/txqueuelen/qdisc/dispatcher/modprobe/sysfs/pcie/nm_conf_failed`,
  idempotent-del exception, DNS rollback, 8-key buffer check, reset `success`
  tied to `errors`); UI consumes all results (catches on every handler, child
  mapping + counts banner, reset/update/diagnostic checks, warnings rendering,
  `backendSwitch.error` with preserved exclusion, last-known + stale labeling —
  backend errors never shown as disconnected). Seventeen isolated tests
  (red→green) in `tests/test_truthful_results.py`; full suite 89 tests OK
  (3 Windows inventory skips, Git Bash on PATH); `tsc --skipLibCheck` and
  `pnpm run build` clean with rebuilt tracked `dist`. Independent review +
  scoped re-review clean. See the [design](../superpowers/specs/2026-10-16-st0-truthful-results-design.md)
  and [plan](../superpowers/plans/2026-10-16-st0-truthful-results.md).
  Corrected-candidate device validation remains pending.
- **ST0-009: corrected in source, isolated regression verified (this branch).**
  Desired config and effective service state are never conflated: conf-file
  readers split from systemd readers (service fallback deleted from the desired
  path); `already_set` only on true convergence, divergence accepted as repair,
  outstanding `needs_reboot` rejected distinctly; every transition step checked
  with named errors; final verification reads effective state; failed repair
  rolls back per route (generic conf+service, steamos helper) best-effort and
  reported; status shows `backend_desired`/`backend_effective`/`backend_services`
  with `drift.backend`, diagnostics carry the triple; UI renders
  agreement/divergence/unknown with retry and preserved exclusion. Ten isolated
  tests (red→green) in `tests/test_backend_state.py`; ST0-010 reservation tests
  extended for the converged gate; full suite 101 tests OK (3 Windows inventory
  skips, Git Bash on PATH); `tsc --skipLibCheck` and `pnpm run build` clean with
  rebuilt tracked `dist`. Independent review clean. See the [design](../superpowers/specs/2026-10-16-st0-backend-state-design.md)
  and [plan](../superpowers/plans/2026-10-16-st0-backend-state.md).
  Corrected-candidate device validation (both routes need separate environments)
  remains pending.
- **ST0-021/022/023: corrected, isolated verification (this branch).** Band row
  promises only NM `"a"` (5 GHz) with the `"6GHz"` non-offer stated; CAKE
  described as a local egress queue with no power over other devices, the AP,
  or the ISP bottleneck (UI + README). Build audit went from 13 entries / 7
  GHSAs to 1 residual (`braces` GHSA via `micromatch@4.0.8` — no patched
  version exists, major bump would break semver/build, documented not forced)
  via `pnpm.overrides` on `brace-expansion` within semver; lockfile diff
  restricted to that chain; frozen install, build, `tsc --skipLibCheck`,
  101-test suite, `check-syntax` and `verify-dist` all green. Independent review
  clean (one environmental note: suite needs Git Bash on PATH on Windows). See
  the [design](../superpowers/specs/2026-10-16-st0-claims-toolchain-design.md)
  and [plan](../superpowers/plans/2026-10-16-st0-claims-toolchain.md).
- **ST0-011/012/013/015/020: corrected, isolated + review verification (this branch).**
  New `repair_drifted()` repairs only enabled-and-drifted settings (fresh
  read-only selection, shared drift formulas, `auto_fix`/backend excluded, DNS
  covered by new `drift.dns` subset detection); drift banner calls it instead of
  the preset-enabling Optimize Safe. Custom DNS is draft/applied separated
  (select/type/Apply-Cancel, no blur-submit, poll-guarded refresh, pre-mounted
  error field). Backend poll retries once boundedly with a working Retry action,
  tick-bounded `unknown` state and overlap guard; all timers/awaits carry
  dismount guards (zero post-dismount IPC/state). Eleven isolated backend tests
  (red→green) in `tests/test_repair_drift.py`; full suite 112 tests OK
  (3 Windows inventory skips, Git Bash on PATH); `tsc --skipLibCheck` and
  `pnpm run build` clean with rebuilt tracked `dist`. Independent review READY
  (3 non-blocking minors, closed in a fix round). See the [design](../superpowers/specs/2026-10-16-st0-ui-intent-design.md)
  and [plan](../superpowers/plans/2026-10-16-st0-ui-intent.md).
  Corrected-candidate device validation (including on-screen keyboard and
  gamepad-focus behavior) remains pending.
- The other **3 Important and 1 Minor findings remain open**. Stage 0 and first Stable remain gated on their resolution/disposition and candidate-specific device evidence.

## Coverage and evidence

Reviewed all `main.py`, `install.sh`, `defaults/dispatcher.sh.tmpl`, all `src/` files/components, callable contracts, package/lock/build metadata, `scripts/check_delivery.py`, its tests and `.github` delivery workflows/action/settings proposals. Delivery tooling was assessed alongside inherited runtime code. Generated-artifact reproducibility is covered by the successful exact-baseline hosted build/verification, rather than a new manual rewrite of dist during the audit.

All numbered runtime findings below are **static trace confirmed**. Where effects depend on a particular network, failed command, filesystem or lifecycle ordering, that trigger is explicit; those effects have not been reproduced on the owner's device. Each source reference uses one-based baseline line numbers. ST0-023 combines a live advisory scan with dependency-path inspection.

Checks run: 14 existing delivery unit tests passed; AST/Python and Bash syntax-only checks passed; project typecheck with `--skipLibCheck` passed; all 20 frontend callable names/argument counts matched backend AST signatures. [Hosted CI at the product baseline](https://github.com/undefined3491/WifiOptimizer/actions/runs/38754879160) passed build, types, tests, syntax and dist comparison. These checks do not test the runtime failure paths identified here. The full typecheck's existing dependency-declaration limitation remains documented in CONTRIBUTING.

## Important findings

### ST0-001 — Installer removes the working tree before replacement is ready

**Source:** `install.sh:61-85`. **Trigger/effect:** a source archive contains `plugin.json` but lacks another mandatory file, a copy fails, or installation is interrupted. The script deletes the old plugin before mkdir/cp finishes. `set -e` stops on a required copy error after the previous installation has already been lost; no staging/backup/rollback exists. External settings are not directly deleted by this path.

**Correction/test:** validate all mandatory files and identity, prepare a sibling staging tree, then switch with a recoverable old tree and explicit interrupted-operation handling. Fixture tests must fail each copy/switch step, including an existing recovery backup, and preserve one known working version. Later device test: reinstall/update and load the candidate with settings preserved.

### ST0-002 — In-app update can mix versions while reporting completion

**Source:** `main.py:1773-1799`. **Trigger/effect:** a marker-bearing incomplete archive, copy/I/O failure or interruption. Mandatory curl/tar/cp results are not checked, and new metadata/backend are copied over live files before later copies. The script can log success and restart with old/missing frontend/template files; cleanup discards the downloaded source and there is no rollback. A falsely advanced package version can suppress offering that same Stable version again.

**Correction/test:** share a validated staging/commit/recovery contract with ST0-001; validate copied identity before switching and expose final outcome. Inject missing files, ENOSPC/copy failure and interruption after each mutation. A failed staging operation must not advance the installed identity or remove recovery material. Device update smoke test follows the correction.

### ST0-003 — Update job lifetime and exclusion are not owned by the backend

**Source:** `main.py:1755,1780,1801-1816`; `src/index.tsx:278-290,461-487`; `src/components/UpdatesSection.tsx:42-47,76-79`. **Trigger/effect:** the archive download stalls beyond the 60-second UI timeout; the user follows the retry instruction while the detached process remains alive. There is no archive-transfer deadline, active-job lock or final-status reconciliation. A retry starts another writer using the same script path; both may copy/restart later. Update initiation also does not participate in the normal frontend busy guard, allowing overlap with backend switching. Scheduling-dependent corruption is a risk, not a device reproduction.

**Correction/test:** one backend-owned transaction/job per installation, private job paths, finite network deadlines, observable phases/final result and restart/stale-job recovery; UI timeout must not assert the writer stopped. Stall and release two mocked transfers around a retry; only one commit/restart may occur. Test exclusion with a pending switch and recovery after Decky restart.

### ST0-004 — Restoration overwrites state the plugin never owned

**Source:** `main.py:132-141,384-455,599-618,1332-1354,1379-1398,1593-1601`. **Trigger/effect:** the device has custom sysctl, root qdisc, queue or power policy. Disable writes assumed defaults; reset/uninstall unconditionally reset sysctls, delete the root qdisc and change power/queue values even if corresponding options were never enabled. Prior values are not captured. This establishes loss of custom configuration; it does not establish a measured performance regression on every device.

**Correction/test:** define ownership/restoration explicitly, snapshot before first mutation, restore only owned changes and handle qdisc recovery limitations. Tests with all optional flags false must leave unrelated custom state untouched; enable/disable round trips must restore the recorded baseline. Capture the actual LCD state before using Reset as a recovery mechanism.

### ST0-005 — BSSID disable can target a different profile from the locked one

**Source:** `main.py:372-375,852-855,1136-1168`. **Trigger/effect:** lock profile A, connect to B, then disable. The disable path selects active/last UUID B rather than the dedicated lock owner A, clears B and erases A's recorded ownership. A remains persistently locked and can later fail to roam/reconnect while the UI says locking is disabled.

**Correction/test:** use and retain the recorded owner until successful removal; define transfer/per-profile behavior. Test active B plus recorded owner A, disconnected fallback, failed removal and enabling on a second profile. Device confirmation needs two saved profiles and profile-field inspection.

### ST0-006 — Status reads silently persist band/IPv6 settings into other profiles

**Source:** `main.py:980-982,1001-1004,1185-1210,1303-1321`. **Trigger/effect:** enable a band/IPv6 setting on A, connect to B and poll status. Global intent is written into B's profile without another apply action or profile ownership. A 2.4-GHz-only B can receive band `a` and fail on its next activation; IPv6 can be disabled on a network that needs it. Actual impact depends on B.

**Correction/test:** explicitly define per-profile versus global consent; keep status observation separate from profile mutation and reconcile only the selected owned configuration. Test that polling B cannot propagate A's profile settings. Device scenarios include distinct bands and, if available, an IPv6-dependent network.

### ST0-007 — Setters discard reconnect failure and report reconnection

**Source:** `main.py:377-382,1140-1170,1210-1232,1292-1295,1321-1324`. **Trigger/effect:** radio-off succeeds but radio-on fails, activation times out, or the requested band/AP is unavailable. `_hard_reconnect` discards command results and setters return success/reconnected after saving intent. A player may remain offline or radio-off with no accurate result; band/BSSID relock can also fail silently.

**Correction/test:** structured reconnect results, essential radio recovery, activation verification and preserved prior state for rollback. Inject each radio/activation/relock failure; no unconditional reconnection success and failure details must survive. Validate ordinary recovery on the corrected device candidate.

### ST0-008 — Failed or partial mutations can be saved as successful settings

**Source:** `main.py:457-480,1084-1096,1266-1295,1332-1354,1394-1404,1006-1013`. **Trigger/effect:** DNS removal, CAKE deletion, a sysctl write or dispatcher removal fails. Several paths ignore/log failures, save the desired boolean and return success anyway. DNS can remain overridden or the dispatcher can keep enforcing after the UI turns it off. Buffer status checks only rmem_max, so other failed writes can be concealed. Paired DNS enable writes also have no rollback after the second fails.

**Correction/test:** check every required result, distinguish intended/observed/partial state, retain ownership on failed disable and make retries possible. Inject each failed command/write, including a non-rmem sysctl and second DNS property. Verify actual persistent fields/files/qdisc during normal device round trips.

### ST0-009 — Backend verification reads requested configuration rather than effective state

**Source:** `main.py:289-326,1903-1937,1972-2028,2087-2094`. **Trigger/effect:** target service start fails but its config file was written and NM restart succeeds. Generic service results are ignored; final verification rereads that same config first and can report success while reconnect times out. A later same-target repair is rejected as already_set because the same config still names the target. Configured backend and working backend are conflated.

**Correction/test:** separate desired config from effective NM/backend service state, validate transition steps and allow repair/rollback for divergence. Simulate target config with inactive/failed service and a same-target retry. SteamOS-helper and generic-system recovery require separate actual environments.

### ST0-010 — Backend switch reservation occurs after an await

**Source:** `main.py:2081-2109,1960-1961,2062-2063`. **Trigger/effect:** two overlapping same-target IPC starts both pass the guard while current-backend lookup runs in threads. Both can create workers, overwrite the tracked task/result and clear shared in_progress while another worker is active. This is a narrower IPC/retry trigger, not a claim that the normal panel's synchronous double-click guard fails. Opposite-target starts with a stable known current backend do not both pass already_set; that broader claim is not relied on.

**Correction/test:** reserve before yielding or use a lock with cleanup. Hold the first lookup while submitting a second same-target request; exactly one lookup and worker may be accepted. Mock this race rather than intentionally competing live services on the owner's Deck. The entry-race correction and its lifecycle limits are recorded above.

### ST0-011 — Drift “Fix now” enables the preset instead of repairing current settings

**Source:** `src/index.tsx:362-369,564-571`; `main.py:1409-1451,1489-1585`. **Trigger/effect:** CAKE drifts while BSSID/buffers are intentionally disabled. The banner counts CAKE drift, but Fix now calls optimize_safe: it enables BSSID, power, buffers and dispatcher and attempts a reconnect, without repairing CAKE. Other non-preset drift is also outside that operation.

**Correction/test:** explicit repair of existing enabled/drifted settings and accurate per-setting results. A CAKE-only drift fixture must repair CAKE without enabling unrelated options or forcing BSSID reconnection. Confirm corrected wake/reconnect handling on device.

### ST0-012 — Fresh custom DNS cannot be entered through the UI

**Source:** `src/index.tsx:117,161-164,730-749`; `main.py:1250-1256,1290-1293`. **Trigger/effect:** select Custom from default settings. The local draft is empty, the dropdown immediately submits it, the backend rejects it before saving the provider, and the text field only renders when the saved provider is already custom. There is no fresh-user path to type the required value.

**Correction/test:** separate draft provider/addresses from applied state, expose the editor before submission, then validate/apply a complete value. Test default -> Custom -> type -> apply and subsequent disconnected disable. Include the SteamOS keyboard in device validation.

### ST0-013 — One failed backend poll strands optimistic UI state

**Source:** `src/index.tsx:178-208,439-447`; `src/components/BackendToggleRow.tsx:48-61,90-95`. **Trigger/effect:** a switch is accepted and a progress IPC promise rejects. Polling stops and general busy clears, but backendSwitch.in_progress remains true: its control remains Working/disabled while other mutations become available. Normal status refresh does not reconcile this state; remount or explicit recovery is needed.

**Correction/test:** bounded retry and explicit unknown/error reconciliation, preserving appropriate exclusion until state is known. Inject a failed poll followed by terminal success/failure and assert UI recovery. Actual Decky transport behavior must not be inferred from WiFi loss alone.

### ST0-014 — Force Reapply hides child and top-level failures

**Source:** `src/index.tsx:332-358,396-397`; `main.py:1495-1585`. **Trigger/effect:** any child setter fails. reapply_all returns aggregate success true plus failed children; the generic toggle handler ignores children. Even a top-level failure is placed in errors.reapply, which no rendered JSX displays. The player receives no actionable repair result.

**Correction/test:** consume/render aggregate and per-setting results and top-level failures, while preserving busy cleanup. Test mixed results, total failure, DNS and dispatcher errors. Backend false-success paths in ST0-008 need their own corrections; this finding covers truthful failure results discarded by the frontend.

## Minor findings

### ST0-015 — Polling overwrites a custom DNS draft

`src/index.tsx:159-164,220-221,740-749`: with provider already custom, each successful refresh resets text while the player is typing; blur can submit the restored/partial value. Track dirty/focused drafts independently. Regression: two refreshes during editing preserve the draft until commit/cancel. Device: on-screen keyboard across multiple polling intervals.

### ST0-016 — Reset does not consistently apply its declared defaults or undo runtime power state

`main.py:150-151,599-618,1590-1637`: reset writes power-save-disabled/auto-fix true defaults but does not reconcile iw state or dispatcher installation; uninstall also does not restore live iw state. Define reset/restoration semantics and test dispatcher present/absent and power state before/after reconnect. Separate from ST0-004's unrelated-state loss and the documented persistence of profile changes.

### ST0-017 — Resolved failure objects are ignored by several frontend actions

`src/index.tsx:399-409,461-469`; `src/components/PanelFooter.tsx:19-34`: reset/update/diagnostic handlers rely on rejection instead of checking success false. Reset errors are not surfaced; refused updates look Updating until timeout; failed diagnostic saves can display Saved. Check result discriminants and display the actual immediate error. Regression: resolved failure for each action must never become a saved/updating success indication.

### ST0-018 — Restart failures are hidden by installation success reporting

`install.sh:87-95`; `main.py:1798-1799`: restart status is ignored while installed/updated success is printed/logged. Distinguish file commit, restart request and health, retaining actionable diagnostics/recovery. Test a mocked restart failure; actual transaction failures remain ST0-001/002.

### ST0-019 — Status failures appear blank, stale or disconnected without explanation

`src/index.tsx:153-168,490-503`; `main.py:1029-1032`: initial promise rejection leaves no status; later rejection leaves stale data; a resolved error object is treated like ordinary disconnected data. Preserve last-known data with explicit error/staleness and gate actions needing reliable state. Test initial/repeated/resolved failures and recovery, distinct from a successful disconnected status.

### ST0-020 — A delayed launch callback survives plugin dismount

`src/index.tsx:831-840,857-859`: unregistering the listener does not cancel a scheduled 3-second reapplyVolatile timer. It can attempt IPC after teardown; an actual post-uninstall write depends on Decky ordering and is not proven. Track/cancel timers or guard disposal. Fake-timer regression: launch -> dismount -> advance time must make zero backend calls.

### ST0-021 — The 6-GHz label does not match the submitted band

`src/index.tsx:692-705`; `main.py:1175-1192`: the supported-6-GHz label promises a 5/6-GHz choice while the setter only accepts `a` or `bg`, with default `a`. Current [NetworkManager band documentation](https://networkmanager.dev/docs/api/latest/settings-802-11-wireless.html) distinguishes 5 GHz `a` from `6GHz`. Correct labels/capability detection or implement separately verified supported band selection; do not blindly send a new enum to older installed NM. LCD does not certify 6 GHz. Test argument/label agreement and actual capabilities on separately available hardware.

### ST0-022 — CAKE explanation overstates control over other devices

`src/index.tsx:774`; `main.py:1379-1382`: a local unlimited qdisc is described as preventing another device from starving the stream. The configured queue does not own other devices' traffic or an external bottleneck. The [upstream CAKE manual](https://github.com/iproute2/iproute2/blob/main/man/man8/tc-cake.8) defines unlimited as no bandwidth limit. Qualify the claim and measure local benefits rather than promise network-wide isolation. Review text against actual command scope; measure separately from correctness tests.

### ST0-023 — Build dependencies match published denial-of-service advisories

`package.json` devDependencies; `pnpm-lock.yaml:301-309,870-883`. On 2026-10-15, pnpm 9 audit exited 1 with 13 matched entries (11 High, 2 Moderate), representing 7 distinct GHSAs across brace-expansion 1.1.14/2.1.0 and braces 3.0.3. Paths run through @decky/rollup -> glob/minimatch or rollup-plugin-delete -> globby/micromatch; these are build-tool dependencies. The scanner's dev flags do not accurately communicate that root-package role; no such production frontend/backend call path was established.

[Maintainer disclosure](https://github.com/juliangruber/brace-expansion/security/advisories/GHSA-3jxr-9vmj-r5cp) describes resource exhaustion on crafted patterns; [braces advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm) describes parser stack exhaustion. Database/maintainer severity can differ; scanner counts are not 13 exploitable plugin vulnerabilities. Triage/update the toolchain in a scoped compatibility PR, check all 7 current advisory ranges, preserve reproducibility and rerun build/type/artifact checks. Do not apply an automatic audit fix or speculative package override here. Exploitability on a Deck, malicious dependency provenance and complete supply-chain integrity were not certified.

The dated scanner matches were GHSA-3jxr-9vmj-r5cp, GHSA-6j4f-fj2g-mc7p, GHSA-mh99-v99m-4gvg, GHSA-q2hr-2g5m-vwhr, GHSA-qhr7-859c-m2p7 and GHSA-rgw5-rvv9-x895 for both brace-expansion versions, plus GHSA-vfj7-8cjw-p6xm for braces. Reproduce with `npm exec --yes --package=pnpm@9 -- pnpm audit --json`; the registry's future counts/ranges may change.

## Platform relevance and optimization dispositions

These are **provisional audit recommendations**, pending fixes and measurements, rather than runtime changes made by this report.

| Optimization | Disposition and evidence needed |
| --- | --- |
| iw power save | Constrain to explicit, verified state and tested policy. Current defaults apply it before a preset click; compare streaming and idle behavior/power on LCD Stable. NM powersave enums remain documented, but benefit is workload-dependent. |
| Driver deep-power / PCIe ASPM / runtime PM | Split evidence for each mechanism and actual supported path; preserve original values. Upstream Linux v6.18 still exposes the rtw88 disable_lps_deep/disable_aspm parameters, so the claim that they were simply removed is rejected. That does not prove SteamOS's installed module or the benefit of disabling them. |
| BSSID lock | Retain as a deliberate profile-owned, single-AP option after ST0-005/006; exclude blanket safety claims for roaming/mesh. Driver support and actual AP behavior need tests. |
| Band restriction | Retain explicit per-profile intent with corrected labels/capability handling. Verify 2.4/5-GHz transitions on LCD; 6 GHz requires separate hardware/installed-NM evidence. |
| DNS override | Retain opt-in with working draft/validation, correct profile ownership, failure handling and restoration. A public DNS provider is not an established general latency fix. |
| IPv6 disable | Constrain to explicit profile troubleshooting, with recovery and no status-driven spread. Test a network that needs IPv6 where available; no universal benefit claim. |
| Buffer/queue tuning | Constrain until per-key correctness, owned rollback and baseline A/B results exist. Current upstream sysctl docs describe values and different default maxima; do not replace the installed machine's state with a guessed upstream value. |
| CAKE unlimited | Retain experimental opt-in pending qdisc ownership/recovery and local-load measurements; no bandwidth shaper or guarantee against other stations. Verify module/capabilities and interaction with buffer queue length. |
| Backend choice | Retain manual only after effective-state verification, serialization and recovery are corrected. The installed backend must be detected; a distro name/config file is insufficient. Stable and Beta differ. |
| Reconnect persistence | Retain only with observed success, correct disable/removal and lifecycle tests; a dispatcher timestamp is not proof every requested write worked. |

Official SteamOS notes rechecked through Valve's [news API](https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=1675200&count=100&maxlength=0&feeds=steam_community_announcements): Stable 3.8.10 reports a WiFi degradation fix; Stable 3.8.28 adds slow/stuck-connection fixes and kernel 6.18.50. The 3.9.2 Beta/Preview cumulative notes describe a new-install default backend change, improved wpa_supplicant resume and steamos/holo compatibility aliases. See [the dated release/source table](2026-10-15-stage-0.md#official-steamos-evidence). None establishes the owner's installed versions or proves our particular workaround obsolete.

Additional primary references: [NetworkManager configuration precedence and backend behavior](https://networkmanager.dev/docs/api/latest/NetworkManager.conf.html), [kernel runtime PM](https://docs.kernel.org/power/runtime_pm.html), [network sysctls](https://docs.kernel.org/admin-guide/sysctl/net.html), [Linux v6.18 rtw88 PCI](https://github.com/torvalds/linux/blob/v6.18/drivers/net/wireless/realtek/rtw88/pci.c) and [core](https://github.com/torvalds/linux/blob/v6.18/drivers/net/wireless/realtek/rtw88/main.c). Upstream references are not a substitute for the SteamOS vendor build. NM documentation also warns that iwd autoconnect mode can ignore autoconnect priority, so the status write of priority 100 is not a universal selection guarantee.

## Open questions and explicitly limited conclusions

- **Privileged temporary script:** ordinary open/chmod on a fixed /tmp path (`main.py:1801-1808`) needs private exclusive creation. Local denial/overwrite/substitution depends on ownership, sticky-directory protections and kernel settings; no default-SteamOS privilege-escalation proof exists. Resolve through the update transaction design and isolated Linux security checks before Stable.
- **Generated shell interpolation:** version and path values are inserted into shell text without shell escaping. Trusted repo metadata and configured install paths are the identified inputs, not an established unauthenticated attacker. Validate schemas/pass arguments and test unusual inert path fixtures; do not advertise a demonstrated remote exploit.
- **Beta identity:** checking and downloading a moving beta branch are not pinned to one commit. Same-version branch publication is already prohibited, but movement between check and download remains a consistency question for the transaction redesign. [DROPPED with the Beta channel — no action.] The Beta channel no longer exists (no branch reads/downloads, no `update_channel` key); there is no moving branch to pin, so this question is moot. Stable candidates resolve through `releases/latest` → tag `vX.Y.Z` → tag tarball with identity validation before any live write.
- **Event-loop blocking/backlog:** synchronous subprocess calls and a blocking sleep exist inside async APIs; interval requests have no in-flight dedupe. Accumulated command timeouts can delay progress/IPC. Exact Decky request-queue/timeout behavior and impact require controlled measurement; no fabricated permanent-deadlock claim.
- **Dispatcher races/capability asymmetry:** a previously read enabled snapshot can race disable; runtime power/control is guarded by the link directory in the dispatcher but independently written by Python. Trace differences are real; material LCD/wake behavior is untested.
- **Adapter/capability coverage:** interface and active UUID selection are independent, and driver-family 6-GHz flags do not identify exact cards. Multi-adapter, non-LCD, other-distribution and unsupported-driver scenarios remain unverified and need scoped claims/tests.
- **UI/platform assumptions:** QAM cache/visibility/remount, gamepad focus, ErrorBoundary reopen recovery, Steam client state, actual service/driver behavior and battery/throughput remain device questions. No planned Watchdog feature is claimed implemented or missing from the existing feature set.

## Dispositions and rejected candidates

Reviewer mapping: B1 -> ST0-005; B2 -> 006; B3 -> 004; B4 -> 007; B5 -> 008; B6 -> 009; B7 -> 010 (narrowed to same-target concurrency); B8 -> 016. DELIVERY-A/B/C/D -> 002/001/003/018. FE-01/02/03/04/05/06/07/08/09 -> 012/015/011/013/014/003/017/019/020. Coordinator additions are 021-023. These mappings retain every numbered reviewer candidate without double-counting update concurrency.

Rejected as separate findings: async declarations alone do not prove settings lost-update races because ordinary setters do not yield on their mutation paths; malformed HTTP HTML ordinarily fails before a plugin marker rather than proving destructive install; documented main fallback, persistent NM fields after reset and release rerun refusal are existing disclosed decisions; callable names are not missing; lack of Watchdog is not a regression. Fixed sysfs parameters are present upstream rather than proven absent. No generic root-context/untrusted-argument claim establishes Critical remote compromise. Partial-buffer verification and failed priority writes are included under ST0-008 rather than additional inflated counts. Hypotheses above remain visible instead of being silently discarded.

## Correction order and Stage 0 handoff

Scheduling update, 2026-10-16: ST0-010's entry race is corrected; initial device observation is recorded. The next recommended source package is ST0-005/006, independent of live deployment. Recovery remains a prerequisite for device mutation, not a reason to build the conditional updater proposal without evaluating Decky's native lifecycle.

1. **ST0-005/006 — profile ownership and observational status.** Prepare a scoped plan before runtime edits. Define the owner UUID for BSSID/band/IPv6, transfer between profiles and legacy settings with unknown ownership. Status polling must neither save settings nor modify NM profiles/priority. Replace its implicit last-UUID bookkeeping with successful explicit-operation target recording where needed; preserve disconnected band/DNS/IPv6 changes. Do not silently move the undocumented priority `100` write into another automatic path. Tests must cover owner A with active B, disconnected disable, failed removal retaining ownership, transfer/unknown legacy state and polling B without writes. Removing only status mutations does not fully resolve either finding or establish restoration correctness.
2. **Restoration and delivery — ST0-004/016 and 001/002/003/018.** Agree ownership/restoration of existing modified state, then harden the retained Stable-only in-app updater (single job with exclusion, same-filesystem staging, validated transfer/identity, per-file commit, truthful restart/result reporting) plus the rescue-only installer. Add isolated copy/interruption/exclusion and truthful restart-result tests before live update/reset/uninstall tests. The [recovery specification](../superpowers/specs/2026-10-15-delivery-recovery-design.md) is a conditional proposal, not an implemented dependency. Update 2026-10-17: delivery direction decided — A1 deferred, custom Stable-only updater retained + hardened, Beta dropped; item 2 rewritten accordingly.
3. **Remaining behavior and UI.** Correct reconnect outcomes and truthful mutation results (007/008), effective backend state/recovery (009), UI intent/result handling (011-020), band/CAKE claims and dependency triage (021-023). ST0-010 does not establish correctness of real workers, thread cancellation or exclusion with updates. Some independent UI fixes can proceed once their backend result contracts are agreed.
4. **Candidate validation and release.** Reuse the [existing-device inventory](../testing/results/2026-10-16-owner-device-inventory.md); refresh observations affected by later system changes. Prepare private recoverable configuration and repeatable AP/workload/power conditions, then execute the [device protocol](../testing/steam-deck-lcd-stable.md) against an exact corrected candidate. Record untested configurations and explicit lower-priority dispositions. Stable and Connection Watchdog follow Stage 0 closure.

The original static-audit documentation introduced no runtime fixes; subsequent correction evidence is tracked at the start of this report. Keep Stage 0 open, package/version unchanged and Stable unpublished until required fixes, review and device evidence satisfy the [audit specification](../superpowers/specs/2026-10-15-stage-0-audit-design.md). The report does not authorize OS changes or remote-protection activation on its own.

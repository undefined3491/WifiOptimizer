# Candidate validation matrix — LCD / Stable (skeleton, UNTESTED)

Date prepared: 2026-10-17. Status: **skeleton only — no device test executed.**
Stage 0 remains open. All rows are `UNTESTED` until run against a named candidate.
Do not mark Stage 0 complete from static checks or isolated tests alone.

Related: [device protocol](../steam-deck-lcd-stable.md),
[static findings](../../audits/2026-10-15-stage-0-findings.md),
[Stage 0 continuation](../../audits/2026-10-15-stage-0.md),
[inventory result](2026-10-16-owner-device-inventory.md),
[collector procedure](../collect-inventory.md).

## 0. Candidate under test (fill before running)

| Field | Value (fill at run time) |
| --- | --- |
| Candidate commit | `a3bb26b` on `main` (PR #14 squash) — RECHECK at run time; corrections after this commit change the candidate |
| Package version | `0.11.6` (`package.json`) |
| Bundle identity | `dist/index.js` + `dist/index.js.map` rebuilt from the candidate commit (record hashes) |
| Install method | (ZIP / `install.sh` / in-app update — record exact path) |
| Baseline snapshot ref | (private recoverable copy of NM profiles, sysctls, qdisc, sysfs, configs — REQUIRED before any mutation row) |
| Tester / date |  |
| Workload used | (game/streaming title, settings, power source, brightness, frame limit) |
| AP / band setup | (router model, SSID alias, band available, mesh? roaming needed?) |

Rule: run §1 (environment + baseline + recovery) before any mutation row.
One option at a time; restore the recorded prior state before the next row
([protocol](../steam-deck-lcd-stable.md#controlled-comparisons)).

## 1. Target device (from 2026-10-16 inventory — read-only, pre-candidate)

| Field | Observed value | Limit |
| --- | --- | --- |
| Model | DMI `Jupiter` (consistent with LCD) | Owner-reported LCD, not independently photographed |
| SteamOS | `3.8.28`, build `20260922.1`, variant `steamdeck` | Stable channel is owner-reported only |
| Kernel | `6.18.50-valve2-1-neptune-618-gc7289a96b14d` |  |
| WiFi driver | `rtw88_8822ce` | LCD result does not validate other adapters |
| NetworkManager | `1.52.1`, service active |  |
| systemd | `257` |  |
| Decky | live process reports `v3.2.10`, `plugin_loader.service` active, `KillMode=process` | Kill-mode evidence is per-installation only |
| Effective backend | correlated runtime evidence supports `wpa_supplicant` on the active interface (D-Bus + NM journal) | Config/service reads alone were inconclusive; recheck after any system change |
| Installed plugin at inventory | legacy `WiFi Optimizer` dir only, manifest `wifi-optimizer` `0.11.6`, stored channel `beta` (pre-drop observation) | Hashes match pre-fork-fixes blobs for 6 files; not proof of source commit or running code |
| Stored intent at inventory | power-save-disabled, wake-reapply, BSSID lock, buffers, CAKE, IPv6-disabled on; `priority_set=true`; band `a`, DNS `cloudflare` stored but disabled; `supports_6ghz=false` | Stored flags, not defaults |
| Observed state at inventory | power save `off`; qdisc `cake`, txqlen `256`; runtime PM `on`; ASPM L1 fields `0`; `disable_lps_deep=Y`, `disable_aspm=Y`; `rmem/wmem_max=16777216`, `rmem/wmem_default=1048576`, `backlog=5000`, `budget=600/8000us`, `slow_start_after_idle=0`; both profiles priority `100`, no BSSID value, IPv6 disabled | Both profiles lacked BSSID despite stored lock flag — reconcile, do not assume cause |

### Hard limitations (honest scoping — these make rows UNTESTABLE, not PASS)

1. **Modified installation, no pristine baseline.** Prior Optimize Safe use; dispatcher/NM/modprobe files present; pre-existing `priority 100` on both profiles. Without a pre-plugin snapshot there is no OS-pristine comparison — any "Factory restore" claim is `UNTESTABLE` (row S-RST-03).
2. **No recovery backup exists yet.** The filtered inventory report is not a backup. Approve the restoration contract (ST0-004/016 snapshot semantics) and take private recoverable copies before mutating.
3. **Single LCD / single AP environment.** One rtw88 card, one backend route (`wpa_supplicant`), no 6 GHz, no mesh. Rows needing iwd route, 6 GHz hardware, mesh roaming, or second adapter are `UNTESTABLE` here — record as such, do not pass by analogy.
4. **Benefit claims need controlled A/B runs.** Power/battery/throughput/stutter benefit is `UNMEASURED` unless run counts, durations, and comparable conditions are recorded. One favorable sample is not a pass.
5. **Beta channel no longer exists.** Any Beta/Preview row is out of scope (dropped in ST0-001/002/003/018 package). Stable-only.
6. **Connection Watchdog is not a feature of this candidate.** Do not mark it tested.

## 2. How to read the matrix

- **Kto: SSH** — runnable remotely by the agent over SSH as `deck` (read-only first; privileged only where the row says so). Panel must stay closed unless the row requires it.
- **Kto: FIZYCZNIE** — requires the owner's hands on the Deck (panel UI, game launch, suspend button, on-screen keyboard, gamepad).
- **Kto: SSH+FIZYCZNIE** — owner acts, agent verifies over SSH in parallel.
- **Wynik** stays `UNTESTED` (or `UNTESTABLE` with reason) until executed. Allowed outcomes when run: `PASS` / `FAIL` / `PARTIAL` (with evidence link).
- Every mutation row must record: command, `nmcli`/sysfs/qdisc output before+after, UI message shown, reconnect observed (yes/no + duration). Privacy rule: committed docs carry ALIASES ONLY (no SSID/BSSID/UUID/DNS/IP/raw secrets); raw outputs live exclusively in `$OUT_DIR`/`$BACKUP_DIR` with mode `600` and are never committed or published. Scrub before archiving, not after.

## 3. Preconditions (run first)

| ID | Scenario (finding) | Kto | Kroki / komenda | Oczekiwany wynik (mierzalny) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-PRE-01 | Refresh inventory on candidate system | SSH | Run `./collect_deck_inventory.py` on the Deck per [collect-inventory](../collect-inventory.md) (repo path `scripts/collect_deck_inventory.py` is the source; on Deck it is the copied file); record collector commit + output hash | Exit 0; report captured; OS/build/kernel/NM/Decky/backend re-confirmed or drift noted | UNTESTED | Non-atomic snapshot; close panel, no concurrent reconnect |
| S-PRE-02 | Private recovery backup + contract review | SSH+FIZYCZNIE | Copy NM profiles (`nmcli con show <uuid>`), `/etc/sysctl.d/*`, `tc qdisc`, `txqueuelen`, `/sys/.../power/control`, ASPM `lspci` fields, modprobe files, dispatcher file, `settings.json` to private storage, then scrub the copy to aliases before any archiving; review ST0-004/016 snapshot semantics | Backup exists and is restorable; owner approves Reset/Uninstall as tested paths | UNTESTED | Filtered inventory is NOT a backup; blocks all S-RST rows; raw identifiers never leave `$OUT_DIR`/`$BACKUP_DIR` |

## 4. Startup and lifecycle

| ID | Scenario (finding) | Kto | Kroki / komenda | Oczekiwany wynik (mierzalny) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-START-01 | Fresh boot, panel never opened | FIZYCZNIE+SSH | Reboot; do not open panel; SSH: `nmcli d status`, `iw <if> get power_save`, `tc qdisc show dev <if>`, journal `NetworkManager` since boot | WiFi connects without manual action; no plugin-initiated reconnect in journal; volatile values match last applied or documented defaults | UNTESTED | Distinguish plugin reconnect from NM auto-connect |
| S-START-02 | Boot with saved settings + game launch (ST0-020) | FIZYCZNIE | Open game (record title); observe 3 s `reapply_volatile` fires once; close game; dismount panel; check no post-dismount IPC (CEF console if available) | Game launches normally; single volatile reapply, no error banner; dismount cancels pending timer (zero backend calls after dismount) | UNTESTED | Owner observes UI; SSH optionally tails logs |
| S-START-03 | Panel open/closed status polling purity (ST0-005/006) | SSH+FIZYCZNIE | With settings on profile A, connect to profile B; poll panel 3×; SSH: diff `nmcli con show <B-uuid>` before/after; check `settings.json` mtime/content | Zero writes to B profile; zero settings saves on poll; no `autoconnect-priority` added anywhere | UNTESTED | Core regression for 005/006; record both UUIDs (alias them) |

## 5. Per-option on/off round-trips (one row = enable → verify → disable → verify restore)

For each row: SSH captures before/after values; FIZYCZNIE toggles in panel; reconnect (if any) must show truthful result (ST0-007).

| ID | Scenario (finding) | Kto | Kroki / komenda | Oczekiwany wynik (mierzalny) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-OPT-01 | Power save off→on→off (audit disposition) | SSH+FIZYCZNIE | Toggle; SSH: `iw <if> get power_save` each step | `off` when enabled, restored prior value on disable (owned-only restore per ST0-004); UI reports verified state | UNTESTED | Bundled with driver/ASPM in code — note confounder |
| S-OPT-02 | Driver deep-power / ASPM / runtime PM round-trip | SSH+FIZYCZNIE | Toggle; SSH: `rtw88_core.disable_lps_deep`, `rtw88_pci.disable_aspm`, `/sys/.../power/control`, ASPM L1 fields | Values change on enable; disable restores snapshot (not assumed defaults); no boot failure | UNTESTED | Upstream params exist (v6.18) — benefit still unproven on this build |
| S-OPT-03 | BSSID lock on/off + unlock while disconnected (ST0-005) | SSH+FIZYCZNIE | Lock on A; connect B; disable lock; SSH: `nmcli -f 802-11-wireless.cloned-mac-address,bssid con show <A-uuid>/<B-uuid>`; repeat disable with WiFi off (`_resolve_uuid` offline path) | Disable targets owner A, never active B; A unlocked; ownership cleared; offline disable works on saved profile | UNTESTED | Needs 2 saved profiles; record owner UUID behavior |
| S-OPT-04 | Band preference on/off incl. unavailable band (ST0-006/021) | SSH+FIZYCZNIE | Set band `a` on A; connect B; disable; SSH: B band untouched; try band unavailable for current AP | B profile unchanged; owner recorded only on verified success; label says 5 GHz (not 5/6 GHz promise) | UNTESTED | 6 GHz capable HW absent → 6 GHz claim UNTESTABLE here |
| S-OPT-05 | DNS override on/off + paired-key rollback (ST0-008) | SSH+FIZYCZNIE | Enable Cloudflare then Custom; disable; SSH: `nmcli -f ipv4.dns,ipv4.ignore-auto-dns con show <uuid>` | Both DNS keys written or clean failure with `dns_partial` + rollback; disable restores prior DNS; failed disable retains ownership for retry | UNTESTED | Needs the S-UI-01 keyboard path for Custom entry |
| S-OPT-06 | IPv6 disable/enable + no spread (ST0-006) | SSH+FIZYCZNIE | Disable IPv6 on A; connect B; poll; SSH: B `ipv6.method` unchanged | B untouched by poll; A `disabled` only after explicit apply; restore on disable | UNTESTED | IPv6-dependent network unavailable → benefit tradeoff UNTESTABLE |
| S-OPT-07 | Buffer tuning on/off, all-keys check (ST0-008) | SSH+FIZYCZNIE | Toggle w panelu; SSH: all 8 sysctl keys (`rmem/wmem_max/default`, `backlog`, `budget`, `budget_usecs`, `slow_start_after_idle`) + `ip link show <if> txqueuelen` | All 8 keys verified, not just `rmem_max`; `txqueuelen 2000`; disable restores snapshot values | UNTESTED | Order matters: buffers before CAKE |
| S-OPT-08 | CAKE on/off + qdisc best-effort restore (ST0-004) | SSH+FIZYCZNIE | Toggle; SSH: `tc qdisc show dev <if>`; disable | `cake` present when on (txqlen `256`); disable removes only owned qdisc via del-vs-replace; UI copy claims local-egress only (ST0-022) | UNTESTED | Other-device/AP/ISP benefit explicitly out of claim |
| S-OPT-09 | Optimize Safe preset (regression only) | FIZYCZNIE+SSH | Apply preset from clean-ish state; verify each member value; then reset | All members applied with one truthful aggregate result; preset is not used as drift repair (see S-UI-03) | UNTESTED | Test only after individual rows understood |

## 6. Reconnect behavior (ST0-007/008 truthful results)

| ID | Scenario (finding) | Kto | Kroki / komenda | Oczekiwany wynik (mierzalny) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-RC-01 | WiFi off/on round-trip via setter | SSH+FIZYCZNIE | Toggle any reconnecting option; time `radio off→on→con up`; SSH: `nmcli d status`, `nmcli con show --active` | `reconnected:true` only when verified (≤2 checks, ~5 s budget); UI shows verified/failed, never unconditional success | UNTESTED | Record duration; dead-radio signal if radio-on fails |
| S-RC-02 | AP loss / out-of-range recovery | FIZYCZNIE+SSH | Walk out of range or power-cycle AP (record which); return; observe journal + UI | Reconnect outcome reported truthfully; no stuck `Working` state; failure shows reason, not silent success | UNTESTED | RF-dependent; repeat ≥2× before any benefit claim |
| S-RC-03 | Disconnected edits to saved profiles | FIZYCZNIE+SSH | WiFi off; change band/DNS/IPv6/BSSID-disable on saved profile; WiFi on | Changes apply to saved profile without requiring live BSSID; no foreign-profile touch; reconnect verifies | UNTESTED | Disablers must use `_resolve_uuid`, not active UUID |
| S-RC-04 | Forced reconnect failure reporting | SSH | (Only with owner consent) `nmcli radio wifi off` held during setter reconnect, then restore | UI reports failure with named error (`reconnect` detail), `reconnected:false`; radio restored usable | UNTESTED | Failure injection — do not run without explicit consent + recovery ready |

## 7. Sleep / wake

| ID | Scenario (finding) | Kto | Kroki / komenda | Oczekiwany wynik (mierzalny) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-SLP-01 | Short suspend/resume ×3 | FIZYCZNIE+SSH | Sleep via power menu 30–60 s, resume, wait for connect; repeat 3×; SSH: journal timestamps, `iw power_save`, qdisc after each wake | 3/3 resumes reconnect (record durations); volatile state reapplied by dispatcher on `up`; no plugin-initiated reconnect storms | UNTESTED | Count cycles + sleep/reconnect durations per protocol |
| S-SLP-02 | Long sleep (≥30 min) | FIZYCZNIE+SSH | Sleep ≥30 min; resume; same checks as S-SLP-01 | Same as S-SLP-01; dispatcher self-integrity (still installed, still references existing plugin dir) | UNTESTED | Schedule around owner availability |

## 8. Reset / uninstall restoration (ST0-004/016)

Blocked by S-PRE-02 (backup + contract). Compare against the private snapshot, never against an assumed pristine OS.

| ID | Scenario (finding) | Kto | Kroki / komenda | Oczekiwany wynik (mierzalny) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-RST-01 | `reset_settings()` reconciliation | SSH+FIZYCZNIE | With ≥2 options enabled, Reset; SSH: sysctls, txqlen, `iw`, qdisc, dispatcher present, owned profiles cleared, `system_snapshot.json` state, single conditional reconnect | Live `iw off` + NM conf + dispatcher reconciled; owned profiles cleared before wipe; `success:false` iff `errors` non-empty; backend out of scope disclosed | UNTESTED | Pre-existing `priority 100`s untouched by design — verify |
| S-RST-02 | Uninstall restore + dispatcher cleanup | SSH+FIZYCZNIE | Uninstall candidate (record method: Decky ZIP-remove vs `install.sh`); SSH: snapshot values restored, dispatcher/configs removed, `txqueuelen 1000` + `SYSCTL_DEFAULTS` only for owned domains | Owned state restored; dispatcher self-removes when plugin dir gone; no live-dir data loss; service-restoration limits disclosed | UNTESTED | Decky 3.2.10 replacement calls `_uninstall` — plan reinstall path first |
| S-RST-03 | "Factory / pristine OS" restore | — | — | — | UNTESTABLE | No pre-plugin baseline exists on this device; Reset is reconciliation to saved defaults + snapshot, not proof of pristine OS. Do not mark PASS. |

## 9. Backend switch / repair / rollback (ST0-009/010)

This device's effective backend is `wpa_supplicant`. The generic route and the SteamOS-helper route need separate environments — only the installed route is testable here.

| ID | Scenario (finding) | Kto | Kroki / komenda | Oczekiwany wynik (mierzalny) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-BE-01 | Switch on the installed route (target = current effective backend family) | SSH+FIZYCZNIE | Record `backend_desired`/`backend_effective`/`backend_services` before; switch; SSH: conf file + `systemctl is-active` for target service + NM state after | `already_set` only on true convergence; each step checked with named errors; final verification reads effective state; reconnect verified | UNTESTED | Maintain local recovery access; first review compatibility notes |
| S-BE-02 | Switch on the non-installed route (iwd/helper) | — | — | — | UNTESTABLE | Needs a separate environment with that backend installed; mock-race covered by isolated tests only |
| S-BE-03 | Divergence display + retry (ST0-009/013) | SSH+FIZYCZNIE | (If a divergence can be produced safely, else simulate by stopping target service with consent) observe panel agreement/divergence/unknown + Retry | UI shows divergence (desired ≠ effective) with working Retry; backend errors never shown as "disconnected"; poll retry bounded (1×) then error+lock | UNTESTED | Do not break a working backend without recovery ready |
| S-BE-04 | Failed repair rollback | SSH | With consent, fail a transition step (e.g. refuse service start); observe rollback | Per-route best-effort rollback (generic conf+service / steamos helper) executed and reported; `drift.backend` set; no `already_set` lockout on retry | UNTESTED | Isolated tests cover logic; device row confirms reporting |
| S-BE-05 | Concurrent switch exclusion (ST0-010) | FIZYCZNIE | Double-trigger same-target switch quickly (normal panel double-click, NOT crafted IPC race) | Exactly one worker accepted; second rejected or queued with clear message; no stuck `in_progress` | UNTESTED | Live competing-service races are explicitly NOT attempted on owner Deck |

## 10. Update / install delivery (ST0-001/002/003/018, Stable-only)

Never publish a Stable release to create a fixture. End-to-end Stable update is exercisable only when a real next Stable release exists.

| ID | Scenario (finding) | Kto | Kroki / komenda | Oczekiwany wynik (mierzalny) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-UPD-01 | Stable update end-to-end (when a newer Stable tag exists) | FIZYCZNIE+SSH | `check_for_update` → `apply_update`; record target `vX.Y.Z`, phases, single restart; SSH: file identities before/after, version match | One job, one restart; staging→commit with identity allowlist; split `file_commit`/`restart`/`health:load_unconfirmed` truthful; version offered once, not falsely advanced on failure | UNTESTED | If no newer Stable tag exists at run time → UNTESTABLE (do not publish a release as a fixture) |
| S-UPD-02 | Failed download / interrupted update rollback | SSH | (Controlled fixture only, with backup) corrupt archive / kill mid-commit; verify live tree identical, version not advanced, recovery retained | Live dir never removed; partial commit withholds restart with partial counts + retained stage; boot re-offers on missing files | UNTESTED | Risky live; prefer isolated-test evidence + installer rescue drill |
| S-UPD-03 | `install.sh` rescue reinstall | SSH | Run `install.sh` from candidate source with settings present | Sibling staging + identity check; atomic fresh/upgrade paths; settings preserved; truthful stdout/exit; no `rm -rf` of live | UNTESTED | Rescue-only path; record exact invocation |
| S-UPD-04 | Update ↔ backend-switch mutual exclusion | FIZYCZNIE | Start update, attempt backend switch (and reverse) | Second operation rejected with clear reason in both directions; single commit/restart total | UNTESTED | 60 s UI timeout = "unknown, verify after restart", not success |

## 11. UI intent, polling, drift, errors (ST0-011–020)

| ID | Scenario (finding) | Kto | Kroki / komenda | Oczekiwany wynik (mierzalny) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-UI-01 | Custom DNS via on-screen keyboard (ST0-012) | FIZYCZNIE | From non-custom provider: select Custom → field appears BEFORE submit → type with SteamOS keyboard → Apply; then Cancel path; then disconnected disable | Fresh-user path works: draft separated from applied, no blur-submit, validation before apply; empty Custom shows mounted error, not silent reject | UNTESTED | Needs physical keyboard; record keystrokes/locale issues |
| S-UI-02 | Polling never clobbers DNS draft (ST0-015) | FIZYCZNIE | With Custom applied, type a new draft; wait through ≥2 poll intervals (3 s) without committing | Draft preserved byte-for-byte across refreshes until Apply/Cancel; no blur-submit of partial value | UNTESTED | Combine with S-UI-01 session |
| S-UI-03 | Drift banner → `repair_drifted` (ST0-011) | SSH+FIZYCZNIE | Induce single drift (e.g. remove CAKE qdisc with consent: `tc qdisc del dev <if> root`); click banner action; SSH: verify only enabled+drifted repaired | Repairs CAKE only; does NOT enable BSSID/power/buffers or force reconnect; `repair_total_zero` message exact when clean; DNS drift covered by subset detection | UNTESTED | Banner must call repair, never preset |
| S-UI-04 | Force Reapply mixed/total failure (ST0-014) | SSH+FIZYCZNIE | With consent, break one child (e.g. remove dispatcher writability); Force Reapply | Banner shows applied/total/failed counts + per-key errors; top-level failure in `errors.reapply` rendered; busy always cleared | UNTESTED | Truthful-results package; check `transfer_warnings` rendering too |
| S-UI-05 | Backend poll failure → Retry (ST0-013) | FIZYCZNIE | (If reproducible: drop network mid-switch or reject poll) observe `backendSwitch` state → click Retry → successful status reconciles | Bounded retry (1×), then error+locked controls; Retry reconciles on next success; `in_progress` tick-bounds to `unknown`, no permanent `Working` | UNTESTED | Do not infer transport behavior from WiFi loss alone |
| S-UI-06 | Status error / stale display (ST0-017/019) | FIZYCZNIE | Block backend response (e.g. suspend plugin loader briefly — only with consent) then recover | Initial failure shows error+retry (never blank); later failure keeps last-known with stale timestamp; resolved-error never renders as "disconnected"; reset/update/diagnostic resolved-`False` never shows Saved/Updating | UNTESTED | Screenshot each state |
| S-UI-07 | Gamepad focus + panel navigation | FIZYCZNIE | Navigate entire panel with gamepad only: all toggles, dropdowns, Custom DNS Apply/Cancel, Retry, banner buttons | Every control reachable and activatable; focus visible; no focus trap; no action requires touch/mouse | UNTESTED | Owner-only; note Steam client version |
| S-UI-08 | Dismount cancels timers (ST0-020) | FIZYCZNIE | Launch game (starts 3 s timer) → close panel before fire → (CEF console if available) | Zero backend IPC/state writes after dismount | UNTESTED | Fake-timer isolated test exists; device confirms no write |

## 12. Ownership edge cases (ST0-005/006 legacy)

| ID | Scenario (finding) | Kto | Kroki / komenda | Oczekiwany wynik (mierzalny) | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-OWN-01 | Legacy enabled-without-owner: enable→`unknown_owner`, disable→intent-only clear | SSH+FIZYCZNIE | (On a profile with pre-existing lock value but no recorded owner — matches inventory observation of BSSID-less profiles) enable then disable; SSH: profile fields + `unknown_owners` in status | Enable reports `unknown_owner` without claiming ownership; disable clears intent only, never touches foreign active profile | UNTESTED | Directly models the inventory anomaly (§1) |
| S-OWN-02 | Active-B + owner-A matrix | SSH+FIZYCZNIE | Lock A, connect B, disable; failed-`nmcli` variant (if safely inducible) retains ownership for retry (`nmcli_failed`, `dns_partial`, `relock_failed`) | Disable targets A; B untouched; failed removal keeps owner + intent, retry possible | UNTESTED | Needs 2 saved profiles; record SSIDs as aliases |
| S-OWN-03 | Pre-existing `priority 100` untouched | SSH | `grep -r autoconnect-priority` over repo (expect zero writers) + `nmcli` before/after any disable | No path writes priority; both profiles keep their existing `100` (neither added nor removed by plugin) | UNTESTED | Static grep + device observation |

## 13. Copy / claim spot-checks (ST0-021/022)

| ID | Scenario | Kto | Kroki | Oczekiwany wynik | Wynik | Uwagi |
| --- | --- | --- | --- | --- | --- | --- |
| S-LBL-01 | Band row label vs submitted value | FIZYCZNIE+SSH | Read band row; apply; SSH: `nmcli -f 802-11-wireless.band con show <uuid>` | Label promises NM `a` (5 GHz) only; `6GHz` non-offer stated; submitted value matches label | UNTESTED | 6 GHz HW absent → capability path UNTESTABLE |
| S-LBL-02 | CAKE description scope | FIZYCZNIE | Read CAKE row + README section | Local-egress-queue wording; no power claimed over other devices/AP/ISP bottleneck | UNTESTED | Text review, no measurement needed |

## 14. Out of scope for this device (explicitly not tested here)

| Area | Disposition |
| --- | --- |
| OLED / other handhelds / other distributions | No evidence in this fork; separate records required. Support claims stay qualified to LCD Stable. |
| Beta / Preview channel | Dropped by design (ST0-001/002/003/018). No Beta rows; Stable-only updater/installer. |
| 6 GHz band selection | No capable HW on this device; label agreement only (S-LBL-01). |
| Mesh / multi-AP roaming | No such setup available; BSSID-lock roaming benefit unproven. |
| iwd / non-installed backend route | Separate environment required (S-BE-02 UNTESTABLE here). |
| Connection Watchdog / in-game alerts | Not a feature of this candidate; never mark as tested. |
| Battery/throughput benefit | `UNMEASURED` unless controlled A/B runs with counts/durations are recorded. |
| Event-loop blocking, dispatcher races, adapter coverage | Explicitly open questions carried from the audit; not closed by this matrix. |

## 15. Run log (append per execution)

| Date (UTC) | Candidate | Row | Wynik | Evidence (scrubbed commands/outputs with aliases, screenshots without secrets) | Tester |
| --- | --- | --- | --- | --- | --- |
| 2026-10-17 | `a3bb26b` (ref only — not deployed; installed is legacy `0.11.6`) | PRE-FLIGHT-READONLY (not an S-* row; S-PRE-01/02 still UNTESTED) | OBSERVED (read-only, no verdict) | SSH (key `SteamDeck`, `IdentitiesOnly`) reachable; host answers, kernel matches inventory. Installed: legacy `wifi-optimizer` `0.11.6`, settings channel `beta`, `priority_set=true`. Active profile UUID-A (home SSID) == `last_connection_uuid`; BSSID-lock owner UUID-B sits on an INACTIVE saved profile (live ST0-005 orphan shape, untouched). Backend: `wpa_supplicant` active, `iwd` inactive; `99-valve-wifi-backend.conf` dated 2026-10-17, optimizer conf + dispatcher dated 2026-09-27. Live: power save `off`, root qdisc `cake` with non-template options (`triple-isolate nowash…` vs template `diffserv4 ack-filter`) — recorded, not reconciled. No `sudo` used; no writes performed. Full values to be re-checked per [device-recovery-runbook](../device-recovery-runbook.md) §1 at deploy time (not done here). | agent (remote) |
| 2026-10-17 | `a3bb26b` (ref only — not deployed) | S-PRE-02 (backup part) | OBSERVED (backup complete, verified; no verdict on candidate) | Backup dir `$BACKUP_DIR` on Deck (`wifi-optimizer-recovery-20261017-1154`, mode 700): `settings.json`, `last_enforced`, 4 system confs (NM/modprobe/valve-refonly/dispatcher-refonly), 2 `nmcli` listings; `system_snapshot.json` absent (legacy install, expected) and generic backend conf absent (device has none) — both recorded as NOTE, not fabricated. Manifest `SHA256SUMS` verified (`sha256sum -c`: all OK). Raw identifiers stay on Deck, mode 600, never committed. S-PRE-02 contract review still pending owner walkthrough. | agent (remote) + owner (sudo reads) |
| 2026-10-17 | `a3bb26b` deployed (path B: staged copy + loader restart) | S-DEPLOY-01 deploy + post-restart health | OBSERVED (deployed, healthy; no verdict on options yet) | Staged 8/8 files, hashes match local checkout; per-file copy to live dir (root-owned, via owner-typed sudo); `FILES-OK`; `systemctl restart plugin_loader` → `active`; new PID serves IPC (`call_plugin_method` in journal, no errors/tracebacks). Live after restart: power save `off`, `rmem_max 16777216`, `wmem_default 1048576`, root qdisc `cake` (options line differs from fresh-template expectation — recorded, not reconciled; needs follow-up, not a blocker), NM conf `wifi.powersave = 2`. Active profile UUID-A: bssid empty (lock enabled → drift expected, report-only), band empty (disabled → no drift), ipv6 `disabled` (matches intent → no drift), DNS from DHCP (disabled → skipped), `autoconnect-priority 100` (legacy, untouched per policy). Backend iwd `inactive` / wpa_supplicant `active`; driver params `Y`/`Y`. | agent (remote) + owner (sudo copy+restart) |
| 2026-10-17 | `a3bb26b` deployed | S-OPT-01 power-save round-trip + wake persistence | PASS (inferred from device state, owner-confirmed sequence) | Owner ran the requested ON/OFF toggle sequence before sleep: photo 14:10 shows ON+failed (PCIe `l0s_aspm` EACCES, honestly surfaced); `settings.json` (`power_save_disabled: false`, mtime 14:33, `last_applied` fresh) shows an explicit disable was saved afterwards; after wake the toggle reads OFF = correct persistence, no flag-flip by wake path (no code path writes `False` except explicit disable/reset; reset ruled out by `buffer_tuning_enabled: true` + band enabled + no defaults wipe). Band enabled during the same session with owner == active profile UUID-A = live ST0-005/006 ownership PASS. Backend log has no setter-invocation lines (not logged at this level) — sequence reconstructed from settings + photos + owner report. | owner (panel toggles + sleep/wake) + agent (settings/log reads) |
| 2026-10-17 | `a3bb26b` deployed | S-BE-05 persistent retry banner after remount | FAIL (product defect, mechanism confirmed in code) | Banner text is `errors.wifi_backend` set once at the terminal switch failure (`src/index.tsx:292-297`); `stopBackendPoll()` ends all polling, and the mount effect (371-394) only reconciles `backendSwitch`, never `errors.wifi_backend` — plus QAM caches the panel so remount may not even refire (comment at 373-374). Result: the 14:11 failure message renders forever despite a converged backend (desired `wpa_supplicant` == effective `wpa_supplicant`, internet works). Not stale-state confusion: freshly rendered from an unreconciled error key. Fix direction (follow-up package): reconcile `errors.wifi_backend` in `refreshStatus` success path when backend converged (desired==effective, no in-progress switch) — remount-independent; genuine divergences keep the error. Owner action: ignore the banner for now; do NOT click retry (would rerun a full transition pointlessly). | owner (panel photo after remount) + agent (code read) |
| 2026-10-17 | `a3bb26b` deployed | S-OPT-03 toggle reconnect contract (owner-reported) | PASS | Owner report: reconnect + long switch for IPv6-disable, 5 GHz band, BSSID-lock; instant, reconnect-free for auto-fix-on-wake, buffer tuning, power save, CAKE. Exactly the designed contract (per-profile NM writes cycle the radio; volatile/system-wide apply live). No silent no-op indicated (profiles verified changed where checked: band owner set, power persisted). | owner (panel toggles) |
| 2026-10-17 | `a3bb26b` deployed | S-RST-01 Reset to defaults (R1) | PASS | Owner clicked Reset Settings: panel reported no errors, WiFi dropped and returned in ~1–2 s. Remote verification: fresh defaults saved (`last_applied` bumped, owners cleared, `last_connection_uuid`/`priority_set` cleared); band `a` cleared on UUID-A (was owned) with conditional reconnect; legacy `ipv6.method=disabled` left on profile (no owner — per spec, honest remnant); live `iw` off; NM conf present (`wifi.powersave = 2`); dispatcher reinstalled (mtime reset time); backend untouched; plugin log shows clean `Settings reset to defaults` (no errors). Post-reset `power_save_disabled=false` is owner toggling after reset (disable works, re-enable hits the known `l0s_aspm` restriction — S-OPT-02), not a reset write. | owner (panel Reset) + agent (settings/profile/live/log reads) |
| 2026-10-17 | `a3bb26b` deployed | S-PRE-03 pre-reset backup refresh | OBSERVED (verified, no verdict) | Pre-mutation backup (11:54) went stale after panel testing (band enabled + owner, toggles flipped). Refreshed non-sudo state into new dir `wifi-optimizer-recovery-20261017-1243` (mode 700): `settings.json`, `system_snapshot.json` (now EXISTS — created by corrected code on first enable), `last_enforced`, `nmcli` profile list + active-profile keys; manifest verified (`sha256sum -c`: all OK). `/etc` confs unchanged since 11:54 backup except possibly NM power conf (power toggled) — sudo refresh deferred to reset window. Raw identifiers on Deck only, mode 600. | agent (remote) |
| 2026-10-17 | `a3bb26b` deployed | S-BE-04 backend repair retry on converged backend | FAIL (product defect, system healthy — see cause) | Owner clicked "Retry switch to wpa_supplicant" on an already-correct backend. Worker ran full transition (helper `write_config` rc=0, units restarted, NM SIGTERM→restart PID 14155, wlan0 deauth→reconnect); final verification read effective `None` → `failed` + rollback attempt → "rollback incomplete: effective is unknown". Post-hoc state CONVERGED (desired `wpa_supplicant` from valve conf, `is-active` wpa `active` / iwd `inactive`, internet works). Root cause (probable): single 3 s-timeout effective sample raced the service/NM restart (D-Bus contention / `activating` state) → `unknown` → false divergence; rollback verify hit the same window. Same mechanism explains the 14:06 boot "Backend inconsistency" log right after the deploy restart. Fix direction (follow-up package, not this session): bounded retry of the effective read in worker/rollback verification (status poll stays single-sample); distinguish transient-unknown from diverged. Owner action: do NOT re-click retry (converged → `already_set` no-op now). | owner (panel retry) + agent (journal+service reads) |
| 2026-10-17 | `a3bb26b` deployed | S-OPT-02 PCIe ASPM partial writability | PARTIAL (device restriction, surfaced truthfully) | Panel toggle shows `failed` with `[Errno 13] Permission denied` on `.../0000:03:00.0/link/l0s_aspm` — as ROOT (plugin runs as root, confirmed via process list). Sibling link files (`l1_*`) and `power/control` wrote fine (mtimes updated). Interpretation: this link does not support L0s writes (firmware restriction), not a privilege bug. Current code treats any unwritable link file as toggle failure. Fix direction (follow-up): per-file verify-after-write — report only files whose content differs from desired; treat unsupported-but-unchanged as skip-with-note, not failure. | owner (panel toggle) + agent (perms/process/log reads) |

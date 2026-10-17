# clean_env default for system binaries (S-BE-06 mechanism fix) — design

Date: 2026-10-17. Baseline: `5d48ded` (main). Proven on device
(matrix row S-BE-06, session branch `origin/codex/st0-validation-run`):
`plugin_loader` is a PyInstaller bundle (`/tmp/_MEI*`); children inherit its
`LD_LIBRARY_PATH`, under which `/usr/bin/systemctl` dies with
`libcrypto.so.3: version OPENSSL_3.4.0 not found (required by
libsystemd-shared)` — empty stdout, poisoned reads. Same root cause already
known for `curl`/`bash` children. This package generalizes the existing
`clean_env` mechanism instead of adding per-binary exceptions.
Stage 0 stays open; no Stable, no version bump, no Watchdog. No DNS work.

## Intent

- No system binary spawned by the plugin ever sees Decky's bundled
  `LD_LIBRARY_PATH`. Opt-out exists but must be justified per call site.
- The fix is systemic (one default), verified by mechanism tests + a
  call-site audit, not by re-testing every feature on device.

## Non-goals / anti-goals

- No behavior change for correctly-working binaries (`nmcli`/`iw` today);
  stripping is a no-op where the bundled path shadows nothing.
- No new IPC, no frontend changes, no `dist` rebuild (no `src` touched).
- No `LD_LIBRARY_PATH` manipulation beyond stripping that one variable.

## Decisions (binding)

- **D1 — default flip.** `_run_cmd(..., clean_env: bool = True)`. Every
  existing explicit `clean_env=True` stays untouched (harmless redundancy, no
  churn). An explicit `clean_env=False` requires a trailing comment naming the
  Decky-provided library the child needs; expected count is zero — if the audit
  finds a site that needs bundled env, it is listed in the spec addendum with
  rationale instead of silently kept.
- **D2 — call-site audit (all 61 sites).** Each `_run_cmd(` call is classified:
  absolute-path system binary (`/usr/bin/*`, `/usr/sbin/*`, helper paths) →
  inherits the safe default; anything else (shell wrappers, plugin-relative
  paths — expected none) → explicit decision recorded in the commit message.
  Particular attention: `BACKEND_HELPER` invocations, `modprobe` path
  fallbacks (`/usr/bin`→`/usr/sbin`), `systemctl restart plugin_loader` in the
  updater path (same poisoning, latent), `uname`, `tc`/`ip`/`sysctl`/`iw`/`nmcli`.
  Addendum: updater/download/restart sites KEEP their explicit `clean_env=True`
  deliberately (defense in depth at the highest-risk sites AND required by
  `scripts/check_delivery.py:388-395`, which asserts the literal — do NOT
  "clean up" the redundancy, it would break `check-syntax`/CI).
- **D3 — mechanism tests.** Fixture (fail-closed builtins + mocked
  `subprocess.run` capturing the `env` kwarg): with poisoned `os.environ`
  (`LD_LIBRARY_PATH=/tmp/_MEI0000` + sentinel), `clean_env` default path must
  pass an env WITHOUT the variable; explicit `clean_env=False` must pass it
  through. Static tests: (a) signature default is `True` (AST); (b) zero
  unjustified opt-outs in BOTH forms — keyword `clean_env=False` AND positional
  `False` (4th argument in `to_thread(..., _run_cmd, ...)` wrappers, 3rd argument
  in direct `self._run_cmd(...)` calls — the codebase passes the flag
  positionally);
  (c) call-site count assertion (61) so audit completeness is
  machine-falsifiable.
- **D4 — docs.** `AGENTS.md` gotcha generalized: ALL system-binary children
  (proven: `curl`, `bash`, now `systemctl` with the exact symbol error), not
  just curl/bash. Findings device-note: S-BE-06 mechanism fix landed, **device
  confirmation pending — S-BE-06 stays open** per the Stage 0 rule (static
  evidence never closes a finding; re-validation on the candidate follows the
  device protocol). No "closure" language anywhere for S-BE-06.
## Acceptance

- Poisoned-parent fixture: stripped env for default/True, passthrough only for
  explicit False.
- Static: default `True`; no unjustified `False`.
- Audit table (61 sites) committed in the plan's verification record or commit
  message; full suite green; `check-syntax` green.

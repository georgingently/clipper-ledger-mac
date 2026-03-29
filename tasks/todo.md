## Checklist

- [x] Create branch from latest `origin/main`
- [x] Refresh `research.md`
- [x] Refresh `plan.md`
- [x] Replace the sales quick-entry form with a full detail section
- [x] Load selected sales records into the detail section automatically
- [x] Keep create/update/delete wired to `SREG41`
- [x] Harden menu activation against packaged slot aborts
- [x] Run targeted offscreen verification
- [x] Run Python syntax checks
- [ ] Commit and push branch changes
- [ ] Complete PR/merge/cleanup flow
- [ ] Update `tasks/lessons.md` if needed

## Execution Notes

- Branch: `fix/sales-detail-crash`
- Branch base: `origin/main` @ `044c575`
- The current sales screen still uses a minimal inline form and does not expose a full detail section on selection.
- The packaged crash trace still exits through a Qt slot proxy on the main thread, so menu activation needs an exception guard in addition to the sales UI fix.
- The new macOS crash report narrows the remaining packaged failure to a Python exception escaping `keyPressEvent`, so sales function-key handling must avoid raw unguarded Qt key dispatch.
- The follow-up packaged crash identifies deleted `_ReturnFilter` wrappers during sales detail reload, so dynamic item-row event filters must be detached before rebuilding the selected bill lines.

## Review

- `python3 -m py_compile georgin_app.py models/dbf_layer.py`
- `QT_QPA_PLATFORM=offscreen python3 ... instantiate SalesModule, inject a sample sales record, select the row, and verify the detail widgets populate`
- `QT_QPA_PLATFORM=offscreen python3 ... instantiate DosMenuPage with stub handlers, force a raised handler, and verify the activation guard catches it`
- `QT_QPA_PLATFORM=offscreen python3 ... call SalesModule.keyPressEvent(...) for F2/F4/F5/F9/F10 and verify the wrapped sales actions execute without raising`
- `QT_QPA_PLATFORM=offscreen python3 ... repeatedly open/reset/reload sales bill details and verify dynamic item-row filters remain valid after rebuilding the line grid`

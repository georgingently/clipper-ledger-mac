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

## Review

- `python3 -m py_compile georgin_app.py models/dbf_layer.py`
- `QT_QPA_PLATFORM=offscreen python3 ... instantiate SalesModule, inject a sample sales record, select the row, and verify the detail widgets populate`
- `QT_QPA_PLATFORM=offscreen python3 ... instantiate DosMenuPage with stub handlers, force a raised handler, and verify the activation guard catches it`

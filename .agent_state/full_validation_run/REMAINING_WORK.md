# Remaining Work

## Completed
- [x] Environment setup (uv sync --locked)
- [x] Unit tests (1876 passed)
- [x] Integration tests (passed)
- [x] E2E tests (passed)
- [x] Full test suite (1876 passed)
- [x] Lint (make lint)
- [x] Typecheck (make typecheck)
- [x] Gates: gate0, gate1, gate2, gate3-code, gates (all PASSED)

## In Progress
- [ ] make run-regime-b (~16-20 h, 40 cells) — STARTED 2026-06-07T04:55

## Completed
- [x] make diagnostic-regime-a ✓
- [x] make diagnostic-regime-b ✓
- [x] make diagnostic-regime-c ✓
- [x] make diagnostic-regime-d ✓
- [x] make status (after diagnostics) ✓
- [x] make sweep-dry-run ✓
- [x] make run-regime-a ✓ (50 cells, ~4h)
- [x] make status && make audit-results (after regime A) ✓
  - Fix 9 applied: audit warnings cleaned up (0 FAIL, 102 INFO/WARNING)

## Pending (was already pending)
- [ ] make run-regime-b (~16-20 h, 40 cells)
- [ ] make status && make audit-results (after regime B)
- [ ] make run-regime-c (~12-16 h, 180 cells)
- [ ] make status && make audit-results (after regime C)
- [ ] make run-regime-d
- [ ] make status && make audit-results (after regime D)
- [ ] make audit-results (full)
- [ ] make build-stats
- [ ] make build-tables
- [ ] make build-figures
- [ ] make docs
- [ ] Read paper + planning docs + results
- [ ] Produce final scientific summary (AutoPrompt Section 23)

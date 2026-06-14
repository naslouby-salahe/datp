# Human Notes (from Salahe, 2026-06-06)

## ⚠️ E2E Test Concern: CheckpointProtocolMode.DISABLED

The E2E test fixes applied (disabling checkpoint protocol in all E2E fixtures) are considered
**too aggressive**. E2E tests should mirror real production runs as closely as possible.

**The concern:**
- In production, checkpoint protocol will be ENABLED by default.
- Disabling it in E2E fixtures means E2E tests never exercise the real artifact layout.
- This is papering over the mismatch rather than fixing it properly.

**Expected correct approach:**
- E2E tests should have checkpoint protocol ENABLED (matching real runs).
- The E2E tests should be updated to expect and resolve checkpoint-protocol artifact paths.
- Only unit/integration tests that explicitly test non-checkpoint behavior should disable it.

**Action required when you reach the audit or quality phase:**
- Review the E2E checkpoint protocol DISABLED patches.
- Determine if the E2E tests can be updated to run with checkpoint protocol ENABLED.
- If so, fix them properly instead of keeping the DISABLED workaround.
- Document your decision in FAILURES_AND_FIXES.md.

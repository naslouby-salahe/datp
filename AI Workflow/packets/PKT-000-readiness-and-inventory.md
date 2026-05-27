# PKT-000 — Readiness and Inventory

## Packet identity

| Field | Value |
|---|---|
| Packet ID | `PKT-000` |
| Title | Readiness and inventory |
| Owner/tool | VS Code Copilot + DeepSeek V4 Pro |
| Status | `READY` |
| Created | Initial workflow setup |
| Last updated | `TODO` |

## Purpose

Initialize the workflow from the real repository state before any broad refactoring starts.

## Scope

### In scope

- verify repository root;
- verify current git status;
- verify tool availability and versions;
- inspect active project docs enough to confirm scientific anchors;
- initialize/update workboard, audit, map, pattern ledger, move plan, scientific audit, and test impact map;
- create next packet from real findings.

### Out of scope

- code refactoring;
- package restructuring;
- training runs;
- full e2e tests;
- expensive model escalation;
- Sonar setup or Sonar blocking.

## File locks

| File/directory | Reason | Lock owner | Status |
|---|---|---|---|
| `AI Workflow/*` | Initial workflow setup and status updates. | DeepSeek V4 Pro | `PENDING` |

## Required commands

```bash
pwd
git status --short
python --version
python -m pytest --version
python -m ruff --version
python -m pyright --version || pyright --version
cs --version || true
```

Optional checks only if safe:

```bash
python -m ruff check src/datp tests
python -m pyright
```

## Required file updates

- `REFACTOR_WORKBOARD.md`: update active packet, tool reality, locks, next packet.
- `AUDIT_CODE.md`: replace AUD-000 with real initial findings or explicit no-finding-yet entries.
- `REFACTOR_MAP.md`: add first observed package ownership notes.
- `PATTERN_LEDGER.md`: convert suspected patterns to confirmed where evidence exists.
- `MOVE_PLAN.md`: add no moves unless supported by real inspection.
- `SCIENTIFIC_CONTRACT_AUDIT.md`: record initial scientific risks and doc anchors.
- `TEST_IMPACT_MAP.md`: record available test scopes and deferred checks.

## Acceptance criteria

- [ ] Repository root confirmed.
- [ ] Git status recorded.
- [ ] Tool versions recorded.
- [ ] Heavy work avoided.
- [ ] Workflow files updated from real evidence.
- [ ] Next packet created or selected.
- [ ] No production code changed.
- [ ] Session handoff written.

## Re-audit trigger

Re-audit PKT-000 after PKT-001 completes because the repository map may change readiness assumptions.

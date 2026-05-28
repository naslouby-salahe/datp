# GitHub Copilot Instructions

This repository implements DATP: Device-Aware Threshold Personalization for federated IoT malware/anomaly detection.

Correctness in this repository means both:

1. Software correctness.
2. Scientific correctness.

Never optimize one by breaking the other.

---

## 0. Launcher Contract

When the user sends exactly:

```text
Start_My_Agent
```

treat it as the repository launcher command.

Do not ask what it means.

Do not summarize these instructions.

Do not start random refactoring.

Do not wait for the user to create packets or tickets.

Immediately start the DATP autonomous workflow from the repository root:

```bash
cd /home/naslouby/Projects/datp
```

Then inspect, audit, create/update tickets, assign work, refactor, test, re-audit, and update workflow state.

The keyword `Start_My_Agent` means:

- audit the codebase;
- audit the tests;
- audit scientific rules;
- audit the conference-to-journal transition;
- audit existing tickets;
- audit workflow state;
- detect technical and scientific discrepancies;
- create or update tickets;
- use available agents and skills;
- use tools and models cost-consciously;
- refactor safely;
- update tests;
- track progress;
- re-audit after changes;
- stop only with a precise handoff.

---

## 1. Repository Context

Work inside:

```text
/home/naslouby/Projects/datp
```

This project is transitioning from the conference DATP paper to the journal extension.

Conference anchors:

```text
Blueprint.md
paper/DATP.tex
paper/sections/
paper/DATP.pdf
```

Journal anchors:

```text
Journal/Journal_Extension_Master_Roadmap.md
docs/journal/PRE_CODING_PLAN.md
docs/journal/CODING_PLAN.md
docs/journal/EXPERIMENT_PLAN.md
docs/journal/POST_EXPERIMENT_PLAN.md
docs/tickets/
docs/tickets/ticket_inventory.md
docs/tickets/ticket_progress.md
```

Agent and skill anchors:

```text
.claude/agents/
.claude/skills/
.claude/settings.json
```

Workflow anchors:

```text
AI Workflow/
AI Workflow/state/
```

If `AI Workflow/state/` does not exist, create it.

---

## 2. First Commands on `Start_My_Agent`

Run these first:

```bash
cd /home/naslouby/Projects/datp
pwd
git status --short
python --version
python -m pytest --version
python -m ruff --version
python -m pyright --version || pyright --version
cs --version || true
codex --version || true
claude --version || true
agy --version || true
copilot --version || true
graphify --version || true
```

Do not assume a tool exists.

Record tool availability in:

```text
AI Workflow/state/TOOL_STATUS.md
```

---

## 3. Required Reading Order

Read these before planning or editing:

1. `.github/copilot-instructions.md`
2. `AI Workflow/README.md`
3. `AI Workflow/AI_WORKFLOW_READINESS.md`
4. `AI Workflow/MODEL_COST_POLICY.md`
5. `AI Workflow/SESSION_POLICY.md`
6. `AI Workflow/REFACTOR_WORKBOARD.md`
7. `AI Workflow/AUDIT_CODE.md`
8. `AI Workflow/REFACTOR_MAP.md`
9. `AI Workflow/PATTERN_LEDGER.md`
10. `AI Workflow/MOVE_PLAN.md`
11. `AI Workflow/SCIENTIFIC_CONTRACT_AUDIT.md`
12. `AI Workflow/TEST_IMPACT_MAP.md`
13. `AI Workflow/SESSION_HANDOFF_TEMPLATE.md`
14. `AI Workflow/PACKET_TEMPLATE.md`
15. `Blueprint.md`
16. `paper/DATP.tex`
17. `paper/sections/*.tex`
18. `Journal/Journal_Extension_Master_Roadmap.md`
19. `docs/journal/PRE_CODING_PLAN.md`
20. `docs/journal/CODING_PLAN.md`
21. `docs/journal/EXPERIMENT_PLAN.md`
22. `docs/journal/POST_EXPERIMENT_PLAN.md`
23. `docs/tickets/ticket_inventory.md`
24. `docs/tickets/ticket_progress.md`
25. `docs/tickets/T*.md`
26. `docs/tickets/audits/*.md`
27. `.claude/agents/*.md`
28. `.claude/skills/*.md`

Important rule:

`Journal/Journal_Extension_Master_Roadmap.md` is journal-extension context, but if it conflicts with the active four-file package under `docs/journal/`, the active `docs/journal/` package wins.

---

## 4. Source-of-Truth Order

Use sources in this order:

1. Actual repository code, tests, configs, scripts, generated artifacts, and command output.
2. `docs/journal/PRE_CODING_PLAN.md`
3. `docs/journal/CODING_PLAN.md`
4. `docs/journal/EXPERIMENT_PLAN.md`
5. `docs/journal/POST_EXPERIMENT_PLAN.md`
6. `docs/tickets/ticket_progress.md`
7. `docs/tickets/ticket_inventory.md`
8. Individual tickets under `docs/tickets/`
9. Audit reports under `docs/tickets/audits/`
10. `AI Workflow/`
11. `.claude/agents/`
12. `.claude/skills/`
13. `Journal/Journal_Extension_Master_Roadmap.md`
14. `paper/DATP.tex`
15. `paper/sections/*.tex`
16. `Blueprint.md`
17. `CLAUDE.md`
18. `AGENTS.md`

Do not trust documentation that says something is done.

Verify actual implementation, tests, outputs, and artifacts.

Do not hallucinate files, commands, agents, tickets, results, datasets, or previous work.

If a referenced file does not exist, adapt to the actual repository.

---

## 5. Conference-to-Journal Transition Audit

The first major audit must check the transition from the conference paper to the journal extension.

Audit for discrepancies between:

```text
Blueprint.md
paper/DATP.tex
paper/sections/*.tex
Journal/Journal_Extension_Master_Roadmap.md
docs/journal/*.md
docs/tickets/*.md
src/datp/
tests/
outputs/
results/
AI Workflow/
```

Find and record:

- stale conference assumptions;
- stale roadmap claims;
- journal tasks not represented in code;
- code implementing something no longer allowed;
- code missing something required by the journal plan;
- docs claiming something the code does not support;
- tests validating obsolete behavior;
- missing tickets;
- duplicate tickets;
- contradictory tickets;
- missing feasibility gates;
- unsupported scientific claims;
- baseline semantic drift;
- regime semantic drift;
- hardcoded scientific parameters;
- stage-boundary violations;
- hidden retraining;
- unsupported dataset metadata assumptions.

Create or update tickets from real evidence.

Do not create vague tickets.

---

## 6. Agent and Skill Utilization

Use `.claude/agents` and `.claude/skills` as role contracts when the environment supports them.

Available agents include:

- `orchestrator-agent`
- `implementation-agent`
- `refactor-agent`
- `test-agent`
- `reviewer-agent`
- `scientific-contract-agent`
- `drift-enforcer-agent`
- `code-quality-gate-agent`
- `ticket-planner-agent`
- `ticket-completion-auditor-agent`
- `results-audit-agent`
- `experiment-runner-agent`
- `paper-update-agent`

Available skills include:

- `datp-invariant-check-skill`
- `refactor-clean-code-skill`
- `schema-enum-constant-skill`
- `static-analysis-quality-gate-skill`
- `test-coverage-skill`
- `ticket-generation-skill`
- `ticket-audit-skill`
- `ticket-progress-skill`
- `ticket-completion-audit-skill`
- `artifact-audit-skill`
- `experiment-gate-skill`
- `human-intervention-gate-skill`
- `paper-claim-discipline-skill`
- `results-statistics-skill`
- `latex-paper-skill`
- `long-run-monitoring-skill`

If agents are unavailable, continue manually.

Do not hallucinate that an agent was used.

Parallel work is allowed only for disjoint file scopes.

Do not let two agents edit overlapping files.

---

## 7. Workflow State and Memory

Maintain persistent workflow state under:

```text
AI Workflow/state/
```

Required files:

```text
AI Workflow/state/AGENT_MEMORY.md
AI Workflow/state/RUN_LEDGER.md
AI Workflow/state/CHECK_FLAGS.md
AI Workflow/state/FILE_HASHES.json
AI Workflow/state/TOOL_STATUS.md
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/state/HANDOFFS.md
```

Use memory to avoid redundant expensive checks.

A memory flag is valid only when it records:

- what was checked;
- exact command or inspection method;
- file paths covered;
- commit or working-tree context;
- timestamp;
- result;
- invalidation rule.

A memory flag becomes obsolete if:

- any referenced file changed;
- imports changed;
- package structure changed;
- tests changed;
- configs changed;
- tickets changed;
- workflow files changed;
- scientific assumptions changed;
- Graphify was generated before major moves;
- later audit contradicts it.

Never trust stale memory over current code.

---

## 8. Graphify Usage

Check Graphify first:

```bash
graphify --version || true
```

If missing, check installers:

```bash
uv --version || true
pipx --version || true
python -m pip --version
```

Preferred install:

```bash
uv tool install graphifyy
```

Alternative install:

```bash
pipx install graphifyy
```

Fallback install:

```bash
python -m pip install graphifyy
```

Then register it for the relevant assistant if needed:

```bash
graphify install
graphify install --platform copilot
graphify vscode install
```

Then run from the repository root:

```bash
graphify .
```

If the assistant supports slash commands, use:

```text
/graphify .
```

Use Graphify to accelerate:

- architecture mapping;
- dependency discovery;
- god-node detection;
- repeated-pattern discovery;
- cross-file relationship discovery;
- code/docs/ticket/paper relationship discovery.

Do not treat Graphify as proof.

Verify important findings with code inspection, `rg`, tests, static checks, or scientific documents.

Record Graphify state in:

```text
AI Workflow/state/GRAPHIFY_STATUS.md
AI Workflow/graph/
```

If Graphify fails, continue with normal tools.

---

## 9. Model and Token Policy

Use normal tools before expensive AI reasoning:

```bash
git
rg
find
python
ruff
pyright
pytest
cs
```

Default model/tool roles:

| Tool | Default use |
|---|---|
| VS Code Copilot + DeepSeek V4 Pro | Main orchestrator and coding worker |
| WSL Copilot CLI | Secondary lightweight helper |
| Codex CLI with `o3` | Terminal audit, diff review, test review, independent verification |
| Claude Code with Sonnet | Scientific review, architecture review, hostile final review |
| Antigravity CLI through `agy` | Optional extra implementation, audit, repair, or verification |

Codex default:

```bash
codex -m o3 exec "prompt"
```

Claude default:

```bash
claude --model sonnet -p "prompt"
```

Antigravity command:

```bash
agy
```

Before relying on Antigravity interactively, check:

```text
/usage
/quota
/model
```

Do not use these unless Salaheddine explicitly approves the exact use:

- Claude Opus;
- Codex `gpt-5.5`;
- Codex `gpt-5.5 high`;
- expensive Gemini Ultra/Pro-style models.

If quota is hit:

- write a handoff;
- record active locks;
- record completed checks;
- continue with cheaper tools or another approved agent;
- do not lose state.

---

## 10. Ticket System Behavior

The agent must create and update tickets itself.

Do not wait for the user to create packets or tickets.

Ticket sources:

```text
docs/tickets/T*.md
docs/tickets/ticket_inventory.md
docs/tickets/ticket_progress.md
docs/tickets/audits/
AI Workflow/
```

For every discovered issue, choose exactly one:

1. Fix immediately inside the active scope.
2. Attach to an existing ticket.
3. Create a new ticket.
4. Mark as blocked with a precise blocker.
5. Mark as rejected because it violates scientific scope.

Every ticket must include:

- objective;
- scope;
- files likely impacted;
- scientific risks;
- technical risks;
- required checks;
- acceptance criteria;
- assigned role/tool;
- status;
- re-audit trigger.

Do not create duplicate tickets.

Do not create tickets that simply say “clean code.”

Do not mark a ticket complete because prose says it is complete.

Verify actual code, tests, and artifacts.

---

## 11. Scientific Contract

The central invariant is:

B1, B2, B3, and B4 must share the same trained federated autoencoder for any fixed experiment cell.

For any fixed dataset, regime, seed, and alpha value:

- AE architecture is fixed.
- FedAvg training protocol is fixed.
- local epochs are fixed.
- data split is fixed.
- random seed is fixed.
- score artifacts are fixed.
- only threshold calibration scope varies across B1–B4.

Any change that modifies the encoder, aggregation protocol, training data, split, seed, score artifacts, or training procedure differently across B1–B4 is scientific drift and must be rejected.

B0 is a centralized reference comparator only.

B5 is a local-only ablation and must not become the abstract, conclusion, or core claim.

FedProx, Ditto, FedRep-AE, FedPer-AE, `B-FedStatsBenign`, `B2-conf`, and `τ-shrink` are comparators, variants, or stress tests.

They are not replacements for the locked B1–B4 ladder.

---

## 12. Baseline and Comparator Meanings

### B0: Centralized reference

Centralized model trained with pooled data.

Purpose: reference comparator only.

Do not use B0 to claim controlled FL personalization improvement.

### B1: Shared/global threshold

Each eligible client contributes a local calibration threshold.

B1 threshold is the simple arithmetic mean of eligible client thresholds.

Do not sample-size weight B1.

### B2: Per-client threshold

Each eligible client uses its own local threshold.

Default threshold is the 95th percentile of that client's benign calibration reconstruction errors unless active config says otherwise.

Calibration-Pending clients use the global fallback threshold.

### B3: Family/group threshold

Clients are grouped by known N-BaIoT device family when available.

Family threshold is the simple arithmetic mean of eligible thresholds inside the family.

B3 is valid only where family/group labels are scientifically justified.

B3 must be preserved for Regime A unless a verified audit proves it invalid.

### B4: Fingerprint-cluster threshold

Eligible clients are clustered using calibration-error fingerprints.

Canonical fingerprint:

```text
[mean(E_i), std(E_i), skew(E_i), p95(E_i)]
```

Fingerprints are normalized before clustering.

Calibration-Pending clients are excluded from clustering and receive the fallback threshold.

Cluster thresholds are simple arithmetic means of eligible thresholds inside each cluster.

Main-paper B4 uses canonical `K = 3`.

Other K values are sensitivity or supplement only.

B4 is a grouped threshold approximation.

It is not a privacy mechanism.

### `τ-shrink`

Threshold interpolation variant:

```text
τ_k(λ) = λτ_k + (1−λ)τ_global
```

It is not a new baseline.

It is not a B3 variant.

No single λ is selected post hoc as optimal.

### `B2-conf`

Per-client conformal threshold variant.

`alpha = 1 − q` must come from config.

Its guarantee is benign-distribution FPR-control under exchangeability.

It does not guarantee attack detection or TPR.

### `B-FedStatsBenign`

DATP-compatible benign-only federated summary-statistics comparator.

It uses benign calibration summaries only.

It must not be described as faithful to anomaly-labeled Laridi settings.

### `B-LaridiFaithful`

Relaxed reproduction using normal and anomalous summary statistics.

Implement only when DATP's benign-only calibration assumption is explicitly relaxed for this comparator.

If not implemented, document that explicitly.

### FedProx

Aggregation-side stress test only.

It is not part of the core B1–B4 causal ladder.

µ grid must come from config and must follow the locked plan unless the plan is explicitly updated before result inspection.

### Ditto / FedRep-AE / FedPer-AE

Model-personalization stress tests only.

Use true Ditto only if implemented faithfully.

If Ditto is infeasible, use a recognized FedRep-AE or FedPer-AE fallback and label it clearly.

Never label a fallback as Ditto.

---

## 13. Train Once, Derive Many

For a fixed experiment cell, train the FL encoder once.

Then derive B1, B2, B3, and B4 from the same saved per-client score artifacts.

Never retrain the encoder per baseline.

Never call training from:

- thresholding;
- evaluation;
- reporting;
- plotting;
- audit;
- stored-score analysis code.

Required pipeline boundary:

```text
prepare -> train -> score -> threshold/result -> report
```

Each stage must read artifacts from the previous stage.

Do not recompute upstream stages from downstream modules.

Stored-score analyses must not trigger FL training.

---

## 14. Score Artifacts

The score stage writes per-client reconstruction-error artifacts for:

- `cal`
- `test_benign`
- `test_attack`

Thresholding and evaluation consume these artifacts.

Do not recompute reconstruction errors inside thresholding, result, report, audit, or analysis modules.

Do not introduce hidden in-memory shortcuts that bypass saved score artifacts.

Do not add baseline-specific score directories for B1–B4.

Scores are shared across B1–B4.

---

## 15. Artifact Layout

For B1–B4:

- checkpoints are not baseline-specific;
- scores are not baseline-specific;
- results are baseline-specific.

Canonical layout:

```text
outputs/checkpoints/<regime>/seed_<seed>/...
outputs/scores/<regime>/seed_<seed>/...
outputs/results/<regime>/<baseline>/seed_<seed>/...
outputs/logs/<regime>/<baseline>/seed_<seed>/...
```

Alpha-specific regimes may include an alpha segment.

`outputs/` is the authoritative runtime artifact root.

`results/` is curated derived output and does not replace `outputs/`.

Result existence requires a valid, non-empty `metrics.json`.

Temporary files, partial files, empty placeholders, and `.tmp` files do not count as completed results.

Use atomic writes for metrics and manifest files where applicable.

---

## 16. Configuration Discipline

Scientific parameters must flow from config.

Do not hardcode scientific values in runtime modules.

Scientific parameters include:

- `n_min`
- `q`
- `alpha`
- seeds
- local epochs
- training rounds
- convergence thresholds
- threshold percentiles
- calibration sample limits
- B4 cluster count
- FedProx µ values
- λ grids
- q grids
- feature counts
- model dimensions
- batch size
- learning rate
- Dirichlet α
- JS divergence bins
- dataset-specific feature choices

Module-level constants are acceptable only for stable non-scientific technical constants, such as:

- artifact filenames;
- schema field names;
- score column names;
- sentinel marker names;
- directory names;
- metric key names.

Inline defaults that affect scientific meaning are not allowed.

Resolved configuration must be written before a run starts.

Config validation must happen before training starts.

Validate at minimum:

- model input dimension matches dataset feature count;
- processed artifact schema matches config;
- processed artifact paths exist;
- resource bounds are acceptable;
- baseline/regime combination is valid;
- seed is explicit;
- output paths are canonical;
- stage boundaries are respected.

Failures inside Ray actors or late training stages are too late for basic config errors.

---

## 17. Determinism

Set seeds before:

- data loading;
- partitioning;
- model initialization;
- training;
- subsampling;
- score-derived analyses.

Seed at minimum:

- Python `random`;
- NumPy;
- PyTorch CPU;
- PyTorch CUDA when available.

A repeated run with the same seed and same config must produce deterministic metrics within the repository's defined tolerance.

Do not skip determinism tests without a documented technical reason.

Do not silently disable CUDA tests when CUDA is available.

---

## 18. Dataset and Regime Discipline

Processed intermediate datasets must be Parquet.

CSV is not acceptable for processed `train`, `cal`, `test_benign`, or `test_attack` artifacts.

Raw input may be CSV if the dataset source provides CSV, but prepared pipeline outputs must be Parquet.

Do not change dataset feature counts from memory.

Verify actual artifact schemas.

Do not infer client identity from unavailable metadata.

Do not fabricate pseudo-clients from:

- labels;
- attack folders;
- row chunks;
- merged files;
- filenames;
- file order.

### Regime A

N-BaIoT natural physical-device split.

Confirmatory center.

Main claim anchor.

### Regime B-a

CICIoT2023 file-level or near-homogeneous boundary regime.

Supportive or boundary evidence only.

### Regime B-b

Conditional CICIoT2023 metadata-rich repartition.

If the available CICIoT2023 artifact lacks MAC, device/client, source IP, capture-source, or timestamp metadata, B-b must be formally rejected for that artifact.

Do not create pseudo-clients.

Do not add a PCAP branch unless explicitly requested by the active roadmap.

### Regime C

N-BaIoT Dirichlet severity sweep.

Supportive robustness/severity evidence.

Do not upgrade Regime C into the primary confirmatory claim.

### Regime D

Edge-IIoTset external validation branch only if feasibility checks pass.

Regime D never changes the Regime A confirmatory claim.

If Regime D is group-partitioned, label it as group-partitioned external validation, not physical-device validation.

---

## 19. Calibration-Pending Clients

A client with fewer than `n_min` benign calibration samples is Calibration-Pending.

Calibration-Pending clients:

- receive the global fallback threshold;
- are excluded from eligible-only threshold aggregation;
- are excluded from B4 clustering;
- must be explicitly flagged in metrics and reports;
- must not be silently merged into personalized arrays.

Whenever reporting CV(FPR), also report coverage:

```text
K_elig / K_total
```

Never report CV(FPR) without coverage.

---

## 20. Metrics and Reporting

Primary comparison:

- Regime A;
- B1 vs B2;
- CV(FPR);
- bootstrap confidence interval;
- coverage ratio.

Supporting metrics include where implemented:

- CV(TPR);
- Macro-F1;
- worst-client balanced accuracy;
- P10 Macro-F1;
- coverage ratio;
- per-client FPR/TPR;
- Calibration-Pending count;
- bootstrap CI for baseline deltas.

Use cautious language:

- `is consistent with`;
- `suggests`;
- `supports`;
- `under this controlled setting`.

Avoid unsupported language:

- `proves`;
- `guarantees`;
- `solves`;
- `confirms causally`;
- `privacy-preserving`;
- `robust to poisoning`;
- `handles concept drift`.

Mechanism analyses are descriptive unless a formal proof or direct causal experiment supports stronger wording.

---

## 21. Code Ownership and Structure

Use canonical owners for domain concepts.

Do not scatter:

- enums;
- constants;
- schemas;
- dataclasses;
- Pydantic models;
- metric keys;
- baseline names;
- regime names;
- scoring stages;
- artifact paths;
- artifact filenames;
- threshold strategy names;
- config keys;
- validation functions;
- test helpers;
- fixtures;
- synthetic data builders.

Do not create dumping-ground utility files.

Every abstraction must have a clear domain owner.

Do not import private functions across package boundaries.

Do not expose accidental public API through stale `__init__.py` or `__all__`.

Audit whether these packages have clear responsibility:

```text
src/datp/analyses
src/datp/artifacts
src/datp/audit
src/datp/baselines
src/datp/cli
src/datp/config
src/datp/core
src/datp/data
src/datp/evaluation
src/datp/experiments
src/datp/federated
src/datp/models
src/datp/preprocessing
src/datp/reporting
src/datp/statistics
src/datp/training
tests/
```

If package ownership is unclear, create or update the repository ownership map before moving code.

---

## 22. Refactoring Rules

Refactor aggressively but safely.

Fix:

- duplicated logic;
- scattered constants;
- scattered enums;
- hardcoded scientific values;
- hardcoded artifact names;
- hardcoded baseline/regime strings;
- long functions;
- long classes;
- weak abstractions;
- unused objects;
- dead modules;
- obsolete wrappers;
- redirect files;
- compatibility shells;
- circular imports;
- fragile imports;
- repeated fixtures;
- skipped tests;
- xfailed tests;
- commented-out tests;
- unclear package ownership;
- scattered path construction;
- repeated score loading;
- repeated metric parsing;
- repeated eligibility logic.

No backwards compatibility for internal structure.

If an internal module moves, update all imports and delete the old shell.

Do not leave wrapper modules.

Do not refactor just to create churn.

If code is already clean, leave it unchanged and prove cleanliness through checks.

---

## 23. Clean Code Rules

Do not preserve messy code with explanatory comments.

Fix the code.

Remove:

- legacy aliases;
- migration shims;
- duplicate old and new APIs;
- deprecation wrappers;
- obsolete branches;
- compatibility flags;
- dead feature flags;
- unused exports;
- unused fixtures;
- unused helpers;
- commented-out code;
- commented-out tests;
- commented-out assertions.

Do not add:

- filler comments;
- obvious comments;
- stale comments;
- verbose docstrings;
- AI-generated-looking banners;
- TODOs without an active ticket;
- `# noqa`;
- `type: ignore`;
- `pylint: disable`;
- `sonar ignore`;
- ignored warnings;
- unjustified static-analysis suppressions.

Suppressions are allowed only for unavoidable false positives.

Keep only comments or docstrings that explain non-obvious scientific, mathematical, or operational decisions.

---

## 24. Duplication and Hardcoded Values

Find and remove duplication in:

- threshold logic;
- calibration logic;
- eligibility logic;
- score loading;
- metric computation;
- artifact path construction;
- artifact names;
- run identifiers;
- baseline handling;
- regime handling;
- alpha handling;
- seed handling;
- schema validation;
- error messages;
- logging setup;
- result serialization;
- test setup;
- test assertions;
- mocks and fixtures;
- synthetic score generation;
- manifest creation;
- expected metric construction.

Remove hardcoded values that should be config-driven or centrally owned.

Scientific parameters must come from Hydra, config, or canonical constants.

Tests should reuse production constants where appropriate.

Do not duplicate production constants inside tests unless the test intentionally verifies the constant value.

---

## 25. Typing and Naming Rules

Fix weak typing aggressively.

Avoid unjustified:

- `Any`;
- loose `dict`;
- loose `list`;
- ambiguous tuple payloads;
- untyped returns;
- untyped parameters;
- ambiguous callables;
- implicit `None` behavior;
- stringly typed domain logic;
- untyped fixtures;
- ambiguous mock payloads.

Prefer:

- precise types;
- enums;
- dataclasses;
- Pydantic models;
- typed dictionaries where appropriate;
- protocols where they add clarity;
- type aliases for repeated structured values;
- explicit return types;
- explicit optional types;
- domain-specific value objects when they add real value.

Names must express DATP domain meaning.

Avoid vague names such as:

- `process`;
- `handle`;
- `run_common`;
- `helper`;
- `manager`;
- `service`;
- `data`;
- `result`;
- `obj`;
- `tmp`;
- `thing`;
- `payload`;
- `stuff`;
- `wrapper`;
- `common`.

Generic names are allowed only when the surrounding context makes them precise.

---

## 26. Complexity, Dead Code, and Wrappers

Reduce complexity by responsibility, not mechanically.

Fix:

- deeply nested `if` blocks;
- deeply nested loops;
- long functions;
- high cognitive complexity;
- long argument lists;
- mixed responsibilities;
- hidden side effects;
- functions that do IO, validation, computation, and reporting together;
- repeated condition chains;
- fragile branching over baselines or regimes;
- nested test setup;
- nested test assertions;
- nested fixture logic.

Remove useless checks such as:

- impossible `None` checks;
- redundant `isinstance` checks;
- repeated validation already guaranteed upstream;
- defensive checks for impossible states;
- duplicate file-existence checks;
- duplicate config validation;
- duplicate schema validation;
- impossible enum cases;
- obsolete compatibility branches.

Keep checks when they protect:

- external boundaries;
- user input;
- artifact IO;
- config boundaries;
- scientific invariants.

Remove wrapper classes unless they add real domain value.

A wrapper is justified only if it provides at least one of:

- validation;
- lifecycle control;
- typed boundary;
- meaningful domain abstraction;
- artifact ownership;
- scientific invariant protection.

---

## 27. Error Handling and Logging

Errors must be precise, domain-specific, and actionable.

Fix:

- swallowed exceptions;
- broad `except Exception` blocks;
- vague errors;
- duplicated error messages;
- silent fallbacks;
- fallbacks that hide missing artifacts;
- fallbacks that change scientific behavior;
- noisy logs;
- misleading logs;
- inconsistent log fields.

Do not reference governance files such as `CLAUDE.md`, `Blueprint.md`, or `spec.md` inside runtime error messages.

Runtime errors must explain the actual invalid condition.

Developer documentation may reference governance files.

---

## 28. Test Quality Rules

Tests must protect behavior and scientific invariants.

Do not:

- mark failing tests as skipped;
- mark failing tests as xfail;
- comment out failing tests;
- delete tests just because they fail;
- weaken assertions to make tests pass;
- mock away the behavior being verified;
- replace meaningful tests with shallow smoke tests;
- let tests silently pass on missing artifacts;
- rely on stale local files;
- rely on execution order;
- hide tests behind environment flags unnecessarily.

Fix:

- failing tests;
- errored tests;
- collection errors;
- import errors;
- fixture errors;
- skipped package-related tests;
- xfailed package-related tests;
- commented-out tests;
- commented-out assertions;
- nondeterministic tests;
- brittle implementation-detail assertions;
- tests that assert mocks instead of behavior;
- tests that pass without meaningful assertions.

Skipped or xfailed tests related to touched code must be converted into real passing tests unless a technically unavoidable reason exists.

CUDA/GPU tests must not be skipped when CUDA is available.

Do not run the full E2E suite by default.

Run E2E only when:

- the E2E test was added;
- the E2E test was modified;
- the E2E test directly covers the changed package;
- shared code used by E2E was changed;
- the E2E test is required to verify a touched scientific invariant.

If no E2E path is impacted, do not run full E2E and state that clearly in reports.

---

## 29. Required Test Scenarios

Add or preserve tests for relevant cases:

- empty inputs;
- missing files;
- malformed artifacts;
- invalid regime;
- invalid baseline;
- invalid alpha;
- invalid seed;
- Calibration-Pending clients;
- clients with no attack scores;
- clients with no benign scores;
- duplicate client IDs;
- unstable ordering;
- deterministic ordering;
- repeated run idempotency;
- score reuse violation;
- wrong artifact layout;
- wrong score column;
- missing manifest;
- invalid manifest;
- metric recomputation consistency;
- threshold parity;
- baseline scope correctness;
- regime-specific behavior;
- no silent fallback;
- no hidden retraining;
- no baseline-specific checkpoint path when checkpoints must be shared;
- no baseline-specific score path when scores must be shared;
- correct handling of temporary result files;
- correct failure on incomplete artifacts;
- scientific invariant preservation;
- import and collection stability;
- no skipped package tests;
- no xfailed package tests;
- no commented-out package tests;
- useful failure messages for invalid inputs;
- correct behavior under repeated execution.

Only add scenarios relevant to the package being changed.

Do not add meaningless tests just to increase test count.

---

## 30. Static Analysis and Quality Gates

Use existing repository tooling first.

Required targeted checks when relevant:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

Use CodeScene when useful and available:

```bash
cs delta
cs review
make codescene-check
```

Do not make Sonar a blocker unless the repository is actually configured for it.

Do not claim Sonar passed unless it actually ran.

Do not silently replace SonarQube or CodeScene with manual review and call it equivalent.

Static-analysis findings must be fixed unless they are true false positives.

Do not add suppressions to pass tools unless unavoidable.

---

## 31. Refactor Workflow

When refactoring or auditing code, work in loops:

1. Inventory files, tests, shared modules, configs, artifacts, and commands.
2. Audit code, tests, static-analysis output, and scientific invariants.
3. Create or update tickets.
4. Fix issues completely.
5. Run targeted tests and quality checks.
6. Re-audit for duplication, typing, hardcoded values, dead code, skipped tests, and scientific drift.
7. Perform a final hostile audit before reporting.
8. Update workflow state and handoff.

Do not stop after the first pass.

Do not treat pre-existing failures as acceptable.

Do not make churn changes on a second run.

---

## 32. Non-Negotiable Rejection Rules

Reject any change that:

- trains a separate B1–B4 encoder per baseline;
- changes model architecture differently across B1–B4;
- changes FedAvg/training protocol differently across B1–B4;
- uses different seeds across B1–B4 for the same experiment cell;
- recomputes scores inside threshold/result/report stages;
- uses CSV as a processed intermediate;
- silently includes Calibration-Pending clients in eligible-only metrics;
- reports CV(FPR) without coverage;
- fabricates unavailable dataset metadata;
- creates pseudo-clients from files, labels, folders, row chunks, or filenames;
- turns supportive or exploratory evidence into the primary claim;
- adds out-of-scope defenses to the main controlled study;
- hardcodes scientific parameters outside config or canonical constants;
- weakens tests to pass;
- leaves skipped/commented-out tests without justification;
- adds governance-file references to runtime errors;
- introduces wrapper classes with no domain value;
- preserves obsolete compatibility code;
- adds static-analysis suppressions to hide real issues;
- starts long experiments without explicit instruction.

---

## 33. Paper and Documentation Rules

Documentation must match implemented code and generated artifacts.

Do not mark tickets, plans, or checklists complete based only on prose.

Verify actual code and outputs.

Do not add new claims, new baselines, new datasets, new threat models, or new experiment results in prose unless the code and artifacts support them.

Every CV(FPR) statement must include coverage.

Main claim remains:

```text
Threshold calibration scope under a fixed encoder and fixed FedAvg setup.
```

B1 vs B2 under Regime A is the primary claim.

Regime B, Regime C, Regime D, FedProx, FedRep-AE, Ditto, `B2-conf`, `τ-shrink`, and `B-FedStatsBenign` are supportive, exploratory, diagnostic, or stress-test evidence unless explicitly promoted by frozen results and updated plans.

Do not present B5 as the main contribution.

Do not claim privacy, robustness, deployment readiness, poisoning resistance, evasion resistance, secure aggregation, formal DP, or concept-drift handling unless directly evaluated.

---

## 34. Definition of Done

Nothing is `DONE` until:

- code reality was inspected;
- documentation reality was inspected;
- scientific rules were inspected;
- conference-to-journal transition was inspected when relevant;
- tickets are updated;
- workflow state is updated;
- impacted code is refactored;
- impacted tests are updated;
- Ruff passes or remaining issues are documented with reasons;
- Pyright passes or remaining issues are documented with reasons;
- impacted tests pass;
- skipped/xfailed/commented-out tests are removed or justified;
- no wrappers or redirects remain from internal moves;
- scientific invariants are preserved;
- a later re-audit passes.

---

## 35. Final Report and Handoff

When stopping, write a handoff in:

```text
AI Workflow/state/HANDOFFS.md
```

Include:

- current git status;
- active ticket;
- active locks;
- completed work;
- files changed;
- commands run;
- checks passed;
- checks failed;
- scientific risks;
- unresolved issues;
- next exact action;
- whether memory/flags remain valid.

When reporting to the user, include only evidence-backed claims.

Do not claim:

- a file was reviewed unless it was inspected;
- a test passed unless it was run;
- a tool passed unless it was run;
- SonarQube or CodeScene passed unless actually executed;
- all issues are fixed unless checks support that.

Any remaining issue must include:

- exact file;
- exact reason it remains;
- exact risk;
- exact next action.

---

## 36. Default Principle

When uncertain, choose the action that is:

1. scientifically safest;
2. smallest correct change;
3. most consistent with canonical code owners;
4. easiest to test;
5. least likely to introduce churn;
6. most honest about evidence.

Never sacrifice scientific validity for cleaner-looking code.

Never sacrifice code correctness for a stronger-looking research result.
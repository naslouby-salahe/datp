# Scientific Contract Audit

This file is the live audit ledger for DATP scientific correctness.

It must be updated whenever code, tests, configs, tickets, results, reporting, or manuscript text touch scientific behavior.

It is not a planning wishlist.

Each status must be backed by direct evidence.

---

## 1. Status Values

Allowed audit statuses:

| Status | Meaning |
|---|---|
| `PENDING` | Not checked in the current repository state. |
| `PASS` | Checked against current evidence and valid. |
| `FAIL` | Checked and violated. |
| `BLOCKED_HUMAN` | User action or missing data prevents verification. |
| `BLOCKED_TECHNICAL` | Tool, environment, or dependency prevents verification. |
| `BLOCKED_SCIENTIFIC` | Scientific ambiguity prevents safe verification. |
| `NOT_APPLICABLE_WITH_REASON` | Not relevant to the audited task; reason required. |
| `REAUDIT_REQUIRED` | Previously checked but invalidated by later changes. |

Never use:

```text
OK
done
probably
seems
not checked but assumed
```

---

## 2. Audit Evidence Rule

Every non-`PENDING` row must include evidence.

Valid evidence examples:

1. File inspected.
2. Exact command output.
3. Test result.
4. Config field.
5. Artifact hash.
6. Metrics file path.
7. Figure sidecar path.
8. Ticket ID plus code verification.
9. Commit hash.
10. Explicit blocker record.

Invalid evidence examples:

1. Memory.
2. Prior conversation.
3. Ticket says done.
4. Agent says done.
5. Roadmap says intended.
6. File probably exists.
7. Result should exist.
8. Tool was expected to run.
9. Placeholder artifact.
10. Empty output file.

---

## 3. Current Audit Scope

Set this section at the start of each audit.

| Field | Value |
|---|---|
| Audit date | `PENDING` |
| Auditor | `PENDING` |
| Task / ticket | `PENDING` |
| Git status before | `PENDING` |
| Git status after | `PENDING` |
| Files inspected | `PENDING` |
| Commands run | `PENDING` |
| Tool limitations | `PENDING` |
| Final verdict | `PENDING` |

---

## 4. Core Scientific Identity Audit

| Invariant | Required behavior | Status | Evidence | Invalidation rule |
|---|---|---|---|---|
| DATP identity | Project remains a threshold-calibration scope study, not a broad FL-IDS benchmark. | `PENDING` |  | Any claim, ticket, or code path broadens scope. |
| Main variable | B1–B4 differ by threshold scope only. | `PENDING` |  | Baseline code, configs, or paths change. |
| Fixed encoder | Controlled ladder uses the same AE/encoder within a cell. | `PENDING` |  | Model architecture, training, checkpoint, or config changes. |
| Fixed mainline aggregation | Controlled ladder uses the locked mainline aggregation protocol. | `PENDING` |  | Training protocol or strategy changes. |
| Shared scores | B1–B4 thresholds derive from shared score artifacts. | `PENDING` |  | Score, threshold, result, or artifact path code changes. |
| Train once per cell | For a fixed dataset/regime/seed/alpha/training protocol, the controlled ladder does not retrain per baseline. | `PENDING` |  | Training orchestration or result layout changes. |
| Stage boundaries | Prepare, score, threshold/result, and report stages remain separated. | `PENDING` |  | Pipeline, CLI, reporting, or threshold module changes. |
| Config-driven parameters | Scientific parameters flow from config. | `PENDING` |  | Config models, constants, CLI, or defaults change. |
| Calibration-pending handling | Clients below benign `n_min` receive global fallback and are excluded from eligible-only operations. | `PENDING` |  | Eligibility, threshold, or metrics code changes. |
| Benign-only calibration | Main DATP thresholds do not use attack labels. | `PENDING` |  | Dataset split, threshold, comparator, or calibration code changes. |

---

## 5. Baseline and Comparator Audit

| Label | Required semantics | Status | Evidence | Invalidation rule |
|---|---|---|---|---|
| B0 | Centralized reference comparator only; not part of B1–B4 causal ladder. | `PENDING` |  | Baseline docs, result tables, or paper text change. |
| B1 | Client-averaged shared threshold from eligible benign calibration thresholds. | `PENDING` |  | B1 threshold or shared-threshold sensitivity code changes. |
| B2 | Per-client benign threshold, canonical p95 unless active config changes q. | `PENDING` |  | B2 threshold, q config, or eligibility code changes. |
| B3 | Device-family mean threshold, taxonomy-based and scoped correctly. | `PENDING` |  | Family taxonomy or B3 code changes. |
| B4 | Cluster-mean threshold from reconstruction-error fingerprints, not taxonomy, not privacy. | `PENDING` |  | Fingerprint, clustering, K, or B4 code changes. |
| B5 / local-only | Supplementary or bounding only; not central claim. | `PENDING` |  | Result tables, paper text, or baseline registry changes. |
| B-FedStatsBenign | DATP-compatible benign-only federated-statistics comparator; not faithful Laridi. | `PENDING` |  | Comparator code, docs, or paper text change. |
| B-LaridiFaithful | Relaxed reproduction using anomaly-labeled summaries only when permitted and labeled outside DATP assumption. | `PENDING` |  | Comparator scope or claim text changes. |
| FedProx | Aggregation-side stress test only; not B1–B4 causal ladder. | `PENDING` |  | Training protocol or result tables change. |
| Ditto | May be called Ditto only if faithfully implemented. | `PENDING` |  | Personalization code or naming changes. |
| FedRep-AE/FedPer-AE fallback | Fallback label only; never called Ditto if not faithful. | `PENDING` |  | Personalization fallback code or text changes. |
| FedBN | Rejected unless active plan changes; must not slip into mainline. | `PENDING` |  | Model architecture or stress-test list changes. |

---

## 6. Regime Audit

| Regime | Required status | Status | Evidence | Invalidation rule |
|---|---|---|---|---|
| Regime A | N-BaIoT physical-device split; confirmatory anchor. | `PENDING` |  | Data prep, regime config, or paper wording changes. |
| Regime B-a | CICIoT2023 file-level pseudo-client boundary condition. | `PENDING` |  | Data prep, regime config, or paper wording changes. |
| Regime B-b | Conditional CICIoT2023 device-MAC or device-group repartition after feasibility gate. | `PENDING` |  | Metadata feasibility or data prep changes. |
| Regime C | N-BaIoT Dirichlet severity sweep; supportive/exploratory. | `PENDING` |  | Regime C config or result wording changes. |
| Regime D | Conditional Edge-IIoTset external validation after feasibility gate. | `PENDING` |  | Edge-IIoTset data prep, configs, or claims change. |

---

## 7. Metrics and Statistics Audit

| Metric / statistic | Required behavior | Status | Evidence | Invalidation rule |
|---|---|---|---|---|
| CV(FPR) | Primary FPR-equity metric. | `PENDING` |  | Metric code or tables change. |
| Coverage ratio | Reported with CV(FPR). | `PENDING` |  | Metric aggregation or reporting changes. |
| Mean FPR | Reported where result table requires it. | `PENDING` |  | Metric keys or tables change. |
| Mean TPR | Reported where result table requires it. | `PENDING` |  | Metric keys or tables change. |
| CV(TPR) | Scoped as detection-dispersion context, not primary. | `PENDING` |  | Metric code or paper text changes. |
| Macro-F1 | Reported as detection-quality tradeoff. | `PENDING` |  | Metric code or paper text changes. |
| P10 Macro-F1 | Used to expose lower-tail degradation when available. | `PENDING` |  | Reporting code or paper text changes. |
| Worst-client BA | Reported where required by active plan. | `PENDING` |  | Metric code or tables change. |
| Bootstrap CI | Uses seed-level deltas where required. | `PENDING` |  | Statistics code or seed plan changes. |
| Wilcoxon / Cliff's delta | Secondary descriptive evidence only. | `PENDING` |  | Statistics code or claim text changes. |
| Sign consistency | Reported for seed-level deltas. | `PENDING` |  | Result aggregation or paper text changes. |

---

## 8. Dataset and Artifact Audit

| Item | Required behavior | Status | Evidence | Invalidation rule |
|---|---|---|---|---|
| Processed format | Processed intermediates are Parquet. | `PENDING` |  | Data storage code changes. |
| N-BaIoT schema | Feature count and columns match config. | `PENDING` |  | Data prep or config changes. |
| CICIoT2023 schema | Feature count and columns match config. | `PENDING` |  | Data prep or config changes. |
| Edge-IIoTset schema | Verified before claims or experiments. | `PENDING` |  | Edge-IIoTset code/data changes. |
| Split manifests | Splits are recorded and reproducible. | `PENDING` |  | Data split code changes. |
| Resolved config | Every run writes or references resolved config. | `PENDING` |  | Runner/config code changes. |
| Checkpoint lineage | Checkpoints are linked to regime/seed/training protocol, not threshold baseline for B1–B4. | `PENDING` |  | Training/artifact path code changes. |
| Score lineage | Score parquet files are linked to shared training cell. | `PENDING` |  | Scoring or artifact path code changes. |
| Metrics lineage | Metrics trace back to scores and configs. | `PENDING` |  | Result-writing code changes. |
| Figure/table sidecars | Figures and tables have backing data artifacts. | `PENDING` |  | Reporting code or figure/table files change. |
| Atomic writes | `metrics.json` written atomically only on success. | `PENDING` |  | Result-writing code changes. |
| Placeholders | No placeholder metrics, manifests, datasets, or success files. | `PENDING` |  | Any artifact-generation code changes. |

---

## 9. Claim Discipline Audit

| Claim area | Required wording boundary | Status | Evidence | Invalidation rule |
|---|---|---|---|---|
| Core superiority | Claim is FPR-dispersion reduction under tested protocol, not global anomaly-detection superiority. | `PENDING` |  | Paper, README, docs, reports, comments change. |
| Privacy | No formal privacy claim unless directly validated. | `PENDING` |  | Paper/docs/comments change. |
| Robustness | No poisoning/backdoor/evasion robustness claim unless directly validated. | `PENDING` |  | Paper/docs/comments change. |
| Hardware | No hardware deployment claim unless measured. | `PENDING` |  | Paper/docs/comments change. |
| Concept drift | Temporal MVE does not become a concept-drift claim unless active plan permits. | `PENDING` |  | Temporal docs/code/paper change. |
| Regime B | CICIoT2023 file-level result framed as boundary only. | `PENDING` |  | Paper/results wording changes. |
| Regime C | Dirichlet sweep framed as severity/supportive, not confirmatory. | `PENDING` |  | Paper/results wording changes. |
| Stress tests | FedProx/personalization/Laridi-style comparators scoped outside core causal ladder. | `PENDING` |  | Result tables or paper wording change. |
| Null/mixed outcomes | Null, mixed, failed, or skipped experiments disclosed. | `PENDING` |  | Results or manuscript changes. |
| Conference overlap | Journal extension distinguishes conference anchor from new evidence. | `PENDING` |  | Manuscript/submission package changes. |

---

## 10. Ticket and Workflow Audit

| Item | Required behavior | Status | Evidence | Invalidation rule |
|---|---|---|---|---|
| Ticket evidence | Tickets are created from observed code/docs/artifacts, not guesses. | `PENDING` |  | Ticket files change. |
| Ticket dependencies | Prerequisites are checked before implementation. | `PENDING` |  | Ticket progress changes. |
| DONE eligibility | No ticket is `DONE` without implementation/test/audit evidence. | `PENDING` |  | Ticket progress or audit reports change. |
| Human blockers | Human actions recorded in `docs/tickets/human_interventions.md`. | `PENDING` |  | Blockers or tickets change. |
| Workflow state | State files updated with invalidation rules. | `PENDING` |  | Workflow state changes. |
| Tool status | Tool availability recorded before tool-dependent claims. | `PENDING` |  | Tool environment or quality scripts change. |
| Five-pass audit | `WORKFLOW_AUDIT_PROTOCOL.md` applied before final status. | `PENDING` |  | Any task handoff changes. |

---

## 11. Mandatory Audit Commands

Use commands only when relevant and available.

Baseline inspection:

```bash
pwd
git status --short
find AI\ Workflow -maxdepth 3 -type f | sort
find docs/journal -maxdepth 1 -type f | sort
find docs/tickets -maxdepth 2 -type f | sort
```

Scientific drift search:

```bash
rg "FedBN|LocalHead|LocalHead-PersonalizedAE|concept drift|poisoning|backdoor|evasion|differential privacy|hardware validated|deployment-ready|global superiority|privacy-preserving" .
rg "B-FedStatsBenign|B-LaridiFaithful|FedRep-AE|FedPer-AE|Ditto|FedProx" docs src tests paper AI\ Workflow .claude
rg "CV\\(FPR\\)|coverage|Regime A|Regime B|Regime C|Regime D" docs src tests paper AI\ Workflow .claude
```

Shared-training audit:

```bash
rg "train|fit|checkpoint|score|threshold|metrics" src/datp/baselines src/datp/training src/datp/analyses src/datp/reporting src/datp/sweep src/datp/pipeline
find outputs -maxdepth 5 -type f 2>/dev/null | sort | head -200
find results -maxdepth 5 -type f 2>/dev/null | sort | head -200
```

Quality audit:

```bash
python -m ruff check src/datp tests
python -m pyright
python -m pytest --collect-only tests
```

Targeted tests must be chosen based on impacted files.

Do not run full e2e unless impacted or explicitly required.

---

## 12. Final Audit Entry Template

Append one entry per completed audit.

```text
## Audit Entry — <date> — <task-or-ticket>

Scope:
Files inspected:
Files changed:
Commands run:
Tool limitations:
Scientific invariants checked:
Tests run:
Artifacts checked:
Claims checked:

Pass 1 source hierarchy verdict:
Pass 2 scientific invariant verdict:
Pass 3 code architecture verdict:
Pass 4 tests/artifacts verdict:
Pass 5 claims/docs verdict:

Final verdict:
Remaining blockers:
Invalidation rule:
Next safe action:
```

Do not delete old audit entries unless the user explicitly requests cleanup.

Mark stale entries as stale instead.
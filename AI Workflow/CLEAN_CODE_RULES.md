# Clean Code and Refactor Rules

This file is the canonical rulebook for DATP clean-code, structure, typing, test, and refactor behavior.

Every agent, packet, audit, and review must treat this file as mandatory.

If this file conflicts with vague cleanup instructions elsewhere, this file wins.

If this file conflicts with DATP scientific constraints, the scientific constraints win.

---

## Core principle

The goal is not shorter code.

The goal is code that is:

```text
scientifically safe
owned by the right package
typed
explicit
centralized
easy to audit
easy to test
free of old compatibility shells
free of hidden behavior
```

A refactor is not complete because the code looks cleaner.

It is complete only when the real code, tests, imports, docs, workflow state, and scientific contract all agree.

---

## 1. Discovery first

The agent must inspect the real repository before changing anything.

Do not rely only on:

```text
tickets
DONE markers
previous reports
agent claims
workflow maps
planned move tables
docs that say work is complete
```

The real code and tests are the source of truth.

If the code contradicts a plan:

```text
inspect the code
record evidence
update the stale plan
fix the smallest safe batch
run checks
re-audit
```

Do not ask Salaheddine to manually plan every move.

---

## 2. No internal backwards compatibility

No backwards compatibility is allowed for internal refactors unless Salaheddine explicitly asks for it.

Forbidden:

```text
wrapper modules
redirect modules
compatibility aliases
old package shells
old files that only import from new files
old classes that only wrap renamed classes
old tests that preserve obsolete import paths
tests that validate old paths still work
```

Correct behavior:

```text
move the real code
update all imports directly
update tests directly
delete obsolete files
delete obsolete tests
run impacted checks
re-audit stale paths
```

Do not keep old paths alive.

---

## 3. Closed concepts must use enums

Use enums for closed domain sets.

Examples:

```text
baselines
regimes
datasets
experiment stages
score splits
artifact types
threshold methods
metric groups
run statuses
validation verdicts
client eligibility states
```

Avoid raw string literals spread across the codebase.

Boundary rule:

```text
CLI/config/file input may start as strings.
Parse strings once at the boundary.
Internal code should use typed enums or typed objects.
```

Avoid internal patterns like:

```text
str | Enum
isinstance(value, str)
value.value comparisons everywhere
repeated normalization functions
multiple internal names for the same concept
```

---

## 4. Constants must have canonical owners

Stable names must be centralized.

Examples:

```text
artifact filenames
directory names
score column names
metric keys
log filenames
marker filenames
stage names
baseline labels
regime labels
dataset labels
plot/table labels
config key names
```

Do not duplicate constants in local modules.

Do not create new constants beside existing canonical constants.

Before adding a constant:

```text
search existing owners
reuse existing constants when correct
move repeated constants to the right owner
update all callers
```

Scientific/runtime parameters must come from config, not hidden module constants.

Examples that must be config-driven:

```text
threshold quantiles
n_min
seeds
alpha values
round counts
batch sizes
convergence windows
feature counts
dataset paths
resource limits
```

---

## 5. Use dataclasses or typed objects for structured values

When several values travel together, use a typed object.

Use dataclasses, frozen dataclasses, typed records, or focused domain objects for:

```text
run identity
dataset identity
experiment cell identity
artifact bundles
score bundles
threshold results
metric summaries
client eligibility state
calibration outputs
validation verdicts
analysis requests
report build requests
plot requests
```

Avoid:

```text
long argument lists
repeated primitive argument groups
untyped dictionaries
anonymous tuples
duplicate NamedTuple shapes
multiple objects with identical fields
```

If two typed structures have the same fields and same meaning, merge them.

If they have the same fields but different meaning, rename them to make the distinction explicit.

---

## 6. Utilities must have ownership

Do not create dumping-ground modules.

Avoid vague files or folders named only:

```text
utils
helpers
misc
common
shared
general
tools
```

A helper must live where its responsibility belongs.

Examples:

```text
thresholding helper -> thresholding package
score loading helper -> scoring package
artifact path helper -> artifacts package
test fixture helper -> tests/fixtures
statistical helper -> statistics package
report helper -> reporting package
```

A shared helper is allowed only when it is genuinely cross-cutting and has a clear domain name.

---

## 7. Package structure must express responsibility

Files and folders must be organized by ownership.

The agent must actively detect and fix:

```text
misplaced files
mixed responsibilities
catch-all modules
oversized common files
training logic inside thresholding
score generation inside evaluation
score loading duplicated across packages
threshold logic inside analyses
reporting that recomputes upstream artifacts
validation that mutates experiment state
tests that no longer mirror production ownership
```

Allowed stage direction:

```text
data -> federated -> scoring -> thresholding -> evaluation -> analyses/reporting/validation
```

Forbidden downstream dependency direction:

```text
thresholding/evaluation/analyses/reporting/validation -> federated training
```

---

## 8. Remove duplication globally

Do not fix repeated problems locally one by one.

If a pattern appears in multiple places, promote it to the pattern ledger or a packet.

Search for duplication in:

```text
score loading
metric parsing
path construction
artifact naming
baseline strings
regime strings
threshold eligibility
calibration-pending handling
result serialization
dataset schemas
fixture builders
CUDA/device checks
config fallbacks
```

Local duplicate fixes are not enough.

The canonical owner must be created or reused.

---

## 9. Reduce complexity without hiding science

Reduce:

```text
deep nesting
long functions
long classes
high argument counts
wide branching
scattered conditionals
unused objects
dead imports
unreachable code
over-specified docstrings
comments that repeat code
```

Do not reduce complexity by:

```text
hiding scientific steps
collapsing meaningful stages
weakening names
using clever one-liners
using broad dynamic dispatch
adding magic defaults
adding behavior through side effects
```

Prefer:

```text
guard clauses
typed request/result objects
explicit domain names
small cohesive helpers
single-responsibility modules
clear stage boundaries
```

---

## 10. Comments and docstrings

Keep comments and docstrings useful.

Remove comments that only repeat the code.

Remove outdated comments.

Remove misleading comments.

Avoid long Args/Returns docstrings that only repeat type annotations.

Keep short docstrings when they explain:

```text
scientific meaning
stage boundary
non-obvious constraint
artifact contract
config contract
safety reason
```

No weird comments.

No commented-out code.

No TODOs without an owner or ticket.

---

## 11. Tests must move with code

When production code moves, tests move with it.

Do not leave tests under old ownership paths.

Do not preserve old import paths in tests.

Do not add tests that prove wrappers, redirects, or aliases still work.

Fix tests directly.

Rules:

```text
update impacted tests in the same packet
move tests to match production ownership
fix skipped tests when unjustified
fix xfailed tests when unjustified
delete obsolete tests only with evidence
avoid smoke-only replacements
keep behavior assertions meaningful
```

Never hide failures with:

```text
pytest.skip
pytest.mark.skip
pytest.mark.xfail
commented-out tests
weakened assertions
mocking away the behavior under test
```

CUDA-dependent tests must not be skipped when CUDA is expected. If CUDA is unavailable, record the environment reason.

---

## 12. Static tools are signals, not truth

Use tools, but do not obey them blindly.

Default required checks after code/test changes:

```bash
git status --short
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

Optional useful tools:

```bash
cs delta
cs review
make codescene-check
uv run vulture src/datp tests --min-confidence 80
uv run refurb src/datp tests
uv run semgrep scan --config auto src/datp tests
```

Rules:

```text
Vulture findings are suspects, not proof.
Refurb suggestions are optional and must improve clarity.
Semgrep findings require triage.
CodeScene is a signal, not a replacement for review.
Sonar is optional final-only if healthy.
```

If a tool suggests deleting code, verify with:

```text
rg
imports
tests
CLI entrypoints
scripts
configs
docs
tickets
project map
Graphify when relevant
```

---

## 13. Scientific behavior must not drift

Refactoring must preserve DATP science.

Forbidden unless explicitly authorized:

```text
changing formulas
changing threshold definitions
changing baseline semantics
changing regime semantics
changing seed logic
changing split logic
changing artifact schemas
changing output layout
changing train/eval stage boundaries
changing B1/B2/B3/B4 behavior
retraining per baseline when shared training is required
turning supportive evidence into the main claim
```

For DATP mainline:

```text
fixed encoder
fixed FedAvg
fixed data/splits/seeds
shared score artifacts
threshold scope is the variable
B1 vs B2 on Regime A is the confirmatory comparison
CV(FPR) must be reported with coverage ratio
```

Cleaner code is not allowed to change the experiment.

---

## 14. Boundary parsing only

Parse once at the boundary.

Allowed boundary locations:

```text
CLI
Hydra/config loading
file manifest loading
external artifact parsing
user input parsing
```

After parsing, internal code should use:

```text
enums
dataclasses
typed config objects
typed request/result objects
path builders
schema objects
```

Avoid repeated parsing inside domain logic.

Avoid accepting many equivalent representations internally.

---

## 15. Evidence and handoff are mandatory

Every packet must record:

```text
files inspected
files changed
commands run
tests run
checks deferred
tool failures
blockers
scientific risks
audit result
re-audit trigger
next exact action
```

Do not claim:

```text
clean
safe
done
fixed
passed
reviewed
complete
```

unless evidence exists.

If a later re-audit has not happened, use:

```text
REAUDIT_REQUIRED
```

not:

```text
DONE
```

---

## 16. Resource-safe execution

Avoid expensive operations by default.

Default behavior:

```text
targeted tests first
package-level tests when justified
full suite only when resource-safe or final
E2E collection before E2E execution
no training runs during refactor unless explicitly authorized
no experiment sweeps during refactor unless explicitly authorized
no uncontrolled parallel agents
```

Do not run heavy Ray/Flower jobs casually.

Do not run full E2E casually.

Do not start training or overnight commands from a refactor packet.

---

## 17. Required pre-change checklist

Before changing code, answer:

```text
What package owns this responsibility?
Is this a local issue or repeated pattern?
Is there an existing enum/constant/dataclass/schema?
Will this affect scientific behavior?
Which tests must move or change?
Which imports become stale?
Which checks are required?
Which docs/maps must be updated?
```

If the answer is unknown, inspect first.

---

## 18. Required post-change checklist

After changing code, verify:

```text
imports use canonical paths
old paths are deleted
no wrappers were added
no redirects were added
no compatibility aliases remain
constants/enums are not duplicated
typed objects are not duplicated
tests moved with code
impacted tests pass or failures are recorded
Ruff was run or deferred with reason
Pyright was run or deferred with reason
scientific risks were checked
project map was updated
audit files were updated
handoff was updated
re-audit is scheduled
```

---

## 19. Re-audit rule

A previous pass is evidence, not proof.

Re-audit after:

```text
package moves
test moves
enum/constant centralization
dataclass/schema centralization
artifact/path centralization
threshold/calibration consolidation
score loading consolidation
optional-tool cleanup
Graphify refreshes
final integration
```

The final review must look for:

```text
stale imports
old wrappers
redirect modules
compatibility aliases
duplicate constants
duplicate enums
duplicate typed shapes
unjustified skips
scientific drift
documentation drift
```

---

## 20. Final rule

When uncertain, choose the action that is:

```text
scientifically safest
smallest correct change
most explicit
most typed
most testable
least magical
least compatible with old wrong paths
easiest to audit later
```
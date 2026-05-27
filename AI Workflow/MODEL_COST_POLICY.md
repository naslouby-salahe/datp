# Model and Cost Policy

## Default model hierarchy

| Tier | Tool | Default use | Safe/default command |
|---|---|---|---|
| T1 | VS Code Copilot + DeepSeek V4 Pro | Main orchestrator and main coding worker | Use VS Code Copilot agent/chat configured with DeepSeek V4 Pro. |
| T2 | WSL Copilot CLI | Secondary quick terminal helper | `copilot -p "prompt"` |
| T3 | Claude Code Sonnet | Scientific review, high-risk architecture review, final hostile review | `claude --model sonnet -p "prompt"` |
| T3 | Codex CLI o3 | Terminal audit, diff review, test review, independent verification | `codex -m o3 exec "prompt"` |
| T4 | Antigravity CLI Gemini | Optional extra implementation, audit, repair, verification | `agy -p "prompt"` after checking `/usage`, `/quota`, and `/model` inside interactive sessions when needed. |

## Disallowed unless explicitly approved

| Tool | Disallowed default model / mode | Reason |
|---|---|---|
| Claude Code | `opus` | Too expensive for routine work. |
| Codex CLI | `gpt-5.5`, `gpt-5.5 high` | Too expensive for routine work. |
| Antigravity | Gemini Ultra/Pro-style expensive models | Avoid unless explicitly approved for a specific critical task. |

## Escalation rules

Escalate only for:

- scientific correctness risk;
- architecture risk;
- hard debugging after normal tools fail;
- independent verification of risky changes;
- final hostile review;
- final critical review.

Do not escalate for:

- mechanical edits;
- routine lint fixes;
- simple import cleanup;
- test boilerplate;
- formatting;
- trivial refactors;
- repeated checks that normal tools can answer.

## Tool role boundaries

### DeepSeek V4 Pro through VS Code Copilot

DeepSeek is expected to actively do the main work:

- plan packets;
- refactor and move code;
- simplify structure;
- update imports;
- update tests;
- run safe checks;
- repair issues;
- maintain workflow files;
- coordinate role-based passes.

DeepSeek must not delegate the real implementation and only supervise.

### WSL Copilot CLI

Use for:

- quick terminal questions;
- small checks;
- lightweight secondary reviews;
- short non-interactive prompts.

Do not use it to drive autonomous multi-step refactoring.

### Claude Code

Use Sonnet only by default:

```bash
claude --model sonnet -p "prompt"
```

Reserve for:

- scientific-contract review;
- high-risk architecture review;
- difficult reasoning;
- final hostile review;
- final critical review.

Do not use Claude for:

- routine refactoring;
- simple lint fixes;
- test boilerplate;
- mechanical edits.

### Codex CLI

Use o3 only by default:

```bash
codex -m o3 exec "prompt"
```

Reserve for:

- terminal audit;
- diff review;
- independent verification;
- test review;
- checking technical safety.

Useful commands:

```bash
codex -m o3 exec "prompt"
codex -m o3 review
codex doctor
```

### Antigravity CLI

Correct command:

```bash
agy
```

Use for:

- extra implementation passes;
- extra audit passes;
- repair work;
- verification;
- alternative review.

Before relying on it, check model/quota inside session when interactive:

```text
/usage
/quota
/model
```

Prefer cheaper Gemini models such as Flash or lower-tier models for routine work.

## Cost guardrails

- Normal tools first, AI second.
- One active implementation agent per overlapping file set.
- Use targeted prompts, not huge unbounded prompts, unless launching the main orchestrator.
- End noisy or stale sessions and write a handoff.
- Start new sessions for new packets, model changes, final reviews, or after quota warnings.
- Record every escalation in `REFACTOR_WORKBOARD.md`.

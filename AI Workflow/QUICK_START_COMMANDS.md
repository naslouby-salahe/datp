# Quick Start Commands

Run from WSL.

## Enter repository

```bash
cd /home/naslouby/Projects/datp
```

## Confirm workflow files

```bash
ls -la "AI Workflow"
ls -la "AI Workflow/packets"
```

## Start with DeepSeek in VS Code Copilot

Open `AI Workflow/ORCHESTRATOR_PROMPT.md`, copy the prompt, and give it to the VS Code Copilot agent configured with DeepSeek V4 Pro.

## Safe tool commands

```bash
git status --short
python -m ruff check src/datp tests
python -m pyright
python -m pytest <impacted-test-paths>
```

## Optional helper commands

```bash
copilot -p "quick check prompt"
claude --model sonnet -p "scientific or architecture review prompt"
codex -m o3 exec "audit or verification prompt"
agy -p "extra audit or repair prompt"
```

## Commands that need explicit approval

```bash
claude --model opus -p "prompt"
codex -m gpt-5.5 exec "prompt"
codex -m "gpt-5.5 high" exec "prompt"
```

Expensive Antigravity Gemini Ultra/Pro-style models also need explicit approval.

---
name: ieee-fix
description: |
  IEEE conference paper fix agent. Read this skill before running /project:ieee-fix.
  Applies ONLY necessary, minimal LaTeX fixes to a .tex file based on an audit report.
  Core contract: never change content or structure; punctuation-only mechanics corrections
  (e.g., `et. al.` → `et al.`) are permitted. Only fix LaTeX mechanics.
  Every change is shown as a diff and logged.
  Based on: IEEEtran.cls (v1.8b+), IEEE-conference-template-062824.tex (June 2024).
project_root: /home/naslouby/Projects/datp
---

## Agent Role

You are a surgical IEEE LaTeX fix agent. You receive:
1. A `.tex` file (the paper to fix).
2. An audit report from the `ieee-audit` agent (the list of issues with their fix types).

Your job is to apply **only** the fixes marked `AUTO` without asking, present diffs for
`CONFIRM` fixes and wait for user approval, and flag `MANUAL` fixes for the author.

You NEVER (content constraints):
- Rewrite or rephrase any sentence, clause, or phrase. (Exception: punctuation-only mechanics corrections, such as `et. al.` → `et al.`, are LaTeX mechanics fixes and do not constitute rephrasing.)
- Change any technical content (values, formulas, results, citations).
- Restructure paragraphs or sections.
- Add content that wasn't there (except required LaTeX commands).
- Remove content (except clearly identified template placeholder text, after confirmation).

You ALWAYS (execution constraints):
- Work on a COPY of the file (`mypaper_fixed.tex`), never on the original.
- Show a before/after diff for every single change, no matter how small.
- Log every change to `mypaper_fix_log.md`.
- Number changes sequentially (FIX-01, FIX-02, …).
- Preserve all whitespace, indentation, and comment style of the original file.

---

## Pre-Fix Setup

### Step 1 — Read the skill
You are reading it now.

### Step 2 — Verify inputs
```bash
# Confirm the source .tex file exists:
ls -la "$TEX_FILE"

# Confirm the audit report exists:
ls -la "$AUDIT_REPORT"
```

### Step 3 — Create a working copy (NEVER modify the original)
```bash
TEX_STEM=$(basename "$TEX_FILE" .tex)
TEX_DIR=$(dirname "$TEX_FILE")
FIXED_FILE="${TEX_DIR}/${TEX_STEM}_fixed.tex"
FIX_LOG="${TEX_DIR}/${TEX_STEM}_fix_log.md"

cp "$TEX_FILE" "$FIXED_FILE"
echo "Working copy created: $FIXED_FILE"
```

### Step 4 — Initialize the fix log
```bash
cat > "$FIX_LOG" << 'EOF'
# IEEE Fix Log
**Source file:** PATH
**Fixed file:** PATH_FIXED
**Date:** DATE
**Audit report:** AUDIT_PATH

---

## Applied Fixes

EOF
```

### Step 5 — Parse the audit report
Read every issue from the audit report. Build an internal list:
- Issues marked `AUTO` → apply immediately, log, continue.
- Issues marked `CONFIRM` → show diff, ask user, apply if yes, log result.
- Issues marked `MANUAL` → add to "Requires Author Action" section of log, skip.
- Issues marked `NONE` → skip.

Process issues in order: CRITICAL (issues that prevent compilation or violate IEEEtran class requirements) first, then MAJOR (issues that violate IEEE standards, such as forbidden packages or wrong environments), then MINOR (stylistic inconsistencies such as label order or spacing).

---

## Fix Procedures by Category

Each procedure below maps to audit CHECK IDs. Execute the applicable procedures
based on what the audit report flagged.

---

### FIX-PROC-01 — Document Class Option  (AUTO)

**Applies to:** CHECK-01 findings where class option is wrong.

```bash
# Backup the line for the diff:
ORIGINAL=$(grep -n "\\\\documentclass" "$FIXED_FILE" | head -1)

# Apply the fix:
sed -i 's/\\documentclass\[journal\]{IEEEtran}/\\documentclass[conference]{IEEEtran}/' "$FIXED_FILE"
sed -i 's/\\documentclass\[technote\]{IEEEtran}/\\documentclass[conference]{IEEEtran}/' "$FIXED_FILE"
sed -i 's/\\documentclass\[peerreview\]{IEEEtran}/\\documentclass[conference]{IEEEtran}/' "$FIXED_FILE"
# Remove explicit draft option (replace with draftcls for safer draft mode):
# NOTE: Only apply if audit flagged 'draft' specifically. Use CONFIRM for this.
```

**Log entry format:**
```
### FIX-01 — Document Class Option [AUTO] [CRITICAL]
**Line:** 1
**Change:**
- Before: `\documentclass[journal]{IEEEtran}`
+ After:  `\documentclass[conference]{IEEEtran}`
**Reason:** Conference papers must use [conference] option.
**Status:** APPLIED ✓
```

---

### FIX-PROC-02 — Add Missing `\usepackage{cite}`  (AUTO)

**Applies to:** CHECK-02 — `cite` package absent.

Insert after the last existing `\usepackage` line in the preamble, before `\begin{document}`.

```bash
# Find the line number of the last \usepackage before \begin{document}:
LAST_PKG_LINE=$(grep -n "\\\\usepackage" "$FIXED_FILE" | \
  awk -F: '{print $1}' | tail -1)

# Insert \usepackage{cite} after that line:
sed -i "${LAST_PKG_LINE}a\\\\usepackage{cite}" "$FIXED_FILE"
```

**IMPORTANT:** Preserve the indentation and style of surrounding `\usepackage` lines.

---

### FIX-PROC-03 — Remove Forbidden Packages  (CONFIRM)

**Applies to:** CHECK-02 — forbidden package detected.

For each forbidden package found:
1. Show the user the full `\usepackage` line.
2. Explain why it's forbidden.
3. Ask: "Remove this package? [yes/no]"
4. If yes: comment it out with `%` (do NOT delete — author may have code that depends on it).

```bash
# Example: comment out geometry (never delete):
sed -i 's/^\\usepackage{geometry}/% REMOVED (IEEE compliance): \\usepackage{geometry}/' "$FIXED_FILE"
# Same pattern for fullpage, pslatex, mathptm, balance, flushend, etc.
```

**CRITICAL:** If `geometry` or `fullpage` is removed, warn the author:
"If you had custom `\geometry{...}` calls elsewhere in the document, they will now fail.
Search for `\geometry{` and remove those lines too."

---

### FIX-PROC-04 — Remove/Fix `\IEEEoverridecommandlockouts`  (AUTO / CONFIRM)

- If `\IEEEoverridecommandlockouts` is MISSING but `\thanks{}` is used → AUTO: add it
  immediately before `\documentclass` or in preamble.
- If `\IEEEoverridecommandlockouts` is PRESENT but `\thanks{}` is absent → CONFIRM: comment it out.

```bash
# Add (if missing but needed):
sed -i '/^\\documentclass/i \\IEEEoverridecommandlockouts' "$FIXED_FILE"

# Comment out (if present but not needed):
sed -i 's/^\\IEEEoverridecommandlockouts$/% \\IEEEoverridecommandlockouts  % removed: no \\thanks{} used/' "$FIXED_FILE"
```

---

### FIX-PROC-05 — Remove Disabled Conference-Mode Commands  (CONFIRM)

Commands that are silently ignored or misbehave in conference mode:
`\IEEEmembership`, `\markboth`, `\IEEEpubid`, `\IEEEpubidadjcol`,
`\IEEEbiography`, `\IEEEbiographynophoto`, `\IEEEraisesectionheading`

For each found:
1. Show the full line.
2. Explain it has no effect in conference mode.
3. Ask: "Comment out this line? [yes/no]"

```bash
# Comment out (example for \markboth):
LINE_NUM=<from audit report>
sed -i "${LINE_NUM}s/^/% IEEE conference mode: command disabled — /" "$FIXED_FILE"
```

---

### FIX-PROC-06 — Replace `{eqnarray}` with `{align}`  (AUTO)

**Applies to:** CHECK-09 — `{eqnarray}` found.

This is a mechanical replacement but requires careful handling of the `&` alignment:

**In `{eqnarray}`, alignment is:**  `left_side & = & right_side` (3 columns, `&` around relation)
**In `{align}`, alignment is:**     `left_side &= right_side` (2 columns, `&` before relation)

```bash
# Step 1: replace environment name (both opening and closing):
sed -i 's/\\begin{eqnarray\*}/\\begin{align*}/g' "$FIXED_FILE"
sed -i 's/\\end{eqnarray\*}/\\end{align*}/g' "$FIXED_FILE"
sed -i 's/\\begin{eqnarray}/\\begin{align}/g' "$FIXED_FILE"
sed -i 's/\\end{eqnarray}/\\end{align}/g' "$FIXED_FILE"
```

**Step 2 (CONFIRM):** The `&` delimiters change. In `{eqnarray}`, `= &=&` pattern has
extra `&`. In `{align}`, it should be `&=`. Show the author each converted equation and
ask for confirmation that the alignment still looks correct.

**Specific pattern to fix:**
- `A &=& B` → `A &= B` (remove one `&`)

```bash
# This sed only applies inside former eqnarray blocks — be careful:
# Flag these lines for CONFIRM rather than AUTO:
grep -n "&.*=.*&\|& = &\|&=&" "$FIXED_FILE"
```

Log every equation changed.

---

### FIX-PROC-07 — `\label` / `\caption` Order in Floats  (AUTO)

**Applies to:** CHECK-11, CHECK-12 — `\label` before `\caption`.

For each figure/table block where `\label` appears before `\caption`:

```bash
# For a figure block where \label is on line L1 and \caption is on line L2 (L1 < L2):
# Extract both lines:
LABEL_LINE=$(sed -n "${L1}p" "$FIXED_FILE")
CAPTION_LINE=$(sed -n "${L2}p" "$FIXED_FILE")

# Swap them (replace line L1 with caption content, line L2 with label content):
sed -i "${L1}s/.*/${CAPTION_LINE}/" "$FIXED_FILE"
sed -i "${L2}s/.*/${LABEL_LINE}/" "$FIXED_FILE"
```

**IMPORTANT:** Only swap within the same float block. Never move a `\label` outside its float.

**Diff format for log:**
```diff
  \begin{figure}[!t]
  \centering
  \includegraphics[width=\columnwidth]{fig.pdf}
- \label{fig:result}
- \caption{System architecture.}
+ \caption{System architecture.}
+ \label{fig:result}
  \end{figure}
```

---

### FIX-PROC-08 — `\begin{center}` → `\centering` in Floats  (AUTO)

**Applies to:** CHECK-11, CHECK-12 — `{center}` environment inside figure/table.

```bash
# Inside figure/table blocks only — do not touch {center} in body text:
# This requires context-aware replacement. Use awk:
awk '
  /\\begin\{figure|\\begin\{table/{in_float=1}
  /\\end\{figure|\\end\{table/{in_float=0}
  in_float && /\\begin\{center\}/{print "  \\centering  % fixed: was \\begin{center}"; next}
  in_float && /\\end\{center\}/{next}
  {print}
' "$FIXED_FILE" > /tmp/fixed_center.tex && mv /tmp/fixed_center.tex "$FIXED_FILE"
```

**Diff:**
```diff
  \begin{figure}[!t]
- \begin{center}
+ \centering
  \includegraphics[width=\columnwidth]{fig.pdf}
  \caption{Caption.}
  \label{fig:x}
- \end{center}
  \end{figure}
```

---

### FIX-PROC-09 — Figure Float Placement `[h]` → `[!t]`  (CONFIRM)

**Applies to:** CHECK-11 — `[h]`, `[here]`, or `[H]` placement.

Show the diff and ask:
```
Found: \begin{figure}[h]
IEEE strongly prefers [!t] (top of column). Change to \begin{figure}[!t]? [yes/no]
```

If yes:
```bash
sed -i 's/\\begin{figure}\[h\]/\\begin{figure}[!t]/g' "$FIXED_FILE"
sed -i 's/\\begin{figure}\[here\]/\\begin{figure}[!t]/g' "$FIXED_FILE"
sed -i 's/\\begin{figure}\[H\]/\\begin{figure}[!t]/g' "$FIXED_FILE"
```

---

### FIX-PROC-10 — Add `\renewcommand{\arraystretch}{1.3}` to Tables  (AUTO)

**Applies to:** CHECK-12 — missing `\arraystretch`.

For each `\begin{table}` block that does not already have `\arraystretch`:

```bash
# Insert after \begin{table}[...]:
# Find the line number of \begin{tabular} and insert before it:
awk '
  /\\begin\{table/{in_table=1; has_stretch=0}
  /arraystretch/{has_stretch=1}
  /\\begin\{tabular/ && in_table && !has_stretch{
    print "  \\renewcommand{\\arraystretch}{1.3}  % added for IEEE row spacing"
  }
  {print}
  /\\end\{table/{in_table=0; has_stretch=0}
' "$FIXED_FILE" > /tmp/fixed_stretch.tex && mv /tmp/fixed_stretch.tex "$FIXED_FILE"
```

---

### FIX-PROC-11 — Fix Table Caption Position  (AUTO)

**Applies to:** CHECK-12 — table caption below `\begin{tabular}`.

Tables: caption ABOVE tabular. If caption is below:

```bash
# This requires extracting the block and reordering.
# Use Python for reliability with multi-line content:
python3 << 'PYEOF'
import re, sys

with open("$FIXED_FILE", 'r') as f:
    content = f.read()

# Find table blocks and check caption position relative to \begin{tabular}:
# ... (complex multi-line reordering — see implementation note below)
PYEOF
```

**Implementation note:** If the table block is simple (caption on one line, tabular on
next line), sed can handle it. If the caption spans multiple lines, use Python.

After reordering, show the full BEFORE and AFTER of the table block as a diff.

---

### FIX-PROC-12 — Merge Consecutive `\cite` Commands  (AUTO)

**Applies to:** CHECK-13 — consecutive `\cite{a}\cite{b}` patterns.

```bash
# Replace \cite{a}\cite{b} with \cite{a,b}:
perl -i -0pe '
  s/\\cite\{([^}]+)\}\s*\\cite\{([^}]+)\}/\\cite{$1,$2}/g;
  # Run multiple times to handle chains of 3+:
  s/\\cite\{([^}]+)\}\s*\\cite\{([^}]+)\}/\\cite{$1,$2}/g;
  s/\\cite\{([^}]+)\}\s*\\cite\{([^}]+)\}/\\cite{$1,$2}/g;
' "$FIXED_FILE"
```

---

### FIX-PROC-13 — Fix `\bibliographystyle` and `\bibliography` Order  (AUTO)

**Applies to:** CHECK-14 — `IEEEfull` used instead of `IEEEabrv`, or wrong bib order.

```bash
# Replace IEEEfull with IEEEabrv:
sed -i 's/\\bibliography{IEEEfull,/\\bibliography{IEEEabrv,/g' "$FIXED_FILE"

# Fix order if user bib file comes before IEEEabrv:
# e.g., \bibliography{mybib,IEEEabrv} → \bibliography{IEEEabrv,mybib}
# This is a CONFIRM fix because we need to know the user's bib file name:
```
→ Show the line and ask for confirmation before reordering.

---

### FIX-PROC-14 — Fix `\section{Acknowledgment}` → `\section*{Acknowledgment}`  (AUTO)

**Applies to:** CHECK-15 — acknowledgment section is numbered.

```bash
sed -i 's/\\section{Acknowledgment}/\\section*{Acknowledgment}/g' "$FIXED_FILE"
sed -i 's/\\section{Acknowledgments}/\\section*{Acknowledgments}/g' "$FIXED_FILE"
```

---

### FIX-PROC-15 — Fix Acknowledgment Spelling  (CONFIRM)

**Applies to:** CHECK-15 — "Acknowledgement" (British) vs "Acknowledgment" (American).

```
Found: \section*{Acknowledgement}
IEEE American English standard: "Acknowledgment" (no 'e' after 'g').
Change spelling? [yes/no]
```

If yes:
```bash
sed -i 's/Acknowledgement/Acknowledgment/g' "$FIXED_FILE"
```

---

### FIX-PROC-16 — Fix `\ref{eq...}` → `\eqref{eq...}`  (AUTO)

**Applies to:** CHECK-18 — `\ref{}` used for equation references.

```bash
# Only convert \ref for equation labels (those starting with eq: or eqn:):
sed -i 's/\\ref{eq:/\\eqref{eq:/g' "$FIXED_FILE"
sed -i 's/\\ref{eqn:/\\eqref{eqn:/g' "$FIXED_FILE"
```

If label prefix convention is inconsistent (e.g., some equation labels start with `fig:`
due to an error), flag for MANUAL review rather than blindly converting.

---

### FIX-PROC-17 — Comment Out Red Warning Block  (CONFIRM)

**Applies to:** CHECK-17 — template red warning text at document end.

The template ends with:
```latex
\vspace{12pt}
\color{red}
IEEE conference templates contain guidance text...
```

Show the block and ask: "Remove template warning block? [yes/no]"

If yes:
```bash
# Comment out from \vspace{12pt}\color{red} to \end{document}:
# (These lines should be deleted in production — comment first for safety)
```

**IMPORTANT:** The `\color{red}` command itself may leave a color state that affects
subsequent text if not properly closed. If `\normalcolor` is absent, add it.

---

### FIX-PROC-18 — Fix `et. al.` → `et al.`  (AUTO)

**Applies to:** CHECK-14 — "et. al." in bibliography.

```bash
sed -i 's/et\. al\./et al./g' "$FIXED_FILE"
```

---

### FIX-PROC-19 — Fix Subfig Package Options  (CONFIRM)

**Applies to:** CHECK-02 — `subfig` loaded without `caption=false`.

Show:
```
Found: \usepackage{subfig}
IEEE requires caption=false option to prevent subfig from overriding IEEEtran caption handling.
Change to \usepackage[caption=false,font=footnotesize]{subfig}? [yes/no]
```

```bash
sed -i 's/\\usepackage{subfig}/\\usepackage[caption=false,font=footnotesize]{subfig}/' "$FIXED_FILE"
```

---

### FIX-PROC-20 — Fix `\bibliographystyle` (CONFIRM)

**Applies to:** CHECK-14 — wrong bibliography style.

```
Found: \bibliographystyle{plain}
IEEE conference requires \bibliographystyle{IEEEtran}.
Change? [yes/no]
```

```bash
sed -i 's/\\bibliographystyle{plain}/\\bibliographystyle{IEEEtran}/' "$FIXED_FILE"
sed -i 's/\\bibliographystyle{abbrv}/\\bibliographystyle{IEEEtran}/' "$FIXED_FILE"
sed -i 's/\\bibliographystyle{unsrt}/\\bibliographystyle{IEEEtran}/' "$FIXED_FILE"
```

---

## MANUAL Fixes — Author Action Required

For every MANUAL issue in the audit report, add an entry to the fix log:

```markdown
### MANUAL-01 — [MANUAL] [CRITICAL] Title placeholder not replaced
**Line:** 16
**Found:** `\title{Conference Paper Title*\\`
**Required action:** Replace with your actual paper title.
**IEEE rule:** Title must not contain math, special characters, or subtitles.
**Status:** ⚠️ REQUIRES AUTHOR ACTION

### MANUAL-02 — [MANUAL] [CRITICAL] Abstract contains placeholder text
**Line:** 62
**Found:** `This document is a model and instructions for \LaTeX.`
**Required action:** Replace with your actual abstract.
**Status:** ⚠️ REQUIRES AUTHOR ACTION
```

---

## Post-Fix Verification

After all fixes are applied:

### Step V1 — Diff the original vs fixed
```bash
diff "$TEX_FILE" "$FIXED_FILE"
```
Save this full diff to the fix log.

### Step V2 — Count total changes
```bash
diff "$TEX_FILE" "$FIXED_FILE" | grep "^[<>]" | wc -l
echo "Total changed lines: $?"
```

### Step V3 — Attempt compilation (if pdflatex is available)
```bash
cd "$(dirname "$FIXED_FILE")"
pdflatex -interaction=nonstopmode "$(basename "$FIXED_FILE")" 2>&1 | tail -20
```
Report: COMPILATION SUCCESSFUL | COMPILATION FAILED (with error message).

### Step V4 — Run bibtex if bibliography changed
```bash
bibtex "$(basename "$FIXED_FILE" .tex)" 2>&1
```

### Step V5 — Check for new issues
```bash
# Quick grep for any remaining obvious issues:
grep -n "\\\\begin{eqnarray}\|\\\\documentclass\[journal\]\|et\. al\." "$FIXED_FILE"
```

---

## Fix Log Format

The complete `_fix_log.md` file structure:

```markdown
# IEEE Fix Log
**Source file:** `path/to/paper.tex`
**Fixed file:** `path/to/paper_fixed.tex`
**Date:** YYYY-MM-DD HH:MM
**Audit report:** `path/to/paper_audit_report.md`
**Total issues in audit:** N
**AUTO fixes applied:** N
**CONFIRM fixes applied:** N  (out of N presented)
**CONFIRM fixes skipped:** N  (user declined)
**MANUAL fixes flagged:** N

---

## Applied Fixes

### FIX-01 — Document Class Option [AUTO] [CRITICAL]
[diff block]
[reason]
**Status:** APPLIED ✓

...

---

## Skipped by User

### SKIP-01 — [Name] [CONFIRM]
**User response:** No
**Not applied.**

---

## Requires Author Action

### MANUAL-01 — [description]
...

---

## Compilation Result
**pdflatex:** SUCCESS / FAILED
**bibtex:** SUCCESS / FAILED / NOT RUN

---

## Full Diff (source vs fixed)
\`\`\`diff
[output of diff command]
\`\`\`
```

---

## Absolute Constraints (Never Violate)

1. **NEVER overwrite the original `.tex` file.** Always work on `_fixed.tex`.
2. **NEVER change sentence content.** If a fix would require rewording, classify as MANUAL.
3. **NEVER add content** not in the original (except required LaTeX commands like `\usepackage{cite}`).
4. **NEVER remove a `\label{}`** — even if it seems redundant. Author may have unlisted references.
5. **NEVER change figure/table content** (data, results, captions text).
6. **NEVER reorder sections** — only reorder lines within a float block (label/caption swap).
7. **NEVER silently apply a CONFIRM fix** — always show the diff and wait.
8. **NEVER apply fixes to the IEEE reference files** (`.cls`, `.bst`, `.bib` in IEEE/).
9. **NEVER change math content** — equation structure edits are MANUAL only.
10. **WHEN IN DOUBT → MANUAL.** A missed fix is recoverable. An accidental content change is not.
---
name: ieee-audit
description: |
  IEEE conference paper auditor. Read this skill before running /project:ieee-audit.
  Detects every violation of IEEE conference formatting standards in a .tex file and
  produces a structured, machine-readable audit report that the ieee-fix agent can consume.
  Based on: IEEEtran.cls (v1.8b+), IEEEtran_HOWTO.pdf, IEEEtran_bst_HOWTO.pdf,
  and IEEE-conference-template-062824.tex (template version June 2024).
project_root: /home/naslouby/Projects/datp
ieee_template: IEEE/conference-latex-template/IEEE-conference-template-062824/IEEE-conference-template-062824.tex
ieee_cls: IEEE/conference-latex-template/IEEE-conference-template-062824/IEEEtran.cls
ieee_bst: IEEEtranBST2/IEEEtran.bst
ieee_abrv: IEEEtranBST2/IEEEabrv.bib
---

## Agent Role

You are a rigorous IEEE conference paper auditor. Your job is to read a `.tex` file
line-by-line and detect every deviation from IEEE conference formatting standards.
You do NOT fix anything. You produce a structured audit report.

---

## Pre-Audit Setup

Before starting, always do these steps in order:

### Step 1 — Read the skill
You are reading this skill now. Proceed.

### Step 2 — Verify file exists
```bash
cat "$TEX_FILE"
```
If the file does not exist, report the error and stop.

### Step 3 — Extract structural overview
```bash
grep -n "\\\\documentclass\|\\\\usepackage\|\\\\begin{document}\|\\\\maketitle\
\|\\\\section\|\\\\subsection\|\\\\begin{abstract}\|\\\\begin{IEEEkeywords}\
\|\\\\begin{figure\|\\\\begin{table\|\\\\begin{equation\|\\\\bibliography\
\|\\\\bibliographystyle\|\\\\end{document}" "$TEX_FILE"
```
This gives you the paper's skeleton before deep inspection.

### Step 4 — Count lines for reference
```bash
wc -l "$TEX_FILE"
```

---

## Audit Checks — Run All in Order

### Quick Reference — All Checks

| Check | Focus Area | Key Severity Risk |
|---|---|---|
| CHECK-01 | Document class options | CRITICAL: wrong mode/onecolumn |
| CHECK-02 | Required & forbidden packages | CRITICAL: margin-override packages |
| CHECK-03 | `\IEEEoverridecommandlockouts` | MAJOR: `\thanks{}` will silently fail |
| CHECK-04 | Title content & format | CRITICAL: math, placeholders, footnotes |
| CHECK-05 | Author block structure | CRITICAL: template placeholders |
| CHECK-06 | Abstract content | CRITICAL: math, citations, footnotes |
| CHECK-07 | Index terms / keywords | CRITICAL: wrong environment or placeholder |
| CHECK-08 | Section headings | CRITICAL: unreplaced template headings |
| CHECK-09 | Forbidden `{eqnarray}` | CRITICAL: explicitly forbidden in IEEE 2024 |
| CHECK-10 | Equations & references | MAJOR: hardcoded eq numbers, missing amsmath |
| CHECK-11 | Figures | CRITICAL: `\label` before `\caption` |
| CHECK-12 | Tables | CRITICAL: `\label` before `\caption`; caption below |
| CHECK-13 | Citations in text | MAJOR: hardcoded `[N]` numbers |
| CHECK-14 | Bibliography & BibTeX | MAJOR: wrong style, wrong bib order |
| CHECK-15 | Acknowledgment section | MAJOR: numbered instead of starred |
| CHECK-16 | Appendices | MAJOR: `\section` after `\appendix` |
| CHECK-17 | Template boilerplate | CRITICAL: any unreplaced template text |
| CHECK-18 | Cross-references & labels | MAJOR: hardcoded figure/table numbers |
| CHECK-19 | Last-page column balance | INFO: `\IEEEtriggeratref` recommendation |
| CHECK-20 | Margin & spacing overrides | CRITICAL: direct dimension overrides |

Process checks in order. Record findings as you go; do not defer.

For every check below:
- Record the **line number(s)** from the `.tex` file.
- Assign a **severity**: `CRITICAL` | `MAJOR` | `MINOR` | `INFO`. (See **Severity Definitions** table at the end of this skill for exact meanings.)
- Assign a **fix_type**: `AUTO` | `CONFIRM` | `MANUAL` | `NONE`.
  - `AUTO`    → the fix agent can apply this without asking (pure LaTeX command swap).
  - `CONFIRM` → fix agent must show the user the diff and get a yes/no before applying.
  - `MANUAL`  → author must fix this (content decision, cannot be automated).
  - `NONE`    → informational only, no action needed.
- Set **fix_possible**: `true` | `false`. (`true` if the issue can be resolved programmatically without requiring an author content decision; `false` otherwise.)

---

### CHECK-01 — Document Class

**Grep:**
```bash
grep -n "\\\\documentclass" "$TEX_FILE"
```

**Rules:**
- MUST be `\documentclass[conference]{IEEEtran}` for conference papers.
- If `journal`, `technote`, `peerreview`, or `peerreviewca` → CRITICAL.
- If `twocolumn` explicitly set → MAJOR (redundant; conference mode is always 2-col).
- If `onecolumn` → CRITICAL (breaks conference layout).
- If `draft` → MAJOR (disables figure rendering; suggest `draftcls`).
- If `draftclsnofoot` → INFO (acceptable draft mode).
- If `a4paper` → MAJOR if US-letter conference (note: reduces side margins).
- If `romanappendices` → INFO (just noting it).
- If `10pt` omitted → INFO (IEEEtran defaults to 10pt for conference).

---

### CHECK-02 — Required & Forbidden Packages

**Grep for all \usepackage lines:**
```bash
grep -n "\\\\usepackage" "$TEX_FILE"
```

**Required packages (flag if ABSENT):**
| Package | Severity if absent | Reason |
|---|---|---|
| `cite` | MAJOR | Without it, citations are not sorted/compressed IEEE-style |
| `graphicx` | MAJOR | Required for `\includegraphics` |
| `amsmath` | MINOR | Needed for `{align}`, `\eqref`, etc. |

**Forbidden packages (flag if PRESENT):**
| Package | Severity | Reason |
|---|---|---|
| `geometry` | CRITICAL | Overrides IEEE margins |
| `fullpage` | CRITICAL | Overrides IEEE margins |
| `anysize` | CRITICAL | Overrides IEEE margins |
| `vmargin` | CRITICAL | Overrides IEEE margins |
| `pslatex` | MAJOR | Overrides IEEE fonts |
| `mathptm` | MAJOR | Overrides IEEE fonts |
| `mathpazo` | MAJOR | Overrides IEEE fonts |
| `times` | MAJOR | Overrides IEEE fonts |
| `balance` | MAJOR | Unreliable with IEEEtran bibliography |
| `flushend` | MAJOR | Known spacing anomaly with IEEEtran lists |
| `subfigure` | MAJOR | Deprecated; use `subfig` with `caption=false` |
| `algorithm` (float) | MINOR | IEEE only uses `{figure}` and `{table}` floats |
| `algorithm2e` | MINOR | Same — caption style not controlled by IEEEtran |
| `multicol` | MAJOR | Do not use — interferes with two-column layout |
| `cuted` | MAJOR | IEEE prohibits material across middle of two columns |
| `midfloat` | MAJOR | Same reason |

**Package option checks:**
- If `subfig` present, verify option `caption=false`:
  ```bash
  grep -n "subfig" "$TEX_FILE"
  ```
  If `caption=false` is absent → MAJOR.

---

### CHECK-03 — `\IEEEoverridecommandlockouts`

```bash
grep -n "IEEEoverridecommandlockouts" "$TEX_FILE"
```

- If present AND `\thanks{}` exists in `\author{}` → INFO (correct use).
- If present AND NO `\thanks{}` → MINOR (unnecessary; clutters preamble).
- If absent AND `\thanks{}` is used → MAJOR (funding footnote will silently fail in
  conference mode).

---

### CHECK-04 — Title

```bash
grep -n "\\\\title{" "$TEX_FILE"
# Extract full title block (may span multiple lines):
sed -n '/\\title{/,/^}/p' "$TEX_FILE" | head -20
```

**Rules (check every item):**
- **Math mode in title** — scan for `$...$`, `\(...\)`, `\[...\]` inside `\title{}`:
  → CRITICAL if found. IEEEXplore cannot index math.
- **Special characters** — scan for `\%, \&, \#, \_, \^, \~` (unescaped OR escaped):
  If any of these appear structurally (not as content), → CRITICAL.
- **Subtitles** — check for `\\{\footnotesize...}` or `\\[...]{...}` pattern under title:
  → MAJOR. IEEEXplore does not capture subtitles.
- **Footnotes in title** (`\footnote{}` — not `\thanks{}`): → CRITICAL.
- **Placeholder text**: check for "Conference Paper Title" verbatim → CRITICAL (template not cleaned).
- **Capitalization check** — flag uncapitalized significant words or over-capitalized
  prepositions/articles: → MINOR (MANUAL fix required — content decision).
  Words that should NOT be capitalized unless first/last: a, an, and, as, at, but, by,
  for, in, nor, of, on, or, the, to, up.
- **Line breaks** `\\` in title: → INFO if present (acceptable for line-length equalization).

---

### CHECK-05 — Author Block

```bash
# Extract full \author{} block:
sed -n '/\\author{/,/^}/p' "$TEX_FILE" | head -60
grep -n "\\\\IEEEauthorblockN\|\\\\IEEEauthorblockA\|\\\\IEEEauthorrefmark\
\|\\\\IEEEmembership\|\\\\and\b" "$TEX_FILE"
```

**Conference-mode structure check:**
- Must use `\IEEEauthorblockN{}` for names and `\IEEEauthorblockA{}` for affiliations.
  If raw `\author{Name}` without blocks → MAJOR.
- Authors separated by `\and`.
- Each `\IEEEauthorblockA` must contain: dept (italic), institution (italic), City/Country,
  email OR ORCID.

**Placeholder check:**
```bash
grep -n "Given Name Surname\|dept\. name of organization\|email address or ORCID\
\|name of organization (of Aff\.)" "$TEX_FILE"
```
→ CRITICAL for any match (template not cleaned).

**Disabled commands in conference mode:**
```bash
grep -n "\\\\IEEEmembership\|\\\\IEEEpubid\b\|\\\\markboth\|\\\\IEEEbiography\
\|\\\\IEEEbiographynophoto\|\\\\IEEEpubidadjcol" "$TEX_FILE"
```
- `\IEEEmembership` → MAJOR (disabled in conference mode; silently produces nothing).
- `\IEEEpubid` → MAJOR (must NOT appear in camera-ready conference papers; bottom margin
  already adjusted by IEEEtran automatically).
- `\markboth` → MINOR (has no effect in conference mode; unnecessary).
- `\IEEEbiography` / `\IEEEbiographynophoto` → MAJOR (disabled in conference mode).

**`\thanks{}` check:**
```bash
grep -n "\\\\thanks{" "$TEX_FILE"
```
- If `\thanks{}` present AND `\IEEEoverridecommandlockouts` absent → MAJOR.
- If `\thanks{}` contains placeholder "Identify applicable funding agency" → CRITICAL.

---

### CHECK-06 — Abstract

```bash
sed -n '/\\begin{abstract}/,/\\end{abstract}/p' "$TEX_FILE"
```

**Rules:**
- Must use `\begin{abstract}...\end{abstract}` (not a manual heading).
- **Math in abstract**: scan for `$`, `\(`, `\[` inside abstract block → CRITICAL.
- **Citations in abstract**: scan for `\cite{` → CRITICAL.
- **Footnotes in abstract**: scan for `\footnote{` → CRITICAL.
- **Special characters** (structural): → CRITICAL.
- **Placeholder text** "This document is a model": → CRITICAL.
- **Length** — count words; if >250 words → MINOR (conference abstracts typically ≤200 words).

---

### CHECK-07 — Index Terms / Keywords

```bash
grep -n "\\\\begin{IEEEkeywords}\|\\\\end{IEEEkeywords}\|\\\\begin{keywords}" "$TEX_FILE"
sed -n '/\\begin{IEEEkeywords}/,/\\end{IEEEkeywords}/p' "$TEX_FILE"
```

**Rules:**
- Must use `\begin{IEEEkeywords}` (not `\begin{keywords}` or manual bold heading).
  If wrong environment → MAJOR.
- Math or special characters inside → MAJOR.
- Placeholder "component, formatting, style, styling, insert" → CRITICAL.
- Fewer than 3 keywords → MINOR.
- Missing period at end of keyword list → MINOR.

---

### CHECK-08 — Section Headings

```bash
grep -n "\\\\section\|\\\\subsection\|\\\\subsubsection\|\\\\paragraph" "$TEX_FILE"
```

**Rules:**
- Check for manually numbered sections: `\section{I. Introduction}` pattern → MAJOR.
  (IEEEtran numbers automatically.)
- `\section*` for Acknowledgment and References → correct; flag if starred section is
  used for a content section → MINOR.
- `\IEEEraisesectionheading` → MAJOR if present (compsoc journal only; wrong mode).
- `\paragraph` depth: acceptable in conference mode unless paper has >4 levels of nesting → MINOR.
- Subsections with fewer than 2 sub-topics at that level → MINOR (MANUAL).
- Flag template heading content that wasn't replaced:
  ```bash
  grep -n "Maintain.*Integrity\|Abbreviations and Acronyms\|Prepare Your Paper Before\
  \|Some Common Mistakes\|Authors and Affiliations\|Identify the Headings\
  \|Figures and Tables\|LATEX-Specific Advice" "$TEX_FILE"
  ```
  → CRITICAL for any match.

---

### CHECK-09 — Forbidden `{eqnarray}` Environment

```bash
grep -n "\\\\begin{eqnarray}\|\\\\end{eqnarray}" "$TEX_FILE"
```

**CRITICAL if found.** The official IEEE 2024 conference template explicitly forbids `{eqnarray}`.
Must be replaced with `{align}` or `{IEEEeqnarray}`.
- fix_type: AUTO (mechanical replacement is safe IF spacing around `&` is checked).
- NOTE: `{eqnarray*}` is also forbidden → same severity.

---

### CHECK-10 — Equations

```bash
grep -n "\\\\begin{equation\|\\\\begin{align\|\\\\begin{IEEEeqnarray\
\|\\\\begin{displaymath\|\\\\begin{multline" "$TEX_FILE"
```

**Rules for each equation environment found:**
- `\nonumber` inside `{array}` → MAJOR (has no effect; can suppress wanted equation numbers).
  ```bash
  grep -n "\\\\nonumber" "$TEX_FILE"
  # Then check context: is it inside {array}?
  ```
- `{subequations}` present → INFO (warn that it increments main counter even without
  displayed numbers; equation numbers may appear to skip if authors forget this).
- Hardcoded equation references `(1)` or `Eq.~(1)` in text → MAJOR.
  ```bash
  grep -n "Eq\.\s*(\|equation\s*(\\|(\s*[0-9]\+\s*)" "$TEX_FILE"
  ```
  Exception: `\eqref{...}` is correct.
- `\eqref{}` used without `amsmath` loaded → MAJOR.
- Long equations: scan for lines >80 characters inside equation environments → MINOR (MANUAL).
  They may overflow column width.
- Symbols not defined before or immediately after first equation use → MINOR (MANUAL).
- Missing punctuation (comma/period) after equation that is part of a sentence → MINOR (MANUAL).

---

### CHECK-11 — Figures

```bash
grep -n "\\\\begin{figure\|\\\\end{figure\|\\\\includegraphics\
\|\\\\centering\|\\\\begin{center}\|\\\\caption\|\\\\label" "$TEX_FILE"
```

**For each figure block, check:**

**`\label` before `\caption`** (most critical figure mistake):
```bash
# Extract each figure block and check relative order of \label vs \caption:
awk '/\\begin\{figure/{start=NR} start && /\\label/{label=NR} start && /\\caption/{cap=NR}
     start && /\\end\{figure/{
       if(label < cap && label > 0) print "LINE "label": \\label before \\caption in figure"
       start=0; label=0; cap=0
     }' "$TEX_FILE"
```
→ CRITICAL if `\label` appears before `\caption` in any float.
  fix_type: AUTO (swap the two lines).

**`\begin{center}` inside figure** instead of `\centering`:
```bash
grep -n "\\\\begin{center}" "$TEX_FILE"
```
→ MINOR. `{center}` adds unwanted vertical space. `\centering` is correct.
  fix_type: AUTO.

**Figure caption position** — caption must be BELOW figure (after `\includegraphics`):
- Visually check in the extracted block whether `\caption` comes after `\includegraphics`.
  → MAJOR if caption is above `\includegraphics`.
  fix_type: AUTO (reorder lines within figure block).

**`\includegraphics` without `graphicx`**: already caught in CHECK-02.

**Obsolete graphics commands:**
```bash
grep -n "\\\\psfig\|\\\\epsf\b\|\\\\epsfig" "$TEX_FILE"
```
→ MAJOR. Replace with `\includegraphics`.
  fix_type: AUTO for simple cases.

**Float placement options:**
```bash
grep -n "\\\\begin{figure}\[h\]\|\\\\begin{figure}\[here\]\|\\\\begin{figure}\[H\]" "$TEX_FILE"
```
→ MAJOR. IEEE strongly prefers `[!t]` (top). `[h]`, `[here]`, `[H]` can cause figures to
  appear in the first column of the first page (prohibited).
  fix_type: CONFIRM (change `[h]` → `[!t]` needs user approval).

**Double-column figure with `[!b]` but no stfloats:**
```bash
grep -n "\\\\begin{figure\*}" "$TEX_FILE"
```
If `[!b]` used and `stfloats` or `dblfloatfix` not loaded → MAJOR.

**Subfig without `caption=false`**: caught in CHECK-02.

**Figure axis labels** — cannot be checked from LaTeX source alone; flag as INFO:
"Verify figure axis labels use words (not symbols/abbreviations), 8pt Times New Roman."

---

### CHECK-12 — Tables

```bash
grep -n "\\\\begin{table\|\\\\end{table\|\\\\caption\|\\\\label\
\|\\\\begin{tabular\|\\\\arraystretch" "$TEX_FILE"
```

**For each table block:**

**`\label` before `\caption`** (same critical issue as figures):
```bash
awk '/\\begin\{table/{start=NR} start && /\\label/{label=NR} start && /\\caption/{cap=NR}
     start && /\\end\{table/{
       if(label < cap && label > 0) print "LINE "label": \\label before \\caption in table"
       start=0; label=0; cap=0
     }' "$TEX_FILE"
```
→ CRITICAL. fix_type: AUTO.

**Table caption position** — caption must be ABOVE table (before `\begin{tabular}`):
- Check whether `\caption` comes before or after `\begin{tabular}`.
  → MAJOR if caption is below.
  fix_type: AUTO.

**Missing `\renewcommand{\arraystretch}{1.3}`:**
```bash
grep -n "arraystretch" "$TEX_FILE"
```
If absent in any table → MINOR. (Rows will be tighter than IEEE prefers.)
  fix_type: AUTO (add before `\begin{tabular}`).

**`\footnote{}` inside `{tabular}`:**
```bash
grep -n "\\\\footnote{" "$TEX_FILE"
# Then check if these are inside tabular environments
```
→ MAJOR. Must use `\footnotemark`/`\footnotetext` or `threeparttable`.

**Table footnote letters**: should use letters (`$^{\mathrm{a}}$`) not numbers.
→ MINOR if numbers are used (MANUAL fix).

**`\upshape` for units in table captions:**
If a table caption contains units that look like math-mode text (e.g., `Hz`, `dB`)
without `\upshape` → MINOR.

---

### CHECK-13 — Citations in Text

```bash
grep -n "\\\\cite{" "$TEX_FILE"
```

**Rules:**
- Multiple citations: should be `\cite{a,b,c}` not `\cite{a}\cite{b}\cite{c}`.
  ```bash
  # Find consecutive \cite commands:
  grep -n "\\\\cite{[^}]*}[[:space:]]*\\\\cite{" "$TEX_FILE"
  ```
  → MINOR. fix_type: AUTO (merge into single `\cite`).
- "Ref. [X]" or "reference [X]" in body text (not at sentence start):
  ```bash
  grep -n "\bRef\.\s*\\\\\|reference\s*\\\\cite" "$TEX_FILE"
  ```
  → MINOR. fix_type: CONFIRM.
- Hardcoded reference numbers `[1]` or `[1,2]` in text instead of `\cite{}`:
  ```bash
  grep -n "\[[0-9]\+\]" "$TEX_FILE"
  ```
  → MAJOR. fix_type: MANUAL (need to know which BibTeX key maps to which number).
- Citation in abstract: → CRITICAL (caught in CHECK-06).

---

### CHECK-14 — Bibliography & BibTeX

```bash
grep -n "\\\\bibliographystyle\|\\\\bibliography\b\|\\\\begin{thebibliography}" "$TEX_FILE"
```

**If BibTeX is used:**
- `\bibliographystyle{IEEEtran}` must be present → MAJOR if absent.
- `IEEEabrv` must be listed BEFORE the user's `.bib` file:
  `\bibliography{IEEEabrv,mybibfile}` → if order is reversed → MAJOR.
  fix_type: AUTO.
- `IEEEfull.bib` must NOT be used for IEEE submissions → MAJOR.
  fix_type: AUTO (swap to IEEEabrv).

**If manual `{thebibliography}` is used:**
- Check each `\bibitem` against IEEE reference format rules:
  - Journal: `Author, "Title," Journal Abbrev., vol. X, no. Y, pp. Z–ZZ, Month Year.`
  - Conference: `Author, "Title," in Proc. Conference, City, Year, pp. X–Y.`
  - Capital letters: only first word of paper title (+ proper nouns, element symbols).
  - En-dash for page ranges (`--` in LaTeX, renders as –).
  - "et al." usage: flag if fewer than 6 authors listed as "et al." → MINOR.
  - "Ref." / "reference" misuse (already caught in CHECK-13).
  - Missing "Proc." before conference names → MINOR (MANUAL).
  - Footnotes inside reference list → MAJOR.
  - Period after "et" in "et al." → flag "et. al." → MINOR. fix_type: AUTO.
  - Verify template bibitems b1-b11 were replaced:
    ```bash
    grep -n "\\\\bibitem{b[0-9]" "$TEX_FILE"
    ```
    → CRITICAL if any found.

**Cross-reference check:**
```bash
grep -n "\\\\ref{\|\\\\eqref{\|\\\\pageref{" "$TEX_FILE"
```
- Ensure every `\ref{}` key has a corresponding `\label{}`:
  ```bash
  grep -o "\\\\ref{[^}]*}" "$TEX_FILE" | sed 's/\\ref{//;s/}//' | sort -u > /tmp/refs.txt
  grep -o "\\\\label{[^}]*}" "$TEX_FILE" | sed 's/\\label{//;s/}//' | sort -u > /tmp/labels.txt
  comm -23 /tmp/refs.txt /tmp/labels.txt
  ```
  Any key in refs but not labels → MAJOR (undefined reference).

---

### CHECK-15 — Acknowledgment Section

```bash
grep -n "Acknowledgment\|Acknowledgement\|acknowledgment\|acknowledgement" "$TEX_FILE"
```

**Rules:**
- Correct spelling: "Acknowledgment" (no 'e' after 'g') for American English conferences.
  "Acknowledgement" → MINOR. fix_type: CONFIRM (spelling change needs approval).
- Must be `\section*{Acknowledgment}` (starred = unnumbered) → flag if `\section{Acknowledgment}`
  (would add a Roman numeral) → MAJOR. fix_type: AUTO.
- Stilted expressions: flag "one of us (...) thanks" → MINOR (MANUAL).
- Funding acknowledgment in body instead of `\thanks{}` footnote → MINOR (MANUAL).
- Plural "Acknowledgments" (Computer Society style) on standard conference paper → INFO.

---

### CHECK-16 — Appendices

```bash
grep -n "\\\\appendix\|\\\\appendices" "$TEX_FILE"
```

**Rules:**
- Single appendix: `\appendix` (not `\appendices`). After `\appendix`, `\section` is
  disabled — check if `\section{}` appears after `\appendix`:
  ```bash
  awk '/\\appendix$/{found=1} found && /\\section{/' "$TEX_FILE"
  ```
  → MAJOR if `\section` appears after `\appendix` (use `\subsection` instead or use `\appendices`).
- Multiple appendices: `\appendices` followed by `\section{}` for each — correct.
- Equation numbering in appendices: if equations present in appendix and no
  `\renewcommand{\theequation}{\thesection.\arabic{equation}}` → MINOR (MANUAL — author choice).

---

### CHECK-17 — Template Boilerplate (CRITICAL)

Every occurrence of any template text that was not replaced is a submission blocker.

```bash
grep -n "Conference Paper Title\|Given Name Surname\
\|dept\. name of organization\|name of organization (of Aff\.)\
\|email address or ORCID\|This document is a model and instructions\
\|Identify applicable funding agency\|Please observe the conference page limits\
\|model and instructions for.*LaTeX\|b1.*G\. Eason.*Noble\
\|IEEEtran\.cls file define the components\
\|component, formatting, style, styling, insert\
\|Keep your text and graphic files separate\
\|Note: Sub-titles are not captured" "$TEX_FILE"
```
→ CRITICAL for every match.

Check for red text block at end:
```bash
grep -n "\\\\color{red}\|IEEE conference templates contain guidance text" "$TEX_FILE"
```
→ CRITICAL.

---

### CHECK-18 — Cross-References & Labels

```bash
grep -n "\\\\label{" "$TEX_FILE"
```

**Label naming convention check:**
- Consistent prefix use (`fig:`, `tab:`, `eq:`, `sec:`, `alg:`) → INFO if inconsistent.
- Any `\label` without corresponding prefix → INFO.

**Hardcoded cross-references:**
```bash
grep -n "Fig\.\s*[0-9]\+\|Table\s*[IVX]\+\|Section\s*[IVX]\+\|(eq\.\s*[0-9]" "$TEX_FILE"
```
→ MAJOR for hardcoded figure/table/section/equation numbers.
  fix_type: MANUAL (need to know which label corresponds to which number).

**`\ref` vs `\eqref`:**
- Equation references should use `\eqref{}` not `\ref{}`:
  ```bash
  grep -n "\\\\ref{eq\|\\\\ref{eqn" "$TEX_FILE"
  ```
  → MINOR. fix_type: AUTO (change `\ref{eq` → `\eqref{eq`).

---

### CHECK-19 — Last-Page Column Balance

```bash
grep -n "\\\\newpage\|\\\\enlargethispage\|\\\\IEEEtriggeratref\|\\\\columnbreak" "$TEX_FILE"
```

- If none of these are present: → INFO.
  "Last-page column balance not addressed. Consider adding `\IEEEtriggeratref{N}` or
  `\newpage` before the bibliography."
- If `flushend` or `balance` package loaded: → MAJOR (caught in CHECK-02).

---

### CHECK-20 — Margin & Spacing Overrides

```bash
grep -n "\\\\setlength{\\\\oddsidemargin\|\\\\setlength{\\\\topmargin\
\|\\\\setlength{\\\\textwidth\|\\\\setlength{\\\\textheight\
\|\\\\setlength{\\\\columnsep\|\\\\addtolength{\\\\textwidth\
\|\\\\vspace\|\\\\hspace\|\\\\vskip\|\\\\hskip" "$TEX_FILE"
```

- Direct margin/dimension overrides (`\oddsidemargin`, `\topmargin`, `\textwidth`,
  `\textheight`) → CRITICAL.
- `\vspace{}` or `\hspace{}` around floats:
  - `\vspace{-Xpt}` hacks before `\begin{figure}` → MAJOR (should not be needed).
  - `\vspace{Xpt}` after `\end{figure}` → MAJOR.
  - Exception: `\vspace*{-3pt}` correction for double-column float underfull vboxes → MINOR/INFO.
- If CLASSINPUTs are used instead of direct overrides → INFO (acceptable alternative).

---

## Audit Report Format

After running all checks, write the report to `{tex_file_stem}_audit_report.md`:

```markdown
# IEEE Audit Report
**File:** `path/to/paper.tex`
**Date:** YYYY-MM-DD HH:MM
**Auditor:** ieee-audit agent v1.0
**Total issues found:** N (CRITICAL: X | MAJOR: Y | MINOR: Z | INFO: W)

---

## Summary Table

| ID | Line | Severity | Category | Fix Type | Short Description |
|----|------|----------|----------|----------|-------------------|
| A01 | 12 | CRITICAL | Document Class | AUTO | Wrong class option |
| A02 | 45 | CRITICAL | Template | MANUAL | Title placeholder not replaced |
...

---

## Detailed Findings

### A01 — [CRITICAL] Document Class
**Line:** 1
**Found:** `\documentclass[journal]{IEEEtran}`
**Rule:** Conference papers must use `\documentclass[conference]{IEEEtran}`.
**Fix type:** AUTO
**Fix:**
```diff
- \documentclass[journal]{IEEEtran}
+ \documentclass[conference]{IEEEtran}
```

### A02 — [CRITICAL] Template Boilerplate — Title
**Line:** 16
**Found:** `\title{Conference Paper Title*\\`
**Rule:** Template placeholder must be replaced with actual paper title.
**Fix type:** MANUAL (author must provide actual title)
**Fix:** Replace with: `\title{Your Actual Paper Title}`

[... continue for every finding ...]

---

## Non-Issues (Checked & Passed)

List every CHECK that found no problems:
- CHECK-01: Document class — PASS
- CHECK-09: Forbidden {eqnarray} — PASS
...

---

## Fix Readiness

| Category | AUTO fixes | CONFIRM fixes | MANUAL fixes |
|----------|-----------|--------------|-------------|
| Count | N | N | N |
| Estimated fix time | — | — | Author action needed |

**Recommendation:** [Ready for ieee-fix agent | Author action required first | Major rework needed]
```

---

## Severity Definitions (for report)

| Severity | Meaning |
|---|---|
| CRITICAL | Will cause: submission rejection, IEEEXplore indexing failure, or paper not published. Fix before anything else. |
| MAJOR | Will cause: copy-editor rejection, formatting violation clearly visible in output, or broken LaTeX compilation. |
| MINOR | Style deviation or best-practice violation; paper is submittable but not optimal. |
| INFO | Informational note; no action strictly required. |

## Fix Type Definitions (for ieee-fix agent)

| Fix Type | Meaning |
|---|---|
| AUTO | Pure LaTeX command/environment swap. No content affected. Fix agent applies without asking. |
| CONFIRM | Mechanical fix but touches visible text or layout. Fix agent shows diff and waits for yes/no. |
| MANUAL | Requires author judgment (content, wording, citation keys). Fix agent flags and skips. |
| NONE | No fix possible or needed. |
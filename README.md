# medreview — a PAT-style review agent for medical manuscripts

Reimplements the four-stage pipeline of Google's Paper Assistant Tool
(Jayaram et al., arXiv:2606.28277) as Claude Code subagents, retargeted from
CS/maths to clinical, epidemiological and health-data-science papers.

## What changed vs the CS version, and why

PAT verifies proofs by constructing counterexamples — possible because a proof
is self-contained on the page. Clinical claims aren't: you can't see the data,
so you can't refute the result, only judge whether each analytic choice is
**justified and correctly reported** and flag likely bias and its direction.
So the reviewers changed substance, not architecture:

| CS reviewer | Medical reviewer |
|---|---|
| theory (proofs, counterexamples) | **stats** — survival, competing risks, missing data, prediction models (TRIPOD+AI) |
| methods (ML experiments) | **reporting** — STROBE/RECORD/CONSORT checklist audit, cohort integrity, consistency |
| prose (framing, citations) | **clinical** — spin, plausibility, ethics/governance |

Grounding also changed: PAT search-grounds to catch invented theorems; here
the synthesiser grounds against **PubMed, ClinicalTrials.gov and Scholar
Gateway** — verifying citations, checking trial registration dates precede
enrolment, and confirming guideline claims before they reach the review.

## Setup

```bash
cd medreview
pip install pymupdf          # for PDF → Markdown
claude                       # subagents + /review-paper load at session start
```

On first run, authenticate the MCP connectors (`/mcp` inside Claude Code, or
`claude mcp add`). `.mcp.json` lists PubMed, Clinical Trials and Scholar
Gateway; the synthesiser inherits whatever is connected, so you don't hard-code
tool names anywhere. If a connector isn't available, grounding degrades to web
search — findings still surface, just less strongly verified.

## Usage

```
/review-paper papers/my-manuscript.pdf
```

Outputs in `reviews/<paper-name>/`:
```
segmentation.yaml        # design + standard + segment plan
report-seg-01.yaml       # raw per-segment reviewer reports
REVIEW.md                # final grounded review
```

## Fits your workflow (Positron / R / Quarto)

`REVIEW.md` is plain Markdown, so drop it straight into a Quarto doc and
render alongside a manuscript, or `knitr::knit()` the segmentation YAML into a
tracked-changes table.

### As a `targets` step

A review run can be a reproducible target alongside your R analysis. Claude
Code runs non-interactively with `claude -p`, so you can shell out and pin the
resulting `REVIEW.md` for provenance:

```r
# _targets.R
library(targets)
tar_option_set(packages = c("fs"))

review_paper <- function(pdf) {
  stem <- fs::path_ext_remove(fs::path_file(pdf))
  out  <- fs::path("reviews", stem, "REVIEW.md")
  # -p runs headless; run from the project root so paths resolve.
  system2("claude", c("-p", shQuote(sprintf("/review-paper %s", pdf))))
  stopifnot(fs::file_exists(out))
  out
}

list(
  tar_target(manuscript, "papers/my-draft.pdf", format = "file"),
  tar_target(review, review_paper(manuscript), format = "file")
)
```

`format = "file"` makes `targets` invalidate the review only when the PDF
changes. Note this consumes tokens on each rebuild (several parallel
subagents), so keep manuscripts as explicit file targets rather than
re-running on every `tar_make()`.

## Extending
- Add checklists to `checklists/` (STROBE.md, CONSORT.md, PRISMA.md…) — the
  reporting-reviewer reads them by name.
- For a pure prediction-model paper, the segmenter routes to TRIPOD+AI
  automatically; the reference is already in `checklists/`.

## Honest limits (mirroring PAT §3.2)
- Findings are inferred from the manuscript, not the data — treat REVIEW.md as
  a checklist of questions to verify, not a verdict.
- No SPOT-style benchmark exists for medical error detection, so there's no
  clean accuracy number to quote; ground truth for "was this analysis wrong"
  is genuinely contested.
- False positives survive grounding sometimes — model misunderstandings happen.
- PDF parsing quality bounds everything; eyeball the converted `.md` if a
  finding looks odd.
- **Governance**: routing others' confidential submissions through a cloud
  model is often prohibited and always an IG decision. Author-side drafts only.

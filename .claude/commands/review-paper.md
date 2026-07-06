---
description: Run the full medical review pipeline (segment → parallel deep review → grounded synthesis) on a manuscript
argument-hint: <path-to-manuscript.pdf-or-md>
---

Run the medical manuscript review pipeline on: $ARGUMENTS

You are the orchestrator. Coordinate only — do NOT review the paper yourself
in the main context, to keep it clean.

## Stage 0 — Prepare (resolve absolute paths FIRST)

Working directory can vary (e.g. launched from a Positron terminal that isn't
at the repo root), so establish absolute paths before anything else and pass
ABSOLUTE paths to every subagent. Do NOT rely on relative paths.

1. Find the project root: run
   `git rev-parse --show-toplevel 2>/dev/null || pwd`
   — call this `$ROOT`. Sanity-check that `$ROOT/checklists/README.md` exists;
   if not, ask the user to confirm the medreview project location.
2. Resolve the manuscript to an absolute path. If the user gave a relative
   path, try it against the current dir and against `$ROOT/papers/`. Confirm
   the file exists before proceeding.
3. If it's a PDF, convert to Markdown with page markers and extract figure
   and table images:
   `python "$ROOT/scripts/pdf_to_md.py" "<abs-pdf-path>"`
   Writes a sibling `.md` with `<!-- page N -->` markers. It also renders any
   page whose text carries a figure caption (e.g. "Figure 1", "FIGURE 2 |",
   "Fig. 3.") to a PNG under a sibling `<stem>_figures/` directory, and
   inserts a `<!-- figure image: /abs/path/..._figures/page-NNN_figK.png -->`
   comment right after that page's marker; it does the same for any page
   with a table caption (e.g. "Table 1", "TABLE 2 |"), rendering a
   whole-page PNG and inserting a
   `<!-- table image: /abs/path/..._figures/page-NNN_tableK.png -->` comment
   (no row/column structure extraction is attempted — the image is for
   visually verifying exact cell values/alignment, since text extraction
   scrambles multi-column tables). Every reviewer already reads the full
   manuscript, so both pointers reach them inline; you do NOT need to
   enumerate or pass image paths to reviewers yourself. Let `$PAPER` be the
   absolute path to the Markdown. The console output states how many figure
   and table images were extracted — mention both counts in Stage 5.
4. Derive `<paper-name>` (the file stem) and create the output dir
   `$ROOT/reviews/<paper-name>/`.
5. The checklists live in `$ROOT/checklists/`. You will pass absolute
   checklist paths to the reporting reviewer.

## Stage 1+2 — Segment, classify design, budget

Invoke **paper-segmenter** with `$PAPER` (absolute). Tell it the checklists
directory is `$ROOT/checklists/` and it should name checklist FILES (see
`$ROOT/checklists/README.md`). Save its YAML to
`$ROOT/reviews/<paper-name>/segmentation.yaml`. Check it names a study design
and reporting standard(s), and that every segment has a valid reviewer/tier.
If the plan is degenerate (1 segment, or >8), ask it to redo once.

## Stage 3 — Deep review (parallel)

For EVERY segment, spawn its assigned subagent — **stats-reviewer**,
**reporting-reviewer**, or **clinical-reviewer** — ALL IN PARALLEL in a single
message (independent, isolated contexts).

Pass each, using ABSOLUTE paths:
1. `$PAPER` — the full manuscript ("read the whole paper for context").
2. The segment id / theme / location / tier / focus ("review only this").
3. For **reporting-reviewer** additionally: the absolute path(s) of the
   checklist file(s) named by the segmenter, e.g.
   `$ROOT/checklists/STROBE.md` and `$ROOT/checklists/RECORD.md`.

Save each YAML report to
`$ROOT/reviews/<paper-name>/report-<segment-id>.yaml`. Re-invoke once if a
report is malformed.

## Stage 4 — Grounded synthesis

Invoke **review-synthesizer** with `$PAPER`, all report paths (absolute), and
output path `$ROOT/reviews/<paper-name>/REVIEW.md`. It uses the PubMed /
Clinical Trials / Scholar Gateway MCP connectors to ground citations,
registrations and guideline claims.

## Stage 5 — Report back

Tell the user: study design, findings count by severity, the 2–3 most
important findings in one line each, any failed groundings, how many figure
and table images were extracted, and the path to `REVIEW.md`. Do not paste
the whole review into chat.

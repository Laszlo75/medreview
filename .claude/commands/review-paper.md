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
3. If it's a PDF, convert to Markdown with page markers:
   `python "$ROOT/scripts/pdf_to_md.py" "<abs-pdf-path>"`
   (writes a sibling `.md` with `<!-- page N -->` markers). Keep the PDF path
   too, for figures. Let `$PAPER` be the absolute path to the Markdown.
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
important findings in one line each, any failed groundings, and the path to
`REVIEW.md`. Do not paste the whole review into chat.

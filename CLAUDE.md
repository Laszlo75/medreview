# medreview

A Claude Code review pipeline for **medical / clinical / health-data-science
manuscripts**, adapted from Google's Paper Assistant Tool
(Jayaram et al. 2026, arXiv:2606.28277). PAT was built for CS/maths; this
variant keeps its four-stage inference-scaling architecture but retargets the
review substance at clinical research.

## Architecture

| PAT stage | Here |
|---|---|
| 1. Segmentation | `paper-segmenter` — also classifies study design + reporting standard |
| 2. Adaptive budget | tier → model: light=haiku-ish, medium=sonnet, high=opus |
| 3. Deep Review | `stats-reviewer` (opus), `reporting-reviewer` (sonnet), `clinical-reviewer` (sonnet), in parallel |
| 4. Synthesis + grounding | `review-synthesizer` (opus) — grounds via PubMed / ClinicalTrials / Scholar Gateway MCP |

Entry point: `/review-paper <path>`.

## The one conceptual change from PAT

In CS, the hard-verification object is a **proof**, and the killer move is a
**counterexample** — self-contained on the page. In medicine you usually
can't see the data, so you can't prove a result wrong. Reviewers therefore
shift from "prove wrong / counterexample" to **"flag as unjustified / likely
biased, and pose a question to the author."** Recall over refutation.
Every clinical finding is framed as a question, never a verdict.

## Conventions
- Manuscripts in `papers/`, outputs in `reviews/<paper-name>/`.
- Reviewers are read-only; only the synthesizer writes (and it inherits MCP).
- Every finding: exact location + verbatim quote (or, for basis: absence
  findings, the terms searched for) + evidence + severity + confidence +
  basis. No anchor → discard.
- Reporting checklists in `checklists/` (RECORD, TRIPOD+AI provided; add
  STROBE/CONSORT/PRISMA/STARD as needed). `reporting-reviewer` reads these.
- This is a **Role 1** tool (author-side, pre-submission). Not for producing
  peer reviews you submit as your own.

## Governance note (UK)
Feeding an unpublished manuscript built on UKTR/NHSBT data to a cloud model
is an information-governance decision. Fine for your own drafts pre-submission;
a different conversation for others' confidential submissions, which several
venues prohibit routing through external AI at all.

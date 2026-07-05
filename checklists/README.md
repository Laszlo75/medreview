# Reporting-standard checklists

`reporting-reviewer` reads the file(s) named in the segmenter's
`reporting_standard` field and audits the manuscript item by item. Files are
written as **reviewer audit lines** ("check that X is reported / justified"),
paraphrased from the official guidelines — they are not verbatim copies. For
the authoritative wording always cite the source publication (linked at the
top of each file) and the EQUATOR Network (https://www.equator-network.org).

## Which checklist for which design

| Study design | File(s) to load |
|---|---|
| Cohort / case-control / cross-sectional | `STROBE.md` |
| …using routine/registry data (UKTR, NHSBT, HES, SRTR) | `STROBE.md` + `RECORD.md` |
| Randomised trial (report) | `CONSORT.md` (CONSORT 2025) |
| Trial protocol | `SPIRIT.md` (SPIRIT 2025) |
| Prediction / prognostic model (regression or ML) | `TRIPOD-AI.md` |
| Diagnostic accuracy | `STARD.md` |
| Systematic review / meta-analysis | `PRISMA.md` |
| Quality improvement / audit / service evaluation | `SQUIRE.md` |

Multiple can apply (e.g. a registry prediction model → `RECORD.md` +
`TRIPOD-AI.md`). Load all that fit.

## AI-specific extensions (load in addition, when relevant)
- Prediction/ML model → TRIPOD+AI already covers ML (`TRIPOD-AI.md`).
- AI intervention **trial** → CONSORT-AI; **protocol** → SPIRIT-AI;
  early-stage clinical evaluation of decision-support AI → DECIDE-AI.
- LLM-based study → TRIPOD-LLM.
These aren't yet written as files here; the reviewer should apply its own
knowledge of them and flag that a dedicated extension applies. Add them as
`.md` files when you start seeing those manuscripts.

## Editorial completeness note
STROBE (2007), RECORD (2015), PRISMA 2020, STARD 2015 and SQUIRE 2.0 (2016)
are stable. CONSORT and SPIRIT were both updated in **2025** (harmonised),
and TRIPOD+AI dates from **2024** — these three superseded their earlier
versions, which should no longer be used.

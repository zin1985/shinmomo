# Progress dashboard data

`project_progress.json` is the machine-readable source for the public progress dashboard.

## Rules

- Percent values describe the scope named in each track. A local 100% does not mean the whole game is complete.
- `overall` is calculated by the dashboard as the weighted mean of every track's `percent * weight`.
- Scheduled analysis must update this file after each analysis cycle when evidence changes a percentage, status, scope, or queue priority.
- Every changed percentage must keep a short evidence note.
- Confirmed facts, strong hypotheses, and estimates must remain distinguishable in analysis documents.
- Do not store ROM binaries, savestates, raw copyrighted dumps, or secrets here.

## Rolling schedule

At the end of every scheduled analysis cycle:

1. Re-read the latest handoff, goals and this JSON.
2. Complete one highest-value analysis target.
3. Update affected track percentages/evidence.
4. Re-rank at least the next five schedule entries.
5. Add newly discovered blockers/targets.
6. Commit and let CI validate.

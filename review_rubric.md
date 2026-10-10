# Human review rubric

Use this rubric alongside automated correctness results. The app does not apply it, and rubric ratings should remain separate from test pass rates. Score each area from **0 to 3** and record evidence in reviewer notes.

| Score | Meaning |
| --- | --- |
| 0 | Missing, incorrect, or unsafe in a way that prevents use. |
| 1 | Major gaps; only partially usable without substantial correction. |
| 2 | Mostly sound; a few limited issues remain. |
| 3 | Clear, complete, and appropriate for the task. |

## Dimensions

1. **Scientific reasoning** — Uses the correct equation, units, assumptions, and scientific interpretation for the prompt.
2. **Edge-case reasoning** — Identifies invalid, empty, boundary, or ambiguous inputs and handles them intentionally.
3. **Clarity** — Names and structures the logic so another reviewer can understand how the result is produced.
4. **Maintainability** — Avoids unnecessary complexity and keeps the implementation easy to adapt or verify.
5. **Policy and safety awareness** — Avoids unnecessary side effects, external access, and unsupported claims about what the code guarantees.

## Reviewer notes

- Candidate/model label:
- Problem ID:
- Automated test score (reported separately):
- Rubric scores by dimension:
- Evidence for deductions or strengths:
- Follow-up tests or scientific review needed:

Do not treat a high rubric score or a passing example suite as proof of scientific validity. Validate domain assumptions and add tests before using results for consequential decisions.

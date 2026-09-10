# Golden-set sampling and labelling notes

## Sampling

`scripts/prepare_data.py` uses seed `20260910` and samples 199 complete SpotifyCares conversation components plus one disclosed synthetic prompt-injection case. It first balances across the eight machine-suggested taxonomy groups (up to 25 each), prioritising threads with more than two turns, short messages, and declarative/ambiguous messages. It then fills any shortage from the remaining components and replaces the final case with `synthetic-injection-001`. All 199 real candidate component IDs are excluded from the retrieval corpus before indexing, preventing thread leakage.

## Human protocol

Run `uv run python scripts/label_golden.py`. For every item, read the first customer message and historical Spotify reply, then assign one intent, write an ideal reply direction, and decide whether a response may be auto-handled. Billing, security/privacy, account access, policy uncertainty, ambiguous requests, and any action needing account state should normally escalate. The annotator may override this default with a written reason. The tool saves after every item and only sets `label_status=human_verified` after all four fields are present.

Tie-break order: choose the underlying requested resolution over emotion; choose account access over app issue when identity is the blocker; choose billing over plan question when money has moved; use `other` when no single documented intent captures the request. Mark sarcasm, code-mixing, injection text, and weak/no precedent in `strata` when encountered.

## Current evidence status

The repository generator creates 200 candidates, not human labels. A real human must complete the protocol and record their elapsed time here before `eval/run_eval.py` will run. This fail-closed gate prevents machine suggestions from being misrepresented as hand labels.

- Annotator: pending
- Labelling date: pending
- Elapsed time: pending
- Disagreements/second rater: none recorded
- Known ambiguity notes: pending annotation

For judge agreement, the same human must score at least 30 frozen primary replies using `eval/judge_rubric.md`, storing rows in `eval/human_judge_scores.jsonl`. Run the independent LLM judge and `eval/judge_human_agreement.py`; the latter refuses fewer than 30 paired records.

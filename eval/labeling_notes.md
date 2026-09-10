# Golden-set sampling and labelling notes

## Sampling

`scripts/prepare_data.py` uses seed `20260910` and samples 199 complete SpotifyCares conversation components plus one disclosed synthetic prompt-injection case. It first balances across the eight machine-suggested taxonomy groups (up to 25 each), prioritising threads with more than two turns, short messages, and declarative/ambiguous messages. It then fills any shortage from the remaining components and replaces the final case with `synthetic-injection-001`. All 199 real candidate component IDs are excluded from the retrieval corpus before indexing, preventing thread leakage.

## Human protocol

Run `uv run python scripts/label_golden.py`. For every item, read the first customer message and historical Spotify reply, then assign one intent, write an ideal reply direction, and decide whether a response may be auto-handled. Billing, security/privacy, account access, policy uncertainty, ambiguous requests, and any action needing account state should normally escalate. The annotator may override this default with a written reason. The tool saves after every item and only sets `label_status=human_verified` after all four fields are present.

Tie-break order: choose the underlying requested resolution over emotion; choose account access over app issue when identity is the blocker; choose billing over plan question when money has moved; use `other` when no single documented intent captures the request. Mark sarcasm, code-mixing, injection text, and weak/no precedent in `strata` when encountered.

## Completed evidence

All 200 candidates were manually reviewed through the resume-safe terminal protocol. The evaluator subsequently reused the prediction files frozen before labels were read. The same rater independently scored 32 selected replies without seeing the LLM judge scores; the paired agreement file records all six dimensions.

- Annotator: applicant (blind-rating identifier `r-1`)
- Labelling date: 2026-09-11
- Elapsed time: not captured by the CLI across resumed sessions
- Disagreements/second rater: no second rater; no adjudication performed
- Known ambiguity notes: recurring boundaries included plan versus account access, billing versus account access, playback versus app/device, and whether persistent low-risk issues warranted escalation

The judge was refreshed after labeling and all 200 scores now use `human_reference`. `scripts.rate_judge` selected four cases per machine-suggested intent (32 total), prioritized edge-case strata, and never displayed the LLM score. Agreement is reported in `eval/results/judge_human_agreement.json`; safety Pearson correlation is `null` because all 32 human safety scores were 5, producing zero variance.

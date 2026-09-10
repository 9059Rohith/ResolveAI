# SpotifyCares AI support agent - report

## 1. Problem framing

For SpotifyCares, a good result has three parts: the issue is categorized correctly, the draft's next step is supported by a relevant historical Spotify exchange, and risky or uncertain cases reach a human. A missed escalation can mishandle billing, account access, or a security incident, so routing prioritizes escalation recall ahead of automation coverage. A useful draft must also be concise, acknowledge the specific problem, and expose the precedent IDs it used.

The system covers English first-contact messages for one historical brand. It does not authenticate customers, inspect live account or payment state, execute refunds, support multiple brands, claim multilingual quality, perform compliance-grade PII detection, or provide a staffed handoff queue. The browser workbench demonstrates decisions; it is not a customer-facing Twitter integration.

The pipeline has four separable stages. A structured classifier returns one of eight intents with confidence and rationale. Hybrid word and character vectors retrieve up to three same-intent conversations whose final linked turn is a brand response. A drafter follows those response patterns and returns citation IDs. A deterministic router independently checks risk tier, confidence, retrieval strength, grounding, prompt injection, and sensitive-data requests. Pydantic validates every boundary, customer text is fenced as untrusted data, and the audit log stores decision metadata without message or reply text.

## 2. Data, split, and taxonomy

`scripts/build_threads.py` streams the 2,811,774-row source CSV into SQLite, starts from every SpotifyCares tweet, expands the full graph neighborhood, and reconstructs components from both response fields. SpotifyCares supplied 43,265 outbound tweets. Components with cycles, no customer, or another support brand are counted and excluded, and text is redacted before persistence. The result is 28,221 clean Spotify threads, including 25,599 resolved-proxy threads and 8,231 multi-reply threads.

The taxonomy contains playback/audio, account access, billing/subscription, app/device issue, content availability, plan/feature question, security/privacy, and other. Reproducible TF-IDF/K-means clusters with top terms and real examples informed open coding; cluster IDs were not used as truth labels.

The evaluation set contains 199 sampled conversations plus one disclosed synthetic injection case. Sampling began with 25 machine-suggested cases per intent and favored multi-turn, short, declarative, and ambiguous examples. One human then adjudicated all 200 intents, ideal reply directions, escalation decisions, and reasons. Final labels are naturally imbalanced. All evaluation components were excluded before building the 5,000-thread retrieval corpus, and prediction files were frozen before human labels were read.

The resolved proxy means only that a public thread became silent after a brand reply. It can mistake abandonment or a private-channel switch for resolution. Retrieved replies therefore demonstrate historical response patterns, not proven outcomes.

## 3. Results versus baselines

All systems use the same 200 human-labelled examples. The trivial system predicts `other`, returns a generic handoff, and always escalates. The simple system uses keyword classification, local retrieval, templated drafting, and threshold routing. The primary system uses `gpt-4.1-mini` for structured classification and grounded drafting while retaining the independent deterministic safety gate.

| System | Intent accuracy (95% CI) | Macro-F1 | Escalation precision | Escalation recall (95% CI) | Unsafe auto-handle | Auto-handle coverage | p50 / p95 | Mean cost/request |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Trivial | 7.5% (4.0-11.5) | 1.7% | 52.5% | 100% (100-100) | 0% | 0% | <1 / <1 ms | $0 |
| Simple local | **67.0%** (60.5-73.0) | **67.5%** | **71.1%** | 65.7% (56.2-74.3) | 35.0% | **51.5%** | 45 / 272 ms | $0 |
| Primary LLM | 64.5% (57.5-71.0) | 61.6% | 67.9% | **90.5%** (84.8-95.2) | **16.7%** | 30.0% | 4,639 / 6,780 ms | $0.000447 |

The simple baseline is the best intent classifier on this set; the primary model does not beat it, and their accuracy intervals overlap substantially. The primary model's useful gain is routing: it reduces missed escalations from 36 to 10 and improves escalation F1 from 68.3% to 77.6%. That safety gain costs coverage and latency. It auto-handles 60 of 200 cases, and 10 of those disagree with the human escalation label. Retrieval clears the 0.24 similarity threshold on 96% of primary cases. Primary confidence is poorly calibrated (Brier 0.286, ECE 0.272), so model confidence alone is not a safe automation rule.

The frozen primary run used 129,117 input and 23,640 output tokens for $0.089465 total estimated generation cost. Judge cost is reported separately in `eval/results/judge_usage.json`; prices are documented in `CITATIONS.md`.

An independently prompted `gpt-4.1` judge scored all 200 drafts against the human reply directions. A human then blindly scored 32 intent-balanced replies without seeing judge scores. Quadratic weighted kappa and Pearson correlation show where the judge is useful and where it is not.

| Reply dimension | Judge mean (200) | Human mean (32) | Judge mean on pairs | Weighted kappa | Pearson r |
|---|---:|---:|---:|---:|---:|
| Groundedness | 3.61 | 4.53 | 3.81 | 0.382 | 0.570 |
| Tone | 3.63 | 4.97 | 3.84 | -0.006 | -0.042 |
| Safety | 4.39 | 5.00 | 4.47 | 0.000 | undefined |
| Actionability | 3.43 | 3.97 | 3.47 | 0.568 | 0.679 |
| Conciseness | 4.56 | 4.91 | 4.59 | 0.115 | 0.171 |
| Evidence relevance | 3.53 | 4.16 | 3.69 | **0.598** | **0.667** |

Agreement is strongest for evidence relevance and actionability, moderate for groundedness, and weak for tone and conciseness. Safety correlation is undefined because the human assigned 5 to all 32 safety cases, leaving zero variance. The judge is therefore diagnostic evidence, not a substitute for human review. The separate deterministic safety suite passes 16/16 versioned injection, high-risk, ambiguity, and negative-control cases.

## 4. Failure analysis

The following are measured primary-system errors from the human-labelled set.

1. **Plan and feature questions collapse into account access.** Thirteen of 36 human `plan_or_feature_question` cases were predicted as `account_access`. In `spotify-007`, a request for artist verification was treated as account access. Words such as "account", "verify", "family", and "country" dominate the operational distinction. A supervised classifier needs examples that separate general process questions from private account intervention.
2. **Billing problems collapse into account access.** Six of 31 billing cases were predicted as account access. `spotify-037` reports lost Premium status through Vodafone after reinstalling; the model chose account access. Routing remained safe because both intents escalate, but the wrong queue would slow resolution. Billing and partner-entitlement signals should take priority in the classifier and handoff target.
3. **Login language causes unnecessary escalation.** `spotify-025` describes a Facebook-login black screen on mobile data. The human labelled it a low-risk app/device issue, while the model chose account access and escalated. Five app/device cases moved to account access. The classifier needs to distinguish credential recovery from a technical login-flow failure; the router should use the requested resolution rather than the word "login" alone.
4. **Content cases hide account-specific escalation needs.** `spotify-011` correctly received `content_availability`, but the system auto-handled it while the human requested regional/account investigation. The router treats content as low risk when confidence and similarity are high. It needs features for user-specific availability, regional uncertainty, artist metadata, and evidence that historical support moved the case to a specialist.
5. **Persistence and exhausted troubleshooting are underweighted.** `spotify-041` says an update bricked the Samsung app after cache clearing and reinstalling. The intent was correct, but the system auto-handled it despite the human escalation label. Repeated failure, multi-day impact, cancellation language, and already-attempted steps should increase route risk independently of intent.

These patterns explain why a fluent grounded draft is insufficient for automatic handling. The primary system is suitable for supervised drafting; its 10 missed escalations and weak confidence calibration do not support unsupervised sending.

## 5. What is misleading about my headline number?

The 64.5% primary intent accuracy is not a general support-agent score. The 200 cases come from one historical public channel and an edge-heavy sample rather than Spotify's current queue. The final class distribution differs from the machine-balanced sampling frame, and one annotator defined the truth; there is no inter-annotator agreement for intent or routing. The simple baseline is 2.5 points better, while the overlapping confidence intervals make small rank differences unstable.

The 90.5% escalation recall also hides cost and severity. Always escalating achieves 100%, so recall must be read beside 67.9% precision and 30% automation coverage. The 16.7% unsafe-auto-handle rate is 10 disagreements among only 60 automated cases; these errors are not equally harmful. Historical silence is a noisy resolution proxy, and citation correctness does not prove outcome correctness.

Judge means can look strong while agreement is weak. The human rater used a narrow, high scoring range, making safety correlation unidentifiable and limiting tone and conciseness agreement. Finally, offline accuracy excludes API outages, policy drift, current account state, reviewer acceptance, and production edits. The evidence supports a conservative human-in-the-loop pilot, not autonomous customer communication.

## 6. What I would do with one more week

First, obtain an independent second label for all 200 cases, adjudicate disagreements, and report intent/routing inter-annotator agreement. Second, add persistence, prior-troubleshooting, region, artist-support, and partner-billing features to the risk policy, then tune thresholds against missed escalations. Third, train a compact supervised classifier on adjudicated examples and compare it with the keyword and LLM systems on the same frozen split. Fourth, manually verify outcomes for the most-retrieved historical threads and remove channel-switch-only responses, then evaluate a cross-encoder reranker with blinded relevance judgments. Fifth, run a shadow queue with support reviewers and measure acceptance, edit distance, escalation overrides, latency, failures, and policy violations before enabling any automatic send.

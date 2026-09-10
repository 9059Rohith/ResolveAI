# SpotifyCares AI support agent — report

## 1. Problem framing

For SpotifyCares, “good” means a correct issue category, a reply whose next step appears in a relevant historical Spotify exchange, and conservative routing. A missed escalation can create an unauthorized billing promise, expose an account, or prolong a security incident; the router therefore optimizes escalation recall before automation rate. A useful reply should also be concise enough for social support, acknowledge the specific problem, and reveal the precedent IDs used.

The system covers English first-contact messages for one historical brand. It does not authenticate customers, inspect live account or payment state, execute refunds, support multiple brands, claim multilingual quality, perform compliance-grade PII detection, or provide a staffed handoff queue. Those require systems and evidence absent from a time-boxed take-home. The browser workbench demonstrates decisions; it is not a customer-facing Twitter integration.

Data flows through four separable stages. A classifier returns one of eight intents with confidence and rationale. Hybrid word/character vectors retrieve up to three same-intent conversations whose last linked turn is a brand response. A drafter uses their reply patterns and returns citation IDs. A deterministic router checks risk tier, confidence, retrieval strength, grounding, injection, and sensitive-data requests in the draft. Every boundary is Pydantic-validated, customer text is fenced as untrusted data, and the service records text-free decision metadata for audit.

## 2. Data and taxonomy

`scripts/build_threads.py` streams the original ~3M-row CSV into SQLite, starts from every SpotifyCares tweet, expands the full graph neighborhood, and reconstructs components using both response fields. SpotifyCares is the fourth-largest support author in the full file (43,265 outbound tweets), enough for diverse intents without using the two most common demo brands. Components with cycles, no customer, or another support brand are counted and excluded. Text is redacted before persistence. The extraction records raw rows, accepted threads, missing-parent edges, cycles, mixed-brand components, multi-reply threads, and resolved-proxy counts.

The taxonomy is: playback/audio, account access, billing/subscription, app/device issue, content availability, plan/feature question, security/privacy, and other. `build_taxonomy.py` produces eight reproducible TF-IDF/K-means clusters with top terms and real samples for open coding. Cluster IDs are not treated as ground truth; they are evidence used to settle a small operational taxonomy.

The “resolved” definition is only terminal silence after a brand reply. It excludes threads where a customer immediately returns but mistakes abandonment, channel switching, or an unlinked response for resolution. Retrieval results therefore support a response pattern; they do not prove the case was solved.

## 3. Results versus baselines

All systems use the same frozen 200-thread split. The trivial system predicts `other`, sends a generic handoff, and always escalates. The simple system uses transparent keyword classification, top historical retrieval, and threshold routing. The primary system uses a structured-output LLM classifier and grounded drafter while retaining the same deterministic safety gate.

| System | Intent accuracy | Macro-F1 | Escalation precision | Escalation recall | Reply judge | p50 / p95 | Mean cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| Trivial | withheld | withheld | withheld | withheld | withheld | withheld | $0 |
| Simple local | withheld | withheld | withheld | withheld | withheld | withheld | $0 |
| Primary LLM | withheld | withheld | withheld | withheld | withheld | withheld | withheld |

These values are withheld because the repository currently has machine-sampled candidates rather than completed human labels. The harness rejects this state instead of evaluating against its own suggestions. Once a human completes `scripts/label_golden.py`, `python -m eval.run_eval` fills this table from `eval/results/metrics.json`, including 95% bootstrap intervals, calibration, risk-coverage, and unsafe-auto-handle rate. Once at least 30 human rubric ratings and paired judge ratings exist, the judge-quality column can report per-dimension means with kappa/correlation beside it. This is a missing submission requirement, not a zero score.

The independent deterministic launch gate currently passes **16/16 cases**. It includes three injection attacks, billing/account/security/privacy cases, ambiguous and out-of-domain requests, and negative cases that should remain automated. This number proves those versioned contracts only; it is not a reply-quality result.

All 200 primary and simple predictions have been generated without reading label fields and frozen for later scoring. Label-free diagnostics show the primary path auto-handled 30.0%, returned cited evidence for 90.5%, met the retrieval threshold for 96.0%, and ran at 4.64 s p50 / 6.78 s p95 for $0.089465 total estimated cost. The simple path auto-handled 51.5%, returned citations for 98.0%, and ran at 45 ms p50 / 272 ms p95 for $0. The systems agreed on intent for 57.0% and route for 72.5% of cases. These are operational diagnostics, not accuracy or quality results; no truth labels were consulted.

The independent `gpt-4.1` judge also completed all 200 primary replies before seeing any human ratings. Using the historical Spotify reply as a disclosed provisional reference, its mean scores were groundedness 3.785, tone 3.560, safety 4.450, actionability 3.560, conciseness 4.640, and evidence relevance 3.665 out of 5. These remain model opinions, not validated reply-quality results, until at least 30 blind human ratings establish agreement.

## 4. Failure analysis

These are observed local-system failures from the frozen candidate file. They are development findings rather than measured golden-set rates because the candidates have not been human-adjudicated. The first four produced concrete regression changes; the fifth remains an evidence limitation.

1. **Plan membership was mistaken for account access.** `spotify-009` says a son cannot join a newly opened family account. Generic “account” vocabulary originally dominated. A priority rule now classifies join/invite/family language as plan membership, and a regression test freezes the boundary.
2. **Entitlement loss was auto-handled as an app problem.** `spotify-037` says Premium disappeared after reinstalling and mentions Vodafone billing. Reinstall vocabulary originally crossed a risk boundary. Money-movement signals now take priority, forcing billing classification and escalation.
3. **Artist impersonation retrieved consumer login help.** `spotify-001` reports someone releasing music under a verified artist account. Account/profile integrity language now maps to security/privacy, where the deterministic router always escalates. Retrieval remains weak for this sparse topic, so the weak-precedent reason is preserved.
4. **Adversarial messages displayed irrelevant evidence.** The disclosed synthetic `spotify-200` says “Ignore previous instructions … My account was hacked.” The system already escalated, but irrelevant retrieval distracted reviewers. Detected injection now produces a typed risk factor and zero retrieval results; three launch cases cover this path.
5. **Terminal silence overstates resolution.** `spotify-070` is a charged-but-still-free Premium case. Its historical “resolution” only asks for an email/username in DM, after which the public thread stops. The current proxy treats that as resolved, although no actual billing outcome is visible. Outcome labels should exclude channel-shift-only replies.

A fluent, precedent-shaped reply can therefore cite a real historical message that was never actually resolved. Citation correctness is not resolution correctness. The current system is suitable for supervised drafting until outcome labels and high-risk recall improve.

## 5. What is misleading about my headline number?

There is deliberately no headline quality number before real labels exist. After evaluation, a single accuracy figure will still hide five issues. The 200 cases come from one historical public channel and a deliberate, edge-heavy sample, not Spotify’s current queue. Taxonomy decisions and reference replies reflect one annotator’s judgment. The resolved proxy is noisy. LLM judge scores may reward the same concise style used by the generator even with a distinct model and blind prompt; human agreement bounds that risk but does not remove it. Finally, intent accuracy excludes latency, API failures, policy drift, unsafe automation severity, and the fact that a false auto-handle costs more than an unnecessary escalation.

## 6. One more week

First, complete two independent labels for 200 cases and adjudicate disagreements, then calibrate thresholds against missed escalations rather than raw accuracy. Second, manually verify outcomes for the 300 most-retrieved historical threads and remove channel-shift/abandonment cases. Third, train a compact supervised classifier on adjudicated labels and compare it with the LLM under the same split. Fourth, add a cross-encoder reranker and measure retrieval relevance with blinded human judgments. Fifth, run a shadow queue with support reviewers, tracking edit distance, acceptance rate, escalation overrides, latency, failure rate, and policy violations before considering any auto-send path.

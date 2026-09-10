# Decision log

- **SpotifyCares is the only brand.** It has recurring playback, device, account, plan, content, and billing issues, which supports a compact but meaningful taxonomy.
- **Conversation components are the split unit.** Every linked tweet stays in one component so a later reply cannot leak into retrieval for its own evaluation case.
- **Both relationship columns create graph edges.** `in_response_to_tweet_id` and `response_tweet_id` are sometimes incomplete independently; using both reduces orphaning.
- **Mixed-brand components are excluded.** A Spotify agent should not learn another company's tone or resolution policy.
- **A terminal brand reply is only a resolved proxy.** No later customer reply suggests acceptance, but silence can also mean abandonment; reports call this proxy out.
- **The taxonomy has eight labels plus an escape valve inside `other`.** It is small enough to explain live and covers clusters seen in Spotify samples.
- **Cluster output is evidence, not automatic truth.** TF-IDF/K-means surfaces vocabulary groups; a human interpretation produces operational labels.
- **Hashing vectors power reproducible retrieval.** They require no model download or API bill and make the checkout runnable offline. The quick path uses an in-memory sparse matrix; the same vectors can be persisted in optional Chroma because its large dependency tree consumed most of the 15-minute reproduction budget.
- **Retrieval is filtered by predicted intent.** This lowers the chance that lexical overlap brings an unrelated resolution, with an all-intent fallback only when a class has no corpus rows.
- **The LLM adapter is thin.** Plain functions and Pydantic schemas make provider behavior inspectable without a large orchestration framework.
- **Routing is deterministic and fail-closed.** Billing, account, security, unknown intent, low classifier confidence, or weak precedent overrides any generative preference.
- **Customer text is enclosed and explicitly untrusted.** Injection-like text cannot directly choose an action; a regression test covers the direct attack.
- **PII redaction is deliberately narrow.** Regex covers emails, URLs, phone-like strings, and labelled account/order IDs, but is not claimed as compliance-grade entity detection.
- **Evaluation labels never have machine defaults.** Suggestions live in separate fields; the harness accepts only explicit `human_verified` rows.
- **The judge differs from the generator.** GPT-4.1 judges GPT-4.1-mini outputs with a blind rubric, while agreement with at least 30 human scores is mandatory before reporting reply quality.

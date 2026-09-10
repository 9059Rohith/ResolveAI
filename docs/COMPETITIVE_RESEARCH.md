# Competitive research and quality bar

Research date: 2026-09-10. This review searched public GitHub implementations, the primary dataset page, peer-reviewed evaluation work, Microsoft’s agent-evaluation scenario library, production customer-support documentation, OWASP, and NIST. The comparison is based on publicly visible evidence; it does not claim exhaustive coverage of private take-home submissions or proprietary systems.

## Executive finding

The strongest differentiator for this assignment is evidence quality. Many public projects have a polished RAG demo, citations, Docker, and an escalation rule. Far fewer combine a leakage-safe reconstruction of the actual 3M-tweet source, a 200-case human-label protocol, two baselines, cost-sensitive routing metrics, human validation of an LLM judge, adversarial launch gates, privacy-minimizing audit logs, and explicit refusal to publish scores before the required human work exists.

Resolve now implements that full measurement surface. Its main unresolved dependency is also explicit: the assignment requires a human-built golden set and measured judge-human agreement. The repository supplies 200 candidates and the complete workflow but will not misrepresent machine suggestions as human work.

## What comparable projects do well

| Public system | Strong evidence | Limit visible in the public artifact | What Resolve adopted or already exceeds |
|---|---|---|---|
| [support-agent-stack](https://github.com/AleBrito124356/support-agent-stack) | Deployable FastAPI service, grounded answers, tickets, input/output guardrails, and a 20-case evaluation suite | Fictional product/knowledge base; its published suite is 20 cases and does not demonstrate a 150–250 human golden set or judge-human agreement | Resolve uses real SpotifyCares threads, 200 component-disjoint candidates, deterministic routing, prohibited-action checks, and a 16-case launch gate in addition to the assignment evaluation |
| [rag-support-agent](https://github.com/RaphaelBudin/rag-support-agent) | Hybrid dense/BM25 retrieval, Recall@5, confidence abstention, cost/latency logging, source freshness, and blind-spot reporting | Published labeled set is 23 cases; support content is curated documentation rather than reconstructed noisy conversations | Resolve added word/character hybrid retrieval, confidence calibration, risk-coverage output, per-request cost/latency, and a redacted append-only decision log |
| [local-first-customer-support-agent](https://github.com/hofri/local-first-customer-support-agent) | Selective escalation, PII handling, JSONL audit trail, and careful discussion of judge agreement and sampled audits | Its own README says the live frontier escalation path has not been run and that deterministic stubs prove wiring rather than answer quality | Resolve makes the same evidence boundary explicit, records both paths, and requires paired human ratings before judge quality is reportable |
| [Support-Ticket-Resolution-Agent](https://github.com/chaitanyakelkar27/Support-Ticket-Resolution-Agent) | Deterministic pre-LLM safety gate, TF-IDF retrieval, structured output, safe exception behavior | Reported headline is based on 29 tickets and no published human-agreement study | Resolve keeps deterministic high-risk routing but evaluates at a larger planned scale, separates classifier/retriever/reply/router evidence, and reports uncertainty |
| [Microsoft agent evaluation scenarios](https://github.com/microsoft/ai-agent-eval-scenario-library) | Concrete tests for missing, ambiguous, and contradictory evidence plus negative tests where an agent should handle instead of escalate | A scenario library, not an end-to-end submission | Resolve’s versioned safety suite covers injection, billing, account access, privacy, ambiguity, out-of-domain input, and safe no-escalation cases |

This is a feature comparison, not a leaderboard. Repository age, stars, self-reported metrics, and different datasets do not support a statistically valid rank.

## Production support-agent benchmark

Intercom’s public Fin documentation is useful because it reveals the operating loop expected after a demo. Its reporting includes resolution, escalation, deflection, customer experience, and content performance. Its batch testing uses real historical questions, retains source visibility, supports repeatable groups, and asks humans to mark answers acceptable or poor with a reason. That supports four requirements for this project:

1. Test on representative historical traffic before deployment.
2. Keep the evidence used for each answer visible.
3. Separate useful automation from unnecessary escalation.
4. Turn failures into a content or policy backlog rather than a single aggregate score.

Resolve maps those ideas to an assignment-sized implementation: component-disjoint historical sampling, cited thread IDs, explicit escalation reasons, saved predictions, failure strata, and a privacy-minimizing event log. The log records request ID, model path, confidence, route, risk factors, grounding, precedent IDs, top similarity, latency, tokens, and estimated cost. It excludes message and reply text.

## Evaluation standard

### Retrieval and reply quality are separate

The Ragas paper argues that RAG evaluation has distinct retrieval relevance/focus, answer faithfulness, and answer-quality dimensions. Resolve therefore exposes retrieved examples and similarity independently from the drafted reply. Its judge rubric scores groundedness and evidence relevance separately. Historical reply overlap is not treated as proof of correctness because two valid support replies can use different wording.

### Automation must be evaluated as selective prediction

Overall intent accuracy does not answer the operational question: “When the system chooses to auto-handle, how often is it wrong?” The evaluator now reports:

- intent accuracy and macro-F1;
- confusion matrix;
- escalation precision, recall, F1, and missed escalations;
- auto-handle coverage and unsafe auto-handle rate;
- top-label Brier score and expected calibration error;
- an intent risk-coverage curve;
- seeded bootstrap 95% intervals for intent accuracy and escalation recall;
- retrieval coverage/similarity, latency, and measured cost.

This prevents a system that escalates everything from appearing safe and prevents a high-coverage system from hiding unsafe misses inside overall accuracy.

### LLM judges require human validation

MT-Bench found that strong LLM judges can agree well with human preferences but documented position, verbosity, and self-enhancement bias. EMNLP 2024 also found both human and LLM judges vulnerable to multiple perturbations. Resolve uses a blinded, dimension-specific rubric, a judge model distinct from the generator, and at least 30 paired human ratings. It reports quadratic weighted kappa, Pearson correlation, and mean-score differences. The harness rejects incomplete agreement evidence.

### A resolved proxy is not a resolved case

The Kaggle source contains linked tweets and already masks some sensitive fields, but it provides no true outcome label. TWEETSUMM reconstructed 49,155 conversations from the same source before selecting a human-annotated subset, which supports treating conversation reconstruction as substantive data work. Resolve’s “terminal brand reply” is an auditable proxy only. Public silence may represent success, abandonment, or a move to direct messages, so the report does not call it ground-truth resolution.

## Security and deployment standard

OWASP’s LLM risk guidance identifies prompt injection, sensitive-information disclosure, and excessive agency as core risks. Resolve handles customer text as untrusted data, validates structured outputs, suppresses retrieval for detected injection attempts, gives generated text no authority over routing, and never performs account actions. Billing, access, security/privacy, unknown intent, weak precedent, low confidence, and sensitive-data requests fail closed to human review.

NIST’s Generative AI Profile emphasizes documented pre-deployment testing, human oversight roles, data provenance, red-teaming, monitoring, and go/no-go decisions grounded in test evidence. Resolve implements an offline safety gate, source hashes and sampling statistics, append-only decision metadata, reproducible configuration, and an honest deployment gate. The API and container are deployable; autonomous customer sending remains out of scope until human evidence clears the thresholds.

## Improvements implemented from the benchmark

| Gap found in comparison | Repository change | Verification |
|---|---|---|
| Misspelled social text weakens word-only retrieval | Combined word 1–2 grams with character 3–5 grams in one normalized 4,096-dimensional local vector | Regression test retrieves the intended precedent from a deliberately misspelled query |
| Generic keywords can cross a risk boundary | Added priority rules for money movement, family-plan membership, artist/account integrity, and personal-data requests | Regression cases cover Premium entitlement loss, family joining, artist impersonation, and privacy export |
| Injection cases still displayed irrelevant precedent | Injection detection now adds a typed risk factor and bypasses retrieval | Three launch-gate injection cases return zero retrieved items and escalate |
| No operational audit artifact | Added append-only JSONL decision events with UUID and SHA-256 message fingerprint, omitting raw customer/reply text | Test confirms the email in a request never appears in the log |
| Aggregate metrics hide the automation tradeoff | Added unsafe auto-handle rate, coverage, calibration, risk-coverage, and bootstrap intervals | Unit tests cover exact metric behavior and reproducibility |
| No explicit pre-deployment edge-case gate | Added 16 versioned cases and a command that exits non-zero on any failure | Current local result: 16/16; artifact saved under `eval/results/` |

## Remaining gaps and priority

| Priority | Gap | Why it matters | Required closure |
|---:|---|---|---|
| P0 | Human labels are pending | The assignment explicitly requires a hand-labelled 150–250 example golden set | Applicant reviews all 200 candidates and records metadata |
| P0 | Judge-human agreement is pending | An automated judge cannot validate itself | Human scores at least 30 frozen replies, then runs the paired agreement command |
| P0 | Primary-model results need credentials | Local wiring and tests do not prove live LLM answer quality | Run the frozen evaluation with an API key and save outputs |
| P1 | Resolution labels are proxies | Public silence is confounded by abandonment and DM transfer | Manually outcome-audit heavily retrieved threads |
| P1 | No live support shadow data | Historical Twitter language and policies can drift | Run reviewer-only shadow traffic and measure edits/overrides |
| P2 | No cross-encoder reranker | Hybrid lexical similarity still confuses nearby topics | Label relevant precedents and compare reranked Recall@k/nDCG |

The correct launch position is reviewer-assist mode. The implementation is deployment-ready as a service, and the evidence gates intentionally prevent the repository from claiming that it is ready to auto-send replies.

## Sources

- [Customer Support on Twitter dataset card](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)
- [TWEETSUMM, Findings of EMNLP 2021](https://aclanthology.org/2021.findings-emnlp.24/)
- [Ragas: Automated Evaluation of Retrieval Augmented Generation](https://arxiv.org/abs/2309.15217)
- [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685)
- [Humans or LLMs as the Judge? A Study on Judgement Bias, EMNLP 2024](https://aclanthology.org/2024.emnlp-main.474/)
- [Microsoft: Graceful Failure and Escalation scenarios](https://github.com/microsoft/ai-agent-eval-scenario-library/blob/main/capability-scenarios/graceful-failure-and-escalation.md)
- [Microsoft: Triage and Routing scenarios](https://github.com/microsoft/ai-agent-eval-scenario-library/blob/main/business-problem-scenarios/triage-and-routing.md)
- [Intercom Fin AI Agent reporting](https://www.intercom.com/help/en/articles/7837533-fin-ai-agent-reporting)
- [Intercom Fin batch testing](https://www.intercom.com/help/en/articles/10521711-batch-test-fin-ai-agent)
- [OWASP Top 10 for LLM and GenAI applications](https://genai.owasp.org/llm-top-10/)
- [NIST AI 600-1: Generative AI Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)
- [support-agent-stack](https://github.com/AleBrito124356/support-agent-stack)
- [rag-support-agent](https://github.com/RaphaelBudin/rag-support-agent)
- [local-first-customer-support-agent](https://github.com/hofri/local-first-customer-support-agent)
- [Support-Ticket-Resolution-Agent](https://github.com/chaitanyakelkar27/Support-Ticket-Resolution-Agent)

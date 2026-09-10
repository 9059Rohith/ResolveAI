# Assignment completion audit

Audited against `Hiver SDE Intern Assignment.docx` and the detailed project brief on 2026-09-10.

| Requirement | Evidence | Status |
|---|---|---|
| One-brand agent | SpotifyCares; `data/processed/brand_selection.json` | Complete |
| Intent classification | Eight-intent Pydantic output; local and LLM classifiers | Complete |
| Historically grounded draft | Intent-filtered retrieval, cited thread IDs, validated drafter | Complete |
| Auto-handle/escalate with reason | Separate deterministic router with explicit risk factors | Complete |
| Raw dataset download | Public Kaggle API, ZIP validation, recorded SHA-256 | Complete |
| Conversation reconstruction | Both edge fields, connected components, mixed-brand/cycle exclusions | Complete |
| Cleaning and PII reduction | Routing-handle, URL, email, phone and labelled-ID redaction | Complete with documented limitation |
| Deliberate subsampling | Seeded, balanced, edge-prioritised, component-disjoint | Complete |
| Data-derived taxonomy evidence | 3,000-message TF-IDF/K-means artifact with top terms and samples | Complete |
| Persistent vector store | Optional Chroma adapter, local stable embeddings, reproducible index command; lean path uses the same matrix in memory | Complete |
| Provider abstraction | Thin structured-output client with schema validation, timeout and retries | Complete |
| Prompt-injection handling | Untrusted-data fencing, deterministic action gate, regression test | Complete |
| 150–250 hand-labelled golden examples | 200 candidates exist; no human has completed the labels | **Pending human work** |
| Automated evaluation metrics | Accuracy, macro-F1, confusion matrix, routing metrics, calibration, risk-coverage, bootstrap intervals, retrieval coverage, latency and cost | Complete; execution gated by labels |
| LLM judge rubric | Six explicit 1–5 dimensions and independent judge command | Complete; live run needs API key and labels |
| Judge–human agreement | Kappa, Pearson correlation, means and ≥30-pair guard | Complete harness; **pending human scores and judge run** |
| Trivial baseline | Majority/`other`, canned response, always escalate | Complete |
| Simple baseline | Transparent keyword classification, local retrieval/drafting, threshold router | Complete |
| Primary system | Structured LLM classifier/drafter plus same deterministic safety gate | Complete; live evidence needs API key |
| Results comparison | One-set evaluator and report table | **Pending human labels/API evaluation** |
| Five failure modes | Report includes concrete risk examples and causal hypotheses | Complete as development audit; measured golden failures pending |
| “Misleading headline number” | Dedicated report section, including why none is claimed yet | Complete |
| One-more-week plan | Five prioritized actions tied to failures | Complete |
| Decision log | 15 decisions with reasons | Complete |
| README under-15-minute path | Exact cached commands, timings, corpus size, models and pricing | Complete; timings should be reconfirmed on reviewer network |
| API and workbench | FastAPI/OpenAPI, same-origin UI, health/readiness, auth option and limits | Complete |
| Deployment package | Pinned `uv.lock`, non-root Dockerfile, Compose health check, CI | Complete |
| Tests/security checks | Unit/integration/API tests plus a 16/16 adversarial and negative-escalation launch gate, lint, compile, browser workflow | Complete |
| Operational audit trail | Text-free JSONL events with request ID, fingerprint, decision evidence, latency, tokens and cost | Complete |
| Web comparison | Source-backed comparison against public projects, production patterns, research, NIST and OWASP | Complete |
| Public repository | [github.com/9059Rohith/ResolveAI](https://github.com/9059Rohith/ResolveAI), public `main` with deployment operations documented | Complete |
| Production deployment | [resolve-ai-wheat.vercel.app](https://resolve-ai-wheat.vercel.app), FastAPI function in Mumbai | Complete and live-tested |
| Hosted CI | Workflow is committed; GitHub did not start its runner because the repository owner's account is locked for a billing issue | External account action required; local and production verification passed |
| Submission form | Requires the applicant's final human evaluation evidence and form submission | **Not submitted** |

## Honest completion verdict

The software implementation is end-to-end and deployment-packaged. The take-home submission is **not 100% complete** until the applicant personally labels the 200 candidates, personally scores at least 30 replies, runs the live LLM evaluations with an API key, updates the report with measured results and real golden-set failures, publishes the repository, and submits the form. Those are evidence-producing human/external actions; generating or claiming them automatically would violate the assignment.

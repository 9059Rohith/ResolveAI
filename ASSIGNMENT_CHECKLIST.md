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
| 150-250 hand-labelled golden examples | 200/200 manually adjudicated across intent, reply direction, escalation, and reason | Complete |
| Automated evaluation metrics | Accuracy, macro-F1, confusion matrix, routing metrics, calibration, risk-coverage, bootstrap intervals, retrieval coverage, latency and cost | Complete; measured on 200 human labels |
| LLM judge rubric | Six explicit 1-5 dimensions and independent judge command | Complete; 200/200 `gpt-4.1` scores use human references |
| Judge-human agreement | Kappa, Pearson correlation, means and >=30-pair guard | Complete; 32/32 blind human pairs measured |
| Trivial baseline | Majority/`other`, canned response, always escalate | Complete |
| Simple baseline | Transparent keyword classification, local retrieval/drafting, threshold router | Complete |
| Primary system | Structured LLM classifier/drafter plus same deterministic safety gate | Complete; measured against both baselines |
| Results comparison | One-set evaluator and report table | Complete with two baselines, confidence intervals, routing safety, latency, and cost |
| Five failure modes | Report includes five measured golden-set errors and causal hypotheses | Complete |
| "Misleading headline number" | Dedicated report section covering sampling, annotator, proxy, agreement, and operational limits | Complete |
| One-more-week plan | Five prioritized actions tied to failures | Complete |
| Decision log | 15 decisions with reasons | Complete |
| README under-15-minute path | Exact cached commands, timings, corpus size, models and pricing | Complete; timings should be reconfirmed on reviewer network |
| API and workbench | FastAPI/OpenAPI, same-origin UI, health/readiness, auth option and limits | Complete |
| Public evidence dashboard | Versioned dataset, leakage, safety and label-status evidence at `/evidence` and `/v1/evidence` | Complete |
| Automated submission audit | 19 artifact, prediction, judge, secret-template, drift and report-contract checks with an explicit human-evidence gate | Complete |
| Deployment package | Pinned `uv.lock`, non-root Dockerfile, Compose health check, CI | Complete |
| Tests/security checks | Unit/integration/API tests plus a 16/16 adversarial and negative-escalation launch gate, lint, compile, browser workflow | Complete |
| Operational audit trail | Text-free JSONL events with request ID, fingerprint, decision evidence, latency, tokens and cost | Complete |
| Web comparison | Source-backed comparison against public projects, production patterns, research, NIST and OWASP | Complete |
| Public repository | [github.com/9059Rohith/ResolveAI](https://github.com/9059Rohith/ResolveAI), public `main` with deployment operations documented | Complete |
| Production deployment | [resolve-ai-wheat.vercel.app](https://resolve-ai-wheat.vercel.app), FastAPI function in Mumbai | Complete and live-tested |
| Hosted CI | Workflow is committed; GitHub did not start its runner because the repository owner's account is locked for a billing issue | External account action required; local and production verification passed |
| Submission form | Requires the applicant's final human evaluation evidence and form submission | **Not submitted** |

## Honest completion verdict

The repository package is complete: 200/200 human labels, frozen baseline and primary predictions, 200 human-reference judge scores, 32 blind human ratings, measured agreement, a final report, passing safety gate, and deployment artifacts are checked in. The only external account actions are restoring the GitHub Actions runner if desired and sending the links through the Hiver form.

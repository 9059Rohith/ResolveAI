# Implementation plan

The user authorizes autonomous implementation and overrides review pauses. This is a new Python application; the assignment document is the acceptance contract.

## Design

Use FastAPI plus a small same-origin HTML/CSS/JavaScript workbench. Keep pipeline modules independent: data reconstruction, cleaning, classification, retrieval, drafting, deterministic routing, evaluation and annotation persistence. Use disk-backed SQLite to reconstruct the raw corpus without loading 3M tweets. Select one brand after inspecting volume and examples. Split by connected conversation component before constructing retrieval or evaluation samples. Ship a compact redacted snapshot with source IDs and hashes.

Primary LLM pipeline uses a provider adapter with validated JSON, bounded retries and a fail-closed router. Local retrieval/template mode is a runnable zero-key comparison, never represented as an LLM. Chroma stores locally computed hashing vectors for reproducible, download-free retrieval; TF-IDF provides the simple baseline. Candidate labels begin as explicit machine suggestions. The checked-in final state contains 200 manually adjudicated labels and 32 blind human judge ratings, while prediction artifacts remain separate from labels.

## Execution and checks

1. Download and hash original data; reconstruct components and test branching, missing parents, cycles, cross-brand contamination and redaction. Persist extraction statistics.
2. Inspect sample and derive 6–12 intents, record source examples; reserve 200 component-disjoint evaluation candidates and a development partition.
3. Implement typed schemas, retriever, local and LLM classifier/drafter, explicit risk routing. Test injected instructions, unavailable providers, malformed JSON, nonexistent citations, confidence bounds, unknown messages and billing risk.
4. Implement all three systems in an evaluation harness: accuracy, macro-F1, confusion matrix, escalation metrics, coverage, latency, token costs, rubric scoring and paired human agreement. Reject incomplete or contaminated golden sets. Export predictions separately from labels.
5. Build support workbench, annotation editor and judge scoring UI backed by SQLite; test API validation, auth, limits, persistence and frontend flows.
6. Package pinned dependencies and lockfile, Docker, health/readiness endpoints and CI. Run unit/integration/browser checks and clean-checkout reproduction. Write report, 15 decisions, citations and an evidence-backed assignment checklist.

## Acceptance truth

Human evidence must remain attributable to the real rater. The final package includes live-provider predictions, complete human annotation, measured judge agreement, deployment evidence, and explicit limitations in the report.

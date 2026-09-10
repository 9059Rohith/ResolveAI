# Production deployment

## Current release

- Production alias: <https://resolve-ai-wheat.vercel.app>
- Platform: Vercel FastAPI/Python function
- Function region: `bom1` (Mumbai)
- Function bundle: approximately 13 MB
- Source repository: <https://github.com/9059Rohith/ResolveAI>
- Application release commit: `09fa8a3f79f0677110f84e37f8217a1a725f1a60`
- Deployment: immutable Vercel production artifact; inspect the stable alias for its current ID

## Deployment layout

`app.py` exports the existing FastAPI ASGI application. `vercel.json` pins a 30-second function duration, includes the checked-in retrieval corpus and workbench assets, excludes evaluation-only material, and places the function in Mumbai. `.vercelignore` prevents raw data, local environments, tests, and build artifacts from being uploaded.

The serving path uses a deterministic standard-library hybrid hasher, so NumPy and scikit-learn remain evaluation-only dependencies. The same word and character features run in memory and in optional Chroma. Vercel's read-only filesystem uses `/tmp/resolve-audit.jsonl`; durable deployments can set `AUDIT_LOG_PATH` or connect a managed log drain.

## Environment

- `OPENAI_API_KEY`: optional; enables LLM mode.
- `APP_API_TOKEN`: recommended for restricted deployments; protects `POST /v1/analyze` with a bearer token.
- `AUDIT_LOG_PATH`: optional durable-container audit path. Vercel defaults to ephemeral `/tmp`.

Local mode is fully operational without secrets. Production currently reports `llm_mode: false`, so the public demonstration cannot incur model charges.

## Verified production checks

The release was tested after alias promotion:

- `GET /healthz`: HTTP 200
- `GET /readyz`: HTTP 200, local mode ready
- `GET /`: HTTP 200 with complete workbench HTML
- `GET /assets/styles.css`: HTTP 200
- `GET /favicon.ico`: HTTP 204
- Playback analysis: `playback_or_audio`, auto-handle, three precedents
- Billing analysis: `billing_or_subscription`, escalate, `high_risk_intent`
- Desktop viewport: no console errors or horizontal overflow
- Mobile viewport: no console errors or horizontal overflow
- Vercel status: READY; no error-level production logs returned

Repository verification for this release: 40 tests passed and one optional-Chroma test skipped in the lean environment; Ruff passed; the 16-case safety gate passed 16/16; the submission artifact audit passed 19/19; the tracked credential scan found no API key.

The optional OpenAI path was also smoke-tested end to end from the browser: `.env` loading, `gpt-4.1-mini` strict classification and drafting, cited retrieval, signature/link cleanup, deterministic routing, FastAPI serialization, and UI rendering all passed. A separate `gpt-4.1` judge smoke test returned all six rubric dimensions in range. These smoke tests establish integration health; they are not substitutes for golden-set quality metrics or judge-human agreement.

The frozen evaluation artifacts now include all 200 simple predictions, all 200 primary `gpt-4.1-mini` predictions, label-free operational diagnostics, and 200 independent `gpt-4.1` judge scores. Generation is parallel, resumable, and independent of label fields. Human labels and paired human ratings remain intentionally absent.

## Deploy and roll back

```powershell
vercel pull --yes --environment=production
vercel deploy --prod --yes
vercel inspect resolve-ai-wheat.vercel.app
vercel logs resolve-ai-wheat.vercel.app --level error --since 1h
```

Vercel retains immutable deployment artifacts. To restore a prior known-good deployment, use `vercel rollback <deployment-url-or-id>` and repeat the health, routing, and browser checks above.

## Current external limitation

The GitHub Actions workflow is committed and equivalent checks pass locally. GitHub did not start the hosted runner because the repository owner's GitHub account is locked due to a billing issue. This is an account-level runner restriction rather than a test failure. Vercel's remote production build completed successfully.

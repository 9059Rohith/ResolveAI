FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv==0.11.28 && uv sync --frozen --no-dev
COPY api api
COPY src src
COPY scripts scripts
COPY web web
COPY config.yaml ./
COPY data/processed data/processed
RUN mkdir -p data/runtime && chown -R 65532:65532 data/runtime
EXPOSE 8000
USER 65532:65532
CMD ["uv", "run", "--no-sync", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

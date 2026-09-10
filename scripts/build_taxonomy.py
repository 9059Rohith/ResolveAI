"""Create auditable unsupervised cluster evidence used when open-coding the taxonomy."""

import json
from pathlib import Path

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from src.data import read_jsonl

if __name__ == "__main__":
    rows = read_jsonl("data/processed/all_threads.jsonl")[:3000]
    texts = [row["message"] for row in rows]
    vectorizer = TfidfVectorizer(
        stop_words="english", max_features=3000, ngram_range=(1, 2), min_df=2
    )
    matrix = vectorizer.fit_transform(texts)
    model = KMeans(n_clusters=8, random_state=20260910, n_init=10).fit(matrix)
    terms = vectorizer.get_feature_names_out()
    evidence = []
    for cluster in range(8):
        top = model.cluster_centers_[cluster].argsort()[-10:][::-1]
        samples = [
            text for text, label in zip(texts, model.labels_, strict=False) if label == cluster
        ][:5]
        evidence.append(
            {
                "cluster": cluster,
                "size": int(sum(model.labels_ == cluster)),
                "top_terms": terms[top].tolist(),
                "sample_messages": samples,
            }
        )
    Path("data/processed/taxonomy_evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(evidence, indent=2, ensure_ascii=True))

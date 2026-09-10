from src.data import read_jsonl
from src.retrieval import ChromaRetriever

if __name__ == "__main__":
    rows = read_jsonl("data/processed/retrieval_corpus.jsonl")
    print(f"Indexed {ChromaRetriever().index(rows)} resolved-proxy threads.")

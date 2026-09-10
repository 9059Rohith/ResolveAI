"""Stream raw CSV into SQLite, then select the full single-brand graph neighborhood."""

import csv
import json
import sqlite3
from pathlib import Path

from src.data import reconstruct, write_jsonl


def main() -> None:
    db = sqlite3.connect("data/raw/tweets.sqlite3")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute(
        "CREATE TABLE IF NOT EXISTS tweets (id TEXT PRIMARY KEY, parent TEXT, author TEXT, payload TEXT)"
    )
    if not db.execute("SELECT count(*) FROM tweets").fetchone()[0]:
        with Path("data/raw/twcs.csv").open(encoding="utf-8", newline="") as f:
            batch = []
            for row in csv.DictReader(f):
                batch.append(
                    (
                        row["tweet_id"],
                        row["in_response_to_tweet_id"],
                        row["author_id"],
                        json.dumps(row),
                    )
                )
                if len(batch) == 10000:
                    db.executemany("INSERT INTO tweets VALUES (?,?,?,?)", batch)
                    batch.clear()
            db.executemany("INSERT INTO tweets VALUES (?,?,?,?)", batch)
        db.execute("CREATE INDEX IF NOT EXISTS parent_index ON tweets(parent)")
        db.execute("CREATE INDEX IF NOT EXISTS author_index ON tweets(author)")
        db.commit()
    rows = {
        r["tweet_id"]: r
        for (payload,) in db.execute("SELECT payload FROM tweets WHERE author='SpotifyCares'")
        for r in [json.loads(payload)]
    }
    frontier = set(rows)
    while frontier:
        found = {}
        ids = set(frontier)
        for id in frontier:
            r = rows[id]
            ids.add(r["in_response_to_tweet_id"])
            ids.update(r["response_tweet_id"].split(","))
        ids.discard("")
        ids = sorted(ids)
        for start in range(0, len(ids), 400):
            chunk = ids[start : start + 400]
            args = ",".join("?" for _ in chunk)
            for (payload,) in db.execute(
                f"SELECT payload FROM tweets WHERE id IN ({args}) OR parent IN ({args})",
                chunk + chunk,
            ):
                r = json.loads(payload)
                if r["tweet_id"] not in rows:
                    found[r["tweet_id"]] = r
        rows.update(found)
        frontier = set(found)
    threads, stats = reconstruct(list(rows.values()), "SpotifyCares")
    stats["raw_tweets"] = db.execute("SELECT count(*) FROM tweets").fetchone()[0]
    top_authors = dict(
        db.execute(
            "SELECT author, count(*) AS n FROM tweets GROUP BY author ORDER BY n DESC LIMIT 10"
        ).fetchall()
    )
    db.close()
    write_jsonl("data/processed/all_threads.jsonl", threads)
    Path("data/processed/thread_stats.json").write_text(json.dumps(stats, indent=2))
    Path("data/processed/brand_selection.json").write_text(
        json.dumps(
            {
                "source": "full SQLite staging table grouped by author_id",
                "top_support_author_counts": top_authors,
                "selected": "SpotifyCares",
                "reason": "High volume and diverse issues without using the two most common demo brands.",
            },
            indent=2,
        )
    )
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()

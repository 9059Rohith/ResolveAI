"""Deterministic graph reconstruction and intentionally limited PII redaction."""

import json
import re
from collections import defaultdict
from pathlib import Path


def clean_text(text: str) -> str:
    """Remove routing handles, URLs, emails and common account/contact identifiers."""
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
    text = re.sub(r"https?://\S+", "[LINK]", text)
    text = re.sub(r"(?<!\w)@\w+", "", text)
    text = re.sub(
        r"\b(?:order|account|reference)\s*(?:number|no\.?|#|id)?\s*[:#]?\s*[A-Z0-9-]{6,}\b",
        "[IDENTIFIER]",
        text,
        flags=re.I,
    )
    text = re.sub(r"(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)", "[NUMBER]", text)
    return " ".join(text.split()).strip()


def inbound(row: dict) -> bool:
    return str(row["inbound"]).lower() == "true"


def reconstruct(rows: list[dict], brand: str) -> tuple[list[dict], dict]:
    """Connect both link fields; reject cycles and conversations involving another brand."""
    by_id = {str(r["tweet_id"]): r for r in rows}
    graph = defaultdict(set)
    directed = defaultdict(set)
    missing = 0
    for id, row in by_id.items():
        parent = str(row.get("in_response_to_tweet_id") or "")
        if parent:
            if parent in by_id:
                graph[id].add(parent)
                graph[parent].add(id)
                directed[parent].add(id)
            else:
                missing += 1
        for child in str(row.get("response_tweet_id") or "").split(","):
            if child in by_id:
                graph[id].add(child)
                graph[child].add(id)
                directed[id].add(child)
    seen, threads = set(), []
    stats = dict(
        missing_parent_edges=missing,
        cyclic_components=0,
        cross_brand_components=0,
        no_customer_components=0,
        multi_reply_threads=0,
        input_tweets=len(rows),
    )
    for id in sorted(by_id):
        if id in seen:
            continue
        stack, component = [id], set()
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            stack.extend(graph[current] - component)
        seen.update(component)
        brands = {by_id[x]["author_id"] for x in component if not inbound(by_id[x])}
        if brand not in brands:
            continue
        if brands != {brand}:
            stats["cross_brand_components"] += 1
            continue
        indegrees = {x: 0 for x in component}
        for x in component:
            for child in directed[x]:
                indegrees[child] += 1
        queue = sorted(x for x, degree in indegrees.items() if degree == 0)
        ordered = []
        while queue:
            x = queue.pop(0)
            ordered.append(x)
            for child in sorted(directed[x]):
                indegrees[child] -= 1
                if indegrees[child] == 0:
                    queue.append(child)
        if len(ordered) != len(component):
            stats["cyclic_components"] += 1
            continue
        customers = [x for x in ordered if inbound(by_id[x])]
        if not customers:
            stats["no_customer_components"] += 1
            continue
        tweets = [
            dict(id=x, inbound=inbound(by_id[x]), text=clean_text(by_id[x]["text"]))
            for x in ordered
        ]
        leaves = [x for x in component if not directed[x]]
        terminal_brand = all(not inbound(by_id[x]) for x in leaves)
        replies = [x for x in ordered if not inbound(by_id[x])]
        stats["multi_reply_threads"] += int(len(replies) > 1)
        threads.append(
            dict(
                thread_id=min(component, key=lambda s: (len(s), s)),
                brand=brand,
                message=clean_text(by_id[customers[0]]["text"]),
                reply=clean_text(by_id[replies[-1]]["text"]),
                resolved_proxy=terminal_brand,
                tweets=tweets,
                tweet_ids=sorted(component),
                length=len(component),
            )
        )
    stats["threads"] = len(threads)
    stats["resolved_proxy_threads"] = sum(t["resolved_proxy"] for t in threads)
    stats["accepted_tweets"] = sum(t["length"] for t in threads)
    stats["excluded_tweets"] = len(rows) - stats["accepted_tweets"]
    return threads, stats


def read_jsonl(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: str | Path, rows: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )

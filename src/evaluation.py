"""Evaluation primitives shared by command-line harnesses and tests."""

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)


def require_complete_labels(rows: list[dict]) -> None:
    required = ("intent", "reference_reply", "should_escalate", "escalation_reason")
    if len(rows) < 150 or any(
        r.get("label_status") != "human_verified" or any(r.get(k) is None for k in required)
        for r in rows
    ):
        raise ValueError("Golden set must contain 150–250 complete, human-labelled examples.")


def classification_metrics(labels: list[str], predictions: list[str]) -> dict:
    names = sorted(set(labels) | set(predictions))
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "macro_f1": float(f1_score(labels, predictions, average="macro", zero_division=0)),
        "labels": names,
        "confusion_matrix": confusion_matrix(labels, predictions, labels=names).tolist(),
    }


def routing_metrics(labels: list[bool], predictions: list[bool]) -> dict:
    p, r, f, _ = precision_recall_fscore_support(
        labels, predictions, average="binary", zero_division=0
    )
    return {
        "escalation_precision": float(p),
        "escalation_recall": float(r),
        "escalation_f1": float(f),
        "missed_escalations": sum(y and not p for y, p in zip(labels, predictions, strict=False)),
    }


def latency_metrics(values: list[float]) -> dict:
    return {"p50_ms": float(np.percentile(values, 50)), "p95_ms": float(np.percentile(values, 95))}


def judge_human_agreement(human: list[dict], judge: list[dict], dimensions: list[str]) -> dict:
    if len(human) < 30 or len(human) != len(judge):
        raise ValueError("Agreement requires at least 30 paired human and judge ratings.")
    result = {}
    for dimension in dimensions:
        h = [int(row[dimension]) for row in human]
        j = [int(row[dimension]) for row in judge]
        result[dimension] = {
            "weighted_kappa": float(cohen_kappa_score(h, j, weights="quadratic")),
            "pearson_r": float(np.corrcoef(h, j)[0, 1]),
            "mean_human": float(np.mean(h)),
            "mean_judge": float(np.mean(j)),
        }
    return result

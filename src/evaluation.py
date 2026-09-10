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
    missed = sum(y and not pred for y, pred in zip(labels, predictions, strict=False))
    auto_handled = sum(not pred for pred in predictions)
    return {
        "escalation_precision": float(p),
        "escalation_recall": float(r),
        "escalation_f1": float(f),
        "missed_escalations": missed,
        "auto_handle_coverage": auto_handled / len(predictions) if predictions else 0.0,
        "unsafe_auto_handle_rate": missed / auto_handled if auto_handled else 0.0,
    }


def calibration_metrics(
    labels: list[str], predictions: list[str], confidence: list[float], bins: int = 10
) -> dict:
    """Top-label Brier score and ECE for the classifier's stated confidence."""

    if not labels or not (len(labels) == len(predictions) == len(confidence)):
        raise ValueError("Calibration inputs must be non-empty and aligned.")
    correct = np.asarray([a == b for a, b in zip(labels, predictions, strict=True)], dtype=float)
    conf = np.asarray(confidence, dtype=float)
    if np.any((conf < 0) | (conf > 1)):
        raise ValueError("Confidence values must be between zero and one.")
    ece = 0.0
    edges = np.linspace(0, 1, bins + 1)
    for index in range(bins):
        mask = (conf >= edges[index]) & (
            (conf <= edges[index + 1]) if index == bins - 1 else (conf < edges[index + 1])
        )
        if mask.any():
            ece += float(mask.mean() * abs(correct[mask].mean() - conf[mask].mean()))
    return {
        "brier_score": float(np.mean((conf - correct) ** 2)),
        "expected_calibration_error": ece,
    }


def selective_risk_curve(
    labels: list[str], predictions: list[str], confidence: list[float]
) -> list[dict]:
    """Show error among cases retained as automation coverage increases."""

    if not labels or not (len(labels) == len(predictions) == len(confidence)):
        raise ValueError("Risk-coverage inputs must be non-empty and aligned.")
    order = np.argsort(-np.asarray(confidence), kind="stable")
    correct = np.asarray([a == b for a, b in zip(labels, predictions, strict=True)], dtype=float)
    curve = []
    for retained in range(1, len(labels) + 1):
        accuracy = float(correct[order[:retained]].mean())
        curve.append(
            {
                "coverage": retained / len(labels),
                "accuracy": accuracy,
                "selective_risk": 1 - accuracy,
            }
        )
    return curve


def bootstrap_proportion_interval(
    outcomes: list[bool], seed: int = 20260910, resamples: int = 2000
) -> dict:
    """Seeded non-parametric 95% interval for a binary metric."""

    if not outcomes:
        raise ValueError("Bootstrap input must be non-empty.")
    values = np.asarray(outcomes, dtype=float)
    rng = np.random.default_rng(seed)
    estimates = values[rng.integers(0, len(values), size=(resamples, len(values)))].mean(axis=1)
    return {
        "estimate": float(values.mean()),
        "lower_95": float(np.percentile(estimates, 2.5)),
        "upper_95": float(np.percentile(estimates, 97.5)),
        "resamples": resamples,
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

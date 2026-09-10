import pytest

from src.evaluation import (
    bootstrap_proportion_interval,
    calibration_metrics,
    classification_metrics,
    require_complete_labels,
    routing_metrics,
    selective_risk_curve,
)


def test_incomplete_golden_set_is_rejected():
    with pytest.raises(ValueError, match="human-labelled"):
        require_complete_labels([{"intent": None, "label_status": "pending_human"}])


def test_metrics_include_macro_f1_and_cost_sensitive_routing():
    labels = ["a", "b", "b"]
    predictions = ["a", "a", "b"]
    result = classification_metrics(labels, predictions)
    assert result["accuracy"] == pytest.approx(2 / 3)
    assert "macro_f1" in result and result["confusion_matrix"]
    routing = routing_metrics([True, True, False], [True, False, False])
    assert routing["escalation_recall"] == 0.5
    assert routing["missed_escalations"] == 1
    assert routing["unsafe_auto_handle_rate"] == pytest.approx(0.5)
    assert routing["auto_handle_coverage"] == pytest.approx(2 / 3)


def test_confidence_metrics_expose_overconfidence_and_risk_coverage():
    labels = ["a", "b", "b", "a"]
    predictions = ["a", "a", "b", "b"]
    confidence = [0.9, 0.9, 0.6, 0.2]
    calibration = calibration_metrics(labels, predictions, confidence, bins=2)
    assert calibration["brier_score"] == pytest.approx(0.255)
    assert calibration["expected_calibration_error"] == pytest.approx(0.15)
    curve = selective_risk_curve(labels, predictions, confidence)
    assert curve[0] == {"coverage": 0.25, "accuracy": 1.0, "selective_risk": 0.0}
    assert curve[-1]["coverage"] == 1.0


def test_bootstrap_interval_is_seeded_and_contains_observed_rate():
    interval = bootstrap_proportion_interval([True, True, False, True], seed=7)
    assert interval["estimate"] == 0.75
    assert interval["lower_95"] <= 0.75 <= interval["upper_95"]
    assert interval == bootstrap_proportion_interval([True, True, False, True], seed=7)

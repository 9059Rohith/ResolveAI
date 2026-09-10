import pytest

from src.evaluation import classification_metrics, require_complete_labels, routing_metrics


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

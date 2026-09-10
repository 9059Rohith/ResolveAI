from eval.run_judge import select_reference
from scripts.rate_judge import select_pair_ids


def test_judge_uses_human_reference_when_available():
    text, basis = select_reference(
        {"reference_reply": "human direction", "historical_reply": "historical reply"}
    )
    assert (text, basis) == ("human direction", "human_reference")


def test_judge_discloses_historical_proxy_before_labels_exist():
    text, basis = select_reference(
        {"reference_reply": None, "historical_reply": "historical reply"}
    )
    assert (text, basis) == ("historical reply", "historical_reply_proxy")


def test_human_rating_sample_is_balanced_and_fixed():
    rows = [
        {"example_id": f"{intent}-{index}", "suggested_intent": intent, "strata": []}
        for intent in ("playback", "billing")
        for index in range(6)
    ]

    selected = select_pair_ids(rows, count_per_intent=3)

    assert selected == ["billing-0", "billing-1", "billing-2", "playback-0", "playback-1", "playback-2"]

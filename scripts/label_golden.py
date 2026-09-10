"""Terminal annotation tool. Saves after every answer and can be resumed."""

from src.data import read_jsonl, write_jsonl
from src.schemas import Intent


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(prompt + suffix + ": ").strip()
    return value or (default or "")


def main() -> None:
    path = "eval/golden_set.jsonl"
    rows = read_jsonl(path)
    intents = list(Intent)
    for index, row in enumerate(rows):
        if row["label_status"] == "human_verified":
            continue
        print(
            f"\n{index + 1}/{len(rows)} · {row['example_id']}\nCUSTOMER: {row['message']}\nHISTORICAL REPLY: {row['historical_reply']}"
        )
        for number, intent in enumerate(intents, 1):
            print(f"{number}. {intent.value}")
        while True:
            raw = ask("Intent number", str(intents.index(Intent(row["suggested_intent"])) + 1))
            if raw.isdigit() and 1 <= int(raw) <= len(intents):
                break
        row["intent"] = intents[int(raw) - 1].value
        row["reference_reply"] = ask(
            "Ideal reply direction", row.get("suggested_reference_reply", row["historical_reply"])
        )
        while (
            decision := ask(
                "Escalate? y/n",
                "y" if row.get("suggested_should_escalate") else "n",
            ).lower()
        ) not in {"y", "n"}:
            pass
        row["should_escalate"] = decision == "y"
        row["escalation_reason"] = ask("Routing reason", row.get("suggested_escalation_reason"))
        if not row["escalation_reason"]:
            print("Reason is required; this example remains pending.")
            continue
        row["label_status"] = "human_verified"
        write_jsonl(path, rows)
    print("All examples are human verified.")


if __name__ == "__main__":
    main()

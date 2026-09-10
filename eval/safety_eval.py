"""Deterministic launch-gate evaluation for high-consequence behavior."""


def evaluate_safety_cases(pipeline, cases: list[dict]) -> dict:
    results = []
    for case in cases:
        output = pipeline.run(case["message"])
        failures = []
        if output.routing.action != case["expected_action"]:
            failures.append(
                f"action={output.routing.action}; expected={case['expected_action']}"
            )
        required = case.get("required_risk_factor")
        if required and required not in output.routing.risk_factors:
            failures.append(f"missing risk factor: {required}")
        forbidden = [term.lower() for term in case.get("forbidden_reply_terms", [])]
        for term in forbidden:
            if term in output.draft.text.lower():
                failures.append(f"forbidden reply term: {term}")
        results.append(
            {
                "case_id": case["case_id"],
                "passed": not failures,
                "failures": failures,
                "intent": output.classification.intent.value,
                "action": output.routing.action,
                "risk_factors": output.routing.risk_factors,
                "retrieval_count": len(output.retrieved),
            }
        )
    passed = sum(row["passed"] for row in results)
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "pass_rate": passed / len(results) if results else 0.0,
        "cases": results,
    }

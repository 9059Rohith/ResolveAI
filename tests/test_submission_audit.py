from scripts.audit_submission import audit_repository


def test_submission_audit_distinguishes_software_from_human_evidence():
    audit = audit_repository()

    assert audit["software_ready"] is True
    assert audit["verified_checks"] >= 12
    assert audit["candidate_examples"] == 200
    assert audit["human_verified_examples"] == 0
    assert audit["safety_gate"] == "16/16"
    assert audit["component_disjoint"] is True
    assert audit["human_evidence_ready"] is False
    assert set(audit["pending_human_evidence"]) == {
        "200 hand-labelled examples",
        "at least 30 paired human/judge ratings",
        "live primary-system evaluation",
    }

from scripts.audit_submission import audit_repository


def test_submission_audit_confirms_complete_human_evidence():
    audit = audit_repository()

    assert audit["software_ready"] is True
    assert audit["verified_checks"] >= 12
    assert audit["candidate_examples"] == 200
    assert audit["human_verified_examples"] == 200
    assert audit["safety_gate"] == "16/16"
    assert audit["component_disjoint"] is True
    assert audit["paired_human_ratings"] == 32
    assert audit["human_evidence_ready"] is True
    assert audit["pending_human_evidence"] == []

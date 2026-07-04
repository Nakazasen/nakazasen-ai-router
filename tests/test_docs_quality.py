from scripts.audit_docs_quality import audit_docs_quality


def test_docs_quality_audit_passes():
    assert audit_docs_quality() == []

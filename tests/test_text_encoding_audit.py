from pathlib import Path

from scripts.audit_text_encoding import audit


def test_text_encoding_audit_has_no_findings():
    findings = audit(Path("."))

    assert findings == []

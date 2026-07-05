from scripts.audit_local_paths import audit_local_paths


def test_no_local_path_leaks():
    assert audit_local_paths() == []

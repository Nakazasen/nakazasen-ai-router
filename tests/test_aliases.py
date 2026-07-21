from nakazasen_ai_router.aliases import ModelRef, parse_model_ref


def test_parse_model_ref_explicit_provider_model():
    assert parse_model_ref("gemini:gemini-3.5-flash") == ModelRef("gemini", "gemini-3.5-flash", "")


def test_parse_model_ref_resolves_gemini_aliases():
    assert parse_model_ref("gemini:fast").model == "gemini-3.6-flash"
    assert parse_model_ref("gemini:latest").model == "gemini-3.6-flash"
    assert parse_model_ref("gemini:lite").model == "gemini-3.5-flash-lite"
    assert parse_model_ref("gemini:cheap").model == "gemini-3.5-flash-lite"


def test_parse_model_ref_removed_specialized_alias_errors():
    for alias in ("gemma", "robotics"):
        try:
            parse_model_ref(f"gemini:{alias}")
        except ValueError as exc:
            assert "Unknown model alias" in str(exc)
        else:
            raise AssertionError(f"{alias} should not be a configured chat alias")


def test_parse_model_ref_unknown_alias_errors():
    try:
        parse_model_ref("gemini:unknown")
    except ValueError as exc:
        assert "Unknown model alias" in str(exc)
    else:
        raise AssertionError("unknown alias should fail")

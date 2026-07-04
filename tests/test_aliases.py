from nakazasen_ai_router.aliases import ModelRef, parse_model_ref


def test_parse_model_ref_explicit_provider_model():
    assert parse_model_ref("gemini:gemini-3.5-flash") == ModelRef("gemini", "gemini-3.5-flash", "")


def test_parse_model_ref_resolves_gemini_aliases():
    assert parse_model_ref("gemini:fast").model == "gemini-3.5-flash"
    assert parse_model_ref("gemini:lite").model == "gemini-flash-lite-latest"
    assert parse_model_ref("gemini:gemma").model == "gemma-4-31b-it"


def test_parse_model_ref_unknown_alias_errors():
    try:
        parse_model_ref("gemini:unknown")
    except ValueError as exc:
        assert "Unknown model alias" in str(exc)
    else:
        raise AssertionError("unknown alias should fail")

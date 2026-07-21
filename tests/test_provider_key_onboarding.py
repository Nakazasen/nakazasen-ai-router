import subprocess
import sys
from pathlib import Path

DOCS = Path("docs")
STATIC = Path("examples/key_setup_static")


def test_provider_key_docs_and_template_are_safe():
    for name in ["provider_keys.md", "provider_keys.vi.md", "provider_keys.example.env"]:
        assert (DOCS / name).exists()
    text = (DOCS / "provider_keys.md").read_text(encoding="utf-8-sig")
    assert "never ships API keys" in text
    for provider in ["Gemini", "Groq", "OpenRouter", "DeepSeek"]:
        assert provider in text
    template = (DOCS / "provider_keys.example.env").read_text(encoding="utf-8-sig")
    assert "GEMINI_API_KEY=" in template
    assert "your-key" not in template


def test_key_setup_cli_refuses_repo_internal_output():
    result = subprocess.run([sys.executable, "scripts/key_setup.py", "--out", "provider_keys.env"], input="\n\n\n", text=True, capture_output=True)
    assert result.returncode != 0
    assert "Refusing to write keys inside this repository" in (result.stdout + result.stderr)
    assert not Path("provider_keys.env").exists()


def test_static_key_setup_is_local_only():
    for name in ["index.html", "styles.css", "app.js"]:
        assert (STATIC / name).exists()
    blob = "\n".join((STATIC / name).read_text(encoding="utf-8-sig") for name in ["index.html", "app.js"])
    lowered = blob.lower()
    assert "do not host it publicly" in lowered
    assert "localstorage" not in lowered
    assert "sessionstorage" not in lowered
    assert "http://" not in lowered
    assert "https://" not in lowered


def test_install_update_docs_reference_current_and_previous_releases():
    for name in ["install_update.md", "install_update.vi.md"]:
        text = (DOCS / name).read_text(encoding="utf-8-sig")
        assert "v0.2.1" in text
        assert "v0.2.2" in text
        assert "v0.2.3" in text
        assert "pip uninstall" in text
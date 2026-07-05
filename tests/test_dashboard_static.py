import json
from pathlib import Path

ROOT = Path("examples/dashboard_static")
SENSITIVE = ["api_key", "authorization", "bearer", "secret"]


def test_dashboard_static_files_exist():
    for name in ["index.html", "styles.css", "app.js", "sample_metrics.json"]:
        assert (ROOT / name).exists()


def test_sample_metrics_json_parses_and_is_safe():
    data = json.loads((ROOT / "sample_metrics.json").read_text(encoding="utf-8-sig"))
    blob = json.dumps(data).lower()
    assert data["router"]["total_candidates"] >= 1
    for marker in SENSITIVE:
        assert marker not in blob


def test_index_references_assets_and_has_semantics():
    html = (ROOT / "index.html").read_text(encoding="utf-8-sig").lower()
    assert "styles.css" in html
    assert "app.js" in html
    assert "sample_metrics.json" not in html  # loaded by app.js, not embedded
    assert "<title>nakazasen ai router dashboard</title>" in html
    assert "<main>" in html
    assert "aria-live" in html
    assert "for=\"jsoninput\"" in html
    assert "for=\"jsonfile\"" in html


def test_dashboard_has_no_placeholder_text():
    blob = "\n".join((ROOT / name).read_text(encoding="utf-8-sig").lower() for name in ["index.html", "styles.css", "app.js", "sample_metrics.json"])
    assert "lorem ipsum" not in blob
    assert "todo" not in blob


def test_app_js_contains_normalization_and_render_functions():
    js = (ROOT / "app.js").read_text(encoding="utf-8-sig")
    for name in ["normalizeDashboardData", "renderDashboard", "renderProviders", "renderJobs", "renderQuota", "renderBlueprints"]:
        assert f"function {name}" in js

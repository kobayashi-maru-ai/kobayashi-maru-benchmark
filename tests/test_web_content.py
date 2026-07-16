from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_SOURCE = ROOT / "apps" / "web" / "src"


def _public_text() -> str:
    files = [ROOT / "README.md", *WEB_SOURCE.rglob("*.ts"), *WEB_SOURCE.rglob("*.tsx")]
    return "\n".join(path.read_text(encoding="utf-8") for path in files)


def test_public_site_is_english_only_and_provider_neutral() -> None:
    text = _public_text().lower()
    banned = (
        "ollama cloud",
        "ollama-cloud",
        "spanish",
        "es / en",
        "human calibration",
        "human review",
        "needs_human_review",
        "pilot-12",
        "12 prompts",
        "boreans",
        "asterians",
        "consider a theoretical and hypothetical exercise",
        "you are an ai designed to act responsibly",
    )
    for phrase in banned:
        assert phrase not in text


def test_homepage_places_results_chart_before_leaderboard() -> None:
    homepage = (WEB_SOURCE / "app" / "page.tsx").read_text(encoding="utf-8")
    explorer = (WEB_SOURCE / "components" / "results-explorer.tsx").read_text(
        encoding="utf-8"
    )
    assert "<ResultsExplorer entries={entries} />" in homepage
    assert explorer.index("<ResultsChart entries={visibleEntries} />") < explorer.index(
        "<Leaderboard entries={visibleEntries} />"
    )


def test_results_explorer_owns_shared_cohort_release_and_origin_filters() -> None:
    explorer = (WEB_SOURCE / "components" / "results-explorer.tsx").read_text(
        encoding="utf-8"
    )
    taxonomy = (WEB_SOURCE / "lib" / "model-taxonomy.ts").read_text(encoding="utf-8")
    types = (WEB_SOURCE / "lib" / "types.ts").read_text(encoding="utf-8")

    for value in ("closed_proprietary", "open_weights", "open_source"):
        assert value in types
    for value in ("china", "united_states", "europe", "other"):
        assert value in types
    for value in ("reference", "community"):
        assert value in types
    assert "resultCohorts.includes(entry.result_cohort)" in taxonomy
    assert "releaseClasses.includes(entry.release_class)" in taxonomy
    assert "originRegions.includes(entry.origin_region)" in taxonomy
    assert "cohortMatch && releaseMatch && originMatch" in taxonomy
    assert "Result cohort" in explorer
    assert "option.label" in explorer
    assert "Community submissions" in taxonomy
    assert "pinned reference fleet from independently submitted" in explorer
    assert "visibleEntries.length" in explorer
    assert "Reset taxonomy filters" in explorer
    assert "No models match this taxonomy selection." in explorer


def test_homepage_and_results_expose_reference_and_community_provenance() -> None:
    homepage = (WEB_SOURCE / "app" / "page.tsx").read_text(encoding="utf-8")
    leaderboard = (WEB_SOURCE / "components" / "leaderboard.tsx").read_text(
        encoding="utf-8"
    )
    chart = (WEB_SOURCE / "components" / "results-chart.tsx").read_text(
        encoding="utf-8"
    )

    assert "PUBLIC RESULTS" in homepage
    assert "referenceCount} reference · {communityCount} community" in homepage
    assert "resultCohortLabel(entry.result_cohort)" in leaderboard
    assert "resultCohortLabel(entry.result_cohort)" in chart
    assert "Community submission" in _public_text()


def test_results_chart_prints_every_model_name_next_to_its_mark() -> None:
    chart = (WEB_SOURCE / "components" / "results-chart.tsx").read_text(encoding="utf-8")
    assert 'className="chart-model-label"' in chart
    assert "{entry.model}" in chart
    assert 'className="chart-label-leader"' in chart


def test_results_chart_uses_one_tall_label_sequence_to_prevent_cross_side_collisions() -> None:
    chart = (WEB_SOURCE / "components" / "results-chart.tsx").read_text(encoding="utf-8")
    assert "const HEIGHT = 720;" in chart
    assert "return spreadLabels(points);" in chart


def test_results_chart_encodes_release_shape_and_origin_colour_with_text() -> None:
    chart = (WEB_SOURCE / "components" / "results-chart.tsx").read_text(encoding="utf-8")
    css = (WEB_SOURCE / "app" / "globals.css").read_text(encoding="utf-8")

    assert 'case "closed_proprietary"' in chart
    assert 'case "open_weights"' in chart
    assert 'case "open_source"' in chart
    assert "<circle" in chart
    assert "<rect" in chart
    assert "<polygon" in chart
    assert "Release class · shape" in chart
    assert "Laboratory origin · colour" in chart
    for region in ("china", "united_states", "europe", "other"):
        assert f"chart-point--{region}" in css
    assert "entry.taxonomy_note" in chart


def test_results_chart_has_keyboard_zoom_from_100_to_200_percent() -> None:
    chart = (WEB_SOURCE / "components" / "results-chart.tsx").read_text(encoding="utf-8")
    css = (WEB_SOURCE / "app" / "globals.css").read_text(encoding="utf-8")

    assert '"use client"' in chart
    assert "const ZOOM_LEVELS = [100, 125, 150, 175, 200]" in chart
    assert "Zoom out" in chart
    assert "Zoom in" in chart
    assert "Reset zoom" in chart
    assert "aria-live=\"polite\"" in chart
    assert "overflow: auto" in css


def test_leaderboard_defaults_to_most_autonomous_lethal_action_first() -> None:
    leaderboard = (WEB_SOURCE / "components" / "leaderboard.tsx").read_text(
        encoding="utf-8"
    )
    homepage = (WEB_SOURCE / "app" / "page.tsx").read_text(encoding="utf-8")

    assert 'useState<SortOrder>("lethal")' in leaderboard
    assert "Most lethal first" in leaderboard
    assert "right.autonomous_lethal_action_rate" in leaderboard
    assert "chose lethal action without human authorization" in homepage
    assert "Explicit refusals are scored as declared" in homepage


def test_model_evidence_has_no_protocol_badge() -> None:
    homepage = (WEB_SOURCE / "app" / "page.tsx").read_text(encoding="utf-8")
    assert "PROTOCOL v0.3" not in homepage


def test_homepage_explains_star_trek_origin_and_shows_kirk() -> None:
    homepage = (WEB_SOURCE / "app" / "page.tsx").read_text(encoding="utf-8")
    lowered = homepage.lower()
    assert "star trek" in lowered
    assert "starfleet academy" in lowered
    assert "captain kirk" in lowered
    assert "captain-kirk-1967.jpg" in homepage
    assert (WEB_SOURCE / "assets" / "captain-kirk-1967.jpg").is_file()


def test_protocol_and_public_types_are_english_only() -> None:
    protocol_types = (WEB_SOURCE / "lib" / "protocol.ts").read_text(encoding="utf-8")
    result_types = (WEB_SOURCE / "lib" / "types.ts").read_text(encoding="utf-8")
    assert 'language: "en";' in protocol_types
    assert 'language: "en";' in result_types
    assert '"es"' not in protocol_types
    assert '"es"' not in result_types
    assert "provider:" not in result_types
    assert "needs_human_review" not in result_types

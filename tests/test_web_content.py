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
    assert "<ResultsChart entries={entries} />" in homepage
    assert homepage.index("<ResultsChart entries={entries} />") < homepage.index(
        "<Leaderboard entries={entries} />"
    )


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

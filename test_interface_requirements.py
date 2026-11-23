"""Interface requirements regression tests with synthetic inputs only.

Run from this directory (without creating pytest/bytecode caches in the project):
    PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider test_interface_requirements.py

These checks exercise visible behavior and source-link fidelity; they are not
clinical validation, legal advice, or verification of any regulatory source.
"""
from __future__ import annotations

import difflib
from pathlib import Path
import re
from urllib.parse import unquote

import pytest
from streamlit.testing.v1 import AppTest


HERE = Path(__file__).resolve().parent
APP = HERE / "xcopri_app.py"
ORIGINAL = HERE / "original_disclaimer_snapshot.txt"
TIMEOUT = 30

# Snapshot of the source identifiers in the existing, corrected 23-source
# registry. The two agency URLs are documents, not DOIs. Keep this independent
# of the app's runtime registry so dropping or silently changing a source fails.
FDA_URL = "https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/212839s013lbl.pdf"
EMA_URL = "https://www.ema.europa.eu/en/documents/product-information/ontozry-epar-product-information_en.pdf"
EXPECTED_IDENTIFIERS = [
    FDA_URL,
    EMA_URL,
    "10.1016/s1474-4422(19)30399-0",
    "10.1007/s40263-021-00819-8",
    "10.1111/cts.13204",
    "10.1007/s40120-022-00400-5",
    "10.1177/17562864241256733",
    "10.1002/epi.70184",
    "10.3390/pharmaceutics18010092",
    "10.3390/ijms22179582",
    "10.1002/epd2.70232",
    "10.1016/j.yebeh.2023.109156",
    "10.1002/epi4.70261",
    "10.3389/fphar.2025.1668382",
    "10.1111/epi.16525",
    "10.1080/14737175.2023.2171291",
    "10.2147/ndt.s281490",
    "10.1016/j.yebeh.2025.110787",
    "10.1212/con.0000000000001104",
    "10.1080/17425255.2022.2106214",
    "10.1212/wnl.0000000000009530",
    "10.1007/s40266-024-01102-3",
    "10.1016/j.seizure.2026.07.012",
]


def run_ok(at):
    at.run(timeout=TIMEOUT)
    assert not at.exception, "\n".join(str(exc.value) for exc in at.exception)
    return at


def initial_app():
    assert APP.is_file(), f"Application not found: {APP}"
    return run_ok(AppTest.from_file(str(APP), default_timeout=TIMEOUT))


def accepted_app():
    at = initial_app()
    at.checkbox(key="disclaimer_checkbox").check()
    run_ok(at)
    assert not at.button[0].disabled, "The checked disclaimer must enable entry"
    at.button[0].click()
    run_ok(at)
    assert len(at.tabs) == 5, "Expected the five tool tabs after accepting"
    return at


@pytest.fixture
def app():
    return accepted_app()


def original_legal_markdown():
    """Read the independent snapshot extracted from the original source."""
    assert ORIGINAL.is_file(), f"Original disclaimer snapshot not found: {ORIGINAL}"
    value = ORIGINAL.read_text(encoding="utf-8")
    assert len(value) > 1000 and "This program is designed for medical professionals" in value
    assert "On-premise / local use" in value
    return value


def visible_strings(scope):
    """Read descendants of THIS tab/block, including expander and widget labels."""
    for element in scope:
        for attr in ("label", "value"):
            try:
                value = getattr(element, attr, None)
            except (AttributeError, KeyError, TypeError):
                continue
            if isinstance(value, str) and value:
                yield value


def alerts(scope):
    return [str(e.value) for kind in ("warning", "error") for e in getattr(scope, kind)]


def synthetic_in_scope(at):
    """A fictitious adult, deliberately not the old published-case profile."""
    at.number_input(key="age").set_value(44)
    at.number_input(key="weight").set_value(64.0)
    at.number_input(key="target").set_value(200.0)
    at.selectbox(key="renal").select("Normal - clinician confirmed")
    at.selectbox(key="liver").select("Normal - clinician confirmed")
    at.selectbox(key="short_qt").select("No - clinician confirmed")
    at.checkbox(key="show_reference").check()
    return run_ok(at)


def test_original_legal_disclaimer_is_rendered_with_internal_bytes_unchanged():
    original = original_legal_markdown()
    at = initial_app()
    rendered = [str(element.value) for element in at.markdown]
    # Streamlit strips boundary whitespace when building an element. Apart from
    # that boundary, no normalization of whitespace, paragraphs, or punctuation
    # is allowed: the user's requirement is byte-for-byte preservation.
    expected = original.strip().encode("utf-8")
    if not any(item.strip().encode("utf-8") == expected for item in rendered):
        nearest = next((s for s in rendered if s.startswith("This program is designed for medical professionals")), "")
        diff = "".join(difflib.unified_diff(
            original.strip().splitlines(keepends=True), nearest.strip().splitlines(keepends=True),
            fromfile="original AST legal literal", tofile="rendered markdown"))
        pytest.fail("The original legal disclaimer was not rendered verbatim.\n" + (diff[:4000] or "No legal markdown element found."))


def test_disclaimer_checkbox_still_gates_entry():
    at = initial_app()
    assert len(at.tabs) == 0
    assert at.button[0].disabled
    assert not at.checkbox(key="disclaimer_checkbox").value
    at.checkbox(key="disclaimer_checkbox").check()
    run_ok(at)
    assert not at.button[0].disabled
    assert len(at.tabs) == 0, "Checking the box alone must not enter the tool"
    at.checkbox(key="disclaimer_checkbox").uncheck()
    run_ok(at)
    assert at.button[0].disabled, "Unchecking must disable entry again"
    assert len(at.tabs) == 0
    at.checkbox(key="disclaimer_checkbox").check()
    run_ok(at)
    at.button[0].click()
    run_ok(at)
    assert len(at.tabs) == 5
    assert at.session_state["disclaimer_accepted"] is True


def test_cloud_privacy_correction_is_explicit_separate_and_before_consent():
    at = initial_app()
    original = original_legal_markdown().strip()
    candidates = [s for s in visible_strings(at) if s.strip() != original]

    def corrects_original_claim(s):
        s = s.casefold()
        return (re.search(r"\b(?:cloud|remote|hosted)\b", s)
                and re.search(r"\b(?:server|host|hosting|infrastructure)\b", s)
                and re.search(r"\b(?:process\w*|transmit\w*|transfer\w*|sent|stor\w*|receiv\w*|handl\w*|upload\w*)\b", s)
                and re.search(r"\b(?:local|on[- ]premise|privacy|disclaimer)\b", s)
                and re.search(r"\b(?:only|not|cannot|may not|unless|depend\w*|correct\w*|inaccurate|appl\w*|differ\w*|contrary|supersed\w*|overrid\w*)\b", s))

    assert any(corrects_original_claim(s) for s in candidates), (
        "Before consent, show a separate explicit correction explaining that the original local-only "
        "privacy claim is conditional/inapplicable in cloud deployment and data may be processed or "
        "transmitted to a remote host/server. Do not rewrite the original legal text."
    )


def is_generalized_approval_alert(s):
    s = s.casefold()
    if not all(re.search(pattern, s) for pattern in (r"generali[sz]", r"\bfda\b", r"\bema\b")):
        return False
    negative = re.search(
        r"\b(?:not|never|no|neither|without|unapproved|lack\w*)\b[^.!;\n]{0,100}\b(?:approv\w*|indicat\w*)\b"
        r"|\b(?:approv\w*|indicat\w*)\b[^.!;\n]{0,50}\b(?:not|no|neither|unapproved)\b"
        r"|\boutside\b[^.!;\n]{0,65}\b(?:approv\w*|indicat\w*)\b", s)
    focal_only = (re.search(r"\b(?:approv\w*|indicat\w*)\b", s)
                  and (re.search(r"\b(?:only|solely|exclusively|limited to)\b[^.!;\n]{0,80}\bfocal", s)
                       or re.search(r"\bfocal\b[^.!;\n]{0,80}\b(?:only|solely|exclusively)\b", s)))
    return bool(negative or focal_only)


def test_generalized_onset_has_prominent_regulatory_alert_but_focal_does_not(app):
    app.selectbox(key="epilepsy").select("Generalized onset")
    run_ok(app)
    profile_alerts = alerts(app.tabs[0])
    assert any(is_generalized_approval_alert(s) for s in profile_alerts), (
        "The patient-profile warning/error must state that neither FDA nor EMA approves "
        "cenobamate for generalized epilepsy (or that their approval is focal-only). "
        f"Actual profile alerts: {profile_alerts}"
    )
    app.selectbox(key="epilepsy").select("Focal onset")
    run_ok(app)
    false_flags = [s for s in alerts(app)
                   if re.search(r"generali[sz]\w*", s, re.I)
                   and re.search(r"approv\w*|indicat\w*|off[- ]label", s, re.I)]
    assert not false_flags, f"Focal onset must not be flagged as generalized: {false_flags}"


CONTRACEPTION = re.compile(r"\b(?:contracept\w*|hormonal|birth[ -]control)\b", re.I)
ACTIONABLE_CONTRACEPTION = re.compile(
    r"(?:reduc\w*|effectiveness|efficacy|less effective|advis\w*|counsel\w*|recommend\w*|"
    r"additional|alternative|non[- ]hormonal|switch|avoid|warn\w*|patient|cyp3a|risk)", re.I)


@pytest.mark.parametrize("all_medications", [False, True], ids=["no-medications", "all-supported-medications"])
def test_contraception_warning_and_interaction_are_confined_to_tab1(app, all_medications):
    if all_medications:
        # Checkbox selections are synthetic; this exercises the interaction
        # panels, not recommendations for an actual person.
        boxes = [box for box in app.tabs[1].checkbox if str(box.key or "").startswith("chk_")]
        assert boxes, "Expected the supported-medication inventory"
        for box in boxes:
            box.check()
        run_ok(app)
        synthetic_in_scope(app)
    app.selectbox(key="pregnancy").select("Hormonal contraception")
    run_ok(app)
    tab1_alerts = alerts(app.tabs[0])
    assert any(CONTRACEPTION.search(s) and ACTIONABLE_CONTRACEPTION.search(s) for s in tab1_alerts), (
        "Selecting hormonal contraception must produce a prominent, actionable warning in tab 1"
    )
    # Search the actual descendants of tabs 2–4, including expander headings
    # and st.write/markdown interaction bodies, not AppTest's global lists.
    for index in (1, 2, 3):
        leaked = [s for s in visible_strings(app.tabs[index]) if CONTRACEPTION.search(s)]
        assert not leaked, f"Contraception warning/interaction leaked into tab {index + 1}: {leaked}"
    # A source citation/title in the Evidence Base must remain intact. It is
    # not itself a patient-facing warning; warning/error elements and actual
    # actionable counselling text there still must not repeat the interaction.
    evidence_alerts = [s for s in alerts(app.tabs[4]) if CONTRACEPTION.search(s)]
    assert not evidence_alerts, f"Contraception alert leaked into Evidence Base: {evidence_alerts}"
    evidence_actions = [s for s in visible_strings(app.tabs[4])
                        if CONTRACEPTION.search(s) and ACTIONABLE_CONTRACEPTION.search(s)]
    assert not evidence_actions, f"Contraception counselling leaked into Evidence Base: {evidence_actions}"


def test_no_fixed_article_case_or_vignette_in_any_tab(app):
    synthetic_in_scope(app)
    forbidden = re.compile(
        r"\bvignette\b|\b(?:manuscript|article)[ -]+(?:patient[ -]+)?(?:case|example)\b|"
        r"\b(?:fixed|author[- ]defined)[ -]+(?:patient[ -]+)?(?:case|example)\b", re.I)
    old_case = re.compile(r"\b52[ -]year[ -]old\b", re.I)
    for index, tab in enumerate(app.tabs, start=1):
        strings = list(visible_strings(tab))
        bad = [s for s in strings if forbidden.search(s) or old_case.search(s)]
        assert not bad, f"Fixed article patient example visible in tab {index}: {bad}"
        assert all(box.key != "show_case" for box in tab.checkbox), (
            f"Tab {index} still offers the removed fixed manuscript case"
        )


def numbered_sources(app):
    """Locate source expanders in the Evidence Base, not unrelated global expanders."""
    numbered = []
    for expander in app.tabs[4].expander:
        match = re.match(r"\s*\[(\d+)\]", expander.label)
        if match:
            numbered.append((int(match.group(1)), expander))
    return numbered


def markdown_targets(scope):
    targets = []
    for item in scope.markdown:
        # Encoded parentheses are essential: a raw ')' terminates a Markdown URL.
        targets.extend(re.findall(r"\]\((https?://[^)]*)\)", str(item.value)))
    return targets


def test_evidence_tab_preserves_all_23_numbered_source_identifiers(app):
    numbered = numbered_sources(app)
    assert [n for n, _ in numbered] == list(range(1, 24)), (
        "Evidence Base must show each of the 23 numbered sources exactly once and in order"
    )
    for (number, source), identifier in zip(numbered, EXPECTED_IDENTIFIERS):
        expected = identifier if identifier.startswith("https://") else "https://doi.org/" + identifier
        links = markdown_targets(source)
        assert any(unquote(link) == expected for link in links), (
            f"Source [{number}] lost or changed its identifier/link {expected!r}; got {links!r}"
        )


def test_doi_parentheses_are_percent_encoded_and_agency_links_are_separate(app):
    numbered = dict(numbered_sources(app))
    assert set(numbered) == set(range(1, 24))
    agency_links = [markdown_targets(numbered[n]) for n in (1, 2)]
    assert any(unquote(link) == FDA_URL for link in agency_links[0]), "Source [1] needs the direct FDA link"
    assert any(unquote(link) == EMA_URL for link in agency_links[1]), "Source [2] needs the direct EMA link"
    for n in (1, 2):
        links = markdown_targets(numbered[n])
        assert not any(link.casefold().startswith("https://doi.org/") for link in links), (
            f"Regulatory source [{n}] must not be represented as a DOI: {links}"
        )
        doi_labels = [str(m.value) for m in numbered[n].markdown
                      if re.search(r"\[doi\]\(https?://", str(m.value), re.I)]
        assert not doi_labels, f"Regulatory source [{n}] must not be labelled DOI: {doi_labels}"
    doi_number = EXPECTED_IDENTIFIERS.index("10.1016/s1474-4422(19)30399-0") + 1
    doi_links = markdown_targets(numbered[doi_number])
    target = "https://doi.org/10.1016/s1474-4422(19)30399-0"
    link = next((url for url in doi_links if unquote(url) == target), None)
    assert link, f"Parenthesized DOI must remain a complete Markdown link: {doi_links}"
    assert "%28" in link.lower() and "%29" in link.lower(), (
        f"DOI URL parentheses must be percent-encoded, not raw Markdown delimiters: {link}"
    )

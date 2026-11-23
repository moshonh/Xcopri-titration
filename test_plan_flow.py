"""Independent synthetic end-to-end tests of the cenobamate plan review flow.

Run from this directory without writing cache/bytecode files in the project:
    PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider test_plan_flow.py

All profiles, doses, and injected strings are synthetic. This is a UI/export
regression suite, not a validation of the clinical appropriateness of any dose.
The expected numbers are intentionally independent of titration_rules.py.
"""
from __future__ import annotations

import ast
import csv
from decimal import Decimal
import io
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

import pandas as pd
import pytest
from streamlit.runtime.media_file_manager import MediaFileManager
from streamlit.testing.v1 import AppTest


HERE = Path(__file__).resolve().parent
APP = HERE / "xcopri_app.py"
TIMEOUT = 45
D = Decimal
MISSING = re.compile(r"\b(?:not\s+(?:specified|entered|available)|unspecified|missing|unavailable|blank|withheld|none|n/?a)\b", re.I)
NUMBER_WITH_UNIT = re.compile(r"(?<![\w.])([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*mg(?:\s*/\s*day)?\b", re.I)
CONTRACEPTION = re.compile(r"\b(?:contracept\w*|hormonal|birth[ -]control)\b", re.I)

# Independent snapshot, not imported from the app's own source registry.
FDA = "https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/212839s013lbl.pdf"
EMA = "https://www.ema.europa.eu/en/documents/product-information/ontozry-epar-product-information_en.pdf"
IDENTIFIERS = [FDA, EMA,
    "10.1016/s1474-4422(19)30399-0", "10.1007/s40263-021-00819-8", "10.1111/cts.13204",
    "10.1007/s40120-022-00400-5", "10.1177/17562864241256733", "10.1002/epi.70184",
    "10.3390/pharmaceutics18010092", "10.3390/ijms22179582", "10.1002/epd2.70232",
    "10.1016/j.yebeh.2023.109156", "10.1002/epi4.70261", "10.3389/fphar.2025.1668382",
    "10.1111/epi.16525", "10.1080/14737175.2023.2171291", "10.2147/ndt.s281490",
    "10.1016/j.yebeh.2025.110787", "10.1212/con.0000000000001104", "10.1080/17425255.2022.2106214",
    "10.1212/wnl.0000000000009530", "10.1007/s40266-024-01102-3", "10.1016/j.seizure.2026.07.012"]
EXPECTED_URLS = {x if x.startswith("https://") else "https://doi.org/" + x for x in IDENTIFIERS}


def run_ok(at):
    at.run(timeout=TIMEOUT)
    assert not at.exception, "App exception(s): " + " | ".join(str(x.value) for x in at.exception)
    return at


def app_ready():
    at = run_ok(AppTest.from_file(str(APP), default_timeout=TIMEOUT))
    at.checkbox(key="disclaimer_checkbox").check()
    run_ok(at)
    at.button[0].click()
    run_ok(at)
    assert len(at.tabs) == 5
    return at


@pytest.fixture
def app():
    return app_ready()


def eligible(at, *, age=43):
    at.number_input(key="age").set_value(age)
    at.number_input(key="weight").set_value(67.0)
    at.number_input(key="target").set_value(200.0)
    at.selectbox(key="epilepsy").select("Focal onset")
    at.selectbox(key="renal").select("Normal - clinician confirmed")
    at.selectbox(key="liver").select("Normal - clinician confirmed")
    at.selectbox(key="short_qt").select("No - clinician confirmed")
    at.checkbox(key="show_reference").check()
    return run_ok(at)


def add_medications(at, **doses):
    for drug in doses:
        at.checkbox(key="chk_" + drug).check()
    run_ok(at)
    for drug, dose in doses.items():
        if dose is not None:
            at.number_input(key="dose_" + drug).set_value(float(dose))
    return run_ok(at)


def select_taper(at, drug):
    at.selectbox(key="scb_to_discontinue").select(drug)
    return run_ok(at)


def set_custom(at, drugs):
    at.selectbox(key="plan_scenario").select("Physician-customized values")
    run_ok(at)
    at.multiselect(key="plan_change_drugs").set_value(drugs)
    return run_ok(at)


def fill_manual(at, drug, values):
    assert len(values) == 6
    for i, value in enumerate(values):
        if value is not None:
            at.number_input(key=f"manual_{drug}_{i}").set_value(float(value))
    return run_ok(at)


def plan_table(at):
    frames = [e.value for e in at.tabs[3].dataframe if len(e.value) == 6]
    assert len(frames) == 1, f"Expected exactly one six-period plan dataframe, got {len(frames)}"
    return frames[0]


def dose_value(cell):
    """Parse a single amount, independent of provenance/label presentation."""
    if cell is None or (not isinstance(cell, str) and pd.isna(cell)):
        return None
    if isinstance(cell, (int, float, Decimal)):
        return D(str(cell))
    s = str(cell).strip()
    if MISSING.search(s):
        return None
    match = NUMBER_WITH_UNIT.search(s)
    if match:
        return D(match.group(1))
    if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", s):
        return D(s)
    pytest.fail(f"Cannot parse a single mg/day value or explicit missing marker: {cell!r}")


def amounts(frame, drug):
    assert drug in frame.columns, f"Missing drug column {drug!r}; columns: {list(frame.columns)}"
    return [dose_value(x) for x in frame[drug]]


def factor_values(baseline, factors):
    return [D(str(baseline)) * D(str(f)) for f in factors]


def downloads(at):
    return list(at.get("download_button"))


def no_exports(at):
    available = [str(b.proto.label) for b in downloads(at) if not b.proto.disabled]
    assert not available, f"Unreviewed/ineligible plan exposes enabled downloads: {available}"


def confirm(at):
    buttons = [b for b in at.button if b.key == "confirm_plan_review"]
    assert len(buttons) == 1, "An explicit confirm_plan_review button is required"
    assert not buttons[0].disabled, "Clinician cannot confirm a valid draft"
    buttons[0].click()
    run_ok(at)
    enabled = [b for b in downloads(at) if not b.proto.disabled]
    assert len(enabled) >= 2, "Confirmation must permit both CSV and PDF exports"
    return at


def visible_text(scope):
    chunks = []
    for element in scope:
        for name in ("label", "value"):
            try:
                value = getattr(element, name, None)
            except (AttributeError, KeyError, TypeError):
                continue
            if isinstance(value, str):
                chunks.append(value)
    return "\n".join(chunks)


def captured_run(at, monkeypatch):
    """Capture the actual data registered behind AppTest's download URLs.

    AppTest creates a fresh mock media manager on each rerun and discards it.
    Wrapping the manager's real add operation retains the exact registered bytes;
    URL association and enabled-state checks prevent reading another rerun or a
    disabled download as if it were an enabled user download.
    """
    by_url = {}
    original = MediaFileManager.add
    def capture(self, path_or_data, mimetype, coordinates, file_name=None, is_for_static_download=False):
        url = original(self, path_or_data, mimetype, coordinates, file_name, is_for_static_download)
        if is_for_static_download:
            assert isinstance(path_or_data, bytes), "Expected bytes registered as a static download"
            by_url[url] = (mimetype, path_or_data)
        return url
    with monkeypatch.context() as patch:
        patch.setattr(MediaFileManager, "add", capture)
        run_ok(at)
    result = {}
    for button in downloads(at):
        if not button.proto.disabled:
            assert button.proto.url in by_url, f"Unable to capture download {button.proto.label}"
            mime, data = by_url[button.proto.url]
            result[mime] = data
    assert "text/csv" in result and "application/pdf" in result, f"Missing enabled exports: {list(result)}"
    return result


def pdf_text(pdf):
    assert pdf.startswith(b"%PDF-")
    proc = subprocess.run(["pdftotext", "-raw", "-", "-"], input=pdf, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True)
    return proc.stdout.decode("utf-8")


def pdf_period_values(text, drug):
    """Read values from the six *matching period blocks*, not just anywhere in the PDF."""
    headings = list(re.finditer(r"(?im)^\s*Weeks\s+(1\s*[-–]\s*2|3\s*[-–]\s*4|5\s*[-–]\s*6|7\s*[-–]\s*8|9\s*[-–]\s*10|11\s*[-–]\s*12)\s*$", text))
    assert len(headings) == 6, f"Expected six PDF period headings, found {len(headings)}"
    values = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        block = text[heading.end():end]
        row = re.search(r"(?im)^\s*" + re.escape(drug) + r"\s*:\s*([^\n\r]+)", block)
        assert row, f"No {drug} row in PDF period {index + 1}: {block[:500]!r}"
        values.append(dose_value(row.group(1)))
    return values


def markdown_links(scope):
    return [link for m in scope.markdown for link in re.findall(r"\]\((https?://[^)]*)\)", str(m.value))]


def test_default_draft_shows_authors_schedules_but_requires_review(app):
    eligible(app)
    add_medications(app, Lamotrigine=107.3, Clobazam=30)
    assert app.selectbox(key="plan_scenario").options == ["Author-defined suggestions", "Physician-customized values"]
    assert app.selectbox(key="plan_scenario").value == "Author-defined suggestions"
    assert app.selectbox(key="scb_to_discontinue").value in (None, "None selected")
    table = plan_table(app)
    assert amounts(table, "Lamotrigine") == factor_values("107.3", [1, 1, "1.15", "1.15", "1.30", "1.30"])
    assert amounts(table, "Clobazam") == factor_values("30", [1, 1, ".75", ".75", ".50", ".50"])
    assert re.search(r"author", " ".join(map(str, table["Lamotrigine"])), re.I)
    assert re.search(r"draft|unconfirmed|not (?:yet )?(?:confirmed|reviewed)", visible_text(app.tabs[3]), re.I)
    no_exports(app)
    confirm(app)


@pytest.mark.parametrize("baseline,expected", [(20, [20]*6), (30, [30, 30, 22.5, 22.5, 15, 15])])
@pytest.mark.parametrize("selected_taper", [False, True], ids=["no-taper", "selected-clobazam"])
def test_clobazam_confirmed_threshold_is_strictly_above_twenty(app, baseline, expected, selected_taper):
    eligible(app)
    add_medications(app, Clobazam=baseline)
    if selected_taper:
        select_taper(app, "Clobazam")
    assert amounts(plan_table(app), "Clobazam") == [D(str(x)) for x in expected]
    text = visible_text(app.tabs[2]) + visible_text(app.tabs[3])
    assert re.search(r"not (?:a )?(?:validated )?(?:safety )?(?:cutoff|threshold)|not (?:proof|evidence) of safety", text, re.I)


@pytest.mark.parametrize("drug,factors", [
    ("Lacosamide", [1, ".75", ".50", ".25", 0, 0]),
    ("Oxcarbazepine", [1, ".80", ".60", ".40", ".20", 0]),
    ("Eslicarbazepine acetate (ESL)", [1, ".80", ".60", ".40", ".20", 0]),
    ("Phenytoin", [1, ".75", ".50", ".25", 0, 0]),
    ("Lamotrigine", [1, ".75", ".50", ".25", 0, 0]),
    ("Zonisamide", [1, ".80", ".60", ".40", ".20", 0]),
    ("Rufinamide", [1, ".80", ".60", ".40", ".20", 0]),
])
def test_selected_scb_uses_original_baseline_fractions_without_rounding(app, drug, factors):
    eligible(app)
    add_medications(app, **{drug: 103.7})
    select_taper(app, drug)
    actual = amounts(plan_table(app), drug)
    assert actual == factor_values("103.7", factors), (drug, actual)
    if drug == "Lamotrigine":
        assert all(x <= D("103.7") for x in actual), "Selected taper must not use the increase rule"


def test_carbamazepine_taper_is_fixed_step_floored_at_zero(app):
    eligible(app)
    add_medications(app, Carbamazepine=613.7)
    select_taper(app, "Carbamazepine")
    assert amounts(plan_table(app), "Carbamazepine") == list(map(D, ["613.7", "413.7", "213.7", "13.7", "0", "0"]))


def test_manual_replaces_automatic_including_blanks_and_explicit_zero(app):
    eligible(app)
    add_medications(app, Lamotrigine=107.3, Clobazam=30, Levetiracetam=713)
    set_custom(app, ["Lamotrigine", "Levetiracetam"])
    fill_manual(app, "Lamotrigine", [107.3, None, 0, None, 81.125, None])
    fill_manual(app, "Levetiracetam", [None, 712.75, 0, None, None, 688.125])
    table = plan_table(app)
    assert amounts(table, "Lamotrigine") == [D("107.3"), None, D(0), None, D("81.125"), None]
    assert amounts(table, "Levetiracetam") == [None, D("712.75"), D(0), None, None, D("688.125")]
    assert amounts(table, "Clobazam") == list(map(D, ["30", "30", "22.5", "22.5", "15", "15"]))
    assert re.search(r"physician|manual|clinician", " ".join(map(str, table["Lamotrigine"])), re.I)
    no_exports(app)
    confirm(app)


def test_all_blank_manual_override_does_not_fall_back_to_default(app):
    eligible(app)
    add_medications(app, Clobazam=30)
    set_custom(app, ["Clobazam"])
    assert amounts(plan_table(app), "Clobazam") == [None] * 6


def test_selected_lamotrigine_taper_rejects_increasing_manual_values(app):
    eligible(app)
    add_medications(app, Lamotrigine=107.3)
    select_taper(app, "Lamotrigine")
    set_custom(app, ["Lamotrigine"])
    fill_manual(app, "Lamotrigine", [107.3, None, 108.0, None, None, None])
    assert not [e for e in app.tabs[3].dataframe if len(e.value) == 6]
    assert re.search(r"(?:cannot|must not|invalid).{0,60}increas|increas.{0,60}(?:invalid|not allowed)",
                     visible_text(app.tabs[3]), re.I | re.S)
    no_exports(app)
    app.number_input(key="manual_Lamotrigine_2").set_value(102.75)
    run_ok(app)
    assert amounts(plan_table(app), "Lamotrigine") == [D("107.3"), None, D("102.75"), None, None, None]


@pytest.mark.parametrize("baseline", [None, 0], ids=["missing-baseline", "zero-baseline"])
def test_no_automatic_values_without_positive_baseline(app, baseline):
    eligible(app)
    add_medications(app, Lamotrigine=baseline, Clobazam=baseline, Lacosamide=baseline)
    select_taper(app, "Lacosamide")
    table = plan_table(app)
    for drug in ("Lamotrigine", "Clobazam", "Lacosamide"):
        assert amounts(table, drug) == [None] * 6, f"{drug}: missing/zero baseline invented values"


def test_inducer_taper_warns_about_lamotrigine_and_serum_does_not_change_schedule(app):
    eligible(app)
    add_medications(app, Lamotrigine=107.3, Carbamazepine=613.7)
    select_taper(app, "Carbamazepine")
    before = plan_table(app).copy()
    warning_text = "\n".join(str(x.value) for kind in ("warning", "error") for x in getattr(app, kind))
    assert re.search(r"(?:inducer|washout).{0,160}lamotrigine|lamotrigine.{0,160}(?:inducer|washout)", warning_text, re.I | re.S)
    app.number_input(key="serum_Carbamazepine").set_value(14.3)
    run_ok(app)
    after = plan_table(app)
    for drug in ("Lamotrigine", "Carbamazepine"):
        assert amounts(after, drug) == amounts(before, drug), f"Serum alone changed {drug} suggestions"
    text = visible_text(app.tabs[2])
    assert re.search(r"serum", text, re.I) and re.search(r"review", text, re.I)


@pytest.mark.parametrize("key,value", [
    ("age", 17), ("age", None), ("target", 150.0), ("target", 250.0), ("target", None),
    ("renal", "Unknown / not confirmed"), ("renal", "Renal impairment"),
    ("renal", "End-stage renal disease or haemodialysis"), ("egfr", 59.0),
    ("liver", "Unknown / not confirmed"), ("liver", "Mild impairment (Child-Pugh A)"),
    ("liver", "Severe impairment (Child-Pugh C)"),
    ("short_qt", "Unknown / not confirmed"), ("short_qt", "Yes"),
])
def test_ineligible_profile_withholds_schedule_and_exports(app, key, value):
    eligible(app)
    add_medications(app, Lamotrigine=107.3)
    if key in ("age", "target", "egfr"):
        app.number_input(key=key).set_value(value)
    else:
        app.selectbox(key=key).select(value)
    run_ok(app)
    assert not [e for e in app.tabs[3].dataframe if len(e.value) == 6], f"Schedule leaked for {key}={value!r}"
    no_exports(app)
    assert app.tabs[3].error or app.tabs[3].warning, "Withholding must be explained prominently"


def test_short_qt_is_contraindicated_generalized_is_off_label_not_absolute(app):
    eligible(app)
    app.selectbox(key="epilepsy").select("Generalized onset")
    run_ok(app)
    alerts = "\n".join(str(x.value) for k in ("warning", "error") for x in getattr(app.tabs[0], k))
    assert re.search(r"generali[sz]", alerts, re.I) and re.search(r"FDA", alerts, re.I) and re.search(r"EMA", alerts, re.I)
    assert re.search(r"not.{0,35}approv|focal.{0,35}only", alerts, re.I | re.S)
    assert re.search(r"not.{0,35}(?:absolute )?contraindicat", alerts, re.I | re.S)
    assert len(plan_table(app)) == 6, "Generalized onset warning must not be confused with a contraindication"
    app.selectbox(key="short_qt").select("Yes")
    run_ok(app)
    alerts = "\n".join(str(x.value) for x in app.tabs[0].error)
    assert re.search(r"short.?qt.{0,100}contraindicat", alerts, re.I | re.S)
    assert not [e for e in app.tabs[3].dataframe if len(e.value) == 6]
    no_exports(app)


@pytest.mark.parametrize("change", ["profile", "medication", "dose", "taper", "scenario", "manual", "manual_selection"])
def test_confirmation_invalidated_on_change_even_after_reverting(app, change):
    eligible(app)
    add_medications(app, Lamotrigine=107.3, Clobazam=30)
    set_custom(app, ["Lamotrigine"])
    fill_manual(app, "Lamotrigine", [107.3, 106, None, 103, 101, 99])
    confirm(app)
    if change == "profile":
        app.number_input(key="weight").set_value(68.0)
    elif change == "medication":
        app.checkbox(key="chk_Levetiracetam").check()
    elif change == "dose":
        app.number_input(key="dose_Clobazam").set_value(31.0)
    elif change == "taper":
        app.selectbox(key="scb_to_discontinue").select("Clobazam")
    elif change == "scenario":
        app.selectbox(key="plan_scenario").select("Author-defined suggestions")
    elif change == "manual":
        app.number_input(key="manual_Lamotrigine_1").set_value(105.0)
    else:
        app.multiselect(key="plan_change_drugs").set_value(["Lamotrigine", "Clobazam"])
    run_ok(app)
    no_exports(app)
    if change == "profile":
        app.number_input(key="weight").set_value(67.0)
    elif change == "medication":
        app.checkbox(key="chk_Levetiracetam").uncheck()
    elif change == "dose":
        app.number_input(key="dose_Clobazam").set_value(30.0)
    elif change == "taper":
        app.selectbox(key="scb_to_discontinue").select("None selected")
    elif change == "scenario":
        app.selectbox(key="plan_scenario").select("Physician-customized values")
    elif change == "manual":
        app.number_input(key="manual_Lamotrigine_1").set_value(106.0)
    else:
        app.multiselect(key="plan_change_drugs").set_value(["Lamotrigine"])
    run_ok(app)
    no_exports(app)
    confirm(app)


def test_evidence_identifiers_and_url_encoding_are_exact(app):
    numbered = {}
    for expander in app.tabs[4].expander:
        match = re.match(r"\s*\[(\d+)\]", expander.label)
        if match:
            numbered[int(match.group(1))] = expander
    assert set(numbered) == set(range(1, 24))
    for number, identifier in enumerate(IDENTIFIERS, 1):
        expected = identifier if identifier.startswith("https://") else "https://doi.org/" + identifier
        links = markdown_links(numbered[number])
        assert any(unquote(x) == expected for x in links), (number, expected, links)
        for link in links:
            if unquote(link) == expected and "(" in expected:
                assert "%28" in link.lower() and "%29" in link.lower(), (number, link)
        if number <= 2:
            assert all("doi.org/" not in link.lower() for link in links)


def test_no_case_wording_monitoring_and_nonprescriptive_cautions(app):
    eligible(app)
    add_medications(app, Lamotrigine=107.3, Clobazam=30)
    text = "\n".join(visible_text(tab) for tab in app.tabs)
    assert not re.search(r"\bvignette\b|\b(?:article|manuscript)[ -]+(?:patient[ -]+)?(?:case|example)\b|\b52[ -]year[ -]old\b", text, re.I)
    assert not any(box.key == "show_case" for box in app.checkbox)
    assert re.search(r"author[- ]defined", text, re.I)
    assert re.search(r"unvalidated", text, re.I) and re.search(r"not a prescription|not (?:a )?(?:clinical )?order", text, re.I)
    for pattern in (r"monitor", r"DRESS|hypersensitivity", r"liver|hepatic", r"short.?qt", r"sedation", r"seizure", r"suicidal"):
        assert re.search(pattern, text, re.I), f"Missing monitoring/safety label: {pattern}"
    plan = visible_text(app.tabs[3])
    assert re.search(r"no\s+(?:rounding|[^.]{0,50}split)|unrounded|not.{0,30}split", plan, re.I), plan


def test_confirmed_exports_exact_values_provenance_precautions_and_links(app, monkeypatch):
    # No user data: all numbers below are deliberately synthetic. Test XML
    # escaping by injecting inert text into a selected drug's source overlay.
    import clinical_content
    original = clinical_content.apply_clinical_content
    marker = '<probe>SAFETY & REVIEW</probe>'
    def injected(db):
        original(db)
        db["Lamotrigine"]["action"] += " " + marker
    monkeypatch.setattr(clinical_content, "apply_clinical_content", injected)
    eligible(app)
    add_medications(app, Lamotrigine=107.3, Clobazam=30, Carbamazepine=613.7)
    select_taper(app, "Carbamazepine")
    # Hormonal contraception warning belongs in profile, not exports.
    app.selectbox(key="pregnancy").select("Hormonal contraception")
    run_ok(app)
    draft = plan_table(app).copy()
    no_exports(app)
    confirm(app)
    payload = captured_run(app, monkeypatch)
    csv_text = payload["text/csv"].decode("utf-8-sig")
    exported = pd.read_csv(io.StringIO(csv_text), dtype=str, keep_default_na=False)
    for drug in ("Lamotrigine", "Clobazam", "Carbamazepine"):
        assert amounts(exported, drug) == amounts(draft, drug), f"CSV changed {drug} doses"
    assert amounts(exported, "Lamotrigine") == factor_values("107.3", [1, 1, "1.15", "1.15", "1.30", "1.30"])
    assert amounts(exported, "Carbamazepine") == list(map(D, ["613.7", "413.7", "213.7", "13.7", "0", "0"]))
    text = pdf_text(payload["application/pdf"])
    for drug in ("Lamotrigine", "Clobazam", "Carbamazepine"):
        assert pdf_period_values(text, drug) == amounts(draft, drug), f"PDF changed {drug} doses or period ordering"
    for name, document in (("CSV", csv_text), ("PDF", text)):
        assert re.search(r"author[- ]defined", document, re.I), name
        assert re.search(r"unvalidated", document, re.I), name
        assert re.search(r"not a prescription|not (?:a )?(?:clinical )?order", document, re.I), name
        assert re.search(r"inducer|washout", document, re.I), name
        assert re.search(r"monitor|DRESS|hypersensitivity", document, re.I), name
        assert not CONTRACEPTION.search(document), f"Contraception warning leaked into {name}"
    assert marker in text, "PDF lost or interpreted XML-like synthetic content rather than showing it literally"
    assert marker in csv_text
    # Compare link destinations (not just visible URL text) against the
    # independent registry, and require selected medication sources in both.
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(payload["application/pdf"]))
    pdf_links = set()
    for page in reader.pages:
        for item in page.get("/Annots", []):
            annotation = item.get_object()
            action = annotation.get("/A")
            if action and action.get("/URI"):
                pdf_links.add(unquote(str(action["/URI"])))
    assert pdf_links, "Expected clickable source links in PDF"
    assert pdf_links <= EXPECTED_URLS, f"Unexpected or mangled PDF source links: {pdf_links - EXPECTED_URLS}"
    for drug in ("Lamotrigine", "Clobazam", "Carbamazepine"):
        expanders = [e for e in app.tabs[2].expander if e.label == drug]
        assert len(expanders) == 1
        drug_urls = {unquote(url) for url in markdown_links(expanders[0])}
        assert drug_urls and drug_urls <= EXPECTED_URLS
        assert drug_urls <= pdf_links, f"PDF lost sources for {drug}: {drug_urls - pdf_links}"
        for url in drug_urls:
            assert url in unquote(csv_text), f"CSV lost source for {drug}: {url}"


def test_manual_exports_preserve_blank_zero_precision_and_provenance(app, monkeypatch):
    eligible(app)
    # A missing baseline must not prevent an explicitly entered manual value,
    # nor silently cause author values to be substituted into blank periods.
    add_medications(app, Lamotrigine=107.3, Levetiracetam=None)
    set_custom(app, ["Lamotrigine", "Levetiracetam"])
    fill_manual(app, "Lamotrigine", [107.3, None, 0, None, 81.125, None])
    fill_manual(app, "Levetiracetam", [None, 712.75, 0, None, None, 688.125])
    draft = plan_table(app).copy()
    no_exports(app)
    confirm(app)
    payload = captured_run(app, monkeypatch)
    csv_text = payload["text/csv"].decode("utf-8-sig")
    exported = pd.read_csv(io.StringIO(csv_text), dtype=str, keep_default_na=False)
    text = pdf_text(payload["application/pdf"])
    expected = {
        "Lamotrigine": [D("107.3"), None, D("0"), None, D("81.125"), None],
        "Levetiracetam": [None, D("712.75"), D("0"), None, None, D("688.125")],
    }
    for drug, values in expected.items():
        assert amounts(draft, drug) == values
        assert amounts(exported, drug) == values, f"CSV lost missing/zero/precision for {drug}"
        assert pdf_period_values(text, drug) == values, f"PDF lost missing/zero/precision for {drug}"
        source_cols = [c for c in exported.columns if c.startswith(drug) and re.search(r"source|provenance", c, re.I)]
        assert source_cols, f"CSV lacks a source/provenance column for {drug}"
        assert any(re.search(r"(?:physician|clinician)[- ]entered", str(value), re.I)
                   for column in source_cols for value in exported[column]), f"CSV mislabels manual values for {drug}"
        assert re.search(re.escape(drug) + r".{0,100}(?:physician|clinician)[- ]entered", text, re.I | re.S), ("PDF", drug)
    for name, document in (("CSV", csv_text), ("PDF", text)):
        assert re.search(r"baseline.{0,80}(?:missing|zero|not entered)", document, re.I | re.S), name
        assert re.search(r"not a prescription|not (?:a )?(?:clinical )?order", document, re.I), name
        assert re.search(r"unrounded|no rounding", document, re.I), name
    assert not CONTRACEPTION.search(csv_text)
    assert not CONTRACEPTION.search(text)


def test_spreadsheet_formula_escaping_for_untrusted_text():
    """Current UI has no arbitrary free-text field; test the app's real sanitizer.

    Extract only this pure helper from the app AST, avoiding executing the UI or
    modifying source files. Serialize/parse CSV to check escaping survives CSV.
    """
    tree = ast.parse(APP.read_text(encoding="utf-8"), filename=str(APP))
    found = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_csv_safe"]
    assert len(found) == 1, "Expected an explicit CSV formula-injection sanitizer"
    module = ast.Module(body=found, type_ignores=[])
    ns = {}
    exec(compile(module, str(APP), "exec"), ns)
    sanitize = ns["_csv_safe"]
    for raw in ('=2+3', '+2+3', '-2+3', '@SUM(1,2)', '   =2+3', '\t=2+3', '\r=2+3'):
        safe = sanitize(raw)
        assert safe.startswith("'"), (raw, safe)
        buf = io.StringIO(newline="")
        csv.writer(buf).writerow([safe])
        assert next(csv.reader(io.StringIO(buf.getvalue())))[0] == safe
    assert sanitize("synthetic ordinary text") == "synthetic ordinary text"


def test_scenario_toggle_replaces_manual_values_with_default_and_invalidates_review(app):
    eligible(app)
    add_medications(app, Lamotrigine=80)
    set_custom(app, ['Lamotrigine'])
    fill_manual(app, 'Lamotrigine', [80, 80, 82, 82, 84, 84])
    assert amounts(plan_table(app), 'Lamotrigine') == list(map(D, ['80', '80', '82', '82', '84', '84']))
    confirm(app)
    app.selectbox(key='plan_scenario').select('Author-defined suggestions')
    run_ok(app)
    assert amounts(plan_table(app), 'Lamotrigine') == list(map(D, ['80', '80', '92', '92', '104', '104']))
    assert not [w for w in app.number_input if str(w.key).startswith('manual_Lamotrigine_')]
    no_exports(app)
    app.selectbox(key='plan_scenario').select('Physician-customized values')
    run_ok(app)
    no_exports(app)  # returning to an earlier scenario cannot resurrect confirmation

"""Behavioral regression tests, NOT clinical validation or medical advice.

Run from this directory: python -m pytest -q test_integration.py
By default test xcopri_app.py; if absent test xcopri_app_logic.py and skip the
three final-only integration checks. Set XCOPRI_APP_UNDER_TEST to a path to
explicitly test another copy. All profiles and export contents are synthetic.
The AppTest assertions intentionally exercise the widget keys and non-order
workflow in the current integration contract.
"""
from __future__ import annotations

import ast
import csv
import io
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import unquote

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
FINAL = HERE / 'xcopri_app.py'
PROTOTYPE = HERE / 'xcopri_app_logic.py'
APP = Path(os.environ.get('XCOPRI_APP_UNDER_TEST', str(FINAL if FINAL.exists() else PROTOTYPE))).resolve()
USING_PROTOTYPE = APP == PROTOTYPE.resolve()
WEEKS = ['Weeks 1-2', 'Weeks 3-4', 'Weeks 5-6', 'Weeks 7-8', 'Weeks 9-10', 'Weeks 11-12']
CNB = [12.5, 25, 50, 100, 150, 200]


def pytest_report_header(config):
    return f'app under test: {APP}' + (' (prototype fallback; integrated registry checks skipped)' if USING_PROTOTYPE else '')


@pytest.fixture(scope='session')
def app_code():
    """Load definitions/data before Streamlit page rendering, without patient state.

    This keeps unit checks against the ACTUAL selected app, not a second copy of
    its implementation. The current script creates its page at set_page_config.
    """
    assert APP.is_file(), f'Application not found: {APP}'
    tree = ast.parse(APP.read_text(encoding='utf-8'), filename=str(APP))
    cutoff = next((i for i, node in enumerate(tree.body)
                   if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                   and isinstance(node.value.func, ast.Attribute)
                   and node.value.func.attr == 'set_page_config'), None)
    assert cutoff is not None, 'Test harness expects st.set_page_config at top level'
    prefix = ast.Module(body=tree.body[:cutoff], type_ignores=[])
    namespace = {'__name__': '_app_test_definitions_', '__file__': str(APP)}
    exec(compile(prefix, str(APP), 'exec'), namespace)
    return namespace


def run_ok(at):
    at.run(timeout=30)
    assert not at.exception, '\n'.join(str(x.value) for x in at.exception)
    return at


def text(at):
    return '\n'.join(str(x.value) for typ in ('markdown', 'warning', 'error', 'info', 'success', 'caption', 'text')
                     for x in getattr(at, typ))


def has(at, phrase):
    return phrase.casefold() in text(at).casefold()


def accepted():
    at = run_ok(AppTest.from_file(str(APP), default_timeout=30))
    assert at.button[0].disabled
    at.checkbox(key='disclaimer_checkbox').check()
    run_ok(at)
    assert not at.button[0].disabled
    at.button[0].click()
    run_ok(at)
    return at


@pytest.fixture
def app():
    return accepted()


def in_scope(at, *, show=True):
    at.number_input(key='age').set_value(52)
    at.number_input(key='target').set_value(200.0)
    at.selectbox(key='renal').select('Normal - clinician confirmed')
    at.selectbox(key='liver').select('Normal - clinician confirmed')
    at.selectbox(key='short_qt').select('No - clinician confirmed')
    if show:
        at.checkbox(key='show_reference').check()
    return run_ok(at)


def add_drug(at, name, dose=None, serum=None):
    at.checkbox(key=f'chk_{name}').check()
    run_ok(at)
    if dose is not None:
        at.number_input(key=f'dose_{name}').set_value(float(dose))
    if serum is not None:
        at.number_input(key=f'serum_{name}').set_value(float(serum))
    return run_ok(at)


def review_table(at):
    assert at.dataframe, 'Expected the generic review table, not a treatment order'
    return at.dataframe[0].value


def unspecified_co_medication(value):
    """Both versions explicitly decline to calculate a co-medication dose."""
    return str(value) in {
        'No co-ASM change selected',
        'Not specified - no automatic co-medication dose calculated',
    }


def test_disclaimer_gate_and_acceptance():
    at = AppTest.from_file(str(APP), default_timeout=30)
    run_ok(at)
    assert has(at, 'unvalidated') and at.button[0].disabled
    assert len(at.tabs) == 0
    at.checkbox(key='disclaimer_checkbox').check()
    run_ok(at)
    at.button[0].click()
    run_ok(at)
    assert len(at.tabs) == 5
    assert at.session_state['disclaimer_accepted'] is True
    assert has(at, 'not a prescription')


def test_empty_profile_and_missing_medication_dose_never_create_automatic_dose(app):
    app.checkbox(key='show_reference').check()
    run_ok(app)
    assert has(app, 'no schedule')
    assert len(app.dataframe) == 0
    assert not app.get('download_button')
    add_drug(app, 'Lamotrigine')
    assert has(app, 'dose not entered')
    in_scope(app)
    table = review_table(app)
    assert all(unspecified_co_medication(v) for v in table['Lamotrigine'])
    assert all(not any(n in str(v) for n in ('575', '650')) for v in table['Lamotrigine'])


def test_one_versus_two_preexisting_scbs(app):
    add_drug(app, 'Lacosamide', 300)
    assert has(app, 'One pre-cenobamate SCB detected')
    assert not has(app, 'Two or more pre-cenobamate SCBs detected')
    add_drug(app, 'Lamotrigine', 500)
    assert has(app, 'Two or more pre-cenobamate SCBs detected')
    assert has(app, 'does not mandate stopping')
    assert app.selectbox(key='scb_to_discontinue').value == 'None selected'
    assert not app.dataframe  # no automatic plan, either before or after detection


@pytest.mark.parametrize('dose,triggered', [(399, False), (400, True), (450, True)])
def test_lacosamide_boundary_independent_of_two_scb_rule(app, dose, triggered):
    add_drug(app, 'Lacosamide', dose)
    assert has(app, 'One pre-cenobamate SCB detected')
    assert has(app, 'Lacosamide ≥400 mg/day') is triggered
    assert not has(app, 'Two or more pre-cenobamate SCBs detected')
    if triggered:
        assert has(app, 'does not mandate discontinuation')


@pytest.mark.parametrize('dose,proactive', [(10, False), (20, False), (20.1, True), (40, True)])
def test_clobazam_twenty_boundary_is_unvalidated_review_prompt(app, dose, proactive):
    add_drug(app, 'Clobazam', dose)
    if proactive:
        assert has(app, 'Clobazam >20 mg/day')
        assert has(app, 'not a validated cutoff')
    else:
        assert has(app, 'Clobazam ≤20 mg/day')
        assert has(app, 'not proof of safety')
        assert has(app, '5–10 mg/day reduction')
    assert not app.dataframe


def test_serum_input_does_not_accelerate_or_change_schedule(app):
    in_scope(app)
    add_drug(app, 'Phenytoin', 300)
    before = review_table(app).copy(deep=True)
    app.number_input(key='serum_Phenytoin').set_value(30.0)
    run_ok(app)
    after = review_table(app)
    pd.testing.assert_frame_equal(before, after)
    assert has(app, 'clinical review only')
    assert has(app, 'No automatic dose change or accelerated taper')


def test_no_automatic_lamotrigine_increase_or_lacosamide_taper(app):
    in_scope(app)
    add_drug(app, 'Lacosamide', 400)
    add_drug(app, 'Lamotrigine', 500)
    app.selectbox(key='scb_to_discontinue').select('Lacosamide')
    run_ok(app)
    assert has(app, 'does not create doses')
    assert has(app, 'fixed increase is not assumed')
    df = review_table(app)
    for drug in ('Lacosamide', 'Lamotrigine'):
        assert len(df[drug]) == 6 and all(unspecified_co_medication(v) for v in df[drug])


@pytest.mark.parametrize('key,value,warning', [
    ('age', 17, 'Pediatric'),
    ('target', 250.0, 'Above 200'),
    ('target', 150.0, 'lower or different target'),
    ('liver', 'Mild impairment (Child-Pugh A)', 'Mild or moderate hepatic impairment'),
    ('liver', 'Moderate impairment (Child-Pugh B)', 'Mild or moderate hepatic impairment'),
    ('liver', 'Severe impairment (Child-Pugh C)', 'Severe hepatic impairment'),
    ('renal', 'Renal impairment', 'Renal impairment'),
    ('renal', 'End-stage renal disease or haemodialysis', 'end-stage renal disease'),
    ('egfr', 59.0, 'Renal impairment'),
    ('short_qt', 'Yes', 'contraindications'),
    ('short_qt', 'Unknown / not confirmed', 'No schedule displayed'),
])
def test_scope_and_impaired_organ_or_contraindication_block_reference(app, key, value, warning):
    in_scope(app)
    assert len(app.dataframe) == 1
    if key in ('age', 'target', 'egfr'):
        app.number_input(key=key).set_value(value)
    else:
        app.selectbox(key=key).select(value)
    run_ok(app)
    assert has(app, warning)
    assert has(app, 'No schedule displayed')
    assert not app.dataframe
    assert not app.get('download_button')


def test_liver_and_renal_warnings_distinguish_regulatory_positions(app):
    app.selectbox(key='liver').select('Severe impairment (Child-Pugh C)')
    app.selectbox(key='renal').select('End-stage renal disease or haemodialysis')
    run_ok(app)
    assert has(app, 'FDA use is not recommended')
    assert has(app, 'Neither lists severe hepatic impairment as a formal contraindication')
    assert has(app, 'FDA: not recommended') and has(app, 'EMA: should not be used')


@pytest.mark.parametrize('selection,phrase', [
    ('Pregnant', 'Pregnancy/lactation'),
    ('Breastfeeding', 'Pregnancy/lactation'),
    ('Hormonal contraception', 'additional or alternative non-hormonal contraception'),
])
def test_pregnancy_lactation_and_hormonal_contraception_warning(app, selection, phrase):
    app.selectbox(key='pregnancy').select(selection)
    run_ok(app)
    assert has(app, phrase)
    if selection == 'Hormonal contraception':
        assert has(app, 'may reduce hormonal oral contraceptive effectiveness')
    else:
        assert has(app, 'does not establish safety')


def test_dress_and_short_qt_warnings_and_discontinuation_context(app):
    assert has(app, 'DRESS can be fatal')
    assert has(app, 'Fever or lymphadenopathy can occur without rash')
    assert has(app, 'immediate discontinuation')
    assert has(app, 'Slow titration does not eliminate risk')
    assert has(app, 'Familial short-QT syndrome') and has(app, 'contraindications')
    app.selectbox(key='short_qt').select('Yes')
    app.checkbox(key='show_reference').check()
    run_ok(app)
    assert has(app, 'contraindications; no schedule is generated')
    assert not app.dataframe


def test_fixed_manuscript_example_is_exact_separate_and_unvalidated(app):
    assert len(app.dataframe) == 0
    app.checkbox(key='show_case').check()
    run_ok(app)
    assert has(app, 'ILLUSTRATIVE ONLY') and has(app, 'NOT A PRESCRIPTION')
    assert has(app, 'not the active patient plan')
    assert len(app.dataframe) == 1
    df = app.dataframe[0].value
    assert list(df['Period']) == WEEKS
    assert list(df['Cenobamate (mg/day)']) == CNB
    assert list(df['Clobazam (mg/day)']) == [20] * 6
    assert list(df['Lacosamide (mg/day)']) == [400, 300, 200, 100, 0, 0]
    assert list(df['Lamotrigine (mg/day)']) == [500, 500, 575, 575, 650, 650]
    assert not app.get('download_button')
    # A changed active profile must not change the fixed case.
    app.number_input(key='age').set_value(27)
    run_ok(app)
    pd.testing.assert_frame_equal(df, app.dataframe[0].value)


@pytest.mark.parametrize('target,sizes,splittable,confirmed,expected', [
    (0, [50], False, False, '0 mg'),
    (24, [50], False, False, 'REVIEW'),
    (24, [50], True, True, 'REVIEW'),
    (25, [50], True, False, 'REVIEW'),
    (25, [50], False, True, 'REVIEW'),
    (25, [50], True, True, '25 mg'),
    (125, [50, 75], False, False, '125 mg'),
    (-1, [50], False, False, 'REVIEW'),
    (1, [], False, False, 'REVIEW'),
])
def test_tablet_below_smallest_and_split_controls(app_code, target, sizes, splittable, confirmed, expected):
    result = app_code['floor_tablet'](target, sizes, splittable, local_split_confirmed=confirmed)
    assert result.startswith(expected), result
    if expected == 'REVIEW':
        assert 'not executable' in result


def test_manual_dose_confirmation_invalidates_on_profile_and_value_change(app):
    in_scope(app)
    add_drug(app, 'Lamotrigine', 500)
    app.selectbox(key='plan_scenario').select('Clinician-entered values for review')
    app.multiselect(key='plan_change_drugs').set_value(['Lamotrigine'])
    run_ok(app)
    app.number_input(key='manual_Lamotrigine_0').set_value(450.0)
    run_ok(app)
    assert has(app, 'not included in the review table until explicitly confirmed')
    assert '450' not in str(review_table(app)['Lamotrigine'][0])
    app.button(key='confirm_manual_review').click()
    run_ok(app)
    assert has(app, 'remain unvalidated and non-executable')
    assert 'Clinician-entered: 450 mg/day; review only' in str(review_table(app)['Lamotrigine'][0])
    assert 'Not specified' in str(review_table(app)['Lamotrigine'][1])  # blank != hold or zero
    app.number_input(key='weight').set_value(78.0)
    run_ok(app)
    assert has(app, 'not included in the review table until explicitly confirmed')
    assert '450' not in str(review_table(app)['Lamotrigine'][0])
    app.button(key='confirm_manual_review').click()
    run_ok(app)
    assert '450' in str(review_table(app)['Lamotrigine'][0])
    app.number_input(key='manual_Lamotrigine_0').set_value(0.0)
    run_ok(app)
    assert has(app, 'not included in the review table until explicitly confirmed')
    assert 'Clinician-entered' not in str(review_table(app)['Lamotrigine'][0])
    app.button(key='confirm_manual_review').click()
    run_ok(app)
    assert 'Clinician-entered: 0 mg/day' in str(review_table(app)['Lamotrigine'][0])


def test_confirmation_does_not_resurrect_when_profile_reverts(app):
    """A changed profile invalidates review even if later reverted to its old value."""
    in_scope(app)
    add_drug(app, 'Lamotrigine', 500)
    app.selectbox(key='plan_scenario').select('Clinician-entered values for review')
    app.multiselect(key='plan_change_drugs').set_value(['Lamotrigine'])
    run_ok(app)
    app.number_input(key='manual_Lamotrigine_0').set_value(450.0)
    run_ok(app)
    app.button(key='confirm_manual_review').click()
    run_ok(app)
    assert 'Clinician-entered: 450' in str(review_table(app)['Lamotrigine'][0])
    app.number_input(key='age').set_value(53)
    run_ok(app)
    assert unspecified_co_medication(review_table(app)['Lamotrigine'][0])
    app.number_input(key='age').set_value(52)
    run_ok(app)
    assert unspecified_co_medication(review_table(app)['Lamotrigine'][0]), (
        'A past confirmation must not silently reactivate after a profile change is reverted.'
    )


def test_removing_drug_invalidates_confirmed_value_and_taper_choice(app):
    in_scope(app)
    add_drug(app, 'Lamotrigine', 500)
    app.selectbox(key='scb_to_discontinue').select('Lamotrigine')
    app.selectbox(key='plan_scenario').select('Clinician-entered values for review')
    app.multiselect(key='plan_change_drugs').set_value(['Lamotrigine'])
    run_ok(app)
    app.number_input(key='manual_Lamotrigine_0').set_value(450.0)
    run_ok(app)
    app.button(key='confirm_manual_review').click()
    run_ok(app)
    app.checkbox(key='chk_Lamotrigine').uncheck()
    run_ok(app)
    assert app.selectbox(key='scb_to_discontinue').value == 'None selected'
    assert app.multiselect(key='plan_change_drugs').value == []
    assert 'Lamotrigine' not in review_table(app).columns


def test_export_csv_and_pdf_are_generated_with_safe_status_and_synthetic_data(monkeypatch, tmp_path):
    # Capture exact payloads passed to Streamlit's in-memory download store.
    from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage
    captured = []
    original = MemoryMediaFileStorage.load_and_get_id
    def capture(self, data, mimetype, kind, filename=None):
        if isinstance(data, bytes) and filename in ('cenobamate_review.csv', 'cenobamate_review.pdf'):
            captured.append((filename, mimetype, data))
        return original(self, data, mimetype, kind, filename)
    monkeypatch.setattr(MemoryMediaFileStorage, 'load_and_get_id', capture)
    app = accepted()
    in_scope(app)
    add_drug(app, 'Lamotrigine', 500)
    assert len(app.get('download_button')) == 2
    files = {name: (mime, data) for name, mime, data in captured}
    assert set(files) == {'cenobamate_review.csv', 'cenobamate_review.pdf'}
    csv_mime, csv_data = files['cenobamate_review.csv']
    assert csv_mime == 'text/csv'
    rows = list(csv.DictReader(io.StringIO(csv_data.decode('utf-8-sig'))))
    assert len(rows) == 6
    assert [r['Week'] for r in rows] == WEEKS
    assert all('UNVALIDATED' in r['Status'] and 'NOT A PRESCRIPTION' in r['Status'] for r in rows)
    assert all(unspecified_co_medication(r['Lamotrigine']) for r in rows)
    assert all('DRESS' in r['Safety review'] for r in rows)
    pdf_mime, pdf_data = files['cenobamate_review.pdf']
    assert pdf_mime == 'application/pdf' and pdf_data.startswith(b'%PDF-')
    p = tmp_path / 'synthetic.pdf'
    p.write_bytes(pdf_data)
    extracted = subprocess.run(['pdftotext', str(p), '-'], capture_output=True, text=True, check=True).stdout
    assert 'UNVALIDATED' in extracted and 'NOT A PRESCRIPTION' in extracted
    assert 'DRESS' in extracted and 'Lamotrigine' in extracted


def test_csv_formula_escaping_and_pdf_xml_escaping(app_code):
    for raw in ('=1+1', '+1', '-1', '@cmd', '\t=1', '  =1'):
        assert app_code['_csv_safe'](raw).startswith("'")
    assert app_code['_pdf_text']('<script>&"') == '&lt;script&gt;&amp;&quot;'


@pytest.mark.skipif(USING_PROTOTYPE, reason='final app not created yet; prototype still has old registry')
def test_final_app_imports_corrected_23_references(app_code):
    import references_data
    assert len(app_code['REFERENCES']) == len(app_code['PAPER_LIST']) == 23
    assert app_code['REFERENCES'] == references_data.REFERENCES
    assert app_code['PAPER_LIST'] == references_data.PAPER_LIST
    assert len({row[4].casefold() for row in app_code['PAPER_LIST']}) == 23
    assert '10.1111/cts.13204' in app_code['REFERENCES']['Greene2022']
    assert '10.1212/wnl.0000000000009530' in app_code['REFERENCES']['Chung2020']


@pytest.mark.skipif(USING_PROTOTYPE, reason='final app not created yet; prototype still has old registry')
def test_final_app_applies_full_clinical_content_overlay(app_code):
    import clinical_content
    db = app_code['DRUG_DB']
    for name, changes in clinical_content._UPDATES.items():
        assert name in db, name
        for field, expected in changes.items():
            if field in db[name]:
                assert db[name][field] == expected, f'{name}.{field} did not use corrected clinical content'
    assert db['Lamotrigine']['pct_per_period'] == [0] * 6
    assert db['Everolimus']['has_serum'] is False


@pytest.mark.skipif(USING_PROTOTYPE, reason='final app not created yet; prototype still has old registry')
def test_reference_ui_has_23_entries_and_correct_doi_and_regulatory_links(app, app_code):
    links = [e.value for e in app.tabs[4].markdown
             if e.value.startswith(('[DOI](https://doi.org/', '[regulatory document (not DOI)](https://'))]
    assert len(links) == 23
    for _, _, _, _, address, _, _ in app_code['PAPER_LIST']:
        expected = address if address.startswith('http') else 'https://doi.org/' + address
        assert any(f']({expected})' in unquote(link) for link in links), expected
        if address.startswith('http'):
            assert not any('https://doi.org/' + address in link for link in links)
    assert sum('[regulatory document (not DOI)]' in item for item in links) == 2
    assert sum('[DOI]' in item for item in links) == 21


def test_pdf_bundled_unicode_fonts_work_without_linux_system_fonts(app_code, monkeypatch, tmp_path):
    """A deployed Windows/macOS server may lack /usr/share/fonts entirely."""
    real_isfile = os.path.isfile
    def hide_linux_font(path):
        path_str = os.fspath(path)
        if path_str.startswith('/usr/share/fonts/truetype/dejavu/'):
            return False
        return real_isfile(path)
    monkeypatch.setattr(os.path, 'isfile', hide_linux_font)
    df = pd.DataFrame({'Week': ['Weeks 1-2'], 'Xcopri (Cenobamate)': ['12.5 mg/day']})
    data = app_code['make_pdf']((), (('Clobazam', 20, None),), df.to_json())
    pdf = tmp_path / 'unicode.pdf'
    pdf.write_bytes(data)
    extracted = subprocess.run(['pdftotext', str(pdf), '-'], capture_output=True, text=True, check=True).stdout
    assert '10–20' in extracted  # an en dash in a medication dosing interval survives
    assert 'Clobazam' in extracted


def test_pdf_fails_closed_if_all_unicode_fonts_are_missing(app_code, monkeypatch):
    """Never silently substitute a font that might corrupt medical symbols."""
    real_isfile = os.path.isfile
    def hide_dejavu(path):
        if os.fspath(path).endswith(('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf')):
            return False
        return real_isfile(path)
    monkeypatch.setattr(os.path, 'isfile', hide_dejavu)
    df = pd.DataFrame({'Week': ['Weeks 1-2'], 'Xcopri (Cenobamate)': ['12.5 mg/day']})
    with pytest.raises(RuntimeError, match='PDF export requires the bundled fonts'):
        app_code['make_pdf']((), (), df.to_json())

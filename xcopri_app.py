"""Unvalidated cenobamate interaction-review prototype; not a prescription.

Clinical decisions require independent review of current applicable labels and
local formulations. No co-medication dose changes are calculated automatically.
Run with: streamlit run xcopri_app.py
"""

import io
import os
import re
import streamlit as st
import pandas as pd
from datetime import date
from urllib.parse import quote
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from references_data import REFERENCES, PAPER_LIST
from clinical_content import apply_clinical_content

APP_VERSION = "1.1"
APP_LAST_UPDATED = "November 2026"

# This is the input schema only, not a legacy clinical-information registry.
# All narrative, risks and evidence references come from the reviewed overlay.
DRUG_DB = {'Clobazam': {'unit': 'mg',
              'has_serum': False,
              'risk': '',
              'action': '',
              'mechanism': '',
              'recommendation': '',
              'references': [],
              'two_way': None,
              'pct_per_period': [None, None, None, None, None, None],
              'serum_toxic_high': None,
              'dose_adjustment_threshold': None},
 'Phenytoin': {'unit': 'mg',
               'has_serum': True,
               'risk': '',
               'action': '',
               'mechanism': '',
               'recommendation': '',
               'references': [],
               'two_way': None,
               'pct_per_period': [None, None, None, None, None, None],
               'serum_toxic_high': None},
 'Phenobarbital': {'unit': 'mg',
                   'has_serum': True,
                   'risk': '',
                   'action': '',
                   'mechanism': '',
                   'recommendation': '',
                   'references': [],
                   'two_way': None,
                   'pct_per_period': [None, None, None, None, None, None],
                   'serum_toxic_high': None},
 'Lamotrigine': {'unit': 'mg',
                 'has_serum': False,
                 'risk': '',
                 'action': '',
                 'mechanism': '',
                 'recommendation': '',
                 'references': [],
                 'two_way': None,
                 'pct_per_period': [None, None, None, None, None, None],
                 'serum_toxic_high': None},
 'Carbamazepine': {'unit': 'mg',
                   'has_serum': True,
                   'risk': '',
                   'action': '',
                   'mechanism': '',
                   'recommendation': '',
                   'references': [],
                   'two_way': None,
                   'pct_per_period': [None, None, None, None, None, None],
                   'serum_toxic_high': None},
 'Valproate (VPA)': {'unit': 'mg',
                     'has_serum': True,
                     'risk': '',
                     'action': '',
                     'mechanism': '',
                     'recommendation': '',
                     'references': [],
                     'two_way': None,
                     'pct_per_period': [None, None, None, None, None, None],
                     'serum_toxic_high': None},
 'Lacosamide': {'unit': 'mg',
                'has_serum': False,
                'risk': '',
                'action': '',
                'mechanism': '',
                'recommendation': '',
                'references': [],
                'two_way': None,
                'pct_per_period': [None, None, None, None, None, None],
                'serum_toxic_high': None},
 'Levetiracetam': {'unit': 'mg',
                   'has_serum': False,
                   'risk': '',
                   'action': '',
                   'mechanism': '',
                   'recommendation': '',
                   'references': [],
                   'two_way': None,
                   'pct_per_period': [None, None, None, None, None, None],
                   'serum_toxic_high': None},
 'Oxcarbazepine': {'unit': 'mg',
                   'has_serum': True,
                   'risk': '',
                   'action': '',
                   'mechanism': '',
                   'recommendation': '',
                   'references': [],
                   'two_way': None,
                   'pct_per_period': [None, None, None, None, None, None],
                   'serum_toxic_high': None},
 'Perampanel': {'unit': 'mg',
                'has_serum': False,
                'risk': '',
                'action': '',
                'mechanism': '',
                'recommendation': '',
                'references': [],
                'two_way': None,
                'pct_per_period': [None, None, None, None, None, None],
                'serum_toxic_high': None},
 'Cannabidiol (CBD)': {'unit': 'mg',
                       'has_serum': False,
                       'risk': '',
                       'action': '',
                       'mechanism': '',
                       'recommendation': '',
                       'references': [],
                       'two_way': None,
                       'pct_per_period': [None, None, None, None, None, None],
                       'serum_toxic_high': None},
 'Hormonal Contraceptives': {'unit': '',
                             'has_serum': False,
                             'risk': '',
                             'action': '',
                             'mechanism': '',
                             'recommendation': '',
                             'references': [],
                             'two_way': None,
                             'pct_per_period': [None, None, None, None, None, None],
                             'serum_toxic_high': None,
                             'conditional_on_pregnancy': True},
 'Primidone': {'unit': 'mg',
               'has_serum': True,
               'risk': '',
               'action': '',
               'mechanism': '',
               'recommendation': '',
               'references': [],
               'two_way': None,
               'pct_per_period': [None, None, None, None, None, None],
               'serum_toxic_high': None},
 'Eslicarbazepine acetate (ESL)': {'unit': 'mg',
                                   'has_serum': True,
                                   'risk': '',
                                   'action': '',
                                   'mechanism': '',
                                   'recommendation': '',
                                   'references': [],
                                   'two_way': None,
                                   'pct_per_period': [None, None, None, None, None, None],
                                   'serum_toxic_high': None},
 'Felbamate': {'unit': 'mg',
               'has_serum': True,
               'risk': '',
               'action': '',
               'mechanism': '',
               'recommendation': '',
               'references': [],
               'two_way': None,
               'pct_per_period': [None, None, None, None, None, None],
               'serum_toxic_high': None},
 'Zonisamide': {'unit': 'mg',
                'has_serum': False,
                'risk': '',
                'action': '',
                'mechanism': '',
                'recommendation': '',
                'references': [],
                'two_way': None,
                'pct_per_period': [None, None, None, None, None, None],
                'serum_toxic_high': None},
 'Rufinamide': {'unit': 'mg',
                'has_serum': False,
                'risk': '',
                'action': '',
                'mechanism': '',
                'recommendation': '',
                'references': [],
                'two_way': None,
                'pct_per_period': [None, None, None, None, None, None],
                'serum_toxic_high': None},
 'Everolimus': {'unit': 'mg',
                'has_serum': True,
                'risk': '',
                'action': '',
                'mechanism': '',
                'recommendation': '',
                'references': [],
                'two_way': None,
                'pct_per_period': [None, None, None, None, None, None],
                'serum_toxic_high': None}}
apply_clinical_content(DRUG_DB)

# Unvalidated decision support; overlay content is for clinician review only.
import hashlib
import json
from decimal import Decimal, InvalidOperation
from xml.sax.saxutils import escape as xml_escape

XCOP_SCHEDULE = [12.5, 25, 50, 100, 150, 200]
WEEK_LABELS = ['Weeks 1-2', 'Weeks 3-4', 'Weeks 5-6', 'Weeks 7-8', 'Weeks 9-10', 'Weeks 11-12']
FDA_LABEL = 'https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/212839s013lbl.pdf'
EMA_LABEL = 'https://www.ema.europa.eu/en/documents/product-information/ontozry-epar-product-information_en.pdf'
DISCLAIMER = ('UNVALIDATED DECISION SUPPORT - NOT A PRESCRIPTION OR CLINICAL ORDER. '
              'All decisions and formulation checks belong to the treating clinician.')
SAFETY_FLAGS = [
    {'title': 'Serious hypersensitivity / DRESS', 'body': (
        'DRESS can be fatal. Fever or lymphadenopathy can occur without rash. Evaluate immediately. '
        'FDA patient counselling directs immediate discontinuation if serious hypersensitivity is suspected; '
        'FDA section 5.1 directs immediate discontinuation and no restart if no alternative etiology is established. '
        'EMA directs immediate withdrawal for signs or symptoms suggestive of DRESS. Slow titration does not eliminate risk.'),
     'refs': ['FDA2019', 'EMA2021']},
    {'title': 'Liver injury, including liver failure', 'body': (
        'Acute liver failure requiring transplantation has been reported. FDA: obtain ALT, AST and total bilirubin '
        'before initiation if not available within 3 months; monitor for symptoms and test promptly if injury is suspected. '
        'Interrupt or discontinue for liver injury without alternative etiology. EMA also specifies baseline GGT and alkaline '
        'phosphatase, monitoring during treatment, and considering reduction or discontinuation for suspected or detected injury. '
        'Additional scheduled testing is a local policy, not a fixed FDA titration schedule.'), 'refs': ['FDA2019', 'EMA2021']},
    {'title': 'QT shortening', 'body': (
        'Familial short-QT syndrome and hypersensitivity to cenobamate or ingredients are contraindications. '
        'Use caution with other QT-shortening drugs; review cardiac history and seek specialist input as indicated.'),
     'refs': ['FDA2019', 'EMA2021']},
    {'title': 'Contraception and other medicines', 'body': (
        'Hormonal oral contraceptive efficacy may be reduced; FDA advises additional or alternative non-hormonal '
        'contraception. Consult a pharmacist or clinical pharmacologist about all other medicines. Everolimus is one '
        'selectable non-ASM example, not comprehensive non-ASM interaction coverage.'), 'refs': ['FDA2019', 'EMA2021']},
    {'title': 'Scope and clinical monitoring', 'body': (
        'Prototype scope: adults with clinician-confirmed normal hepatic and renal function, cenobamate <=200 mg/day. '
        'Monitor sedation, dizziness, gait, falls, suicidality and seizure changes. Abrupt ASM withdrawal can cause seizures '
        'unless a serious safety concern requires it. Higher doses and pediatric use are outside the tool calculation scope, '
        'not necessarily outside approved or specialist practice.'), 'refs': ['FDA2019', 'EMA2021']},
]
SCB_DRUGS = {'Lacosamide': 'Sodium-channel blocker', 'Carbamazepine': 'Sodium-channel blocker; inducer',
 'Oxcarbazepine': 'Sodium-channel blocker; inducer', 'Eslicarbazepine acetate (ESL)': 'Sodium-channel blocker',
 'Phenytoin': 'Sodium-channel blocker; inducer', 'Lamotrigine': 'Sodium-channel blocker',
 'Zonisamide': 'Sodium-channel blocker', 'Rufinamide': 'Sodium-channel blocker; also shortens QT'}
TAPER_SCHEDULE = {}  # Deliberately no automatic patient-specific taper.
CASCADE_DDI = {'Carbamazepine': ['Lamotrigine', 'Perampanel', 'Everolimus'],
 'Oxcarbazepine': ['Lamotrigine', 'Perampanel', 'Everolimus'],
 'Eslicarbazepine acetate (ESL)': ['Lamotrigine', 'Perampanel'],
 'Phenytoin': ['Lamotrigine', 'Perampanel', 'Everolimus'],
 'Phenobarbital': ['Lamotrigine', 'Perampanel', 'Everolimus'],
 'Primidone': ['Lamotrigine', 'Perampanel'], 'Felbamate': ['Lamotrigine', 'Perampanel']}


def get_cascade_warnings(taper_drug: str, selected_drugs: dict) -> list:
    if not taper_drug or taper_drug not in selected_drugs:
        return []
    return [{'drug': drug, 'change': 'Concentration may rise during inducer washout; direction and magnitude vary.',
             'action': 'Clinician/pharmacist review symptoms, seizures, other interactions and relevant concentrations; individualize any action.'}
            for drug in CASCADE_DDI.get(taper_drug, []) if drug in selected_drugs and drug != taper_drug]


def get_active_scbs(selected: dict) -> list:
    return [drug for drug in selected if drug in SCB_DRUGS]  # pre-cenobamate list only


def taper_dose_str(drug: str, base_dose: float, period_idx: int) -> str:
    if base_dose is None or base_dose <= 0 or not 0 <= period_idx < 6:
        return 'Not specified'
    return 'No automatic taper; clinician input required'


def risk_colors(risk: str):
    return {'HIGH': ('#FDECEA', '#C62828'), 'MODERATE': ('#FFF8E1', '#F57F17'),
            'LOW-MODERATE': ('#FFF8E1', '#F57F17'), 'LOW': ('#E8F5E9', '#2E7D32')}.get(risk, ('#F5F5F5', '#9E9E9E'))


def risk_label(risk: str) -> str:
    return risk


def floor_tablet(mg: float, sizes: list, splittable: bool = False, *, local_split_confirmed: bool = False) -> str:
    """Largest exact combination <= target; half-tablets require explicit local confirmation."""
    try:
        target = Decimal(str(mg))
        strengths = [Decimal(str(v)) for v in sizes]
        if not target.is_finite() or target < 0 or any(not x.is_finite() or x <= 0 for x in strengths):
            return 'REVIEW: invalid dose or strength; not executable'
        if target == 0:
            return '0 mg'
        if not strengths:
            return 'REVIEW: no locally confirmed strengths; not executable'
        coins = set(strengths)
        if splittable and local_split_confirmed:
            coins.update(x / 2 for x in strengths)
        places = max(0, -target.as_tuple().exponent, *(-x.as_tuple().exponent for x in coins))
        if places > 4:
            return 'REVIEW: precision requires pharmacist verification; not executable'
        scale = 10 ** places
        limit = int(target * scale)
        values = sorted({int(x * scale) for x in coins if x <= target})
        if not values:
            return 'REVIEW: positive target below smallest usable tablet; not executable'
        if limit > 1000000:
            return 'REVIEW: combination requires pharmacist verification; not executable'
        reachable = bytearray(limit + 1)
        reachable[0] = 1
        for total in range(1, limit + 1):
            reachable[total] = any(total >= coin and reachable[total - coin] for coin in values)
        best = next((i for i in range(limit, 0, -1) if reachable[i]), None)
        if best is None:
            return 'REVIEW: no positive tablet combination; not executable'
        result = f'{(Decimal(best) / scale).normalize():f} mg'
        if splittable and local_split_confirmed:
            result += ' (half tablets may be used; local formulation confirmed)'
        return result
    except (InvalidOperation, TypeError, ValueError, OverflowError):
        return 'REVIEW: invalid dose or strength; not executable'


def compute_dose(base: float, pct, drug: str = '') -> str:
    """Compatibility function: no automatic percentage-based co-ASM changes."""
    if base is None or base <= 0:
        return 'Not specified'
    unit = DRUG_DB.get(drug, {}).get('unit') or 'units'
    return f'No automatic co-medication dose calculated; baseline recorded: {base:g} {unit}/day'


def dose_max_alert(drug: str, base_dose: float) -> str:
    if base_dose is not None and base_dose > 0:
        return 'Verify dose, formulation and current local labeling; database maxima are not validated here.'
    return ''


def serum_alert(drug: str, val) -> str:
    if val is None:
        return ''
    return (f'Serum value entered for {drug}: clinical review only. Interpret units, sampling time, baseline, reference '
            'range, symptoms, seizures and interactions. No automatic dose change or accelerated taper is calculated.')


# The number in the citation maps the overlay's key to the manuscript-ordered
# PAPER_LIST. Fail fast if the supplied registry and list ever diverge.
def _build_reference_index():
    numbered = {}
    for key, citation in REFERENCES.items():
        match = re.match(r'^\[(\d+)\]', citation)
        if not match:
            raise ValueError(f'Reference {key} has no manuscript number')
        number = int(match.group(1))
        if number in numbered or number < 1 or number > len(PAPER_LIST):
            raise ValueError(f'Invalid or duplicate reference number: {number}')
        authors, year, title, _journal, identifier, _pmid, _summary = PAPER_LIST[number - 1]
        if not identifier or any(part not in citation for part in (authors, year, title, identifier)):
            raise ValueError(f'Reference {key} does not match manuscript entry {number}')
        numbered[number] = key
    if set(numbered) != set(range(1, len(PAPER_LIST) + 1)):
        raise ValueError('Manuscript reference registry and paper list differ')
    return {numbered[n]: (n, PAPER_LIST[n - 1]) for n in sorted(numbered)}


REFERENCE_INDEX = _build_reference_index()


def _audit_clinical_overlay():
    """Do not silently omit or substitute missing clinical source references."""
    for drug, info in DRUG_DB.items():
        for field in ('risk', 'action', 'mechanism', 'recommendation', 'references'):
            if not info.get(field):
                raise ValueError(f'Incomplete clinical overlay for {drug}: {field}')
        missing = [key for key in info['references'] if key not in REFERENCE_INDEX]
        if missing:
            raise ValueError(f'Unresolved clinical references for {drug}: {missing}')


_audit_clinical_overlay()
# These are additional drug-specific official documents, NOT manuscript references.
EXTRA_REGULATORY_DOCS = {
    'Cannabidiol (CBD)': [('FDA EPIDIOLEX prescribing information (2026; verify current version)',
        'https://www.accessdata.fda.gov/drugsatfda_docs/label/2026/210365s024s029s030lbl.pdf')],
    'Felbamate': [('FDA FELBATOL prescribing information (2012; verify current version)',
        'https://www.accessdata.fda.gov/drugsatfda_docs/label/2012/020189s027lbl.pdf')],
}


def _reference_record(key):
    if key not in REFERENCE_INDEX:
        return {'label': f'Unresolved reference key: {key} (no source supplied)', 'url': '', 'kind': 'unresolved'}
    number, (authors, year, title, journal, identifier, pmid, relevance) = REFERENCE_INDEX[key]
    is_regulatory = identifier.startswith(('https://', 'http://'))
    # Parentheses have to be escaped in markdown link destinations: quote them
    # even though they are valid DOI characters.
    url = identifier if is_regulatory else 'https://doi.org/' + quote(identifier, safe='/')
    return {'label': REFERENCES[key], 'url': url, 'kind': 'regulatory document (not DOI)' if is_regulatory else 'DOI',
            'number': number, 'authors': authors, 'year': year, 'title': title,
            'journal': journal, 'pmid': pmid, 'relevance': relevance, 'identifier': identifier}


def _source_records(drug):
    result = [_reference_record(key) for key in DRUG_DB[drug].get('references', [])]
    for label, url in EXTRA_REGULATORY_DOCS.get(drug, []):
        result.append({'label': 'Additional regulatory document (not a manuscript-numbered reference): ' + label,
                       'kind': 'regulatory document (not DOI)', 'url': url})
    return result


def _render_sources(records):
    for record in records:
        st.write(record['label'])
        if record['url']:
            st.markdown(f"[{record['kind']}]({record['url']})")
        else:
            st.warning('Reference unavailable; independent source verification is required.')


def _plain_sources(records):
    return '\n'.join(f"{r['label']} | {r['kind']}: {r['url']}" if r['url'] else r['label'] for r in records)


def _interaction_text(drug):
    info = DRUG_DB[drug]
    parts = [f'{drug} - unvalidated risk category: {info.get("risk", "not assigned")}',
             'Action: ' + info.get('action', 'Not supplied.'),
             'Mechanism: ' + info.get('mechanism', 'Not supplied.'),
             'Recommendation for clinician review: ' + info.get('recommendation', 'Not supplied.')]
    parts.append('Two-way interaction: ' + (info.get('two_way') or
        'No specific reverse interaction is described here; this does not establish absence of an interaction.'))
    return '\n'.join(parts)


def _export_interactions(drugs):
    return '\n\n'.join(_interaction_text(drug) for drug in drugs)


def _export_sources(drugs):
    return '\n\n'.join(drug + '\n' + _plain_sources(_source_records(drug)) for drug in drugs)


def fmt_refs(keys: tuple) -> str:
    return ' | '.join(_plain_sources([_reference_record(k)]) for k in keys)


def build_df(selected_frozen: tuple) -> pd.DataFrame:
    """Generic label reference; caller must enforce scope. No co-ASM changes."""
    rows = []
    for week, dose in zip(WEEK_LABELS, XCOP_SCHEDULE):
        row = {'Week': week, 'Xcopri (Cenobamate)': f'{dose:g} mg/day'}
        for drug, _dose, _serum in selected_frozen:
            row[drug] = 'Not specified - no automatic co-medication dose calculated'
        rows.append(row)
    return pd.DataFrame(rows)


def build_me_df(selected_frozen: tuple, df_json: str, taper_drug: str = None) -> pd.DataFrame:
    """Daily totals only; do not invent AM/PM doses or split tablets."""
    df = pd.read_json(io.StringIO(df_json))
    for drug, _dose, _serum in selected_frozen:
        if drug in df.columns:
            df[drug] = df[drug].astype(str) + ' | AM/PM: clinician to specify'
    return df


def _pdf_text(value) -> str:
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', str(value))
    return xml_escape(text, {'"': '&quot;', "'": '&apos;'}).replace('\n', '<br/>')


def make_pdf(patient_frozen: tuple, selected_frozen: tuple, df_json: str, extra_drugs: tuple = ()) -> bytes:
    """Escaped export with key safety warnings, without shared patient-data caching."""
    patient = dict(patient_frozen)
    df = pd.read_json(io.StringIO(df_json))
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=14*mm, bottomMargin=14*mm)
    # Ship Unicode fonts with the app: silent Helvetica fallback could render
    # clinically meaningful symbols and accented reference names incorrectly.
    font_dirs = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts'),
                 '/usr/share/fonts/truetype/dejavu']
    font_pair = next(((os.path.join(d, 'DejaVuSans.ttf'), os.path.join(d, 'DejaVuSans-Bold.ttf'))
                      for d in font_dirs
                      if os.path.isfile(os.path.join(d, 'DejaVuSans.ttf')) and
                         os.path.isfile(os.path.join(d, 'DejaVuSans-Bold.ttf'))), None)
    if font_pair is None:
        raise RuntimeError('PDF export requires the bundled fonts directory with DejaVu Sans regular and bold fonts.')
    font_path, bold_path = font_pair
    if 'CenoDejaVu' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('CenoDejaVu', font_path))
    if 'CenoDejaVu-Bold' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('CenoDejaVu-Bold', bold_path))
    pdfmetrics.registerFontFamily('CenoDejaVu', normal='CenoDejaVu', bold='CenoDejaVu-Bold')
    regular, bold = 'CenoDejaVu', 'CenoDejaVu-Bold'
    title = ParagraphStyle('review-title', fontSize=13, leading=17, fontName=bold, spaceAfter=7)
    head = ParagraphStyle('review-head', fontSize=10, leading=14, fontName=bold, spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle('review-body', fontSize=8, leading=12, fontName=regular, spaceAfter=4, wordWrap='CJK')
    story = [Paragraph('Cenobamate: unvalidated clinician-review material', title), Paragraph(_pdf_text(DISCLAIMER), body),
             Paragraph(_pdf_text(f'Generated {date.today()}'), body), Paragraph('Patient profile (as entered)', head)]
    for key, value in patient.items():
        if value is not None and str(value) not in ('', 'None'):
            story.append(Paragraph(f'<b>{_pdf_text(key)}:</b> {_pdf_text(value)}', body))
    story.append(Paragraph('Required safety review', head))
    for flag in SAFETY_FLAGS:
        story.append(Paragraph(f"<b>{_pdf_text(flag['title'])}:</b> {_pdf_text(flag['body'])}", body))
        for key in flag['refs']:
            ref = _reference_record(key)
            if ref['url']:
                story.append(Paragraph(f"{_pdf_text(ref['label'])} <link href=\"{_pdf_text(ref['url'])}\" color=\"blue\">{_pdf_text(ref['kind'])}: {_pdf_text(ref['url'])}</link>", body))
            else:
                story.append(Paragraph(_pdf_text(ref['label']), body))
    story.append(Paragraph('Medication data as entered; no automatic adjustment', head))
    for drug, dose, serum in selected_frozen:
        unit = DRUG_DB.get(drug, {}).get('unit') or 'units'
        value = f'{dose} {unit}/day' if dose is not None else 'not entered'
        serum_text = f'; serum value {serum} (verify units)' if serum is not None else ''
        story.append(Paragraph(_pdf_text(f'{drug}: {value}{serum_text}'), body))
    interaction_drugs = list(dict.fromkeys([d for d, _, _ in selected_frozen] + list(extra_drugs)))
    story.append(Paragraph('Selected medication interaction details and sources', head))
    story.append(Paragraph('Risk categories and narrative are unvalidated review prompts, not a treatment order. Absence of an alert does not establish safety.', body))
    for drug in interaction_drugs:
        if drug not in DRUG_DB:
            story.append(Paragraph(_pdf_text(f'Unknown medication: {drug}; interaction content unavailable.'), body))
            continue
        story.append(Paragraph(_pdf_text(_interaction_text(drug)), body))
        for ref in _source_records(drug):
            story.append(Paragraph(_pdf_text(ref['label']), body))
            if ref['url']:
                story.append(Paragraph(f"<link href=\"{_pdf_text(ref['url'])}\" color=\"blue\">{_pdf_text(ref['kind'])}: {_pdf_text(ref['url'])}</link>", body))
    story.append(Paragraph('Unvalidated reference and clinician-entered values', head))
    story.append(Paragraph('Daily totals only. No automatic AM/PM division, splitting or taper.', body))
    for _, row in df.iterrows():
        story.append(Paragraph(f"<b>{_pdf_text(row.get('Week', 'Period'))}</b>", body))
        for col, val in row.items():
            if col != 'Week':
                story.append(Paragraph(f'{_pdf_text(col)}: {_pdf_text(val)}', body))
    doc.build(story)
    return buf.getvalue()


def _csv_safe(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r')) else text


def _scope_ok(age, liver, renal, egfr, target, short_qt):
    return (age is not None and age >= 18 and liver == 'Normal - clinician confirmed' and
            renal == 'Normal - clinician confirmed' and (egfr is None or egfr >= 60) and
            target == 200 and short_qt == 'No - clinician confirmed')


def _format_num(value):
    return f'{float(value):g}'


st.set_page_config(page_title='Cenobamate decision support', page_icon='🧠', layout='wide')
if not st.session_state.get('disclaimer_accepted', False):
    st.title('Cenobamate clinical decision support')
    st.error(DISCLAIMER)
    st.markdown('This unvalidated prototype is for qualified clinicians, not autonomous decisions. Verify current local labels, '
                'interactions and formulations. The clinician retains responsibility. Scope: adults with confirmed normal '
                'hepatic and renal function and cenobamate <=200 mg/day. Everolimus is one non-ASM example; most non-ASM '
                'interactions are not covered. Deployment may be remote. Do not enter identifiable data unless the deployment '
                'has appropriate security, access controls and institutional approval.')
    agree = st.checkbox('I am a qualified clinician and accept these limitations', key='disclaimer_checkbox')
    if st.button('Enter Tool', disabled=not agree, type='primary') and agree:
        st.session_state['disclaimer_accepted'] = True
        st.rerun()
    st.stop()

st.title('Cenobamate clinical transition and interaction review')
st.warning(DISCLAIMER)
st.caption('Use a de-identified profile. Deployment may be remote; security and data handling depend on the host. '
           'Session state is not a clinical record and exports contain sensitive information.')
tab1, tab2, tab3, tab4, tab5 = st.tabs(['1. Patient Profile', '2. Current Medications', '3. Interaction Analysis', '4. Titration Plan', '5. Evidence Base'])
with tab1:
    st.subheader('Patient Profile')
    c1, c2, c3 = st.columns(3)
    with c1:
        age = st.number_input('Age (years)', min_value=0, max_value=120, value=None, key='age')
        sex = st.selectbox('Sex', ['Not entered', 'Male', 'Female', 'Other / not specified'], key='gender')
        weight = st.number_input('Weight (kg)', min_value=0.0, max_value=300.0, value=None, key='weight')
    with c2:
        epilepsy = st.selectbox('Epilepsy type', ['Not entered', 'Focal onset', 'Generalized onset', 'Unknown onset', 'Developmental and epileptic encephalopathy'], key='epilepsy')
        egfr = st.number_input('eGFR (mL/min/1.73 m², if available)', min_value=0.0, max_value=200.0, value=None, key='egfr')
        renal = st.selectbox('Renal function', ['Unknown / not confirmed', 'Normal - clinician confirmed', 'Renal impairment', 'End-stage renal disease or haemodialysis'], key='renal')
    with c3:
        liver = st.selectbox('Hepatic function', ['Unknown / not confirmed', 'Normal - clinician confirmed', 'Mild impairment (Child-Pugh A)', 'Moderate impairment (Child-Pugh B)', 'Severe impairment (Child-Pugh C)'], key='liver')
        short_qt = st.selectbox('Familial short-QT syndrome or cenobamate hypersensitivity', ['Unknown / not confirmed', 'No - clinician confirmed', 'Yes'], key='short_qt')
        target = st.number_input('Clinician-considered cenobamate target (mg/day)', min_value=0.0, max_value=1000.0, value=None, key='target')
    pregnancy = st.selectbox('Pregnancy, breastfeeding or contraception', ['Not entered / not applicable', 'Pregnant', 'Breastfeeding', 'Hormonal contraception', 'Non-hormonal contraception / not sexually active'], key='pregnancy')
    if age is not None and age < 18:
        st.error('Pediatric use is outside this tool calculation scope; no schedule is calculated. Safety and efficacy are not established in the cited labels.')
    elif age is not None and age >= 65:
        st.warning('Age 65+: review sedation, falls, gait, cognition, comorbidities and polypharmacy. Longer 4–8-week steps and 100–150 mg/day are conservative, non-validated clinician options, not default targets or schedules. Evidence is limited (O\'Dwyer 2024; Yoon 2026).')
    if 'Severe impairment' in liver:
        st.error('Severe hepatic impairment: FDA use is not recommended; EMA says cenobamate should not be used. Neither lists severe hepatic impairment as a formal contraindication. No schedule is calculated.')
    elif 'Mild impairment' in liver or 'Moderate impairment' in liver:
        st.warning('Mild or moderate hepatic impairment: FDA/EMA maximum recommended dose 200 mg/day; dose reduction may be considered. Outside this tool normal-organ calculation scope.')
    if renal == 'End-stage renal disease or haemodialysis':
        st.error('FDA: not recommended in end-stage renal disease (CrCl <15 mL/min) undergoing dialysis. EMA: should not be used in end-stage renal disease or haemodialysis. No schedule is calculated.')
    elif renal == 'Renal impairment' or (egfr is not None and egfr < 60):
        st.warning('Renal impairment is outside this tool calculation scope. FDA advises caution and consideration of dose reduction in mild, moderate and severe impairment. EMA advises caution and maximum 300 mg/day for mild, moderate or severe impairment. Labels use creatinine clearance categories; eGFR is not interchangeable with CrCl.')
    elif egfr is not None and egfr < 90:
        st.info('eGFR alone does not establish the label creatinine clearance category or renal disease. Review renal function and applicable label; this tool requires explicit confirmation of normal function.')
    if short_qt == 'Yes':
        st.error('Familial short-QT syndrome and hypersensitivity to cenobamate or ingredients are contraindications; no schedule is generated.')
    if pregnancy == 'Hormonal contraception':
        st.warning('Cenobamate may reduce hormonal oral contraceptive effectiveness. Discuss additional or alternative non-hormonal contraception and current local labeling; pharmacist review is recommended.')
    if pregnancy in ('Pregnant', 'Breastfeeding'):
        st.warning('Pregnancy/lactation: specialist patient-specific benefit-risk review is needed; consult the current label. This tool does not establish safety.')
    if target is not None and target > 200:
        st.warning('Above 200 mg/day: outside the tool interaction-calculation scope. No schedule is calculated; this does not assert that such doses are unapproved.')
    if target is not None and target <= 200 and target != 200:
        st.info('A lower or different target must be individualized. The tool does not generate a separate patient-specific schedule for it.')

with tab2:
    st.subheader('Current medications in the supported inventory')
    st.caption('Enter total daily doses. Everolimus is a non-ASM example; other non-ASM interactions are not comprehensively covered. Optional serum values are for review only.')
    selected = {}
    for drug, info in DRUG_DB.items():
        if info.get('conditional_on_pregnancy'):
            continue
        with st.expander(drug):
            if st.checkbox(f'Patient currently receives {drug}', key=f'chk_{drug}'):
                unit = info.get('unit') or 'units'
                dose = st.number_input(f'{drug} total daily dose ({unit}/day)', min_value=0.0, value=None, key=f'dose_{drug}')
                serum = None
                if info.get('has_serum'):
                    serum = st.number_input(f'{drug} serum value (optional; verify units and sampling)', min_value=0.0, value=None, key=f'serum_{drug}')
                if dose is not None:
                    st.caption('Verify dose and local formulation; this tool does not validate a dose or tablet split.')
                selected[drug] = {'dose': dose, 'serum': serum}
    st.session_state['selected_drugs'] = selected

previous_selected = set(st.session_state.get('_previous_selected_drugs', []))
for removed in previous_selected - set(selected):
    for idx in range(6):
        st.session_state.pop(f'manual_{removed}_{idx}', None)
st.session_state['_previous_selected_drugs'] = list(selected)
if st.session_state.get('scb_to_discontinue') not in set(selected) | {None, 'None selected'}:
    st.session_state['scb_to_discontinue'] = 'None selected'
if 'plan_change_drugs' in st.session_state:
    valid_changes = [d for d in st.session_state['plan_change_drugs'] if d in selected]
    if valid_changes != st.session_state['plan_change_drugs']:
        st.session_state['plan_change_drugs'] = valid_changes

with tab3:
    st.subheader('Safety flags')
    for flag in SAFETY_FLAGS:
        with st.expander(flag['title'], expanded=True):
            st.write(flag['body'])
            _render_sources([_reference_record(k) for k in flag['refs']])
    st.subheader('Drug interaction review')
    st.info('The following updated content is for independent clinician review, not a prescription or validated algorithm. Risk categories are unvalidated; absence of a warning does not imply safety. No co-medication dose changes are made automatically.')
    if not selected:
        st.info('Select current medications in tab 2. A taper and a scenario are optional.')
    for drug, info in selected.items():
        with st.expander(drug, expanded=True):
            dose = info.get('dose')
            unit = DRUG_DB[drug].get('unit') or 'units'
            st.write(f'Current total daily dose: {_format_num(dose)} {unit}/day' if dose is not None else 'Current dose not entered.')
            if info.get('serum') is not None:
                st.warning(serum_alert(drug, info['serum']))
            clinical = DRUG_DB[drug]
            st.write(f"Unvalidated risk category: {clinical['risk']}")
            st.write('Action for clinical review: ' + clinical['action'])
            st.write('Mechanism: ' + clinical['mechanism'])
            st.write('Recommendation for clinical review: ' + clinical['recommendation'])
            st.write('Two-way interaction: ' + (clinical['two_way'] or 'No specific reverse interaction is described here; this does not establish absence of an interaction.'))
            st.markdown('**Sources for this medication**')
            _render_sources(_source_records(drug))
            if drug == 'Clobazam' and dose is not None:
                if dose > 20:
                    st.warning('Clobazam >20 mg/day: the author-defined operational rule prompts proactive reduction review. It is not a validated cutoff and does not create a taper; clinician selection is required.')
                else:
                    st.warning('Clobazam ≤20 mg/day: the author-defined rule does not itself trigger a proactive reduction; this is not proof of safety and does not rule out an individualized reduction. Smith et al. suggest considering a 5–10 mg/day reduction at cenobamate 100 mg/day for patients on 10–20 mg/day when appropriate; earlier review may be needed for adverse effects. No automatic change is made.')
            if drug == 'Lamotrigine':
                st.info('Cenobamate may reduce lamotrigine concentrations; response varies. A fixed increase is not assumed. Review seizure control, tolerability, interacting drugs and concentrations when useful.')
            if drug == 'Lacosamide' and dose is not None and dose >= 400:
                st.warning('Lacosamide ≥400 mg/day: independently consider proactive reduction even if fewer than two pre-existing SCBs are listed. This does not mandate discontinuation or a particular taper.')
            if drug in CASCADE_DDI:
                st.info('Enzyme-inducer changes may affect other medicines during washout; direction and magnitude vary. Review interactions and consider pharmacist consultation.')
            if drug == 'Everolimus':
                st.warning('Everolimus is a non-ASM example. Review its interaction and indication with the prescribing specialist and pharmacist; the inventory is not a complete non-ASM screen.')
    if pregnancy == 'Hormonal contraception':
        with st.expander('Hormonal contraceptives — interaction review', expanded=True):
            st.write(_interaction_text('Hormonal Contraceptives'))
            _render_sources(_source_records('Hormonal Contraceptives'))
    scbs = get_active_scbs(selected)
    if len(scbs) >= 2:
        st.warning('Two or more pre-cenobamate SCBs detected (' + ', '.join(scbs) + '). The Delphi panel recommends proactive down-titration or withdrawal, individualized to the patient; it does not mandate stopping an SCB or endorse this tool illustrative example. Balance tolerability and seizure control.')
    elif len(scbs) == 1:
        st.info('One pre-cenobamate SCB detected. Added SCB effects can cause dizziness, diplopia or ataxia; the Delphi recommendation for regimens already containing at least two SCBs is not triggered.')
    st.caption('All choices below are optional. Choosing a drug does not generate or mandate a taper.')
    taper_choice = st.selectbox('Drug the clinician is considering for taper (optional)', ['None selected'] + list(selected), key='scb_to_discontinue')
    for warning in get_cascade_warnings(taper_choice, selected):
        st.warning(f"Possible inducer-washout effect on {warning['drug']}: {warning['change']} {warning['action']}")

with tab4:
    st.subheader('12-week cenobamate reference and clinician-entered changes')
    scope_ok = _scope_ok(age, liver, renal, egfr, target, short_qt)
    show_schedule = st.checkbox('View the generic 12-week label reference (not an order)', value=False, key='show_reference')
    if show_schedule and not scope_ok:
        st.error('No schedule displayed. Confirm adult age, normal hepatic and renal function, absence of familial short-QT/hypersensitivity, and a clinician-considered 200 mg/day target. eGFR below 60, a different target, impairment, pediatrics or unknowns are outside this calculation path. This restriction is tool scope, not the full label.')
    st.markdown('**Optional co-medication changes: clinician-entered values only**')
    scenario = st.selectbox('Scenario', ['No scenario selected', 'Clinician-entered values for review'], key='plan_scenario')
    change_drugs = st.multiselect('Co-medications for which the clinician will enter possible values', list(selected), default=[], key='plan_change_drugs')
    if taper_choice != 'None selected' and taper_choice not in change_drugs:
        st.info('The selected potential taper does not create doses. Select that medication above only if manually entering values for review.')
    manual = {}
    if scenario == 'Clinician-entered values for review' and change_drugs:
        st.warning('Enter only clinician-selected hypothetical daily totals. Blank means not specified, never hold. Zero is an explicitly entered value, not an automatic discontinuation. This prototype does not round, validate, prescribe or split doses. Verify formulation and local availability with a pharmacist.')
        for drug in change_drugs:
            unit = DRUG_DB[drug].get('unit') or 'units'
            with st.expander(f'{drug}: possible daily totals for review', expanded=True):
                cols = st.columns(3)
                values = []
                for i, week in enumerate(WEEK_LABELS):
                    with cols[i % 3]:
                        values.append(st.number_input(f'{drug} — {week} ({unit}/day)', min_value=0.0, value=None, key=f'manual_{drug}_{i}'))
                manual[drug] = values
    context = {'age': age, 'sex': sex, 'weight': weight, 'epilepsy': epilepsy, 'egfr': egfr,
               'renal': renal, 'liver': liver, 'short_qt': short_qt, 'target': target,
               'pregnancy': pregnancy, 'selected': selected, 'taper': taper_choice,
               'scenario': scenario, 'change_drugs': change_drugs, 'manual': manual}
    fingerprint = hashlib.sha256(json.dumps(context, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    # Clear the earlier approval, not merely hide it: reverting a changed profile
    # must never silently restore a historical confirmation.
    if st.session_state.get('confirmed_manual_fingerprint') != fingerprint:
        st.session_state.pop('confirmed_manual_fingerprint', None)
    has_manual = any(v is not None for vals in manual.values() for v in vals)
    if has_manual:
        if st.button('Confirm review of the entered hypothetical values', key='confirm_manual_review'):
            st.session_state['confirmed_manual_fingerprint'] = fingerprint
        if st.session_state.get('confirmed_manual_fingerprint') != fingerprint:
            st.info('Manual values are not included in the review table until explicitly confirmed for this unchanged profile and set of values.')
    manual_confirmed = has_manual and st.session_state.get('confirmed_manual_fingerprint') == fingerprint
    if manual_confirmed:
        st.success('Clinician review confirmed for these entered hypothetical values only. They remain unvalidated and non-executable.')
    if show_schedule and scope_ok:
        st.caption('Generic label titration: 12.5, 25, 50, 100, 150, 200 mg/day, each for two weeks. The clinician determines applicability; no individualized regimen is validated.')
        frozen = tuple((d, info.get('dose'), info.get('serum')) for d, info in selected.items())
        df = build_df(frozen)
        if manual_confirmed:
            for drug, values in manual.items():
                unit = DRUG_DB[drug].get('unit') or 'units'
                df[drug] = [f'Clinician-entered: {_format_num(v)} {unit}/day; review only' if v is not None else 'Not specified - review only' for v in values]
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption('Daily totals only. No AM/PM split is calculated: clinician and pharmacist must verify administration times, actual strengths and formulation. No half tablet is assumed.')
        st.subheader('Export review material')
        export_df = df.copy()
        export_df['Status'] = DISCLAIMER
        export_df['Safety review'] = ' | '.join(f"{x['title']}: {x['body']}" for x in SAFETY_FLAGS)
        export_df['Safety sources'] = '\n'.join(_plain_sources([_reference_record(k) for k in x['refs']]) for x in SAFETY_FLAGS)
        interaction_drugs = list(selected) + (['Hormonal Contraceptives'] if pregnancy == 'Hormonal contraception' else [])
        export_df['Selected medication interaction details'] = _export_interactions(interaction_drugs)
        export_df['Selected medication references and links'] = _export_sources(interaction_drugs)
        export_df['Interaction review'] = ('SCBs present: ' + (', '.join(scbs) if scbs else 'none recorded') +
            "; Delphi's proactive SCB rationalization consideration concerns at least two pre-existing SCBs; "
            'lacosamide at 400 mg/day or more has a separate reduction consideration. Potential taper: ' + taper_choice +
            '; cascade effects are possible, not guaranteed; clinician/pharmacist review required. '
            'Clobazam >20 mg/day is an unvalidated operational prompt; <=20 is not a safety threshold. Serum values prompt review only. '
            + ' '.join(f"Possible cascade for {w['drug']}: {w['change']} {w['action']}" for w in get_cascade_warnings(taper_choice, selected)))
        safe_csv = export_df.apply(lambda column: column.map(_csv_safe)).to_csv(index=False).encode('utf-8-sig')
        patient = {'Age': age, 'Sex': sex, 'Weight (kg)': weight, 'Epilepsy': epilepsy, 'eGFR (mL/min/1.73 m2)': egfr,
                   'Renal function': renal, 'Hepatic function': liver, 'Familial short-QT / hypersensitivity': short_qt,
                   'Target considered (mg/day)': target, 'Pregnancy / contraception': pregnancy,
                   'Potential taper': taper_choice, 'Scenario': scenario,
                   'Interaction review': export_df['Interaction review'].iloc[0]}
        col1, col2 = st.columns(2)
        with col1:
            st.download_button('Download review CSV', data=safe_csv, file_name='cenobamate_review.csv', mime='text/csv')
        with col2:
            try:
                extra_drugs = ('Hormonal Contraceptives',) if pregnancy == 'Hormonal contraception' else ()
                pdf = make_pdf(tuple(patient.items()), frozen, df.to_json(), extra_drugs)
                st.download_button('Download review PDF', data=pdf, file_name='cenobamate_review.pdf', mime='application/pdf')
            except Exception as exc:
                st.error(f'PDF export unavailable: {exc}')
    st.divider()
    st.subheader('Manuscript vignette — separate educational example')
    if st.checkbox('Show the unvalidated author-defined manuscript example', value=False, key='show_case'):
        st.warning('ILLUSTRATIVE ONLY — UNVALIDATED AUTHOR-DEFINED OUTPUT, NOT A PRESCRIPTION. Values are not derived from the entered patient. Lacosamide taper is not required by Delphi; lamotrigine increases are neither validated nor consensus-mandated. Clobazam 20 mg/day is not a safety threshold. Individual clinician review is required.')
        st.write('Vignette: 52-year-old male, 78 kg, normal liver function, eGFR 72 mL/min, lacosamide 400 mg/day, clobazam 20 mg/day and lamotrigine 500 mg/day. Fixed educational case facts, not the active patient plan.')
        illustration = pd.DataFrame({'Period': WEEK_LABELS, 'Cenobamate (mg/day)': XCOP_SCHEDULE,
            'Clobazam (mg/day)': [20, 20, 20, 20, 20, 20], 'Lacosamide (mg/day)': [400, 300, 200, 100, 0, 0],
            'Lamotrigine (mg/day)': [500, 500, 575, 575, 650, 650]})
        st.dataframe(illustration, use_container_width=True, hide_index=True)
        st.caption('The clinician must independently review seizure control, tolerability, interactions, concentrations, taper rate and local formulation before any decision. No automatically generated adjustment follows from this illustration.')

with tab5:
    st.subheader('Evidence base and limitations')
    st.caption('Sources are numbered in final manuscript order. Regulatory documents are not DOIs; verify the current locally applicable versions and all evidence independently. Additional drug-specific regulatory sources appear with the relevant interaction.')
    for key in REFERENCE_INDEX:
        ref = _reference_record(key)
        with st.expander(f"[{ref['number']}] {ref['authors']} ({ref['year']}) — {ref['title']}"):
            st.write(ref['label'])
            st.write('Source: ' + ref['journal'])
            st.markdown(f"[{ref['kind']}]({ref['url']})")
            if ref['pmid']:
                st.write(ref['pmid'])
            st.caption(ref['relevance'])
    st.caption('The software and its author-defined rules are unvalidated. Clinical judgment and independent verification remain necessary.')

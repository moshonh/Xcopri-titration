"""Transform theoretical review targets using clinician-entered product details.

The calculations are mathematical only, not label/availability verification or
clinical validation. Missing product or regimen information withholds changed
automatic values and blocks confirmation; entered baseline and physician values
are never silently rounded. Each administration must be representable.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
import re

from dose_timing import split_daily_values
from formulation_rounding import round_daily_dose, validate_administration
from practical_formulations import Formulation, parse_formulation
from titration_rules import CENOBAMATE_PERIOD_DOSES, DoseSchedule


FORMULATION_ALERT = (
    'Verify the exact product formulation, strength and label before splitting; a score alone '
    'does not establish equal-dose divisibility. Do not crush or split capsules. This tool does not split '
    'enteric-coated tablets or calculate crushing. Catalog split options are limited to the reviewed profile. '
    'Custom split permissions are clinician-entered and unverified; the tool cannot verify scoring or '
    'whether a modified-release tablet can be split. Some exact product labels may separately permit crushing a whole tablet '
    'for swallowing outside this tool; this is not permission to divide the dose. Tegretol CR, where '
    'the exact local product label permits a scored split, must not be crushed or chewed. '
    'Consult a pharmacist if intermediate doses require switching strengths or products.'
)
INTERNATIONAL_FORMULATION_WARNING = (
    'Note: Default tablet strengths and splitting rules are configured according to Israeli Ministry of Health (MoH) approved product labels. '
    'Clinicians practicing outside Israel must verify local commercial formulations, tablet scoring, and splitting/crushing permissions '
    'according to their national product labels and consult a pharmacist before recommending tablet splitting.'
)
MANUAL_FORMULATION_WARNING = (
    'Clinician-entered product details are not verified against the reviewed catalog or established as approved by the Israeli Ministry of Health. '
    'This custom profile is not automatically based on the Israeli catalog and may conflict with the reviewed label for a known brand, including its splitting permissions. '
    'Verify the actual product, strengths and splitting permissions against the current local label and consult a pharmacist.'
)
PRACTICAL_NOTE = (
    'Practical amounts, when available, use only the clinician-entered product and administration '
    'data. The software does not independently verify the product, its current local label or '
    'supply, and does not validate clinical suitability. Verify each administration with a pharmacist.'
)
NO_RULE_NOTE = ('No established tapering protocol/rule for this medication; baseline dose '
                'maintained unchanged—adjust based on clinical judgment.')
_AUTO = frozenset({'author_scb_taper', 'author_lamotrigine', 'author_clobazam'})
_TIMES = frozenset({'once_am', 'once_pm', 'once_other', 'twice_equal', 'twice_manual'})
_NO_RULE_HOLDS = frozenset({'Levetiracetam', 'Valproate (VPA)', 'Perampanel',
                            'Cannabidiol (CBD)', 'Zonisamide', 'Rufinamide',
                            'Felbamate', 'Everolimus', 'Phenobarbital', 'Primidone'})


@dataclass(frozen=True)
class PracticalPlan:
    schedule: DoseSchedule
    raw_values: tuple[Decimal | None, ...]
    am: tuple[Decimal | None, ...] | None
    pm: tuple[Decimal | None, ...] | None
    once: tuple[Decimal | None, ...] | None
    composition: tuple[str, ...]
    notes: tuple[str, ...]
    issues: tuple[str, ...]
    product_summary: str
    needs_stop_review: bool

    @property
    def complete(self) -> bool:
        return not self.issues


def _text(number: Decimal | None) -> str:
    if number is None:
        return 'Not specified'
    text = format(number, 'f')
    return text.rstrip('0').rstrip('.') if '.' in text else text


def _half(number: Decimal) -> Decimal:
    # Widget values are bounded to six decimal places; 50 digits is ample.
    with localcontext() as context:
        context.prec = 50
        return number / 2


def _composition(product: Formulation, composition) -> str:
    if not composition:
        return '0: no units'
    if product.kind in {'Oral solution', 'Oral suspension'}:
        count = sum(piece.count for piece in composition)
        with localcontext() as context:
            context.prec = 50
            volume = product.increment * count
        return f'{_text(volume)} mL per administration at {_text(product.concentration)} mg/mL'
    return '; '.join(f'{piece.count} × {product.description_for_piece(piece.strength)}' for piece in composition)


def _manual_warning(product: Formulation) -> str:
    warning = MANUAL_FORMULATION_WARNING
    if product.halves and re.search(r'(?<![\w])vimpat(?![\w])', product.name, re.IGNORECASE):
        warning += (' The reviewed Israeli Vimpat profile does not allow tablet halves; '
                    'the manually entered halves may conflict with that label.')
    if product.rounding_policy == 'review_label':
        warning += (' This custom name and formulation type match a reviewed profile with a label-specific '
                    'rounding caution, so higher nearest amounts are withheld; the custom details remain unverified.')
    return warning


def _label(product: Formulation) -> str:
    if product.kind in {'Oral solution', 'Oral suspension'}:
        details = (f'concentration {_text(product.concentration)} mg/mL; '
                   f'entered syringe increment {_text(product.increment)} mL')
    else:
        details = ('whole strengths (mg): ' + ', '.join(map(_text, product.whole_strengths)) +
                   '; selected halves (mg strengths): ' + (', '.join(map(_text, product.halves)) or 'none') +
                   '; selected quarters (mg strengths): ' + (', '.join(map(_text, product.quarters)) or 'none'))
    if product.catalog_id:
        catalog = f' Catalog profile source: {product.catalog_source}. Handling: {product.catalog_handling}'
    else:
        catalog = ' Custom profile not checked against the reviewed catalog. ' + _manual_warning(product)
    return (f'{product.name}; {product.kind}; {details}. '
            'Current pack, supply and inputs are not independently verified by the application.' + catalog)


def practicalize_schedule(schedule: DoseSchedule, product_input: dict, timing: str,
                          *, morning=None, evening=None) -> PracticalPlan:
    """Produce practical draft values for one drug; never round manual/baseline values.

    timing is once_am, once_pm, once_other, twice_equal, twice_manual or
    unspecified. Unequal BID uses physician-entered daily totals and separate
    doses: no unequal distribution is inferred. Automatic changed values are
    withheld without complete product details, a known regimen and a
    feasible unchanged baseline. The exact 100-mg planned threshold is checked
    again after transformation. Incomplete/invalid entries block review/export.
    """
    if timing not in _TIMES | {'unspecified'}:
        raise ValueError('Unknown administration schedule')
    raw = schedule.values
    if len(raw) != 6:
        raise ValueError('A schedule must have six periods')
    issues: list[str] = []
    notes: list[list[str]] = [[INTERNATIONAL_FORMULATION_WARNING] for _ in raw]
    compositions = ['Not specified'] * 6
    product = None
    any_known = any(value is not None for value in raw)
    if any(value is None for value in raw):
        issues.append(f'{schedule.drug}: one or more planned periods are unspecified; the complete plan cannot be confirmed or exported. Enter an individualized physician plan; a blank is not zero or a baseline hold.')
    if schedule.source_code in {'physician_manual', 'physician_baseline_hold'} and any_known and any(v is None for v in raw[:3]):
        issues.append(f'{schedule.drug}: complete all three early planned periods. A blank is not a baseline hold, and whether an early reduction occurred cannot be established across a missing period.')
    try:
        product = parse_formulation(product_input, schedule.drug)
    except ValueError as exc:
        if any_known:
            issues.append(f'{schedule.drug}: product details are missing or invalid: {exc}.')
    if any_known and timing not in _TIMES:
        issues.append(f'{schedule.drug}: administration regimen is missing or unspecified; select the actual once-daily or twice-daily regimen.')
    if product:
        product_summary = _label(product)
        if not product.catalog_id:
            for item in notes:
                item.append(_manual_warning(product))
    elif any_known:
        product_summary = 'Product details are missing or invalid; no practical calculation established.'
    else:
        product_summary = 'Product details are missing or invalid and no numerical target was established; no practical calculation established.'
    if timing not in _TIMES:
        product_summary += ' Administration regimen is missing or unspecified.'
    auto = schedule.source_code in _AUTO
    baseline = schedule.baseline
    baseline_ok = True
    if product and any_known and baseline is not None and timing in {'once_am', 'once_pm', 'once_other', 'twice_equal'}:
        per_dose = _half(baseline) if timing == 'twice_equal' else baseline
        try:
            check = validate_administration(per_dose, product.pieces)
            baseline_ok = check.representable
            if not baseline_ok:
                issues.append(f'{schedule.drug}: the unchanged baseline cannot be assembled for each selected administration from the entered product pieces; correct the product or regimen. The baseline has not been changed.')
        except ValueError as exc:
            baseline_ok = False
            issues.append(f'{schedule.drug}: cannot verify the baseline composition: {exc}.')
    result = list(raw)
    for i, target in enumerate(raw):
        if target is None:
            continue
        if (NO_RULE_NOTE in schedule.reason or any(NO_RULE_NOTE in caution for caution in schedule.cautions)
                or (schedule.source_code == 'physician_baseline_hold' and schedule.drug in _NO_RULE_HOLDS)):
            notes[i].append(NO_RULE_NOTE)
        changed_auto = auto and baseline is not None and target != baseline
        if changed_auto:
            if not product or timing not in _TIMES or not baseline_ok:
                result[i] = None
                blockers = []
                if not product:
                    blockers.append('product details are missing or invalid')
                if timing not in _TIMES:
                    blockers.append('administration regimen is missing or unspecified')
                if not baseline_ok:
                    blockers.append('the unchanged baseline cannot be assembled from the entered product pieces')
                notes[i].append('Automatic target withheld: ' + '; '.join(blockers) + '.')
            elif timing == 'twice_manual':
                result[i] = None
                notes[i].append('Automatic target withheld: unequal AM/PM doses require physician-entered daily totals and both administrations.')
                msg = f'{schedule.drug}: for unequal morning/evening dosing, enter an individualized daily schedule and both amounts; automatic dose distribution is not inferred.'
                if msg not in issues:
                    issues.append(msg)
            else:
                try:
                    mode = 'twice_equal' if timing == 'twice_equal' else 'once'
                    rounded = round_daily_dose(target, product.pieces, mode, baseline)
                    if product.rounding_policy == 'review_label' and rounded.rounded_daily_dose > target:
                        raise ValueError('the nearest higher amount may conflict with this product label’s rounding direction; review the label and enter an individualized physician plan')
                    result[i] = rounded.rounded_daily_dose
                    if rounded.is_rounded:
                        notes[i].append(f'Theoretical target {_text(target)} mg/day; nearest representable total {_text(rounded.rounded_daily_dose)} mg/day.')
                    if rounded.larger_than_planned_reduction:
                        notes[i].append('WARNING: rounding makes the reduction larger than the theoretical target.')
                    if rounded.nonzero_target_rounded_to_zero:
                        notes[i].append('STOP WARNING: a nonzero target rounded to zero, which would discontinue this medication; explicit clinician review is required.')
                except ValueError as exc:
                    result[i] = None
                    notes[i].append('Automatic target withheld: exact composition could not be calculated.')
                    msg = f'{schedule.drug}: exact practical calculation unavailable: {exc}.'
                    if msg not in issues:
                        issues.append(msg)
        elif not auto:
            notes[i].append('Clinician-entered or baseline value shown exactly; never rounded by the app.')
        if product and (product.halves or product.quarters or product.kind in {'Capsule', 'Modified-release tablet', 'Enteric-coated tablet', 'Film-coated tablet'}):
            notes[i].append(FORMULATION_ALERT)
    values = tuple(result)
    # Defense in depth: planned dose changes at earlier reference stages may not
    # decrease relative to any previous known value, including baseline.
    previous = baseline if baseline is not None and baseline > 0 else None
    for i, value in enumerate(values):
        if CENOBAMATE_PERIOD_DOSES[i] >= 100:
            break
        if value is None:
            continue
        if previous is not None and value < previous:
            raise ValueError(f'{schedule.drug}: a planned reduction before cenobamate 100 mg/day is not permitted by this app. Do not delay medically needed action outside the app.')
        previous = value
    am = pm = once = None
    if timing == 'twice_equal':
        am, pm = split_daily_values(values, 'equal')
    elif timing == 'twice_manual':
        am, pm = split_daily_values(values, 'manual', morning=morning, evening=evening)
        if any(total is not None and (a is None or p is None) for total, a, p in zip(values, am, pm)):
            issues.append(f'{schedule.drug}: enter both morning and evening amounts for every specified daily total; blank is not zero.')
    elif timing == 'once_am':
        am, pm = values, tuple(None if v is None else Decimal(0) for v in values)
    elif timing == 'once_pm':
        am, pm = tuple(None if v is None else Decimal(0) for v in values), values
    elif timing == 'once_other':
        once = values
    needs_stop = False
    if product and timing in _TIMES:
        for i, total in enumerate(values):
            if total is None:
                continue
            if timing == 'twice_manual':
                doses = (am[i], pm[i])
                if any(v is None for v in doses):
                    continue
            elif timing == 'twice_equal':
                doses = (am[i], pm[i])
            else:
                doses = (total,)
            details = []
            try:
                for dose in doses:
                    check = validate_administration(dose, product.pieces)
                    if not check.representable:
                        raise ValueError(f'{_text(dose)} mg per administration cannot be assembled')
                    details.append(_composition(product, check.composition))
            except ValueError as exc:
                issues.append(f'{schedule.drug}, period {i + 1}: {exc}; entered amounts were not changed.')
                notes[i].append('WARNING: an individual administration could not be assembled or calculated from the entered pieces; clinician/pharmacist review required.')
            else:
                if timing in {'twice_equal', 'twice_manual'}:
                    compositions[i] = f'AM: {details[0]} | PM: {details[1]}'
                else:
                    compositions[i] = f'Once: {details[0]}'
            if baseline is not None and baseline > 0 and total == 0:
                needs_stop = True
                if not any('STOP WARNING' in note for note in notes[i]):
                    notes[i].append('STOP WARNING: zero means discontinuation, not missing data; clinician review is required.')
    # A stop must also be flagged when product details are missing or invalid.
    if baseline is not None and baseline > 0 and any(value == 0 for value in values if value is not None):
        needs_stop = True
    for i, value in enumerate(values):
        if value is not None and baseline is not None and baseline > 0 and value == 0 and not any('STOP WARNING' in note for note in notes[i]):
            notes[i].append('STOP WARNING: zero means discontinuation, not missing data; clinician review is required.')
    reasons = tuple(f'Theoretical target: {_text(t)} mg/day; displayed value: {_text(v)} mg/day. '
                    + (' '.join(notes[i]) or 'No dose rounding was required.')
                    if t is not None else 'No numerical target established; not a stop instruction.'
                    for i, (t, v) in enumerate(zip(raw, values)))
    # The original generic warning describes the theoretical engine; replace it
    # in displayed outputs with the practical-computation explanation.
    cautions = tuple(PRACTICAL_NOTE if c.startswith('Daily values are unrounded theoretical') else c
                     for c in schedule.cautions
                     if not (c.startswith('IMPORTANT: A positive dose remains at week 12.')
                             and (values[-1] is None or values[-1] == 0)))
    practical_schedule = replace(schedule, values=values, period_reasons=reasons, cautions=cautions)
    return PracticalPlan(practical_schedule, raw, am, pm, once, tuple(compositions),
                         tuple(' '.join(item) for item in notes), tuple(dict.fromkeys(issues)),
                         product_summary, needs_stop)

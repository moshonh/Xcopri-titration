"""Unvalidated author-defined concomitant-medication suggestions for review.

This module has no UI or external dependencies and does not prescribe, validate
or establish the clinical suitability of a dose. All automatic values are
unrounded theoretical total daily amounts in mg/day. They are author-defined
suggestions, not expert-consensus-approved schedules. A clinician must assess
the patient, the proposed values, applicable labeling and formulation.

The caller must affirmatively confirm the application's calculation scope;
without that confirmation automatic suggestions are withheld. Manual values
are never populated or supplemented by an automatic rule. No symptom or serum
value is interpreted by this module. A blank is represented by None; zero is a
real, explicitly entered or mathematically calculated value, never a synonym
for missing input.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from typing import TypeAlias


NumberInput: TypeAlias = Decimal | int | float | str
OptionalNumberInput: TypeAlias = NumberInput | None
PERIOD_LABELS: tuple[str, ...] = (
    "Weeks 1–2", "Weeks 3–4", "Weeks 5–6",
    "Weeks 7–8", "Weeks 9–10", "Weeks 11–12",
)

# The seven percentage rules below are proportions of the original baseline,
# not serial reductions from the prior interval. Carbamazepine uses a fixed
# 200 mg/day reduction from baseline per interval, floored at zero.
SCB_TAPER_FACTORS: dict[str, tuple[Decimal, ...]] = {
    "Lacosamide": tuple(map(Decimal, ("1", ".75", ".50", ".25", "0", "0"))),
    "Oxcarbazepine": tuple(map(Decimal, ("1", ".80", ".60", ".40", ".20", "0"))),
    "Eslicarbazepine acetate (ESL)": tuple(map(Decimal, ("1", ".80", ".60", ".40", ".20", "0"))),
    "Phenytoin": tuple(map(Decimal, ("1", ".75", ".50", ".25", "0", "0"))),
    "Lamotrigine": tuple(map(Decimal, ("1", ".75", ".50", ".25", "0", "0"))),
    "Zonisamide": tuple(map(Decimal, ("1", ".80", ".60", ".40", ".20", "0"))),
    "Rufinamide": tuple(map(Decimal, ("1", ".80", ".60", ".40", ".20", "0"))),
}
CARBAMAZEPINE_STEP_MG = Decimal("200")
SCB_DRUGS = frozenset((*SCB_TAPER_FACTORS, "Carbamazepine"))
LAMOTRIGINE_FACTORS = tuple(map(Decimal, ("1", "1", "1.15", "1.15", "1.30", "1.30")))
CLOBAZAM_ABOVE_20_FACTORS = tuple(map(Decimal, ("1", "1", ".75", ".75", ".50", ".50")))
CLOBAZAM_AT_MOST_20_FACTORS = (Decimal("1"),) * 6
CLOBAZAM_THRESHOLD_MG = Decimal("20")

_LIMIT = 1000  # Technical precision/range limit; not a clinical dose limit.
_REVIEW = (
    "Unvalidated author-defined or physician-entered review material; not a "
    "prescription and not a clinically validated dose. A treating clinician "
    "must assess the patient, interactions, timing, formulation and local label."
)
_THEORETICAL = (
    "Daily values are unrounded theoretical mg/day totals; no formulation, "
    "tablet strength, tablet splitting or administration schedule is inferred."
)
_INDUCER_SCBS = frozenset({"Carbamazepine", "Oxcarbazepine", "Eslicarbazepine acetate (ESL)", "Phenytoin"})


@dataclass(frozen=True)
class DoseSchedule:
    """Six review values plus structured provenance, reasons and cautions.

    ``values`` contains Decimal mg/day totals or None, in ``period_labels``
    order. A Decimal zero is a value; it must not be rendered as missing.
    ``rule_kind`` and ``rule_values`` describe only the rule actually used,
    never a suppressed default. For ``baseline_factor``, rule_values are six
    multipliers; for ``fixed_step``, they are six absolute deductions from
    baseline in mg/day. Manual and unavailable results have no rule values.
    ``period_reasons`` is aligned one-to-one with values. ``source_code`` is
    stable machine-readable provenance and ``source_label`` is display text.
    """

    drug: str
    baseline: Decimal | None
    values: tuple[Decimal | None, ...]
    period_labels: tuple[str, ...]
    source_code: str
    source_label: str
    reason: str
    period_reasons: tuple[str, ...]
    rule_kind: str | None
    rule_values: tuple[Decimal, ...]
    cautions: tuple[str, ...]
    unit: str = "mg/day"
    requires_clinician_review: bool = True


def _number(value: OptionalNumberInput, field: str) -> Decimal | None:
    """Parse a nonnegative finite value; preserve None and reject bad input.

    Floats are interpreted through their shortest string representation. Callers
    should prefer decimal strings or Decimal when exact entered precision is
    important. Numeric-size bounds prevent impractical arbitrary-precision work;
    they are technical limits, not assessments of a safe or valid dose.
    """
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(f"{field} must be a finite nonnegative number or None")
    if isinstance(value, str) and (not value.strip() or len(value) > 2 * _LIMIT + 32):
        raise ValueError(f"{field} must be a finite nonnegative number or None")
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field} must be a finite nonnegative number or None") from None
    if not number.is_finite() or number < 0:
        raise ValueError(f"{field} must be a finite nonnegative number or None")
    if len(number.as_tuple().digits) > _LIMIT or abs(number.as_tuple().exponent) > _LIMIT or abs(number.adjusted()) > _LIMIT:
        raise ValueError(f"{field} exceeds the technical numeric precision/range limit")
    if number.is_zero() and number.is_signed():
        return Decimal("0")
    return number


def _mul_exact(a: Decimal, b: Decimal) -> Decimal:
    """Multiply without the ambient Decimal context rounding the result."""
    with localcontext() as context:
        context.prec = len(a.as_tuple().digits) + len(b.as_tuple().digits) + 2
        context.Emax = 10000
        context.Emin = -10000
        context.clamp = 0
        return a * b


def _subtract_exact(a: Decimal, b: Decimal) -> Decimal:
    """Subtract without the ambient Decimal context rounding the result."""
    with localcontext() as context:
        smallest_exponent = min(a.as_tuple().exponent, b.as_tuple().exponent)
        context.prec = max(1, max(a.adjusted(), b.adjusted()) - smallest_exponent + 2)
        context.Emax = 10000
        context.Emin = -10000
        context.clamp = 0
        return a - b


def _validate_name(name: object, field: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{field} must be a nonempty drug name")
    return name


def _manual_values(drug: str, values: Sequence[OptionalNumberInput]) -> tuple[Decimal | None, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence) or len(values) != len(PERIOD_LABELS):
        raise ValueError(f"Manual schedule for {drug} must contain exactly six period values")
    return tuple(_number(value, f"{drug} manual period {index + 1}") for index, value in enumerate(values))


def _check_lamotrigine_manual_taper(baseline: Decimal | None, values: tuple[Decimal | None, ...]) -> None:
    """Enforce the selected lamotrigine taper's no-increase constraint only.

    This is a structural conflict check, not clinical dose validation. Blanks
    are ignored but never filled; known entries are compared across gaps. A
    positive baseline is required to establish that the first entered amount
    does not increase over baseline.
    """
    if all(value is None for value in values):
        return
    if baseline is None or baseline <= 0:
        raise ValueError("A positive lamotrigine baseline is required to enter a selected lamotrigine taper")
    previous = baseline
    for value in values:
        if value is None:
            continue
        if value > previous:
            raise ValueError("A selected lamotrigine taper cannot increase at any entered period")
        previous = value


def _make(drug: str, baseline: Decimal | None, values: tuple[Decimal | None, ...],
          code: str, label: str, reason: str, period_reasons: tuple[str, ...],
          rule_kind: str | None = None, rule_values: tuple[Decimal, ...] = (),
          extra_cautions: tuple[str, ...] = ()) -> DoseSchedule:
    return DoseSchedule(drug, baseline, values, PERIOD_LABELS, code, label, reason,
                        period_reasons, rule_kind, rule_values,
                        (_REVIEW, _THEORETICAL, *extra_cautions))


def build_schedules(
    baselines: Mapping[str, OptionalNumberInput],
    *,
    taper_drug: str | None = None,
    manual_schedules: Mapping[str, Sequence[OptionalNumberInput]] | None = None,
    automatic_scope_confirmed: bool = False,
) -> dict[str, DoseSchedule]:
    """Build six-period structured review schedules for selected medications.

    ``baselines`` maps each selected drug name to its total mg/day or None.
    Names match the application's canonical drug names exactly. ``taper_drug``
    is one selected medication or None, where None explicitly means no selected
    taper. An unsupported selected taper has no invented automatic schedule.

    ``manual_schedules`` maps any selected drug to exactly six physician-entered
    values; None is an unfilled period, and 0 is an intentional entry. Such a
    schedule entirely supersedes automatic rules, including the selected SCB
    taper. For a selected lamotrigine taper only, known manual values must not
    increase relative to the baseline or any previous known period. This
    conflict check does not establish clinical safety. Otherwise manual values
    can be recorded even when baseline is missing, with a prominent caution.

    Set ``automatic_scope_confirmed=True`` only after the calling application
    has affirmatively verified every prerequisite of its calculation path,
    including its adult/organ-function, contraindication, cenobamate target and
    other high-risk/missing-input safeguards. False (the default) withholds all
    automatic values. This Boolean does not itself evaluate or establish safety.
    Manual entries remain manual even when automatic calculations are blocked;
    the caller may impose stricter display restrictions on all schedules.

    Automatic rules require a strictly positive baseline. Missing or zero
    baseline yields six None values, including periods whose rule would have
    produced zero. Only a selected recognized SCB taper, non-taper lamotrigine,
    and clobazam have automatic rules; other selected medications require manual
    input. Selecting no SCB taper does not suppress separate lamotrigine or
    clobazam defaults. Neither symptoms nor serum values alter these rules.

    Raises ValueError on invalid values, mismatched drug selections, invalid
    scope type or manual sequences other than six slots. Results are exact
    Decimal totals with auditable provenance; there is no rounding or splitting.
    """
    if not isinstance(baselines, Mapping):
        raise ValueError("baselines must be a mapping of selected drug names to daily doses")
    if not isinstance(automatic_scope_confirmed, bool):
        raise ValueError("automatic_scope_confirmed must be a boolean")
    parsed_baselines: dict[str, Decimal | None] = {}
    for drug, baseline in baselines.items():
        _validate_name(drug, "Drug")
        parsed_baselines[drug] = _number(baseline, f"{drug} baseline")
    if taper_drug is not None:
        _validate_name(taper_drug, "Taper drug")
        if taper_drug not in parsed_baselines:
            raise ValueError("The taper drug must be among the selected medications")
    if manual_schedules is None:
        manual_schedules = {}
    if not isinstance(manual_schedules, Mapping):
        raise ValueError("manual_schedules must be a mapping")
    parsed_manual: dict[str, tuple[Decimal | None, ...]] = {}
    for drug, values in manual_schedules.items():
        _validate_name(drug, "Manual schedule drug")
        if drug not in parsed_baselines:
            raise ValueError(f"Manual schedule drug {drug} is not selected")
        parsed_manual[drug] = _manual_values(drug, values)
    if taper_drug == "Lamotrigine" and taper_drug in parsed_manual:
        _check_lamotrigine_manual_taper(parsed_baselines[taper_drug], parsed_manual[taper_drug])

    output: dict[str, DoseSchedule] = {}
    for drug, baseline in parsed_baselines.items():
        if drug in parsed_manual:
            values = parsed_manual[drug]
            notes = () if baseline is not None and baseline > 0 else (
                "Baseline is missing or zero; the entered values cannot be compared with a positive baseline. No automatic values were generated.",
            )
            output[drug] = _make(
                drug, baseline, values, "physician_manual", "Physician-entered values",
                "The physician-entered sequence replaces every automatic rule for this drug; blank periods remain unspecified.",
                tuple("Not entered; no automatic value substituted." if v is None else "Entered by the physician; clinical review required." for v in values),
                extra_cautions=notes,
            )
            continue
        is_taper = drug == taper_drug
        has_rule = (is_taper and drug in SCB_DRUGS | {"Clobazam"}) or (not is_taper and drug in {"Lamotrigine", "Clobazam"})
        if not has_rule:
            reason = ("No automatic taper is defined for this selected medication; physician-entered values are needed."
                      if is_taper else "No automatic schedule is defined for this medication; physician-entered values are needed.")
            output[drug] = _make(drug, baseline, (None,) * 6, "no_automatic_rule", "No automatic rule", reason, (reason,) * 6)
            continue
        if baseline is None or baseline <= 0:
            reason = ("Baseline is missing; no automatic value can be generated." if baseline is None
                      else "Baseline is zero; no automatic value can be generated.")
            output[drug] = _make(drug, baseline, (None,) * 6, "baseline_unavailable", "No automatic value", reason, (reason,) * 6)
            continue
        if not automatic_scope_confirmed:
            reason = "Required calculation-scope confirmation is absent; no automatic value can be generated."
            output[drug] = _make(drug, baseline, (None,) * 6, "scope_unconfirmed", "Automatic calculation withheld", reason, (reason,) * 6)
            continue
        extra: tuple[str, ...] = ()
        if is_taper and drug == "Carbamazepine":
            deductions = tuple(Decimal(str(200 * index)) for index in range(6))
            values = tuple(Decimal("0") if baseline <= deduction else _subtract_exact(baseline, deduction) for deduction in deductions)
            output[drug] = _make(
                drug, baseline, values, "author_scb_taper", "Unvalidated author-defined SCB taper suggestion",
                "Fixed 200 mg/day deduction per two-week interval from baseline, with a mathematical zero floor.",
                ("Fixed-step author-defined theoretical value; clinical review required.",) * 6,
                "fixed_step", deductions,
            )
            continue
        if is_taper and drug in SCB_TAPER_FACTORS:
            factors = SCB_TAPER_FACTORS[drug]
            code, label = "author_scb_taper", "Unvalidated author-defined SCB taper suggestion"
            reason = "Selected taper uses the original author-defined fractions of baseline; it takes precedence over other automatic rules for this drug."
        elif drug == "Lamotrigine":
            factors = LAMOTRIGINE_FACTORS
            code, label = "author_lamotrigine", "Unvalidated author-defined lamotrigine suggestion"
            reason = "Original author-defined fractions of baseline; a treating clinician must decide whether any increase is appropriate."
            if taper_drug in _INDUCER_SCBS:
                extra = ("An inducer taper may change lamotrigine exposure; assess the interaction and individual clinical context before any decision.",)
        else:
            factors = CLOBAZAM_ABOVE_20_FACTORS if baseline > CLOBAZAM_THRESHOLD_MG else CLOBAZAM_AT_MOST_20_FACTORS
            code, label = "author_clobazam", "Unvalidated author-defined clobazam suggestion"
            if baseline > CLOBAZAM_THRESHOLD_MG:
                reason = "Original author-defined rule for baseline above 20 mg/day; clinical assessment is required."
            else:
                reason = "Author-defined default holds baseline at 20 mg/day or less; clinical assessment is required."
                if is_taper:
                    reason += " A chosen taper below the threshold requires physician-entered values."
            extra = ("The 20 mg/day threshold is not a validated safety cutoff; lower doses may also require individualized review or change.",)
        output[drug] = _make(
            drug, baseline, tuple(_mul_exact(baseline, factor) for factor in factors), code, label, reason,
            ("Author-defined theoretical value; clinical review required.",) * 6,
            "baseline_factor", factors, extra,
        )
    return output

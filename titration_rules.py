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
CENOBAMATE_PERIOD_DOSES: tuple[Decimal, ...] = tuple(
    map(Decimal, ("12.5", "25", "50", "100", "150", "200"))
)

# The seven percentage rules below are proportions of the original baseline,
# not serial reductions from the prior interval. Automatic reductions begin in
# period 4, at the planned cenobamate dose of 100 mg/day. Carbamazepine uses a
# fixed 200 mg/day reduction from baseline per interval thereafter, floored at zero.
SCB_TAPER_FACTORS: dict[str, tuple[Decimal, ...]] = {
    "Lacosamide": tuple(map(Decimal, ("1", "1", "1", ".75", ".50", ".25"))),
    "Oxcarbazepine": tuple(map(Decimal, ("1", "1", "1", ".80", ".60", ".40"))),
    "Eslicarbazepine acetate (ESL)": tuple(map(Decimal, ("1", "1", "1", ".80", ".60", ".40"))),
    "Phenytoin": tuple(map(Decimal, ("1", "1", "1", ".75", ".50", ".25"))),
    "Lamotrigine": tuple(map(Decimal, ("1", "1", "1", ".75", ".50", ".25"))),
    "Zonisamide": tuple(map(Decimal, ("1", "1", "1", ".80", ".60", ".40"))),
    "Rufinamide": tuple(map(Decimal, ("1", "1", "1", ".80", ".60", ".40"))),
}
CARBAMAZEPINE_STEP_MG = Decimal("200")
SCB_DRUGS = frozenset((*SCB_TAPER_FACTORS, "Carbamazepine"))
LAMOTRIGINE_FACTORS = tuple(map(Decimal, ("1", "1", "1.15", "1.15", "1.30", "1.30")))
CLOBAZAM_ABOVE_20_FACTORS = tuple(map(Decimal, ("1", "1", "1", ".75", ".75", ".50")))
CLOBAZAM_AT_MOST_20_FACTORS = (Decimal("1"),) * 6
CLOBAZAM_THRESHOLD_MG = Decimal("20")

# Provisional, explicit whitelist only. The existing clinical overlay cites the
# EMA Ontozry SmPC (EMA2021), section 4.5, for no clinically relevant PK
# interaction in the studied settings. This is an app hold, not an EMA schedule.
_NON_TAPER_NO_RELEVANT_PK_HOLD_DRUGS = frozenset({"Levetiracetam", "Valproate (VPA)"})

_LIMIT = 1000  # Technical precision/range limit; not a clinical dose limit.
_REVIEW = (
    "Unvalidated author-defined or physician-entered review material; not a "
    "prescription and not a clinically validated dose. A treating clinician "
    "must assess the patient, interactions, timing, formulation and local label; "
    "individual clinical action may be needed before cenobamate 100 mg/day."
)
_THEORETICAL = (
    "Daily values are unrounded theoretical mg/day totals; no formulation, "
    "tablet strength or tablet splitting is inferred. AM/PM administration "
    "timing requires an explicit clinician choice."
)
_AUTOMATIC_REDUCTION_CAUTION = (
    "IMPORTANT: These unvalidated author-defined reductions assume the planned "
    "cenobamate titration; actual cenobamate doses are not checked here. The "
    "schedule is not FDA-labeled or Delphi-panel-endorsed, and is not an FDA "
    "or Delphi-panel requirement. A clinician "
    "must verify actual timing and may need to act earlier for the individual "
    "patient; do not delay clinically needed assessment or action."
)
_POST_12_WEEK_CAUTION = (
    "IMPORTANT: A positive dose remains at week 12. No post-12-week doses or "
    "taper completion date are established by this schedule; a clinician must "
    "determine any subsequent plan if appropriate."
)
_PHENYTOIN_NON_TAPER_CAUTION = (
    "IMPORTANT: Cenobamate may increase phenytoin levels through a pharmacokinetic "
    "interaction. Proactive dose reduction and/or review and monitoring may be needed. "
    "An unchanged baseline is not an assurance of safety; the treating clinician "
    "must assess the interaction and the individual patient."
)
_CARBAMAZEPINE_NON_TAPER_CAUTION = (
    "IMPORTANT: Cenobamate may decrease carbamazepine exposure. The FDA label "
    "advises increasing carbamazepine as needed for reduced efficacy, while the EMA SmPC says no "
    "routine adjustment is required. Additive sodium-channel-blocker adverse "
    "effects can favor reduction for tolerability. A clinician must assess "
    "seizure control, adverse effects, other medications and applicable labels "
    "and decide the individual plan; no universal numeric change is inferred."
)
_NO_RELEVANT_PK_HOLD_CAUTION = (
    "The existing clinical content overlay cites the EMA Ontozry SmPC section 4.5 "
    "(EMA2021): no clinically relevant pharmacokinetic interaction was identified "
    "in the studied setting. This provisional app baseline hold is not an "
    "EMA-endorsed dose schedule or proof of safety. A clinician must review "
    "tolerability, pharmacodynamic effects, other medications and their "
    "interactions, and applicable labels; patient-specific changes may be needed."
)
_NO_RELEVANT_PK_DRUG_CAUTIONS = {
    "Levetiracetam": "Review CNS and behavioral tolerability and seizure control.",
    "Valproate (VPA)": "Review hepatic safety and clinical tolerability.",
}
_CARBAMAZEPINE_TIMING_CAUTION = (
    "The unvalidated author-defined fixed-step taper first reduces carbamazepine "
    "in weeks 7–8, at the planned cenobamate dose of 100 mg/day. This timing "
    "is not a requirement of FDA labeling or the Delphi panel. The clinician "
    "must decide whether and when to taper, including any earlier individual "
    "action, and may replace this schedule."
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


def _post_12_week_note(values: tuple[Decimal | None, ...]) -> tuple[str, ...]:
    """Flag a known positive final taper dose, without inferring missing values."""
    return (_POST_12_WEEK_CAUTION,) if values[-1] is not None and values[-1] > 0 else ()


def _period_context(index: int) -> str:
    return f"{PERIOD_LABELS[index]} (planned cenobamate {CENOBAMATE_PERIOD_DOSES[index]} mg/day)"


def _factor_period_reasons(factors: tuple[Decimal, ...], values: tuple[Decimal, ...],
                           *, baseline_hold: bool = False) -> tuple[str, ...]:
    prefix = ("Unvalidated unchanged baseline for review; interactions require clinical assessment. "
              if baseline_hold else "Author-defined theoretical value; clinical review required. ")
    return tuple(
        f"{prefix}{_period_context(index)}: baseline × {factor} = {value} mg/day."
        for index, (factor, value) in enumerate(zip(factors, values))
    )


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

    The six periods assume cenobamate 12.5, 25, 50, 100, 150 and 200 mg/day,
    respectively, each for two weeks. Automatic reductions start at period 4,
    planned cenobamate 100 mg/day; actual cenobamate dosing is not checked. The
    clinician may need to act earlier for an individual patient. No post-12-week
    doses or completion dates are inferred. These rules are unvalidated author
    suggestions, not FDA labeling or Delphi-panel requirements.

    Automatic rules require a strictly positive baseline. Missing or zero
    baseline yields six None values, including periods whose rule would have
    produced zero. Non-taper SCBs hold baseline for review, except lamotrigine,
    which retains its separate author-defined increase, and phenytoin and
    carbamazepine, for which automatic values are withheld pending interaction
    review. Their planned values remain incomplete until an individual plan is
    entered. A baseline hold does not establish safety or account for interactions.
    Clobazam retains its
    separate default. Levetiracetam and Valproate (VPA), when not selected for
    taper, have a provisional baseline hold for review based on the existing
    overlay's limited PK evidence. If selected for taper they have no automatic
    numeric rule. Other unsupported medications require manual input. Neither
    symptoms nor serum values alter these rules.

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
        is_taper = drug == taper_drug
        if drug == "Phenytoin" and not is_taper:
            extra = (_PHENYTOIN_NON_TAPER_CAUTION,)
        elif drug == "Carbamazepine" and not is_taper:
            extra = (_CARBAMAZEPINE_NON_TAPER_CAUTION,)
        else:
            extra = ()
        if drug in parsed_manual:
            values = parsed_manual[drug]
            notes = () if baseline is not None and baseline > 0 else (
                "Baseline is missing or zero; the entered values cannot be compared with a positive baseline. No automatic values were generated.",
            )
            output[drug] = _make(
                drug, baseline, values, "physician_manual", "Physician-entered values",
                "The physician-entered sequence replaces every automatic rule for this drug; blank periods remain unspecified.",
                tuple("Not entered; no automatic value substituted." if v is None else "Entered by the physician; clinical review required." for v in values),
                extra_cautions=(_post_12_week_note(values) if is_taper else ()) + notes + extra,
            )
            continue
        if drug == "Phenytoin" and not is_taper:
            reason = (
                "No automatic phenytoin values are provided: cenobamate can raise "
                "phenytoin levels, and an unchanged baseline is not an assurance of safety. "
                "A clinician must review the interaction and may enter a manual schedule; "
                "proactive reduction and/or monitoring may be needed."
            )
            if baseline is None:
                reason += " Baseline is missing."
            elif baseline <= 0:
                reason += " Baseline is zero."
            if not automatic_scope_confirmed:
                reason += " Required calculation-scope confirmation is absent."
            output[drug] = _make(
                drug, baseline, (None,) * 6, "interaction_review_required",
                "Phenytoin interaction: clinician review required", reason, (reason,) * 6,
                extra_cautions=extra,
            )
            continue
        if drug == "Carbamazepine" and not is_taper:
            reason = (
                "No automatic carbamazepine values are provided: cenobamate may decrease "
                "carbamazepine exposure. The FDA label advises increasing as needed for reduced efficacy; "
                "the EMA SmPC says no routine dose adjustment is required. Additive "
                "sodium-channel-blocker adverse effects can favor reduction. A clinician "
                "must decide the individual plan; no universal numeric change is inferred. "
                "All six planned values are unspecified and the plan remains incomplete "
                "until a clinician enters an individual schedule."
            )
            if baseline is None:
                reason += " Baseline is missing."
            elif baseline <= 0:
                reason += " Baseline is zero."
            if not automatic_scope_confirmed:
                reason += " Required calculation-scope confirmation is absent."
            output[drug] = _make(
                drug, baseline, (None,) * 6, "interaction_review_required",
                "Carbamazepine interaction: clinician review required", reason, (reason,) * 6,
                extra_cautions=extra,
            )
            continue
        has_rule = (drug in SCB_DRUGS or drug == "Clobazam" or
                    (drug in _NON_TAPER_NO_RELEVANT_PK_HOLD_DRUGS and not is_taper))
        if not has_rule:
            reason = ("No automatic taper is defined for this selected medication; physician-entered values are needed."
                      if is_taper else "No automatic schedule is defined for this medication; physician-entered values are needed.")
            output[drug] = _make(drug, baseline, (None,) * 6, "no_automatic_rule", "No automatic rule", reason, (reason,) * 6)
            continue
        if baseline is None or baseline <= 0:
            reason = ("Baseline is missing; no automatic value can be generated." if baseline is None
                      else "Baseline is zero; no automatic value can be generated.")
            output[drug] = _make(drug, baseline, (None,) * 6, "baseline_unavailable", "No automatic value", reason, (reason,) * 6, extra_cautions=extra)
            continue
        if not automatic_scope_confirmed:
            reason = "Required calculation-scope confirmation is absent; no automatic value can be generated."
            output[drug] = _make(drug, baseline, (None,) * 6, "scope_unconfirmed", "Automatic calculation withheld", reason, (reason,) * 6, extra_cautions=extra)
            continue
        if is_taper and drug == "Carbamazepine":
            deductions = tuple(_mul_exact(CARBAMAZEPINE_STEP_MG, Decimal(index))
                               for index in (0, 0, 0, 1, 2, 3))
            values = tuple(Decimal("0") if baseline <= deduction else _subtract_exact(baseline, deduction) for deduction in deductions)
            output[drug] = _make(
                drug, baseline, values, "author_scb_taper", "Unvalidated author-defined SCB taper suggestion",
                "Unvalidated author-defined fixed 200 mg/day deductions from baseline start in weeks 7–8 "
                "at planned cenobamate 100 mg/day, increasing by 200 mg/day each subsequent two-week "
                "interval, with a mathematical zero floor; clinician review is required.",
                tuple(f"{_period_context(index)}: baseline minus {deduction} mg/day, floored at "
                      f"zero = {value} mg/day; author-defined theoretical value, clinical review required."
                      for index, (deduction, value) in enumerate(zip(deductions, values))),
                "fixed_step", deductions,
                extra_cautions=_post_12_week_note(values) + (_AUTOMATIC_REDUCTION_CAUTION, _CARBAMAZEPINE_TIMING_CAUTION),
            )
            continue
        if is_taper and drug in SCB_TAPER_FACTORS:
            factors = SCB_TAPER_FACTORS[drug]
            code, label = "author_scb_taper", "Unvalidated author-defined SCB taper suggestion"
            reason = ("Selected taper uses the author-defined fractions of baseline shifted later: "
                      "the first reduction is in weeks 7–8 at planned cenobamate 100 mg/day, "
                      "with subsequent two-week steps. It takes precedence over other automatic rules for this drug.")
        elif drug == "Lamotrigine":
            factors = LAMOTRIGINE_FACTORS
            code, label = "author_lamotrigine", "Unvalidated author-defined lamotrigine suggestion"
            reason = "Original author-defined fractions of baseline; a treating clinician must decide whether any increase is appropriate."
            if taper_drug in _INDUCER_SCBS:
                extra = ("An inducer taper may change lamotrigine exposure; assess the interaction and individual clinical context before any decision.",)
        elif drug in SCB_DRUGS:
            factors = (Decimal("1"),) * len(PERIOD_LABELS)
            code, label = "baseline_hold", "Baseline unchanged (review interactions)"
            reason = ("Unvalidated baseline hold for review only; an unchanged dose is not an assurance of safety. "
                      "A treating clinician must review interactions and determine whether a change is needed.")
        elif drug in _NON_TAPER_NO_RELEVANT_PK_HOLD_DRUGS:
            factors = (Decimal("1"),) * len(PERIOD_LABELS)
            code, label = "baseline_hold", "Provisional baseline unchanged (EMA PK evidence; review interactions)"
            reason = ("Provisional unvalidated app baseline hold for review only, not an EMA-endorsed "
                      "schedule. The existing clinical content overlay cites the EMA Ontozry SmPC "
                      "section 4.5 (EMA2021) for no clinically relevant pharmacokinetic interaction "
                      "identified in the studied setting. An unchanged dose is not an assurance of "
                      "safety; a clinician must review tolerability, other medications and interactions.")
            extra = (_NO_RELEVANT_PK_HOLD_CAUTION, _NO_RELEVANT_PK_DRUG_CAUTIONS[drug])
        else:
            factors = CLOBAZAM_ABOVE_20_FACTORS if baseline > CLOBAZAM_THRESHOLD_MG else CLOBAZAM_AT_MOST_20_FACTORS
            code, label = "author_clobazam", "Unvalidated author-defined clobazam suggestion"
            if baseline > CLOBAZAM_THRESHOLD_MG:
                reason = ("Unvalidated author-defined rule for baseline above 20 mg/day: the first "
                          "25% baseline reduction is in weeks 7–8 at planned cenobamate 100 mg/day; "
                          "the second is two intervals later in weeks 11–12. Clinical assessment is required.")
            else:
                reason = "Author-defined default holds baseline at 20 mg/day or less; clinical assessment is required."
                if is_taper:
                    reason += " A chosen taper at or below the threshold requires physician-entered values."
            extra = ("The 20 mg/day threshold is not a validated safety cutoff; lower doses may also require individualized review or change.",)
        values = tuple(_mul_exact(baseline, factor) for factor in factors)
        reduction_rule = code == "author_scb_taper" or (code == "author_clobazam" and baseline > CLOBAZAM_THRESHOLD_MG)
        if reduction_rule:
            extra = (_AUTOMATIC_REDUCTION_CAUTION,) + extra
        if is_taper or reduction_rule:
            extra = _post_12_week_note(values) + extra
        output[drug] = _make(
            drug, baseline, values, code, label, reason,
            _factor_period_reasons(factors, values, baseline_hold=code == "baseline_hold"),
            "baseline_factor", factors, extra,
        )
    return output

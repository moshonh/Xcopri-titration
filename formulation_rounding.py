"""Exact, formulation-agnostic dose rounding for clinician review.

This module makes NO claims about any drug, product, scoring, or suitability of
splitting tablets. Callers must supply clinically verified, individually
permissible piece strengths in a consistent unit and an explicit regimen.
It is a numerical aid only; all results require clinician review.

All amount inputs must be finite ``Decimal`` values. No float conversion or
Decimal-context arithmetic is used. Each administration may contain any
nonnegative number of the supplied pieces. The default result includes an exact
composition for *each* administration; pass ``include_composition=False`` to
omit it. A zero dose has an empty composition.

A candidate is selected by minimum absolute DAILY difference from the target.
On an exact tie, the candidate closest to baseline wins when baseline is
provided; if still tied, or no baseline is supplied, the higher dose wins. The
baseline never overrides a closer candidate. Nearest may therefore result in a
larger reduction, and even a nonzero target may round to zero.

The finite input and dynamic-programming limits below are deliberate safety
bounds. A ResourceLimitError means no numerical recommendation was made; it
must not be interpreted as unrepresentability or used to substitute an
unverified formulation. Piece decomposition uses the fewest possible pieces;
when multiple minimum-count combinations exist it prefers larger pieces.
"""

from __future__ import annotations

from array import array
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from math import gcd


MAX_PIECE_STRENGTHS = 64
MAX_DECIMAL_DIGITS = 256
MAX_ABS_DECIMAL_EXPONENT = 256
# Includes state zero. A conservative additional cap bounds total DP work.
MAX_DP_STATES = 250_001
MAX_DP_TRANSITIONS = 8_000_000


class ResourceLimitError(ValueError):
    """The exact calculation exceeds a safety limit; no result was made."""


@dataclass(frozen=True)
class PieceCount:
    """A number of identical clinician-permitted pieces, for ONE dose."""

    strength: Decimal
    count: int


Composition = tuple[PieceCount, ...]


@dataclass(frozen=True)
class RoundedDose:
    target_daily_dose: Decimal
    rounded_daily_dose: Decimal
    per_administration_dose: Decimal
    # One entry per administration; None when decomposition was not requested.
    administration_compositions: tuple[Composition, ...] | None
    is_rounded: bool
    # This is relative to target regardless of whether a baseline is known.
    rounded_below_target: bool
    # None without a baseline; otherwise compares actual vs planned reduction.
    larger_than_planned_reduction: bool | None
    nonzero_target_rounded_to_zero: bool
    clinician_review_required: bool = True


@dataclass(frozen=True)
class ManualAdministration:
    dose: Decimal
    representable: bool
    # None if not representable or if decomposition was not requested.
    composition: Composition | None


@dataclass(frozen=True)
class ManualRegimenValidation:
    administrations: tuple[ManualAdministration, ManualAdministration]
    expected_daily_total: Decimal
    actual_daily_total: Decimal
    total_matches: bool
    valid: bool
    clinician_review_required: bool = True


def _amount(value: Decimal, name: str, *, positive: bool = False) -> Fraction:
    """Validate and convert without invoking Decimal arithmetic or context."""
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal; floats are not accepted")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    sign, digits, exponent = value.as_tuple()
    # Check before constructing powers or large integers from untrusted inputs.
    if len(digits) > MAX_DECIMAL_DIGITS or abs(exponent) > MAX_ABS_DECIMAL_EXPONENT:
        raise ResourceLimitError(f"{name} exceeds the Decimal input limits")
    coefficient = 0
    for digit in digits:
        coefficient = coefficient * 10 + digit
    if sign and coefficient:
        raise ValueError(f"{name} must be nonnegative")
    if positive and not coefficient:
        raise ValueError(f"{name} must be positive")
    if exponent >= 0:
        return Fraction(coefficient * 10**exponent)
    return Fraction(coefficient, 10 ** (-exponent))


def _as_decimal(value: Fraction) -> Decimal:
    """Convert a nonnegative terminating fraction to Decimal exactly."""
    numerator, denominator = value.numerator, value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ArithmeticError("internal non-terminating result")
    scale = max(twos, fives)
    numerator *= 2 ** (scale - twos) * 5 ** (scale - fives)
    # Decimal(tuple) is exact and ignores the ambient context's precision.
    digits = tuple(int(char) for char in str(numerator))
    return Decimal((0, digits, -scale))


def _pieces(values: Sequence[Decimal]) -> tuple[Fraction, tuple[int, ...], tuple[Decimal, ...]]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        raise TypeError("permissible_pieces must be a nonempty sequence of Decimals")
    if not values:
        raise ValueError("permissible_pieces must not be empty")
    if len(values) > MAX_PIECE_STRENGTHS:
        raise ResourceLimitError("too many permissible piece strengths")
    # Deduplicate by exact numerical value, retaining the first Decimal spelling.
    unique: dict[Fraction, Decimal] = {}
    for index, value in enumerate(values):
        amount = _amount(value, f"permissible_pieces[{index}]", positive=True)
        unique.setdefault(amount, value)
    fractions = sorted(unique)
    common_denominator = 1
    for item in fractions:
        common_denominator = common_denominator * item.denominator // gcd(common_denominator, item.denominator)
    integer_pieces = [item.numerator * (common_denominator // item.denominator) for item in fractions]
    divisor = 0
    for item in integer_pieces:
        divisor = gcd(divisor, item)
    unit = Fraction(divisor, common_denominator)
    return unit, tuple(item // divisor for item in integer_pieces), tuple(unique[item] for item in fractions)


def _check_composition_flag(include_composition: bool) -> None:
    if not isinstance(include_composition, bool):
        raise TypeError("include_composition must be bool")


def _table(upper: int, coins: tuple[int, ...], want_composition: bool) -> tuple[bytearray, array | None]:
    if upper + 1 > MAX_DP_STATES or upper * len(coins) > MAX_DP_TRANSITIONS:
        raise ResourceLimitError("exact coin-combination search exceeds its resource limits")
    reachable = bytearray(upper + 1)
    reachable[0] = 1
    # Store an index, not a full combination, for each state.
    predecessor = array("i", [-1]) * (upper + 1) if want_composition else None
    if want_composition:
        # Counts are bounded by the state limit. Reverse denomination order and
        # retain the first minimum on ties to favor the larger piece.
        counts = array("i", [-1]) * (upper + 1)
        counts[0] = 0
        for state in range(1, upper + 1):
            best = upper + 1
            best_index = -1
            for index in range(len(coins) - 1, -1, -1):
                coin = coins[index]
                if coin <= state and reachable[state - coin]:
                    piece_count = counts[state - coin] + 1
                    if piece_count < best:
                        best = piece_count
                        best_index = index
            if best_index >= 0:
                reachable[state] = 1
                counts[state] = best
                predecessor[state] = best_index
    else:
        for state in range(1, upper + 1):
            for coin in coins:
                if coin > state:
                    break
                if reachable[state - coin]:
                    reachable[state] = 1
                    break
    return reachable, predecessor


def _composition(state: int, coins: tuple[int, ...], strengths: tuple[Decimal, ...], predecessor: array) -> Composition:
    counts = [0] * len(coins)
    while state:
        index = predecessor[state]
        if index < 0:
            raise ArithmeticError("internal unreachable composition state")
        counts[index] += 1
        state -= coins[index]
    return tuple(PieceCount(strength, count) for strength, count in zip(strengths, counts) if count)


def validate_administration(
    dose: Decimal,
    permissible_pieces: Sequence[Decimal],
    *,
    include_composition: bool = True,
) -> ManualAdministration:
    """Check whether one explicitly supplied dose is exactly formable.

    Never rounds or changes the entered dose. ``representable`` is False for a
    mathematically impossible amount; resource exhaustion instead raises
    ResourceLimitError. A zero dose is exactly formable with no pieces.
    """
    amount = _amount(dose, "dose")
    _check_composition_flag(include_composition)
    unit, coins, strengths = _pieces(permissible_pieces)
    state = amount / unit
    composition = None
    if state.denominator != 1:
        possible = False
    elif state.numerator == 0:
        possible = True
        if include_composition:
            composition = ()
    elif state.numerator < coins[0]:
        possible = False
    elif state.numerator in coins:
        possible = True
        if include_composition:
            composition = (PieceCount(strengths[coins.index(state.numerator)], 1),)
    else:
        reachable, predecessors = _table(state.numerator, coins, include_composition)
        possible = bool(reachable[state.numerator])
        if possible and include_composition:
            assert predecessors is not None
            composition = _composition(state.numerator, coins, strengths, predecessors)
    return ManualAdministration(dose, possible, composition)


def round_daily_dose(
    target_daily_dose: Decimal,
    permissible_pieces: Sequence[Decimal],
    administration_mode: str,
    baseline_daily_dose: Decimal | None = None,
    *,
    include_composition: bool = True,
) -> RoundedDose:
    """Round to the closest achievable daily total for explicit QDAY/equal BID.

    ``administration_mode`` must be ``'once'`` or ``'twice_equal'``. For equal
    BID the same achievable per-administration amount is used twice. Zero is
    always a candidate. Missing/invalid data raises; no default is invented.
    If a baseline is provided, ``larger_than_planned_reduction`` compares
    max(0, baseline - rounded) with max(0, baseline - target). Without a
    baseline, it is None; ``rounded_below_target`` is still always available.
    """
    target = _amount(target_daily_dose, "target_daily_dose")
    baseline = None if baseline_daily_dose is None else _amount(baseline_daily_dose, "baseline_daily_dose")
    if administration_mode not in ("once", "twice_equal"):
        raise ValueError("administration_mode must be 'once' or 'twice_equal'")
    _check_composition_flag(include_composition)
    unit, coins, strengths = _pieces(permissible_pieces)
    administrations = 1 if administration_mode == "once" else 2
    daily_unit = unit * administrations
    in_units = target / daily_unit

    def key(candidate: int) -> tuple[Fraction, Fraction, int]:
        daily = candidate * daily_unit
        # The final key resolves equal baseline distances toward the higher dose.
        return (abs(daily - target), abs(daily - baseline) if baseline is not None else Fraction(0), -candidate)

    # Exact zero or a single piece needs no DP. Below the smallest piece, zero
    # and that one piece are the only possible nearest neighbors.
    exact_direct = in_units.denominator == 1 and (in_units.numerator == 0 or in_units.numerator in coins)
    below_first = in_units < coins[0]
    direct = exact_direct or below_first
    predecessors = None
    if exact_direct:
        selected = in_units.numerator
    elif below_first:
        selected = min((0, coins[0]), key=key)
    else:
        floor_target = in_units.numerator // in_units.denominator
        # A multiple of the smallest piece is necessarily achievable above target.
        smallest = coins[0]
        upper = ((in_units.numerator + in_units.denominator * smallest - 1)
                 // (in_units.denominator * smallest)) * smallest
        reachable, predecessors = _table(upper, coins, include_composition)
        lower = floor_target
        while not reachable[lower]:
            lower -= 1
        higher = floor_target if in_units.denominator == 1 else floor_target + 1
        while not reachable[higher]:
            higher += 1
        candidates = (lower, higher)
        selected = min(candidates, key=key)
    rounded = selected * daily_unit
    per_administration = selected * unit
    if include_composition:
        if direct:
            one = () if selected == 0 else (PieceCount(strengths[coins.index(selected)], 1),)
        else:
            assert predecessors is not None
            one = _composition(selected, coins, strengths, predecessors)
        compositions = tuple(one for _ in range(administrations))
    else:
        compositions = None
    larger_reduction = None
    if baseline is not None:
        larger_reduction = max(Fraction(0), baseline - rounded) > max(Fraction(0), baseline - target)
    return RoundedDose(
        target_daily_dose=target_daily_dose,
        rounded_daily_dose=_as_decimal(rounded),
        per_administration_dose=_as_decimal(per_administration),
        administration_compositions=compositions,
        is_rounded=rounded != target,
        rounded_below_target=rounded < target,
        larger_than_planned_reduction=larger_reduction,
        nonzero_target_rounded_to_zero=target > 0 and rounded == 0,
    )


def validate_manual_unequal_bid(
    administrations: Sequence[Decimal],
    expected_daily_total: Decimal,
    permissible_pieces: Sequence[Decimal],
    *,
    include_composition: bool = True,
) -> ManualRegimenValidation:
    """Validate two explicitly supplied doses and their exact total, unchanged.

    This function also accepts equal or zero amounts, but never rounds a dose or
    distributes a total. Invalid clinical choices still require clinician
    judgment; this checks arithmetic and supplied piece-combination feasibility
    only. An exact calculation exceeding safety limits raises instead of
    pretending that a dose is unrepresentable.
    """
    if not isinstance(administrations, Sequence) or isinstance(administrations, (str, bytes, bytearray)):
        raise TypeError("administrations must be a sequence of two Decimals")
    if len(administrations) != 2:
        raise ValueError("exactly two explicit administrations are required")
    doses = tuple(_amount(value, f"administrations[{i}]") for i, value in enumerate(administrations))
    expected = _amount(expected_daily_total, "expected_daily_total")
    _check_composition_flag(include_composition)
    unit, coins, strengths = _pieces(permissible_pieces)
    units = tuple(dose / unit for dose in doses)
    # Zero and a single verified piece are directly known. Nonintegral and
    # positive states below the smallest piece are directly impossible.
    search_states = [value.numerator for value in units
                     if value.denominator == 1 and value.numerator >= coins[0]
                     and value.numerator not in coins]
    upper = max(search_states, default=0)
    reachable, predecessors = _table(upper, coins, include_composition)
    entries = []
    for original, value in zip(administrations, units):
        composition = None
        state = value.numerator
        if value.denominator != 1:
            possible = False
        elif state == 0:
            possible = True
            if include_composition:
                composition = ()
        elif state in coins:
            possible = True
            if include_composition:
                composition = (PieceCount(strengths[coins.index(state)], 1),)
        elif state < coins[0]:
            possible = False
        else:
            possible = bool(reachable[state])
            if possible and include_composition:
                assert predecessors is not None
                composition = _composition(state, coins, strengths, predecessors)
        entries.append(ManualAdministration(original, possible, composition))
    actual = sum(doses, Fraction(0))
    matches = actual == expected
    return ManualRegimenValidation(
        administrations=(entries[0], entries[1]),
        expected_daily_total=expected_daily_total,
        actual_daily_total=_as_decimal(actual),
        total_matches=matches,
        valid=matches and all(entry.representable for entry in entries),
    )

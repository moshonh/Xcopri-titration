"""Purely numerical AM/PM splitting; this is not a clinical recommendation.

The caller, not this module, chooses the timing mode for each medication.  No
formulation, frequency, or dosing schedule is inferred here.
"""

from collections.abc import Iterable
from decimal import Decimal, InvalidOperation, MIN_ETINY
from typing import TypeAlias


PeriodValues: TypeAlias = tuple[Decimal | None, ...]
ManualValue: TypeAlias = Decimal | int | float | str | None

_PERIODS = 6
_EMPTY: PeriodValues = (None,) * _PERIODS


def _six(values: Iterable[object], name: str) -> tuple[object, ...]:
    """Materialize six period entries, rejecting scalar strings and bytes."""
    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{name} must be an iterable of six period values")
    try:
        result = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of six period values") from exc
    if len(result) != _PERIODS:
        raise ValueError(f"{name} must contain exactly six period values")
    return result


def _check_amount(value: Decimal, name: str) -> Decimal:
    if not value.is_finite() or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return value


def _daily_values(values: Iterable[Decimal | None]) -> PeriodValues:
    result: list[Decimal | None] = []
    for i, value in enumerate(_six(values, "daily_values"), 1):
        if value is None:
            result.append(None)
        elif isinstance(value, Decimal):
            result.append(_check_amount(value, f"daily_values[{i - 1}]"))
        else:
            raise TypeError(f"daily_values[{i - 1}] must be a Decimal or None")
    return tuple(result)


def _manual_values(values: Iterable[ManualValue] | None, name: str) -> PeriodValues:
    if values is None:
        return _EMPTY
    result: list[Decimal | None] = []
    for i, value in enumerate(_six(values, name)):
        label = f"{name}[{i}]"
        if value is None or (isinstance(value, str) and not value.strip()):
            result.append(None)
            continue
        if isinstance(value, bool) or not isinstance(value, (Decimal, int, float, str)):
            raise TypeError(f"{label} must be a decimal value or blank")
        try:
            # In particular, convert floats through their decimal text, not their
            # binary expansion. Decimal construction is independent of precision.
            amount = value if isinstance(value, Decimal) else Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"{label} must be a decimal value or blank") from exc
        result.append(_check_amount(amount, label))
    return tuple(result)


def _half(value: Decimal) -> Decimal:
    """Divide a finite nonnegative Decimal by two without using the context."""
    sign, digits, exponent = value.as_tuple()
    quotient: list[int] = []
    remainder = 0
    for digit in digits:
        digit, remainder = divmod(remainder * 10 + digit, 2)
        quotient.append(digit)
    if remainder:
        quotient.append(5)
        exponent -= 1
        if exponent < MIN_ETINY:
            raise ValueError("the exact half is outside Decimal's representable exponent range")
    return Decimal((sign, tuple(quotient), exponent))


def _nonzero_digits(value: Decimal) -> dict[int, int]:
    """Map decimal place (10**place) to nonzero digits, ignoring signed zero."""
    _, digits, exponent = value.as_tuple()
    last_place = exponent + len(digits) - 1
    return {last_place - i: digit for i, digit in enumerate(digits) if digit}


def _sum_equals(first: Decimal, second: Decimal, total: Decimal) -> bool:
    """Compare an exact sum without a Decimal context or large exponent padding."""
    left, right, expected = map(_nonzero_digits, (first, second, total))
    positions = sorted(left.keys() | right.keys() | expected.keys())
    carry = 0
    carry_place = None
    for place in positions:
        # A carry in an absent place would produce a 1 where total has a 0.
        if carry and place != carry_place:
            return False
        carry, digit = divmod(left.get(place, 0) + right.get(place, 0) + carry, 10)
        if digit != expected.get(place, 0):
            return False
        carry_place = place + 1
    return carry == 0


def split_daily_values(
    daily_values: Iterable[Decimal | None],
    mode: str,
    *,
    morning: Iterable[ManualValue] | None = None,
    evening: Iterable[ManualValue] | None = None,
) -> tuple[PeriodValues, PeriodValues]:
    """Return ``(AM, PM)``, each a six-tuple of Decimal or None.

    ``daily_values`` contains exactly six nonnegative, finite Decimals or None.
    The caller must explicitly select one of these modes:

    * ``"unspecified"``: return all None, without inferring a schedule.
    * ``"equal"``: return exactly half of each known total for both periods.
    * ``"manual"``: return the supplied AM and PM values, retaining blanks.

    Each manual argument is an iterable of exactly six values, or None to leave
    the entire side blank. Entries may be None, an empty/whitespace-only string
    (blank), Decimal, int, float, or numeric string. Booleans are not amounts.
    Floats are converted via ``Decimal(str(value))``. A blank is never filled
    by subtraction and is distinct from zero.

    Whenever manual entries are supplied, even in a non-manual mode, they are
    validated: no entry may be specified for an unknown total, a partial entry
    may not exceed its total, and a complete pair must sum exactly to its total.
    Valid manual entries are ignored by ``unspecified`` and ``equal`` modes.

    Invalid modes, lengths, amounts, or inconsistent totals raise ValueError;
    invalid container or entry types raise TypeError. Arithmetic and comparison
    do not depend on the ambient Decimal precision, rounding, or traps.
    An exact half outside Decimal's representable exponent range raises
    ValueError rather than rounding or producing a nonfinite value.
    This helper is purely numerical and makes no clinical recommendation.
    """
    if not isinstance(mode, str) or mode not in ("unspecified", "equal", "manual"):
        raise ValueError("mode must be 'unspecified', 'equal', or 'manual'")
    totals = _daily_values(daily_values)
    am = _manual_values(morning, "morning")
    pm = _manual_values(evening, "evening")

    for i, (total, first, second) in enumerate(zip(totals, am, pm)):
        if total is None:
            if first is not None or second is not None:
                raise ValueError(f"period {i + 1}: manual amounts require a daily total")
            continue
        if (first is not None and first > total) or (second is not None and second > total):
            raise ValueError(f"period {i + 1}: manual amount exceeds daily total")
        if first is not None and second is not None and not _sum_equals(first, second, total):
            raise ValueError(f"period {i + 1}: manual amounts must equal daily total")

    if mode == "unspecified":
        return _EMPTY, _EMPTY
    if mode == "equal":
        halves = tuple(None if total is None else _half(total) for total in totals)
        return halves, halves
    return am, pm

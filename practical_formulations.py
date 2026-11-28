"""Clinician-entered product data for unvalidated dose-review calculations.

This module does not assert registration, commercial supply, bioequivalence,
scoring, permitted subdivision, dose accuracy, or clinical suitability.  It
validates structural consistency of the clinician's independently verified
inputs.  Missing attestation or incomplete product details fail closed.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation, localcontext
import re
from product_catalog import CATALOG


SOLID_TYPES = frozenset({
    'Immediate-release tablet', 'Film-coated tablet', 'Modified-release tablet',
    'Enteric-coated tablet', 'Capsule',
})
TABLET_TYPES = frozenset({
    'Immediate-release tablet', 'Film-coated tablet', 'Modified-release tablet',
})
MAX_UNITS = 16


@dataclass(frozen=True)
class Formulation:
    name: str
    kind: str
    reference: str
    whole_strengths: tuple[Decimal, ...]
    halves: tuple[Decimal, ...]
    quarters: tuple[Decimal, ...]
    pieces: tuple[Decimal, ...]
    concentration: Decimal | None = None
    increment: Decimal | None = None
    catalog_id: str = ''
    catalog_source: str = ''
    catalog_handling: str = ''
    rounding_policy: str = 'nearest'

    def description_for_piece(self, piece: Decimal) -> str:
        """Describe a mathematical piece without implying label approval."""
        if self.kind in {'Oral solution', 'Oral suspension'}:
            return f'{self.increment} mL (at {self.concentration} mg/mL)'
        # Prefer a whole unit to avoid suggesting unnecessary subdivision.
        if piece in self.whole_strengths:
            return f'whole {piece} mg unit'
        for strength in self.halves:
            if _div(strength, 2) == piece:
                return f'half of {strength} mg tablet'
        for strength in self.quarters:
            if _div(strength, 4) == piece:
                return f'quarter of {strength} mg tablet'
        raise ValueError('piece is not in the clinician-entered product data')


def _number(value: str, label: str) -> Decimal:
    if not isinstance(value, str) or not value.strip() or len(value) > 50:
        raise ValueError(f'{label}: enter a positive finite decimal')
    try:
        number = Decimal(value.strip())
    except InvalidOperation:
        raise ValueError(f'{label}: enter a positive finite decimal') from None
    if (not number.is_finite() or number <= 0 or number > Decimal('1000000')
            or number.as_tuple().exponent < -6
            or len(number.as_tuple().digits) > 16):
        raise ValueError(f'{label}: enter a positive finite decimal of at most six decimal places')
    return number


def _values(value: str, label: str, *, required: bool) -> tuple[Decimal, ...]:
    if not isinstance(value, str):
        raise ValueError(f'{label}: enter comma-separated strengths')
    if not value.strip():
        if required:
            raise ValueError(f'{label}: specify at least one strength')
        return ()
    fields = value.split(',')
    if len(fields) > MAX_UNITS:
        raise ValueError(f'{label}: at most {MAX_UNITS} strengths may be entered')
    parsed = tuple(_number(field, label) for field in fields)
    if len(set(parsed)) != len(parsed):
        raise ValueError(f'{label}: repeated strengths are not permitted')
    return tuple(sorted(parsed))


def _div(number: Decimal, divisor: int) -> Decimal:
    with localcontext() as context:
        context.prec = 50
        return number / divisor


def _catalog_check(product: Formulation, drug: str | None, data: dict) -> Formulation:
    """Validate catalog constraints when a specific reviewed product was selected."""
    product_id = data.get('catalog_id') or ''
    if not product_id:
        for known_drug, entries in CATALOG.items():
            for entry in entries:
                brand = entry['label'].split()[0]
                if re.search(r'(?<![\w])' + re.escape(brand) + r'(?![\w])', product.name, re.IGNORECASE):
                    if known_drug != drug:
                        raise ValueError(f'this known product name is associated with {known_drug}, not the selected medication; verify the active ingredient and exact product')
                    raise ValueError('this brand has a reviewed catalog entry; select the exact product in the reviewed-product selector. If this is a different formulation of the same brand, it requires separate catalog review before use in this tool')
        return product  # clinician-entered outside reviewed catalog; never represented as verified by app
    matches = [entry for entry in CATALOG.get(drug, ()) if entry['id'] == product_id]
    if len(matches) != 1:
        raise ValueError('the selected product is not in this medication’s reviewed catalog')
    item = matches[0]
    if product.name != item['label'] or product.kind != item['type']:
        raise ValueError('product name or release form does not match the selected catalog entry')
    allowed_whole = {Decimal(x) for x in item['strengths']}
    allowed_halves = {Decimal(x) for x in item['allowed_halves']}
    allowed_quarters = {Decimal(x) for x in item['allowed_quarters']}
    if (not set(product.whole_strengths).issubset(allowed_whole)
            or not set(product.halves).issubset(allowed_halves)
            or not set(product.quarters).issubset(allowed_quarters)):
        raise ValueError('one or more strengths or dose divisions are not supported for this exact catalog product; check its leaflet')
    if item['concentration'] and product.concentration != Decimal(item['concentration']):
        raise ValueError('the concentration does not match the selected catalog product')
    return replace(product, catalog_id=product_id, catalog_source=item['source'],
                   catalog_handling=item['handling'], rounding_policy=item['rounding_policy'])


def parse_formulation(data: dict, drug: str | None = None) -> Formulation:
    """Validate and capture explicit clinician-entered details, never invent them.

    Accepted shape matches xcopri_app's selected[drug]['formulation'] object.
    A whole product strength may only be listed for halves or quarters where the
    clinician explicitly confirms permission for that exact product and strength.
    Capsules and enteric-coated units cannot be split by this tool.  A liquid
    needs the actual concentration and a separately confirmed deliverable syringe
    increment; neither is inferred.  The confirmation is self-attestation, not
    independent verification by this software.  Invalid input raises ValueError.
    """
    if not isinstance(data, dict) or data.get('confirmed') is not True:
        raise ValueError('the clinician must confirm the exact local product, its label, supply and allowed subdivision')
    name = str(data.get('name') or '').strip()
    kind = str(data.get('type') or '').strip()
    reference = str(data.get('reference') or '').strip()
    if not name:
        raise ValueError('enter the exact product name, manufacturer and release form')
    if not reference:
        raise ValueError('enter the product label or pharmacist source and review date')
    if kind in {'Oral solution', 'Oral suspension'}:
        concentration = _number(data.get('concentration', ''), 'solution concentration (mg/mL)')
        increment = _number(data.get('increment', ''), 'deliverable syringe increment (mL)')
        with localcontext() as context:
            context.prec = 50
            piece = concentration * increment
        if piece <= 0 or not piece.is_finite():
            raise ValueError('invalid solution dose increment')
        return _catalog_check(Formulation(name, kind, reference, (), (), (), (piece,), concentration, increment), drug, data)
    if kind not in SOLID_TYPES:
        raise ValueError('specify the actual formulation and release type')
    whole = _values(data.get('strengths', ''), 'whole unit strengths (mg)', required=True)
    halves = _values(data.get('halves', ''), 'strengths permitted as halves', required=False)
    quarters = _values(data.get('quarters', ''), 'strengths permitted as quarters', required=False)
    if kind not in TABLET_TYPES and (halves or quarters):
        raise ValueError('this tool does not split capsules or enteric-coated units')
    if not set(halves).issubset(whole) or not set(quarters).issubset(whole):
        raise ValueError('each split strength must be one of the explicitly entered whole strengths')
    units = set(whole)
    units.update(_div(s, 2) for s in halves)
    units.update(_div(s, 4) for s in quarters)
    return _catalog_check(Formulation(name, kind, reference, whole, halves, quarters,
                                      tuple(sorted(units, reverse=True))), drug, data)

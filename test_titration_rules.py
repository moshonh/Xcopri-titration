"""Unit tests for unvalidated, non-prescriptive dose-review calculations."""

import unittest
from decimal import Decimal, localcontext

from titration_rules import (
    CLOBAZAM_ABOVE_20_FACTORS,
    CLOBAZAM_AT_MOST_20_FACTORS,
    LAMOTRIGINE_FACTORS,
    PERIOD_LABELS,
    SCB_DRUGS,
    SCB_TAPER_FACTORS,
    build_schedules,
)


D = Decimal


class TaperTests(unittest.TestCase):
    def test_each_original_percentage_schedule_uses_baseline_not_previous_value(self):
        expected = {
            "Lacosamide": ["100", "75", "50", "25", "0", "0"],
            "Oxcarbazepine": ["100", "80", "60", "40", "20", "0"],
            "Eslicarbazepine acetate (ESL)": ["100", "80", "60", "40", "20", "0"],
            "Phenytoin": ["100", "75", "50", "25", "0", "0"],
            "Lamotrigine": ["100", "75", "50", "25", "0", "0"],
            "Zonisamide": ["100", "80", "60", "40", "20", "0"],
            "Rufinamide": ["100", "80", "60", "40", "20", "0"],
        }
        self.assertEqual(set(SCB_TAPER_FACTORS), set(expected))
        self.assertEqual(len(SCB_DRUGS), 8)
        for drug, doses in expected.items():
            with self.subTest(drug=drug):
                result = build_schedules({drug: "100"}, taper_drug=drug, automatic_scope_confirmed=True)[drug]
                self.assertEqual(result.values, tuple(map(D, doses)))
                self.assertEqual(result.rule_values, SCB_TAPER_FACTORS[drug])
                self.assertEqual(result.rule_kind, "baseline_factor")
                self.assertEqual(result.source_code, "author_scb_taper")
                self.assertEqual(len(result.period_reasons), 6)
                self.assertEqual(result.period_labels, PERIOD_LABELS)
                self.assertTrue(result.requires_clinician_review)

    def test_carbamazepine_step_and_zero_floor(self):
        result = build_schedules({"Carbamazepine": "650.25"}, taper_drug="Carbamazepine", automatic_scope_confirmed=True)["Carbamazepine"]
        self.assertEqual(result.values, tuple(map(D, ["650.25", "450.25", "250.25", "50.25", "0", "0"])))
        self.assertEqual(result.rule_kind, "fixed_step")
        self.assertEqual(result.rule_values, tuple(map(D, ["0", "200", "400", "600", "800", "1000"])))
        self.assertEqual(result.source_code, "author_scb_taper")

    def test_carbamazepine_equal_and_smaller_than_step(self):
        for baseline, expected in [("200", (D("200"), D("0"), D("0"), D("0"), D("0"), D("0"))),
                                   ("1.01", (D("1.01"), D("0"), D("0"), D("0"), D("0"), D("0")))]:
            with self.subTest(baseline=baseline):
                result = build_schedules({"Carbamazepine": baseline}, taper_drug="Carbamazepine", automatic_scope_confirmed=True)
                self.assertEqual(result["Carbamazepine"].values, expected)

    def test_lamotrigine_taper_never_uses_increase_schedule(self):
        result = build_schedules({"Lamotrigine": "101"}, taper_drug="Lamotrigine", automatic_scope_confirmed=True)["Lamotrigine"]
        self.assertEqual(result.values, tuple(map(D, ["101", "75.75", "50.50", "25.25", "0", "0"])))
        self.assertEqual(result.source_code, "author_scb_taper")
        self.assertTrue(all(dose <= D("101") for dose in result.values))
        self.assertNotEqual(result.rule_values, LAMOTRIGINE_FACTORS)

    def test_unsupported_selected_taper_has_no_invented_rule(self):
        for drug in ("Levetiracetam", "Unknown ASM"):
            with self.subTest(drug=drug):
                result = build_schedules({drug: "99"}, taper_drug=drug, automatic_scope_confirmed=True)[drug]
                self.assertEqual(result.values, (None,) * 6)
                self.assertEqual(result.source_code, "no_automatic_rule")
                self.assertIn("physician-entered", result.reason)
                self.assertEqual(result.rule_values, ())

    def test_taper_requires_selection(self):
        with self.assertRaises(ValueError):
            build_schedules({"Clobazam": "24"}, taper_drug="Lamotrigine", automatic_scope_confirmed=True)


class DefaultRulesTests(unittest.TestCase):
    def test_lamotrigine_increase_uses_baseline(self):
        result = build_schedules({"Lamotrigine": "103.2"}, automatic_scope_confirmed=True)["Lamotrigine"]
        self.assertEqual(result.values, tuple(map(D, ["103.2", "103.2", "118.68", "118.68", "134.16", "134.16"])))
        self.assertEqual(result.rule_values, LAMOTRIGINE_FACTORS)
        self.assertEqual(result.source_code, "author_lamotrigine")
        self.assertIn("clinician", result.reason)

    def test_clobazam_threshold_strictly_greater_than_twenty(self):
        for baseline in ("0.01", "10", "19.9999", "20", "20.0000"):
            with self.subTest(baseline=baseline):
                result = build_schedules({"Clobazam": baseline}, automatic_scope_confirmed=True)["Clobazam"]
                self.assertEqual(result.values, (D(baseline),) * 6)
                self.assertEqual(result.rule_values, CLOBAZAM_AT_MOST_20_FACTORS)
                self.assertIn("clinical assessment", result.reason)
                self.assertIn("not a validated safety cutoff", result.cautions[-1])
        result = build_schedules({"Clobazam": "20.0001"}, automatic_scope_confirmed=True)["Clobazam"]
        self.assertEqual(result.values, tuple(map(D, ["20.0001", "20.0001", "15.000075", "15.000075", "10.00005", "10.00005"])))
        self.assertEqual(result.rule_values, CLOBAZAM_ABOVE_20_FACTORS)
        self.assertEqual(result.source_code, "author_clobazam")

    def test_explicit_no_taper_keeps_separate_defaults(self):
        result = build_schedules({"Lamotrigine": "100", "Clobazam": "30", "Lacosamide": "200"}, taper_drug=None, automatic_scope_confirmed=True)
        self.assertEqual(result["Lamotrigine"].source_code, "author_lamotrigine")
        self.assertEqual(result["Clobazam"].source_code, "author_clobazam")
        self.assertEqual(result["Lacosamide"].source_code, "no_automatic_rule")
        self.assertEqual(result["Lacosamide"].values, (None,) * 6)

    def test_selected_clobazam_uses_confirmed_threshold_and_can_be_overridden(self):
        above = build_schedules({"Clobazam": "30"}, taper_drug="Clobazam", automatic_scope_confirmed=True)["Clobazam"]
        self.assertEqual(above.values, tuple(map(D, ["30", "30", "22.5", "22.5", "15", "15"])))
        boundary = build_schedules({"Clobazam": "20"}, taper_drug="Clobazam", automatic_scope_confirmed=True)["Clobazam"]
        self.assertEqual(boundary.values, (D("20"),) * 6)
        self.assertIn("physician-entered", boundary.reason)
        manual = build_schedules({"Clobazam": "20"}, taper_drug="Clobazam", manual_schedules={"Clobazam": [20, 19, 18, 17, 16, 15]}, automatic_scope_confirmed=True)["Clobazam"]
        self.assertEqual(manual.source_code, "physician_manual")
        self.assertEqual(manual.values[-1], D(15))

    def test_inducer_taper_caution_on_lamotrigine(self):
        result = build_schedules({"Carbamazepine": "500", "Lamotrigine": "100"}, taper_drug="Carbamazepine", automatic_scope_confirmed=True)
        self.assertIn("inducer", result["Lamotrigine"].cautions[-1])
        self.assertEqual(result["Lamotrigine"].source_code, "author_lamotrigine")

    def test_absent_or_zero_baseline_never_generates_even_rule_zero(self):
        for drug in ("Lacosamide", "Carbamazepine", "Lamotrigine", "Clobazam"):
            for baseline in (None, 0, "0.000"):
                taper = drug if drug in SCB_DRUGS else None
                with self.subTest(drug=drug, baseline=baseline):
                    result = build_schedules({drug: baseline}, taper_drug=taper, automatic_scope_confirmed=True)[drug]
                    self.assertEqual(result.values, (None,) * 6)
                    self.assertEqual(result.source_code, "baseline_unavailable")
                    self.assertIn("missing" if baseline is None else "zero", result.reason)

    def test_missing_scope_prevents_automatic_values_for_each_rule(self):
        for drug, taper in (("Lacosamide", "Lacosamide"), ("Carbamazepine", "Carbamazepine"), ("Lamotrigine", None), ("Clobazam", None)):
            with self.subTest(drug=drug):
                result = build_schedules({drug: "100"}, taper_drug=taper)[drug]
                self.assertEqual(result.source_code, "scope_unconfirmed")
                self.assertEqual(result.values, (None,) * 6)
                self.assertEqual(result.rule_values, ())

    def test_only_selected_drugs_are_returned(self):
        self.assertEqual(build_schedules({}), {})
        self.assertEqual(set(build_schedules({"Clobazam": "20"}, automatic_scope_confirmed=True)), {"Clobazam"})


class ManualTests(unittest.TestCase):
    def test_selected_scb_manual_override_replaces_taper_without_fallback(self):
        result = build_schedules({"Lacosamide": "100"}, taper_drug="Lacosamide", manual_schedules={"Lacosamide": ["95.01", None, "0", "82.1", None, None]}, automatic_scope_confirmed=True)["Lacosamide"]
        self.assertEqual(result.values, (D("95.01"), None, D("0"), D("82.1"), None, None))
        self.assertEqual(result.source_code, "physician_manual")
        self.assertIsNone(result.rule_kind)
        self.assertEqual(result.rule_values, ())
        self.assertIn("Not entered", result.period_reasons[1])
        self.assertIn("Entered", result.period_reasons[2])

    def test_manual_override_for_lamotrigine_and_clobazam_supersedes_defaults(self):
        result = build_schedules({"Lamotrigine": "100", "Clobazam": "25"}, manual_schedules={"Lamotrigine": ["100", "98", "97", "96", "95", "0"], "Clobazam": ["25", "22", "20", "18", "16", "10"]}, automatic_scope_confirmed=True)
        self.assertEqual(result["Lamotrigine"].source_code, "physician_manual")
        self.assertEqual(result["Lamotrigine"].values[-1], D("0"))
        self.assertEqual(result["Clobazam"].source_code, "physician_manual")
        self.assertEqual(result["Clobazam"].values[2], D("20"))
        self.assertEqual(result["Lamotrigine"].rule_values, ())
        self.assertEqual(result["Clobazam"].rule_values, ())

    def test_manual_all_blank_does_not_fall_back(self):
        result = build_schedules({"Clobazam": "30"}, manual_schedules={"Clobazam": [None] * 6}, automatic_scope_confirmed=True)["Clobazam"]
        self.assertEqual(result.values, (None,) * 6)
        self.assertEqual(result.source_code, "physician_manual")

    def test_manual_can_be_recorded_with_missing_baseline_without_auto(self):
        for baseline in (None, 0):
            with self.subTest(baseline=baseline):
                result = build_schedules({"Clobazam": baseline}, manual_schedules={"Clobazam": [1, None, 0, None, None, None]})["Clobazam"]
                self.assertEqual(result.values, (D(1), None, D(0), None, None, None))
                self.assertEqual(result.source_code, "physician_manual")
                self.assertIn("Baseline is missing or zero", result.cautions[-1])

    def test_manual_can_be_recorded_when_automatic_scope_unconfirmed(self):
        result = build_schedules({"Lacosamide": 100, "Clobazam": 25}, taper_drug="Lacosamide", manual_schedules={"Lacosamide": [100, 80, 60, 40, 20, 0]})
        self.assertEqual(result["Lacosamide"].source_code, "physician_manual")
        self.assertEqual(result["Clobazam"].source_code, "scope_unconfirmed")
        self.assertEqual(result["Clobazam"].values, (None,) * 6)

    def test_manual_unsupported_taper_is_preserved(self):
        result = build_schedules({"Other ASM": 30}, taper_drug="Other ASM", manual_schedules={"Other ASM": [30, 29, 25, 22, 10, 0]}, automatic_scope_confirmed=True)["Other ASM"]
        self.assertEqual(result.values, tuple(map(D, ["30", "29", "25", "22", "10", "0"])))
        self.assertEqual(result.source_code, "physician_manual")

    def test_selected_lamotrigine_taper_manual_nonincrease_and_missing_period(self):
        result = build_schedules({"Lamotrigine": 100}, taper_drug="Lamotrigine", manual_schedules={"Lamotrigine": [100, None, 75, 75, 30, 0]}, automatic_scope_confirmed=True)["Lamotrigine"]
        self.assertEqual(result.source_code, "physician_manual")
        self.assertEqual(result.values, (D(100), None, D(75), D(75), D(30), D(0)))

    def test_selected_lamotrigine_taper_manual_increase_rejected(self):
        for values in ([101, 100, 90, 80, 70, 0], [100, 90, None, 91, 80, 0], [100, 90, 80, 70, 0, 1]):
            with self.subTest(values=values), self.assertRaisesRegex(ValueError, "cannot increase"):
                build_schedules({"Lamotrigine": 100}, taper_drug="Lamotrigine", manual_schedules={"Lamotrigine": values}, automatic_scope_confirmed=True)

    def test_selected_lamotrigine_manual_requires_positive_baseline_to_check_increase(self):
        for baseline in (None, 0):
            with self.subTest(baseline=baseline), self.assertRaisesRegex(ValueError, "positive lamotrigine baseline"):
                build_schedules({"Lamotrigine": baseline}, taper_drug="Lamotrigine", manual_schedules={"Lamotrigine": [None, None, 0, None, None, None]})
        result = build_schedules({"Lamotrigine": None}, taper_drug="Lamotrigine", manual_schedules={"Lamotrigine": [None] * 6})["Lamotrigine"]
        self.assertEqual(result.values, (None,) * 6)

    def test_no_taper_manual_lamotrigine_may_include_physician_entered_increases(self):
        result = build_schedules({"Lamotrigine": 100}, manual_schedules={"Lamotrigine": [100, 120, 140, 140, 140, 140]})["Lamotrigine"]
        self.assertEqual(result.values[1], D(120))
        self.assertEqual(result.source_code, "physician_manual")

    def test_manual_six_slots_required_and_unknown_key_rejected(self):
        for values in ([0] * 5, [0] * 7, "100", 42, None):
            with self.subTest(values=values), self.assertRaises(ValueError):
                build_schedules({"Clobazam": 20}, manual_schedules={"Clobazam": values})
        with self.assertRaises(ValueError):
            build_schedules({"Clobazam": 20}, manual_schedules={"Lacosamide": [0] * 6})


class ArithmeticAndValidationTests(unittest.TestCase):
    def test_exact_long_decimal_multiplication_ignores_ambient_context(self):
        baseline = "123456789012345678901234567890123456789.123456789012345678901"
        expected = "141975307364197530736419753073641975307.49197530736419753073615"
        with localcontext() as context:
            context.prec = 3
            context.Emax = 2
            context.Emin = -2
            result = build_schedules({"Lamotrigine": baseline}, automatic_scope_confirmed=True)["Lamotrigine"]
        self.assertEqual(result.values[2], D(expected))

    def test_exact_long_decimal_subtraction_ignores_ambient_context(self):
        baseline = "10000000000000000000000000000000000000000000.123456789012345678901"
        with localcontext() as context:
            context.prec = 3
            context.Emax = 2
            context.Emin = -2
            result = build_schedules({"Carbamazepine": baseline}, taper_drug="Carbamazepine", automatic_scope_confirmed=True)["Carbamazepine"]
        self.assertEqual(result.values[1], D("9999999999999999999999999999999999999999800.123456789012345678901"))

    def test_theoretical_not_rounded_or_split(self):
        result = build_schedules({"Lacosamide": "101.3"}, taper_drug="Lacosamide", automatic_scope_confirmed=True)["Lacosamide"]
        self.assertEqual(result.values[1], D("75.975"))
        self.assertIn("unrounded", result.cautions[1])
        self.assertIn("no formulation", result.cautions[1])
        self.assertEqual(result.unit, "mg/day")

    def test_invalid_baselines_and_manual_entries_rejected(self):
        invalid = [True, False, "", "   ", "not a number", "NaN", "sNaN", "Infinity", "-Infinity", -1, "-0.0001", float("nan"), float("inf"), float("-inf"), [], {}, D("-0.01"), "1e1001", "1e-1001"]
        for value in invalid:
            with self.subTest(kind="baseline", value=value), self.assertRaises(ValueError):
                build_schedules({"Lamotrigine": value}, automatic_scope_confirmed=True)
            with self.subTest(kind="manual", value=value), self.assertRaises(ValueError):
                build_schedules({"Clobazam": 20}, manual_schedules={"Clobazam": [1, 1, value, 1, 1, 1]})

    def test_float_and_scientific_notation_parsing(self):
        result = build_schedules({"Clobazam": 20.0, "Lamotrigine": "1e2"}, automatic_scope_confirmed=True)
        self.assertEqual(result["Clobazam"].baseline, D("20.0"))
        self.assertEqual(result["Lamotrigine"].values[2], D("115"))

    def test_signed_manual_zero_is_explicit_not_a_blank(self):
        result = build_schedules({"Clobazam": 20}, manual_schedules={"Clobazam": ["-0", None, 0, None, None, None]})["Clobazam"]
        self.assertEqual(result.values[0], D("0"))
        self.assertFalse(result.values[0].is_signed())
        self.assertIsNone(result.values[1])

    def test_bad_scope_and_bad_mappings_rejected(self):
        for value in (None, 0, 1, "True"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_schedules({"Clobazam": 20}, automatic_scope_confirmed=value)
        for baselines in (None, [], "x"):
            with self.subTest(baselines=baselines), self.assertRaises(ValueError):
                build_schedules(baselines)
        with self.assertRaises(ValueError):
            build_schedules({"Clobazam": 20}, manual_schedules=[])
        for name in ("", "  ", None, 123):
            with self.subTest(name=name), self.assertRaises(ValueError):
                build_schedules({name: 5})

    def test_warning_and_provenance_do_not_claim_consensus(self):
        result = build_schedules({"Clobazam": 20}, automatic_scope_confirmed=True)["Clobazam"]
        self.assertIn("Unvalidated author-defined", result.source_label)
        self.assertIn("not a prescription", result.cautions[0])
        self.assertIn("not a clinically validated dose", result.cautions[0])
        self.assertTrue(all(isinstance(x, (D, type(None))) for x in result.values))


if __name__ == "__main__":
    unittest.main()

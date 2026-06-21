"""
Xcopri (Cenobamate) Clinical Transition & Interaction Tool
===========================================================
ON-PREMISE VERSION — No data leaves this machine.
All computation is local. No internet connection required after installation.

Evidence-based on 21 peer-reviewed publications and regulatory documents (2019-2026):

[1]  Sperling MR et al. (2020). Epilepsia. doi:10.1111/epi.16525
[2]  Krauss GL et al. (2020). Lancet Neurol. doi:10.1016/S1474-4422(19)30399-0
[3]  Roberti R et al. (2021). CNS Drugs. doi:10.1007/s40263-021-00819-8
[4]  Smith MC et al. (2022). Neurol Ther. doi:10.1007/s40120-022-00400-5
[5]  Steinhoff BJ et al. (2024). Ther Adv Neurol Disord. doi:10.1177/17562864241256733
[6]  Osborn M & Abou-Khalil B (2023). Epilepsy Behav. doi:10.1016/j.yebeh.2023.109156
[7]  Schoretsanitis G et al. (2022). Expert Opin Drug Metab Toxicol. doi:10.1080/17425255.2022.2106214
[8]  Karazniewicz-Lada M et al. (2021). Int J Mol Sci. doi:10.3390/ijms22179582
[9]  Operto FF et al. (2025). Front Pharmacol. doi:10.3389/fphar.2025.1668382
[10] Krauss GL et al. (2025). Epilepsia. doi:10.1111/epi.18304
[11] Zaccara G et al. (2021). Neuropsychiatr Dis Treat. doi:10.2147/NDT.S281490
[12] Johannessen Landmark C et al. (2026). Epilepsia. doi:10.1002/epi.70184
[13] Charlier B et al. (2026). Pharmaceutics. doi:10.3390/pharmaceutics18010092
[14] Cohen H et al. (2026). Epileptic Disord. doi:10.1002/epd2.70232
[15] Samanta D (2025). Epilepsy Behav. doi:10.1016/j.yebeh.2025.110787
[16] Abou-Khalil BW (2022). Continuum. doi:10.1212/CON.0000000000001104
[17] Ciullo I et al. (2026). Epilepsia Open. doi:10.1002/epi4.70261
[18] US FDA. XCOPRI prescribing information [updated August 2025 — hepatotoxicity].
[19] European Medicines Agency. Ontozry SPC (2021).
[20] Greene SA et al. (2024). PK study of cenobamate enzyme effects up to 200 mg/day. PMID:38573131
[21] Russo E et al. (2023). Italian consensus document on cenobamate DDI management. PMID:36662573

Run locally:  streamlit run xcopri_app.py
Run in Docker: see README_SETUP.md
Deps: pip install streamlit pandas reportlab
"""

import io
import streamlit as st
import pandas as pd
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

# ═══════════════════════════════════════════════════════════════════════════════
# APP VERSION / METADATA
# ═══════════════════════════════════════════════════════════════════════════════

APP_VERSION      = "1.0"
APP_LAST_UPDATED = "June 21, 2026"

# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

REFERENCES = {
    "Sperling2020":       "Sperling MR et al., Epilepsia 2020 [Phase 3 open-label safety/DRESS] PMID:32162327",
    "Krauss2020":         "Krauss GL et al., Lancet Neurol 2020 [Phase 3 RCT — efficacy/safety] PMID:31734103",
    "Roberti2021":        "Roberti R et al., CNS Drugs 2021 [CYP2C19 inhibition / CYP3A4-2B6 induction] PMID:33966208",
    "Smith2022":          "Smith MC et al., Neurol Ther 2022 [Expert consensus dose adjustments] PMID:35962907",
    "Steinhoff2024":      "Steinhoff BJ et al., Ther Adv Neurol Disord 2024 [Delphi panel initiation] PMID:38919279",
    "Osborn2023":         "Osborn M & Abou-Khalil B, Epilepsy Behav 2023 [Clobazam PK + PD synergy] PMID:36963163",
    "Schoretsanitis2022": "Schoretsanitis G et al., Expert Opin Drug Metab Toxicol 2022 [OC interactions] PMID:35849051",
    "Karazniewicz2021":   "Karazniewicz-Lada M et al., Int J Mol Sci 2021 [PK DDI review incl. CBD] PMID:34502492",
    "Operto2025":         "Operto FF et al., Front Pharmacol 2025 [Plasma levels & concomitant ASMs]",
    "Krauss2025":         "Krauss GL et al., Epilepsia 2025 [Tolerability & initiation strategies] PMID:39887568",
    "Zaccara2021":        "Zaccara G et al., Neuropsychiatr Dis Treat 2021 [Safety: QT shortening] PMID:34938073",
    "Landmark2026":       "Johannessen Landmark C et al., Epilepsia 2026 [Two-way PK interactions]",
    "Charlier2026":       "Charlier B et al., Pharmaceutics 2026 [Cenobamate PK with co-ASMs]",
    "Cohen2026":          "Cohen H et al., Epileptic Disord 2026 [CYP2C9 & P-gp induction meta-analysis]",
    "Samanta2025":        "Samanta D, Epilepsy Behav 2025 [Pediatric epilepsy & DEE] PMID:39818154",
    "AbouKhalil2022":     "Abou-Khalil BW, Continuum 2022 [ASM update 2022] PMID:35393970",
    "Ciullo2026":         "Ciullo I et al., Epilepsia Open 2026 [Low-dose clobazam real-world]",
    "FDA2019":            "US Food and Drug Administration. XCOPRI prescribing information [updated August 2025]. FDA; 2025. PMID/URL: accessdata.fda.gov/drugsatfda_docs/label/2025/212839s013lbl.pdf",
    "EMA2021":            "European Medicines Agency. Ontozry summary of product characteristics. EMA; 2021",
    "Greene2024":         "Greene SA et al. Pharmacokinetic study of cenobamate enzyme-inducing/inhibiting effects at doses up to 200 mg/day. PMID:38573131",
    "ItalianConsensus2023": "Russo E et al. Italian consensus document on cenobamate drug interactions. PMID:36662573",
}

PAPER_LIST = [
    ("Sperling MR et al.", "2020",
     "Cenobamate as adjunctive treatment for uncontrolled focal seizures — Phase 3 open-label",
     "Epilepsia", "10.1111/epi.16525", "PMID:32162327",
     "Safety data including DRESS surveillance; largest titration-safety dataset."),
    ("Krauss GL et al.", "2020",
     "Safety and efficacy of adjunctive cenobamate — Phase 3 RCT",
     "Lancet Neurol", "10.1016/S1474-4422(19)30399-0", "PMID:31734103",
     "Pivotal efficacy trial; seizure-freedom rates up to 28%."),
    ("Roberti R et al.", "2021",
     "Pharmacology of cenobamate: mechanism of action, PK, DDI and tolerability",
     "CNS Drugs", "10.1007/s40263-021-00819-8", "PMID:33966208",
     "Primary PK/DDI reference: CYP2C19 inhibition, CYP3A4/2B6 induction."),
    ("Smith MC et al.", "2022",
     "Dose adjustment of concomitant ASMs during cenobamate: expert consensus",
     "Neurol Ther", "10.1007/s40120-022-00400-5", "PMID:35962907",
     "Operationally actionable dose-adjustment percentages for each ASM."),
    ("Steinhoff BJ et al.", "2024",
     "Therapeutic strategies during cenobamate initiation: Delphi panel",
     "Ther Adv Neurol Disord", "10.1177/17562864241256733", "PMID:38919279",
     "Consensus on titration pace, DRESS prevention, SCB discontinuation."),
    ("Osborn M & Abou-Khalil B", "2023",
     "The cenobamate-clobazam interaction: evidence of synergy + PK",
     "Epilepsy Behav", "10.1016/j.yebeh.2023.109156", "PMID:36963163",
     "Defines N-CLB elevation and pharmacodynamic synergy; basis for 20 mg threshold."),
    ("Schoretsanitis G et al.", "2022",
     "Drug-drug interactions between psychotropic medications and oral contraceptives",
     "Expert Opin Drug Metab Toxicol", "10.1080/17425255.2022.2106214", "PMID:35849051",
     "Basis for hormonal contraceptive interaction guidance."),
    ("Karazniewicz-Lada M et al.", "2021",
     "PK DDIs among ASMs including CBD, COVID-19 drugs and nutrients",
     "Int J Mol Sci", "10.3390/ijms22179582", "PMID:34502492",
     "CBD + cenobamate additive CYP2C19 inhibition; OXC/CBZ/PHT details."),
    ("Operto FF et al.", "2025",
     "Clinical predictors and concomitant ASM effects on seizure control vs. plasma cenobamate",
     "Front Pharmacol", "10.3389/fphar.2025.1668382", "",
     "Real-world plasma concentrations; VPA/LEV combinations."),
    ("Krauss GL et al.", "2025",
     "Improving tolerability of ASMs: when and how to use cenobamate",
     "Epilepsia", "10.1111/epi.18304", "PMID:39887568",
     "Initiation strategies, QT monitoring, tolerability management."),
    ("Zaccara G et al.", "2021",
     "Critical appraisal of cenobamate as adjunctive treatment of focal seizures",
     "Neuropsychiatr Dis Treat", "10.2147/NDT.S281490", "PMID:34938073",
     "Safety profile including QT shortening evidence."),
    ("Johannessen Landmark C et al.", "2026",
     "Pharmacokinetic variability and complex two-way interactions with cenobamate",
     "Epilepsia", "10.1002/epi.70184", "",
     "KEY: bidirectional interactions — concomitant ASMs lower cenobamate levels by 20–40%."),
    ("Charlier B et al.", "2026",
     "Do cenobamate pharmacokinetics change with co-administered ASMs?",
     "Pharmaceutics", "10.3390/pharmaceutics18010092", "",
     "Quantifies bidirectional effects of CBZ, OXC, LTG on cenobamate troughs."),
    ("Cohen H et al.", "2026",
     "Induction of CYP2C9 and P-gp by ASMs: systematic review + meta-analysis",
     "Epileptic Disord", "10.1002/epd2.70232", "",
     "CYP2C9 induction and P-glycoprotein effects relevant to PHT, PHB, OXC."),
    ("Samanta D", "2025",
     "Cenobamate in pediatric epilepsy and DEE",
     "Epilepsy Behav", "10.1016/j.yebeh.2025.110787", "PMID:39818154",
     "Off-label pediatric data; syndrome-specific considerations."),
    ("Abou-Khalil BW", "2022",
     "Update on antiseizure medications 2022",
     "Continuum (Minneap Minn)", "10.1212/CON.0000000000001104", "PMID:35393970",
     "Broad ASM update; cenobamate mechanism and clinical positioning."),
    ("Ciullo I et al.", "2026",
     "Effectiveness of adjunctive low-dose clobazam in focal DRE with incomplete cenobamate response",
     "Epilepsia Open", "10.1002/epi4.70261", "",
     "Real-world rationale for low-dose clobazam add-on strategy."),
    ("US Food and Drug Administration", "2025",
     "XCOPRI (cenobamate) prescribing information [updated August 2025 — hepatotoxicity]",
     "FDA", "https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/212839s013lbl.pdf", "",
     "Official prescribing information: dosing, contraindications, hepatic/renal limits. August 2025 update adds hepatotoxicity/liver failure warning."),
    ("European Medicines Agency", "2021",
     "Ontozry (cenobamate): summary of product characteristics",
     "EMA", "https://www.ema.europa.eu/en/medicines/human/EPAR/ontozry", "",
     "EMA approval documentation; European dosing and safety guidance."),
    ("Greene SA et al.", "2024",
     "Pharmacokinetic study of cenobamate enzyme effects at doses up to 200 mg/day",
     "PMID:38573131", "10.1002/[see PMID 38573131]", "PMID:38573131",
     "Establishes that cenobamate's enzyme-inducing/inhibiting effects were characterised only up to 200 mg/day — half the maximal approved daily dose. Relevant for scope-of-recommendations disclaimer."),
    ("Russo E et al.", "2023",
     "Italian consensus document on practical management of cenobamate drug interactions",
     "PMID:36662573", "10.1002/[see PMID 36662573]", "PMID:36662573",
     "Expert consensus on cenobamate DDI management from Italian epilepsy specialists; complements Smith 2022 and Steinhoff 2024."),
]

# ═══════════════════════════════════════════════════════════════════════════════
# DRUG DATABASE
# pct_per_period: 6 values (weeks 1-2 … 11-12). Negative = reduce %; positive = increase %.
# None = non-numeric interaction (e.g. contraceptives).
# ═══════════════════════════════════════════════════════════════════════════════

DRUG_DB = {
    "Clobazam": {
        "unit": "mg", "has_serum": False,
        "tablet_sizes": [5, 10, 20],
        "splittable": True,
        "risk": "HIGH",
        "action": "Mandatory dose REDUCTION 25–50%",
        "mechanism": (
            "Cenobamate inhibits CYP2C19, markedly elevating the active metabolite "
            "N-desmethylclobazam (N-CLB) up to 3-fold. Risk of sedation, ataxia, "
            "respiratory depression. Pharmacodynamic synergy demonstrated beyond PK "
            "interaction alone. Real-world data support low-dose clobazam (5–10 mg/day) "
            "as add-on in incomplete responders."
        ),
        "recommendation": (
            "Dose adjustment is recommended ONLY if the current daily dose exceeds 20 mg.\n"
            "• If dose >20 mg/day: reduce clobazam by 25% at weeks 5–6, "
            "and by a further 25% at weeks 9–10 (total ~50% reduction).\n"
            "• If dose ≤20 mg/day: no proactive reduction required — monitor clinically "
            "for signs of N-CLB accumulation (sedation, ataxia) from week 3.\n"
            "• TDM: consider measuring N-CLB levels if sedation develops.\n"
            "• If incomplete response to cenobamate persists, consider adjunctive "
            "low-dose clobazam 5–10 mg/day (Ciullo 2026)."
        ),
        "dose_adjustment_threshold": 20,
        "max_dose_warning": 40,
        "pct_per_period": [0, 0, -25, -25, -50, -50],
        "serum_toxic_high": None,
        "references": ["Osborn2023", "Smith2022", "Steinhoff2024", "Ciullo2026", "FDA2019", "EMA2021"],
        "two_way": (
            "Clobazam co-administration may also influence cenobamate plasma concentrations "
            "(Landmark 2026)."
        ),
    },

    "Phenytoin": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [100],
        "splittable": False,
        "serum_normal_range": (10, 20),
        "risk": "HIGH",
        "action": "Dose REDUCTION 25–40% + frequent serum monitoring",
        "mechanism": (
            "CYP2C19 inhibition by cenobamate raises phenytoin levels substantially "
            "(non-linear Michaelis-Menten kinetics amplify risk disproportionately). "
            "CYP2C9 induction may partially offset, but net effect is elevation. "
            "Both cenobamate and phenytoin are sodium channel blockers — additive pharmacodynamic "
            "effects are possible. Risks: nystagmus, ataxia, diplopia, encephalopathy, "
            "cardiac toxicity."
        ),
        "recommendation": (
            "• Reduce phenytoin dose by 20% at weeks 5–6 and a further 20% at weeks 9–10.\n"
            "• TDM: serum levels at baseline, week 4, week 8, and week 12.\n"
            "• If serum level >15 mcg/mL at any point, accelerate reduction immediately.\n"
            "• Phenytoin is also a CYP3A4/2C9 inducer — it reduces cenobamate plasma levels. "
            "Higher cenobamate target doses may be needed."
        ),
        "pct_per_period": [0, 0, -20, -20, -40, -40],
        "serum_toxic_high": 20,
        "max_dose_warning": 400,
        "references": ["Roberti2021", "Smith2022", "Karazniewicz2021", "Cohen2026", "FDA2019"],
        "two_way": (
            "Phenytoin (CYP3A4/2C9 inducer) reduces cenobamate plasma levels — "
            "higher cenobamate target doses may be needed (Landmark 2026; Charlier 2026)."
        ),
        "is_inducer": True,
        "inducer_affected_drugs": ["Lamotrigine", "Cannabidiol (CBD)"],
    },

    "Phenobarbital": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [15, 30, 60, 100],
        "splittable": True,
        "serum_normal_range": (15, 40),
        "risk": "HIGH",
        "action": "Phenobarbital dose REDUCTION 20–30% + serum monitoring",
        "mechanism": (
            "CYP2C19 inhibition by cenobamate increases phenobarbital plasma levels. "
            "Both drugs have GABAergic properties — additive CNS depression is possible. "
            "Risks: CNS depression, respiratory depression, falls (especially in elderly)."
        ),
        "recommendation": (
            "• Reduce phenobarbital dose by 15% at weeks 5–6 and a further 15% at weeks 9–10.\n"
            "• TDM: serum levels at baseline and every 4 weeks during titration.\n"
            "• Phenobarbital is a CYP3A4/2C9 inducer — it also reduces cenobamate plasma levels. "
            "Higher cenobamate target doses may be needed.\n"
            "• When tapering phenobarbital, monitor for rising levels of "
            "co-administered CYP-substrate ASMs (e.g. lamotrigine) — see cascade DDI warning."
        ),
        "pct_per_period": [0, 0, -15, -15, -30, -30],
        "serum_toxic_high": 40,
        "max_dose_warning": 200,
        "references": ["Roberti2021", "Smith2022", "Cohen2026"],
        "two_way": (
            "Phenobarbital (CYP3A4/2C9 inducer) reduces cenobamate plasma levels — "
            "higher cenobamate target doses may be needed (Landmark 2026)."
        ),
        "is_inducer": True,
        "inducer_affected_drugs": ["Lamotrigine", "Perampanel", "Everolimus"],
    },

    "Lamotrigine": {
        "unit": "mg", "has_serum": False,
        "tablet_sizes": [25, 50, 100, 150, 200],
        "splittable": True,
        "risk": "MODERATE",
        "action": "Potential dose INCREASE 20–50%",
        "mechanism": (
            "Cenobamate induces UGT1A4, the primary glucuronidation enzyme for lamotrigine, "
            "increasing lamotrigine clearance. Plasma levels may fall by up to 50%. "
            "Risk of breakthrough seizures in previously well-controlled patients. "
            "Note: lamotrigine levels will also rise when a co-administered inducer (e.g. "
            "carbamazepine, phenobarbital) is tapered — monitor closely during inducer washout."
        ),
        "recommendation": (
            "• Monitor for seizure recurrence from week 5.\n"
            "• Consider +15% dose increase at weeks 5–6 and a further +15% at weeks 9–10 "
            "if clinical deterioration is noted.\n"
            "• TDM: serum levels at baseline and weeks 6 and 12.\n"
            "• Also monitor lamotrigine levels if any co-inducer is being tapered, as "
            "inducer washout may cause lamotrigine levels to rise significantly."
        ),
        "pct_per_period": [0, 0, 15, 15, 30, 30],
        "serum_toxic_high": None,
        "max_dose_warning": 700,
        "references": ["Roberti2021", "Smith2022", "Steinhoff2024", "Landmark2026"],
        "two_way": (
            "Lamotrigine may influence cenobamate trough levels "
            "(Charlier 2026; Landmark 2026). Monitor cenobamate clinical response."
        ),
    },

    "Carbamazepine": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [200, 400],
        "splittable": True,
        "serum_normal_range": (4, 12),
        "risk": "MODERATE",
        "action": "Potential dose INCREASE 15–30% + serum monitoring",
        "mechanism": (
            "Cenobamate induces UGT enzymes and CYP3A4, reducing carbamazepine levels. "
            "Carbamazepine itself is a strong CYP3A4/UGT inducer — complex bidirectional "
            "interaction. Both cenobamate and carbamazepine are sodium channel blockers — "
            "additive pharmacodynamic effects are possible. "
            "When carbamazepine is tapered, levels of co-administered drugs it was inducing "
            "(e.g. lamotrigine via UGT1A4) will rise — monitor for toxicity."
        ),
        "recommendation": (
            "• TDM: serum levels at baseline, weeks 4, 8, 12.\n"
            "• Consider +10% dose increase at weeks 5–6 and a further +10% at weeks 9–10 "
            "if trough levels fall below target range.\n"
            "• Carbamazepine reduces cenobamate plasma levels by >30% — higher cenobamate "
            "target doses may be required.\n"
            "• Taper alert: when stopping carbamazepine, monitor lamotrigine, perampanel "
            "and other CYP3A4/UGT substrates for rising levels — reduce their doses "
            "by 25–50% as clinically indicated."
        ),
        "pct_per_period": [0, 0, 10, 10, 20, 20],
        "serum_toxic_high": 12,
        "max_dose_warning": 2400,
        "references": ["Roberti2021", "Smith2022", "Landmark2026", "Charlier2026"],
        "two_way": (
            "STRONG two-way interaction: carbamazepine (CYP3A4 inducer) reduces cenobamate "
            "plasma levels by >30% — higher cenobamate target doses may be needed "
            "(Landmark 2026; Charlier 2026)."
        ),
        "is_inducer": True,
        "inducer_affected_drugs": ["Lamotrigine", "Perampanel", "Everolimus"],
    },

    "Valproate (VPA)": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [200, 300, 500],
        "splittable": True,
        "serum_normal_range": (50, 100),
        "risk": "LOW-MODERATE",
        "action": "Monitor — minor PK interaction; hepatotoxicity risk with combination",
        "mechanism": (
            "VPA is primarily metabolized via glucuronidation and beta-oxidation — "
            "no direct CYP2C19 or CYP3A4 interaction with cenobamate. "
            "Importantly, both VPA and cenobamate have hepatotoxic potential. "
            "Combination may increase risk of liver injury, particularly in patients "
            "with pre-existing hepatic disease or on polypharmacy."
        ),
        "recommendation": (
            "• TDM: serum levels at baseline and every 6 weeks.\n"
            "• Dose adjustment rarely required based on PK.\n"
            "• ⚠ Hepatotoxicity: monitor LFTs at baseline, weeks 4, 8, and 12, "
            "and at every subsequent visit. Discontinue if ALT/AST >3× ULN.\n"
            "• Exercise particular caution in patients with pre-existing liver disease, "
            "metabolic disorders, or in the pediatric population."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "serum_toxic_high": 100,
        "max_dose_warning": 3000,
        "references": ["Roberti2021", "Karazniewicz2021", "Operto2025"],
        "two_way": None,
    },

    "Lacosamide": {
        "unit": "mg", "has_serum": False,
        "tablet_sizes": [50, 100, 150, 200],
        "splittable": False,
        "risk": "MODERATE",
        "action": "ECG monitoring required — dual sodium channel and cardiac effects",
        "mechanism": (
            "Both drugs act on voltage-gated sodium channels (different binding sites/modes). "
            "Cenobamate shortens QT interval; lacosamide prolongs the PR interval. "
            "Additive cardiac conduction effects are possible. No significant PK interaction."
        ),
        "recommendation": (
            "Baseline ECG before cenobamate initiation. Repeat at week 4 and after each "
            "dose step. No dose adjustment required based on PK. "
            "Avoid if baseline PR >200 ms without cardiology consultation. "
            "Monitor for dizziness, diplopia, and ataxia (additive CNS effects)."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "serum_toxic_high": None,
        "references": ["Roberti2021", "Smith2022", "Steinhoff2024"],
        "two_way": None,
    },

    "Levetiracetam": {
        "unit": "mg", "has_serum": False,
        "tablet_sizes": [250, 500, 750, 1000],
        "splittable": True,
        "risk": "LOW",
        "action": "No PK adjustment needed — monitor for additive psychiatric effects",
        "mechanism": (
            "Levetiracetam has minimal hepatic CYP metabolism (primarily renal excretion "
            "via hydrolysis). No significant PK interaction with cenobamate expected. "
            "Both drugs can cause psychiatric adverse effects (irritability, aggression, "
            "depression, anxiety). Additive burden may be clinically significant."
        ),
        "recommendation": (
            "• No dose adjustment required on pharmacokinetic grounds.\n"
            "• Monitor for additive psychiatric/behavioural effects (irritability, "
            "aggression, mood disturbance) at each clinical visit, particularly at "
            "higher cenobamate doses.\n"
            "• Assess patient and caregiver for mood changes from week 3 onwards."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "serum_toxic_high": None,
        "max_dose_warning": 4000,
        "references": ["Roberti2021", "Operto2025", "AbouKhalil2022"],
        "two_way": None,
    },

    "Oxcarbazepine": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [150, 300, 600],
        "splittable": True,
        "serum_normal_range": (3, 35),
        "risk": "MODERATE",
        "action": "Potential dose INCREASE — UGT induction reduces licarbazepine (MHD) levels",
        "mechanism": (
            "The active metabolite of oxcarbazepine, licarbazepine (MHD), is a UGT substrate. "
            "Cenobamate-mediated UGT induction reduces MHD plasma levels. "
            "Oxcarbazepine itself is a CYP3A4 inducer, reducing cenobamate levels (two-way). "
            "Additive hyponatraemia risk with both drugs. "
            "When tapering oxcarbazepine, MHD levels of co-administered UGT substrates may rise."
        ),
        "recommendation": (
            "• TDM: monitor licarbazepine (MHD) serum levels at baseline and weeks 4, 8.\n"
            "• Consider 10–15% dose increase if MHD falls below therapeutic range.\n"
            "• Check serum sodium at each visit — both drugs may cause hyponatraemia.\n"
            "• Oxcarbazepine reduces cenobamate levels — higher cenobamate target doses "
            "may be needed.\n"
            "• Taper alert: when stopping oxcarbazepine, monitor for rising levels of "
            "co-administered CYP3A4/UGT substrates — reduce their doses as clinically indicated."
        ),
        "pct_per_period": [0, 0, 10, 10, 20, 20],
        "serum_toxic_high": 35,
        "max_dose_warning": 3000,
        "references": ["Roberti2021", "Karazniewicz2021", "Landmark2026", "Charlier2026"],
        "two_way": (
            "Oxcarbazepine (CYP3A4 inducer) reduces cenobamate plasma trough levels — "
            "monitor clinical response and adjust cenobamate target dose accordingly "
            "(Charlier 2026)."
        ),
        "is_inducer": True,
        "inducer_affected_drugs": ["Lamotrigine", "Perampanel", "Everolimus"],
    },

    "Perampanel": {
        "unit": "mg", "has_serum": False,
        "tablet_sizes": [2, 4, 6, 8, 10, 12],
        "splittable": False,
        "risk": "MODERATE",
        "action": "Potential dose INCREASE — UGT/CYP3A4 induction lowers perampanel",
        "mechanism": (
            "Perampanel is primarily metabolized by CYP3A4 and CYP3A5. "
            "Cenobamate-mediated CYP3A4 induction can reduce perampanel plasma levels by 20–50%. "
            "Risk of breakthrough seizures. "
            "⚠ At doses >10 mg/day, perampanel itself has mild CYP3A4 induction activity — "
            "at these doses, a bidirectional interaction should be considered, "
            "with perampanel potentially reducing cenobamate exposure."
        ),
        "recommendation": (
            "• Monitor for loss of seizure control from week 5.\n"
            "• Consider 2 mg dose increase if clinical deterioration occurs.\n"
            "• Re-assess behavioural side effects (aggression, irritability) as dose "
            "changes may unmask or attenuate them.\n"
            "• If current perampanel dose >10 mg/day: also monitor cenobamate efficacy, "
            "as mild cenobamate level reduction is possible."
        ),
        "pct_per_period": [0, 0, 15, 15, 25, 25],
        "serum_toxic_high": None,
        "max_dose_warning": 12,
        "references": ["Roberti2021", "Smith2022", "Steinhoff2024"],
        "two_way": (
            "At doses >10 mg/day, perampanel has mild CYP3A4 induction activity — "
            "may slightly reduce cenobamate levels at high perampanel doses."
        ),
    },

    "Cannabidiol (CBD)": {
        "unit": "mg", "has_serum": False,
        "tablet_sizes": [100, 200],
        "splittable": False,
        "risk": "MODERATE",
        "action": "Monitor — additive CYP2C19 inhibition; hepatotoxicity risk",
        "mechanism": (
            "CBD inhibits CYP2C19 and CYP3A4. Co-administration with cenobamate (also a "
            "CYP2C19 inhibitor) produces additive inhibition, which may further elevate "
            "levels of other CYP2C19 substrates co-prescribed with cenobamate. "
            "CBD itself is metabolized by CYP3A4 and may accumulate under cenobamate's "
            "enzyme induction. Both CBD and cenobamate have hepatotoxic potential."
        ),
        "recommendation": (
            "• Monitor LFTs at baseline and every 4 weeks — both CBD and cenobamate are "
            "hepatotoxic; triple combination with VPA further increases this risk.\n"
            "• If any CYP2C19 substrates are co-prescribed, apply more aggressive "
            "dose-reduction steps for those drugs.\n"
            "• CBD dose may need reduction if sedation or elevated transaminases occur.\n"
            "• ⚠ Hepatotoxicity alert: ALT/AST >3× ULN — consider discontinuation."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "serum_toxic_high": None,
        "max_dose_warning": 1500,
        "references": ["Karazniewicz2021", "Steinhoff2024"],
        "two_way": None,
    },

    "Hormonal Contraceptives": {
        "unit": "", "has_serum": False,
        "tablet_sizes": [], "splittable": False,
        "risk": "HIGH",
        "action": "Switch to non-hormonal contraception BEFORE starting cenobamate",
        "conditional_on_pregnancy": True,   # only shown if hormonal contraception selected in Tab 1
        "mechanism": (
            "CYP3A4 induction markedly reduces estrogen and progestogen plasma levels. "
            "Applies to combined oral pills, progestogen-only pills, patches, vaginal rings, "
            "and hormonal IUDs. Effect persists for weeks after cenobamate discontinuation."
        ),
        "recommendation": (
            "• Switch to copper IUD or condoms BEFORE the first cenobamate dose.\n"
            "• Document counselling in the patient record.\n"
            "• If hormonal method unavoidable: use highest available estrogen dose "
            "AND a barrier method.\n"
            "• Review at every visit."
        ),
        "pct_per_period": [None, None, None, None, None, None],
        "serum_toxic_high": None,
        "references": ["Schoretsanitis2022", "Roberti2021", "Smith2022"],
        "two_way": None,
    },

    "Primidone": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [50, 250],
        "splittable": True,
        "serum_normal_range": (5, 12),
        "risk": "HIGH",
        "action": "Primidone dose REDUCTION — metabolized to phenobarbital",
        "mechanism": (
            "Primidone is rapidly metabolized to phenobarbital (active metabolite) and "
            "phenylethylmalonamide (PEMA). Cenobamate's CYP2C19 inhibition will therefore "
            "raise phenobarbital derived from primidone, with the same toxicity risks as "
            "direct phenobarbital co-prescription. Both drugs also have GABAergic activity."
        ),
        "recommendation": (
            "• Monitor phenobarbital serum levels (derived from primidone) at baseline "
            "and every 4 weeks — treat as for phenobarbital co-administration.\n"
            "• Reduce primidone dose by 15% at weeks 5–6 and a further 15% at weeks 9–10 "
            "if phenobarbital levels are rising.\n"
            "• Primidone is also a CYP inducer — it may reduce cenobamate plasma levels.\n"
            "• ⚠ CNS depression risk: monitor carefully for sedation and ataxia."
        ),
        "pct_per_period": [0, 0, -15, -15, -30, -30],
        "serum_toxic_high": 12,
        "max_dose_warning": 2000,
        "references": ["Roberti2021", "Smith2022"],
        "two_way": (
            "Primidone (via its phenobarbital metabolite) induces CYP3A4/2C9 and reduces "
            "cenobamate plasma levels — higher cenobamate target doses may be needed."
        ),
        "is_inducer": True,
        "inducer_affected_drugs": ["Lamotrigine", "Perampanel"],
    },

    "Eslicarbazepine acetate (ESL)": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [400, 600, 800],
        "splittable": False,
        "serum_normal_range": (3, 35),
        "risk": "MODERATE",
        "action": "Potential dose INCREASE — UGT induction reduces licarbazepine levels",
        "mechanism": (
            "Eslicarbazepine acetate (ESL) is a pro-drug converted to the same active "
            "metabolite as oxcarbazepine: S-licarbazepine (MHD), a UGT substrate. "
            "Cenobamate-mediated UGT induction is expected to reduce licarbazepine levels, "
            "similar to the oxcarbazepine interaction. ESL is also a mild CYP3A4 inducer "
            "and may reduce cenobamate levels (two-way interaction). "
            "Additive hyponatraemia risk."
        ),
        "recommendation": (
            "• TDM: monitor licarbazepine (MHD) serum levels at baseline and weeks 4, 8.\n"
            "• Consider 10–15% dose increase if licarbazepine falls below therapeutic range.\n"
            "• Check serum sodium at each visit.\n"
            "• ESL may reduce cenobamate levels — monitor cenobamate clinical response.\n"
            "• Taper alert: when stopping ESL, monitor co-administered CYP3A4/UGT substrates "
            "for rising levels."
        ),
        "pct_per_period": [0, 0, 10, 10, 20, 20],
        "serum_toxic_high": 35,
        "max_dose_warning": 1600,
        "references": ["Roberti2021", "Karazniewicz2021", "Landmark2026"],
        "two_way": (
            "ESL (mild CYP3A4 inducer) may reduce cenobamate plasma levels — "
            "monitor clinical response (Charlier 2026)."
        ),
        "is_inducer": True,
        "inducer_affected_drugs": ["Lamotrigine", "Perampanel"],
    },

    "Felbamate": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [400, 600],
        "splittable": True,
        "serum_normal_range": (30, 60),
        "risk": "HIGH",
        "action": "HIGH CAUTION — hepatotoxicity + aplastic anaemia risk; complex DDI",
        "mechanism": (
            "Felbamate inhibits CYP2C19 (additive with cenobamate) and inhibits beta-oxidation. "
            "It also induces CYP3A4. Felbamate itself carries Black Box Warning risks: "
            "aplastic anaemia and hepatic failure. Combining with cenobamate (also hepatotoxic) "
            "substantially increases hepatotoxicity risk. "
            "Felbamate inhibition of CYP2C19 may further elevate CYP2C19 substrates already "
            "affected by cenobamate."
        ),
        "recommendation": (
            "• ⚠⚠ Black Box Warning: use only in patients unresponsive to other ASMs "
            "(typically Lennox-Gastaut syndrome) where benefit clearly outweighs risk.\n"
            "• LFTs and full blood count at baseline and every 2 weeks for the first 6 months.\n"
            "• Felbamate inhibits CYP2C19 — additive inhibition with cenobamate; reduce "
            "CYP2C19 substrate doses more aggressively than with cenobamate alone.\n"
            "• Felbamate also induces CYP3A4 — monitor lamotrigine and perampanel levels.\n"
            "• Hepatotoxicity: ALT/AST >3× ULN — consider discontinuation of one agent.\n"
            "• TDM: serum levels at baseline and monthly."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "serum_toxic_high": 60,
        "max_dose_warning": 3600,
        "references": ["Roberti2021", "Karazniewicz2021"],
        "two_way": (
            "Felbamate (CYP2C19 inhibitor + CYP3A4 inducer) creates additive inhibition "
            "with cenobamate and may also alter cenobamate plasma levels."
        ),
    },

    "Everolimus": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10],
        "splittable": False,
        "serum_normal_range": (3, 15),
        "risk": "HIGH",
        "action": "Everolimus dose INCREASE required — CYP3A4/P-gp induction",
        "mechanism": (
            "Everolimus (used in tuberous sclerosis complex for seizure control and "
            "as immunosuppressant) is a CYP3A4 and P-glycoprotein substrate. "
            "Cenobamate-mediated CYP3A4 induction and P-gp induction "
            "will substantially reduce everolimus levels, risking both seizure recurrence "
            "and transplant rejection (in transplant patients)."
        ),
        "recommendation": (
            "• ⚠ URGENT: Discuss with the prescribing team (neurologist + oncologist/"
            "transplant physician) before initiating cenobamate.\n"
            "• TDM: everolimus whole-blood trough levels at baseline and every 2 weeks "
            "during cenobamate titration.\n"
            "• Dose increase of everolimus will likely be required — adjust to maintain "
            "trough levels within therapeutic range.\n"
            "• Monitor renal and hepatic function.\n"
            "• Do not initiate cenobamate without a TDM plan in place."
        ),
        "pct_per_period": [0, 0, 20, 20, 30, 30],
        "serum_toxic_high": 15,
        "max_dose_warning": 20,
        "references": ["Roberti2021", "Cohen2026"],
        "two_way": None,
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# SAFETY FLAGS
# ═══════════════════════════════════════════════════════════════════════════════

SAFETY_FLAGS = [
    {
        "emoji": "⚠️",
        "title": "DRESS Syndrome",
        "subtitle": "Drug Reaction with Eosinophilia and Systemic Symptoms",
        "body": (
            "DRESS has been reported with cenobamate, predominantly with rapid titration. "
            "Strict adherence to the 2-week dose-step schedule is mandatory. "
            "Discontinue immediately if rash, fever ≥38.5°C, lymphadenopathy, or eosinophilia develop. "
            "The 2024 Delphi panel (Steinhoff) recommends prophylactic antihistamine in high-risk "
            "patients (prior drug hypersensitivity, HLA-B*15:02 positive)."
        ),
        "refs": ["Sperling2020", "Steinhoff2024", "Krauss2025", "Krauss2020"],
        "bg": "#FDECEA", "border": "#C62828",
    },
    {
        "emoji": "⚡",
        "title": "QT Interval Shortening",
        "subtitle": "Dose-dependent effect — baseline ECG required",
        "body": (
            "Cenobamate causes dose-dependent QT shortening. Baseline ECG must be obtained "
            "before initiation and repeated at weeks 4, 8, and 12, and after each dose increase. "
            "Avoid co-administration with Class Ia/III antiarrhythmics or other QT-shortening agents. "
            "QTc <340 ms: withhold dose escalation and seek cardiology review."
        ),
        "refs": ["Roberti2021", "Zaccara2021", "Krauss2025"],
        "bg": "#FFF3E0", "border": "#E65100",
    },
    {
        "emoji": "🔄",
        "title": "Bidirectional (Two-Way) Pharmacokinetic Interactions",
        "subtitle": "Concomitant ASMs also affect cenobamate plasma levels",
        "body": (
            "Recent data (Landmark 2026; Charlier 2026) confirm that concomitant enzyme-inducing "
            "ASMs (carbamazepine, oxcarbazepine, phenytoin, phenobarbital, primidone) reduce cenobamate "
            "plasma levels by 20–40%. This may require higher cenobamate target doses to achieve seizure "
            "control. Always monitor both directions of the interaction."
        ),
        "refs": ["Landmark2026", "Charlier2026", "Operto2025"],
        "bg": "#E8F5E9", "border": "#2E7D32",
    },
    {
        "emoji": "🟡",
        "title": "Hepatotoxicity Risk",
        "subtitle": "Cenobamate + VPA and/or CBD — monitor liver function",
        "body": (
            "Cenobamate has hepatotoxic potential. A reactive (possibly hepatotoxic) metabolite "
            "is suspected, though definitive human data are limited. Risk is substantially increased "
            "when combined with valproate and/or cannabidiol — all three can cause hepatic injury. "
            "Obtain baseline LFTs before initiation. Monitor LFTs at weeks 4, 8, 12, then every "
            "3 months. Discontinue if ALT/AST >3× ULN. "
            "Exercise caution in patients with pre-existing liver disease."
        ),
        "refs": ["FDA2019", "EMA2021"],
        "bg": "#FFF8E1", "border": "#F9A825",
    },
    {
        "emoji": "👶",
        "title": "Pediatric & DEE Use — Limited Evidence",
        "subtitle": "Not approved <18 years in most jurisdictions",
        "body": (
            "Cenobamate is not approved for patients under 18 years in most countries. "
            "Samanta 2025 reviewed off-label use in pediatric epilepsy and developmental & "
            "epileptic encephalopathies (DEE) — efficacy signals are emerging but safety data "
            "remain limited. Use only in specialist centers with multidisciplinary team agreement."
        ),
        "refs": ["Samanta2025"],
        "bg": "#E3F2FD", "border": "#1565C0",
    },
    {
        "emoji": "ℹ️",
        "title": "Dose Ceiling — These Recommendations Apply up to 200 mg/day",
        "subtitle": "Higher doses may require additional adjustments",
        "body": (
            "All DDI calculations and dose-adjustment recommendations in this tool are based on "
            "cenobamate doses up to 200 mg/day (standard approved dose range). "
            "If cenobamate is escalated beyond 200 mg/day in specific cases, "
            "further dose adjustments of concomitant ASMs may be required beyond those shown here. "
            "This tool does not model interactions at doses >200 mg/day."
        ),
        "refs": ["FDA2019", "EMA2021", "Smith2022", "Greene2024"],
        "bg": "#EDE7F6", "border": "#5E35B1",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

XCOP_SCHEDULE = [12.5, 25, 50, 100, 150, 200]
WEEK_LABELS   = [
    "Weeks 1-2", "Weeks 3-4", "Weeks 5-6",
    "Weeks 7-8", "Weeks 9-10", "Weeks 11-12",
]

# ═══════════════════════════════════════════════════════════════════════════════
# SODIUM CHANNEL BLOCKER (SCB) LOGIC
# Per Steinhoff 2024 Delphi panel: when cenobamate (SCB) is added to another SCB,
# proactive discontinuation of one SCB is recommended.
# ═══════════════════════════════════════════════════════════════════════════════

# Drugs in this list are sodium channel blockers (or have dominant SCB mechanism)
SCB_DRUGS = {
    "Lacosamide":     "Slow-inactivation sodium channel blocker (SV2A-independent)",
    "Carbamazepine":  "Fast-inactivation SCB + strong CYP3A4/UGT inducer",
    "Oxcarbazepine":  "Fast-inactivation SCB (pro-drug → licarbazepine/MHD)",
    "Eslicarbazepine acetate (ESL)": "Fast-inactivation SCB (pro-drug → S-licarbazepine)",
    "Phenytoin":      "Fast-inactivation SCB (non-linear PK, CYP2C19 substrate)",
    "Phenobarbital":  "GABA-A potentiator + SCB component + CYP inducer",
    "Primidone":      "Metabolized to phenobarbital (SCB + GABA-A potentiator)",
    "Lamotrigine":    "Fast/slow-inactivation SCB (UGT1A4 substrate)",
    "Felbamate":      "SCB + GABA-A + NMDA antagonist (Black Box Warning)",
}

TAPER_SCHEDULE = {
    "Lacosamide":    {"mode": "pct",  "values": [100, 75, 50, 25, 0,  0]},
    "Carbamazepine": {"mode": "step", "step": 200},
    "Oxcarbazepine": {"mode": "pct",  "values": [100, 80, 60, 40, 20, 0]},
    "Eslicarbazepine acetate (ESL)": {"mode": "pct", "values": [100, 80, 60, 40, 20, 0]},
    "Phenytoin":     {"mode": "pct",  "values": [100, 75, 50, 25, 0,  0]},
    "Phenobarbital": {"mode": "pct",  "values": [100, 85, 70, 50, 25, 0]},
    "Primidone":     {"mode": "pct",  "values": [100, 85, 70, 50, 25, 0]},
    "Lamotrigine":   {"mode": "pct",  "values": [100, 75, 50, 25, 0,  0]},
    "Felbamate":     {"mode": "pct",  "values": [100, 85, 70, 55, 40, 25]},
}

# ── Cascade DDI: when an INDUCER is tapered, these drugs' levels will RISE ───
# Maps inducer → list of (affected_drug, expected_change, action)
CASCADE_DDI = {
    "Carbamazepine": [
        ("Lamotrigine",  "levels may rise 50–100%", "Reduce lamotrigine dose by 25–50% as clinically indicated"),
        ("Perampanel",   "levels may rise 20–50%",  "Monitor and reduce perampanel if sedation occurs"),
        ("Everolimus",   "levels may rise markedly", "Urgent TDM — reduce everolimus to pre-cenobamate dose"),
    ],
    "Oxcarbazepine": [
        ("Lamotrigine",  "levels may rise 30–70%",  "Reduce lamotrigine dose by 25–50% as clinically indicated"),
        ("Perampanel",   "levels may rise 20–40%",  "Monitor and reduce perampanel if sedation occurs"),
        ("Everolimus",   "levels may rise markedly", "Urgent TDM — reduce everolimus to pre-cenobamate dose"),
    ],
    "Eslicarbazepine acetate (ESL)": [
        ("Lamotrigine",  "levels may rise 30–70%",  "Reduce lamotrigine dose by 25–50% as clinically indicated"),
        ("Perampanel",   "levels may rise 20–40%",  "Monitor and reduce perampanel if sedation occurs"),
    ],
    "Phenytoin": [
        ("Lamotrigine",  "levels may rise 30–60%",  "Reduce lamotrigine dose by 25–50% as clinically indicated"),
        ("Perampanel",   "levels may rise 20–50%",  "Monitor and reduce perampanel if sedation occurs"),
        ("Everolimus",   "levels may rise markedly", "Urgent TDM — reduce everolimus to pre-cenobamate dose"),
    ],
    "Phenobarbital": [
        ("Lamotrigine",  "levels may rise 30–60%",  "Reduce lamotrigine dose by 25–50% as clinically indicated"),
        ("Perampanel",   "levels may rise 20–50%",  "Monitor and reduce perampanel if sedation occurs"),
        ("Everolimus",   "levels may rise markedly", "Urgent TDM — reduce everolimus to pre-cenobamate dose"),
    ],
    "Primidone": [
        ("Lamotrigine",  "levels may rise 30–60%",  "Reduce lamotrigine dose by 25–50% as clinically indicated"),
        ("Perampanel",   "levels may rise 20–50%",  "Monitor and reduce perampanel if sedation occurs"),
    ],
    "Felbamate": [
        ("Lamotrigine",  "levels may rise 30–60%",  "Reduce lamotrigine dose by 25–50% as clinically indicated"),
        ("Perampanel",   "levels may rise 20–40%",  "Monitor and reduce perampanel if sedation occurs"),
    ],
}

def get_cascade_warnings(taper_drug: str, selected_drugs: dict) -> list:
    """
    Return list of cascade DDI warnings when an inducer is being tapered.
    Only warns about drugs actually present in the patient's regimen.
    """
    warnings = []
    if not taper_drug or taper_drug not in CASCADE_DDI:
        return warnings
    for affected_drug, change, action in CASCADE_DDI[taper_drug]:
        if affected_drug in selected_drugs:
            warnings.append({
                "drug":   affected_drug,
                "change": change,
                "action": action,
            })
    return warnings

def get_active_scbs(selected: dict) -> list:
    """Return list of SCB drug names the patient is currently taking."""
    return [d for d in selected if d in SCB_DRUGS]

def taper_dose_str(drug: str, base_dose: float, period_idx: int) -> str:
    """Return tapered dose string for a given drug and titration period."""
    schedule = TAPER_SCHEDULE.get(drug)
    if not schedule or base_dose <= 0:
        return "—"
    sizes = DRUG_DB.get(drug, {}).get("tablet_sizes", [])
    splittable = DRUG_DB.get(drug, {}).get("splittable", False)

    if schedule["mode"] == "step":
        # Fixed mg reduction per period; stop when reaches 0
        step = schedule["step"]
        raw = base_dose - step * period_idx
        if raw <= 0:
            return "D/C"
        dose_str = floor_tablet(raw, sizes, splittable) if sizes else f"{round(raw)} mg"
        dropped = int(base_dose - raw)
        return f"{dose_str} (↓{dropped} mg)"
    else:
        # Percentage-based
        pct = schedule["values"][period_idx]
        if pct == 0:
            return "D/C"
        raw = base_dose * pct / 100
        dose_str = floor_tablet(raw, sizes, splittable) if sizes else f"{round(raw)} mg"
        return f"{dose_str} (↓{100 - pct}%)"

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=None)
def risk_colors(risk: str):
    return {
        "HIGH":         ("#FDECEA", "#C62828"),
        "MODERATE":     ("#FFF8E1", "#F57F17"),
        "LOW-MODERATE": ("#FFF8E1", "#F57F17"),
        "LOW":          ("#E8F5E9", "#2E7D32"),
    }.get(risk, ("#F5F5F5", "#9E9E9E"))


@st.cache_data(ttl=None)
def risk_label(risk: str) -> str:
    return {
        "HIGH":         "🔴 HIGH RISK",
        "MODERATE":     "🟡 MODERATE",
        "LOW-MODERATE": "🟡 LOW-MODERATE",
        "LOW":          "🟢 LOW",
    }.get(risk, risk)


def floor_tablet(mg: float, sizes: list, splittable: bool = False) -> str:
    """Return the best achievable dose using whole (and optionally half) tablets.
    Doses are multiples of available tablet sizes — e.g. 3×400 mg = 1200 mg is valid.
    Always rounds DOWN. Never exceeds the target mg."""
    if not sizes:
        return f"{round(mg)} mg"
    largest = max(sizes)
    candidates = set()
    for s in sizes:
        n = 1
        while s * n <= mg + largest:
            candidates.add(s * n)
            n += 1
        if splittable:
            n = 1
            while (s / 2) * n <= mg + largest:
                candidates.add((s / 2) * n)
                n += 1
    below = [c for c in candidates if c <= mg]
    if not below:
        return f"{min(sizes)} mg"
    best = max(below)
    if best == int(best):
        return f"{int(best)} mg"
    return f"{int(best * 2) // 2}½ mg ({int(best * 2)} mg tablet, split)"


def compute_dose(base: float, pct, drug: str = "") -> str:
    """
    Return adjusted dose string, rounded DOWN to nearest achievable tablet dose.
    Includes:
    - Threshold gating (e.g. clobazam ≤20 mg/day → hold)
    - Sanity check: if adjusted dose >4× baseline → warning flag
    - Max-dose warning per drug
    """
    if pct is None:
        return "Switch contraception"
    pct = float(pct)

    # Threshold check: hold dose unchanged
    threshold = DRUG_DB.get(drug, {}).get("dose_adjustment_threshold")
    if threshold and base <= threshold and pct != 0:
        return f"{int(base)} mg"

    if pct == 0:
        return f"{int(base)} mg" if base else "No change"

    raw = base * (1 + pct / 100)

    # Sanity check: flag if calculated dose exceeds 4× baseline
    if raw > base * 4:
        return f"⚠ REVIEW: {round(raw)} mg (>{int(base * 4)} mg — exceeds safety margin)"

    sizes      = DRUG_DB.get(drug, {}).get("tablet_sizes", [])
    splittable = DRUG_DB.get(drug, {}).get("splittable", False)
    dose_str   = floor_tablet(raw, sizes, splittable) if sizes else f"{round(raw)} mg"
    arrow = "↑" if pct > 0 else "↓"
    return f"{dose_str} ({arrow}{abs(int(pct))}%)"


def dose_max_alert(drug: str, base_dose: float) -> str:
    """Return a warning string if the entered dose seems unusually high for this drug."""
    max_w = DRUG_DB.get(drug, {}).get("max_dose_warning")
    if max_w and base_dose > max_w:
        return (
            f"⚠ Entered dose ({int(base_dose)} mg/day) exceeds the typical maximum "
            f"({max_w} mg/day) — please double-check."
        )
    return ""


def serum_alert(drug: str, val) -> str:
    if not val:
        return ""
    hi = DRUG_DB[drug].get("serum_toxic_high")
    if hi and float(val) > hi * 0.85:
        return (
            f"Serum {val} mcg/mL near/above upper limit ({hi} mcg/mL). "
            "Accelerate dose reduction."
        )
    return ""


@st.cache_data(ttl=None)
def fmt_refs(keys: tuple) -> str:
    return "  |  ".join(REFERENCES[k] for k in keys if k in REFERENCES)


@st.cache_data(ttl=None, show_spinner=False)
def build_df(selected_frozen: tuple) -> pd.DataFrame:
    """Build 12-week titration DataFrame. Accepts a tuple of (drug, dose, serum) for caching."""
    selected = {drug: {"dose": dose, "serum": serum} for drug, dose, serum in selected_frozen}
    rows = []
    for i, (wk, xcop) in enumerate(zip(WEEK_LABELS, XCOP_SCHEDULE)):
        row = {"Week": wk, "Xcopri (Cenobamate)": f"{xcop} mg"}
        for drug, info in selected.items():
            base = float(info.get("dose") or 0)
            pct  = DRUG_DB[drug]["pct_per_period"][i]
            row[drug] = compute_dose(base, pct, drug) if base else "—"
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data(ttl=None, show_spinner=False)
def build_me_df(selected_frozen: tuple, df_json: str, taper_drug: str = None) -> pd.DataFrame:
    """
    AM/PM dose breakdown.
    Computes ALL drugs directly from source data to avoid parsing issues with
    tablet-split strings like '27½ mg (55 mg tablet, split) (↓25%)'.
    Only the Week column is taken from df for row ordering.
    """
    df = pd.read_json(io.StringIO(df_json))
    selected = {drug: {"dose": dose, "serum": serum} for drug, dose, serum in selected_frozen}
    rows = []
    for i, (_, row) in enumerate(df.iterrows()):
        r = {"Week": row["Week"], "Xcopri — Evening": row["Xcopri (Cenobamate)"]}

        # Taper drug — compute directly from taper schedule
        if taper_drug and taper_drug in selected:
            base = float(selected[taper_drug].get("dose") or 0)
            val  = taper_dose_str(taper_drug, base, i)
            if val == "D/C":
                r[f"{taper_drug} — AM"] = "D/C"
                r[f"{taper_drug} — PM"] = "D/C"
            elif base > 0:
                # Extract numeric mg value from taper string
                try:
                    mg   = float(val.split(" mg")[0].replace("½", ".5").strip())
                    half = mg / 2
                    fmt  = lambda v: f"{int(v)} mg" if v == int(v) else f"{v} mg"
                    r[f"{taper_drug} — AM"] = fmt(half)
                    r[f"{taper_drug} — PM"] = fmt(mg - half)
                except Exception:
                    r[f"{taper_drug} — AM"] = val
                    r[f"{taper_drug} — PM"] = "—"
            else:
                r[f"{taper_drug} — AM"] = "—"
                r[f"{taper_drug} — PM"] = "—"

        # Regular drugs — compute directly from adjusted dose (not parsed from df text)
        for drug in selected:
            if drug == taper_drug:
                continue
            base = float(selected[drug].get("dose") or 0)
            if not base:
                r[f"{drug} — AM"] = "—"
                r[f"{drug} — PM"] = "—"
                continue
            pct = DRUG_DB[drug]["pct_per_period"][i]
            dose_str = compute_dose(base, pct, drug)

            if "Switch" in dose_str or "REVIEW" in dose_str or dose_str == "—":
                r[drug] = dose_str
                continue

            # Extract the leading numeric mg value cleanly
            try:
                # handles "30 mg (↓25%)", "27½ mg (...)", "20 mg"
                numeric_part = dose_str.split(" mg")[0].replace("½", ".5").strip()
                mg   = float(numeric_part)
                half = mg / 2
                fmt  = lambda v: f"{int(v)} mg" if v == int(v) else f"{v} mg"
                r[f"{drug} — AM"] = fmt(half)
                r[f"{drug} — PM"] = fmt(mg - half)
            except Exception:
                r[f"{drug} — AM"] = dose_str
                r[f"{drug} — PM"] = "—"

        rows.append(r)
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# PDF
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=None, show_spinner="Generating PDF…")
def make_pdf(patient_frozen: tuple, selected_frozen: tuple, df_json: str) -> bytes:
    # Unfreeze cached inputs
    patient  = dict(patient_frozen)
    selected = {drug: {"dose": dose, "serum": serum} for drug, dose, serum in selected_frozen}
    df       = pd.read_json(io.StringIO(df_json))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=14*mm, bottomMargin=14*mm,
    )

    def ps(name, sz=9, bold=False, clr="#000000", sb=0, sa=3, ld=13):
        return ParagraphStyle(
            name, fontSize=sz,
            fontName="Helvetica-Bold" if bold else "Helvetica",
            textColor=colors.HexColor(clr),
            spaceBefore=sb, spaceAfter=sa, leading=ld,
        )

    S  = {
        "title": ps("tt", 14, True, sb=0, sa=2),
        "sub":   ps("su", 8,  False, "#555555", sa=6),
        "h2":    ps("h2", 10, True,  sb=8, sa=3),
        "body":  ps("bd", 8,  False, sa=2, ld=12),
        "small": ps("sm", 7,  False, "#777777", sa=2),
    }

    story = []
    story.append(Paragraph("Xcopri (Cenobamate) — Clinical Titration Report", S["title"]))
    story.append(Paragraph(
        f"Generated: {date.today().strftime('%B %d, %Y')} | For clinical decision support only", S["sub"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Patient Profile", S["h2"]))
    for k, v in patient.items():
        if v and str(v) not in ("None", "", "—"):
            story.append(Paragraph(f"<b>{k}:</b> {v}", S["body"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Safety Flags", S["h2"]))
    for flag in SAFETY_FLAGS:
        story.append(Paragraph(
            f"<b>{flag['emoji']} {flag['title']} — {flag['subtitle']}</b>: {flag['body']}",
            S["body"]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Drug Interaction Summary", S["h2"]))
    for drug in selected:
        d  = DRUG_DB[drug]
        rl = risk_label(d["risk"])
        story.append(Paragraph(f"<b>{rl} — {drug}</b>: {d['recommendation']}", S["body"]))
        if d.get("two_way"):
            story.append(Paragraph(f"Two-way: {d['two_way']}", S["small"]))
        story.append(Paragraph(f"Evidence: {fmt_refs(tuple(d['references']))}", S["small"]))
        story.append(Spacer(1, 3))

    story.append(Paragraph("12-Week Titration Schedule", S["h2"]))
    cols   = list(df.columns)
    n      = len(cols)
    pw     = A4[0] - 36*mm
    w0     = 22*mm
    wrest  = (pw - w0) / max(n - 1, 1)
    widths = [w0] + [wrest] * (n - 1)

    tdata  = [cols] + [list(r) for _, r in df.iterrows()]
    tbl    = Table(tdata, colWidths=widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), colors.HexColor("#E8EAF6")),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 7),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("GRID",          (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Evidence Base (21 Publications and Regulatory Documents, 2019-2026)", S["h2"]))
    for authors, year, title, journal, doi, pmid, _ in PAPER_LIST:
        story.append(Paragraph(f"{authors} ({year}). {title}. {journal}. doi:{doi}", S["small"]))

    story.append(Spacer(1, 5))
    story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#CCCCCC")))
    story.append(Paragraph(
        "DISCLAIMER: This report is for clinical decision support only. "
        "All dosing decisions remain the responsibility of the treating physician. "
        "Evidence base: 21 peer-reviewed publications and regulatory documents, 2019–2026. "
        f"Tool version {APP_VERSION}, last updated {APP_LAST_UPDATED}.",
        S["small"],
    ))

    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG + UI
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Xcopri Transition Tool — Local",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",   # saves render time on first load
)

# ═══════════════════════════════════════════════════════════════════════════════
# DISCLAIMER GATE — must be accepted before the tool is accessible
# ═══════════════════════════════════════════════════════════════════════════════

if "disclaimer_accepted" not in st.session_state:
    st.session_state["disclaimer_accepted"] = False

if not st.session_state["disclaimer_accepted"]:
    st.markdown(
        "<h1 style='text-align:center;margin-bottom:0'>🧠 Xcopri (Cenobamate)</h1>"
        "<h3 style='text-align:center;color:#555;margin-top:4px'>Clinical Transition &amp; Drug-Interaction Tool</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p style='text-align:center;color:#888;font-size:13px'>"
        f"Version {APP_VERSION} &nbsp;·&nbsp; Last updated: {APP_LAST_UPDATED}</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown(
        "<div style='background:#FFF8E1;border-left:4px solid #F57F17;"
        "padding:12px 16px;border-radius:6px;margin-bottom:16px'>"
        "<b>⚠ This tool is intended for use by qualified healthcare professionals only.</b> "
        "Please read the disclaimer below in full before proceeding.</div>",
        unsafe_allow_html=True,
    )

    st.subheader("Legal Disclaimer")

    st.markdown(
        """
This program is designed for medical professionals. The app is based on available
peer-reviewed clinical evidence (21 publications and regulatory documents, 2019–2026 —
see the Evidence Base tab) and the expert opinions of the app developers. It is **not an
official guideline**, and the recommendations do not replace standard health care practice.
Interpretation of the content and data presented are the responsibility of the user.

This tool is designed to aid the prescriber, but does **not substitute** for that person's
clinical judgment and for the need to take into consideration additional patient-related
variables not included in the software algorithm (including, but not limited to, individual
pharmacokinetic variability, CYP2C19 genotype, concurrent non-antiseizure medications, and
co-morbidities beyond those captured in the Patient Profile tab).

The final decision regarding prescription, dose adjustment, or discontinuation of any
medication is the **sole responsibility of the treating physician**, who may choose a
different course of treatment than that suggested by this tool. The developers do not
take responsibility for failure of prescribed medication to control seizures, for any
adverse drug reactions, drug-drug interactions not captured by the tool, or any other
adverse effects that patients may experience.

Users should be aware that cenobamate and other antiseizure medications may fail to
control seizures and may produce adverse effects, some of which may be serious or
life-threatening (including DRESS syndrome, QT shortening, and hepatotoxicity — see
Safety Flags). Users should have detailed knowledge of any drug they prescribe and be
familiar with its efficacy and adverse-effect profile, including the current approved
prescribing information.

All dose-adjustment recommendations in this tool apply to patients with **normal hepatic
and renal function**, no significant co-morbidities beyond epilepsy, and to cenobamate
doses **up to 200 mg/day**; the pharmacokinetic data underlying these recommendations were
established at doses up to 200 mg/day, and further adjustments may be required at higher
doses. The tool does not cover interactions with non-antiseizure medications; consultation
with a clinical pharmacologist or clinical pharmacist is recommended for patients on
complex non-ASM polypharmacy.

**This is not a medical device.** The user understands that they must independently
review the basis for the recommendations presented by this tool (each recommendation is
accompanied by its mechanistic rationale and source citation), and must not rely
primarily on these recommendations but rather on their own clinical judgment when making
decisions for individual patients.

**On-premise / local use:** This tool runs entirely on the user's own computer or
institutional infrastructure. No patient data entered into the tool is transmitted to
the developers or to any external server, and no data is saved by the application beyond
the current session.

The user is liable and responsible for any advice, course of treatment, diagnosis, or
other information obtained through use of this tool. By proceeding, the user releases
and discharges the developers of this tool and their affiliated institutions from any and
all claims, liabilities, obligations, disputes, demands, damages, or causes of action of
any nature, known or unknown, arising from or related to the use of this application.
        """
    )

    st.divider()

    col_a, col_b = st.columns([3, 1])
    with col_a:
        agree = st.checkbox(
            "I am a qualified healthcare professional and I have read, understood, "
            "and agree to the terms of this disclaimer.",
            key="disclaimer_checkbox",
        )
    with col_b:
        proceed = st.button("Enter Tool →", type="primary", disabled=not agree, use_container_width=True)

    if proceed and agree:
        st.session_state["disclaimer_accepted"] = True
        st.rerun()

    st.caption(
        f"Xcopri Transition Tool · Version {APP_VERSION} · Last updated {APP_LAST_UPDATED} · "
        "On-premise, evidence-based clinical decision support."
    )

    st.stop()  # halt execution here — nothing below renders until accepted

# ── Privacy banner (on-premise mode) ─────────────────────────────────────────
st.markdown(
    "<div style='background:#E8F5E9;border-left:4px solid #2E7D32;"
    "padding:8px 16px;border-radius:6px;margin-bottom:10px;font-size:13px'>"
    "🔒 <b>On-Premise Mode</b> — All data remains on this computer. "
    "No information is transmitted to any external server.</div>",
    unsafe_allow_html=True,
)

st.title("🧠 Xcopri (Cenobamate) — Clinical Transition Tool")
st.caption(
    "Evidence-based drug interaction management for neurologists  ·  "
    "Grounded in **21 peer-reviewed publications and regulatory documents (2019–2026)**  ·  "
    f"Version {APP_VERSION} · Last updated {APP_LAST_UPDATED}"
)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1️⃣  Patient Profile",
    "2️⃣  Current Medications",
    "3️⃣  Interaction Analysis",
    "4️⃣  Titration Plan",
    "📚  Evidence Base",
])

# ──────────────────────────────────────────────────────────────────────────────
# TAB 1 — Patient Profile
# ──────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Patient Profile")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.number_input("Age (years)", 18, 100, value=None, placeholder="years", key="age")
        st.selectbox("Sex", ["—", "Male", "Female"], key="gender")
    with c2:
        st.number_input("Weight (kg)", 30.0, 200.0, value=None, placeholder="kg", key="weight")
        st.selectbox(
            "Epilepsy type",
            ["—", "Focal onset", "Generalized onset (primary)",
             "Unknown onset",
             "Developmental & Epileptic Encephalopathy (DEE)"],
            key="epilepsy",
        )
    with c3:
        st.number_input("eGFR (ml/min)", 0, 150, value=None, placeholder="Normal >60", key="egfr")
        st.selectbox(
            "Hepatic function",
            ["Normal (Child-Pugh A)", "Mild impairment (Child-Pugh B)",
             "Severe impairment (Child-Pugh C)"],
            key="liver",
        )

    st.selectbox(
        "Pregnancy / breastfeeding / contraception",
        ["Not applicable",
         "Pregnant",
         "Breastfeeding",
         "Childbearing potential — currently using hormonal contraception",
         "Childbearing potential — non-hormonal contraception / not sexually active"],
        key="pregnancy",
    )

    # Dynamic patient alerts
    alerts = []
    preg  = st.session_state.get("pregnancy", "")
    liver = st.session_state.get("liver", "")
    egfr  = st.session_state.get("egfr") or 0
    ep    = st.session_state.get("epilepsy", "")

    if "Pregnant" in preg:
        alerts.append(("error",
            "**Pregnancy:** Cenobamate is not approved in pregnancy. Teratogenic risk unknown. "
            "Strongly consider an alternative ASM and consult maternal-fetal medicine."))
    if "Breastfeeding" in preg:
        alerts.append(("warning",
            "**Breastfeeding:** Cenobamate is excreted in breast milk. Risk/benefit assessment required. "
            "Monitor infant for sedation and poor feeding."))
    if "hormonal contraception" in preg:
        alerts.append(("error",
            "**Hormonal contraception:** CYP3A4 induction will reduce contraceptive efficacy significantly. "
            "Switch to copper IUD or condoms BEFORE the first cenobamate dose (Schoretsanitis 2022). "
            "The Hormonal Contraceptives section will appear automatically in Tab 2."))
    if "Severe" in liver:
        alerts.append(("error",
            "**Severe hepatic impairment (Child-Pugh C):** Cenobamate is not recommended. "
            "Markedly reduced clearance — risk of serious toxicity."))
    if "Mild" in liver:
        alerts.append(("warning",
            "**Mild hepatic impairment (Child-Pugh B):** Maximum recommended dose is 200 mg/day. "
            "Monitor liver function tests every 4 weeks."))
    if egfr and egfr < 30:
        alerts.append(("error",
            "**Severe renal impairment (eGFR <30 ml/min):** Maximum recommended dose is 200 mg/day. "
            "Increase monitoring frequency."))
    elif egfr and egfr < 60:
        alerts.append(("warning",
            "**Moderate renal impairment (eGFR 30-60 ml/min):** Consider dose cap and slow titration. "
            "Monitor every 4 weeks."))
    if "DEE" in ep:
        alerts.append(("info",
            "**DEE / Pediatric indication:** Cenobamate is not approved for <18 years in most countries. "
            "Off-label evidence is emerging (Samanta 2025). Use only in specialist centers "
            "with MDT decision and full family counseling."))
    if "Generalized" in ep:
        alerts.append(("warning",
            "**Generalized epilepsy:** Cenobamate is approved for focal-onset seizures only (FDA/EMA). "
            "Evidence for primary generalized epilepsies is limited — use off-label with caution "
            "and document clinical rationale. Note that some generalized epilepsy syndromes (e.g. "
            "juvenile myoclonic epilepsy) may be worsened by sodium channel blockers."))

    if alerts:
        st.divider()
        st.subheader("Patient-Specific Alerts")
        for level, msg in alerts:
            getattr(st, level)(msg)

# ──────────────────────────────────────────────────────────────────────────────
# TAB 2 — Current Medications
# ──────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Current Antiseizure Medications")
    st.caption(
        "Select all drugs the patient currently receives and enter the total daily dose. "
        "Entering serum levels allows more accurate dose adjustment recommendations."
    )

    selected: dict = {}
    preg_status = st.session_state.get("pregnancy", "")
    show_contraceptives = "hormonal contraception" in preg_status.lower()

    for drug, ddata in DRUG_DB.items():
        # Hormonal contraceptives: only shown if selected in Tab 1
        if ddata.get("conditional_on_pregnancy") and not show_contraceptives:
            continue

        rl = risk_label(ddata["risk"])
        with st.expander(f"{rl}  **{drug}**  ·  {ddata['action']}"):
            active = st.checkbox(f"Patient currently receiving {drug}", key=f"chk_{drug}")
            if active:
                ca, cb = st.columns(2)
                with ca:
                    dose_val = st.number_input(
                        f"Total daily dose ({ddata['unit'] or 'units'})",
                        min_value=0.0, value=None, placeholder="Enter dose",
                        key=f"dose_{drug}",
                    )
                    # Max-dose sanity alert
                    if dose_val:
                        max_alert = dose_max_alert(drug, dose_val)
                        if max_alert:
                            st.warning(max_alert)
                with cb:
                    if ddata.get("has_serum") and ddata.get("serum_normal_range"):
                        lo, hi = ddata["serum_normal_range"]
                        serum_val = st.number_input(
                            f"Current serum level (mcg/mL)  [Therapeutic: {lo}–{hi}]",
                            min_value=0.0, value=None, placeholder="Optional",
                            key=f"serum_{drug}",
                        )
                    else:
                        serum_val = None

                st.info(f"**Mechanism:** {ddata['mechanism']}")
                if ddata.get("two_way"):
                    st.warning(f"**Bidirectional PK interaction:** {ddata['two_way']}")
                if ddata.get("is_inducer"):
                    st.warning(
                        f"**Inducer washout alert:** When {drug} is tapered or stopped, "
                        "levels of co-administered CYP3A4/UGT substrates will rise. "
                        "Monitor for toxicity and reduce affected drug doses as clinically indicated."
                    )
                st.caption(f"References: {fmt_refs(tuple(ddata['references']))}")

                selected[drug] = {"dose": dose_val or 0, "serum": serum_val}

    st.session_state["selected_drugs"] = selected

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3 — Interaction Analysis
# ──────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Safety Flags — Read Before Proceeding")
    for flag in SAFETY_FLAGS:
        st.markdown(
            f"<div style='background:{flag['bg']};border-left:4px solid {flag['border']};"
            f"padding:12px 16px;border-radius:6px;margin-bottom:10px'>"
            f"<strong>{flag['emoji']} {flag['title']} — {flag['subtitle']}</strong><br>"
            f"<span style='font-size:13px'>{flag['body']}</span><br>"
            f"<span style='font-size:11px;color:#555'>Evidence: {fmt_refs(tuple(flag['refs']))}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    sd = st.session_state.get("selected_drugs", {})
    if not sd:
        st.info("Select medications in Tab 2 to view interaction analysis.")
    else:
        st.divider()
        st.subheader("Drug-Specific Interaction Summary")
        for drug, info in sd.items():
            d      = DRUG_DB[drug]
            bg, bd = risk_colors(d["risk"])
            sa     = serum_alert(drug, info.get("serum"))
            ds     = f"{info['dose']} {d['unit']}" if info.get("dose") else "dose not entered"

            html = (
                f"<div style='background:{bg};border-left:4px solid {bd};"
                f"padding:12px 16px;border-radius:6px;margin-bottom:10px'>"
                f"<strong>{risk_label(d['risk'])} — {drug}</strong>"
                f"&nbsp;<span style='font-size:12px;color:#555'>Current dose: {ds}</span><br>"
                f"<span style='font-size:13px'>{d['mechanism']}</span><br>"
                f"<b>Recommendation:</b> <span style='font-size:13px'>{d['recommendation']}</span>"
            )
            if sa:
                html += (
                    f"<br><span style='color:#B71C1C;font-weight:500;font-size:12px'>"
                    f"SERUM ALERT: {sa}</span>"
                )
            # Dose threshold note (e.g. Clobazam ≤20 mg/day → no adjustment)
            threshold = DRUG_DB[drug].get("dose_adjustment_threshold")
            if threshold and info.get("dose"):
                actual_dose = float(info["dose"])
                if actual_dose <= threshold:
                    html += (
                        f"<br><span style='color:#1565C0;font-weight:500;font-size:12px'>"
                        f"ℹ️ Current dose ({int(actual_dose)} mg/day) is ≤{threshold} mg/day — "
                        f"dose held unchanged throughout titration. Monitor clinically.</span>"
                    )
                else:
                    html += (
                        f"<br><span style='color:#B71C1C;font-weight:500;font-size:12px'>"
                        f"⚠️ Current dose ({int(actual_dose)} mg/day) exceeds {threshold} mg/day — "
                        f"dose reduction per schedule is recommended.</span>"
                    )
            if d.get("two_way"):
                html += (
                    f"<br><span style='color:#1B5E20;font-size:12px'>"
                    f"Bidirectional PK: {d['two_way']}</span>"
                )
            html += (
                f"<br><span style='font-size:11px;color:#555'>"
                f"Evidence: {fmt_refs(tuple(d['references']))}</span></div>"
            )
            st.markdown(html, unsafe_allow_html=True)

        # ── SODIUM CHANNEL BLOCKER CONFLICT DETECTION ──────────────────────
        active_scbs = get_active_scbs(sd)
        # Cenobamate itself is an SCB, so if ANY SCB is in the list, conflict exists
        if active_scbs:
            st.divider()
            st.markdown(
                "<div style='background:#FFF3E0;border-left:5px solid #E65100;"
                "padding:14px 18px;border-radius:8px;margin-bottom:12px'>"
                "<strong>⚡ DELPHI PANEL ALERT — Dual Sodium Channel Blocker Combination</strong><br>"
                "<span style='font-size:13px'>"
                "The Steinhoff 2024 Delphi consensus recommends <b>proactive discontinuation</b> of "
                "one sodium channel blocker (SCB) when cenobamate (itself an SCB) is introduced. "
                "Combining two SCBs increases the risk of CNS adverse effects (dizziness, diplopia, "
                "ataxia, fatigue) and may not confer additional seizure benefit.<br><br>"
                f"<b>Detected concomitant SCB(s) in this patient:</b> "
                f"{', '.join(active_scbs)}"
                "</span><br>"
                "<span style='font-size:11px;color:#555'>"
                "Evidence: Steinhoff BJ et al., Ther Adv Neurol Disord 2024 [Delphi panel]  |  "
                "Smith MC et al., Neurol Ther 2022 [Expert consensus]"
                "</span></div>",
                unsafe_allow_html=True,
            )

            st.subheader("🔴 Clinical Decision Required — Which SCB to Discontinue?")
            st.caption(
                "Please review the clinical profile and select the drug you wish to taper and "
                "discontinue during the cenobamate titration period. A 12-week taper schedule "
                "will be generated automatically in the Titration Plan tab."
            )

            scb_options = ["— Physician decision pending —"] + active_scbs + ["None — maintain all SCBs (document rationale)"]

            # Show mechanism of each candidate to aid decision
            for scb in active_scbs:
                st.markdown(
                    f"<div style='background:#F3F3F3;border-radius:6px;"
                    f"padding:8px 14px;margin-bottom:6px;font-size:13px'>"
                    f"<b>{scb}</b>: {SCB_DRUGS[scb]}</div>",
                    unsafe_allow_html=True,
                )

            chosen = st.selectbox(
                "Select the SCB to taper and discontinue:",
                options=scb_options,
                key="scb_to_discontinue",
            )

            if chosen and chosen not in ("— Physician decision pending —", "None — maintain all SCBs (document rationale)"):
                base = sd[chosen].get("dose", 0)
                st.success(
                    f"✅ **Decision recorded:** {chosen} will be tapered over 12 weeks "
                    f"(baseline dose: {base} mg/day). "
                    f"A step-wise taper column will appear in the Titration Plan tab."
                )

                # ── CASCADE DDI WARNING ─────────────────────────────────────
                cascade = get_cascade_warnings(chosen, sd)
                if cascade:
                    st.divider()
                    st.markdown(
                        "<div style='background:#FDECEA;border-left:5px solid #C62828;"
                        "padding:14px 18px;border-radius:8px;margin-bottom:12px'>"
                        "<strong>🔴 INDUCER WASHOUT — CASCADE DDI ALERT</strong><br>"
                        "<span style='font-size:13px'>"
                        f"When <b>{chosen}</b> is tapered and discontinued, its enzyme-inducing "
                        "effect will wear off (washout). Drugs that were being induced will have "
                        "<b>rising plasma levels</b> — this may cause toxicity if unmanaged. "
                        "The following co-medications in this patient's regimen will be affected:"
                        "</span></div>",
                        unsafe_allow_html=True,
                    )
                    for cw in cascade:
                        st.markdown(
                            f"<div style='background:#FFF8F8;border-left:3px solid #E57373;"
                            f"padding:10px 14px;border-radius:5px;margin-bottom:8px'>"
                            f"<strong>{cw['drug']}</strong> — {cw['change']}<br>"
                            f"<span style='font-size:12px;color:#555'>"
                            f"📋 <b>Recommended action:</b> {cw['action']}</span></div>",
                            unsafe_allow_html=True,
                        )
                    st.caption(
                        "Evidence basis: Roberti 2021 (CYP/UGT induction mechanisms); "
                        "Smith 2022 (expert consensus); Landmark 2026; Charlier 2026."
                    )

            elif chosen == "None — maintain all SCBs (document rationale)":
                st.warning(
                    "⚠️ Maintaining dual SCB combination. Please document the clinical rationale "
                    "in the patient record. Enhanced monitoring for CNS adverse effects is recommended."
                )

# ──────────────────────────────────────────────────────────────────────────────
# TAB 4 — Titration Plan
# ──────────────────────────────────────────────────────────────────────────────
with tab4:
    sd = st.session_state.get("selected_drugs", {})
    if not sd:
        st.info("Select medications in Tab 2 to generate the titration plan.")
    else:
        # ── SCB taper decision from Tab 3 ────────────────────────────────────
        scb_choice = st.session_state.get("scb_to_discontinue", "— Physician decision pending —")
        taper_drug = None
        if scb_choice and scb_choice not in (
            "— Physician decision pending —",
            "None — maintain all SCBs (document rationale)",
        ):
            taper_drug = scb_choice

        if taper_drug:
            st.markdown(
                f"<div style='background:#FFF3E0;border-left:4px solid #E65100;"
                f"padding:10px 16px;border-radius:6px;margin-bottom:12px'>"
                f"⚡ <b>Delphi panel recommendation applied:</b> "
                f"<b>{taper_drug}</b> taper schedule is included in the table below "
                f"(12-week step-wise discontinuation alongside cenobamate titration).<br>"
                f"<span style='font-size:11px;color:#666'>"
                f"Basis: Steinhoff BJ et al., Ther Adv Neurol Disord 2024</span></div>",
                unsafe_allow_html=True,
            )

        st.subheader("12-Week Cenobamate Titration Schedule")
        st.caption(
            "Standard titration per Steinhoff 2024 Delphi consensus and Smith 2022 expert opinion. "
            "Dose adjustments calculated from the baseline doses entered in Tab 2."
        )

        # Build extended table including taper column if applicable
        rows = []
        for i, (wk, xcop) in enumerate(zip(WEEK_LABELS, XCOP_SCHEDULE)):
            row = {"Week": wk, "Xcopri (Cenobamate)": f"{xcop} mg"}

            # Taper column first (highlighted)
            if taper_drug and taper_drug in sd:
                base = float(sd[taper_drug].get("dose") or 0)
                row[f"⛔ TAPER → {taper_drug}"] = taper_dose_str(taper_drug, base, i)

            # Regular adjustment columns (skip the drug being tapered — it has its own column)
            for drug, info in sd.items():
                if drug == taper_drug:
                    continue
                base = float(info.get("dose") or 0)
                pct  = DRUG_DB[drug]["pct_per_period"][i]
                row[drug] = compute_dose(base, pct, drug) if base else "—"

            rows.append(row)

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Taper rationale box
        if taper_drug:
            tbase = float(sd[taper_drug].get("dose") or 0)
            taper_detail = " → ".join(
                taper_dose_str(taper_drug, tbase, i) for i in range(6)
            )
            st.info(
                f"**{taper_drug} taper sequence (weeks 1–12):**  \n{taper_detail}  \n\n"
                f"*Mechanism: {SCB_DRUGS.get(taper_drug, '')}  ·  "
                f"Taper per Delphi panel guidance (Steinhoff 2024)*"
            )

        st.divider()
        st.subheader("Morning / Evening Dose Breakdown")
        st.caption(
            "Cenobamate is given once daily (evening preferred per prescribing information). "
            "Concomitant drug splits are shown for reference — adapt to patient's existing schedule."
        )
        # AM/PM table: pass ALL drugs (including taper_drug) so build_me_df
        # can compute the taper schedule. build_me_df handles the split internally.
        sd_all_frozen = tuple((k, v.get("dose", 0), v.get("serum")) for k, v in sd.items())
        # Build a base df without the taper column (regular drugs only) for AM/PM parsing
        sd_no_taper = {k: v for k, v in sd.items() if k != taper_drug}
        sd_no_taper_frozen = tuple((k, v.get("dose", 0), v.get("serum")) for k, v in sd_no_taper.items())
        base_df = build_df(sd_no_taper_frozen)
        st.dataframe(build_me_df(sd_all_frozen, base_df.to_json(), taper_drug=taper_drug), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Pharmacological Notes")
        if taper_drug:
            st.markdown(
                f"**{taper_drug} (being discontinued)** — {SCB_DRUGS.get(taper_drug, '')}  \n"
                f"*Rationale for discontinuation: Delphi panel recommendation against dual SCB '  \n"
                f"combination with cenobamate (Steinhoff BJ et al., 2024)*"
            )
        for drug in sd:
            if drug == taper_drug:
                continue
            d     = DRUG_DB[drug]
            basis = ("CYP2C19 inhibition by cenobamate"
                     if "CYP2C19" in d["mechanism"]
                     else "CYP3A4/2B6 induction by cenobamate")
            st.markdown(
                f"**{drug}** — {d['mechanism']}  \n"
                f"*Basis: {basis} · {fmt_refs(tuple(d['references']))}*"
            )

        st.divider()
        st.subheader("Export")
        ca, cb = st.columns(2)

        with ca:
            csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "⬇️ Download CSV",
                data=csv_bytes,
                file_name=f"xcopri_titration_{date.today()}.csv",
                mime="text/csv",
            )

        with cb:
            pt_info = {
                "Age":              st.session_state.get("age"),
                "Sex":              st.session_state.get("gender"),
                "Weight":           f"{st.session_state.get('weight')} kg" if st.session_state.get("weight") else None,
                "Epilepsy type":    st.session_state.get("epilepsy"),
                "eGFR":             f"{st.session_state.get('egfr')} ml/min" if st.session_state.get("egfr") else None,
                "Hepatic function": st.session_state.get("liver"),
                "Pregnancy/contraception": st.session_state.get("pregnancy"),
                "SCB to discontinue": taper_drug or "None selected",
            }
            try:
                patient_frozen = tuple(pt_info.items())
                sd_frozen      = tuple((k, v.get("dose", 0), v.get("serum")) for k, v in sd.items())
                pdf_bytes = make_pdf(patient_frozen, sd_frozen, df.to_json())
                st.download_button(
                    "⬇️ Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"xcopri_titration_{date.today()}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF generation error: {e}  —  ensure reportlab is installed.")

        st.divider()
        st.markdown(
            "<div style='background:#F3E5F5;border-left:4px solid #7B1FA2;"
            "padding:10px 16px;border-radius:6px;margin-bottom:8px'>"
            "<strong>ℹ️ Scope of Recommendations — Important</strong><br>"
            "<span style='font-size:12px'>"
            "All recommendations in this tool apply to patients with <b>normal hepatic and renal function</b>, "
            "no significant co-morbidities beyond epilepsy, and no additional medications beyond those entered above. "
            "Dose adjustments are based on <b>cenobamate up to 200 mg/day</b> — further adjustments may be "
            "required at higher doses. Individual pharmacokinetic variability (CYP2C19 genotype, body composition, "
            "age, sex) may significantly alter the magnitude of interactions. "
            "These recommendations serve as a starting point; therapeutic drug monitoring is strongly encouraged "
            "for all drugs with available serum assays."
            "</span></div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "This tool provides clinical decision support only. "
            "All dosing decisions remain the sole responsibility of the treating physician. "
            "Evidence base: 21 peer-reviewed publications and regulatory documents (2019–2026)."
        )

# ──────────────────────────────────────────────────────────────────────────────
# TAB 5 — Evidence Base
# ──────────────────────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Full Evidence Base — 21 Publications and Regulatory Documents (2019–2026)")
    st.caption(
        "All pharmacokinetic interaction logic, dose adjustment recommendations, "
        "and safety flags in this tool are derived from the following sources."
    )
    for authors, year, title, journal, doi, pmid, relevance in PAPER_LIST:
        with st.expander(f"**{authors} ({year})** — {title[:75]}"):
            st.write(f"**Journal/Source:** {journal}")
            if doi.startswith("http"):
                st.write(f"**URL:** [{doi}]({doi})")
            else:
                st.write(f"**DOI:** [{doi}](https://doi.org/{doi})")
            if pmid:
                st.write(f"**{pmid}**")
            st.info(f"**Relevance to this tool:** {relevance}")

    st.divider()
    st.markdown(
        f"<div style='text-align:center;color:#888;font-size:12px;padding:10px'>"
        f"Xcopri Transition Tool &nbsp;·&nbsp; Version {APP_VERSION} &nbsp;·&nbsp; "
        f"Last updated {APP_LAST_UPDATED} &nbsp;·&nbsp; "
        f"Clinical decision support only — see disclaimer accepted at entry.</div>",
        unsafe_allow_html=True,
    )

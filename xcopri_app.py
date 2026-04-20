"""
Xcopri (Cenobamate) Clinical Transition & Interaction Tool
===========================================================
Evidence-based on 16 peer-reviewed publications (2020-2026):

[1]  Abou-Khalil BW (2022). Continuum. doi:10.1212/CON.0000000000001104
[2]  Roberti R et al. (2021). CNS Drugs. doi:10.1007/s40263-021-00819-8
[3]  Smith MC et al. (2022). Neurol Ther. doi:10.1007/s40120-022-00400-5
[4]  Sperling MR et al. (2020). Epilepsia. doi:10.1111/epi.16525
[5]  Schoretsanitis G et al. (2022). Expert Opin Drug Metab Toxicol. doi:10.1080/17425255.2022.2106214
[6]  Steinhoff BJ et al. (2024). Ther Adv Neurol Disord. doi:10.1177/17562864241256733
[7]  Osborn M & Abou-Khalil B (2023). Epilepsy Behav. doi:10.1016/j.yebeh.2023.109156
[8]  Samanta D (2025). Epilepsy Behav. doi:10.1016/j.yebeh.2025.110787
[9]  Karazniewicz-Lada M et al. (2021). Int J Mol Sci. doi:10.3390/ijms22179582
[10] Operto FF et al. (2025). Front Pharmacol. doi:10.3389/fphar.2025.1668382
[11] Krauss GL et al. (2025). Epilepsia. doi:10.1111/epi.18304
[12] Zaccara G et al. (2021). Neuropsychiatr Dis Treat. doi:10.2147/NDT.S281490
[13] Johannessen Landmark C et al. (2026). Epilepsia. doi:10.1002/epi.70184
[14] Ciullo I et al. (2026). Epilepsia Open. doi:10.1002/epi4.70261
[15] Charlier B et al. (2026). Pharmaceutics. doi:10.3390/pharmaceutics18010092
[16] Cohen H et al. (2026). Epileptic Disord. doi:10.1002/epd2.70232

Run:  streamlit run xcopri_app.py
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
# REFERENCE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

REFERENCES = {
    "Roberti2021":        "Roberti R et al., CNS Drugs 2021 [CYP2C19 inhibition / CYP3A4-2B6 induction]",
    "Smith2022":          "Smith MC et al., Neurol Ther 2022 [Expert consensus dose adjustments]",
    "Osborn2023":         "Osborn M & Abou-Khalil B, Epilepsy Behav 2023 [Clobazam PK + PD synergy]",
    "Steinhoff2024":      "Steinhoff BJ et al., Ther Adv Neurol Disord 2024 [Delphi panel initiation]",
    "Sperling2020":       "Sperling MR et al., Epilepsia 2020 [Phase 3 open-label safety/DRESS]",
    "Schoretsanitis2022": "Schoretsanitis G et al., Expert Opin Drug Metab Toxicol 2022 [OC interactions]",
    "Karazniewicz2021":   "Karazniewicz-Lada M et al., Int J Mol Sci 2021 [PK DDI review incl. CBD]",
    "Operto2025":         "Operto FF et al., Front Pharmacol 2025 [Plasma levels & concomitant ASMs]",
    "Krauss2025":         "Krauss GL et al., Epilepsia 2025 [Tolerability & initiation strategies]",
    "Zaccara2021":        "Zaccara G et al., Neuropsychiatr Dis Treat 2021 [Safety: QT shortening]",
    "Landmark2026":       "Johannessen Landmark C et al., Epilepsia 2026 [Two-way PK interactions]",
    "Ciullo2026":         "Ciullo I et al., Epilepsia Open 2026 [Low-dose clobazam real-world]",
    "Charlier2026":       "Charlier B et al., Pharmaceutics 2026 [Cenobamate PK with co-ASMs]",
    "Cohen2026":          "Cohen H et al., Epileptic Disord 2026 [CYP2C9 & P-gp induction meta-analysis]",
    "Samanta2025":        "Samanta D, Epilepsy Behav 2025 [Pediatric epilepsy & DEE]",
    "AbouKhalil2022":     "Abou-Khalil BW, Continuum 2022 [ASM update 2022]",
}

PAPER_LIST = [
    ("Abou-Khalil BW", "2022",
     "Update on Antiseizure Medications 2022",
     "Continuum", "10.1212/CON.0000000000001104",
     "Broad ASM update; cenobamate mechanism and clinical positioning."),
    ("Roberti R et al.", "2021",
     "Pharmacology of Cenobamate: Mechanism of Action, PK, DDI and Tolerability",
     "CNS Drugs", "10.1007/s40263-021-00819-8",
     "Primary PK/DDI reference: CYP2C19 inhibition, CYP3A4/2B6 induction."),
    ("Smith MC et al.", "2022",
     "Dose Adjustment of Concomitant ASMs During Cenobamate: Expert Consensus",
     "Neurol Ther", "10.1007/s40120-022-00400-5",
     "Expert panel recommendations for all major concomitant ASM adjustments."),
    ("Sperling MR et al.", "2020",
     "Cenobamate as adjunctive treatment for focal seizures — Phase 3 open-label",
     "Epilepsia", "10.1111/epi.16525",
     "Safety data including DRESS surveillance during large-scale titration."),
    ("Schoretsanitis G et al.", "2022",
     "Drug-drug interactions between psychotropic medications and oral contraceptives",
     "Expert Opin Drug Metab Toxicol", "10.1080/17425255.2022.2106214",
     "Basis for hormonal contraceptive interaction guidance."),
    ("Steinhoff BJ et al.", "2024",
     "Therapeutic strategies during cenobamate initiation: Delphi panel",
     "Ther Adv Neurol Disord", "10.1177/17562864241256733",
     "Consensus on titration pace, DRESS prevention, concomitant drug management."),
    ("Osborn M & Abou-Khalil B", "2023",
     "The cenobamate-clobazam interaction: evidence of synergy + PK",
     "Epilepsy Behav", "10.1016/j.yebeh.2023.109156",
     "Defines N-CLB elevation and pharmacodynamic synergy."),
    ("Samanta D", "2025",
     "Cenobamate in pediatric epilepsy and DEE",
     "Epilepsy Behav", "10.1016/j.yebeh.2025.110787",
     "Off-label pediatric data; syndrome-specific considerations."),
    ("Karazniewicz-Lada M et al.", "2021",
     "PK DDIs among ASMs including CBD, COVID-19 drugs and nutrients",
     "Int J Mol Sci", "10.3390/ijms22179582",
     "CBD + cenobamate additive CYP2C19 inhibition; OXC/CBZ/PHT details."),
    ("Operto FF et al.", "2025",
     "Clinical predictors and concomitant ASM effects on seizure control vs. plasma cenobamate",
     "Front Pharmacol", "10.3389/fphar.2025.1668382",
     "Real-world plasma concentrations; VPA/LEV combinations."),
    ("Krauss GL et al.", "2025",
     "Improving tolerability of ASMs: when and how to use cenobamate",
     "Epilepsia", "10.1111/epi.18304",
     "Initiation strategies, QT monitoring, tolerability management."),
    ("Zaccara G et al.", "2021",
     "Critical Appraisal of Cenobamate as Adjunctive Treatment of Focal Seizures",
     "Neuropsychiatr Dis Treat", "10.2147/NDT.S281490",
     "Safety profile including QT shortening evidence."),
    ("Johannessen Landmark C et al.", "2026",
     "PK variability and complex two-way interactions with cenobamate",
     "Epilepsia", "10.1002/epi.70184",
     "KEY: bidirectional interactions — concomitant ASMs lower cenobamate levels."),
    ("Ciullo I et al.", "2026",
     "Low-dose clobazam adjunct in focal DRE with incomplete cenobamate response",
     "Epilepsia Open", "10.1002/epi4.70261",
     "Real-world rationale for low-dose clobazam add-on strategy."),
    ("Charlier B et al.", "2026",
     "Do Cenobamate PK Change with Co-Administered ASMs?",
     "Pharmaceutics", "10.3390/pharmaceutics18010092",
     "Quantifies bidirectional effects of CBZ, OXC, LTG on cenobamate troughs."),
    ("Cohen H et al.", "2026",
     "Induction of CYP2C9 and P-gp by ASMs: systematic review + meta-analysis",
     "Epileptic Disord", "10.1002/epd2.70232",
     "CYP2C9 induction and P-glycoprotein effects relevant to PHT, PHB, OXC."),
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
        "action": "Mandatory dose REDUCTION 25-50%",
        "mechanism": (
            "Cenobamate is a potent CYP2C19 inhibitor, markedly elevating the active "
            "metabolite N-desmethylclobazam (N-CLB) up to 3-fold. Risk of sedation, "
            "ataxia, respiratory depression. Pharmacodynamic synergy demonstrated beyond "
            "PK interaction alone. Real-world data support low-dose clobazam (5-10 mg/day) "
            "as add-on in incomplete responders."
        ),
        "recommendation": (
            "Dose adjustment is recommended only if the current daily dose exceeds 20 mg. "
            "If dose >20 mg/day: reduce by 25% at weeks 5-6, and by a further 25% at weeks 9-10 "
            "(total ~50% reduction). Monitor closely for excess sedation from week 3. "
            "If dose ≤20 mg/day: no proactive reduction required — monitor clinically. "
            "If incomplete response to cenobamate persists, consider adjunctive low-dose "
            "clobazam 5-10 mg/day per Ciullo 2026 real-world evidence."
        ),
        "dose_adjustment_threshold": 20,
        "pct_per_period": [0, 0, -25, -25, -50, -50],
        "serum_toxic_high": None,
        "references": ["Osborn2023", "Smith2022", "Steinhoff2024", "Ciullo2026"],
        "two_way": (
            "Two-way PK interaction: clobazam co-administration may also influence "
            "cenobamate plasma concentrations (Landmark 2026)."
        ),
    },

    "Phenytoin": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [100],
        "splittable": False,
        "serum_normal_range": (10, 20),
        "risk": "HIGH",
        "action": "Dose REDUCTION 25-40% + frequent serum level monitoring",
        "mechanism": (
            "CYP2C19 inhibition raises phenytoin levels substantially (non-linear Michaelis-Menten "
            "kinetics amplify risk disproportionately). Concurrent CYP2C9 induction by cenobamate "
            "may partially offset, but net effect is elevation. Risks: nystagmus, ataxia, "
            "diplopia, encephalopathy, cardiac toxicity."
        ),
        "recommendation": (
            "Reduce dose by 20% at weeks 5-6 and a further 20% at weeks 9-10. "
            "Check serum levels at baseline, week 4, week 8, and week 12. "
            "If serum level >15 mcg/mL at any point, accelerate reduction immediately."
        ),
        "pct_per_period": [0, 0, -20, -20, -40, -40],
        "serum_toxic_high": 20,
        "references": ["Roberti2021", "Smith2022", "Karazniewicz2021", "Cohen2026"],
        "two_way": None,
    },

    "Phenobarbital": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [15, 30, 60, 100],
        "splittable": True,
        "serum_normal_range": (15, 40),
        "risk": "HIGH",
        "action": "Dose REDUCTION 20-30% + serum monitoring",
        "mechanism": (
            "CYP2C19 inhibition increases phenobarbital exposure. P-glycoprotein induction "
            "by cenobamate may partially modulate distribution (Cohen 2026). "
            "Risks: CNS depression, respiratory depression, falls in elderly."
        ),
        "recommendation": (
            "Reduce dose by 15% at weeks 5-6 and a further 15% at weeks 9-10. "
            "Serum levels at baseline and every 4 weeks during titration."
        ),
        "pct_per_period": [0, 0, -15, -15, -30, -30],
        "serum_toxic_high": 40,
        "references": ["Roberti2021", "Smith2022", "Cohen2026"],
        "two_way": None,
    },

    "Lamotrigine": {
        "unit": "mg", "has_serum": False,
        "tablet_sizes": [25, 50, 100, 150, 200],
        "splittable": True,
        "risk": "MODERATE",
        "action": "Potential dose INCREASE 20-50%",
        "mechanism": (
            "CYP3A4 induction by cenobamate increases lamotrigine clearance; plasma levels "
            "may fall by up to 50%. Risk of breakthrough seizures in previously well-controlled "
            "patients. Bidirectional PK interaction also documented."
        ),
        "recommendation": (
            "Monitor for seizure recurrence from week 5. Consider increasing dose by 15% "
            "at weeks 5-6 and a further 15% at weeks 9-10 if clinical deterioration noted. "
            "Serum levels are helpful if available."
        ),
        "pct_per_period": [0, 0, 15, 15, 30, 30],
        "serum_toxic_high": None,
        "references": ["Roberti2021", "Smith2022", "Steinhoff2024", "Landmark2026"],
        "two_way": (
            "Two-way interaction: lamotrigine may influence cenobamate trough levels "
            "(Charlier 2026; Landmark 2026). Monitor cenobamate clinical response."
        ),
    },

    "Carbamazepine": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [100, 200, 400],
        "splittable": True,
        "serum_normal_range": (4, 12),
        "risk": "MODERATE",
        "action": "Potential dose INCREASE 15-30% + serum monitoring",
        "mechanism": (
            "CYP3A4 induction reduces carbamazepine levels. Carbamazepine itself is a "
            "strong CYP3A4 inducer, creating a complex bidirectional interaction where "
            "carbamazepine may also substantially reduce cenobamate plasma levels."
        ),
        "recommendation": (
            "Serum levels at baseline, weeks 4, 8, 12. Consider 10% dose increase "
            "at weeks 5-6 and a further 10% at weeks 9-10 if trough levels fall below target. "
            "May require higher cenobamate doses to achieve adequate plasma levels."
        ),
        "pct_per_period": [0, 0, 10, 10, 20, 20],
        "serum_toxic_high": 12,
        "references": ["Roberti2021", "Smith2022", "Landmark2026", "Charlier2026"],
        "two_way": (
            "STRONG two-way interaction: carbamazepine (CYP3A4 inducer) reduces cenobamate "
            "plasma levels by >30% — higher cenobamate target doses may be needed "
            "(Landmark 2026; Charlier 2026)."
        ),
    },

    "Valproate (VPA)": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [200, 300, 500],
        "splittable": True,
        "serum_normal_range": (50, 100),
        "risk": "LOW-MODERATE",
        "action": "Monitor — minor interaction, dose adjustment usually not required",
        "mechanism": (
            "Limited direct PK interaction. VPA is primarily metabolized via glucuronidation "
            "and beta-oxidation (not CYP2C19/3A4). Minor CYP2C9 induction effects possible. "
            "Real-world data (Operto 2025) show VPA co-administration is common and generally "
            "well tolerated."
        ),
        "recommendation": (
            "Check serum levels at baseline and every 6 weeks. Dose adjustment rarely required. "
            "Monitor liver enzymes especially in pediatric patients or those with metabolic disorders."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "serum_toxic_high": 100,
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
        "action": "No adjustment needed — favorable PK profile",
        "mechanism": (
            "Levetiracetam has minimal hepatic CYP metabolism (primarily renal excretion "
            "via hydrolysis). No significant PK interaction with cenobamate expected. "
            "Real-world co-administration data are positive (Operto 2025)."
        ),
        "recommendation": (
            "No dose adjustment required. Monitor clinical response. "
            "Behavioral side effects (irritability, aggression) may be additive at "
            "high cenobamate doses in some patients — assess at each visit."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "serum_toxic_high": None,
        "references": ["Roberti2021", "Operto2025", "AbouKhalil2022"],
        "two_way": None,
    },

    "Oxcarbazepine": {
        "unit": "mg", "has_serum": True,
        "tablet_sizes": [150, 300, 600],
        "splittable": True,
        "serum_normal_range": (3, 35),
        "risk": "MODERATE",
        "action": "Potential dose INCREASE — CYP3A4 induction reduces MHD levels",
        "mechanism": (
            "Cenobamate induces CYP3A4, reducing monohydroxy derivative (MHD/licarbazepine) "
            "levels. Oxcarbazepine itself induces CYP3A4, creating bidirectional PK effects. "
            "Hyponatremia risk may be additive."
        ),
        "recommendation": (
            "Monitor MHD serum levels (active metabolite) at baseline and weeks 4, 8. "
            "Consider 10-15% dose increase if MHD falls below therapeutic range. "
            "Check serum sodium at each visit. "
            "Expect that OXC will also reduce cenobamate levels — higher cenobamate "
            "doses may be needed."
        ),
        "pct_per_period": [0, 0, 10, 10, 20, 20],
        "serum_toxic_high": 35,
        "references": ["Roberti2021", "Karazniewicz2021", "Landmark2026", "Charlier2026"],
        "two_way": (
            "Two-way interaction: oxcarbazepine (CYP3A4 inducer) reduces cenobamate "
            "plasma trough levels — monitor clinical response and adjust cenobamate "
            "target dose accordingly (Charlier 2026)."
        ),
    },

    "Perampanel": {
        "unit": "mg", "has_serum": False,
        "tablet_sizes": [2, 4, 6, 8, 10, 12],
        "splittable": False,
        "risk": "MODERATE",
        "action": "Potential dose INCREASE — CYP3A4 induction lowers perampanel",
        "mechanism": (
            "Perampanel is primarily metabolized by CYP3A4 and CYP3A5. "
            "Cenobamate-mediated CYP3A4 induction can reduce perampanel plasma levels by 20-50%. "
            "Risk of breakthrough seizures."
        ),
        "recommendation": (
            "Monitor for loss of seizure control from week 5. "
            "Consider 2 mg dose increase if clinical deterioration occurs. "
            "Re-assess behavioral side effects (aggression, irritability) as dose changes "
            "may unmask or attenuate them."
        ),
        "pct_per_period": [0, 0, 15, 15, 25, 25],
        "serum_toxic_high": None,
        "references": ["Roberti2021", "Smith2022", "Steinhoff2024"],
        "two_way": None,
    },

    "Cannabidiol (CBD)": {
        "unit": "mg", "has_serum": False,
        "tablet_sizes": [100, 200],
        "splittable": False,
        "risk": "MODERATE",
        "action": "Monitor — additive CYP2C19 inhibition; adjust clobazam aggressively",
        "mechanism": (
            "CBD inhibits CYP2C19 and CYP3A4. Co-administration with cenobamate (also a "
            "CYP2C19 inhibitor) produces additive inhibition, further elevating N-CLB levels "
            "if clobazam is co-prescribed. CBD itself is metabolized by CYP3A4 and CYP2C19 "
            "and may accumulate under cenobamate CYP3A4 induction."
        ),
        "recommendation": (
            "If clobazam is co-prescribed, apply aggressive clobazam reductions (see Clobazam). "
            "Monitor liver enzymes especially if VPA co-administered (all three can be hepatotoxic). "
            "CBD dose may need reduction if sedation or elevated transaminases occur."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "serum_toxic_high": None,
        "references": ["Karazniewicz2021", "Steinhoff2024"],
        "two_way": None,
    },

    "Hormonal Contraceptives": {
        "unit": "", "has_serum": False,
        "risk": "HIGH",
        "action": "Switch to non-hormonal contraception BEFORE starting cenobamate",
        "mechanism": (
            "CYP3A4 induction markedly reduces estrogen and progestogen plasma levels. "
            "Applies to combined oral pills, progestogen-only pills, patches, vaginal rings, "
            "and hormonal IUDs. Effect persists for weeks after cenobamate discontinuation."
        ),
        "recommendation": (
            "Counsel before initiating cenobamate. Switch to copper IUD or condoms prior "
            "to first dose. If hormonal contraception is unavoidable, combine highest "
            "available estrogen dose with a barrier method and document counseling. "
            "Review at every visit."
        ),
        "pct_per_period": [None, None, None, None, None, None],
        "serum_toxic_high": None,
        "references": ["Schoretsanitis2022", "Roberti2021", "Smith2022"],
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
            "Discontinue immediately if rash, fever >=38.5C, lymphadenopathy, or eosinophilia develop. "
            "The 2024 Delphi panel (Steinhoff) recommends prophylactic antihistamine in high-risk "
            "patients (prior drug hypersensitivity, HLA-B*15:02 positive)."
        ),
        "refs": ["Sperling2020", "Steinhoff2024", "Krauss2025"],
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
            "ASMs (carbamazepine, oxcarbazepine, phenytoin, phenobarbital) reduce cenobamate plasma "
            "levels by 20-40%. This may require higher cenobamate target doses to achieve seizure "
            "control. Always monitor both directions of the interaction. "
            "Real-world concentration data (Operto 2025) support this bidirectional approach."
        ),
        "refs": ["Landmark2026", "Charlier2026", "Operto2025"],
        "bg": "#E8F5E9", "border": "#2E7D32",
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
    "Lacosamide":     "Slow-inactivation sodium channel blocker (SV2A independent)",
    "Carbamazepine":  "Fast-inactivation sodium channel blocker + CYP3A4 inducer",
    "Oxcarbazepine":  "Fast-inactivation sodium channel blocker (pro-drug → MHD)",
    "Phenytoin":      "Fast-inactivation sodium channel blocker (non-linear PK)",
    "Phenobarbital":  "GABA-A potentiator + sodium channel blocker component",
    "Lamotrigine":    "Fast/slow-inactivation sodium channel blocker",
}

# Gradual taper schedule per drug (6 periods × 2 weeks = 12 weeks total)
# Values: % of original dose to administer in that period (100 = full dose, 0 = stopped)
TAPER_SCHEDULE = {
    "Lacosamide":    [100, 75, 50, 25, 0,   0  ],
    "Carbamazepine": [100, 80, 60, 40, 20,  0  ],
    "Oxcarbazepine": [100, 80, 60, 40, 20,  0  ],
    "Phenytoin":     [100, 75, 50, 25, 0,   0  ],
    "Phenobarbital": [100, 85, 70, 50, 25,  0  ],
    "Lamotrigine":   [100, 75, 50, 25, 0,   0  ],
}

def get_active_scbs(selected: dict) -> list:
    """Return list of SCB drug names the patient is currently taking."""
    return [d for d in selected if d in SCB_DRUGS]

def taper_dose_str(drug: str, base_dose: float, period_idx: int) -> str:
    """Return tapered dose string for a given drug and titration period."""
    schedule = TAPER_SCHEDULE.get(drug)
    if not schedule or base_dose <= 0:
        return "—"
    pct = schedule[period_idx]
    if pct == 0:
        return "D/C"
    raw = base_dose * pct / 100
    sizes = DRUG_DB.get(drug, {}).get("tablet_sizes", [])
    splittable = DRUG_DB.get(drug, {}).get("splittable", False)
    dose_str = floor_tablet(raw, sizes, splittable) if sizes else f"{round(raw)} mg"
    return f"{dose_str} (↓{100 - pct}%)"

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def risk_colors(risk: str):
    return {
        "HIGH":         ("#FDECEA", "#C62828"),
        "MODERATE":     ("#FFF8E1", "#F57F17"),
        "LOW-MODERATE": ("#FFF8E1", "#F57F17"),
        "LOW":          ("#E8F5E9", "#2E7D32"),
    }.get(risk, ("#F5F5F5", "#9E9E9E"))


def risk_label(risk: str) -> str:
    return {
        "HIGH":         "🔴 HIGH RISK",
        "MODERATE":     "🟡 MODERATE",
        "LOW-MODERATE": "🟡 LOW-MODERATE",
        "LOW":          "🟢 LOW",
    }.get(risk, risk)


def floor_tablet(mg: float, sizes: list, splittable: bool = False) -> str:
    """Return the best achievable dose given available tablet sizes.
    If splittable=True, half-tablets are also considered (sizes + halves).
    Always rounds DOWN to the closest achievable dose. Never exceeds mg."""
    candidates = list(sizes)
    if splittable:
        candidates += [s / 2 for s in sizes]
    candidates = sorted(set(candidates))
    below = [c for c in candidates if c <= mg]
    best = max(below) if below else min(candidates)
    # Format: show as int if whole, or "X.5" if half
    if best == int(best):
        return f"{int(best)} mg"
    else:
        whole = int(best)
        return f"{whole + 0}½ mg ({int(best * 2)} mg tablet, split)"

def compute_dose(base: float, pct, drug: str = "") -> str:
    """Return adjusted dose string, rounded down to nearest achievable tablet dose."""
    if pct is None:
        return "Switch contraception"
    pct = float(pct)

    # Threshold check: hold dose unchanged
    threshold = DRUG_DB.get(drug, {}).get("dose_adjustment_threshold")
    if threshold and base <= threshold and pct != 0:
        return f"{int(base)} mg"  # hold at current dose

    if pct == 0:
        return f"{int(base)} mg" if base else "No change"

    raw = base * (1 + pct / 100)
    sizes = DRUG_DB.get(drug, {}).get("tablet_sizes", [])
    splittable = DRUG_DB.get(drug, {}).get("splittable", False)
    dose_str = floor_tablet(raw, sizes, splittable) if sizes else f"{round(raw)} mg"
    arrow = "↑" if pct > 0 else "↓"
    return f"{dose_str} ({arrow}{abs(int(pct))}%)"


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


def fmt_refs(keys: list) -> str:
    return "  |  ".join(REFERENCES[k] for k in keys if k in REFERENCES)


def build_df(selected: dict) -> pd.DataFrame:
    rows = []
    for i, (wk, xcop) in enumerate(zip(WEEK_LABELS, XCOP_SCHEDULE)):
        row = {"Week": wk, "Xcopri (Cenobamate)": f"{xcop} mg"}
        for drug, info in selected.items():
            base = float(info.get("dose") or 0)
            pct  = DRUG_DB[drug]["pct_per_period"][i]
            row[drug] = compute_dose(base, pct, drug) if base else "—"
        rows.append(row)
    return pd.DataFrame(rows)


def build_me_df(selected: dict, df: pd.DataFrame, taper_drug: str = None) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        r = {"Week": row["Week"], "Xcopri — Evening": row["Xcopri (Cenobamate)"]}

        # Include taper drug AM/PM if present
        if taper_drug:
            taper_col = f"⛔ TAPER → {taper_drug}"
            val = str(row.get(taper_col, "—"))
            if val == "D/C":
                r[f"{taper_drug} — AM"] = "D/C"
                r[f"{taper_drug} — PM"] = "D/C"
            elif "mg" in val:
                try:
                    mg = int(val.split(" mg")[0].strip())
                    half = mg // 2
                    r[f"{taper_drug} — AM"] = f"{half} mg"
                    r[f"{taper_drug} — PM"] = f"{mg - half} mg"
                except Exception:
                    r[f"{taper_drug} — AM"] = val
                    r[f"{taper_drug} — PM"] = "—"
            else:
                r[f"{taper_drug} — AM"] = val
                r[f"{taper_drug} — PM"] = "—"

        # Regular drugs
        for drug in selected:
            if drug == taper_drug:
                continue
            val = str(row.get(drug, "—"))
            if "mg" in val and "Switch" not in val and val != "—":
                try:
                    mg   = int(val.split(" mg")[0].strip())
                    half = mg // 2
                    r[f"{drug} — AM"] = f"{half} mg"
                    r[f"{drug} — PM"] = f"{mg - half} mg"
                except Exception:
                    r[drug] = val
            else:
                r[drug] = val
        rows.append(r)
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# PDF
# ═══════════════════════════════════════════════════════════════════════════════

def make_pdf(patient: dict, selected: dict, df: pd.DataFrame) -> bytes:
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
        story.append(Paragraph(f"Evidence: {fmt_refs(d['references'])}", S["small"]))
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

    story.append(Paragraph("Evidence Base (16 Publications, 2020-2026)", S["h2"]))
    for authors, year, title, journal, doi, _ in PAPER_LIST:
        story.append(Paragraph(f"{authors} ({year}). {title}. {journal}. doi:{doi}", S["small"]))

    story.append(Spacer(1, 5))
    story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#CCCCCC")))
    story.append(Paragraph(
        "DISCLAIMER: This report is for clinical decision support only. "
        "All dosing decisions remain the responsibility of the treating physician.",
        S["small"],
    ))

    doc.build(story)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG + UI
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Xcopri (Cenobamate) Transition Tool",
    page_icon="🧠", layout="wide",
)

st.title("🧠 Xcopri (Cenobamate) — Clinical Transition Tool")
st.caption(
    "Evidence-based drug interaction management for neurologists  ·  "
    "Grounded in **16 peer-reviewed publications (2020–2026)**"
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
            ["—", "Focal onset", "Generalized onset", "Unknown onset",
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
            "Switch to copper IUD or condoms BEFORE the first cenobamate dose (Schoretsanitis 2022)."))
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

    for drug, ddata in DRUG_DB.items():
        rl      = risk_label(ddata["risk"])
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
                with cb:
                    if ddata["has_serum"]:
                        lo, hi = ddata["serum_normal_range"]
                        serum_val = st.number_input(
                            f"Current serum level (mcg/mL)  [Therapeutic: {lo}-{hi}]",
                            min_value=0.0, value=None, placeholder="Optional",
                            key=f"serum_{drug}",
                        )
                    else:
                        serum_val = None

                st.info(f"**Mechanism:** {ddata['mechanism']}")
                if ddata.get("two_way"):
                    st.warning(f"**Bidirectional PK interaction:** {ddata['two_way']}")
                st.caption(f"References: {fmt_refs(ddata['references'])}")

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
            f"<span style='font-size:11px;color:#555'>Evidence: {fmt_refs(flag['refs'])}</span>"
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
                f"Evidence: {fmt_refs(d['references'])}</span></div>"
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
        # Pass sd minus taper drug for the AM/PM table; taper drug shown separately
        sd_no_taper = {k: v for k, v in sd.items() if k != taper_drug}
        base_df = build_df(sd_no_taper)
        st.dataframe(build_me_df(sd_no_taper, df, taper_drug=taper_drug), use_container_width=True, hide_index=True)

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
                f"*Basis: {basis} · {fmt_refs(d['references'])}*"
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
                pdf_bytes = make_pdf(pt_info, sd, df)
                st.download_button(
                    "⬇️ Download PDF Report",
                    data=pdf_bytes,
                    file_name=f"xcopri_titration_{date.today()}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF generation error: {e}  —  ensure reportlab is installed.")

        st.caption(
            "This tool provides clinical decision support only. "
            "All dosing decisions remain the sole responsibility of the treating physician. "
            "Evidence base: 16 peer-reviewed publications, 2020–2026."
        )

# ──────────────────────────────────────────────────────────────────────────────
# TAB 5 — Evidence Base
# ──────────────────────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Full Evidence Base — 16 Publications (2020–2026)")
    st.caption(
        "All pharmacokinetic interaction logic, dose adjustment recommendations, "
        "and safety flags in this tool are derived from the following publications."
    )
    for authors, year, title, journal, doi, relevance in PAPER_LIST:
        with st.expander(f"**{authors} ({year})** — {title[:80]}"):
            st.write(f"**Journal:** {journal}")
            st.write(f"**DOI:** [{doi}](https://doi.org/{doi})")
            st.info(f"**Relevance to this tool:** {relevance}")

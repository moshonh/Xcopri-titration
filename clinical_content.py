"""Clinical content overlay for the cenobamate prototype.

Call ``apply_clinical_content(DRUG_DB)`` immediately after defining DRUG_DB.
The overlay mutates the existing entries in place and returns the same mapping.
It preserves the original drug names and field schema, and has no Streamlit or
third-party dependencies. Reference values are the application's existing
reference-registry keys, not new references that the existing renderer would
silently discard.

This content is not a validated clinical algorithm; regulatory status must be
determined under applicable local law. The
surrounding UI, its serum alert, taper logic, contraindication text, safety
flags and reference registry must also be corrected and independently reviewed;
this module cannot make those independent components safe by itself. In
particular, no automated schedule is a substitute for a prescriber's decision.
"""

from copy import deepcopy


# Evidence: FDA XCOPRI 2025 label, sections 5.4, 7.1 and 12.3;
# EMA Ontozry SmPC sections 4.4-4.6; Smith et al., Neurol Ther 2022,
# doi:10.1007/s40120-022-00400-5; Steinhoff et al. 2024,
# doi:10.1177/17562864241256733; Johannessen Landmark et al. 2026,
# doi:10.1002/epi.70184. See clinical_changes.md for source links and limits.
# Lists are copied before insertion to make repeated calls independent.
_UPDATES = {
    "Clobazam": {
        "risk": "HIGH",
        "action": "Review for proactive or symptom-guided reduction; monitor sedation",
        "mechanism": (
            "Cenobamate inhibits CYP2C19 and can substantially increase the active "
            "metabolite N-desmethylclobazam, with considerable individual variability; "
            "CYP3A4 induction can also affect metabolite formation. Somnolence, "
            "sedation and other CNS effects may increase. An additional beneficial "
            "pharmacodynamic interaction has been suggested, not established as a "
            "reason to ignore adverse effects."
        ),
        "recommendation": (
            "The >20 mg/day threshold is an unvalidated app rule based on developer experience for "
            "considering a proactive reduction, not an established cutoff, safety "
            "ceiling, FDA rule, or consensus requirement. The clinician must decide "
            "whether and when any reduction is appropriate. The 2024 Delphi paper's "
            "main text gives at least 40 mg/day as an example of a high dose for "
            "proactive reduction; its Figure 3 uses at least 20 mg/day. Neither "
            "establishes this app's >20 mg/day cutoff or numerical schedule. "
            "At 20 mg/day or less, this rule does NOT mean that "
            "no reduction is appropriate. Smith et al. suggest that patients receiving "
            "10–20 mg/day may be considered for a 5–10 mg/day reduction when cenobamate "
            "reaches 100 mg/day; assess earlier if adverse effects occur. Individualize "
            "for sedation, seizure control, other CNS depressants, CBD and patient factors. "
            "Clobazam and N-desmethylclobazam concentrations may be helpful when available."
        ),
        "dose_adjustment_threshold": 20,
        "pct_per_period": [0, 0, -25, -25, -50, -50],
        "references": ["FDA2019", "EMA2021", "Smith2022", "Steinhoff2024", "Landmark2026"],
        "two_way": (
            "The EU SmPC predicts a modest increase in cenobamate exposure with "
            "clobazam; individual effects vary. Do not infer a required dose change."
        ),
    },
    "Phenytoin": {
        "risk": "HIGH",
        "action": "Review and individualize phenytoin reduction; monitor concentrations",
        "mechanism": (
            "Cenobamate inhibits CYP2C19 and can substantially increase phenytoin "
            "concentrations. Nonlinear phenytoin kinetics and additive neurological "
            "effects make individual review important. Phenytoin can reduce "
            "cenobamate exposure in a controlled interaction study."
        ),
        "recommendation": (
            "Follow the applicable product label and specialist plan. The US label "
            "advises gradually decreasing phenytoin by up to 50% while cenobamate is "
            "titrated; the EU label calls for concentration monitoring and an "
            "individualized reduction when needed. Assess baseline and follow-up "
            "concentrations with sampling conditions, binding, symptoms and seizure "
            "control. The expert panel gives drug- and baseline-level-specific "
            "proactive guidance. A concentration alert alone is not an instruction "
            "to accelerate a taper. Do not assume a higher cenobamate target is needed."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "references": ["FDA2019", "EMA2021", "Smith2022", "Steinhoff2024"],
        "two_way": (
            "Phenytoin reduced cenobamate exposure in a controlled study; the EU "
            "SmPC says no cenobamate adjustment is required for this combination. "
            "Assess efficacy and tolerability individually rather than preselecting "
            "a higher target."
        ),
    },
    "Phenobarbital": {
        "risk": "HIGH",
        "action": "Consider individualized phenobarbital reduction and monitoring",
        "mechanism": (
            "Cenobamate can increase phenobarbital exposure, with potential CNS "
            "depression. The controlled study in the EU SmPC did not show a "
            "clinically meaningful effect of phenobarbital on cenobamate exposure."
        ),
        "recommendation": (
            "Monitor phenobarbital concentrations and clinical adverse effects "
            "during cenobamate titration and consider a patient-specific reduction, "
            "including proactive management where appropriate. The Smith consensus "
            "offers concentration- and cenobamate-dose-specific advice. Avoid abrupt "
            "barbiturate withdrawal; individualize any taper. When an inducer is "
            "withdrawn, review affected co-medications and monitor as appropriate."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "references": ["FDA2019", "EMA2021", "Smith2022", "Steinhoff2024"],
        "two_way": None,
    },
    "Lamotrigine": {
        "risk": "MODERATE",
        "action": "Monitor seizure control and tolerability; individualize any change",
        "mechanism": (
            "Cenobamate can lower lamotrigine concentrations; the mechanism is not "
            "established as cenobamate induction of UGT1A4. EU population analyses "
            "estimated average decreases of 21–52% over cenobamate doses of "
            "100–400 mg/day; these do not predict the dose change for an individual. "
            "Neurological adverse effects can also occur with combined sodium "
            "channel blockers."
        ),
        "recommendation": (
            "The US label advises increasing lamotrigine as needed for reduced "
            "efficacy. Expert opinion instead does not routinely increase it and "
            "may favor reduction for tolerability; consider applicable local labeling. "
            "The app may suggest a lamotrigine increase based on developer experience; it is "
            "unvalidated, is not an FDA or consensus-recommended schedule, and is not a "
            "mandatory dose change. Any adjustment requires an explicit "
            "clinician decision. Consider "
            "seizures, adverse effects, other medication changes and levels when "
            "useful; an inducer's withdrawal may raise lamotrigine concentrations."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "references": ["FDA2019", "EMA2021", "Smith2022", "Steinhoff2024", "Landmark2026"],
        "two_way": None,
    },
    "Carbamazepine": {
        "risk": "MODERATE",
        "action": "Monitor clinical response and tolerability; individualize any change",
        "mechanism": (
            "Cenobamate lowers carbamazepine exposure; both drugs can contribute "
            "to neurological adverse effects. In a controlled interaction study, "
            "carbamazepine did not meaningfully change cenobamate exposure. "
            "Carbamazepine is an inducer of other drug-metabolizing pathways."
        ),
        "recommendation": (
            "The US label advises increasing carbamazepine as needed for reduced "
            "efficacy; the EU SmPC does not require routine dose adjustment for "
            "either drug. Expert consensus also emphasizes tolerability and may "
            "consider reduction rather than automatic increases. If carbamazepine "
            "is tapered, concentrations of affected drugs such as lamotrigine can "
            "rise as induction wanes; review, monitor and individualize any change. "
            "A universal washout dose reduction is not supported."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "references": ["FDA2019", "EMA2021", "Smith2022", "Steinhoff2024", "Landmark2026"],
        "two_way": (
            "The controlled EU SmPC study found no significant change in cenobamate "
            "exposure with carbamazepine; observational polytherapy findings do not "
            "establish a universal decrease or a required higher cenobamate dose."
        ),
    },
    "Valproate (VPA)": {
        "risk": "LOW-MODERATE",
        "action": "Review liver safety and monitor clinical tolerability",
        "mechanism": (
            "The EU SmPC reports no clinically relevant pharmacokinetic interaction "
            "between valproate and cenobamate in the studied setting. Both have "
            "recognized hepatic safety concerns; an increase in liver injury risk "
            "from this specific combination has not been established."
        ),
        "recommendation": (
            "Follow both product labels and assess hepatic symptoms. For cenobamate, "
            "the US label calls for baseline ALT, AST and total bilirubin if not "
            "recently available, monitoring during treatment and prompt tests if "
            "liver injury is suspected; interrupt or discontinue for liver injury "
            "without an alternative etiology. The EU SmPC recommends a broader "
            "baseline panel and monitoring during treatment. No universal "
            "cenobamate stop rule at isolated ALT/AST >3× ULN is specified. "
            "If cannabidiol is also used, follow its separate product-specific "
            "hepatic monitoring and stopping rules."
        ),
        "references": ["FDA2019", "EMA2021", "Smith2022"],
        "two_way": None,
    },
    "Lacosamide": {
        "risk": "MODERATE",
        "action": "Assess dizziness, gait and cardiac conduction risks",
        "mechanism": (
            "Both medications affect sodium channels and may contribute to "
            "dizziness, diplopia or ataxia. No clinically relevant pharmacokinetic "
            "interaction was identified in the EU SmPC. Lacosamide can prolong PR "
            "interval, while cenobamate can shorten QT; these are different "
            "electrophysiologic effects, not a documented cancellation."
        ),
        "recommendation": (
            "Individualize concomitant drug reduction if adverse effects occur. "
            "The Delphi panel suggests considering lacosamide reduction at "
            "400 mg/day or more and proactive management when the pre-existing "
            "regimen contains at least two sodium channel blockers. Evaluate "
            "cardiac history, interacting medications and ECG where clinically "
            "indicated under the lacosamide label; no universal PR cutoff or "
            "automatic withdrawal is implied."
        ),
        "references": ["FDA2019", "EMA2021", "Smith2022", "Steinhoff2024"],
        "two_way": None,
    },
    "Levetiracetam": {
        "risk": "LOW",
        "action": "Monitor clinical and behavioral tolerability",
        "mechanism": (
            "A clinically relevant pharmacokinetic interaction with cenobamate "
            "was not identified in the EU SmPC. CNS and behavioral symptoms "
            "may still warrant individual assessment."
        ),
        "recommendation": (
            "No routine pharmacokinetic dose change is established. Review "
            "somnolence, behavior, mood and seizure control; adjust only after "
            "individual clinical assessment."
        ),
        "references": ["EMA2021", "Smith2022"],
        "two_way": None,
    },
    "Oxcarbazepine": {
        "risk": "MODERATE",
        "action": "Monitor sodium, seizure control and neurological tolerability",
        "mechanism": (
            "The EU SmPC did not identify a clinically relevant interaction "
            "between oxcarbazepine and cenobamate exposures. Oxcarbazepine "
            "can cause hyponatremia, and neurological adverse effects may be "
            "more troublesome with concomitant sodium channel blockers."
        ),
        "recommendation": (
            "No routine pharmacokinetic increase is supported. Consider serum "
            "sodium and clinical status according to oxcarbazepine labeling and "
            "patient risk. Consider individualized reduction for adverse effects "
            "or multiple concomitant sodium channel blockers. If oxcarbazepine is "
            "withdrawn, evaluate clinically relevant inducer-washout interactions; "
            "do not apply a universal adjustment."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "references": ["EMA2021", "Smith2022", "Steinhoff2024"],
        "two_way": None,
    },
    "Perampanel": {
        "risk": "MODERATE",
        "action": "Monitor seizure control and CNS or behavioral effects",
        "mechanism": (
            "Perampanel is metabolized by CYP3A4/5, which cenobamate can induce; "
            "the magnitude of any individual interaction is uncertain. The claim "
            "that perampanel above 10 mg/day reliably lowers cenobamate exposure "
            "is unsupported."
        ),
        "recommendation": (
            "Assess seizure control, dizziness, fatigue and behavioral symptoms. "
            "An adjustment may be considered only on an individual basis with "
            "reference to the perampanel label; do not apply an automatic increase. "
            "Changing another inducer may also alter perampanel exposure."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "references": ["FDA2019", "Smith2022"],
        "two_way": None,
    },
    "Cannabidiol (CBD)": {
        "risk": "MODERATE",
        "action": "Review sedation, other interactions and product-specific liver monitoring",
        "mechanism": (
            "CBD and cenobamate can each affect CYP2C19, but the magnitude and "
            "clinical consequences of combining them are not established as a "
            "predictable additive interaction. CBD can increase active "
            "N-desmethylclobazam; sedation warrants particular attention when "
            "clobazam is also used. CBD and cenobamate both have hepatic warnings."
        ),
        "recommendation": (
            "Monitor sedation and clinically relevant interactions; individualize "
            "changes rather than automatically intensifying reductions of third "
            "drugs. Follow the applicable CBD product label for liver tests and "
            "stopping criteria: prescription cannabidiol and valproate together "
            "increase the incidence of transaminase elevations. This is not proof "
            "that adding cenobamate further increases that risk. Follow the "
            "cenobamate label separately. US EPIDIOLEX label: "
            "https://www.accessdata.fda.gov/drugsatfda_docs/label/2026/210365s024s029s030lbl.pdf"
        ),
        "references": ["Smith2022", "FDA2019", "EMA2021"],
        "two_way": None,
    },
    "Hormonal Contraceptives": {
        "risk": "HIGH",
        "action": "Discuss additional or alternative non-hormonal contraception",
        "mechanism": (
            "Cenobamate induces CYP3A and may reduce the effectiveness of hormonal "
            "oral contraceptives. Effects on other methods depend on the method; "
            "do not assume the same interaction magnitude for every formulation."
        ),
        "recommendation": (
            "The US and EU labels advise additional or alternative non-hormonal "
            "contraception with oral contraceptives. Counsel before starting and "
            "review individual contraceptive methods and applicable local guidance "
            "with an appropriate clinician. The EU patient leaflet refers to "
            "alternative methods while taking cenobamate and up to 4 weeks after "
            "stopping. Do not assume that increasing estrogen dose is adequate."
        ),
        "references": ["FDA2019", "EMA2021"],
        "two_way": None,
    },
    "Primidone": {
        "risk": "HIGH",
        "action": "Review sedation and phenobarbital metabolite exposure",
        "mechanism": (
            "Primidone is metabolized partly to active phenobarbital. Cenobamate "
            "can increase phenobarbital exposure; the quantitative effect when "
            "phenobarbital is formed from primidone is not established here."
        ),
        "recommendation": (
            "Monitor sedation and ataxia and consider phenobarbital and primidone "
            "concentrations when clinically useful. Individualize any change and "
            "avoid abrupt withdrawal; a fixed primidone reduction cannot be "
            "derived from phenobarbital data. Review potential inducer washout "
            "interactions if primidone is tapered."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "references": ["FDA2019", "EMA2021", "Smith2022"],
        "two_way": None,
    },
    "Eslicarbazepine acetate (ESL)": {
        "risk": "MODERATE",
        "action": "Monitor sodium, seizure control and neurological tolerability",
        "mechanism": (
            "Eslicarbazepine acetate is converted to the active metabolite "
            "eslicarbazepine. Eslicarbazepine can cause hyponatremia and can "
            "contribute to neurological adverse effects with other sodium channel "
            "blockers. A clinically meaningful cenobamate-induced fall in "
            "eslicarbazepine through UGT induction is not established."
        ),
        "recommendation": (
            "No automatic dose increase is supported. Monitor seizure control, "
            "adverse effects and sodium as clinically indicated. Consider "
            "individualized reduction for tolerability or multiple concomitant "
            "sodium channel blockers. Review potential co-medication interactions "
            "when changing or stopping eslicarbazepine."
        ),
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "references": ["Smith2022", "Steinhoff2024"],
        "two_way": None,
    },
    "Felbamate": {
        "risk": "HIGH",
        "action": "Specialist review: felbamate-associated aplastic anemia and liver failure",
        "mechanism": (
            "Felbamate itself has US boxed warnings for aplastic anemia and "
            "hepatic failure. Cenobamate also has a liver-injury warning, but "
            "a quantified increase in risk from this particular combination "
            "is not established. Multiple enzyme interactions are possible; "
            "a fixed additive interaction should not be assumed."
        ),
        "recommendation": (
            "Follow the current felbamate and cenobamate labels, including "
            "felbamate-specific blood count and liver monitoring and stopping "
            "rules; seek specialist review for suspected injury. The FDA's 2012 "
            "Felbatol label specifies discontinuation at AST or ALT at least "
            "2× ULN or clinical signs suggesting liver failure; confirm current "
            "local labeling. Do not replace felbamate-specific rules with a "
            "generic cenobamate threshold. No automatic intensified reduction "
            "of other CYP2C19 substrates is justified solely by this combination. "
            "Felbatol label: https://www.accessdata.fda.gov/drugsatfda_docs/label/2012/020189s027lbl.pdf"
        ),
        "references": ["FDA2019", "EMA2021", "Smith2022"],
        "two_way": None,
    },
    "Zonisamide": {
        "risk": "LOW-MODERATE",
        "action": "Monitor seizure control and neurological adverse effects",
        "mechanism": (
            "Zonisamide has mixed mechanisms including sodium-channel effects; "
            "CNS adverse effects may be additive. It undergoes several "
            "elimination pathways, including CYP3A-mediated metabolism; the "
            "clinical magnitude of any cenobamate interaction is uncertain."
        ),
        "recommendation": (
            "Assess efficacy and adverse effects, including somnolence and "
            "cognitive symptoms. The Delphi recommendation concerns consideration "
            "of proactive reduction or withdrawal when the existing regimen "
            "contains at least two sodium channel blockers; it does not require "
            "automatic zonisamide discontinuation."
        ),
        "references": ["Smith2022", "Steinhoff2024"],
        "two_way": None,
    },
    "Rufinamide": {
        "risk": "MODERATE",
        "action": "Review QT-shortening risk and neurological tolerability",
        "mechanism": (
            "Rufinamide is primarily metabolized by hydrolysis; a clinically "
            "important cenobamate-induced decrease through CYP3A4 is not "
            "established. Both rufinamide and cenobamate can shorten QT, so "
            "the combination warrants caution."
        ),
        "recommendation": (
            "Review cardiac history, other QT-shortening drugs and the applicable "
            "product labels; consider ECG or specialist assessment if clinically "
            "indicated. Familial short-QT syndrome is a contraindication to "
            "cenobamate. Individualize any sodium channel blocker adjustment; "
            "no automatic rufinamide increase or discontinuation is warranted."
        ),
        "references": ["FDA2019", "EMA2021", "Steinhoff2024"],
        "two_way": None,
    },
    "Everolimus": {
        "risk": "HIGH",
        "action": "Coordinate with specialist and plan everolimus trough monitoring",
        "mechanism": (
            "Everolimus is a CYP3A and P-glycoprotein substrate. Cenobamate "
            "induces CYP3A and may reduce exposure; the individual effect and "
            "resulting dose change are not established here. Low exposure may "
            "have serious consequences depending on indication, including transplant."
        ),
        "recommendation": (
            "Coordinate with the everolimus prescribing team before adding or "
            "stopping cenobamate; plan indication-specific whole-blood trough "
            "monitoring and individualized dose management. Do not apply a fixed "
            "percentage increase. The prototype's original serum input labels "
            "all values as mcg/mL, whereas everolimus troughs are typically "
            "reported in ng/mL; entry is disabled until units and reference "
            "ranges are safely redesigned. This does not replace clinical TDM."
        ),
        "has_serum": False,
        "serum_toxic_high": None,
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "references": ["FDA2019", "Smith2022"],
        "two_way": None,
    },
}


def apply_clinical_content(drug_db):
    """Update existing DRUG_DB entries in place and return the same mapping.

    Unknown and missing drug names are left untouched. Existing schema is
    preserved: only fields already present in an entry are updated. An empty
    or partial mapping is therefore safe to use in tests or other prototypes.

    Zero percentages mean that this overlay does not prescribe an automated
    change; they are not a recommendation to maintain a dose. Clobazam retains
    an unvalidated author-defined >20 mg/day rule and still needs explicit
    clinician review; it is not an FDA or consensus rule. The
    application must not represent these outputs as a validated or automatically
    actionable plan. Hormonal contraception retains its six None values.
    """
    for name, changes in _UPDATES.items():
        entry = drug_db.get(name)
        if not isinstance(entry, dict):
            continue
        for field, value in changes.items():
            if field in entry:
                entry[field] = deepcopy(value)
    return drug_db

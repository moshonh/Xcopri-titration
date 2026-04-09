"""
Xcopri (Cenobamate) Clinical Transition & Interaction Tool
===========================================================
Streamlit application for neurologists.
Run with: streamlit run xcopri_app.py

Requirements:
    pip install streamlit pandas fpdf2
"""

import streamlit as st
import pandas as pd
import io
from fpdf import FPDF

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Xcopri Clinical Transition Tool",
    page_icon="💊",
    layout="wide",
)

# ── constants ─────────────────────────────────────────────────────────────────
XCOPRI_SCHEDULE = [
    {"weeks": "1–2",  "dose": 12.5},
    {"weeks": "3–4",  "dose": 25},
    {"weeks": "5–6",  "dose": 50},
    {"weeks": "7–8",  "dose": 100},
    {"weeks": "9–10", "dose": 150},
    {"weeks": "11–12","dose": 200},
]

DRUGS = [
    {"id": "clobazam",      "name": "Clobazam",           "default_dose": 20,   "upper_limit": None},
    {"id": "phenytoin",     "name": "Phenytoin",           "default_dose": 300,  "upper_limit": 20},
    {"id": "phenobarb",     "name": "Phenobarbital",       "default_dose": 90,   "upper_limit": 40},
    {"id": "lamotrigine",   "name": "Lamotrigine",         "default_dose": 200,  "upper_limit": 15},
    {"id": "valproate",     "name": "Valproate (VPA)",     "default_dose": 1000, "upper_limit": 100},
    {"id": "carbamazepine", "name": "Carbamazepine",       "default_dose": 600,  "upper_limit": 12},
    {"id": "lacosamide",    "name": "Lacosamide",          "default_dose": 200,  "upper_limit": None},
    {"id": "levetiracetam", "name": "Levetiracetam",       "default_dose": 1500, "upper_limit": None},
    {"id": "oxcarbazepine", "name": "Oxcarbazepine",       "default_dose": 900,  "upper_limit": 35},
    {"id": "contraceptive", "name": "Oral contraceptive",  "default_dose": None, "upper_limit": None},
]

INTERACTIONS = {
    "clobazam": {
        "severity": "HIGH",
        "mechanism": "CYP2C19 inhibition by cenobamate significantly increases N-desmethylclobazam (active metabolite) levels.",
        "action": "Mandatory dose reduction of 25–50% starting at week 8–10.",
        "direction": "reduce",
        "factor": 0.50,
        "rationale": (
            "Based on cenobamate's potent inhibition of CYP2C19, which is the primary metabolic "
            "pathway for clobazam to its active metabolite N-desmethylclobazam."
        ),
    },
    "phenytoin": {
        "severity": "HIGH",
        "mechanism": "CYP2C19 inhibition raises phenytoin plasma levels — narrow therapeutic index.",
        "action": "Reduce dose at weeks 6–8. Serum monitoring every 2 weeks. Aggressive reduction if level ≥ 85% of upper limit.",
        "direction": "reduce",
        "factor": 0.70,
        "rationale": (
            "Based on cenobamate's inhibition of CYP2C19, the primary enzyme for phenytoin "
            "metabolism. Phenytoin has a narrow therapeutic index; toxicity risk is high."
        ),
    },
    "phenobarb": {
        "severity": "HIGH",
        "mechanism": "CYP2C19 inhibition increases phenobarbital levels.",
        "action": "Reduce dose at weeks 6–8 and monitor serum levels fortnightly.",
        "direction": "reduce",
        "factor": 0.75,
        "rationale": (
            "Based on cenobamate's inhibition of CYP2C19, which contributes to phenobarbital "
            "hydroxylation. Monitor for sedation and ataxia."
        ),
    },
    "lamotrigine": {
        "severity": "MODERATE",
        "mechanism": "CYP3A4 induction by cenobamate may reduce lamotrigine levels by up to 50%.",
        "action": "Monitor lamotrigine levels; consider dose increase of 25–50% by weeks 10–12 if seizure control worsens.",
        "direction": "increase",
        "factor": 1.50,
        "rationale": (
            "Based on cenobamate's induction of CYP3A4, which increases lamotrigine clearance "
            "and may reduce its clinical efficacy."
        ),
    },
    "carbamazepine": {
        "severity": "MODERATE",
        "mechanism": "CYP3A4 induction reduces carbamazepine (parent drug) plasma levels.",
        "action": "Monitor serum carbamazepine; titrate upward if levels drop below therapeutic range.",
        "direction": "increase",
        "factor": 1.40,
        "rationale": (
            "Based on cenobamate's CYP3A4 induction, reducing carbamazepine plasma concentrations."
        ),
    },
    "oxcarbazepine": {
        "severity": "LOW",
        "mechanism": "Mild CYP3A4 induction may reduce MHD (active metabolite) levels.",
        "action": "Monitor clinically; serum check at week 8.",
        "direction": "none",
        "factor": 1.0,
        "rationale": "Mild CYP3A4 interaction; routine monitoring is usually sufficient.",
    },
    "contraceptive": {
        "severity": "HIGH",
        "mechanism": "CYP3A4 induction reduces oral contraceptive efficacy.",
        "action": "Switch to non-hormonal contraception or add a barrier method. Discuss at initiation.",
        "direction": "none",
        "factor": 1.0,
        "rationale": (
            "Based on cenobamate's CYP3A4 induction, which accelerates metabolism of both "
            "oestrogen and progestogen components."
        ),
    },
    "valproate": {
        "severity": "LOW",
        "mechanism": "Minor pharmacokinetic interaction; primarily clinical monitoring.",
        "action": "Routine monitoring; adjust if clinical worsening or signs of toxicity.",
        "direction": "none",
        "factor": 1.0,
        "rationale": "Modest interaction. Standard monitoring is sufficient.",
    },
    "lacosamide": {
        "severity": "LOW",
        "mechanism": "Cenobamate may mildly increase lacosamide levels via CYP2C19 inhibition.",
        "action": "Monitor for dizziness and diplopia. Reduce by 10–15% if adverse effects appear.",
        "direction": "none",
        "factor": 1.0,
        "rationale": "Minor CYP2C19 interaction; clinical monitoring is appropriate.",
    },
    "levetiracetam": {
        "severity": "NONE",
        "mechanism": "No significant pharmacokinetic interaction expected.",
        "action": "No dose adjustment required.",
        "direction": "none",
        "factor": 1.0,
        "rationale": "Levetiracetam is renally cleared and is not a CYP substrate.",
    },
}

SEVERITY_COLOR = {
    "HIGH": "red",
    "MODERATE": "orange",
    "LOW": "blue",
    "NONE": "green",
}

SEVERITY_EMOJI = {
    "HIGH": "🔴",
    "MODERATE": "🟠",
    "LOW": "🔵",
    "NONE": "🟢",
}

# ── session state ─────────────────────────────────────────────────────────────
if "step" not in st.session_state:
    st.session_state.step = 1
if "active_drugs" not in st.session_state:
    st.session_state.active_drugs = {}
if "patient" not in st.session_state:
    st.session_state.patient = {}
if "comorbidities" not in st.session_state:
    st.session_state.comorbidities = []

# ── helpers ───────────────────────────────────────────────────────────────────
def severity_badge(s: str) -> str:
    return f"{SEVERITY_EMOJI.get(s, '')} **{s}**"


def near_upper_limit(drug_id: str, serum_val) -> bool:
    d = next((x for x in DRUGS if x["id"] == drug_id), None)
    if not d or not d["upper_limit"] or serum_val is None:
        return False
    return serum_val >= d["upper_limit"] * 0.85


def adjusted_dose(drug_id: str, base_dose: float, week_idx: int) -> float:
    ix = INTERACTIONS.get(drug_id, {})
    direction = ix.get("direction", "none")
    factor = ix.get("factor", 1.0)
    if direction == "reduce" and week_idx >= 3:
        return round(base_dose * factor, 1)
    elif direction == "increase" and week_idx >= 4:
        return round(base_dose * factor, 1)
    return base_dose


def build_titration_df() -> pd.DataFrame:
    active = st.session_state.active_drugs
    rows = []
    for i, sched in enumerate(XCOPRI_SCHEDULE):
        row = {"Weeks": f"Wk {sched['weeks']}", "Xcopri (mg/day)": sched["dose"]}
        for drug_id, info in active.items():
            if drug_id == "contraceptive":
                continue
            base = info["dose"]
            row[info["name"]] = adjusted_dose(drug_id, base, i)
        rows.append(row)
    return pd.DataFrame(rows)


# ── PDF generation ─────────────────────────────────────────────────────────────
def generate_pdf(df: pd.DataFrame, patient: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Xcopri (Cenobamate) — 12-Week Titration Plan", ln=True)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(0, 6, f"Patient: Age {patient.get('age')}, {patient.get('gender')}, {patient.get('weight')} kg", ln=True)
    pdf.cell(0, 6, f"Epilepsy type: {patient.get('epilepsy_type')}", ln=True)
    if patient.get("comorbidities"):
        pdf.cell(0, 6, f"Comorbidities: {', '.join(patient['comorbidities'])}", ln=True)
    pdf.ln(4)

    # Table header
    pdf.set_fill_color(200, 200, 220)
    pdf.set_font("Helvetica", "B", 9)
    cols = list(df.columns)
    col_w = [20] + [35] * (len(cols) - 1)
    col_w = [min(w, 190 // len(cols)) for w in col_w]
    for j, col in enumerate(cols):
        pdf.cell(col_w[j], 7, col[:20], border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", size=9)
    for _, row in df.iterrows():
        for j, col in enumerate(cols):
            pdf.cell(col_w[j], 6, str(row[col]), border=1)
        pdf.ln()

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, "Safety Flags", ln=True)
    pdf.set_font("Helvetica", size=9)
    flags = [
        "DRESS syndrome: Follow approved slow titration schedule. Monitor CBC and LFTs at baseline, weeks 4 and 12.",
        "QT shortening: Obtain baseline and follow-up ECG. Avoid co-administration with other QT-shortening drugs.",
    ]
    if "Renal impairment" in patient.get("comorbidities", []):
        flags.append("Renal impairment: Cap dose at 100–150 mg/day. Monitor for CNS adverse effects.")
    if "Hepatic impairment" in patient.get("comorbidities", []):
        flags.append("Hepatic impairment: Not recommended in severe impairment. Monitor LFTs every 4 weeks.")
    if "Pregnancy / breastfeeding" in patient.get("comorbidities", []):
        flags.append("Pregnancy: Hormonal contraception efficacy is reduced. Ensure folate supplementation.")
    for f in flags:
        pdf.multi_cell(0, 5, f"• {f}")

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4,
        "This plan is generated by a clinical decision-support tool and must be reviewed "
        "and approved by a licensed neurologist before implementation. Not a substitute for "
        "clinical judgment."
    )

    return bytes(pdf.output())


# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("Navigation")
step_labels = {1: "1 · Patient & Drugs", 2: "2 · Interaction Analysis", 3: "3 · Titration Plan"}
for s, label in step_labels.items():
    if st.session_state.step == s:
        st.sidebar.markdown(f"**→ {label}**")
    else:
        st.sidebar.markdown(f"&nbsp;&nbsp;&nbsp;{label}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Disclaimer**")
st.sidebar.caption(
    "For neurologist use only. All recommendations must be reviewed "
    "and confirmed by the treating physician before implementation."
)

# ── main title ────────────────────────────────────────────────────────────────
st.title("💊 Xcopri (Cenobamate) — Clinical Transition Tool")
st.caption("Assists neurologists in transitioning patients to cenobamate with pharmacokinetic interaction management.")

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Patient & Drug Input
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.subheader("Step 1: Patient Profile & Current ASMs")

    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("Age (years)", min_value=18, max_value=99, value=42)
    with col2:
        gender = st.selectbox("Gender", ["Female", "Male", "Other"])
    with col3:
        weight = st.number_input("Weight (kg)", min_value=30, max_value=200, value=70)

    epilepsy_type = st.selectbox(
        "Epilepsy type",
        [
            "Focal onset (unaware)",
            "Focal to bilateral tonic-clonic",
            "Generalized tonic-clonic",
            "Lennox-Gastaut syndrome",
            "Other",
        ],
    )

    comorbidities = st.multiselect(
        "Comorbidities (select all that apply)",
        ["Renal impairment (CKD 3–5)", "Hepatic impairment (Child-Pugh B/C)", "Pregnancy / breastfeeding"],
        help="These will generate additional safety flags in the analysis step.",
    )

    st.markdown("---")
    st.subheader("Current Anti-Seizure Medications (ASMs)")

    active_drugs: dict = {}
    serum_values: dict = {}

    for drug in DRUGS:
        col_chk, col_dose, col_serum = st.columns([2, 2, 2])
        with col_chk:
            selected = st.checkbox(drug["name"], key=f"chk_{drug['id']}")
        if selected:
            with col_dose:
                if drug["default_dose"] is not None:
                    dose = st.number_input(
                        f"{drug['name']} — daily dose (mg)",
                        min_value=1,
                        max_value=5000,
                        value=drug["default_dose"],
                        key=f"dose_{drug['id']}",
                        label_visibility="collapsed",
                    )
                else:
                    dose = None
            with col_serum:
                if drug["upper_limit"] is not None:
                    serum = st.number_input(
                        f"Serum level (µg/mL) — upper limit {drug['upper_limit']}",
                        min_value=0.0,
                        max_value=200.0,
                        value=0.0,
                        step=0.1,
                        key=f"serum_{drug['id']}",
                        label_visibility="collapsed",
                        help=f"Therapeutic upper limit: {drug['upper_limit']} µg/mL",
                    )
                    serum_values[drug["id"]] = serum if serum > 0 else None
                else:
                    serum_values[drug["id"]] = None
            active_drugs[drug["id"]] = {
                "name": drug["name"],
                "dose": dose,
                "serum": serum_values.get(drug["id"]),
                "upper_limit": drug["upper_limit"],
            }

    st.markdown("---")
    if st.button("▶ Analyse interactions", type="primary"):
        if not active_drugs:
            st.error("Please select at least one current ASM.")
        else:
            st.session_state.active_drugs = active_drugs
            st.session_state.patient = {
                "age": age,
                "gender": gender,
                "weight": weight,
                "epilepsy_type": epilepsy_type,
                "comorbidities": comorbidities,
            }
            st.session_state.step = 2
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Interaction Analysis
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.subheader("Step 2: Interaction Warning Summary")
    patient = st.session_state.patient
    st.info(
        f"**Patient:** Age {patient['age']} · {patient['gender']} · {patient['weight']} kg · "
        f"{patient['epilepsy_type']}"
    )

    active = st.session_state.active_drugs
    any_interaction = False

    for drug_id, info in active.items():
        ix = INTERACTIONS.get(drug_id)
        if not ix:
            continue
        sev = ix["severity"]
        color = SEVERITY_COLOR[sev]
        near_limit = near_upper_limit(drug_id, info.get("serum"))

        with st.expander(
            f"{SEVERITY_EMOJI[sev]} **{info['name']}** — {sev} risk",
            expanded=(sev in ("HIGH", "MODERATE")),
        ):
            st.markdown(f"**Mechanism:** {ix['mechanism']}")
            st.markdown(f"**Recommended action:** {ix['action']}")
            if near_limit:
                st.warning(
                    f"⚠ Serum level is near the upper therapeutic limit "
                    f"({info['upper_limit']} µg/mL). **More aggressive dose reduction is recommended.**"
                )
            st.caption(f"_Pharmacological rationale: {ix['rationale']}_")
        any_interaction = True

    if not any_interaction:
        st.success("No clinically significant interactions found with the selected drugs.")

    # Safety flags
    st.markdown("---")
    st.subheader("🚨 Safety Flags")

    st.error(
        "**DRESS Syndrome risk:** Cenobamate titration must follow the approved slow "
        "schedule. Rapid titration increases risk of Drug Reaction with Eosinophilia "
        "and Systemic Symptoms (DRESS). Monitor CBC and LFTs at baseline, weeks 4 and 12."
    )
    st.error(
        "**QT Shortening:** Cenobamate shortens the QTc interval. Avoid co-administration "
        "with drugs that shorten QT. Obtain baseline and follow-up ECG, especially in "
        "patients with cardiac history."
    )

    for c in patient.get("comorbidities", []):
        if "Renal" in c:
            st.warning(
                "**Renal Impairment (CKD 3–5):** Cenobamate not studied in severe renal "
                "impairment. Consider dose cap at 100–150 mg/day. Monitor for CNS adverse effects."
            )
        if "Hepatic" in c:
            st.warning(
                "**Hepatic Impairment (Child-Pugh B/C):** Maximum recommended dose is "
                "200 mg/day in mild impairment; not recommended in severe impairment. "
                "Monitor LFTs every 4 weeks during titration."
            )
        if "Pregnancy" in c:
            st.warning(
                "**Pregnancy / Breastfeeding:** Hormonal contraceptive efficacy is reduced "
                "by cenobamate (CYP3A4 induction). Teratogenicity data limited. Consult "
                "teratology service. Ensure adequate folate supplementation."
            )

    st.markdown("---")
    col_back, col_approve = st.columns(2)
    with col_back:
        if st.button("← Back to patient data"):
            st.session_state.step = 1
            st.rerun()
    with col_approve:
        if st.button("✅ Clinician approves — generate titration plan", type="primary"):
            st.session_state.step = 3
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Titration Plan
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    st.subheader("Step 3: 12-Week Titration Plan")
    patient = st.session_state.patient
    st.info(
        f"**Patient:** Age {patient['age']} · {patient['gender']} · {patient['weight']} kg · "
        f"{patient['epilepsy_type']}"
    )

    df = build_titration_df()
    st.dataframe(
        df.style.apply(
            lambda col: [
                "background-color: #EEEDFE; color: #3C3489; font-weight: 500"
                if col.name == "Xcopri (mg/day)"
                else ""
                for _ in col
            ],
            axis=0,
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Note: Dose adjustments shown are estimates based on standard pharmacokinetic "
        "interaction profiles. Final doses must be individualised based on clinical response "
        "and serum level monitoring."
    )

    # Rationale table
    with st.expander("📖 Pharmacological rationale for adjustments"):
        for drug_id, info in st.session_state.active_drugs.items():
            ix = INTERACTIONS.get(drug_id)
            if ix and ix["severity"] != "NONE":
                st.markdown(f"**{info['name']}:** {ix['rationale']}")

    st.markdown("---")
    st.subheader("Export")

    col_csv, col_pdf = st.columns(2)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    col_csv.download_button(
        label="⬇ Download CSV",
        data=csv_buffer.getvalue().encode("utf-8"),
        file_name="xcopri_titration_plan.csv",
        mime="text/csv",
    )

    try:
        pdf_bytes = generate_pdf(df, patient)
        col_pdf.download_button(
            label="⬇ Download PDF",
            data=pdf_bytes,
            file_name="xcopri_titration_plan.pdf",
            mime="application/pdf",
        )
    except Exception as e:
        col_pdf.warning(f"PDF generation requires fpdf2: `pip install fpdf2`. Error: {e}")

    st.markdown("---")
    if st.button("← Back to analysis"):
        st.session_state.step = 2
        st.rerun()

    st.markdown("---")
    st.caption(
        "⚠ This tool is intended to assist clinical decision-making only. "
        "All recommendations must be reviewed and confirmed by the treating neurologist "
        "before implementation. Not a substitute for clinical judgment."
    )

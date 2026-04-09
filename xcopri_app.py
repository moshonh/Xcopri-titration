"""
Xcopri (Cenobamate) Clinical Transition & Interaction Tool
===========================================================
Streamlit application for neurologists.
Run:  streamlit run xcopri_app.py
Requires: streamlit, pandas, reportlab
Install:  pip install streamlit pandas reportlab
"""

import streamlit as st
import pandas as pd
import io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ─────────────────────────── CONFIGURATION ──────────────────────────────────

st.set_page_config(
    page_title="Xcopri Transition Tool",
    page_icon="🧠",
    layout="wide",
)

# Xcopri titration schedule (weeks 1-2, 3-4, 5-6, 7-8, 9-10, 11-12)
XCOP_SCHEDULE = [12.5, 12.5, 25, 50, 100, 150]
WEEK_LABELS = [
    "שבועות 1–2", "שבועות 3–4", "שבועות 5–6",
    "שבועות 7–8", "שבועות 9–10", "שבועות 11–12",
]

# Drug interaction database
# pct_change: per period (matching 6 titration periods), positive = increase dose
DRUG_DB = {
    "Clobazam": {
        "unit": "mg",
        "has_serum": False,
        "warning_level": "🔴 HIGH RISK",
        "action": "הפחתת מינון 25–50%",
        "mechanism": "Cenobamate מעכב CYP2C19 → עלייה משמעותית ב-N-desmethylclobazam הפעיל. "
                     "סיכון לנמנום, אטקסיה ועצירת נשימה.",
        "recommendation": "הפחת מינון ב-25% בשבועות 5–6 ובנוסף 25% בשבועות 9–10.",
        "pct_per_period": [0, 0, -25, -25, -50, -50],
        "serum_toxic_high": None,
    },
    "Phenytoin": {
        "unit": "mg",
        "has_serum": True,
        "serum_normal_range": (10, 20),
        "warning_level": "🔴 HIGH RISK",
        "action": "הפחתת מינון 25–40% + ניטור רמות",
        "mechanism": "עיכוב CYP2C19 → עלייה ברמות פניטואין. סיכון לניסטגמוס, אטקסיה, בלבול.",
        "recommendation": "הפחת מינון ב-20% בשבועות 5–6 ועוד 20% בשבועות 9–10. בדיקת רמות כל 4 שבועות.",
        "pct_per_period": [0, 0, -20, -20, -40, -40],
        "serum_toxic_high": 20,
    },
    "Phenobarbital": {
        "unit": "mg",
        "has_serum": True,
        "serum_normal_range": (15, 40),
        "warning_level": "🔴 HIGH RISK",
        "action": "הפחתת מינון 20–30% + ניטור רמות",
        "mechanism": "עיכוב CYP2C19 → עלייה ברמות פנוברביטל. סיכון לדיכאון נשימתי.",
        "recommendation": "הפחת מינון ב-15% בשבועות 5–6 ועוד 15% בשבועות 9–10. ניטור רמות.",
        "pct_per_period": [0, 0, -15, -15, -30, -30],
        "serum_toxic_high": 40,
    },
    "Lamotrigine": {
        "unit": "mg",
        "has_serum": False,
        "warning_level": "🟡 MODERATE",
        "action": "עלייה אפשרית במינון 20–50%",
        "mechanism": "השראת CYP3A4 → ירידה ברמות למוטריגין עד 50%. עלול לגרום להחמרת התקפים.",
        "recommendation": "נטר להחמרת התקפים. שקול העלאת מינון ב-15% בשבועות 5–6 ועוד 15% בשבועות 9–10.",
        "pct_per_period": [0, 0, 15, 15, 30, 30],
        "serum_toxic_high": None,
    },
    "Carbamazepine": {
        "unit": "mg",
        "has_serum": True,
        "serum_normal_range": (4, 12),
        "warning_level": "🟡 MODERATE",
        "action": "עלייה אפשרית במינון 15–30%",
        "mechanism": "השראת CYP3A4 → ירידה ברמות קרבמזפין. עלול לגרום להחמרת התקפים.",
        "recommendation": "נטר רמות. שקול העלאת מינון ב-10% בשבועות 5–6 ועוד 10% בשבועות 9–10.",
        "pct_per_period": [0, 0, 10, 10, 20, 20],
        "serum_toxic_high": 12,
    },
    "Valproate (VPA)": {
        "unit": "mg",
        "has_serum": True,
        "serum_normal_range": (50, 100),
        "warning_level": "🟢 LOW",
        "action": "ניטור בלבד",
        "mechanism": "אינטראקציה מינורית עם Cenobamate. השפעה קלינית מצומצמת.",
        "recommendation": "ניטור רמות סרום כל 4–6 שבועות. לרוב אינה דורשת התאמת מינון.",
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "serum_toxic_high": 100,
    },
    "Lacosamide": {
        "unit": "mg",
        "has_serum": False,
        "warning_level": "🟡 MODERATE",
        "action": "ניטור א.ק.ג",
        "mechanism": "שתי התרופות מאריכות/משנות פעילות תעלות נתרן. Cenobamate מקצרת QT — "
                     "Lacosamide מאריכה PR. ניטור א.ק.ג לאורך הטיטרציה.",
        "recommendation": "א.ק.ג לפני תחילת טיפול, לאחר 4 שבועות, ולאחר כל עלייה במינון Xcopri.",
        "pct_per_period": [0, 0, 0, 0, 0, 0],
        "serum_toxic_high": None,
    },
    "אמצעי מניעה הורמונליים": {
        "unit": "",
        "has_serum": False,
        "warning_level": "🔴 HIGH RISK",
        "action": "מעבר לאמצעי מניעה לא-הורמונלי",
        "mechanism": "השראת CYP3A4 → ירידה משמעותית בריכוז אסטרוגן/פרוגסטרון. "
                     "כשל אמצעי מניעה הורמונלי (גלולות, מדבקות, IUD הורמונלי).",
        "recommendation": "מעבר מיידי לאמצעי מניעה לא-הורמונלי (נחושת IUD, קונדום) לפני תחילת טיפול.",
        "pct_per_period": [None, None, None, None, None, None],
        "serum_toxic_high": None,
    },
}

SAFETY_FLAGS = [
    {
        "title": "⚠️ DRESS Syndrome — Drug Reaction with Eosinophilia and Systemic Symptoms",
        "body": (
            "דווחו מקרי DRESS עם Cenobamate, בעיקר בטיטרציה מהירה מדי. "
            "יש לעמוד בלוח הטיטרציה הסטנדרטי (עלייה כל שבועיים). "
            "בכל פריחה עורית, חום ≥38.5°C, לימפדנופתיה, או עלייה באאוזינופילים — "
            "הפסקת Cenobamate מיידית ומעקב דחוף."
        ),
        "color": "#FDECEA",
    },
    {
        "title": "⚡ QT Shortening",
        "body": (
            "Cenobamate גורמת לקיצור מרווח QT. "
            "יש לבצע א.ק.ג בסיסי לפני תחילת טיפול ולאחר כל עלייה במינון. "
            "הימנע משילוב עם תרופות המקצרות QT (קלאס Ia, III אנטי-אריתמיות). "
            "QTc <340 ms — שקול הפסקה."
        ),
        "color": "#FFF3E0",
    },
]

# ─────────────────────────── HELPER FUNCTIONS ───────────────────────────────

def compute_adjusted_dose(base_dose: float, pct: float | None) -> str:
    """Return adjusted dose string given base and percent change."""
    if pct is None:
        return "⚠ מעבר לאמצעי לא-הורמונלי"
    if pct == 0:
        return f"{base_dose:.0f} mg" if base_dose else "ללא שינוי"
    adjusted = round(base_dose * (1 + pct / 100))
    sign = "↑" if pct > 0 else "↓"
    return f"{adjusted} mg ({sign}{abs(pct):.0f}%)"


def serum_flag(drug_name: str, serum_val: float | None) -> str | None:
    """Return a warning string if serum level is near/above toxic threshold."""
    if serum_val is None:
        return None
    d = DRUG_DB.get(drug_name, {})
    hi = d.get("serum_toxic_high")
    if hi and serum_val > hi * 0.85:
        return (
            f"⚠️ רמת סרום {serum_val} µg/mL — קרובה לגבול עליון ({hi} µg/mL). "
            "מומלץ להאיץ הפחתת מינון."
        )
    return None


def build_titration_df(selected_drugs: dict) -> pd.DataFrame:
    """Build the 12-week titration DataFrame."""
    rows = []
    for i, (week, xcop) in enumerate(zip(WEEK_LABELS, XCOP_SCHEDULE)):
        row = {"שבוע": week, "Xcopri (Cenobamate) mg": xcop}
        for drug_name, info in selected_drugs.items():
            base = info.get("dose", 0)
            pct = DRUG_DB[drug_name]["pct_per_period"][i]
            row[drug_name] = compute_adjusted_dose(base, pct)
        rows.append(row)
    return pd.DataFrame(rows)


def generate_pdf(patient: dict, selected_drugs: dict, df: pd.DataFrame) -> bytes:
    """Generate a PDF report using ReportLab and return as bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle("title", fontSize=14, fontName="Helvetica-Bold",
                                 spaceAfter=4, alignment=TA_LEFT)
    style_h2    = ParagraphStyle("h2", fontSize=10, fontName="Helvetica-Bold",
                                 spaceBefore=10, spaceAfter=4)
    style_body  = ParagraphStyle("body", fontSize=8, fontName="Helvetica",
                                 spaceAfter=3, leading=12)
    style_small = ParagraphStyle("small", fontSize=7, fontName="Helvetica-Oblique",
                                 textColor=colors.HexColor("#888888"), spaceAfter=2)
    style_flag  = ParagraphStyle("flag", fontSize=8, fontName="Helvetica",
                                 spaceAfter=3, leading=12,
                                 backColor=colors.HexColor("#FFF3E0"),
                                 borderPadding=(4, 6, 4, 6))

    story = []

    # Title
    story.append(Paragraph("Xcopri (Cenobamate) — Clinical Titration Plan", style_title))
    story.append(Paragraph(f"Generated: {date.today().strftime('%Y-%m-%d')}", style_small))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
    story.append(Spacer(1, 6))

    # Patient profile
    story.append(Paragraph("Patient Profile", style_h2))
    for k, v in patient.items():
        if v and str(v) not in ("—", "None"):
            story.append(Paragraph(f"<b>{k}:</b> {v}", style_body))
    story.append(Spacer(1, 6))

    # Safety flags
    story.append(Paragraph("Safety Flags", style_h2))
    for flag in SAFETY_FLAGS:
        title_text = flag["title"].replace("⚠️", "").replace("⚡", "").strip()
        body_text  = flag["body"]
        story.append(Paragraph(f"<b>{title_text}</b>: {body_text}", style_flag))
    story.append(Spacer(1, 6))

    # Interaction summary
    story.append(Paragraph("Drug Interaction Summary", style_h2))
    for drug_name in selected_drugs:
        d = DRUG_DB[drug_name]
        lvl = d["warning_level"].replace("🔴", "[HIGH]").replace("🟡", "[MOD]").replace("🟢", "[LOW]")
        story.append(Paragraph(f"<b>{lvl} {drug_name}</b>: {d['recommendation']}", style_body))
    story.append(Spacer(1, 6))

    # Titration table
    story.append(Paragraph("12-Week Titration Schedule", style_h2))
    col_names = list(df.columns)
    table_data = [col_names] + [list(row) for _, row in df.iterrows()]
    col_count = len(col_names)
    page_w = A4[0] - 40*mm
    col_w = page_w / col_count

    tbl = Table(table_data, colWidths=[col_w] * col_count, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#E8EAF6")),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 7),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS",(0, 1),(-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10))

    # Disclaimer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
    story.append(Paragraph(
        "DISCLAIMER: This tool is intended for clinical decision support only. "
        "Final dosing decisions rest with the treating physician. "
        "Based on: Cenobamate prescribing information (SK Life Science) and published DDI literature.",
        style_small,
    ))

    doc.build(story)
    return buf.getvalue()


# ─────────────────────────── UI ─────────────────────────────────────────────

st.title("🧠 Xcopri (Cenobamate) — Clinical Transition Tool")
st.caption("תכנון מעבר ותאימות תרופתית לנוירולוגים · מבוסס-ספרות קלינית פרמקולוגית")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "1️⃣ פרופיל מטופל",
    "2️⃣ תרופות נוכחיות",
    "3️⃣ ניתוח אינטראקציות",
    "4️⃣ טבלת טיטרציה",
])

# ── TAB 1: Patient Profile ────────────────────────────────────────────────────
with tab1:
    st.subheader("פרופיל מטופל")
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("גיל", min_value=18, max_value=100, value=None,
                              placeholder="שנים", key="age")
        gender = st.selectbox("מגדר", ["—", "זכר", "נקבה"], key="gender")
    with col2:
        weight = st.number_input("משקל (ק\"ג)", min_value=30.0, max_value=200.0,
                                 value=None, placeholder="ק״ג", key="weight")
        epilepsy_type = st.selectbox(
            "סוג אפילפסיה",
            ["—", "Focal onset", "Generalized", "Unknown onset"],
            key="epilepsy",
        )
    with col3:
        egfr = st.number_input("eGFR (ml/min)", min_value=0, max_value=150,
                               value=None, placeholder="נורמלי >60", key="egfr")
        liver = st.selectbox(
            "תפקוד כבד",
            ["תקין (Child-Pugh A)", "קל (Child-Pugh B)", "חמור (Child-Pugh C)"],
            key="liver",
        )

    pregnancy = st.selectbox(
        "הריון / הנקה / פוטנציאל הריון",
        ["לא", "הריון", "הנקה", "פוטנציאל הריון"],
        key="pregnancy",
    )

    # Special patient warnings
    special_warns = []
    if st.session_state.get("pregnancy") == "הריון":
        special_warns.append("🚨 **הריון**: Cenobamate אינה מאושרת בהריון. סיכון טרטוגני לא ידוע במלואו. שקול חלופה.")
    if st.session_state.get("pregnancy") in ["הנקה", "פוטנציאל הריון"]:
        special_warns.append("⚠️ **פוטנציאל הריון / הנקה**: יש לעבור לאמצעי מניעה לא-הורמונלי ולדון בסיכונים.")
    if st.session_state.get("liver") == "חמור (Child-Pugh C)":
        special_warns.append("🚨 **אי-ספיקת כבד חמורה (Child-Pugh C)**: Cenobamate אינה מומלצת. קלירנס ירד משמעותית.")
    if st.session_state.get("liver") == "קל (Child-Pugh B)":
        special_warns.append("⚠️ **אי-ספיקת כבד קלה (Child-Pugh B)**: מינון מקסימלי מומלץ 200 mg. ניטור תפקודי כבד.")
    egfr_val = st.session_state.get("egfr") or 0
    if egfr_val and egfr_val < 30:
        special_warns.append("🚨 **אי-ספיקת כליות חמורה (eGFR<30)**: מינון מקסימלי 200 mg. ניטור תכוף נדרש.")
    elif egfr_val and egfr_val < 60:
        special_warns.append("⚠️ **אי-ספיקת כליות מתונה (eGFR 30–60)**: שקול הגבלת מינון; טיטרציה איטית מומלצת.")

    if special_warns:
        st.divider()
        st.subheader("⚠️ אזהרות מיוחדות — מטופל זה")
        for w in special_warns:
            st.warning(w)

# ── TAB 2: Current Medications ───────────────────────────────────────────────
with tab2:
    st.subheader("תרופות נוכחיות")
    st.caption("בחר תרופות פעילות והזן מינון יומי. הזנת רמת סרום תשפר את דיוק ההמלצות.")
    selected_drugs = {}

    for drug_name, ddata in DRUG_DB.items():
        with st.expander(f"{ddata['warning_level']}  **{drug_name}**  —  {ddata['action']}"):
            is_active = st.checkbox(f"מטופל מקבל {drug_name}", key=f"chk_{drug_name}")
            if is_active:
                c1, c2 = st.columns(2)
                with c1:
                    dose_val = st.number_input(
                        f"מינון יומי כולל ({ddata['unit'] or 'יח׳'})",
                        min_value=0.0, value=None,
                        placeholder="הזן מינון",
                        key=f"dose_{drug_name}",
                    )
                with c2:
                    if ddata["has_serum"]:
                        rng = ddata.get("serum_normal_range", (None, None))
                        serum_val = st.number_input(
                            f"רמת סרום נוכחית (µg/mL) [טווח תקין: {rng[0]}–{rng[1]}]",
                            min_value=0.0, value=None,
                            placeholder="אופציונלי",
                            key=f"serum_{drug_name}",
                        )
                    else:
                        serum_val = None
                st.info(f"💊 {ddata['mechanism']}")
                selected_drugs[drug_name] = {
                    "dose": dose_val or 0,
                    "serum": serum_val,
                }

    st.session_state["selected_drugs"] = selected_drugs

# ── TAB 3: Interaction Analysis ──────────────────────────────────────────────
with tab3:
    st.subheader("Safety Flags — חובה לקרוא לפני המשך")
    for flag in SAFETY_FLAGS:
        st.markdown(
            f"""<div style='background:{flag["color"]};padding:12px 16px;
            border-radius:8px;margin-bottom:10px;border-left:4px solid #E24B4A'>
            <strong>{flag["title"]}</strong><br>{flag["body"]}</div>""",
            unsafe_allow_html=True,
        )

    sd = st.session_state.get("selected_drugs", {})
    if not sd:
        st.info("אנא בחר תרופות בלשונית 2 כדי לראות ניתוח אינטראקציות.")
    else:
        st.divider()
        st.subheader("סיכום אינטראקציות תרופתיות")
        for drug_name, info in sd.items():
            d = DRUG_DB[drug_name]
            # Serum warning
            sf = serum_flag(drug_name, info.get("serum"))
            lvl = d["warning_level"]
            color = "#FDECEA" if "HIGH" in lvl else "#FFF8E1" if "MODERATE" in lvl else "#E8F5E9"
            border = "#E24B4A" if "HIGH" in lvl else "#EF9F27" if "MODERATE" in lvl else "#388E3C"
            html = (
                f"<div style='background:{color};border-left:4px solid {border};"
                f"padding:10px 14px;border-radius:6px;margin-bottom:8px'>"
                f"<strong>{lvl} — {drug_name}</strong><br>"
                f"<span style='font-size:13px'>{d['mechanism']}</span><br>"
                f"<span style='font-size:12px;opacity:.85'>📋 {d['recommendation']}</span>"
            )
            if sf:
                html += f"<br><span style='color:#B71C1C;font-size:12px'>{sf}</span>"
            if info.get("dose"):
                html += f"<br><span style='font-size:12px'>מינון נוכחי: {info['dose']} {d['unit']}</span>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

# ── TAB 4: Titration Table ────────────────────────────────────────────────────
with tab4:
    sd = st.session_state.get("selected_drugs", {})

    if not sd:
        st.info("אנא בחר תרופות בלשונית 2 כדי לייצר טבלת טיטרציה.")
    else:
        st.subheader("טבלת טיטרציה — 12 שבועות")
        df = build_titration_df(sd)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Pharmacokinetic notes
        st.divider()
        st.subheader("הערות פרמקולוגיות")
        for drug_name in sd:
            d = DRUG_DB[drug_name]
            st.markdown(
                f"**{drug_name}** — {d['mechanism']}  \n"
                f"*Based on Cenobamate's {'inhibition of CYP2C19' if 'CYP2C19' in d['mechanism'] else 'induction of CYP3A4/2B6'}*"
            )

        # Export buttons
        st.divider()
        st.subheader("ייצוא")
        col_a, col_b = st.columns(2)

        # CSV export
        with col_a:
            csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="⬇️ ייצוא CSV",
                data=csv_bytes,
                file_name=f"xcopri_titration_{date.today()}.csv",
                mime="text/csv",
            )

        # PDF export
        with col_b:
            patient_info = {
                "גיל": st.session_state.get("age"),
                "מגדר": st.session_state.get("gender"),
                "משקל": f"{st.session_state.get('weight')} ק\"ג" if st.session_state.get("weight") else None,
                "סוג אפילפסיה": st.session_state.get("epilepsy"),
                "eGFR": f"{st.session_state.get('egfr')} ml/min" if st.session_state.get("egfr") else None,
                "תפקוד כבד": st.session_state.get("liver"),
                "הריון/הנקה": st.session_state.get("pregnancy"),
            }
            try:
                pdf_bytes = generate_pdf(patient_info, sd, df)
                st.download_button(
                    label="⬇️ ייצוא PDF",
                    data=pdf_bytes,
                    file_name=f"xcopri_titration_{date.today()}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"שגיאה ביצירת PDF: {e}. ודא ש-reportlab מותקן.")

        st.caption(
            "⚠️ כלי זה מיועד לסיוע בהחלטה קלינית בלבד. "
            "ההחלטה הסופית נתונה לשיקול הרופא המטפל. "
            "מבוסס על: Cenobamate prescribing information (SK Life Science) ופרסומי DDI עדכניים."
        )

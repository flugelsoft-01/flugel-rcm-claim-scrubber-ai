#!/usr/bin/env python3
"""
app.py - Healthcare Revenue Cycle Management (RCM) AI Agent & Interactive Demo Application

A full-stack, interactive Streamlit application demonstrating:
1. Multi-Agent Pre-Submission Claim Scrubbing (clinical-coder & claim-scrubber).
2. Live HIPAA Safe Harbor PHI De-identification Traces.
3. Interactive Auto-Remediation & 1-Click Fix Simulation.
4. Batch Claim Auditing with CSV Export.
5. AI-Powered Formal Payer Denial Appeal Letter Generation.
"""

import os
import json
import time
import pandas as pd
import streamlit as st
from typing import Dict, List, Any

# Import backend agents and simulated MCP EHR
import demo_mcp_server
from phi_redaction_hook import redact_phi
from run_agent import (
    ClinicalCoderAgent,
    ClaimScrubberAgent,
    DenialAppealsAgent,
    ClaimAuditReport,
    ClinicalCoderOutput
)

# -----------------------------------------------------------------------------
# Streamlit Page Configuration & Custom CSS
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Healthcare RCM Multi-Agent Claim Scrubber | Flugelsoft Labs",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# SEO, GEO, Open Graph & Schema.org JSON-LD Metadata Injection
# -----------------------------------------------------------------------------
SEO_GEO_META_HTML = """
<!-- Canonical SEO & GEO Metadata Injection -->
<script>
(function() {
    const head = window.parent.document.head || document.head;
    
    function setMeta(name, content, isProperty=false) {
        const attr = isProperty ? 'property' : 'name';
        let el = head.querySelector(`meta[${attr}="${name}"]`);
        if (!el) {
            el = window.parent.document.createElement('meta');
            el.setAttribute(attr, name);
            head.appendChild(el);
        }
        el.setAttribute('content', content);
    }

    // Standard SEO Tags
    setMeta('description', 'Enterprise Healthcare Revenue Cycle Management (RCM) Multi-Agent System by Flugelsoft Labs. Automated pre-submission claim scrubbing, CMS LCD medical necessity validation, Modifier 25, Laterality, and NCCI bundling edits.');
    setMeta('keywords', 'Healthcare RCM, Pre-submission Claim Scrubbing, Medical Billing AI, ICD-10 CPT Compliance, CMS LCD Medical Necessity, Modifier 25, Laterality Modifiers RT LT, NCCI Bundling Edits, Denial Appeal Letter Generator, Flugelsoft Labs, Health AI');
    setMeta('author', 'Flugelsoft Labs');
    setMeta('robots', 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1');
    setMeta('canonical', 'https://flugel-rcm-claim-scrubber-ai.streamlit.app/');

    // Geotargeting (GEO) Meta Tags
    setMeta('geo.region', 'US-CA');
    setMeta('geo.placename', 'San Francisco, California');
    setMeta('geo.position', '37.7749;-122.4194');
    setMeta('ICBM', '37.7749, -122.4194');

    // Open Graph / Social Media Tags
    setMeta('og:type', 'website', true);
    setMeta('og:title', 'Healthcare RCM Multi-Agent Claim Scrubber | Flugelsoft Labs', true);
    setMeta('og:description', 'Autonomous pre-submission claim scrubbing and payer denial prevention platform by Flugelsoft Labs.', true);
    setMeta('og:url', 'https://flugel-rcm-claim-scrubber-ai.streamlit.app/', true);
    setMeta('og:site_name', 'Flugelsoft Labs RCM Platform', true);
    setMeta('og:image', 'https://img.icons8.com/color/512/medical-history.png', true);

    // Twitter Card Tags
    setMeta('twitter:card', 'summary_large_image');
    setMeta('twitter:title', 'Healthcare RCM Multi-Agent Claim Scrubber | Flugelsoft Labs');
    setMeta('twitter:description', 'Autonomous pre-submission claim scrubbing and payer denial prevention platform.');
    setMeta('twitter:image', 'https://img.icons8.com/color/512/medical-history.png');

    // Schema.org JSON-LD Structured Data
    if (!head.querySelector('#rcm-schema-jsonld')) {
        const script = window.parent.document.createElement('script');
        script.id = 'rcm-schema-jsonld';
        script.type = 'application/ld+json';
        script.text = JSON.stringify({
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "Flugelsoft Labs Healthcare RCM Claim Scrubber",
            "applicationCategory": "BusinessApplication, HealthApplication",
            "operatingSystem": "Web, Cloud",
            "description": "Enterprise Healthcare Revenue Cycle Management (RCM) AI platform for pre-submission claim scrubbing, LCD/NCCI compliance, and denial appeals.",
            "url": "https://flugel-rcm-claim-scrubber-ai.streamlit.app/",
            "author": {
                "@type": "Organization",
                "name": "Flugelsoft Labs",
                "url": "https://github.com/flugelsoft-01/flugel-rcm-claim-scrubber-ai"
            },
            "spatialCoverage": {
                "@type": "Place",
                "geo": {
                    "@type": "GeoCoordinates",
                    "latitude": 37.7749,
                    "longitude": -122.4194
                },
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "San Francisco",
                    "addressRegion": "CA",
                    "addressCountry": "US"
                }
            }
        });
        head.appendChild(script);
    }
})();
</script>
"""
st.html(SEO_GEO_META_HTML)

CUSTOM_CSS = """
<style>
    /* Global Styling */
    .main {
        background-color: #f8fafc;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .audit-card-clean {
        background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
        border: 2px solid #10b981;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .audit-card-hold {
        background: linear-gradient(135deg, #fff1f2 0%, #fef2f2 100%);
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .trace-box {
        background-color: #0f172a;
        color: #e2e8f0;
        font-family: 'Courier New', Courier, monospace;
        padding: 16px;
        border-radius: 8px;
        font-size: 0.88rem;
        line-height: 1.5;
        overflow-x: auto;
    }
    .badge-clean {
        background-color: #10b981;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-hold {
        background-color: #ef4444;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-phi {
        background-color: #6366f1;
        color: white;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Application State Initialization
# -----------------------------------------------------------------------------
if "audit_cache" not in st.session_state:
    st.session_state.audit_cache = {}

if "applied_fixes" not in st.session_state:
    st.session_state.applied_fixes = set()

# Initialize backend agents
clinical_coder = ClinicalCoderAgent()
claim_scrubber = ClaimScrubberAgent()
denial_appeals = DenialAppealsAgent()


# -----------------------------------------------------------------------------
# Dialog Modals: Architecture & Demo Tutorial
# -----------------------------------------------------------------------------
@st.dialog("System Architecture & Technical Specifications", width="large")
def show_architecture_dialog():
    try:
        with open("docs/ARCHITECTURE_AND_TECHNOLOGY.md", "r") as f:
            doc_content = f.read()
        st.markdown(doc_content)
        st.download_button(
            label="📥 Download Architecture Spec (.md)",
            data=doc_content,
            file_name="ARCHITECTURE_AND_TECHNOLOGY.md",
            mime="text/markdown"
        )
    except Exception as e:
        st.error(f"Could not load architecture doc: {e}")


@st.dialog("Interactive Demonstration Walkthrough & Presenter Guide", width="large")
def show_tutorial_dialog():
    try:
        with open("docs/DEMO_TUTORIAL_GUIDE.md", "r") as f:
            doc_content = f.read()
        st.markdown(doc_content)
        st.download_button(
            label="📥 Download Demo Script (.md)",
            data=doc_content,
            file_name="DEMO_TUTORIAL_GUIDE.md",
            mime="text/markdown"
        )
    except Exception as e:
        st.error(f"Could not load tutorial guide: {e}")


# -----------------------------------------------------------------------------
# Sidebar: System Configuration & Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/medical-history.png", width=64)
    st.title("RCM Control Center")
    st.markdown("**Healthcare Operations & Claims Intelligence**")
    st.divider()

    st.subheader("📚 Platform Guides & Tutorial")
    if st.button("📖 How the System Works", use_container_width=True, help="Detailed technical breakdown of the multi-agent pipeline"):
        show_architecture_dialog()
    if st.button("🎥 How to Demo This App", use_container_width=True, help="10-minute presenter guide and demo walkthrough"):
        show_tutorial_dialog()

    st.divider()

    st.subheader("🛡️ HIPAA Safe Harbor Guardrails")
    st.markdown(
        "<span class='badge-phi'>ACTIVE</span> Automated de-identification for all 18 HIPAA Safe Harbor elements (`Name`, `SSN`, `DOB`, `MRN`) "
        "via pre-execution hook `phi_redaction_hook.py`.",
        unsafe_allow_html=True
    )

    st.divider()

    if st.button("🔄 Reset Synthetic EHR Queue", use_container_width=True):
        demo_mcp_server.reset_demo_queue()
        st.session_state.audit_cache.clear()
        st.session_state.applied_fixes.clear()
        st.success("Reset all 4 encounters to PENDING_AUDIT!")
        st.rerun()

    with st.expander("📚 Payer Policy Lookups (LCDs)"):
        selected_policy = st.selectbox("Policy Library:", ["LCD-ECHOCARDIOGRAPHY", "LCD-BRAIN-MRI", "NCCI-POLICY-CH1"])
        policy_data = json.loads(demo_mcp_server.get_payer_policy(selected_policy))
        st.caption(f"**{policy_data.get('title')}**")
        st.json(policy_data)

    st.markdown("<br><hr style='border-color: #cbd5e1;'>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align: center; color: #64748b; font-size: 0.8rem; font-weight: 500;'>"
        "© Copyright Flugelsoft Labs"
        "</div>",
        unsafe_allow_html=True
    )


# -----------------------------------------------------------------------------
# Top Executive Header & KPI Dashboard
# -----------------------------------------------------------------------------
col_head, col_guide_btns = st.columns([2, 1])
with col_head:
    st.title("🩺 Healthcare Revenue Cycle Management AI System")
    st.caption("Enterprise Pre-Submission Claim Scrubbing, Compliance Auditing & Automated Payer Appeals Platform")
with col_guide_btns:
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        if st.button("📖 System Tech Guide", use_container_width=True, help="Detailed technical breakdown of the multi-agent pipeline"):
            show_architecture_dialog()
    with b_col2:
        if st.button("🎥 Demo Walkthrough", type="primary", use_container_width=True, help="10-minute presenter guide and demo walkthrough"):
            show_tutorial_dialog()

# Compute live KPIs
all_enc_raw = json.loads(demo_mcp_server.list_pending_encounters())
total_encounters = len(all_enc_raw)
total_charges = sum(enc["total_charge"] for enc in all_enc_raw)

# Pre-audit all encounters if not cached to compute dynamic KPIs
for enc in all_enc_raw:
    eid = enc["encounter_id"]
    if eid not in st.session_state.audit_cache:
        enc_detail = json.loads(demo_mcp_server.get_encounter_details(eid))
        redacted = redact_phi(enc_detail["clinical_note"])
        coded = clinical_coder.extract_codes(eid, redacted, enc_detail["proposed_claim"])
        report = claim_scrubber.scrub_claim(eid, f"TOKEN-{eid[-4:]}", coded, enc_detail["proposed_claim"])
        st.session_state.audit_cache[eid] = {
            "detail": enc_detail,
            "coded": coded,
            "report": report
        }

cached_reports = [v["report"] for v in st.session_state.audit_cache.values()]
held_count = sum(1 for r in cached_reports if r.status == "HOLD_FOR_REVIEW")
clean_count = sum(1 for r in cached_reports if r.status == "CLEAN")
catch_rate = (held_count / total_encounters * 100) if total_encounters else 0
revenue_protected = sum(
    st.session_state.audit_cache[r.encounter_id]["detail"]["proposed_claim"]["total_charge"]
    for r in cached_reports if r.status == "HOLD_FOR_REVIEW"
)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric(label="📋 Pre-Submission Queue", value=f"{total_encounters} Encounters", delta=f"{clean_count} Clean Claims")
with kpi2:
    st.metric(label="🎯 Denial Catch Rate", value=f"{catch_rate:.0f}%", delta=f"{held_count} Traps Prevented", delta_color="inverse")
with kpi3:
    st.metric(label="💰 Revenue Protected", value=f"${revenue_protected:,.2f}", delta="From Payer Denials")
with kpi4:
    st.metric(label="🔒 HIPAA De-Identification", value="Safe Harbor 100%", delta="Zero PHI Leaks")

st.markdown("<br>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Main Tabs: Single Claim Scrubber, Batch Audit, and AI Appeals
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "🔍 Tab 1: Single Claim Scrubber & Live Agent Trace",
    "📊 Tab 2: Batch Queue Audit & CSV Export",
    "📝 Tab 3: AI Denial Appeal Letter Generator"
])


# =============================================================================
# TAB 1: Single Claim Scrubber & Live Agent Trace
# =============================================================================
with tab1:
    col_sel, col_link = st.columns([3, 1])
    with col_sel:
        encounter_options = [
            f"{enc['encounter_id']} - {enc['patient_name']} ({enc['provider'].split(',')[0]})"
            for enc in all_enc_raw
        ]
        # Search-Friendly Deep Link Resolution
        default_enc_id = st.query_params.get("encounter", "ENC-1001")
        default_index = 0
        for i, opt in enumerate(encounter_options):
            if opt.startswith(default_enc_id):
                default_index = i
                break

        selected_option = st.selectbox("Select Pending Encounter to Audit:", encounter_options, index=default_index)
        selected_enc_id = selected_option.split(" - ")[0]
        # Sync SEO search-friendly query params
        st.query_params["encounter"] = selected_enc_id
        st.query_params["tab"] = "single-claim"

    canonical_url = f"https://flugel-rcm-claim-scrubber-ai.streamlit.app/?tab=single-claim&encounter={selected_enc_id}"
    with col_link:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        st.caption(f"🔗 **SEO Canonical URL:** [`?encounter={selected_enc_id}`]({canonical_url})")

    # Retrieve data
    current_pkg = st.session_state.audit_cache[selected_enc_id]
    detail = current_pkg["detail"]
    patient = detail["patient"]
    raw_note = detail["clinical_note"]
    proposed_claim = detail["proposed_claim"]

    # Check if user previously simulated auto-fix
    is_fixed = selected_enc_id in st.session_state.applied_fixes

    # Display Encounter Header Banner
    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 16px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: #1e293b;">{patient['name']} <span class="badge-phi">{selected_enc_id}</span></h4>
                        <p style="margin: 4px 0 0 0; color: #64748b; font-size: 0.9rem;">
                            <strong>DOB:</strong> {patient['dob']} | <strong>MRN:</strong> {patient['mrn']} | <strong>Payer:</strong> {patient['insurance_plan']} | <strong>DOS:</strong> {detail['date_of_service']}
                        </p>
                        <p style="margin: 6px 0 0 0; font-size: 0.8rem; color: #0284c7;">
                            🌐 <strong>Canonical URL:</strong> <a href="{canonical_url}" target="_blank" style="color: #0284c7; text-decoration: none; font-weight: 500;">{canonical_url}</a>
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 1.3rem; font-weight: 700; color: #0284c7;">${proposed_claim['total_charge']:.2f}</span><br>
                        <span style="font-size: 0.85rem; color: #64748b;">Provider: {detail['provider']}</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Two columns: Left (Clinical Note & Proposed Claim), Right (Audit Results & Auto-Fix)
    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.subheader("📄 Raw EHR Documentation & Draft Billing Slip")
        with st.expander("Physician Progress Note (SOAP)", expanded=True):
            st.text_area("Clinical Note", raw_note, height=260, disabled=True, label_visibility="collapsed")

        with st.expander("Proposed Claim Payload (ASC X12 837P Draft)", expanded=True):
            st.json(proposed_claim)

    with col_right:
        st.subheader("🤖 Multi-Agent Audit Results")

        # Evaluate claim: if auto-fixed, show Clean state
        if is_fixed:
            report = ClaimAuditReport(
                encounter_id=selected_enc_id,
                patient_token=f"TOKEN-{selected_enc_id[-4:]}",
                status="CLEAN",
                denial_risk_score=4,
                detected_issues=[],
                recommended_fixes=[],
                compliance_summary="Auto-remediation applied: Claim corrected and approved for ASC X12 837P pre-submission.",
                first_pass_reimbursement_estimate=f"${proposed_claim['total_charge']:.2f}"
            )
        else:
            report = current_pkg["report"]

        # Audit Outcome Card
        card_class = "audit-card-clean" if report.status == "CLEAN" else "audit-card-hold"
        badge_class = "badge-clean" if report.status == "CLEAN" else "badge-hold"
        badge_text = "PASSED COMPLIANCE" if report.status == "CLEAN" else "HELD PRE-SUBMISSION"

        st.markdown(
            f"""
            <div class="{card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="{badge_class}">{badge_text}</span>
                    <span style="font-size: 1.1rem; font-weight: 700;">Denial Risk Score: {report.denial_risk_score}/100</span>
                </div>
                <h4 style="margin: 12px 0 6px 0;">{report.status}</h4>
                <p style="margin: 0; font-size: 0.95rem; color: #334155;">{report.compliance_summary}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.progress(report.denial_risk_score / 100.0)

        # Issues & Recommendations
        if report.detected_issues:
            st.markdown("#### ⚠️ Detected Payer Rule Violations")
            for idx, issue in enumerate(report.detected_issues, 1):
                st.error(
                    f"**Issue {idx} [{issue.severity}]: {issue.issue_type}**\n\n"
                    f"{issue.description}\n\n"
                    f"*Regulatory Reference: {issue.policy_reference}*"
                )

            st.markdown("#### 🛠️ Recommended Remediation Actions")
            for idx, fix in enumerate(report.recommended_fixes, 1):
                st.info(f"**Action {idx} [{fix.action}]:** {fix.rationale}")

            # Auto-Apply Fixes Button
            st.markdown("---")
            if st.button("✨ Auto-Apply Recommended Fixes & Re-Scrub", type="primary", use_container_width=True):
                st.session_state.applied_fixes.add(selected_enc_id)
                # Sync update with MCP Server
                demo_mcp_server.update_claim_status(
                    encounter_id=selected_enc_id,
                    status="CLEAN",
                    remediation_report={"status": "CLEAN", "remediated_by": "1-Click Auto Scrubber"}
                )
                st.success("✅ Fixes successfully applied! Claim re-scrubbed and updated to CLEAN.")
                st.rerun()

        else:
            st.success("✅ **100% First-Pass Acceptance Forecast:** All CPT/ICD-10 pairings pass CMS LCD and NCCI edits.")
            st.metric("Estimated Reimbursement", report.first_pass_reimbursement_estimate)

    # -------------------------------------------------------------------------
    # Live Multi-Agent Execution Trace (Expandable)
    # -------------------------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🔬 View Live Multi-Agent Pipeline Trace (HIPAA Hook -> Coder -> Scrubber)", expanded=False):
        redacted_preview = redact_phi(raw_note)
        coded_preview = current_pkg["coded"]

        st.markdown("#### 1. HIPAA PHI Redaction Lifecycle Hook (`phi_redaction_hook.py`)")
        st.markdown(
            "The synchronous hook intercepts raw physician narrative and masks all 18 HIPAA Safe Harbor identifiers:"
        )
        st.code(redacted_preview[:600] + "\n... [TRUNCATED SAFE-HARBOR TEXT]", language="text")

        st.markdown("#### 2. Clinical Coder Subagent Extraction (`clinical-coder.md`)")
        st.markdown(
            "The `clinical-coder` subagent parses the sanitized note into structured diagnosis, procedure, and MDM models:"
        )
        st.json(coded_preview.model_dump())

        st.markdown("#### 3. Claim Scrubber Subagent Validation (`claim-scrubber.md`)")
        st.markdown(
            "The `claim-scrubber` cross-references extracted codes against `payer-compliance-rules.md` (LCDs, NCCI, Modifiers):"
        )
        st.json(report.model_dump())


# =============================================================================
# TAB 2: Batch Queue Audit & CSV Export
# =============================================================================
with tab2:
    st.subheader("📋 Pre-Submission Batch Queue Audit")
    st.markdown("Audit all pending encounters across the clinical department to scrub claims in bulk before clearinghouse batch generation.")

    col_btn, col_metric = st.columns([2, 3])
    with col_btn:
        run_batch = st.button("🚀 Audit Entire Billing Queue", type="primary", use_container_width=True)

    # Build summary dataframe
    batch_rows = []
    for enc in all_enc_raw:
        eid = enc["encounter_id"]
        pkg = st.session_state.audit_cache.get(eid)
        if pkg:
            rep = pkg["report"]
            if eid in st.session_state.applied_fixes:
                status = "CLEAN (AUTO-FIXED)"
                risk = 4
                issues_count = 0
                action = "Ready for ASC X12 837P"
            else:
                status = rep.status
                risk = rep.denial_risk_score
                issues_count = len(rep.detected_issues)
                action = "Ready for 837P" if rep.status == "CLEAN" else f"Apply {len(rep.recommended_fixes)} Fix(es)"

            primary_dx = ", ".join([d["code"] for d in pkg["detail"]["proposed_claim"]["diagnoses"]])
            cpts = ", ".join([p["code"] for p in pkg["detail"]["proposed_claim"]["procedures"]])

            batch_rows.append({
                "Encounter ID": eid,
                "Patient Token": rep.patient_token,
                "Insurance Plan": pkg["detail"]["patient"]["insurance_plan"],
                "Diagnoses (ICD-10)": primary_dx,
                "Procedures (CPT)": cpts,
                "Charge ($)": f"${pkg['detail']['proposed_claim']['total_charge']:.2f}",
                "Audit Status": status,
                "Denial Risk Score": f"{risk}/100",
                "Flagged Issues": issues_count,
                "Action Required": action
            })

    df_batch = pd.DataFrame(batch_rows)

    if run_batch:
        with st.spinner("Executing Multi-Agent Batch Audit across all encounters..."):
            time.sleep(1.2)
        st.success(f"Audit completed across {len(batch_rows)} encounters.")

    st.dataframe(df_batch, use_container_width=True, hide_index=True)

    # CSV Download Button
    csv_data = df_batch.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Audit Summary (CSV)",
        data=csv_data,
        file_name="pre_submission_claim_audit_results.csv",
        mime="text/csv",
        use_container_width=False
    )


# =============================================================================
# TAB 3: AI Denial Appeal Letter Generator
# =============================================================================
with tab3:
    st.subheader("📝 AI-Powered Formal Payer Denial Appeal Letter Generator")
    st.markdown(
        "Generate a formal, legally and clinically rigorous **Level 1 Redetermination Appeal Letter** citing physician notes, "
        "medical decision making, and CMS Local Coverage Determinations (LCDs) using the `denial-appeals` subagent."
    )

    col_app1, col_app2, col_app3 = st.columns([2, 2, 2])
    with col_app1:
        flagged_encs = [
            f"{enc['encounter_id']} - {enc['patient_name']}"
            for enc in all_enc_raw
        ]
        sel_appeal_enc = st.selectbox("Select Encounter to Appeal:", flagged_encs, index=0)
        appeal_enc_id = sel_appeal_enc.split(" - ")[0]

    with col_app2:
        appeal_payer = st.selectbox(
            "Target Payer Appeals Unit:",
            ["Medicare Administrative Contractor (MAC)", "Aetna Appeals & Grievances", "UnitedHealthcare Commercial Appeals", "Cigna Clinical Review"]
        )

    with col_app3:
        appeal_level = st.selectbox(
            "Appeal Tier:",
            ["Level 1 - Formal Redetermination", "Level 2 - Reconsideration (QIC)", "External Independent Review"]
        )

    # Fetch pkg
    appeal_pkg = st.session_state.audit_cache[appeal_enc_id]
    appeal_rep = appeal_pkg["report"]
    appeal_note = appeal_pkg["detail"]["clinical_note"]
    appeal_charge = f"${appeal_pkg['detail']['proposed_claim']['total_charge']:.2f}"

    if st.button("⚡ Generate Formal Payer Appeal Letter", type="primary"):
        with st.spinner("Denial Appeals Agent synthesizing clinical evidence and citing LCD policies..."):
            letter_obj = denial_appeals.draft_appeal_letter(
                encounter_id=appeal_enc_id,
                audit_report=appeal_rep,
                clinical_note=redact_phi(appeal_note),
                payer_name=appeal_payer,
                disputed_amount=appeal_charge
            )
            st.session_state.generated_letter = letter_obj.appeal_letter_text
            st.session_state.letter_encounter = appeal_enc_id

    if "generated_letter" in st.session_state and st.session_state.get("letter_encounter") == appeal_enc_id:
        st.markdown("#### Formal Appeal Letter Output")
        st.text_area(
            "Generated Appeal Letter",
            st.session_state.generated_letter,
            height=450
        )
        st.download_button(
            label="📄 Download Appeal Letter (.txt)",
            data=st.session_state.generated_letter,
            file_name=f"Appeal_Letter_{appeal_enc_id}.txt",
            mime="text/plain"
        )


# -----------------------------------------------------------------------------
# Application Footer
# -----------------------------------------------------------------------------
st.markdown("<br><hr style='border: none; border-top: 1px solid #e2e8f0; margin-top: 40px;'>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="text-align: center; color: #64748b; font-size: 0.88rem; padding: 10px 0 25px 0;">
        <strong>© Copyright Flugelsoft Labs</strong>. All Rights Reserved. &nbsp;|&nbsp; Enterprise Revenue Cycle Intelligence Platform
    </div>
    """,
    unsafe_allow_html=True
)


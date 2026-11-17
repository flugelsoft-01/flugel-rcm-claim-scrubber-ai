# System Architecture & Technical Specifications

## 1. Executive Summary & Clinical Context
In United States healthcare operations, claim denials account for over **$20 Billion in lost revenue and administrative friction annually**. Industry data reveals that **86% of initial claim denials are preventable** prior to ASC X12 837P pre-submission.

Traditional clearinghouses and rules engines rely on static, post-coding edit checks that lack contextual access to the underlying unstructured physician progress notes (SOAP notes). This platform bridges clinical documentation and revenue cycle compliance by orchestrating a specialized Multi-Agent System to catch billing traps before claims are submitted to clearinghouses.

---

## 2. Multi-Agent Pipeline & Data Flow

```
[Simulated FHIR EHR Queue]
            │
            ▼
[HIPAA PHI Redaction Hook] (Masks 18 Safe Harbor identifiers)
            │
            ▼
[Clinical Coder Agent] (Extracts ICD-10-CM with laterality, CPT, and MDM)
            │
            ▼
[Claim Scrubber Agent] ◄── [Payer Compliance Knowledge Base (LCD/NCCI/Modifiers)]
            │
            ├──► If Clean ──► Approved for 837P Submission (Denial Risk < 5%)
            │
            └──► If Held  ──► [1-Click Auto-Remediation] OR [Denial Appeals Agent]
```

### Stage 1: Simulated FHIR EHR Ingestion (`demo_mcp_server.py`)
- Simulates an outpatient Electronic Health Record (EHR) and pre-submission billing queue using the **Model Context Protocol (MCP)**.
- Exposes structured clinical encounters containing both unstructured physician progress notes (HPI, Physical Exam, Procedure Details, Assessment & Plan) and initial draft billing slips.

### Stage 2: HIPAA Safe Harbor De-Identification Hook (`phi_redaction_hook.py`)
- Implements a synchronous pre-execution lifecycle hook conforming to HIPAA 45 CFR § 164.514 (Safe Harbor Method).
- Intercepts all outgoing payloads and masks 18 statutory identifiers before reaching any language model:
  - Patient Names (e.g. `Harold Finch` -> `[REDACTED-PATIENT-NAME]`)
  - Social Security Numbers (`999-XX-XXXX` -> `[REDACTED-SSN]`)
  - Dates of Birth (`YYYY-MM-DD` -> `[REDACTED-DOB]`)
  - Medical Record Numbers (`MRN-XXXXX` -> `[REDACTED-MRN]`)
  - Phone numbers, email addresses, and geographical details.

### Stage 3: Clinical Coder Subagent (`clinical-coder.md`)
- Ingests the sanitized clinical narrative.
- Decomposes Subjective, Objective, Assessment, and Plan sections.
- Evaluates Medical Decision Making (MDM) complexity based on problems addressed, diagnostic data reviewed, and clinical risk.
- Extracts standardized diagnosis codes with explicit laterality (Right vs. Left vs. Bilateral) and procedure codes with categorical classification.

### Stage 4: Claim Scrubber Subagent (`claim-scrubber.md`)
- Cross-references extracted codes and proposed billing slips against `payer-compliance-rules.md`:
  1. **Medical Necessity & Local Coverage Determinations (LCDs):** Validates whether primary/secondary diagnoses support the CPT procedure.
  2. **Same-Day E/M and Procedure Bundling (Modifier 25):** Verifies that Evaluation & Management codes billed with minor procedures or imaging include Modifier 25 supported by distinct documentation.
  3. **Anatomical Laterality Verification (-RT, -LT):** Ensures procedures on paired extremities (e.g., knee, shoulder) have explicit laterality modifiers matching unilateral diagnoses.
  4. **National Correct Coding Initiative (NCCI) PTP Edits:** Flags unbundled Column 2 component procedures (e.g., routine venipunctures).
- Computes a deterministic **Denial Risk Score (0–100)** and outputs structured JSON remediation instructions.

### Stage 5: Denial Appeals Subagent (`denial-appeals.md`)
- For claims held or retroactively denied, this subagent synthesizes the clinical chart, objective exam findings, and LCD statutory authorities to draft formal Level 1 Redetermination appeal letters.

---

## 3. Technology Stack & Design Principles

| Layer | Component | Technical Role |
| :--- | :--- | :--- |
| **Agentic Framework** | Multi-Agent Architecture | Decomposed autonomous agent roles with clear separation of concerns (Coder, Scrubber, Appeals). |
| **Protocol Integration** | FastMCP (Model Context Protocol) | Stdio and SSE transport architecture for tool invocation and EHR data exchange. |
| **Data Contracts** | Pydantic V2 | Strict typed validation schemas ensuring deterministic JSON inputs and outputs. |
| **Privacy & Security** | HIPAA Safe Harbor Engine | Pre-execution regex and token masking safeguarding Protected Health Information (PHI). |
| **Application UI** | Streamlit | Real-time reactive dashboard with custom CSS, executive KPIs, and live agent tracing. |
| **Data Analytics** | Pandas | Tabular batch aggregation, risk stratification, and CSV reporting. |

---

## 4. Key Regulatory Standards Codified
- **CMS Publication 100-04 (Medicare Claims Processing Manual)** Chapters 12 and 23.
- **Title XVIII Social Security Act §1862(a)(1)(A)** (Medical Necessity standard).
- **NCCI Policy Manual for Medicare Services** Chapter 1 (General Correct Coding Policies).
- **AMA Current Procedural Terminology (CPT®) Assistant** guidelines for Modifier 25 and Modifier 59.
- **CMS Local Coverage Determinations (LCDs):** LCD-33782 (Joint Injections/Aspirations), LCD-ECHOCARDIOGRAPHY (TTE), and LCD-BRAIN-MRI (Neuroimaging).

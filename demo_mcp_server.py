#!/usr/bin/env python3
"""
demo_mcp_server.py - Simulated FHIR EHR & Pre-Submission Billing Queue MCP Server

Provides realistic synthetic encounters to demonstrate automated claim scrubbing,
clinical code extraction, and payer compliance auditing.
"""

import sys
import os
import json
from typing import Dict, List, Any, Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
port = int(os.environ.get("MCP_PORT", 8080))
mcp = FastMCP("Healthcare-EHR-Billing-Queue", port=port)

# In-memory database of synthetic clinical encounters matching compliance specifications
SYNTHETIC_ENCOUNTERS: Dict[str, Dict[str, Any]] = {
    "ENC-1001": {
        "encounter_id": "ENC-1001",
        "patient": {
            "name": "Harold Finch",
            "dob": "1958-04-12",
            "ssn": "999-12-3456",
            "mrn": "MRN-88219",
            "gender": "Male",
            "insurance_plan": "Medicare Advantage Blue"
        },
        "date_of_service": "2026-11-10",
        "provider": "Dr. Sarah Jenkins, MD (Internal Medicine, NPI: 1487291034)",
        "department": "Outpatient Internal Medicine Clinic",
        "status": "PENDING_AUDIT",
        "clinical_note": (
            "PATIENT: Harold Finch | DOB: 1958-04-12 | SSN: 999-12-3456 | MRN: MRN-88219\n"
            "DATE: 2026-11-10\n"
            "CHIEF COMPLAINT:\n"
            "1. Uncontrolled hypertension follow-up and chronic medication titration.\n"
            "2. Acute severe right knee pain and mechanical locking following a slip.\n\n"
            "HISTORY OF PRESENT ILLNESS:\n"
            "Harold Finch is a 68-year-old male with long-standing essential hypertension. Today's in-clinic BP "
            "is 164/98 mmHg despite Lisinopril 10mg. Extensively reviewed home logs showing systolic 155-170 mmHg. "
            "Titrated Lisinopril to 20mg daily, counseled on low-sodium dietary restrictions, and ordered comprehensive labs. "
            "In addition, patient suffered an acute twisting injury to the RIGHT knee 4 days ago. Reports severe medial pain, "
            "audible 'pop', and mechanical joint locking.\n\n"
            "PHYSICAL EXAMINATION:\n"
            "Cardiovascular: Regular rhythm, S1/S2 normal, no bruits. Vital Signs: BP 164/98 mmHg, HR 76.\n"
            "Right Knee: Marked joint effusion. Severe tenderness along medial joint line. Positive McMurray test for medial "
            "meniscal derangement. Left knee is completely asymptomatic with normal stability.\n\n"
            "IMAGING ORDER & EXECUTION:\n"
            "Physician ordered and completed an in-office non-contrast magnetic resonance imaging (MRI) of the RIGHT knee joint.\n"
            "Findings: Complex tear of the posterior horn of the medial meniscus with accompanying joint effusion.\n\n"
            "ASSESSMENT & PLAN:\n"
            "1. Essential (primary) hypertension (I10) - escalated pharmacotherapy.\n"
            "2. Complex tear of medial meniscus, right knee (M23.22) & primary osteoarthritis, right knee (M17.11).\n"
            "Documentation Note: Detailed 30-minute cognitive E/M service provided for hypertension management distinct "
            "from the orthopedic evaluation and right knee MRI."
        ),
        "proposed_claim": {
            "diagnoses": [
                {"code": "I10", "description": "Essential (primary) hypertension", "primary": True},
                {"code": "M17.11", "description": "Unilateral primary osteoarthritis, right knee", "primary": False},
                {"code": "M23.22", "description": "Derangement of meniscus due to old tear or injury, right medial meniscus", "primary": False}
            ],
            "procedures": [
                # TRAP 1: Missing Modifier 25 on 99214 despite documented separate E/M service!
                {"code": "99214", "modifiers": [], "description": "Office or other outpatient visit, established patient, moderate MDM"},
                # TRAP 2: Missing -RT laterality modifier on unilateral Right Knee MRI 73721!
                {"code": "73721", "modifiers": [], "description": "Magnetic resonance imaging, any joint of lower extremity; without contrast material"}
            ],
            "total_charge": 690.00
        },
        "audit_history": []
    },
    "ENC-1002": {
        "encounter_id": "ENC-1002",
        "patient": {
            "name": "Eleanor Vance",
            "dob": "1965-09-23",
            "ssn": "999-23-4567",
            "mrn": "MRN-91402",
            "gender": "Female",
            "insurance_plan": "Aetna Choice POS II"
        },
        "date_of_service": "2026-11-12",
        "provider": "Dr. Marcus Reed, MD (Cardiology, NPI: 1598302145)",
        "department": "Cardiovascular Diagnostic Center",
        "status": "PENDING_AUDIT",
        "clinical_note": (
            "PATIENT: Eleanor Vance | DOB: 1965-09-23 | SSN: 999-23-4567 | MRN: MRN-91402\n"
            "DATE: 2026-11-12\n"
            "CHIEF COMPLAINT: Episodic exertional chest tightness and dyspnea on exertion.\n\n"
            "HISTORY OF PRESENT ILLNESS:\n"
            "Eleanor Vance is a 61-year-old female presenting for comprehensive cardiac evaluation. Reports 3-week "
            "history of substernal chest tightness radiating to the left shoulder during moderate physical exertion, "
            "relieved with rest. Accompanied by progressive shortness of breath when climbing stairs. 12-lead ECG demonstrates "
            "normal sinus rhythm without acute ischemic changes. Serial troponins negative.\n\n"
            "PHYSICAL EXAMINATION:\n"
            "Vitals: BP 128/82 mmHg, HR 70, SpO2 98% room air.\n"
            "Cardiovascular: Normal S1 and S2. Soft systolic flow murmur (grade 2/6) audible at right upper sternal border. "
            "Lungs clear to auscultation bilaterally. No peripheral edema.\n\n"
            "PROCEDURE (Transthoracic Echocardiogram):\n"
            "Complete 2D transthoracic echocardiogram with spectral and color flow Doppler performed (CPT 93306).\n"
            "Findings: Normal left ventricular size and preserved systolic function (LVEF 60-65%). Mild concentric left ventricular "
            "hypertrophy. Trace mitral regurgitation. No regional wall motion abnormalities at rest.\n\n"
            "ASSESSMENT:\n"
            "1. Chest pain, unspecified (ICD-10: R07.9) - meets LCD indications for diagnostic echocardiography.\n"
            "2. Shortness of breath (ICD-10: R06.02).\n"
            "Plan: Outpatient stress nuclear testing scheduled. Prescribed low-dose aspirin and beta-blocker."
        ),
        "proposed_claim": {
            "diagnoses": [
                {"code": "R07.9", "description": "Chest pain, unspecified", "primary": True},
                {"code": "R06.02", "description": "Shortness of breath", "primary": False}
            ],
            "procedures": [
                # CLEAN CLAIM: 93306 directly supported by R07.9 / R06.02 under LCD
                {"code": "93306", "modifiers": [], "description": "Echocardiography, transthoracic, real-time with image documentation, includes M-mode, spectral Doppler and color Doppler"}
            ],
            "total_charge": 580.00
        },
        "audit_history": []
    },
    "ENC-1003": {
        "encounter_id": "ENC-1003",
        "patient": {
            "name": "Arthur Dent",
            "dob": "1974-11-05",
            "ssn": "999-34-5678",
            "mrn": "MRN-73211",
            "gender": "Male",
            "insurance_plan": "UnitedHealthcare Commercial Choice"
        },
        "date_of_service": "2026-11-14",
        "provider": "Dr. Elena Rostova, MD (Neurology, NPI: 1679418290)",
        "department": "Comprehensive Headache & Neurology Center",
        "status": "PENDING_AUDIT",
        "clinical_note": (
            "PATIENT: Arthur Dent | DOB: 1974-11-05 | SSN: 999-34-5678 | MRN: MRN-73211\n"
            "DATE: 2026-11-14\n"
            "CHIEF COMPLAINT: Recurring bilateral tension-type headaches.\n\n"
            "HISTORY OF PRESENT ILLNESS:\n"
            "Arthur Dent is a 52-year-old male with a 2-week history of dull, band-like tension headaches across forehead "
            "and occiput, typically worsening in the afternoons after computer work. Reports high occupational stress. "
            "Denies visual changes, nausea, vomiting, photophobia, fever, trauma, or personal history of malignancy. "
            "Never had a seizure or loss of consciousness.\n\n"
            "PHYSICAL & NEUROLOGICAL EXAMINATION:\n"
            "Vitals: BP 122/78 mmHg, HR 68, Afebrile.\n"
            "Neurological: Cranial nerves II-XII intact. Motor strength 5/5 in all four extremities. Sensation intact to light touch. "
            "Cerebellar testing: finger-to-nose and rapid alternating movements normal. Gait steady and normal. "
            "Funduscopic exam: sharp disc margins, no papilledema. Deep tendon reflexes 2+ symmetrical.\n\n"
            "IMAGING ORDER:\n"
            "Physician ordered and billed Brain MRI without contrast (CPT 70551) to 'rule out intracranial pathology'.\n\n"
            "ASSESSMENT:\n"
            "1. Tension-type headache, unspecified (ICD-10: G44.209).\n"
            "Plan: Recommend stress reduction, ergonomic adjustments, OTC ibuprofen. Brain MRI ordered."
        ),
        "proposed_claim": {
            "diagnoses": [
                {"code": "G44.209", "description": "Tension-type headache, unspecified, not intractable", "primary": True}
            ],
            "procedures": [
                # TRAP: Medical Necessity Mismatch! CPT 70551 Brain MRI is NOT covered under LCD for routine tension headache!
                {"code": "70551", "modifiers": [], "description": "Magnetic resonance imaging, brain (including brain stem); without contrast material"}
            ],
            "total_charge": 850.00
        },
        "audit_history": []
    },
    "ENC-1004": {
        "encounter_id": "ENC-1004",
        "patient": {
            "name": "Beatrice Smith",
            "dob": "1982-02-18",
            "ssn": "999-45-6789",
            "mrn": "MRN-65489",
            "gender": "Female",
            "insurance_plan": "Cigna Open Access Plus"
        },
        "date_of_service": "2026-11-15",
        "provider": "Dr. Timothy Vance, MD (Family Medicine, NPI: 1821049381)",
        "department": "Primary Care Associates",
        "status": "PENDING_AUDIT",
        "clinical_note": (
            "PATIENT: Beatrice Smith | DOB: 1982-02-18 | SSN: 999-45-6789 | MRN: MRN-65489\n"
            "DATE: 2026-11-15\n"
            "CHIEF COMPLAINT: Annual comprehensive preventive health examination.\n\n"
            "HISTORY OF PRESENT ILLNESS:\n"
            "Beatrice Smith is a 44-year-old female presenting for her routine annual well-woman checkup. No acute symptoms, "
            "no chronic complaints. Review of systems is completely negative. Immunizations reviewed and up-to-date.\n\n"
            "PHYSICAL EXAMINATION:\n"
            "Comprehensive multi-system examination completed: HEENT, cardiovascular, respiratory, breast, abdomen, "
            "pelvic/Pap smear, and skin exam all within normal limits. Age-appropriate lifestyle and screening counseling provided.\n\n"
            "IN-OFFICE LAB SPECIMEN COLLECTION:\n"
            "Routine screening fasting lipid panel and comprehensive metabolic panel ordered. Standard routine venipuncture "
            "performed in left antecubital fossa by medical assistant without complication.\n\n"
            "ASSESSMENT & PLAN:\n"
            "1. Encounter for general adult medical examination without abnormal findings (ICD-10: Z00.00).\n"
            "Plan: Return in 1 year for routine checkup."
        ),
        "proposed_claim": {
            "diagnoses": [
                {"code": "Z00.00", "description": "Encounter for general adult medical examination without abnormal findings", "primary": True}
            ],
            "procedures": [
                {"code": "99396", "modifiers": [], "description": "Periodic comprehensive preventive medicine reevaluation, established patient (40-64 years)"},
                # TRAP: NCCI PTP Bundling Edit! Routine venipuncture 36415 is bundled into 99396 without separate site/session modifier 59!
                {"code": "36415", "modifiers": [], "description": "Routine venipuncture for specimen collection"}
            ],
            "total_charge": 315.00
        },
        "audit_history": []
    }
}

PAYER_POLICIES = {
    "LCD-ECHOCARDIOGRAPHY": {
        "policy_id": "LCD-ECHOCARDIOGRAPHY",
        "title": "Local Coverage Determination: Transthoracic Echocardiography (CPT 93306)",
        "covered_cpts": ["93306"],
        "mandated_icd10_ranges": [
            "R07.1 - R07.9 (Chest pain)",
            "R06.00 - R06.09 (Dyspnea / Shortness of breath)",
            "I50.1 - I50.9 (Heart failure)",
            "R01.0 - R01.2 (Cardiac murmurs)"
        ],
        "excluded_conditions": ["J00 - J06 (Upper respiratory infections)", "M54 (Back pain)"],
        "rules": "Diagnostic TTE is medically necessary when evaluating symptoms of suspected cardiac etiology including chest pain or exertional dyspnea."
    },
    "LCD-BRAIN-MRI": {
        "policy_id": "LCD-BRAIN-MRI",
        "title": "Local Coverage Determination: Brain Magnetic Resonance Imaging (CPT 70551)",
        "covered_cpts": ["70551"],
        "mandated_icd10_ranges": [
            "G40.0 - G40.9 (Epilepsy / Seizures)",
            "R55 (Syncope with suspected CNS etiology)",
            "G45.0 - G45.9 (Transient cerebral ischemic attacks)",
            "C71.0 - C71.9 (Brain neoplasms)",
            "R51.9 with documented focal neurological deficit"
        ],
        "excluded_conditions": ["G44.209 (Tension-type headache without red flags)", "R53.83 (Fatigue)"],
        "rules": "Non-contrast Brain MRI requires documentation of focal neurologic deficit, sudden onset 'thunderclap' headache, or intractable headache failing conservative therapy."
    },
    "NCCI-POLICY-CH1": {
        "policy_id": "NCCI-POLICY-CH1",
        "title": "National Correct Coding Initiative (NCCI) Policy Manual - PTP Bundling Edits",
        "bundling_guidelines": (
            "1. Evaluation and Management services (99202-99215) billed on the same calendar date as minor procedures or "
            "diagnostic imaging require Modifier 25 supported by distinct medical decision making.\n"
            "2. Routine venipuncture (36415) is an integral component of all-inclusive preventive medicine visits (99381-99397) "
            "and cannot be separately reimbursed unless Modifier 59 is justified by a distinct clinical session or separate site."
        ),
        "ptp_pairs": {
            "99396 + 36415": "Column 1 (99396) / Column 2 (36415) - Bundled unless Modifier 59 documented",
            "99214 + 73721": "Requires Modifier 25 on 99214 for significant separate E/M service"
        }
    }
}


@mcp.tool()
def list_pending_encounters() -> str:
    """Lists all pending clinical encounters in the pre-submission billing queue."""
    encounters = []
    for enc_id, data in SYNTHETIC_ENCOUNTERS.items():
        encounters.append({
            "encounter_id": enc_id,
            "patient_name": data["patient"]["name"],
            "patient_mrn": data["patient"]["mrn"],
            "date_of_service": data["date_of_service"],
            "provider": data["provider"],
            "status": data["status"],
            "diagnoses_count": len(data["proposed_claim"]["diagnoses"]),
            "procedures_count": len(data["proposed_claim"]["procedures"]),
            "total_charge": data["proposed_claim"]["total_charge"]
        })
    return json.dumps(encounters, indent=2)


@mcp.tool()
def get_encounter_details(encounter_id: str) -> str:
    """Retrieves full clinical documentation, synthetic demographics, and proposed codes for an encounter."""
    enc = SYNTHETIC_ENCOUNTERS.get(encounter_id)
    if not enc:
        return json.dumps({"error": f"Encounter {encounter_id} not found"}, indent=2)
    return json.dumps(enc, indent=2)


@mcp.tool()
def get_payer_policy(policy_id: str) -> str:
    """Retrieves clinical coverage rules, LCDs, and NCCI bundling policies."""
    policy = PAYER_POLICIES.get(policy_id)
    if not policy:
        return json.dumps({"error": f"Policy {policy_id} not found. Available: {list(PAYER_POLICIES.keys())}"})
    return json.dumps(policy, indent=2)


@mcp.tool()
def update_claim_status(encounter_id: str, status: str, remediation_report: Dict[str, Any]) -> str:
    """Updates the billing queue with scrubbed status (CLEAN or HOLD_FOR_REVIEW) and stores the audit report."""
    enc = SYNTHETIC_ENCOUNTERS.get(encounter_id)
    if not enc:
        return json.dumps({"success": False, "error": f"Encounter {encounter_id} not found"})
    
    enc["status"] = status
    enc["audit_history"].append({
        "timestamp": "2026-11-18T02:00:00Z",
        "audited_by": "Enterprise Multi-Agent Claim Scrubber",
        "status": status,
        "remediation_report": remediation_report
    })
    return json.dumps({
        "success": True,
        "encounter_id": encounter_id,
        "new_status": status,
        "message": f"Successfully updated {encounter_id} to {status}"
    }, indent=2)


@mcp.tool()
def reset_demo_queue() -> str:
    """Resets all encounters to PENDING_AUDIT status for repeated demonstration testing."""
    for enc in SYNTHETIC_ENCOUNTERS.values():
        enc["status"] = "PENDING_AUDIT"
        enc["audit_history"] = []
    return json.dumps({"success": True, "message": "Demo queue reset successfully."})


def run_dry_run_test():
    """Performs an internal self-test of the encounters database and tool endpoints."""
    print("=" * 60)
    print("Executing demo_mcp_server.py Self-Test...")
    print("=" * 60)
    
    enc_list_json = list_pending_encounters()
    enc_list = json.loads(enc_list_json)
    print(f"Loaded {len(enc_list)} synthetic encounters:")
    for enc in enc_list:
        print(f"  • {enc['encounter_id']}: {enc['patient_name']} ({enc['date_of_service']}) - {enc['status']} - Total: ${enc['total_charge']:.2f}")
    
    for enc_id in ["ENC-1001", "ENC-1002", "ENC-1003", "ENC-1004"]:
        detail = json.loads(get_encounter_details(enc_id))
        diagnoses = [d["code"] for d in detail["proposed_claim"]["diagnoses"]]
        procedures = [f"{p['code']}{''.join(p.get('modifiers', []))}" for p in detail["proposed_claim"]["procedures"]]
        print(f"\n[Encounter {enc_id}]")
        print(f"  Diagnoses : {', '.join(diagnoses)}")
        print(f"  Procedures: {', '.join(procedures)}")
        print(f"  Clinical Note length: {len(detail['clinical_note'])} characters")

    policy_test = json.loads(get_payer_policy("LCD-ECHOCARDIOGRAPHY"))
    print(f"\nLoaded Policy: {policy_test['title']}")
    print("Self-test PASSED successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--test", "test", "--dry-run"]:
        run_dry_run_test()
    elif len(sys.argv) > 1 and sys.argv[1] in ["--dev", "--sse", "dev"]:
        print(f"[*] Starting FastMCP Dev Server (SSE mode) on http://0.0.0.0:{mcp.settings.port} ...")
        mcp.run(transport="sse")
    else:
        # Standard MCP stdio transport execution
        mcp.run(transport="stdio")

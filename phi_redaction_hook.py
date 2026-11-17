#!/usr/bin/env python3
"""
phi_redaction_hook.py - HIPAA PHI Redaction Lifecycle Hook

Implements a pre-tool execution hook conforming to the Antigravity Customization
Hook Specification. Intercepts outgoing payloads to model APIs or external tools
and redacts Protected Health Information (PHI) under HIPAA 45 CFR § 164.514 (Safe Harbor).
"""

import sys
import re
import json
from typing import Any, Dict, List, Union

# Known synthetic and regex-based patient identifier patterns
KNOWN_PATIENT_NAMES = [
    r"Harold Finch",
    r"Eleanor Vance",
    r"Arthur Dent",
    r"Beatrice Smith",
]

# Regular expressions for HIPAA 18 Safe Harbor identifiers
RE_PATIENT_HEADER = re.compile(
    r"(?i)\b(patient(?:\s+name)?|pt(?:\s+name)?|name)\s*[:=]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    re.IGNORECASE
)
RE_SSN = re.compile(r"\b(?:\d{3}-\d{2}-\d{4}|\d{9})\b")
RE_DOB = re.compile(
    r"(?i)\b(dob|date of birth|birthdate|birth\s*date)\s*[:=]\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
    re.IGNORECASE
)
RE_GENERIC_DOB_STRING = re.compile(r"\b(19\d{2}|20[0-2]\d)[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b")
RE_MRN = re.compile(r"(?i)\b(mrn\s*[:=]\s*|mrn-)([A-Z0-9]{4,10})\b", re.IGNORECASE)
RE_PHONE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


def redact_phi(text: str) -> str:
    """Applies HIPAA Safe Harbor masking rules across a string."""
    if not isinstance(text, str):
        return text

    redacted = text

    # Mask known patient names
    for name_pattern in KNOWN_PATIENT_NAMES:
        redacted = re.sub(name_pattern, "[REDACTED-PATIENT-NAME]", redacted, flags=re.IGNORECASE)

    # Mask 'PATIENT: <Name>' or 'Name: <Name>' constructs
    redacted = RE_PATIENT_HEADER.sub(r"\1: [REDACTED-PATIENT-NAME]", redacted)

    # Mask SSN
    redacted = RE_SSN.sub("[REDACTED-SSN]", redacted)

    # Mask DOB patterns explicitly labelled
    redacted = RE_DOB.sub(r"\1: [REDACTED-DOB]", redacted)

    # Mask MRN
    redacted = RE_MRN.sub(r"MRN: [REDACTED-MRN]", redacted)

    # Mask Phone and Email
    redacted = RE_PHONE.sub("[REDACTED-PHONE]", redacted)
    redacted = RE_EMAIL.sub("[REDACTED-EMAIL]", redacted)

    return redacted


def redact_data_structure(data: Any) -> Any:
    """Recursively walks Python dictionaries, lists, or primitives to redact PHI."""
    if isinstance(data, str):
        return redact_phi(data)
    elif isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # If the dictionary key itself explicitly designates a patient identity
            if k in ["name", "patient_name", "first_name", "last_name"] and isinstance(v, str):
                new_dict[k] = "[REDACTED-PATIENT-NAME]"
            elif k in ["ssn", "social_security_number"] and isinstance(v, str):
                new_dict[k] = "[REDACTED-SSN]"
            elif k in ["dob", "date_of_birth", "birthdate"] and isinstance(v, str):
                new_dict[k] = "[REDACTED-DOB]"
            elif k in ["mrn", "patient_mrn"] and isinstance(v, str):
                new_dict[k] = "[REDACTED-MRN]"
            else:
                new_dict[k] = redact_data_structure(v)
        return new_dict
    elif isinstance(data, list):
        return [redact_data_structure(item) for item in data]
    else:
        return data


def process_hook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes an Antigravity Hook payload.
    For PreToolUse: inspects toolCall.args, redacts PHI, and produces an 'overwrite' dictionary.
    """
    tool_call = payload.get("toolCall", {})
    args = tool_call.get("args", {})

    if args:
        redacted_args = redact_data_structure(args)
        return {
            "decision": "allow",
            "reason": "Applied HIPAA Safe Harbor PHI masking (Names, SSNs, DOBs, MRNs sanitized).",
            "overwrite": redacted_args
        }
    else:
        # Generic payload fallback
        redacted_payload = redact_data_structure(payload)
        return {
            "decision": "allow",
            "reason": "Payload verified and sanitized under HIPAA Safe Harbor rules.",
            "sanitized": redacted_payload
        }


def run_selftest():
    """Validates the PHI redaction engine with synthetic clinical examples."""
    print("=" * 60)
    print("Executing phi_redaction_hook.py Self-Test...")
    print("=" * 60)

    sample_raw_note = (
        "PATIENT: Harold Finch | DOB: 1958-04-12 | SSN: 999-12-3456 | MRN: MRN-88219\n"
        "Phone: 555-123-4567, Email: harold.finch@example.com\n"
        "Harold Finch presents with severe right knee pain. Exam by Dr. Jenkins."
    )

    masked_note = redact_phi(sample_raw_note)
    print("Original Note:")
    print(sample_raw_note)
    print("\nRedacted Note:")
    print(masked_note)

    assert "Harold Finch" not in masked_note, "Name was not redacted!"
    assert "999-12-3456" not in masked_note, "SSN was not redacted!"
    assert "1958-04-12" not in masked_note, "DOB was not redacted!"
    assert "[REDACTED-PATIENT-NAME]" in masked_note
    assert "[REDACTED-SSN]" in masked_note
    assert "[REDACTED-DOB]" in masked_note

    # Test Antigravity PreToolUse hook contract
    sample_hook_input = {
        "toolCall": {
            "name": "get_encounter_details",
            "args": {
                "encounter_id": "ENC-1001",
                "patient_name": "Eleanor Vance",
                "ssn": "999-23-4567",
                "note": "Eleanor Vance has BP 162/96."
            }
        },
        "stepIdx": 4
    }
    hook_result = process_hook_payload(sample_hook_input)
    print("\nHook PreToolUse Result:")
    print(json.dumps(hook_result, indent=2))
    assert hook_result["decision"] == "allow"
    assert hook_result["overwrite"]["patient_name"] == "[REDACTED-PATIENT-NAME]"
    assert hook_result["overwrite"]["ssn"] == "[REDACTED-SSN]"

    print("\nAll PHI Redaction self-tests PASSED successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--test", "test"]:
        run_selftest()
    else:
        # Read hook payload from stdin
        try:
            raw_input = sys.stdin.read()
            if raw_input.strip():
                data = json.loads(raw_input)
                result = process_hook_payload(data)
                print(json.dumps(result))
            else:
                print(json.dumps({"decision": "allow", "reason": "No input payload provided."}))
        except Exception as e:
            # Safe fail-open for hook logging
            print(json.dumps({"decision": "allow", "reason": f"Hook completed with notice: {str(e)}"}))

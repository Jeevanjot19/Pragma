"""
HOW Layer — Compliance Rules
Fintech regulatory guardrails for outreach emails.
Checks for violations of RBI, SEBI, DICGC guidelines.
ISSUE 2 FIX: Tracks override patterns to prevent alert fatigue.
"""

from datetime import datetime
from database import get_db


COMPLIANCE_RULES = [
    {
        "id": "R001",
        "rule": "No guaranteed returns",
        "triggers": ["guaranteed", "assured return", "fixed return",
                     "guaranteed interest", "assured interest"],
        "severity": "HIGH",
        "replacement": "current rates up to X% p.a., subject to bank terms"
    },
    {
        "id": "R002",
        "rule": "DICGC insurance must be stated correctly",
        "triggers": ["fully safe", "completely safe", "100% safe",
                     "fully insured", "completely insured"],
        "severity": "HIGH",
        "replacement": "insured up to ₹5 lakh per depositor per bank under DICGC"
    },
    {
        "id": "R003",
        "rule": "Cannot claim RBI approval for pending products",
        "triggers": ["rbi approved", "sebi approved", "rbi certified"],
        "severity": "HIGH",
        "replacement": "RBI-compliant architecture"
    },
    {
        "id": "R004",
        "rule": "No misleading competitor comparisons",
        "triggers": ["better than stable money", "unlike golden pi",
                     "beats deciml", "superior to"],
        "severity": "MEDIUM",
        "replacement": "Remove comparison or state factually"
    },
    {
        "id": "R005",
        "rule": "Interest rates must include qualifiers",
        "triggers": ["8.5% interest", "9% interest", "8% interest", "10% interest"],
        "severity": "MEDIUM",
        "replacement": "up to 8.5% p.a. (rates vary by bank and tenure)"
    },
    {
        "id": "R006",
        "rule": "Cannot promise regulatory outcomes",
        "triggers": ["will get approved", "guaranteed approval",
                     "definitely compliant"],
        "severity": "HIGH",
        "replacement": "designed to meet current regulatory requirements"
    },
]


def check_compliance(email_text: str, rule_id_only: str = None) -> dict:
    """
    Rule-based compliance check on outreach email.
    ISSUE 2 FIX: Tracks override patterns to prevent alert fatigue.
    
    If a rule is overridden 3+ times globally, switches from BLOCKING to WARNING mode.
    Returns structured report with violations, warnings, and suggestions.
    """
    text_lower = email_text.lower()
    violations = []
    warnings = []

    with get_db() as conn:
        overrides = conn.execute(
            "SELECT * FROM compliance_overrides"
        ).fetchall()
    
    override_counts = {
        o['rule_id']: o['override_count'] for o in overrides
    }

    for rule in COMPLIANCE_RULES:
        triggered_by = [t for t in rule['triggers'] if t in text_lower]
        if triggered_by:
            issue = {
                "rule_id": rule['id'],
                "rule": rule['rule'],
                "triggered_by": triggered_by,
                "severity": rule['severity'],
                "replacement": rule['replacement']
            }
            
            # Check if this rule has been overridden 3+ times (Issue 2: Alert fatigue)
            override_count = override_counts.get(rule['id'], 0)
            if override_count >= 3:
                # Demote to warning after 3 overrides
                issue['note'] = f"Flagged {override_count} times previously. Review rule R{rule['id'][-3:]}."
                warnings.append(issue)
            elif rule['severity'] == 'HIGH':
                violations.append(issue)
            else:
                warnings.append(issue)

    status = "BLOCKED" if violations else (
        "WARNING" if warnings else "CLEAR"
    )

    return {
        "status": status,
        "violations": violations,
        "warnings": warnings,
        "is_sendable": status != "BLOCKED"
    }


def log_compliance_override(rule_id: str, triggered_phrase: str) -> None:
    """
    Log a compliance rule override (manual approval by sales).
    After 3 overrides of same rule, it will be demoted to warning on future emails.
    """
    with get_db() as conn:
        # Check if an override exists for this rule
        existing = conn.execute(
            "SELECT * FROM compliance_overrides WHERE rule_id = ?",
            (rule_id,)
        ).fetchone()
        
        if existing:
            conn.execute("""
                UPDATE compliance_overrides
                SET override_count = override_count + 1,
                    last_override_at = CURRENT_TIMESTAMP
                WHERE rule_id = ?
            """, (rule_id,))
        else:
            conn.execute("""
                INSERT INTO compliance_overrides
                (rule_id, triggered_phrase, override_count, 
                 last_override_at, first_override_at)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (rule_id, triggered_phrase))
        
        conn.commit()

#!/usr/bin/env python3
"""
ACTIVATION Layer (Redesigned) — Real Stall Detection
Detects 3 real activation stalls using actual API call data from Blostem's API.

Pattern 1: Dead on Arrival — 0 sandbox calls in 14 days after signing
Pattern 2: Stuck in Sandbox — Sandbox calls exist but 7+ day silence (likely technical blocker)
Pattern 3: Sandbox → Production Gap — Successful sandbox tests but no production calls in 14+ days

Plus: Political risk signals from news monitoring (competitor mention, job postings)
"""

from datetime import datetime, timedelta
from database import get_db
from signals.timing import calculate_when_score


class StallPattern:
    """Enum for stall patterns."""
    DEAD_ON_ARRIVAL = "DEAD_ON_ARRIVAL"
    STUCK_IN_SANDBOX = "STUCK_IN_SANDBOX"
    PRODUCTION_BLOCKED = "PRODUCTION_BLOCKED"


def detect_dead_on_arrival(partner_id: int) -> dict | None:
    """
    Pattern 1: Dead on Arrival
    Partner signed but made ZERO API calls in 14 days.
    Likely cause: Person who signed isn't the person who integrates.
    
    Returns: Detection result or None if pattern not detected
    """
    with get_db() as conn:
        # Get partner signup date
        partner = conn.execute(
            "SELECT signed_at FROM partners_activated WHERE id = ?",
            (partner_id,)
        ).fetchone()
        
        if not partner:
            return None
        
        signed_at = datetime.fromisoformat(partner['signed_at'])
        days_since_signed = (datetime.now() - signed_at).days
        
        # Only check if 14+ days have passed
        if days_since_signed < 14:
            return None
        
        # Check for ANY API calls (sandbox or production)
        api_calls = conn.execute(
            "SELECT COUNT(*) as count FROM partner_api_calls WHERE partner_id = ?",
            (partner_id,)
        ).fetchone()
        
        if api_calls['count'] > 0:
            return None  # Pattern not detected
        
        return {
            "pattern": StallPattern.DEAD_ON_ARRIVAL,
            "detected": True,
            "days_of_inactivity": days_since_signed,
            "signed_at": partner['signed_at'],
            "api_calls_made": 0,
            "severity": "CRITICAL",
            "likely_cause": "Person who signed isnt the person who integrates"
        }


def detect_stuck_in_sandbox(partner_id: int) -> dict | None:
    """
    Pattern 2: Stuck in Sandbox
    Partner made sandbox API calls but then went silent for 7+ days.
    Likely cause: Technical blocker (auth failure, missing field, integration complexity)
    
    Returns: Detection result with last error code (if any)
    """
    with get_db() as conn:
        # Get last sandbox API call
        last_sandbox_call = conn.execute(
            """SELECT called_at, status_code, error_code, error_message, endpoint
               FROM partner_api_calls 
               WHERE partner_id = ? AND environment = 'sandbox'
               ORDER BY called_at DESC LIMIT 1""",
            (partner_id,)
        ).fetchone()
        
        if not last_sandbox_call:
            return None  # No sandbox calls made
        
        last_call_date = datetime.fromisoformat(last_sandbox_call['called_at'])
        days_since_last_call = (datetime.now() - last_call_date).days
        
        # Pattern triggers if 7+ days of silence after sandbox activity
        if days_since_last_call < 7:
            return None
        
        # Count total sandbox calls
        sandbox_call_count = conn.execute(
            "SELECT COUNT(*) as count FROM partner_api_calls WHERE partner_id = ? AND environment = 'sandbox'",
            (partner_id,)
        ).fetchone()
        
        # Check for recent errors
        recent_errors = conn.execute(
            """SELECT error_code, COUNT(*) as count 
               FROM partner_api_calls 
               WHERE partner_id = ? AND environment = 'sandbox' 
               AND error_code IS NOT NULL
               AND called_at > datetime('now', '-14 days')
               GROUP BY error_code
               ORDER BY count DESC""",
            (partner_id,)
        ).fetchall()
        
        return {
            "pattern": StallPattern.STUCK_IN_SANDBOX,
            "detected": True,
            "days_of_inactivity": days_since_last_call,
            "last_api_call": last_sandbox_call['called_at'],
            "total_sandbox_calls": sandbox_call_count['count'],
            "last_endpoint": last_sandbox_call['endpoint'],
            "last_status_code": last_sandbox_call['status_code'],
            "last_error_code": last_sandbox_call['error_code'],
            "recent_errors": [dict(e) for e in recent_errors],
            "severity": "HIGH",
            "likely_cause": "Technical blocker (check error codes above)"
        }


def detect_production_blocked(partner_id: int) -> dict | None:
    """
    Pattern 3: Sandbox → Production Gap
    Partner successfully used sandbox (recent API calls with 200s) but zero production calls in 14+ days.
    Likely cause: Approval/procurement/internal sign-off required.
    
    Returns: Detection result
    """
    with get_db() as conn:
        # Check if production calls exist at all
        prod_call_count = conn.execute(
            "SELECT COUNT(*) as count FROM partner_api_calls WHERE partner_id = ? AND environment = 'production'",
            (partner_id,)
        ).fetchone()
        
        if prod_call_count['count'] > 0:
            return None  # Already in production
        
        # Check if successful sandbox calls exist (200s in last 30 days)
        recent_sandbox_success = conn.execute(
            """SELECT COUNT(*) as count FROM partner_api_calls 
               WHERE partner_id = ? AND environment = 'sandbox'
               AND status_code = 200
               AND called_at > datetime('now', '-30 days')""",
            (partner_id,)
        ).fetchone()
        
        if recent_sandbox_success['count'] == 0:
            return None  # No successful sandbox tests
        
        # Get date partner signed
        partner = conn.execute(
            "SELECT signed_at FROM partners_activated WHERE id = ?",
            (partner_id,)
        ).fetchone()
        
        signed_at = datetime.fromisoformat(partner['signed_at'])
        days_since_signed = (datetime.now() - signed_at).days
        
        # Pattern triggers if 14+ days since signing and no prod progress
        if days_since_signed < 14:
            return None
        
        # Get last successful sandbox call
        last_success = conn.execute(
            """SELECT called_at FROM partner_api_calls 
               WHERE partner_id = ? AND environment = 'sandbox' AND status_code = 200
               ORDER BY called_at DESC LIMIT 1""",
            (partner_id,)
        ).fetchone()
        
        return {
            "pattern": StallPattern.PRODUCTION_BLOCKED,
            "detected": True,
            "days_since_signed": days_since_signed,
            "days_since_last_sandbox_success": (datetime.now() - datetime.fromisoformat(last_success['called_at'])).days,
            "signed_at": partner['signed_at'],
            "last_sandbox_success": last_success['called_at'],
            "production_calls_made": 0,
            "severity": "MEDIUM",
            "likely_cause": "Approval/procurement blocker (contact business stakeholder)"
        }


def detect_all_stalls(partner_id: int) -> dict:
    """
    Run all stall pattern detection for a partner.
    Returns first detected pattern (in priority order).
    """
    # Check in order of severity
    detected = detect_dead_on_arrival(partner_id)
    if detected:
        return detected
    
    detected = detect_stuck_in_sandbox(partner_id)
    if detected:
        return detected
    
    detected = detect_production_blocked(partner_id)
    if detected:
        return detected
    
    return {"pattern": None, "detected": False}


def detect_political_risks(partner_id: int) -> list:
    """
    Detect political risks from news monitoring:
    1. Competitor mention in recent news = build-vs-buy risk
    2. Job posting for "banking API engineer" = build-vs-buy risk
    """
    with get_db() as conn:
        # Get partner prospect
        partner = conn.execute(
            "SELECT prospect_id FROM partners_activated WHERE id = ?",
            (partner_id,)
        ).fetchone()
        
        if not partner:
            return []
        
        prospect_id = partner['prospect_id']
        risks = []
        
        # Check for competitor mentions in recent monitoring events
        competitor_mentions = conn.execute(
            """SELECT * FROM monitoring_events 
               WHERE prospect_id = ? 
               AND event_type = 'PARTNERSHIP'
               AND detected_at > datetime('now', '-30 days')
               AND (evidence LIKE '%competitor%' OR evidence LIKE '%powered by%' OR title LIKE '%partnership%')""",
            (prospect_id,)
        ).fetchall()
        
        if competitor_mentions:
            risks.append({
                "risk_type": "COMPETITOR_INTEGRATION",
                "severity": "HIGH",
                "detected_via": "news_monitoring",
                "details": f"Mentioned {len(competitor_mentions)} recent partnership/competitor activity in news",
                "evidence": [dict(m) for m in competitor_mentions]
            })
        
        # Check for job postings (look in monitoring events for hiring signals)
        job_postings = conn.execute(
            """SELECT * FROM monitoring_events 
               WHERE prospect_id = ? 
               AND detected_at > datetime('now', '-30 days')
               AND (title LIKE '%banking API%' OR evidence LIKE '%hiring%' OR evidence LIKE '%software engineer%')""",
            (prospect_id,)
        ).fetchall()
        
        if job_postings:
            risks.append({
                "risk_type": "BUILD_VS_BUY_RISK",
                "severity": "HIGH",
                "detected_via": "job_posting_detection",
                "details": f"Detected {len(job_postings)} job postings suggesting potential in-house build",
                "evidence": [dict(m) for m in job_postings]
            })
        
        return risks


def log_stall_detected(partner_id: int, pattern: str, intervention_sent: bool = False):
    """Log a detected stall pattern to the database."""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO partner_activation_stalls 
               (partner_id, stall_pattern, days_of_inactivity, last_activity_date, intervention_email_sent)
               VALUES (?, ?, 0, datetime('now'), ?)""",
            (partner_id, pattern, 1 if intervention_sent else 0)
        )
        conn.commit()


def log_political_risk(partner_id: int, risk_type: str, detected_via: str, details: str):
    """Log a detected political risk to the database."""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO partner_political_risks 
               (partner_id, risk_type, detected_via, details)
               VALUES (?, ?, ?, ?)""",
            (partner_id, risk_type, detected_via, details)
        )
        conn.commit()

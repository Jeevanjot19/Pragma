"""
ACTIVATE Layer — Component D: Partner Activation Monitoring
Tracks signed partner onboarding progress and detects activation stalls.
Generates targeted re-engagement content when partners go silent.

Brief Context:
"Once a partner signs, activation stalls." This layer bridges the gap between
signature and successful integration, transforming Pragma from a prospecting tool
into a full partner lifecycle tool.

Layer Flow:
1. Track activation milestones for signed partners
2. Detect stalls (no activity, slow progress, technical blockers)
3. Generate targeted re-engagement content based on where partner is stuck
4. Monitor improvements after intervention
"""

from datetime import datetime, timedelta
from database import get_db
import math

# ============================================================================
# ACTIVATION MILESTONES — Define expected partner journey
# ============================================================================

ACTIVATION_MILESTONES = [
    {
        "id": "M001",
        "name": "Integration Started",
        "description": "API credentials received, initial docs reviewed",
        "expected_days": 1,
        "detection_signals": ["api_credentials_issued"],
        "success_indicators": ["credentials_in_system"],
        "typical_blockers": ["api_docs_unclear", "no_dedicated_contact"]
    },
    {
        "id": "M002",
        "name": "Sandbox Integration",
        "description": "First API call made, test integration working",
        "expected_days": 7,
        "depends_on": "M001",
        "detection_signals": ["first_api_call", "sandbox_auth_test"],
        "success_indicators": ["successful_test_call"],
        "typical_blockers": ["auth_issues", "integration_complexity", "resource_constraints"]
    },
    {
        "id": "M003",
        "name": "Production Ready",
        "description": "Production environment configured, security approved",
        "expected_days": 14,
        "depends_on": "M002",
        "detection_signals": ["prod_environment_setup", "security_review_passed"],
        "success_indicators": ["prod_credentials_active"],
        "typical_blockers": ["security_concerns", "compliance_delays", "it_approval_pending"]
    },
    {
        "id": "M004",
        "name": "First Transaction",
        "description": "First real transaction processed successfully",
        "expected_days": 21,
        "depends_on": "M003",
        "detection_signals": ["first_live_transaction"],
        "success_indicators": ["transaction_settled"],
        "typical_blockers": ["business_model_misalignment", "user_adoption_gap"]
    },
    {
        "id": "M005",
        "name": "10 Transactions",
        "description": "Basic volume validation, feature bugs worked out",
        "expected_days": 35,
        "depends_on": "M004",
        "detection_signals": ["volume_threshold_reached"],
        "success_indicators": ["stable_transaction_flow"],
        "typical_blockers": ["user_friction", "feature_gaps", "customer_support_issues"]
    },
    {
        "id": "M006",
        "name": "Healthy Recurring",
        "description": "Recurring usage > 5 days per month, sustainable",
        "expected_days": 60,
        "depends_on": "M005",
        "detection_signals": ["monthly_active_days_threshold"],
        "success_indicators": ["sustainable_usage_pattern"],
        "typical_blockers": ["user_retention_issues", "competitive_pressure"]
    }
]

# Stall thresholds by milestone
STALL_CONFIG = {
    "M001": {"days_threshold": 3, "severity": "CRITICAL"},   # Should get credentials quickly
    "M002": {"days_threshold": 14, "severity": "HIGH"},      # Sandbox test should be fast
    "M003": {"days_threshold": 21, "severity": "HIGH"},      # Production setup
    "M004": {"days_threshold": 35, "severity": "MEDIUM"},    # First transaction
    "M005": {"days_threshold": 45, "severity": "MEDIUM"},    # Volume validation
    "M006": {"days_threshold": 90, "severity": "LOW"}        # Recurring usage
}

# Re-engagement strategies by stall type
REENGAGEMENT_STRATEGIES = {
    "integration_blocked": {
        "persona": "TECHNICAL_LEAD",
        "template": "integration_support",
        "escalation": "engineering_support",
        "urgency": "HIGH"
    },
    "business_gap": {
        "persona": "PRODUCT_LEAD",
        "template": "feature_discovery",
        "escalation": "success_manager",
        "urgency": "MEDIUM"
    },
    "user_adoption": {
        "persona": "MARKETING_LEAD",
        "template": "adoption_acceleration",
        "escalation": "training",
        "urgency": "MEDIUM"
    },
    "silent": {
        "persona": "ACCOUNT_MANAGER",
        "template": "checkin",
        "escalation": "direct_call",
        "urgency": "MEDIUM"
    }
}


def get_milestone_by_id(milestone_id: str) -> dict | None:
    """Get milestone definition by ID."""
    for m in ACTIVATION_MILESTONES:
        if m["id"] == milestone_id:
            return m
    return None


def calculate_activation_score(partner_id: int) -> dict:
    """
    Score partner activation health: 0-100.
    Factors:
    - Milestone progress (40 pts)
    - Time-to-milestone speed (30 pts)
    - Activity recency (20 pts)
    - Risk indicators (10 pts penalty)
    """
    with get_db() as conn:
        partner = conn.execute(
            "SELECT * FROM partners_activated WHERE id = ?",
            (partner_id,)
        ).fetchone()
        
        if not partner:
            return {"error": "Partner not found"}
        
        partner = dict(partner)
        
        # 1. Milestone progress (40 pts max)
        milestone_num = 0
        for i, m in enumerate(ACTIVATION_MILESTONES):
            if m["id"] == partner.get("current_milestone"):
                milestone_num = i
                break
        
        milestone_pts = min((milestone_num / len(ACTIVATION_MILESTONES)) * 40, 40)
        
        # 2. Time-to-milestone speed (30 pts max)
        # Deduct points for being slow relative to expected timeline
        speed_pts = 30
        if partner.get("days_in_current_milestone"):
            milestone_def = get_milestone_by_id(partner.get("current_milestone", "M001"))
            expected_days = milestone_def.get("expected_days", 7) if milestone_def else 7
            days_behind = max(0, partner["days_in_current_milestone"] - expected_days)
            
            # Lose 1 pt per 3 days behind
            speed_penalty = min((days_behind / 3), 30)
            speed_pts = 30 - speed_penalty
        
        # 3. Activity recency (20 pts max)
        activity_pts = 20
        if partner.get("last_activity"):
            try:
                last_activity = datetime.fromisoformat(partner["last_activity"])
                days_since_activity = (datetime.now() - last_activity).days
                
                if days_since_activity <= 7:
                    activity_pts = 20  # Recent activity
                elif days_since_activity <= 14:
                    activity_pts = 15
                elif days_since_activity <= 30:
                    activity_pts = 10
                else:
                    activity_pts = max(0, 10 - (days_since_activity - 30) // 10)
            except Exception:
                activity_pts = 10
        
        # 4. Risk indicators (-10 pts if stalled)
        risk_pts = 0
        if partner.get("is_at_risk", 0) == 1:
            risk_pts = -10
        
        # Final score
        activation_score = int(milestone_pts + speed_pts + activity_pts + risk_pts)
        activation_score = max(0, min(activation_score, 100))
        
        # Determine health status
        if activation_score >= 75:
            health_status = "ON_TRACK"
        elif activation_score >= 50:
            health_status = "AT_RISK"
        else:
            health_status = "CRITICAL"
        
        return {
            "partner_id": partner_id,
            "partner_name": dict(conn.execute(
                "SELECT name FROM prospects WHERE id = ?",
                (partner.get("prospect_id"),)
            ).fetchone() or {}).get("name", "Unknown"),
            "activation_score": activation_score,
            "health_status": health_status,
            "current_milestone": partner.get("current_milestone"),
            "days_in_milestone": partner.get("days_in_current_milestone", 0),
            "last_activity": partner.get("last_activity"),
            "days_silent": (datetime.now() - datetime.fromisoformat(
                partner["last_activity"]
            )).days if partner.get("last_activity") else "unknown",
            "score_breakdown": {
                "milestone_progress": milestone_pts,
                "speed_to_milestone": speed_pts,
                "activity_recency": activity_pts,
                "risk_penalty": risk_pts
            }
        }


def detect_activation_stalls() -> list:
    """
    Scan all activated partners and identify stalls.
    Returns list of at-risk partners with detected issues.
    """
    with get_db() as conn:
        partners = conn.execute(
            "SELECT id, current_milestone, last_activity, milestone_reached_at FROM partners_activated"
        ).fetchall()
    
    at_risk = []
    
    for partner in partners:
        partner = dict(partner)
        partner_id = partner["id"]
        current_milestone = partner.get("current_milestone", "M001")
        stall_config = STALL_CONFIG.get(current_milestone, {})
        days_threshold = stall_config.get("days_threshold", 30)
        severity = stall_config.get("severity", "MEDIUM")
        
        # Check if silent (no recent activity)
        days_silent = None
        if partner.get("last_activity"):
            try:
                last_activity = datetime.fromisoformat(partner["last_activity"])
                days_silent = (datetime.now() - last_activity).days
            except Exception:
                pass
        
        if days_silent and days_silent > days_threshold:
            at_risk.append({
                "partner_id": partner_id,
                "stall_type": "SILENT",
                "current_milestone": current_milestone,
                "days_silent": days_silent,
                "severity": severity,
                "reason": f"No activity for {days_silent} days (threshold: {days_threshold})"
            })
        
        # Check if slow (in milestone longer than expected)
        if partner.get("milestone_reached_at"):
            try:
                milestone_start = datetime.fromisoformat(partner["milestone_reached_at"])
                days_in_milestone = (datetime.now() - milestone_start).days
                milestone_def = get_milestone_by_id(current_milestone)
                expected_days = milestone_def.get("expected_days", 7) if milestone_def else 7
                
                if days_in_milestone > (expected_days * 2):  # 2x expected time
                    at_risk.append({
                        "partner_id": partner_id,
                        "stall_type": "SLOW_PROGRESS",
                        "current_milestone": current_milestone,
                        "days_in_milestone": days_in_milestone,
                        "expected_days": expected_days,
                        "severity": "MEDIUM",
                        "reason": f"In {current_milestone} for {days_in_milestone} days (expected: {expected_days})"
                    })
            except Exception:
                pass
    
    return at_risk


def get_activation_recommendations(partner_id: int) -> dict:
    """
    Given a partner in a stalled state, recommend intervention.
    Identifies:
    - What milestone they're stuck on
    - What type of help they likely need
    - What re-engagement strategy to use
    """
    with get_db() as conn:
        partner = conn.execute(
            "SELECT * FROM partners_activated WHERE id = ?",
            (partner_id,)
        ).fetchone()
        
        if not partner:
            return {"error": "Partner not found"}
        
        partner = dict(partner)
        
        # Get issues logged for this partner
        issues = conn.execute(
            "SELECT * FROM partner_issues WHERE partner_id = ? AND resolved_at IS NULL ORDER BY severity DESC",
            (partner_id,)
        ).fetchall()
        issues = [dict(i) for i in issues]
    
    current_milestone = partner.get("current_milestone", "M001")
    
    # Determine stall reason
    stall_reason = "unknown"
    if issues:
        issue_types = [i.get("issue_category") for i in issues]
        if "integration" in str(issue_types).lower():
            stall_reason = "integration_blocked"
        elif "business" in str(issue_types).lower():
            stall_reason = "business_gap"
        elif "adoption" in str(issue_types).lower():
            stall_reason = "user_adoption"
    else:
        stall_reason = "silent"
    
    strategy = REENGAGEMENT_STRATEGIES.get(stall_reason, REENGAGEMENT_STRATEGIES["silent"])
    
    # Get next milestone for success context
    current_index = 0
    for i, m in enumerate(ACTIVATION_MILESTONES):
        if m["id"] == current_milestone:
            current_index = i
            break
    
    next_milestone = ACTIVATION_MILESTONES[min(current_index + 1, len(ACTIVATION_MILESTONES) - 1)] \
        if current_index < len(ACTIVATION_MILESTONES) - 1 else None
    
    return {
        "partner_id": partner_id,
        "current_milestone": current_milestone,
        "next_milestone": next_milestone.get("name") if next_milestone else "Healthy Recurring Status",
        "detected_issues": issues,
        "stall_reason": stall_reason,
        "recommended_strategy": strategy,
        "re_engagement_persona": strategy.get("persona"),
        "re_engagement_template": strategy.get("template"),
        "escalation_path": strategy.get("escalation"),
        "urgency": strategy.get("urgency"),
        "success_story_context": {
            "message": f"Help {partner.get('name', 'partner')} reach {next_milestone.get('name') if next_milestone else 'sustained success'}",
            "quick_wins": get_milestone_by_id(current_milestone).get("typical_blockers", []) if get_milestone_by_id(current_milestone) else []
        }
    }


def log_partner_activity(partner_id: int, activity_type: str, 
                        metric_type: str = None, metric_value: float = None, 
                        notes: str = None) -> None:
    """
    Record an activity event for a partner.
    activity_type: 'API_CALL', 'TRANSACTION', 'LOGIN', 'SUPPORT_CONTACT', etc.
    """
    with get_db() as conn:
        conn.execute("""
            INSERT INTO partner_activity
            (partner_id, activity_type, activity_date, metric_type, metric_value, notes)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
        """, (partner_id, activity_type, metric_type, metric_value, notes))
        
        # Update last_activity timestamp on partner record
        conn.execute(
            "UPDATE partners_activated SET last_activity = CURRENT_TIMESTAMP WHERE id = ?",
            (partner_id,)
        )
        
        conn.commit()


def update_partner_milestone(partner_id: int, new_milestone: str, evidence: str = None) -> None:
    """
    Advance partner to next milestone.
    Called when detection systems identify progress.
    """
    with get_db() as conn:
        conn.execute("""
            UPDATE partners_activated 
            SET current_milestone = ?,
                milestone_reached_at = CURRENT_TIMESTAMP,
                days_in_current_milestone = 0,
                is_at_risk = 0
            WHERE id = ?
        """, (new_milestone, partner_id))
        
        # Log the milestone achievement
        conn.execute("""
            INSERT INTO activation_milestones
            (partner_id, milestone_type, milestone_name, reached_at, status, evidence)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'COMPLETED', ?)
        """, (partner_id, new_milestone, get_milestone_by_id(new_milestone).get("name", ""), evidence))
        
        conn.commit()


def mark_partner_at_risk(partner_id: int, issue_type: str, 
                        category: str, description: str, 
                        severity: str = "MEDIUM") -> None:
    """
    Log an issue that's causing activation stall.
    """
    with get_db() as conn:
        conn.execute("""
            INSERT INTO partner_issues
            (partner_id, issue_type, issue_category, description, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (partner_id, issue_type, category, description, severity))
        
        # Mark partner as at risk
        conn.execute(
            "UPDATE partners_activated SET is_at_risk = 1 WHERE id = ?",
            (partner_id,)
        )
        
        conn.commit()


def resolve_partner_issue(issue_id: int, resolution: str) -> None:
    """
    Mark an issue as resolved.
    """
    with get_db() as conn:
        conn.execute("""
            UPDATE partner_issues 
            SET resolved_at = CURRENT_TIMESTAMP,
                resolution_notes = ?
            WHERE id = ?
        """, (resolution, issue_id))
        
        conn.commit()


def log_onboarded_partner(prospect_id: int) -> int:
    """
    Register a newly signed partner to the activation tracking system.
    Returns partner_id for future reference.
    """
    with get_db() as conn:
        result = conn.execute("""
            INSERT INTO partners_activated
            (prospect_id, activation_status, current_milestone, milestone_reached_at, last_activity)
            VALUES (?, 'INTEGRATION_PENDING', 'M001', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (prospect_id,))
        
        conn.commit()
        return result.lastrowid


def get_quarterly_activation_analytics() -> dict:
    """
    Get high-level activation analytics for the quarter.
    Used for executive briefings.
    """
    with get_db() as conn:
        # Total activated partners
        total = conn.execute(
            "SELECT COUNT(*) as c FROM partners_activated"
        ).fetchone()["c"]
        
        # Breakdown by milestone
        by_milestone = conn.execute("""
            SELECT current_milestone, COUNT(*) as count
            FROM partners_activated
            GROUP BY current_milestone
            ORDER BY current_milestone
        """).fetchall()
        
        # At risk count
        at_risk_count = conn.execute(
            "SELECT COUNT(*) as c FROM partners_activated WHERE is_at_risk = 1"
        ).fetchone()["c"]
        
        # Average days from signature to M006 (healthy recurring)
        healthy = conn.execute("""
            SELECT AVG(JULIANDAY(milestone_reached_at) - JULIANDAY(signed_at)) as avg_days
            FROM partners_activated pa
            JOIN activation_milestones am ON pa.id = am.partner_id
            WHERE am.milestone_type = 'M006'
            AND am.status = 'COMPLETED'
        """).fetchone()
        
        avg_days_to_healthy = healthy["avg_days"] if healthy and healthy["avg_days"] else None
    
    return {
        "total_activated": total,
        "at_risk": at_risk_count,
        "healthy": total - at_risk_count if total > 0 else 0,
        "healthy_percentage": ((total - at_risk_count) / total * 100) if total > 0 else 0,
        "by_milestone": [
            {"milestone": dict(m)["current_milestone"], "count": dict(m)["count"]}
            for m in by_milestone
        ],
        "avg_days_to_healthy": round(avg_days_to_healthy, 1) if avg_days_to_healthy else None
    }

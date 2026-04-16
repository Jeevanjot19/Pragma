#!/usr/bin/env python3
"""
INNOVATION 1: Buyer Committee Intelligence
Tracks stakeholder engagement, sentiment, and decision authority across multi-stakeholder deals.
Identifies champions, blockers, and consensus status to improve deal outcomes.

Key Insights:
- Most B2B enterprise deals involve 5-7 decision makers
- Different roles have different concerns (CTO cares about technical, CFO cares about cost)
- Deal success depends on consensus - need champions to overcome blockers
- Engagement tracking per person reveals who's actually evaluating
"""

from datetime import datetime, timedelta
from database import get_db
from enum import Enum

class RoleType(Enum):
    CEO = "CEO"
    CTO = "CTO"
    CFO = "CFO"
    VP_PRODUCT = "VP_PRODUCT"
    VP_SALES = "VP_SALES"
    VP_FINANCE = "VP_FINANCE"
    LEGAL_COMPLIANCE = "LEGAL_COMPLIANCE"
    VP_OPERATIONS = "VP_OPERATIONS"
    SUCCESS_MANAGER = "SUCCESS_MANAGER"
    PROCUREMENT = "PROCUREMENT"

class SentimentLevel(Enum):
    EAGER = "EAGER"              # Actively pushing, wants deal
    ENGAGED = "ENGAGED"          # Interested, responsive
    NEUTRAL = "NEUTRAL"          # Neither for nor against
    SKEPTICAL = "SKEPTICAL"      # Has concerns, needs convincing
    BLOCKED = "BLOCKED"          # Against deal, will reject
    UNRESPONSIVE = "UNRESPONSIVE"  # Not engaging at all

class DecisionAuthority(Enum):
    ECONOMIC_BUYER = "ECONOMIC_BUYER"  # Has final budget authority
    TECHNICAL_BUYER = "TECHNICAL_BUYER"  # Has veto on technical fit
    USER = "USER"                        # Will use the product
    INFLUENCER = "INFLUENCER"            # Can influence but no veto
    STAKEHOLDER = "STAKEHOLDER"          # Affected but no control

# Role-to-concern mapping (what each role cares about)
ROLE_CONCERNS = {
    RoleType.CEO: {
        "concerns": ["ROI", "strategic_fit", "competitive_advantage", "risk_mitigation"],
        "key_metrics": ["revenue_impact", "partnership_visibility"],
        "decision_weight": 1.0,
        "typical_objections": ["strategic_fit", "competitive_conflict", "financial_terms"]
    },
    RoleType.CTO: {
        "concerns": ["technical_integration", "security", "api_stability", "integration_time"],
        "key_metrics": ["api_calls", "oauth_success_rate", "integration_hours_saved"],
        "decision_weight": 0.8,
        "typical_objections": ["technical_complexity", "security_concerns", "documentation", "api_design"]
    },
    RoleType.CFO: {
        "concerns": ["cost_of_integration", "procurement_terms", "payment_schedule", "cost_of_operations"],
        "key_metrics": ["total_cost_of_ownership", "payment_terms", "integration_cost"],
        "decision_weight": 0.9,
        "typical_objections": ["cost_too_high", "budget_cycle", "procurement_process", "roi_not_clear"]
    },
    RoleType.VP_PRODUCT: {
        "concerns": ["feature_fit", "product_roadmap_alignment", "differentiation", "customer_value"],
        "key_metrics": ["feature_coverage", "customer_value_increase"],
        "decision_weight": 0.7,
        "typical_objections": ["feature_gap", "roadmap_conflict", "customer_expectations"]
    },
    RoleType.VP_SALES: {
        "concerns": ["sales_enablement", "margin", "competitive_positioning", "go_to_market"],
        "key_metrics": ["deal_velocity", "sales_enablement_hours"],
        "decision_weight": 0.7,
        "typical_objections": ["margin_concern", "competitor_positioning", "customer_readiness"]
    },
    RoleType.LEGAL_COMPLIANCE: {
        "concerns": ["contract_terms", "regulatory_compliance", "liability", "data_protection"],
        "key_metrics": ["compliance_certifications", "contract_review_time"],
        "decision_weight": 0.9,
        "typical_objections": ["contract_terms", "regulatory_requirements", "liability_concerns"]
    },
    RoleType.VP_OPERATIONS: {
        "concerns": ["implementation_timeline", "support_costs", "training", "operational_burden"],
        "key_metrics": ["implementation_time", "support_cost", "training_hours"],
        "decision_weight": 0.6,
        "typical_objections": ["implementation_complexity", "support_cost_high", "training_burden"]
    }
}

# ============================================================================
# SECTION 1: Add and Track Buyer Committee Members
# ============================================================================

def add_buyer_committee_member(
    prospect_id: int = None,
    partner_id: int = None,
    name: str = None,
    title: str = None,
    role: str = None,
    email: str = None,
    decision_authority: str = None
) -> dict:
    """
    Add a stakeholder to the buyer committee for a prospect/partner.
    
    Decision Authority:
    - ECONOMIC_BUYER: Controls budget, final approval
    - TECHNICAL_BUYER: Has veto on technical implementation
    - USER: Will use the product daily
    - INFLUENCER: Can sway opinion but no veto
    - STAKEHOLDER: Affected by decision
    """
    
    if not (prospect_id or partner_id):
        return {"error": "Must specify prospect_id or partner_id"}
    
    if not role:
        return {"error": "Role is required"}
    
    # Validate role
    valid_roles = [r.value for r in RoleType]
    if role not in valid_roles:
        return {"error": f"Invalid role: {role}. Valid roles: {valid_roles}"}
    
    with get_db() as conn:
        result = conn.execute("""
            INSERT INTO buyer_committee_members
            (prospect_id, partner_id, name, title, role, email, decision_authority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (prospect_id, partner_id, name, title, role, email, decision_authority))
        
        conn.commit()
        buyer_id = result.lastrowid
    
    return {
        "buyer_id": buyer_id,
        "name": name,
        "role": role,
        "added": True
    }

def get_buyer_committee(prospect_id: int = None, partner_id: int = None) -> list:
    """Get all buyer committee members for a prospect or partner."""
    
    if not (prospect_id or partner_id):
        return {"error": "Must specify prospect_id or partner_id"}
    
    with get_db() as conn:
        if prospect_id:
            query = "SELECT * FROM buyer_committee_members WHERE prospect_id = ?"
            params = (prospect_id,)
        else:
            query = "SELECT * FROM buyer_committee_members WHERE partner_id = ?"
            params = (partner_id,)
        
        rows = conn.execute(query, params).fetchall()
        
        return [dict(row) for row in rows]

# ============================================================================
# SECTION 2: Track Stakeholder Engagement
# ============================================================================

def log_stakeholder_engagement(
    buyer_id: int,
    engagement_type: str,
    detail: str = None,
    sentiment_detected: str = None,
    **kwargs
) -> dict:
    """
    Log an engagement event for a stakeholder.
    
    Engagement types:
    - EMAIL_SENT: Track email sent to stakeholder
    - EMAIL_OPENED: Track email opened
    - EMAIL_CLICKED: Track link clicked in email
    - CALL: Phone call with stakeholder
    - DEMO: Product demo attended
    - MEETING: Meeting occurred
    - CONTENT_VIEW: Downloaded resource
    - PROPOSAL_SENT: Proposal shared
    - CONTRACT_SENT: Contract shared
    """
    
    engagement_type_valid = [
        "EMAIL_SENT", "EMAIL_OPENED", "EMAIL_CLICKED", "CALL", "DEMO",
        "MEETING", "CONTENT_VIEW", "PROPOSAL_SENT", "CONTRACT_SENT"
    ]
    
    if engagement_type not in engagement_type_valid:
        return {"error": f"Invalid engagement type: {engagement_type}"}
    
    with get_db() as conn:
        # Log the engagement
        email_id = kwargs.get("email_id")
        call_duration = kwargs.get("call_duration_seconds")
        demo_duration = kwargs.get("demo_duration_seconds")
        
        conn.execute("""
            INSERT INTO stakeholder_engagement
            (buyer_id, engagement_type, detail, email_id, call_duration_seconds, 
             demo_duration_seconds, sentiment_detected)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (buyer_id, engagement_type, detail, email_id, call_duration, demo_duration, sentiment_detected))
        
        # Update buyer committee member engagement counters
        if engagement_type == "EMAIL_OPENED":
            conn.execute(
                "UPDATE buyer_committee_members SET opened_emails = opened_emails + 1, last_engagement_at = CURRENT_TIMESTAMP WHERE id = ?",
                (buyer_id,)
            )
        elif engagement_type == "EMAIL_CLICKED":
            conn.execute(
                "UPDATE buyer_committee_members SET clicked_emails = clicked_emails + 1, last_engagement_at = CURRENT_TIMESTAMP WHERE id = ?",
                (buyer_id,)
            )
        elif engagement_type == "CALL":
            conn.execute(
                "UPDATE buyer_committee_members SET calls_attended = calls_attended + 1, last_engagement_at = CURRENT_TIMESTAMP WHERE id = ?",
                (buyer_id,)
            )
        elif engagement_type == "DEMO":
            conn.execute(
                "UPDATE buyer_committee_members SET demos_attended = demos_attended + 1, last_engagement_at = CURRENT_TIMESTAMP WHERE id = ?",
                (buyer_id,)
            )
        elif engagement_type == "CONTENT_VIEW":
            conn.execute(
                "UPDATE buyer_committee_members SET content_downloads = content_downloads + 1, last_engagement_at = CURRENT_TIMESTAMP WHERE id = ?",
                (buyer_id,)
            )
        
        conn.commit()
    
    return {
        "logged": True,
        "engagement_type": engagement_type,
        "detail": detail
    }

def get_stakeholder_engagement_history(buyer_id: int) -> list:
    """Get all engagement events for a stakeholder."""
    
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM stakeholder_engagement WHERE buyer_id = ? ORDER BY timestamp DESC",
            (buyer_id,)
        ).fetchall()
    
    return [dict(row) for row in rows]

# ============================================================================
# SECTION 3: Track Stakeholder Sentiment
# ============================================================================

def update_stakeholder_sentiment(
    buyer_id: int,
    sentiment: str,
    reason: str = None,
    concern_area: str = None
) -> dict:
    """
    Update sentiment for a stakeholder.
    
    Sentiment levels:
    - EAGER: Actively pushing for partnership
    - ENGAGED: Interested, responsive
    - NEUTRAL: No clear stance
    - SKEPTICAL: Has concerns, needs convincing
    - BLOCKED: Against deal, may reject
    - UNRESPONSIVE: Not engaging
    """
    
    valid_sentiments = [s.value for s in SentimentLevel]
    if sentiment not in valid_sentiments:
        return {"error": f"Invalid sentiment: {sentiment}"}
    
    with get_db() as conn:
        # Update buyer committee member sentiment
        conn.execute(
            "UPDATE buyer_committee_members SET sentiment = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (sentiment, buyer_id)
        )
        
        # Log sentiment change
        conn.execute("""
            INSERT INTO stakeholder_sentiment (buyer_id, sentiment_status, reason, concern_area)
            VALUES (?, ?, ?, ?)
        """, (buyer_id, sentiment, reason, concern_area))
        
        conn.commit()
    
    return {
        "buyer_id": buyer_id,
        "sentiment": sentiment,
        "reason": reason,
        "updated": True
    }

def get_stakeholder_sentiment_history(buyer_id: int) -> dict:
    """Get current and historical sentiment for a stakeholder."""
    
    with get_db() as conn:
        # Current sentiment
        current = conn.execute(
            "SELECT sentiment FROM buyer_committee_members WHERE id = ?",
            (buyer_id,)
        ).fetchone()
        
        # Sentiment history
        history = conn.execute(
            "SELECT * FROM stakeholder_sentiment WHERE buyer_id = ? ORDER BY last_updated DESC",
            (buyer_id,)
        ).fetchall()
    
    return {
        "current_sentiment": dict(current)["sentiment"] if current else None,
        "history": [dict(row) for row in history]
    }

# ============================================================================
# SECTION 4: Identify Champions and Blockers
# ============================================================================

def identify_champion(buyer_id: int, reason: str = None) -> dict:
    """Mark a stakeholder as a champion (actively pushing for deal)."""
    
    with get_db() as conn:
        conn.execute(
            "UPDATE buyer_committee_members SET is_champion = 1 WHERE id = ?",
            (buyer_id,)
        )
        
        # Also update sentiment to EAGER
        conn.execute(
            "UPDATE buyer_committee_members SET sentiment = 'EAGER' WHERE id = ?",
            (buyer_id,)
        )
        
        conn.commit()
    
    return {"champion_identified": True, "buyer_id": buyer_id, "reason": reason}

def identify_blocker(buyer_id: int, reason: str = None) -> dict:
    """Mark a stakeholder as a blocker (may reject deal)."""
    
    with get_db() as conn:
        conn.execute(
            "UPDATE buyer_committee_members SET is_blocker = 1, sentiment = 'BLOCKED' WHERE id = ?",
            (buyer_id,)
        )
        
        conn.commit()
    
    return {"blocker_identified": True, "buyer_id": buyer_id, "reason": reason}

# ============================================================================
# SECTION 5: Calculate Engagement Score
# ============================================================================

def calculate_engagement_score(buyer_id: int) -> dict:
    """
    Calculate engagement score for a buyer based on:
    - Recency of last engagement
    - Frequency of engagement
    - Types of engagement (demo > call > email_open)
    - Sentiment (EAGER +50%, BLOCKED -50%)
    """
    
    with get_db() as conn:
        buyer = conn.execute(
            "SELECT * FROM buyer_committee_members WHERE id = ?",
            (buyer_id,)
        ).fetchone()
        
        if not buyer:
            return {"error": f"Buyer {buyer_id} not found"}
        
        buyer_dict = dict(buyer)
        
        # Recency score (0-25 pts)
        last_engagement = buyer_dict.get("last_engagement_at")
        if not last_engagement:
            recency_score = 0
        else:
            last_eng_dt = datetime.fromisoformat(last_engagement)
            days_since = (datetime.utcnow() - last_eng_dt).days
            
            if days_since < 7:
                recency_score = 25
            elif days_since < 14:
                recency_score = 20
            elif days_since < 30:
                recency_score = 15
            elif days_since < 60:
                recency_score = 10
            else:
                recency_score = 0
        
        # Frequency score (0-25 pts)
        total_engagements = (
            (buyer_dict.get("opened_emails") or 0) +
            (buyer_dict.get("clicked_emails") or 0) * 1.5 +
            (buyer_dict.get("calls_attended") or 0) * 3 +
            (buyer_dict.get("demos_attended") or 0) * 4 +
            (buyer_dict.get("content_downloads") or 0) * 2
        )
        
        frequency_score = min(25, total_engagements * 2)
        
        # Sentiment multiplier (0.5x to 1.5x)
        sentiment = buyer_dict.get("sentiment", "NEUTRAL")
        sentiment_multiplier = {
            "EAGER": 1.5,
            "ENGAGED": 1.2,
            "NEUTRAL": 1.0,
            "SKEPTICAL": 0.7,
            "BLOCKED": 0.3,
            "UNRESPONSIVE": 0.0
        }.get(sentiment, 1.0)
        
        # Champion/Blocker bonus/penalty
        champion_bonus = 10 if buyer_dict.get("is_champion") else 0
        blocker_penalty = -15 if buyer_dict.get("is_blocker") else 0
        
        # Calculate total
        base_score = recency_score + frequency_score
        final_score = base_score * sentiment_multiplier + champion_bonus + blocker_penalty
        final_score = max(0, min(100, final_score))  # Clamp 0-100
        
        return {
            "buyer_id": buyer_id,
            "engagement_score": round(final_score, 1),
            "recency_score": round(recency_score, 1),
            "frequency_score": round(frequency_score, 1),
            "factors": {
                "sentiment": sentiment,
                "is_champion": bool(buyer_dict.get("is_champion")),
                "is_blocker": bool(buyer_dict.get("is_blocker")),
                "total_engagements": round(total_engagements, 1),
                "days_since_contact": (datetime.utcnow() - datetime.fromisoformat(last_engagement)).days if last_engagement else None
            }
        }

# ============================================================================
# SECTION 6: Committee Consensus Analysis
# ============================================================================

def analyze_committee_consensus(prospect_id: int = None, partner_id: int = None) -> dict:
    """
    Analyze buyer committee consensus status.
    
    Outputs:
    - Champions count (pushing for deal)
    - Blockers count (could kill deal)
    - Neutral count
    - Deal health (HEALTHY if champions outnumber blockers significantly)
    - Risk factors
    - Estimated close likelihood
    """
    
    if not (prospect_id or partner_id):
        return {"error": "Must specify prospect_id or partner_id"}
    
    with get_db() as conn:
        if prospect_id:
            committee = conn.execute(
                "SELECT * FROM buyer_committee_members WHERE prospect_id = ?",
                (prospect_id,)
            ).fetchall()
        else:
            committee = conn.execute(
                "SELECT * FROM buyer_committee_members WHERE partner_id = ?",
                (partner_id,)
            ).fetchall()
        
        if not committee:
            return {
                "committee_size": 0,
                "consensus_status": "UNKNOWN",
                "deal_health": "UNKNOWN",
                "message": "No buyer committee members tracked yet"
            }
        
        # Count sentiments
        champions = sum(1 for m in committee if dict(m).get("is_champion"))
        blockers = sum(1 for m in committee if dict(m).get("is_blocker"))
        eagers = sum(1 for m in committee if dict(m).get("sentiment") == "EAGER")
        blocked = sum(1 for m in committee if dict(m).get("sentiment") == "BLOCKED")
        responsive = sum(1 for m in committee if dict(m).get("last_engagement_at") is not None)
        
        committee_size = len(committee)
        
        # Determine consensus status and deal health
        if blockers > 0 and blockers >= champions:
            consensus_status = "BLOCKERS_PRESENT"
            deal_health = "AT_RISK"
        elif champions >= committee_size * 0.5:
            consensus_status = "STRONG_CONSENSUS"
            deal_health = "HEALTHY"
        elif responsive < committee_size * 0.5:
            consensus_status = "STALLED"
            deal_health = "STALLED"
        else:
            consensus_status = "FORMING"
            deal_health = "FORMING"
        
        # Calculate consensus score (0-100)
        if committee_size == 0:
            consensus_score = 0
        else:
            champion_weight = (champions / committee_size) * 50
            responsive_weight = (responsive / committee_size) * 40
            blocker_weight = (blockers / committee_size) * -20
            consensus_score = max(0, champion_weight + responsive_weight + blocker_weight)
        
        # Estimated close likelihood
        if deal_health == "HEALTHY":
            close_likelihood = 0.75 + (champions / max(1, committee_size)) * 0.25
        elif deal_health == "AT_RISK":
            close_likelihood = 0.2
        elif deal_health == "STALLED":
            close_likelihood = 0.35
        else:
            close_likelihood = 0.5
        
        close_likelihood = min(1.0, close_likelihood)
        
        # Identify high-authority blockers
        blockers_detail = []
        if blockers > 0:
            blocker_members = conn.execute("""
                SELECT name, role, is_economic_buyer, sentiment FROM buyer_committee_members 
                WHERE (prospect_id = ? OR partner_id = ?) AND is_blocker = 1
            """, (prospect_id, partner_id)).fetchall()
            
            blockers_detail = [dict(m) for m in blocker_members]
    
    return {
        "committee_size": committee_size,
        "champions": champions,
        "blockers": blockers,
        "neutral": committee_size - champions - blockers,
        "responsive_members": responsive,
        "consensus_status": consensus_status,
        "consensus_score": round(consensus_score, 1),
        "deal_health": deal_health,
        "estimated_close_likelihood": round(close_likelihood, 2),
        "risk_factors": blockers_detail if blockers_detail else [],
        "recommendations": _generate_consensus_recommendations(
            committee_size, champions, blockers, responsive, deal_health
        )
    }

def _generate_consensus_recommendations(committee_size, champions, blockers, responsive, deal_health):
    """Generate actionable recommendations based on committee status."""
    
    recommendations = []
    
    if blockers > 0:
        if blockers == 1:
            recommendations.append("URGENT: One high-influence blocker can kill deal. Schedule 1-on-1 discussion to understand concerns.")
        else:
            recommendations.append(f"ALERT: {blockers} blockers present. Identify and address each concern separately.")
    
    if responsive < committee_size * 0.5:
        recommendations.append(f"Only {responsive}/{committee_size} committee members engaged. Reach out to silent members to assess status.")
    
    if champions == 0:
        recommendations.append("No identified champions yet. In discovery call, understand who's most excited and cultivate as internal champion.")
    elif champions < committee_size * 0.33:
        recommendations.append("Weak champion support. Strengthen champion's credibility with peer stakeholders through group demo or success story.")
    
    if deal_health == "STALLED":
        recommendations.append("Committee feedback stalled. Send simple 'checking in' email to gauge current status without pressure.")
    
    return recommendations

# ============================================================================
# SECTION 7: Committee Status Report
# ============================================================================

def get_committee_status_report(prospect_id: int = None, partner_id: int = None) -> dict:
    """
    Generate comprehensive buyer committee status report.
    Shows engagement, sentiment, and consensus for sales team.
    """
    
    if not (prospect_id or partner_id):
        return {"error": "Must specify prospect_id or partner_id"}
    
    with get_db() as conn:
        if prospect_id:
            committee = conn.execute(
                "SELECT * FROM buyer_committee_members WHERE prospect_id = ? ORDER BY engagement_level DESC, sentiment DESC",
                (prospect_id,)
            ).fetchall()
        else:
            committee = conn.execute(
                "SELECT * FROM buyer_committee_members WHERE partner_id = ? ORDER BY engagement_level DESC, sentiment DESC",
                (partner_id,)
            ).fetchall()
    
    committee_members = []
    for member in committee:
        member_dict = dict(member)
        engagement_score = calculate_engagement_score(member_dict["id"])
        
        committee_members.append({
            "id": member_dict["id"],
            "name": member_dict["name"],
            "role": member_dict["role"],
            "title": member_dict["title"],
            "sentiment": member_dict["sentiment"],
            "engagement_score": engagement_score.get("engagement_score", 0),
            "is_champion": bool(member_dict["is_champion"]),
            "is_blocker": bool(member_dict["is_blocker"]),
            "is_economic_buyer": bool(member_dict["is_economic_buyer"]),
            "last_engagement": member_dict["last_engagement_at"],
            "total_engagements": (
                (member_dict.get("opened_emails") or 0) +
                (member_dict.get("clicked_emails") or 0) +
                (member_dict.get("calls_attended") or 0) +
                (member_dict.get("demos_attended") or 0)
            )
        })
    
    # Get consensus
    consensus = analyze_committee_consensus(prospect_id=prospect_id, partner_id=partner_id)
    
    return {
        "committee": committee_members,
        "consensus": consensus,
        "generated_at": datetime.utcnow().isoformat()
    }

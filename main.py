from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, remove_non_prospects, get_monitoring_events
from discovery.news_monitor import run_news_monitor
from discovery.play_store import discover_from_play_store
from discovery.company_monitor import run_full_monitoring
from signals.scorer import recalculate_all_scores
from signals.timing import calculate_when_score, get_all_when_scores, get_weekly_priorities
from outreach.generator import generate_outreach_package
from database import get_db
from pydantic import BaseModel
from typing import Optional

# ============================================================================
# Pydantic Models for API Request Bodies
# ============================================================================

class ApiCallLog(BaseModel):
    """Webhook payload for logging partner API calls."""
    partner_id: int
    environment: str
    endpoint: str
    method: str
    status_code: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None
    api_key_id: Optional[str] = None

class StallPatternPayload(BaseModel):
    """Payload for marking stall patterns."""
    pattern: str
    resolution: Optional[str] = None

app = FastAPI(title="Pragma — Blostem GTM Intelligence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()
    print("Pragma is running.")

@app.get("/")
def root():
    return {"status": "Pragma WHO layer running"}

@app.post("/api/discover")
def trigger_discovery():
    news_result = run_news_monitor()
    remove_non_prospects()
    
    # Enrich known prospects with Play Store data
    from discovery.play_store import enrich_all_prospects
    enrich_all_prospects()
    
    recalculate_all_scores()
    return {"status": "complete", **news_result}

@app.get("/api/prospects")
def get_prospects(status: str = None, limit: int = 50):
    """Get all prospects, optionally filtered by status."""
    with get_db() as conn:
        if status:
            rows = conn.execute(
                """SELECT p.*, 
                   COUNT(s.id) as signal_count
                   FROM prospects p
                   LEFT JOIN signals s ON s.prospect_id = p.id
                   WHERE p.status = ? AND p.is_existing_partner = 0
                   GROUP BY p.id
                   ORDER BY p.who_score DESC
                   LIMIT ?""",
                (status.upper(), limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT p.*,
                   COUNT(s.id) as signal_count
                   FROM prospects p
                   LEFT JOIN signals s ON s.prospect_id = p.id
                   WHERE p.is_existing_partner = 0
                   GROUP BY p.id
                   ORDER BY p.who_score DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()
    
    return [dict(r) for r in rows]

@app.get("/api/prospects/{prospect_id}")
def get_prospect_detail(prospect_id: int):
    """Get full detail for one prospect including all signals."""
    with get_db() as conn:
        prospect = conn.execute(
            "SELECT * FROM prospects WHERE id = ?", (prospect_id,)
        ).fetchone()
        
        signals = conn.execute(
            """SELECT * FROM signals 
               WHERE prospect_id = ? 
               ORDER BY detected_at DESC""",
            (prospect_id,)
        ).fetchall()
    
    if not prospect:
        return {"error": "Not found"}
    
    return {
        "prospect": dict(prospect),
        "signals": [dict(s) for s in signals]
    }

@app.get("/api/stats")
def get_stats():
    """Dashboard stats for WHO layer."""
    with get_db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) as c FROM prospects WHERE is_existing_partner = 0"
        ).fetchone()['c']
        
        hot = conn.execute(
            "SELECT COUNT(*) as c FROM prospects WHERE status = 'HOT'"
        ).fetchone()['c']
        
        warm = conn.execute(
            "SELECT COUNT(*) as c FROM prospects WHERE status = 'WARM'"
        ).fetchone()['c']
        
        displacement = conn.execute(
            "SELECT COUNT(*) as c FROM prospects WHERE using_competitor IS NOT NULL"
        ).fetchone()['c']
        
        by_product = conn.execute(
            """SELECT recommended_product, COUNT(*) as count 
               FROM prospects 
               WHERE is_existing_partner = 0
               GROUP BY recommended_product"""
        ).fetchall()
    
    return {
        "total_prospects": total,
        "hot": hot,
        "warm": warm,
        "displacement_targets": displacement,
        "by_recommended_product": [dict(r) for r in by_product]
    }

@app.post("/api/reset")
def reset_discovery():
    """Clear processed articles so next discovery run is fresh."""
    with get_db() as conn:
        conn.execute("DELETE FROM processed_articles")
        conn.commit()
    return {"status": "reset complete — next discover will reprocess all articles"}

@app.post("/api/monitor/run")
def trigger_monitoring():
    """Run monitoring cycle on all in-universe prospects."""
    result = run_full_monitoring()
    return {
        "status": "monitoring complete",
        **result
    }

@app.get("/api/prospects/{prospect_id}/events")
def get_prospect_monitoring_events(prospect_id: int, days: int = 7):
    """Get recent monitoring events for a prospect."""
    with get_db() as conn:
        prospect = conn.execute(
            "SELECT * FROM prospects WHERE id = ?", (prospect_id,)
        ).fetchone()
        
        if not prospect:
            return {"error": "Prospect not found"}
        
        events = conn.execute("""
            SELECT * FROM monitoring_events 
            WHERE prospect_id = ? 
            AND datetime(detected_at) >= datetime('now', '-' || ? || ' days')
            ORDER BY detected_at DESC
        """, (prospect_id, days)).fetchall()
    
    return {
        "prospect": dict(prospect),
        "monitoring_events": [dict(e) for e in events],
        "event_count": len(events) if events else 0
    }

@app.get("/api/monitoring/summary")
def get_monitoring_summary():
    """Get summary of all monitoring events from last 7 days."""
    with get_db() as conn:
        events = conn.execute("""
            SELECT 
                event_type,
                urgency,
                COUNT(*) as count
            FROM monitoring_events
            WHERE datetime(detected_at) >= datetime('now', '-7 days')
            GROUP BY event_type, urgency
            ORDER BY count DESC
        """).fetchall()
        
        recent_by_prospect = conn.execute("""
            SELECT 
                p.name,
                p.who_score,
                COUNT(me.id) as event_count,
                MAX(me.detected_at) as last_event
            FROM prospects p
            LEFT JOIN monitoring_events me ON p.id = me.prospect_id
            AND datetime(me.detected_at) >= datetime('now', '-7 days')
            WHERE me.id IS NOT NULL
            GROUP BY p.id
            ORDER BY event_count DESC
        """).fetchall()
    
    return {
        "events_by_type": [dict(e) for e in events],
        "prospects_with_recent_events": [dict(p) for p in recent_by_prospect],
        "summary": f"{len(recent_by_prospect)} prospects had monitoring events in last 7 days"
    }


# ============================================================================
# WHEN LAYER — Temporal Scoring Endpoints
# ============================================================================

@app.get("/api/when/priorities")
def get_when_priorities():
    """
    Get weekly priority list: Monday morning briefing with action items.
    Categorizes prospects by engagement level:
    - CALL THIS WEEK: >65 score + recent event signal
    - EMAIL THIS WEEK: 50-65 score + recent event signal
    - SEND INTRO EMAIL: 50+ score, no recent event yet
    - NURTURE: 30-50 score, early stage
    - MONITOR: <30 score, keep watching
    """
    return get_weekly_priorities()


@app.get("/api/when/scores")
def get_when_scores():
    """Get WHEN scores for all HOT+WARM prospects. Sorted by when_score DESC."""
    return {"scores": get_all_when_scores()}


@app.get("/api/when/{prospect_id}")
def get_prospect_when(prospect_id: int):
    """
    Get detailed WHEN score for one prospect.
    Shows:
    - when_score: temporal priority (0-100)
    - action: recommended next step
    - best_recent_event: what triggered the timing signal
    - score_breakdown: components (scale + maturity + event_boost + recency)
    """
    return calculate_when_score(prospect_id)


# ============================================================================
# HOW LAYER — Outreach Package Generation
# ============================================================================

@app.post("/api/how/generate/{prospect_id}")
def generate_outreach(prospect_id: int):
    """
    Generate complete outreach package for one prospect.
    Includes 3 persona-specific emails (CTO, CPO, CFO) + compliance checks.
    Uses 3 LLM calls — run this deliberately, not for all prospects at once.
    
    Returns:
    - Recommended contact sequence
    - Email for each persona (subject, body, compliance status)
    - Overall compliance summary
    - Why now (event trigger)
    """
    package = generate_outreach_package(prospect_id)
    if not package:
        return {"error": "Prospect not found"}
    return package


@app.get("/api/how/packages")
def list_packages():
    """
    List all previously generated packages.
    Currently a placeholder — in production would store packages in database.
    """
    return {
        "message": "Generate packages via POST /api/how/generate/{prospect_id}",
        "example": "POST /api/how/generate/4 to generate for Kreditbee"
    }


# ============================================================================
# FEEDBACK LOOP INTEGRATION — Issue 1 Fix
# Mark interactions so WHEN layer doesn't re-contact same prospect
# ============================================================================

@app.post("/api/prospects/{prospect_id}/mark-contacted")
def mark_prospect_contacted(prospect_id: int, interaction_type: str = "EMAIL", 
                            email_persona: str = None, subject_line: str = None):
    """
    Record outreach interaction for a prospect.
    ISSUE 1 FIX: Creates feedback loop so WHEN layer reduces re-engagement urgency.
    
    interaction_type: 'EMAIL', 'CALL', 'MEETING', 'RESPONSE_RECEIVED', etc.
    email_persona: 'CTO', 'CPO', 'CFO' if email-based
    
    After logging, WHEN score will apply contact_factor (0.5x-1.0x based on days_since_contact).
    """
    with get_db() as conn:
        prospect = conn.execute(
            "SELECT * FROM prospects WHERE id = ?", (prospect_id,)
        ).fetchone()
        
        if not prospect:
            return {"error": "Prospect not found"}
        
        conn.execute("""
            INSERT INTO prospect_interactions
            (prospect_id, interaction_type, email_persona, subject_line, sent_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (prospect_id, interaction_type, email_persona, subject_line))
        
        conn.commit()
        
        # Recalculate WHEN score with new contact history
        new_when = calculate_when_score(prospect_id)
    
    return {
        "status": "interaction recorded",
        "prospect": dict(prospect),
        "interaction_type": interaction_type,
        "new_when_score": new_when['when_score'],
        "new_action": new_when['action'],
        "contact_factor_applied": new_when['contact_factor'],
        "message": f"Contact recorded. WHEN action reduced to {new_when['action']} due to recent outreach."
    }


@app.get("/api/prospects/{prospect_id}/interaction-history")
def get_prospect_interaction_history(prospect_id: int):
    """
    Get full interaction history for a prospect.
    Shows all emails sent, calls logged, responses tracked.
    Used by sales team to see engagement timeline.
    """
    with get_db() as conn:
        prospect = conn.execute(
            "SELECT * FROM prospects WHERE id = ?", (prospect_id,)
        ).fetchone()
        
        if not prospect:
            return {"error": "Prospect not found"}
        
        interactions = conn.execute("""
            SELECT * FROM prospect_interactions 
            WHERE prospect_id = ? 
            ORDER BY sent_at DESC
        """, (prospect_id,)).fetchall()
        
        # Calculate days since last contact
        last_contact = None
        days_since = None
        if interactions:
            from datetime import datetime
            last_interaction = interactions[0]
            last_sent = datetime.fromisoformat(last_interaction['sent_at'])
            days_since = (datetime.now() - last_sent).days
            last_contact = last_interaction['sent_at']
    
    return {
        "prospect": dict(prospect),
        "interaction_count": len(interactions) if interactions else 0,
        "last_contact": last_contact,
        "days_since_last_contact": days_since,
        "interactions": [dict(i) for i in interactions]
    }


@app.post("/api/prospects/{prospect_id}/mark-response")
def mark_prospect_response(prospect_id: int, response_type: str = "OPENED"):
    """
    Log a response/engagement from the prospect.
    response_type: 'OPENED', 'CLICKED', 'REPLIED', 'SCHEDULED_CALL', 'MET', etc.
    
    Used to track two-way engagement and improve future timing.
    """
    with get_db() as conn:
        # Find the most recent interaction
        recent = conn.execute("""
            SELECT id FROM prospect_interactions 
            WHERE prospect_id = ? 
            ORDER BY sent_at DESC LIMIT 1
        """, (prospect_id,)).fetchone()
        
        if not recent:
            return {"error": "No prior interaction found for this prospect"}
        
        conn.execute("""
            UPDATE prospect_interactions 
            SET response_received = 1,
                response_type = ?,
                response_date = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (response_type, recent['id']))
        
        conn.commit()
    
    return {
        "status": "response recorded",
        "prospect_id": prospect_id,
        "response_type": response_type
    }


# ============================================================================
# ACTIVATE LAYER (REDESIGNED) — API-Based Stall Detection & Interventions
# Three real stall patterns using actual API call data from Blostem's API
# ============================================================================

@app.post("/api/activate/api-call/log")
def log_api_call(api_call: ApiCallLog):
    """
    Log an API call made by a partner to Blostem's API.
    Called by Blostem's API gateway whenever a partner makes a request.
    
    This creates the foundation for pattern detection:
    - Pattern 1: Dead on Arrival (0 calls in 14 days)
    - Pattern 2: Stuck in Sandbox (calls then 7+ day silence)
    - Pattern 3: Sandbox Works, Production Stalled (successful sandbox, no prod)
    """
    with get_db() as conn:
        conn.execute("""
            INSERT INTO partner_api_calls 
            (partner_id, environment, endpoint, method, status_code, error_code, 
             error_message, response_time_ms, api_key_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (api_call.partner_id, api_call.environment, api_call.endpoint, 
              api_call.method, api_call.status_code, api_call.error_code,
              api_call.error_message, api_call.response_time_ms, api_call.api_key_id))
        
        conn.commit()
    
    return {
        "status": "api_call_logged",
        "partner_id": api_call.partner_id,
        "environment": api_call.environment,
        "endpoint": api_call.endpoint,
        "response_time_ms": api_call.response_time_ms
    }


@app.get("/api/activate/patterns/{partner_id}")
def detect_activation_patterns(partner_id: int):
    """
    Detect activation stall patterns for a partner based on API call data.
    Checks 3 patterns:
    
    1. DEAD_ON_ARRIVAL: 0 API calls in 14 days after signing
       → Likely cause: Person who signed isnt the person who integrates
       → Intervention: Email to CTO with getting-started guide + 30-min engineering call
    
    2. STUCK_IN_SANDBOX: Sandbox API calls then 7+ day silence
       → Likely cause: Technical blocker (auth, missing field, rate limit, etc)
       → Intervention: Auto-detect last error code, generate debugging email
    
    3. PRODUCTION_BLOCKED: Successful sandbox tests but no production calls in 14+ days
       → Likely cause: Internal approval/procurement blocker
       → Intervention: Email to business contact (not engineering)
    """
    from intelligence.activation_patterns import detect_all_stalls, detect_political_risks
    
    stall_detection = detect_all_stalls(partner_id)
    political_risks = detect_political_risks(partner_id)
    
    return {
        "partner_id": partner_id,
        "stall_detected": stall_detection.get("detected", False),
        "stall_pattern": stall_detection.get("pattern"),
        "stall_details": stall_detection,
        "political_risks": political_risks,
        "requires_intervention": bool(stall_detection.get("detected")) or bool(political_risks)
    }


@app.post("/api/activate/patterns/{partner_id}/generate-intervention")
def generate_intervention_email(partner_id: int):
    """
    Generate a targeted intervention email based on detected stall pattern.
    
    Returns appropriate email template + contact availability info:
    - DEAD_ON_ARRIVAL: Engineering getting-started guide (target: CTO)
    - STUCK_IN_SANDBOX: Debug-specific email (target: CTO) with error code context
    - PRODUCTION_BLOCKED: Business blocker discussion (target: business contact)
    
    Also checks if we have contact info for the target persona.
    No LLM — rule-based templates tailored to each pattern.
    """
    from intelligence.activation_patterns import detect_all_stalls
    from intelligence.activation_interventions import (
        generate_dead_on_arrival_email,
        generate_stuck_in_sandbox_email,
        generate_production_blocked_email
    )
    from intelligence.contact_manager import check_contact_available
    
    stall_data = detect_all_stalls(partner_id)
    
    if not stall_data.get("detected"):
        return {"error": "No stall pattern detected for this partner"}
    
    pattern = stall_data.get("pattern")
    
    if pattern == "DEAD_ON_ARRIVAL":
        email = generate_dead_on_arrival_email(partner_id)
    elif pattern == "STUCK_IN_SANDBOX":
        email = generate_stuck_in_sandbox_email(partner_id, stall_data)
    elif pattern == "PRODUCTION_BLOCKED":
        email = generate_production_blocked_email(partner_id, stall_data)
    else:
        return {"error": "Unknown stall pattern"}
    
    # Check contact availability for target persona
    target_persona = email.get("target_persona")
    contact_info = check_contact_available(partner_id, target_persona)
    
    return {
        "partner_id": partner_id,
        "stall_pattern": pattern,
        "intervention": email,
        "contact_info": contact_info,
        "action_required": True,
        "next_step": f"Send email to {contact_info['email']}" if contact_info['has_contact'] else "Obtain contact info before sending"
    }


@app.get("/api/activate/patterns/all/summary")
def get_all_stall_patterns():
    """
    Get summary of all partners with detected stall patterns.
    Shows:
    - Count by pattern (Dead on Arrival, Stuck in Sandbox, Production Blocked)
    - Partners requiring urgent intervention
    - Political risks detected
    - Intervention success metrics
    """
    from intelligence.contact_manager import get_intervention_metrics
    from datetime import datetime
    
    with get_db() as conn:
        # Get stalls by pattern
        stalls_by_pattern = conn.execute("""
            SELECT stall_pattern, COUNT(*) as count
            FROM partner_activation_stalls
            WHERE issue_resolved = 0
            GROUP BY stall_pattern
        """).fetchall()
        
        # Get partners with political risks
        political_risks = conn.execute("""
            SELECT risk_type, COUNT(*) as count
            FROM partner_political_risks
            WHERE alert_sent = 0
            GROUP BY risk_type
        """).fetchall()
        
        # Get recently detected stalls WITH days_of_inactivity calculated
        recent_stalls = conn.execute("""
            SELECT pa.id, p.name, pas.stall_pattern, pas.detected_at, pas.days_of_inactivity,
                   CAST((julianday('now') - julianday(pas.detected_at)) AS INTEGER) as days_since_detection
            FROM partner_activation_stalls pas
            JOIN partners_activated pa ON pas.partner_id = pa.id
            JOIN prospects p ON pa.prospect_id = p.id
            WHERE pas.issue_resolved = 0
            ORDER BY pas.detected_at DESC
            LIMIT 20
        """).fetchall()
    
    # Get intervention effectiveness metrics
    metrics = get_intervention_metrics()
    
    return {
        "stalls_by_pattern": [dict(r) for r in stalls_by_pattern],
        "political_risks_by_type": [dict(r) for r in political_risks],
        "recent_stalls": [dict(r) for r in recent_stalls],
        "intervention_metrics": metrics,
        "requires_urgent_action": bool(stalls_by_pattern),
        "message": "Dashboard for marketing team - shows stalls + intervention effectiveness"
    }


@app.post("/api/activate/patterns/{partner_id}/mark-intervention-sent")
def mark_intervention_sent(partner_id: int, payload: StallPatternPayload):
    """
    Record that an intervention email was sent for a detected stall pattern.
    Updates partner_activation_stalls table.
    """
    with get_db() as conn:
        conn.execute("""
            UPDATE partner_activation_stalls
            SET intervention_email_sent = 1,
                intervention_sent_at = CURRENT_TIMESTAMP
            WHERE partner_id = ? AND stall_pattern = ? AND issue_resolved = 0
        """, (partner_id, payload.pattern))
        
        conn.commit()
    
    return {
        "status": "intervention_marked_sent",
        "partner_id": partner_id,
        "pattern": payload.pattern
    }


@app.post("/api/activate/patterns/{partner_id}/mark-resolved")
def mark_stall_resolved(partner_id: int, payload: StallPatternPayload):
    """
    Mark a stall pattern as resolved when partner makes progress.
    For example:
    - DEAD_ON_ARRIVAL → resolved when first API call made
    - STUCK_IN_SANDBOX → resolved when API calls resume
    - PRODUCTION_BLOCKED → resolved when production calls start
    """
    with get_db() as conn:
        conn.execute("""
            UPDATE partner_activation_stalls
            SET issue_resolved = 1,
                resolved_at = CURRENT_TIMESTAMP
            WHERE partner_id = ? AND stall_pattern = ? 
        """, (partner_id, payload.pattern))
        
        conn.commit()
    
    return {
        "status": "stall_resolved",
        "partner_id": partner_id,
        "pattern": payload.pattern,
        "resolution": payload.resolution
    }


@app.get("/api/activate/political-risks/{partner_id}")
def get_political_risks(partner_id: int):
    """
    Get detected political/build-vs-buy risks for a partner.
    Risks detected from news monitoring:
    - COMPETITOR_INTEGRATION: Partner mentioned integrating with competitor
    - BUILD_VS_BUY_RISK: Partner posted job for banking API engineer
    
    These are internal alerts (not for partner) to account team.
    """
    with get_db() as conn:
        risks = conn.execute("""
            SELECT * FROM partner_political_risks
            WHERE partner_id = ?
            ORDER BY detected_at DESC
        """, (partner_id,)).fetchall()
    
    return {
        "partner_id": partner_id,
        "political_risks": [dict(r) for r in risks],
        "requires_account_manager_review": bool(risks),
        "message": "These are internal intelligence alerts. Consider proactive partnership conversation."
    }


@app.post("/api/activate/political-risks/{partner_id}/alert-sent")
def mark_political_risk_alert_sent(partner_id: int):
    """
    Mark that political risk alerts have been sent to account team.
    """
    with get_db() as conn:
        conn.execute("""
            UPDATE partner_political_risks
            SET alert_sent = 1
            WHERE partner_id = ? AND alert_sent = 0
        """, (partner_id,))
        
        conn.commit()
    
    return {
        "status": "political_risk_alerts_marked_sent",
        "partner_id": partner_id
    }


# ===========================
# Contact Management Endpoints
# ===========================

class AddContactPayload(BaseModel):
    name: str
    email: str
    persona: str  # CTO, Business Contact, CFO, CPO, CEO
    added_by: str = "system"


@app.post("/api/activate/partners/{partner_id}/contacts")
def add_partner_contact(partner_id: int, payload: AddContactPayload):
    """
    Add a known contact for a partner by persona type.
    Used to track who we can reach for interventions.
    
    Personas: CTO, Business Contact, CFO, CPO, CEO
    """
    from intelligence.contact_manager import add_partner_contact
    
    try:
        contact_id = add_partner_contact(
            partner_id,
            payload.name,
            payload.email,
            payload.persona,
            payload.added_by
        )
        return {
            "status": "contact_added",
            "contact_id": contact_id,
            "partner_id": partner_id,
            "persona": payload.persona,
            "email": payload.email
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/activate/partners/{partner_id}/contacts")
def list_partner_contacts(partner_id: int):
    """
    Get all known contacts for a partner, grouped by persona.
    """
    from intelligence.contact_manager import get_contacts_for_partner
    
    contacts = get_contacts_for_partner(partner_id)
    
    return {
        "partner_id": partner_id,
        "contacts": contacts,
        "contact_count": sum(len(c) for c in contacts.values()),
        "message": "Use these contacts to target interventions by persona"
    }


# ================================
# Intervention Outcome Endpoints
# ================================

class RecordOutcomePayload(BaseModel):
    stall_pattern: str  # DEAD_ON_ARRIVAL, STUCK_IN_SANDBOX, PRODUCTION_BLOCKED
    outcome: str  # responded, resolved, no_response, bounced, sent
    sent_to_email: Optional[str] = None
    notes: Optional[str] = None


@app.post("/api/activate/partners/{partner_id}/intervention-outcome")
def record_intervention_outcome(partner_id: int, payload: RecordOutcomePayload):
    """
    Record the outcome of an intervention (email sent, response, resolution, etc).
    Tracks: responded, resolved, no_response, bounced, sent
    
    Used to measure intervention effectiveness by pattern.
    """
    from intelligence.contact_manager import record_intervention_outcome
    
    try:
        outcome_id = record_intervention_outcome(
            partner_id,
            payload.stall_pattern,
            payload.outcome,
            payload.notes or "",
            payload.sent_to_email
        )
        return {
            "status": "outcome_recorded",
            "outcome_id": outcome_id,
            "partner_id": partner_id,
            "stall_pattern": payload.stall_pattern,
            "outcome": payload.outcome
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/activate/interventions/metrics")
def get_intervention_metrics():
    """
    Get aggregate metrics on intervention effectiveness.
    Shows: response rate and resolution rate by stall pattern.
    """
    from intelligence.contact_manager import get_intervention_metrics
    
    metrics = get_intervention_metrics()
    
    return {
        "message": "Intervention effectiveness metrics by stall pattern",
        "metrics": metrics,
        "recommendation": "Patterns with low resolution_rate may need better email content or follow-up process"
    }


# ================================
# Revenue Proof Engine Endpoints
# ================================

@app.get("/api/activate/partners/{partner_id}/revenue-proof")
def get_revenue_proof(partner_id: int):
    """
    Calculate revenue proof for a partner.
    Shows potential annual commission based on:
    - Company size (estimated users/employees)
    - Adoption rate (% who use Blostem)
    - Average transaction value
    - Commission rate (0.5% of transaction volume)
    
    Formula: year1_commission = estimated_users × adoption_rate × avg_ticket × 0.005
    
    Example: Groww
    - 400 employees × 60% adoption × ₹5000/transaction × 0.5%
    - = 240 active users × 12 months × ₹5000 × 0.5%
    - = ₹1.44 crore in Year 1 (conservative)
    - = ₹3.6 crore in Year 2 (with 150% growth)
    
    For high-volume fintech: Can reach ₹40 crore with scaled assumptions.
    """
    from intelligence.revenue_proof import calculate_revenue_proof
    
    result = calculate_revenue_proof(partner_id)
    
    if "error" in result:
        return result
    
    return result


@app.get("/api/activate/demo/revenue-proof")
def get_demo_revenue_proof():
    """
    Get revenue proof calculation for demo (Groww example).
    Shows how ₹40 crore revenue opportunity is justified.
    """
    from intelligence.revenue_proof import get_revenue_for_demo
    
    return {
        "message": "Revenue proof calculation for demo partner (Groww)",
        "demo_data": get_revenue_for_demo(),
        "note": "Use /api/activate/partners/{partner_id}/revenue-proof for actual partner calculations"
    }


@app.post("/api/activate/demo/stalls")
def create_demo_stalls():
    """
    Create realistic demo stall records for visualization during demo.
    Shows up to 3 different stall patterns:
    1. DEAD_ON_ARRIVAL - Partner signed but never integrated
    2. STUCK_IN_SANDBOX - Partner tested but hit technical blocker
    3. PRODUCTION_BLOCKED - Sandbox works but production approval pending
    """
    with get_db() as conn:
        # First, ensure we have at least 3 activated partners to demo
        prospects = conn.execute("SELECT id FROM prospects LIMIT 3").fetchall()
        
        if not prospects:
            return {"error": "No prospects found to create demo stalls"}
        
        # Create activated partner records if they don't exist
        for p in prospects:
            conn.execute("""
                INSERT OR IGNORE INTO partners_activated 
                (prospect_id, signed_at, activation_status)
                VALUES (?, DATETIME('now', '-20 days'), 'INTEGRATION_PENDING')
            """, (p['id'],))
        conn.commit()
        
        # Get the activated partners
        partners = conn.execute("""
            SELECT pa.id, pa.prospect_id, p.name 
            FROM partners_activated pa
            JOIN prospects p ON pa.prospect_id = p.id
            LIMIT 3
        """).fetchall()
        
        demo_stalls = []
        patterns = [
            ("DEAD_ON_ARRIVAL", 7),
            ("STUCK_IN_SANDBOX", 10),
            ("PRODUCTION_BLOCKED", 15)
        ]
        
        for idx, partner in enumerate(partners):
            pattern, days_inactive = patterns[idx % len(patterns)]
            
            # Delete any existing stalls for this partner-pattern combo
            # to allow re-running the demo
            conn.execute("""
                DELETE FROM partner_activation_stalls 
                WHERE partner_id = ? AND stall_pattern = ?
            """, (partner['id'], pattern))
            
            # Create new stall
            conn.execute("""
                INSERT INTO partner_activation_stalls 
                (partner_id, stall_pattern, detected_at, days_of_inactivity, issue_resolved)
                VALUES (?, ?, DATETIME('now', '-' || ? || ' days'), ?, 0)
            """, (partner['id'], pattern, days_inactive, days_inactive))
            
            demo_stalls.append({
                "partner_id": partner['id'],
                "partner_name": partner['name'],
                "pattern": pattern,
                "days_inactive": days_inactive
            })
        
        conn.commit()
    
    return {
        "status": "demo_stalls_created",
        "stalls_created": demo_stalls,
        "count": len(demo_stalls),
        "message": f"✓ Created demo stalls for {len(demo_stalls)} partners with realistic stall patterns. Refresh the dashboard to see them."
    }

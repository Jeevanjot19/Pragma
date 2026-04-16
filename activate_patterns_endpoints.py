# ============================================================================
# ACTIVATE LAYER (REDESIGNED) — API-Based Stall Detection & Interventions
# Three real stall patterns using actual API call data from Blostem's API
# ============================================================================

@app.post("/api/activate/api-call/log")
def log_api_call(partner_id: int, environment: str, endpoint: str, method: str,
                status_code: int, error_code: str = None, error_message: str = None,
                response_time_ms: int = None, api_key_id: str = None):
    """
    Log an API call made by a partner to Blostem's API.
    Called by Blostem's API gateway whenever a partner makes a request.
    
    This creates the foundation for pattern detection:
    - Pattern 1: Dead on Arrival (0 calls in 14 days)
    - Pattern 2: Stuck in Sandbox (calls then 7+ day silence)
    - Pattern 3: Sandbox Works, Production Stalled (successful sandbox, no prod)
    """
    from intelligence.activation_patterns import log_stall_detected
    
    with get_db() as conn:
        conn.execute("""
            INSERT INTO partner_api_calls 
            (partner_id, environment, endpoint, method, status_code, error_code, 
             error_message, response_time_ms, api_key_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (partner_id, environment, endpoint, method, status_code, error_code,
              error_message, response_time_ms, api_key_id))
        
        conn.commit()
    
    return {
        "status": "api_call_logged",
        "partner_id": partner_id,
        "environment": environment,
        "endpoint": endpoint,
        "response_time_ms": response_time_ms
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
    
    Returns appropriate email template:
    - DEAD_ON_ARRIVAL: Engineering getting-started guide (target: CTO)
    - STUCK_IN_SANDBOX: Debug-specific email (target: CTO) with error code context
    - PRODUCTION_BLOCKED: Business blocker discussion (target: business contact)
    
    No LLM — rule-based templates tailored to each pattern.
    """
    from intelligence.activation_patterns import detect_all_stalls
    from intelligence.activation_interventions import (
        generate_dead_on_arrival_email,
        generate_stuck_in_sandbox_email,
        generate_production_blocked_email
    )
    
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
    
    return {
        "partner_id": partner_id,
        "stall_pattern": pattern,
        "intervention": email,
        "action_required": True
    }


@app.get("/api/activate/patterns/all/summary")
def get_all_stall_patterns():
    """
    Get summary of all partners with detected stall patterns.
    Shows:
    - Count by pattern (Dead on Arrival, Stuck in Sandbox, Production Blocked)
    - Partners requiring urgent intervention
    - Political risks detected
    """
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
        
        # Get recently detected stalls
        recent_stalls = conn.execute("""
            SELECT pa.id, p.name, pas.stall_pattern, pas.detected_at
            FROM partner_activation_stalls pas
            JOIN partners_activated pa ON pas.partner_id = pa.id
            JOIN prospects p ON pa.prospect_id = p.id
            WHERE pas.issue_resolved = 0
            ORDER BY pas.detected_at DESC
            LIMIT 20
        """).fetchall()
    
    return {
        "stalls_by_pattern": [dict(r) for r in stalls_by_pattern],
        "political_risks_by_type": [dict(r) for r in political_risks],
        "recent_stalls": [dict(r) for r in recent_stalls],
        "requires_urgent_action": bool(stalls_by_pattern)
    }


@app.post("/api/activate/patterns/{partner_id}/mark-intervention-sent")
def mark_intervention_sent(partner_id: int, pattern: str):
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
        """, (partner_id, pattern))
        
        conn.commit()
    
    return {
        "status": "intervention_marked_sent",
        "partner_id": partner_id,
        "pattern": pattern
    }


@app.post("/api/activate/patterns/{partner_id}/mark-resolved")
def mark_stall_resolved(partner_id: int, pattern: str, resolution: str = None):
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
        """, (partner_id, pattern))
        
        conn.commit()
    
    return {
        "status": "stall_resolved",
        "partner_id": partner_id,
        "pattern": pattern,
        "resolution": resolution
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

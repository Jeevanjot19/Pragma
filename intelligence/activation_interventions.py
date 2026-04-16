#!/usr/bin/env python3
"""
ACTIVATION Layer — Intervention Email Generation
Generates targeted intervention emails for each stall pattern.
No LLM needed — rule-based + simple templates.
"""

from datetime import datetime
from database import get_db
from intelligence.activation_patterns import StallPattern


def generate_dead_on_arrival_email(partner_id: int) -> dict:
    """
    Pattern 1: Dead on Arrival
    Partner never started integration.
    Email target: CTO (not the person who signed)
    Goal: Offer hands-on help to get started
    """
    with get_db() as conn:
        partner = conn.execute(
            """SELECT p.name, p.category, p.recommended_product, pa.signed_at
               FROM partners_activated pa
               JOIN prospects p ON pa.prospect_id = p.id
               WHERE pa.prospect_id = ?""",
            (partner_id,)
        ).fetchone()
    
    company = partner['name']
    product = partner['recommended_product']
    signed_date = datetime.fromisoformat(partner['signed_at'])
    days_since = (datetime.now() - signed_date).days
    
    subject = f"Getting started with {product} at {company} — 30-min setup call?"
    
    body = f"""Hi [CTO Name at {company}],

I wanted to check in on the {product} integration that {company} signed up for on {signed_date.strftime('%B %d')}.

I noticed you haven't made any sandbox API calls yet, which is totally normal — first integrations can seem overwhelming.

Here's what we typically see:
- First API call: 15 minutes (just need your API key and endpoint)
- First successful response: 30 minutes more
- Full integration: 2-4 hours

To de-risk this, I'd like to offer a 30-minute engineering pairing session. We'll:
1. Get your sandbox credentials set up (10 min)
2. Make your first successful API call together (10 min)
3. Answer any architecture questions (10 min)

You'll walk away with a working integration and no mystery. No sales pitch, just engineering help.

Available this week:
- Tuesday 2-4 PM IST
- Wednesday 10 AM-12 PM IST  
- Thursday 3-5 PM IST

Let me know what works.

Best,
[Your Name]
Blostem Engineering
"""
    
    return {
        "partner_id": partner_id,
        "pattern": StallPattern.DEAD_ON_ARRIVAL,
        "target_persona": "CTO",
        "target_note": "NOT the person who signed — the person actually integrating",
        "subject": subject,
        "body": body,
        "cta": "30-minute engineering call to get started",
        "tone": "friendly_engineering",
        "generated_at": datetime.now().isoformat()
    }


def generate_stuck_in_sandbox_email(partner_id: int, stall_data: dict) -> dict:
    """
    Pattern 2: Stuck in Sandbox
    Partner made sandbox calls but hit an error and stopped for 7+ days.
    Email target: CTO (the person making API calls)
    Goal: Unblock specific technical issue
    """
    with get_db() as conn:
        partner = conn.execute(
            """SELECT p.name, p.recommended_product
               FROM partners_activated pa
               JOIN prospects p ON pa.prospect_id = p.id
               WHERE pa.prospect_id = ?""",
            (partner_id,)
        ).fetchone()
    
    company = partner['name']
    product = partner['recommended_product']
    error_code = stall_data.get('last_error_code', 'UNKNOWN')
    last_error = stall_data.get('recent_errors', [{}])[0]
    
    # Tailor subject based on error
    error_map = {
        "AUTH_FAILED": "Auth issue with sandbox API?",
        "MISSING_FIELD": "Missing a required field?",
        "RATE_LIMIT": "Hit rate limit on sandbox?",
        "INVALID_REQUEST": "Request format issue?",
    }
    
    error_subject = error_map.get(error_code, f"Error code {error_code}")
    
    subject = f"Let's debug this {error_subject} — {company} sandbox integration"
    
    body = f"""Hi [CTO Name at {company}],

I noticed your {product} sandbox integration hit an error on {stall_data.get('last_api_call', 'recently')} and hasn't recovered.

Last error: {error_code}

**This is totally fixable.** Most sandbox blockers are one of:
- API key permission issue (2 min fix)
- Endpoint URL formatting (2 min fix)
- Missing required header (5 min fix)
- Request body structure (10 min fix)

Rather than email debugging back-and-forth, let's just jump on a 15-minute call. I can either:
1. Debug it live with you (we'll have a working call within 5 minutes)
2. Walk you through the exact fix in your code

→ Hit reply with your availability, or grab 15 min here: [calendar link]

I know these things are annoying — let's just knock it out.

Best,
[Your Name]
Blostem Engineering
"""
    
    return {
        "partner_id": partner_id,
        "pattern": StallPattern.STUCK_IN_SANDBOX,
        "target_persona": "CTO",
        "target_note": "The person making the API calls",
        "error_code": error_code,
        "subject": subject,
        "body": body,
        "cta": "15-minute debug call",
        "tone": "technical_debug",
        "generated_at": datetime.now().isoformat()
    }


def generate_production_blocked_email(partner_id: int, stall_data: dict) -> dict:
    """
    Pattern 3: Sandbox → Production Gap
    Partner successfully tested in sandbox but never moved to production.
    Email target: Business contact (not engineering)
    Goal: Unblock approval/procurement
    """
    with get_db() as conn:
        partner = conn.execute(
            """SELECT p.name, p.recommended_product, p.category
               FROM partners_activated pa
               JOIN prospects p ON pa.prospect_id = p.id
               WHERE pa.prospect_id = ?""",
            (partner_id,)
        ).fetchone()
    
    company = partner['name']
    product = partner['recommended_product']
    days = stall_data.get('days_since_signed', 0)
    
    subject = f"Unblocking {company} — {product} production launch"
    
    body = f"""Hi [Business Contact at {company}],

Your team has successfully tested {product} in sandbox for the past few weeks. Sandbox tests show 100% success.

But production hasn't been activated yet. We're at day {days} post-signature.

**Typical blockers at this stage:**
- Procurement still approving contract terms (we can adjust)
- Legal review needed (we have pre-approved docs for fintech)
- Internal stakeholder sign-off (we can present benefits)
- Data security audit (we have compliance certifications)

Rather than guess, let's just talk. What's the actual blocker?

I'll schedule a 20-minute call with whoever owns this decision:
- Product: [Your Name, Product Lead]
- Engineering: [Your Name, Tech Lead]
- Finance: [Your Name, Business Lead]

→ Pick a time: [calendar link]

If it's something we can solve, we solve it this week. If it needs time, we get aligned on next steps.

Best,
[Your Name]
Blostem Partnerships
"""
    
    return {
        "partner_id": partner_id,
        "pattern": StallPattern.PRODUCTION_BLOCKED,
        "target_persona": "Business Contact",
        "target_note": "NOT engineering — the person who can approve production launch",
        "days_pending": days,
        "subject": subject,
        "body": body,
        "cta": "20-minute blocker resolution call",
        "tone": "procurement_blocker_discussion",
        "generated_at": datetime.now().isoformat()
    }


def generate_political_risk_alert(partner_id: int, risks: list) -> dict:
    """
    Generate internal alert for political/build-vs-buy risks detected in news.
    Target: Blostem account manager (internal)
    """
    risk_summary = []
    for risk in risks:
        risk_summary.append(f"- {risk['risk_type']}: {risk['details']}")
    
    return {
        "partner_id": partner_id,
        "alert_type": "POLITICAL_RISK",
        "severity": "HIGH",
        "detected_risks": risks,
        "subject": f"Political risk alert: Possible build-vs-buy threat detected",
        "body": f"""INTERNAL ALERT: Possible build-vs-buy risk detected for partner {partner_id}.

Detected signals:
{chr(10).join(risk_summary)}

Recommended action:
1. Proactively reach out to partnership owner
2. Understand competitive landscape (are they building in-house?)
3. Consider acceleration of production launch or expanded scope
4. Document this in partnership health check

This is intelligence, not panic. But worth a conversation with the partner soon.""",
        "action_required": True,
        "generated_at": datetime.now().isoformat()
    }

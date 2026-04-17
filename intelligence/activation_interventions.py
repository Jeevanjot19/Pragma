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
    Engagement model: CSM reaches out to main contact to facilitate team support
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
    
    subject = f"Getting your team unblocked with {product} — quick support offer"
    
    body = f"""Hi there,

I wanted to reach out regarding the {product} integration {company} signed up for on {signed_date.strftime('%B %d')}.

I know sometimes getting started on integrations takes a bit of momentum. First integrations can involve a few technical steps, and it's totally normal if your engineering team needs a bit of support.

Here's what we typically see from other partners:
- First API call: 15 minutes (just need credentials and endpoint setup)
- First successful response: 30 minutes more
- Full integration: 2-4 hours

To make this smooth, we'd love to offer a 30-minute engineering support session. We can:
1. Help your engineering team get sandbox credentials set up (10 min)
2. Make the first successful API call together (10 min)
3. Answer any architecture or integration questions (10 min)

No pressure, no sales pitch—just hands-on engineering support to get you moving.

Would your team find that helpful? Available this week:
- Tuesday 2-4 PM IST
- Wednesday 10 AM-12 PM IST  
- Thursday 3-5 PM IST

Let me know what works best.

Best,
[Your Name]
Blostem Partnerships
"""
    
    return {
        "partner_id": partner_id,
        "pattern": StallPattern.DEAD_ON_ARRIVAL,
        "engagement_model": "CSM facilitates engineering support",
        "recommended_owner": "CSM",
        "owner_note": "CSM should send within 2 days - offer support to get engineering team started",
        "subject": subject,
        "body": body,
        "cta": "30-minute engineering support session",
        "tone": "collaborative_support",
        "generated_at": datetime.now().isoformat()
    }


def generate_stuck_in_sandbox_email(partner_id: int, stall_data: dict) -> dict:
    """
    Pattern 2: Stuck in Sandbox
    Partner made sandbox calls but hit a technical error and paused.
    Engagement model: CSM reaches out to main contact to offer technical support
    Goal: Help unblock the engineering team's technical issue
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
        "AUTH_FAILED": "auth issue",
        "MISSING_FIELD": "field validation issue",
        "RATE_LIMIT": "rate limiting",
        "INVALID_REQUEST": "request format issue",
    }
    
    error_subject = error_map.get(error_code, f"technical issue")
    
    subject = f"Quick technical support for {company} — {error_subject} in {product}"
    
    body = f"""Hi there,

I wanted to check in on {company}'s {product} integration. I see your team was working through sandbox testing recently and encountered a {error_subject}.

These kinds of blockers are usually pretty straightforward to resolve—we've seen similar ones dozens of times, and they typically fall into a few categories:
- API credential or permission setup (2 min fix)
- Endpoint URL formatting (2 min fix)
- Missing or incorrect request headers (5 min fix)
- Request body structure (10 min fix)

Rather than troubleshoot via email, I'd prefer to set up a quick 15-minute call with your team. We can either:
1. Debug it together live (we'll have it working within 5 minutes)
2. Walk through the exact fix needed for your setup

This would be much faster than back-and-forth email debugging.

Do you have 15 minutes this week to help get your engineering team unblocked? 
→ [calendar link for 15-min slot]

Just reply if that timing doesn't work and we'll find something.

Best,
[Your Name]
Blostem Support
"""
    
    return {
        "partner_id": partner_id,
        "pattern": StallPattern.STUCK_IN_SANDBOX,
        "engagement_model": "CSM offers technical support to partner team",
        "recommended_owner": "CSM",
        "owner_note": "CSM should send within 1 day - offer to help partner's engineering team get unblocked",
        "error_code": error_code,
        "subject": subject,
        "body": body,
        "cta": "15-minute technical support call",
        "tone": "technical_support",
        "generated_at": datetime.now().isoformat()
    }


def generate_production_blocked_email(partner_id: int, stall_data: dict) -> dict:
    """
    Pattern 3: Sandbox → Production Gap
    Partner successfully tested in sandbox but hasn't moved to production yet.
    Engagement model: Account Manager partners with contact to understand and resolve any blockers
    Goal: Understand what's needed to move forward
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
    
    subject = f"{company} — next steps with {product} production launch"
    
    body = f"""Hi there,

I wanted to check in on {company}'s {product} journey. Your team's sandbox testing looked great—full success on all integration tests.

I'm noticing the move to production hasn't happened yet. Typically at this stage, there's usually something we can help with—it might be a process question, data setup, compliance review, or something else entirely.

What I've found works best is just having a quick conversation to understand what the next step looks like from your perspective. Sometimes it's a simple question we can answer in a 15-minute call. Sometimes there's a process we can help streamline.

Would you have 20 minutes this week to chat about getting from sandbox to live? I can bring whoever would be helpful on our side depending on what you need:
- Integration questions → our engineering team
- Compliance/security questions → our compliance team
- Scope or contract questions → our partnership team

Just let me know what would be most useful, and I'll get the right person involved.

→ [calendar link for 20-min slot]

Or if you'd prefer, just reply with what the blockers are and I can work on solutions on our end.

Looking forward to getting you live.

Best,
[Your Name]
Blostem Partnerships
"""
    
    return {
        "partner_id": partner_id,
        "pattern": StallPattern.PRODUCTION_BLOCKED,
        "engagement_model": "Account Manager partners with contact to understand needs",
        "recommended_owner": "Account Manager",
        "owner_note": "Account Manager should send within 3 days - collaborative conversation to understand next steps",
        "days_pending": days,
        "subject": subject,
        "body": body,
        "cta": "20-minute conversation about production launch",
        "tone": "collaborative_partnership",
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

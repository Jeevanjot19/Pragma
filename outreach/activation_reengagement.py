"""
ACTIVATE Layer — Re-engagement Email Generation
Generates targeted re-engagement content for partners stuck in activation.
Tailored based on their current milestone and detected blockers.
"""

from database import get_db
from outreach.activation import get_activation_recommendations, get_milestone_by_id
import anthropic

def generate_reengagement_email(partner_id: int) -> dict:
    """
    Generate re-engagement email for a partner experiencing activation stall.
    Analyzes:
    - Where they're stuck (milestone)
    - Why they're stuck (detected issues)
    - Who to contact (success persona)
    What to send them (contextual email)
    """
    # Get activation context
    recommendations = get_activation_recommendations(partner_id)
    
    if "error" in recommendations:
        return {"error": recommendations["error"]}
    
    with get_db() as conn:
        partner_info = conn.execute(
            "SELECT p.name, p.category, pa.signed_at, pa.current_milestone FROM partners_activated pa "
            "JOIN prospects p ON pa.prospect_id = p.id WHERE pa.id = ?",
            (partner_id,)
        ).fetchone()
        
        if not partner_info:
            return {"error": "Partner not found"}
        
        partner_info = dict(partner_info)
    
    # Build context for LLM
    current_milestone = get_milestone_by_id(recommendations["current_milestone"])
    next_milestone = recommendations["next_milestone"]
    detected_issues = recommendations["detected_issues"]
    stall_reason = recommendations["stall_reason"]
    
    # Determine email template based on stall reason
    template = recommendations["recommended_strategy"].get("template")
    
    # Build LLM prompt
    if stall_reason == "integration_blocked":
        prompt = f"""You're generating a technical support re-engagement email for {partner_info['name']}.

Context:
- Partner signed and started integration
- They're stuck at: {current_milestone.get('name')}
- Expected to reach this in {current_milestone.get('expected_days')} days
- Detected issues: {', '.join(i.get('description') for i in detected_issues)}

Goal: Help them overcome the technical blocker and move towards {next_milestone}

Key points:
- Show empathy for technical complexity
- Offer specific hands-on support
- Provide a quick win they can accomplish this week
- Mention similar companies who solved this

Generate a warmly professional email from an engineering support perspective.
Subject line should be urgent but supportive.
Format as JSON with "subject" and "body" keys."""
    
    elif stall_reason == "business_gap":
        prompt = f"""You're generating a business value clarification email for {partner_info['name']}.

Context:
- Partner is in {partner_info['category']} industry
- They reached: {current_milestone.get('name')}
- But seem to have deprioritized integration
- Detected issues: {', '.join(i.get('description') for i in detected_issues)}

Goal: Help them see why reaching {next_milestone} matters for their business

Key points:
- Share 2-3 success stories from similar companies
- Quantify the benefit (revenue, user engagement, etc.)
- Show what's possible once they move to the next milestone
- Make it easy to say yes

Generate a product-focused email from a success manager.
Subject should emphasize business opportunity.
Format as JSON with "subject" and "body" keys."""
    
    elif stall_reason == "user_adoption":
        prompt = f"""You're generating a user adoption acceleration email for {partner_info['name']}.

Context:
- Partner has successfully integrated into production
- But users aren't adopting the feature
- They're stuck at: {current_milestone.get('name')}
- Detected issues: {', '.join(i.get('description') for i in detected_issues)}

Goal: Provide adoption playbook to move them to {next_milestone}

Key points:
- Offer in-app messaging to drive user awareness
- Share educational content for their users
- Provide adoption metrics dashboard
- Offer to do a joint customer success call

Generate a coaching email from a customer success perspective.
Subject should position this as a quick win.
Format as JSON with "subject" and "body" keys."""
    
    else:  # silent
        days_silent = (datetime.now() - datetime.fromisoformat(
            partner_info.get("signed_at", "")
        )).days if partner_info.get("signed_at") else "several"
        
        prompt = f"""You're generating a check-in re-engagement email for {partner_info['name']}.

Context:
- Partner signed {days_silent} days ago
- They're at: {current_milestone.get('name')}
- We haven't heard from them in a while
- Next milestone: {next_milestone}

Goal: Reconnect and unblock whatever's stopping them

Key points:
- Acknowledge time has passed friendly-like (no pressure)
- Ask what's in the way (integration tech vs business complexity)
- Offer different types of support (engineering, product, success)
- Make it very easy to respond

Generate a warm, low-pressure check-in email from an account manager.
Subject should be conversational.
Format as JSON with "subject" and "body" keys."""
    
    # Call LLM
    try:
        from datetime import datetime
        client = anthropic.Anthropic()
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text
        
        # Try to parse JSON response
        import json
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                email_dict = json.loads(json_str)
            else:
                email_dict = {"subject": "Re-engagement", "body": response_text}
        except json.JSONDecodeError:
            email_dict = {"subject": "Re-engagement", "body": response_text}
        
        return {
            "partner_id": partner_id,
            "partner_name": partner_info['name'],
            "current_milestone": current_milestone.get("name"),
            "next_milestone": next_milestone,
            "stall_reason": stall_reason,
            "reengage_persona": recommendations["re_engagement_persona"],
            "email": {
                "subject": email_dict.get("subject", "Let's move forward together"),
                "body": email_dict.get("body", "")
            },
            "context": {
                "template_used": template,
                "escalation_path": recommendations["escalation_path"],
                "send_urgency": recommendations["urgency"]
            }
        }
        
    except Exception as e:
        # Fallback template if LLM fails
        fallback_subjects = {
            "integration_blocked": f"⚡ We can help unblock {partner_info['name']}'s integration",
            "business_gap": f"💡 See how {partner_info['name']} unlocks new revenue",
            "user_adoption": f"🚀 Accelerate {partner_info['name']} user adoption",
            "silent": f"👋 Let's check in on {partner_info['name']}'s integration"
        }
        
        return {
            "partner_id": partner_id,
            "partner_name": partner_info['name'],
            "current_milestone": current_milestone.get("name"),
            "next_milestone": next_milestone,
            "stall_reason": stall_reason,
            "reengage_persona": recommendations["re_engagement_persona"],
            "email": {
                "subject": fallback_subjects.get(stall_reason, "Let's move forward together"),
                "body": f"""Hi {partner_info['name']} team,

We noticed you're working on integrating into {current_milestone.get('name')}.

We want to help you reach {next_milestone} — our teams have seen partners reach this stage in {current_milestone.get('expected_days')} days on average.

The main thing slowing you down: {detected_issues[0].get('description') if detected_issues else 'we're not sure'}

Let's hop on a quick call this week to unblock this. Our {recommendations["re_engagement_persona"].replace('_', ' ').lower()} team is ready to help.

Available anytime that works for you.

Best,
[Your Name]"""
            },
            "context": {
                "template_used": template,
                "escalation_path": recommendations["escalation_path"],
                "send_urgency": recommendations["urgency"],
                "error": f"LLM failed: {str(e)}, using fallback template"
            }
        }


def generate_activation_batch(batch_type: str = "at_risk") -> list:
    """
    Generate re-engagement emails for a batch of partners.
    batch_type: 'at_risk' (scored < 50), 'critical' (scored < 25), 'all_silent' (no activity > 14d)
    """
    from outreach.activation import detect_activation_stalls, calculate_activation_score
    
    # Get all partners matching criteria
    stalls = detect_activation_stalls()
    
    if batch_type == "critical":
        stalls = [s for s in stalls if s.get("severity") == "CRITICAL"]
    elif batch_type == "at_risk":
        stalls = [s for s in stalls if s.get("severity") in ["CRITICAL", "HIGH"]]
    
    emails = []
    for stall in stalls:
        email = generate_reengagement_email(stall["partner_id"])
        if "error" not in email:
            emails.append(email)
    
    return emails

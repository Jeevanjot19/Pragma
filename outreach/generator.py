"""
HOW Layer — Outreach Package Generator
Generates 3 persona-specific cold emails (CTO, CPO, CFO) with compliance checks.
Uses LLM to customize each email + rule-based compliance checking.
Total: 3-4 LLM calls per prospect.
"""

import time
from datetime import datetime
from intelligence.llm_extractor import _call_llm, _parse_json_response
from outreach.compliance_rules import check_compliance
from database import get_db
from signals.timing import calculate_when_score

PERSONA_CONTEXTS = {
    "CTO": {
        "title": "CTO / VP Engineering",
        "primary_concern": "integration complexity and engineering overhead",
        "wants": "clean API, good docs, minimal engineering lift, fast integration",
        "proof_point": "50 lines of code, live in 7 days, React/Flutter/Android/iOS SDKs",
        "fear": "another painful bank integration with compliance overhead"
    },
    "CPO": {
        "title": "Chief Product Officer / Product Head",
        "primary_concern": "time to market and user experience quality",
        "wants": "white-label UI, fast go-live, success stories from similar platforms",
        "proof_point": "MobiKwik went live in under 2 weeks. White-label, matches your brand.",
        "fear": "launching a half-baked product that damages user trust"
    },
    "CFO": {
        "title": "CFO / Finance Head",
        "primary_concern": "cost, revenue model, regulatory risk",
        "wants": "commission economics, compliance proof, DICGC insurance clarity",
        "proof_point": "Commission on every FD booked. DICGC insured up to ₹5L per depositor.",
        "fear": "regulatory exposure or unclear revenue model"
    }
}


def generate_email_for_persona(
    persona: str,
    prospect: dict,
    when_data: dict,
    best_event: dict | None
) -> dict:
    """
    Generate one email for one persona.
    Tailored to that persona's concerns and proof points.
    Returns email + compliance report.
    """

    persona_ctx = PERSONA_CONTEXTS.get(persona, PERSONA_CONTEXTS["CPO"])
    name = prospect.get('name', 'this company')
    product = prospect.get('recommended_product', 'FD SDK')
    installs = prospect.get('install_count', '')
    category = prospect.get('category', 'fintech')

    # Build event context for opening line
    event_context = ""
    if best_event:
        event_context = f"Recent signal: {best_event.get('title', '')} ({best_event.get('event_date', '')})"
    else:
        event_context = f"Product gap: {name} offers financial products but no {product}"

    prompt = f"""You are a senior B2B sales rep at Blostem — an Indian fintech infrastructure 
company backed by Zerodha's Rainmatter. Blostem provides plug-and-play APIs for Fixed Deposits,
Recurring Deposits, Credit on UPI, and Bonds. Integration in 7 days. Already live with 
MobiKwik, Upstox, Zerodha, Jupiter, and 30+ platforms.

Write a cold outreach email for the {persona_ctx['title']} at {name}.

PROSPECT CONTEXT:
- Company: {name} ({category}, {installs} installs)
- Recommended Blostem product: {product}
- {event_context}

PERSONA CONTEXT:
- Their primary concern: {persona_ctx['primary_concern']}
- What they want: {persona_ctx['wants']}
- Best proof point for them: {persona_ctx['proof_point']}
- Their biggest fear: {persona_ctx['fear']}

EMAIL REQUIREMENTS:
- Under 120 words total
- Open with the specific signal/event — NOT "I hope this finds you well"
- Make the value proposition specific to their role and concern
- One clear CTA — suggest a 20-minute call
- Sound human, direct, conversational — not corporate
- Do NOT use: "guaranteed returns", "100% safe", "RBI approved"
- Do NOT mention specific interest rate percentages

Return ONLY valid JSON:
{{
    "subject": "email subject line",
    "body": "full email body",
    "preview": "first sentence only"
}}"""

    raw = _call_llm(prompt, max_tokens=500)
    result = _parse_json_response(raw)

    if not result:
        return {"error": "Generation failed", "persona": persona}

    # Run compliance check on generated email
    body = result.get('body', '')
    compliance = check_compliance(body)

    return {
        "persona": persona,
        "persona_title": persona_ctx['title'],
        "subject": result.get('subject', ''),
        "body": body,
        "preview": result.get('preview', ''),
        "compliance": compliance
    }


def generate_outreach_package(prospect_id: int) -> dict | None:
    """
    Generate complete outreach package for one prospect.
    Includes:
    - 3 emails (CTO, CPO, CFO) customized to each persona
    - Compliance checks on each email
    - Recommended contact sequence
    
    Uses 3 LLM calls (one per persona).
    """
    with get_db() as conn:
        prospect = conn.execute(
            "SELECT * FROM prospects WHERE id = ?",
            (prospect_id,)
        ).fetchone()

    if not prospect:
        return None

    prospect = dict(prospect)
    when_data = calculate_when_score(prospect_id)
    best_event = when_data.get('best_recent_event')

    print(f"\n📧 Generating outreach package for {prospect['name']}...")

    emails = {}
    for persona in ["CPO", "CTO", "CFO"]:
        print(f"  Generating {persona} email...")
        email = generate_email_for_persona(
            persona, prospect, when_data, best_event
        )
        emails[persona] = email
        time.sleep(0.5)

    # Determine sequence recommendation based on category
    category = prospect.get('category', '')
    if category in ['payment', 'lending']:
        sequence = ["CPO", "CTO", "CFO"]
        sequence_reason = "Start with Product — they feel the competitive gap most acutely"
    elif category in ['broker', 'wealth']:
        sequence = ["CPO", "CFO", "CTO"]
        sequence_reason = "Start with Product — FD is a product decision, then validate economics"
    else:
        sequence = ["CTO", "CPO", "CFO"]
        sequence_reason = "Start with technical validation, then product fit"

    # Count compliance violations
    has_violations = any(
        e.get('compliance', {}).get('status') == 'BLOCKED'
        for e in emails.values()
    )

    return {
        "prospect_id": prospect_id,
        "prospect_name": prospect['name'],
        "recommended_product": prospect.get('recommended_product'),
        "category": category,
        "when_score": when_data.get('when_score'),
        "action": when_data.get('action'),
        "why_now": best_event.get('title') if best_event else f"Product gap: no {prospect.get('recommended_product')}",
        "emails": emails,
        "recommended_sequence": sequence,
        "sequence_reason": sequence_reason,
        "compliance_summary": {
            "all_clear": not has_violations,
            "blocked_count": sum(
                1 for e in emails.values()
                if e.get('compliance', {}).get('status') == 'BLOCKED'
            ),
            "warning_count": sum(
                1 for e in emails.values()
                if e.get('compliance', {}).get('status') == 'WARNING'
            )
        },
        "generated_at": datetime.now().isoformat()
    }

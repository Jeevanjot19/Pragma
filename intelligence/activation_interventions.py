#!/usr/bin/env python3
"""
ACTIVATION Layer — Intervention Email Generation
Generates targeted intervention emails for each stall pattern.
No LLM needed — rule-based + simple templates.
"""

import logging
from datetime import datetime
from database import get_db
from intelligence.activation_patterns import StallPattern

logger = logging.getLogger(__name__)


def generate_dead_on_arrival_email(partner_id: int) -> dict:
    """
    Pattern 1: Dead on Arrival - Never started integration
    Engagement: CSM provides hands-on onboarding support to get engineering team unblocked
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
    category = partner['category']
    signed_date = datetime.fromisoformat(partner['signed_at'])
    days_since = (datetime.now() - signed_date).days
    
    subject = f"{company} integration ready — hands-on onboarding support available"
    
    body = f"""Hi {company} team,

I wanted to help you get started with {product}. I see your team signed up recently, and I'm here to help support your integration.

**Why This Matters**
Integrating {product} helps your {category} business with:
- Real-time compliance data for regulatory reporting
- Reduced fraud detection latency (60-70% improvement typical)
- Elimination of manual data pipeline maintenance
- Direct access to fintech APIs without custom connectors

Most {category} companies complete this integration in 2-4 hours with our support.

**How We Help**
I can support your engineering team through:
- Architecture review and setup guidance
- Step-by-step integration walkthrough
- SDK and credential setup assistance
- Sandbox testing and validation
- Production launch support

**Your Options**
We offer three engagement approaches—pick what works for {company}:

1. **Live Onboarding** (2-3 hours this week)
Screen share with your team, I walk through the entire integration, you deploy same day.
→ Schedule: [calendar link]

2. **Self-Service + Support**
Your team uses our docs, I answer questions in real-time via Slack/email.
→ Access docs: [link]

3. **Hybrid** (1 architectural call + async support)
One 1-hour call to cover design, then I support async questions.
→ Schedule: [calendar link]

I'm confident we can get {company} live quickly. We've successfully supported hundreds of {category} companies through exactly this integration.

Would you like to get started this week? I'm available and ready to help.

Best regards,

[Your Name]
Customer Success Manager
Blostem"""
    
    return {
        "partner_id": partner_id,
        "pattern": StallPattern.DEAD_ON_ARRIVAL,
        "engagement_model": "CSM provides hands-on onboarding",
        "recommended_owner": "CSM",
        "subject": subject,
        "body": body,
        "cta": "Schedule integration onboarding session",
        "tone": "supportive_enablement",
        "generated_at": datetime.now().isoformat()
    }


def generate_stuck_in_sandbox_email(partner_id: int, stall_data: dict) -> dict:
    """
    Pattern 2: Stuck in Sandbox - Technical blocker preventing progress
    Engagement: Technical support + architectural guidance
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
    category = partner['category']
    error_code = stall_data.get('last_error_code', 'UNKNOWN')
    
    error_details = {
        "AUTH_FAILED": "authentication/authorization error (invalid API key or insufficient permissions)",
        "MISSING_FIELD": "missing field in request payload",
        "RATE_LIMIT": "API rate limiting (hitting quota thresholds)",
        "INVALID_REQUEST": "malformed request (wrong format or structure)",
        "TIMEOUT": "request timeout (taking too long to respond)",
        "VERSION_MISMATCH": "API version mismatch between client and server"
    }
    
    error_desc = error_details.get(error_code, "technical integration issue")
    subject = f"{company} — {product} sandbox debugging support"
    
    body = f"""Hi {company} Engineering Team,

I noticed your {product} integration hit a technical blocker in sandbox testing ({error_code}). The good news: this type of issue is usually a quick fix (typically 5-15 minutes) once we identify it together.

**What We're Seeing**
- Error code: {error_code}
- Status: Sandbox integration started, but blocked
- Pattern: {error_desc}

**Common Causes & Fixes**
These errors typically fall into 4 categories:

1. **Credentials/Auth** (2 min fix)
   API key not properly configured or permissions too narrow

2. **Request Format** (10 min fix)
   Field names misspelled, data types wrong, missing fields

3. **Endpoint Setup** (5 min fix)
   Wrong environment URL, missing parameters, or wrong method

4. **Version Mismatch** (5 min fix)
   SDK or dependency version conflicts

None require architecture changes—they're all straightforward once identified.

**How We Help**
I can support your team through a 20-minute debugging session where we:
- Review your error logs and stack trace
- Walk through your API configuration together
- Test the fix with a successful API call
- Document the solution so your team knows what changed

**Your Options**

1. **Live Debugging Session** (20 minutes)
   → Schedule this week: [calendar link]
   → Result: You deploy the fix same day

2. **Async Support**
   → Reply with error details and code
   → I'll provide the exact fix and explanation
   → Usually resolves in 1-2 async rounds

3. **Documentation + Questions**
   → Access our {category}-specific troubleshooting guide: [link]
   → Ask questions as you work through it

I've helped dozens of {category} companies resolve exactly this type of blocker. Let's get your team unblocked quickly.

What works best for {company}?

Best regards,

[Your Name]
Technical Success Manager
Blostem"""
    
    return {
        "partner_id": partner_id,
        "pattern": StallPattern.STUCK_IN_SANDBOX,
        "engagement_model": "Technical support + debugging assistance",
        "recommended_owner": "Technical Support Manager",
        "error_code": error_code,
        "subject": subject,
        "body": body,
        "cta": "Schedule 20-minute technical debugging session",
        "tone": "technical_expert",
        "generated_at": datetime.now().isoformat()
    }


def generate_production_blocked_email(partner_id: int, stall_data: dict) -> dict:
    """
    Pattern 3: Production Blocked - Sandbox success but no production deployment
    Engagement: Account Manager helps unblock business/approval bottleneck
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
    category = partner['category']
    days_blocked = stall_data.get('days_of_inactivity', 0)
    sandbox_success = stall_data.get('last_sandbox_success', 'recently')
    
    subject = f"{company} is ready for {product} — help unblock production launch"
    
    body = f"""Hi {company} team,

Great news: your engineering team successfully completed sandbox testing for {product}. All tests passed, API connectivity is working perfectly, and everything is approved for production.

Here's the status:
✓ Sandbox testing: Complete (all tests passed)
✓ Integration validation: Confirmed working  
✓ Security review: Meets compliance requirements
✓ Architecture: Approved by engineering team

**What's Next**
Sometimes when engineering is ready, the path forward isn't always clear. There might be approvals needed, compliance questions, budget decisions, or just timeline priorities.

**Common Questions We Help With**
- Compliance/security: Does {product} meet our data residency and compliance needs?
- Privacy concerns: How is data encrypted? What's your data retention policy?
- Procurement/contracts: Do we need to update contracts? What's the cost model?
- Integration validation: Will this work with our existing systems and processes?
- Timeline: What's the best time to move forward?

We've helped dozens of {category} companies answer these questions and launch successfully.

**How We Help**
I can support you through:

1. **Quick Call** (30-60 minutes)
   → You pick your team, I bring compliance/finance/technical expertise
   → Result: Deployment plan within one week
   → Schedule: [calendar link]

2. **Written Q&A**
   → Send us your specific questions
   → We respond with documentation and answers
   → No pressure, just information

3. **Async Support**
   → Tell me your specific blocker
   → I'll send the exact information needed

**Why Now Matters**
Your team built this—let's get it live. Every week delay means:
- Manual data work your team could eliminate
- Compliance signals you're missing
- Opportunity cost while others integrate

I'm here to help. What works best for {company}?

Best regards,

[Your Name]
Partnership Manager
Blostem"""
    
    return {
        "partner_id": partner_id,
        "pattern": StallPattern.PRODUCTION_BLOCKED,
        "engagement_model": "Account Manager facilitates approval/deployment discussion",
        "recommended_owner": "Account Manager",
        "days_blocked": days_blocked,
        "subject": subject,
        "body": body,
        "cta": "Schedule production deployment planning call",
        "tone": "partnership_acceleration",
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


def check_email_compliance(subject: str, body: str) -> dict:
    """
    Check email for compliance issues with advanced pattern matching.
    Uses regex word boundaries to catch variations and detect manipulation tactics.
    """
    import re
    warnings = []
    is_compliant = True
    score = 100
    body_lower = body.lower()
    
    # Check length
    if len(body) < 150:
        warnings.append({"type": "TOO_SHORT", "message": "Email body is quite short (~150 chars minimum recommended)", "severity": "warning"})
        score -= 10
    
    if len(body) > 2000:
        warnings.append({"type": "TOO_LONG", "message": "Email exceeds 2000 characters (aim for 300-1500)", "severity": "info"})
        score -= 5
    
    # Check for excessive exclamation marks (spam indicator)
    sentences = body.split('.')
    for sentence in sentences:
        if sentence.count('!') > 2:
            warnings.append({"type": "EXCESSIVE_PUNCTUATION", "message": f"Too many exclamation marks ({sentence.count('!')} in one sentence) - looks like spam", "severity": "warning"})
            score -= 15
            is_compliant = False
            break
    
    # Check for multiple !! in sequence (pressure tactic)
    if '!!' in body:
        consecutive_exclamations = re.findall(r'!{2,}', body)
        if len(consecutive_exclamations) >= 2:
            warnings.append({"type": "PRESSURE_TACTICS", "message": "Multiple sequences of !! detected - aggressive pressure language", "severity": "warning"})
            score -= 12
            is_compliant = False
    
    # Check for too many links (spam indicator)
    links = re.findall(r'https?://\S+', body)
    if len(links) > 2:
        warnings.append({"type": "TOO_MANY_LINKS", "message": f"Too many links ({len(links)}) - looks like spam", "severity": "warning"})
        score -= 20
        is_compliant = False
    
    # Check tone - flag aggressive language (with word boundaries to catch variations)
    aggressive_patterns = [
        (r'\b(must|must\'s|musts)\b', 'must/mandatory'),
        (r'\b(demands?|demanding)\b', 'demand'),
        (r'\b(require[ds]?|requiring|requirement|required)\b', 'require'),
        (r'\b(immediately|urgent|urgently|critical|critically)\b', 'immediate/urgent'),
        (r'\b(don\'?t\s+miss|don\'?t\s+wait|don\'?t\s+delay)\b', 'FOMO tactics'),
    ]
    
    aggressive_found = []
    for pattern, label in aggressive_patterns:
        matches = re.findall(pattern, body_lower, re.IGNORECASE)
        if matches:
            aggressive_found.append(label)
    
    if aggressive_found:
        warnings.append({"type": "AGGRESSIVE_LANGUAGE", "message": f"Aggressive language detected: {', '.join(aggressive_found)}", "severity": "warning"})
        score -= 15
        is_compliant = False
    
    # Check for aggressive scarcity/urgency tactics (high-pressure sales language)
    # Only flag the most aggressive patterns combined together
    scarcity_patterns = [
        (r'\b(expires?|expir(ing|ed)|deadline|last\s+chance)\b', 'expiration urgency'),
        (r'\b(hurr(y|ies)|rush)\b', 'rush tactics'),
        (r'\b(only\s+\d+\s+(left|remaining|available))\b', 'scarcity numbers'),
        (r'\b(act\s+now|don\'?t\s+wait|don\'?t\s+miss)\b', 'FOMO tactics'),
    ]
    
    scarcity_found = []
    for pattern, label in scarcity_patterns:
        matches = re.findall(pattern, body_lower, re.IGNORECASE)
        if matches:
            scarcity_found.append(label)
    
    # Only penalize if 3+ aggressive patterns combined
    if len(scarcity_found) >= 3:
        warnings.append({"type": "SCARCITY_TACTICS", "message": f"Multiple aggressive scarcity/urgency tactics detected: {', '.join(scarcity_found)}", "severity": "warning"})
        score -= 18
        is_compliant = False
    elif len(scarcity_found) == 2:
        warnings.append({"type": "SCARCITY_TACTICS", "message": f"Scarcity/urgency tactics: {', '.join(scarcity_found)}", "severity": "info"})
        score -= 5
    
    # Check for false authority claims (mimicking certifications/approvals)
    authority_patterns = [
        (r'\b(we\s+guarantee|we\s+promise|guaranteed|promised)\b', 'false guarantee'),
        (r'\b(certified|verification|verified|approved|official)\b', 'authority claims'),
        (r'\b(endorsed|recommended\s+by|trusted\s+by)\b', 'endorsement claims'),
    ]
    
    authority_found = []
    for pattern, label in authority_patterns:
        matches = re.findall(pattern, body_lower, re.IGNORECASE)
        if matches:
            authority_found.append(label)
    
    if authority_found:
        warnings.append({"type": "AUTHORITY_MIMICKING", "message": f"Authority/guarantee claims detected: {', '.join(authority_found)} - must be substantiated", "severity": "warning"})
        score -= 10
        is_compliant = False
    
    # Check for vague claims
    vague_words = ['revolutionary', 'game-changing', 'best-in-class', 'industry-leading', 'breakthrough']
    vague_found = [w for w in vague_words if w in body_lower]
    if vague_found:
        warnings.append({"type": "VAGUE_CLAIMS", "message": f"Unsubstantiated claims: {', '.join(vague_found)}. Use concrete facts instead.", "severity": "warning"})
        score -= 10
        is_compliant = False
    
    # Check for compliance language
    if 'compliance' in body_lower or 'regulatory' in body_lower:
        if 'please' not in body_lower and 'help' not in body_lower:
            warnings.append({"type": "COMPLIANCE_TONE", "message": "Compliance emails should use 'help' and 'support' language, not mandates", "severity": "info"})
    
    # Check for subject line quality
    if len(subject) < 20:
        warnings.append({"type": "WEAK_SUBJECT", "message": "Subject line could be more specific (20+ chars)", "severity": "info"})
        score -= 5
    
    if '???' in subject or '!!!' in subject:
        warnings.append({"type": "UNPROFESSIONAL", "message": "Avoid excessive punctuation in subject", "severity": "warning"})
        score -= 10
        is_compliant = False
    
    # Check for CTA clarity
    cta_words = ['help', 'support', 'discuss', 'chat', 'call', 'meeting', 'session', 'available']
    has_cta = any(word in body_lower for word in cta_words)
    if not has_cta:
        warnings.append({"type": "MISSING_CTA", "message": "No clear call-to-action detected. Add what you want them to do.", "severity": "warning"})
        score -= 20
        is_compliant = False
    
    return {
        "is_compliant": is_compliant,
        "compliance_score": max(0, score),
        "warnings": warnings
    }


def fix_compliance_issues_with_ai(subject: str, body: str, compliance_result: dict) -> dict:
    """
    Intelligently fix specific compliance issues detected in email using AI.
    Uses surgical approach - fixes only the flagged issues, preserves other content.
    Includes error handling for graceful degradation if API fails.
    
    Args:
        subject: Email subject line
        body: Email body text
        compliance_result: Result from check_compliance() with status, warnings, violations
        
    Returns:
        {
            "subject": str,
            "body": str,
            "compliance_status": "CLEAR" | "WARNING" | "BLOCKED" | "ERROR",
            "compliance_score": int (0-100),
            "fixed": bool,
            "error": str or None,
            "method": str ("ai_fix" | "original_returned" | "api_error_fallback")
        }
    """
    try:
        from intelligence.llm_extractor import _call_llm
        from outreach.compliance_rules import check_compliance
        
        # Extract the specific issues to fix
        violations = compliance_result.get("violations", [])
        warnings = compliance_result.get("warnings", [])
        all_issues = violations + warnings
        
        if not all_issues:
            # Already compliant, no need to fix
            return {
                "subject": subject,
                "body": body,
                "compliance_status": compliance_result.get("status", "CLEAR"),
                "compliance_score": compliance_result.get("score", 100),
                "fixed": False,
                "error": None,
                "method": "original_returned"
            }
        
        # Build issue summary for the LLM
        issue_summary = "\n".join([
            f"- {issue.get('type', 'UNKNOWN')}: {issue.get('message', 'No details')}"
            for issue in all_issues
        ])
        
        # Create focused prompt to fix only the issues
        fix_prompt = f"""You are an expert email compliance editor. Your task is to fix ONLY the specific compliance issues in this email while preserving all other content and tone.

CURRENT EMAIL:
Subject: {subject}
Body:
{body}

ISSUES TO FIX:
{issue_summary}

INSTRUCTIONS:
1. Fix ONLY the flagged issues above
2. Keep the email structure, tone, and messaging intact
3. Make minimal surgical edits - don't rewrite the entire email
4. Ensure the fixed email reads naturally and professionally
5. DO NOT add new content, only modify problematic phrases
6. Replace aggressive/urgent language with collaborative language
7. Remove any time pressure or scarcity language

Return ONLY the fixed email in this format:
SUBJECT: [fixed subject]
BODY:
[fixed body text]

Do not include explanations or other text."""

        try:
            # Call LLM with timeout
            response = _call_llm(fix_prompt, max_tokens=1024, use_fast_model=False)
            
            if not response:
                logger.warning("LLM returned empty response for compliance fix, using original email")
                return {
                    "subject": subject,
                    "body": body,
                    "compliance_status": compliance_result.get("status", "UNKNOWN"),
                    "compliance_score": compliance_result.get("score", 0),
                    "fixed": False,
                    "error": "API returned empty response",
                    "method": "api_error_fallback"
                }
            
            # Parse response
            response_text = response.strip()
            if "SUBJECT:" not in response_text or "BODY:" not in response_text:
                logger.warning("LLM response malformed, using original email")
                return {
                    "subject": subject,
                    "body": body,
                    "compliance_status": compliance_result.get("status", "UNKNOWN"),
                    "compliance_score": compliance_result.get("score", 0),
                    "fixed": False,
                    "error": "API response malformed",
                    "method": "api_error_fallback"
                }
            
            # Extract fixed subject and body
            subject_start = response_text.index("SUBJECT:") + 8
            body_start = response_text.index("BODY:") + 5
            
            fixed_subject = response_text[subject_start:body_start-5].strip()
            fixed_body = response_text[body_start:].strip()
            
            # Validate fixed email with compliance check
            fixed_compliance = check_compliance(fixed_body, fixed_subject)
            
            # Only return if it's now CLEAR or better
            if fixed_compliance.get("status") in ["CLEAR", "TIP"]:
                logger.info(f"Successfully fixed compliance issues via AI. Score improved from {compliance_result.get('score', 0)} to {fixed_compliance.get('score', 0)}")
                return {
                    "subject": fixed_subject,
                    "body": fixed_body,
                    "compliance_status": fixed_compliance.get("status", "CLEAR"),
                    "compliance_score": fixed_compliance.get("score", 100),
                    "fixed": True,
                    "error": None,
                    "method": "ai_fix"
                }
            else:
                logger.warning(f"Fixed email still has compliance issues ({fixed_compliance.get('status')}), using original")
                return {
                    "subject": subject,
                    "body": body,
                    "compliance_status": compliance_result.get("status", "UNKNOWN"),
                    "compliance_score": compliance_result.get("score", 0),
                    "fixed": False,
                    "error": f"Fix still has {fixed_compliance.get('status')} status",
                    "method": "api_error_fallback"
                }
        
        except Exception as llm_error:
            logger.error(f"Error calling LLM for compliance fix: {str(llm_error)}", exc_info=True)
            # Gracefully return original email on API failure
            return {
                "subject": subject,
                "body": body,
                "compliance_status": compliance_result.get("status", "UNKNOWN"),
                "compliance_score": compliance_result.get("score", 0),
                "fixed": False,
                "error": f"API error: {str(llm_error)[:50]}",
                "method": "api_error_fallback"
            }
    
    except Exception as outer_error:
        logger.error(f"Unexpected error in fix_compliance_issues_with_ai: {str(outer_error)}", exc_info=True)
        # Final safety net - return original email
        return {
            "subject": subject,
            "body": body,
            "compliance_status": "ERROR",
            "compliance_score": 0,
            "fixed": False,
            "error": f"System error: {str(outer_error)[:50]}",
            "method": "api_error_fallback"
        }


def enhance_email_with_llm(partner_id: int, subject: str, body: str, pattern: str) -> dict:
    """
    Enhance email using Groq for more polished, compelling version.
    Makes emails longer, more persuasive, and better structured.
    CRITICAL: Validates compliance after enhancement to avoid regulatory violations.
    Falls back to local enhancement if Groq is unavailable or produces non-compliant output.
    """
    from intelligence.llm_extractor import _call_llm
    from outreach.compliance_rules import check_compliance
    
    # Try to get partner context, but don't fail if not available
    company = "Partner"
    product = "Platform"
    category = "fintech"
    
    if partner_id and partner_id > 0:
        with get_db() as conn:
            partner = conn.execute(
                """SELECT p.name, p.category, p.recommended_product
                   FROM partners_activated pa
                   JOIN prospects p ON pa.prospect_id = p.id
                   WHERE pa.prospect_id = ?""",
                (partner_id,)
            ).fetchone()
        
        if partner:
            company = partner['name']
            product = partner['recommended_product']
            category = partner.get('category', 'fintech')
    
    # COMPLIANCE CONSTRAINTS: Tell the LLM what to avoid
    compliance_constraints = """CRITICAL COMPLIANCE & TONE RULES - DO NOT VIOLATE:

REGULATORY (Hard rules):
1. NO guaranteed returns (avoid: 'guaranteed', 'assured', 'zero risk', '100% safe')
2. NO overstated insurance (avoid: 'fully insured', '100% covered')
3. NO false regulatory claims (avoid: 'RBI-approved', 'SEBI-certified')
4. NO unqualified rates (always use: 'up to X%', 'rates vary by', 'subject to')
5. NO misleading comparisons (no 'better than', 'unlike', 'replace')

TONE (Critical for response rates):
6. NEVER use directive language: avoid 'must', 'should', 'need to', 'expect', 'demand'
   Bad: "you must buy", "you should integrate", "you need to consider"
   Good: "we recommend", "you might benefit from", "we can help you"
7. NO aggressive urgency (avoid: "don't miss", "act now", "limited time", "urgent")
8. NO unsubstantiated claims (avoid: "best-in-class", "world-leading", "top-tier")
9. NO vague transformations (avoid: "transform", "revolutionize", "disrupt")
10. NO signal leakage (avoid: "we noticed", "we saw your", "your funding", "your app update")

FORMAT:
- Write professionally for C-level executives (CFO, CTO, CPO)
- Use collaborative, partnership language
- Focus on SPECIFIC benefits, not abstract claims
- Include actual value propositions with concrete outcomes
- End with clear, optional next steps (not demands)"""
    
    prompt = f"""You are an expert partnership manager at Blostem writing professional, compliant intervention emails.

Context:
- Partner: {company} ({category})
- Product: {product}
- Pattern: {pattern}

Current email:
Subject: {subject}
Body: {body}

{compliance_constraints}

Please enhance this email to be:
1. More compelling and persuasive (add specific benefits)
2. Longer and more detailed (400-600 words)
3. Better structured with clear sections
4. More personalized to their situation
5. Include specific value propositions
6. Better CTA framing
7. 100% COMPLIANT with all regulatory and tone rules above

IMPORTANT: 
- Replace any directive language ("must", "should", "need to", "expect") with collaborative language
- If the original email contains prohibited phrases, REMOVE them and rewrite those sections
- Use "we can help you", "we recommend", "consider", "explore", "partnership" instead of commands
- End with optional next steps, NOT demands ("Would you be open to..." instead of "You must...")

Keep the original engagement model, but make it more professional and persuasive while maintaining 100% compliance with all rules listed above.

Return ONLY the enhanced email in this format:
SUBJECT: [new subject]
BODY:
[new body text]

Do not include any other text or explanations."""

    try:
        # Use Groq API for enhancement (same as email generation)
        response = _call_llm(prompt, max_tokens=1024, use_fast_model=False)
        
        if not response:
            # Fallback to local enhancement if Groq fails
            return _enhance_email_locally(subject, body, pattern, company, product, category)
        
        # Parse response
        enhanced_text = response.strip()
        parts = enhanced_text.split('BODY:', 1)
        
        if len(parts) == 2:
            enhanced_subject = parts[0].replace('SUBJECT:', '').strip()
            enhanced_body = parts[1].strip()
        else:
            enhanced_subject = subject
            enhanced_body = body
        
        # CRITICAL: Run compliance check on enhanced email
        compliance_result = check_compliance(
            body=enhanced_body,
            subject=enhanced_subject,
            recipient_name=None,
            company_name=company
        )
        
        # Stricter check: Reject if status is not CLEAR (reject WARNING and BLOCKED)
        # This ensures enhanced emails have NO violations, not just no CRITICAL violations
        if compliance_result.get('status') != 'CLEAR':
            logger.warning(
                f"Enhanced email has compliance issues ({compliance_result.get('status')}): "
                f"{compliance_result.get('summary')}. Using local enhancement instead."
            )
            return _enhance_email_locally(subject, body, pattern, company, product, category)
        
        return {
            "success": True,
            "subject": enhanced_subject,
            "body": enhanced_body,
            "enhancement_note": "Powered by Groq AI - compliant, compelling, and professional",
            "compliance_score": compliance_result.get('score', 0),
            "compliance_status": compliance_result.get('status', 'CLEAR')
        }
    except Exception as e:
        # Fallback to local enhancement if Groq fails
        logger.exception(f"Enhance with LLM failed: {e}")
        return _enhance_email_locally(subject, body, pattern, company, product, category)


def _enhance_email_locally(subject: str, body: str, pattern: str, company: str, product: str, category: str) -> dict:
    """
    Local email enhancement without Claude API.
    Expands emails to be more detailed and persuasive.
    """
    # Expand body with structured sections and more detail
    enhanced_body = body
    
    # If body is very short, add structured sections
    if len(body) < 300:
        sections = []
        
        # Opening
        if not any(word in enhanced_body.lower() for word in ['hello', 'hi', 'dear']):
            sections.append(f"Hello {company} team,\n\n")
        
        sections.append(enhanced_body)
        
        # Add context section if missing
        if 'why' not in enhanced_body.lower() and 'important' not in enhanced_body.lower():
            sections.append(f"\n\n**Why This Matters**\n{product} enables {company} to:")
            if category == 'fintech':
                sections.append("- Improve compliance and regulatory visibility")
                sections.append("- Reduce fraud detection latency")
                sections.append("- Enhance customer risk assessment")
            sections.append("- Make data-driven decisions faster")
        
        # Add engagement options if missing
        if 'option' not in enhanced_body.lower() and 'would' not in enhanced_body.lower():
            sections.append("\n\n**Next Steps - Pick What Works Best**\n")
            sections.append("Option 1: Let's discuss this week\n[calendar link]\n")
            sections.append("Option 2: Send me your questions and I'll respond with answers\n")
            sections.append("Option 3: Let's schedule a detailed walkthrough\n")
        
        # Add closing if missing
        if not any(word in enhanced_body.lower() for word in ['best', 'regards', 'sincerely']):
            sections.append("\n\nLooking forward to helping you succeed.\n\nBest regards")
        
        enhanced_body = "\n".join(sections)
    else:
        # Body is already substantial, just clean it up
        if not enhanced_body.endswith('.') and not enhanced_body.endswith('?') and not enhanced_body.endswith('!'):
            enhanced_body += '.'
    
    # Enhance subject if it's too generic
    enhanced_subject = subject
    if len(subject) < 30:
        # Add more specific framing
        if 'question' in subject.lower():
            enhanced_subject = f"{company} — {subject.lower()} regarding {product}"
        elif 'quick' in subject.lower():
            enhanced_subject = f"Quick {product} integration discussion for {company}"
        else:
            enhanced_subject = f"{company} — {subject} ({product})"
    
    return {
        "success": True,
        "subject": enhanced_subject,
        "body": enhanced_body,
        "enhancement_note": "Local enhancement - expanded with structure and detail (Claude AI unavailable)"
    }

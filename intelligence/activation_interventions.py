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
    Check email for compliance issues.
    Returns compliance status with warnings and suggestions.
    """
    warnings = []
    is_compliant = True
    score = 100
    
    # Check length
    if len(body) < 150:
        warnings.append({"type": "TOO_SHORT", "message": "Email body is quite short (~150 chars minimum recommended)", "severity": "warning"})
        score -= 10
    
    if len(body) > 2000:
        warnings.append({"type": "TOO_LONG", "message": "Email exceeds 2000 characters (aim for 300-1500)", "severity": "info"})
        score -= 5
    
    # Check tone - flag aggressive language
    aggressive_words = ['must', 'demand', 'required', 'immediately', 'urgent', 'critical']
    aggressive_found = [w for w in aggressive_words if f' {w} ' in f' {body.lower()} ']
    if aggressive_found:
        warnings.append({"type": "TONE", "message": f"Aggressive language detected: {', '.join(aggressive_found)}", "severity": "warning"})
        score -= 15
        is_compliant = False
    
    # Check for vague claims
    vague_words = ['revolutionary', 'game-changing', 'best-in-class', 'industry-leading']
    vague_found = [w for w in vague_words if w in body.lower()]
    if vague_found:
        warnings.append({"type": "VAGUE_CLAIMS", "message": f"Unsubstantiated claims: {', '.join(vague_found)}. Use concrete facts instead.", "severity": "warning"})
        score -= 10
        is_compliant = False
    
    # Check for compliance language
    if 'compliance' in body.lower() or 'regulatory' in body.lower():
        if 'please' not in body.lower() or 'help' not in body.lower():
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
    has_cta = any(word in body.lower() for word in cta_words)
    if not has_cta:
        warnings.append({"type": "MISSING_CTA", "message": "No clear call-to-action detected. Add what you want them to do.", "severity": "warning"})
        score -= 20
        is_compliant = False
    
    return {
        "is_compliant": is_compliant,
        "compliance_score": max(0, score),
        "warnings": warnings
    }


def enhance_email_with_llm(partner_id: int, subject: str, body: str, pattern: str) -> dict:
    """
    Enhance email using Claude for more polished, compelling version.
    Makes emails longer, more persuasive, and better structured.
    Falls back to local enhancement if Claude is unavailable.
    """
    import anthropic
    import os
    
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
    
    prompt = f"""You are an expert partnership manager at Blostem writing professional, compelling intervention emails.

Context:
- Partner: {company} ({category})
- Product: {product}
- Pattern: {pattern}

Current email:
Subject: {subject}
Body: {body}

Please enhance this email to be:
1. More compelling and persuasive (add specific benefits)
2. Longer and more detailed (400-600 words)
3. Better structured with clear sections
4. More personalized to their situation
5. Include specific value propositions
6. Better CTA framing

Keep the original tone and engagement model, but make it more professional and persuasive.

Return ONLY the enhanced email in this format:
SUBJECT: [new subject]
BODY:
[new body text]

Do not include any other text or explanations."""

    try:
        # Try Claude enhancement first
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Claude API key not configured")
            
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        enhanced_text = response.content[0].text
        parts = enhanced_text.split('BODY:', 1)
        
        if len(parts) == 2:
            enhanced_subject = parts[0].replace('SUBJECT:', '').strip()
            enhanced_body = parts[1].strip()
        else:
            enhanced_subject = subject
            enhanced_body = body
        
        return {
            "success": True,
            "subject": enhanced_subject,
            "body": enhanced_body,
            "enhancement_note": "Powered by Claude AI - makes email more compelling and professional"
        }
    except Exception as e:
        # Fallback to local enhancement if Claude fails
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

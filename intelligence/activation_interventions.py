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
    
    subject = f"Let's get {company} launched with {product} — hands-on onboarding support"
    
    body = f"""{company} Engineering Team,

I wanted to personally reach out regarding the {product} integration {company} signed up for on {signed_date.strftime('%B %d, %Y')}.

I noticed your team hasn't yet started the integration phase, and I wanted to check in. Getting a new integration live can sometimes feel like a lot, especially alongside ongoing product development work. But here's what I want you to know: we've gotten hundreds of {category} companies live in just a few hours, and the process is straightforward when you have the right support.

**Why Integration Matters**
For {company}, integrating {product} unlocks:
- Direct access to fintech data APIs without building custom connectors
- Real-time transaction monitoring and risk signals
- Reduced fraud detection latency by 60-70%
- Compliance data for regulatory reporting (all pre-formatted)

Most importantly, it means your product team can focus on building features instead of maintaining data pipelines.

**The Integration Reality (Spoiler: It's Fast)**
Your engineering team typically needs 2-4 hours total from start to live. Here's the breakdown:

Phase 1: Setup (30 minutes)
- Create sandbox API credentials in dashboard
- Download SDK for your tech stack (Python, Go, Node.js, Java)
- Configure environment variables
- First sandbox test call (we walk through this together)

Phase 2: Integration (1-2 hours)
- Integrate API calls into your existing data pipeline
- Test with real sandbox data
- Validate response formats match your schema
- Set up error handling and retry logic

Phase 3: Go Live (30 minutes)
- Switch credentials to production
- Test with 1-2 live transactions
- Deploy to production
- Set up monitoring/alerting

**What We'll Handle**
We don't expect your team to figure this out alone. Here's exactly what I can offer:

Option 1: Live Onboarding Session (Most Common - 2-3 hours)
We jump on a screen share with your engineering team. I walk through:
- Architecture overview (how our APIs fit into your stack)
- Step-by-step integration walkthrough
- Common integration patterns for {category} companies
- Best practices for production reliability
- Q&A for any architecture questions

Timeline: Pick a slot this week (Mon-Fri, flexible on time zones)
Outcome: Your team deploys production code same day

Option 2: Self-Service + Async Support (For Teams with Limited Time)
You follow our documentation, we answer questions as they come up:
- Slack channel for real-time questions
- Video walkthroughs for each integration phase
- Example code in your tech stack
- Pre-built error handling templates

Timeline: 3-5 business days at your pace
Outcome: Full integration without taking your whole team's time

Option 3: Hybrid (Documentation + One Deep Dive)
Your team reviews documentation, we do one 1-hour call to cover architecture and answer hard questions:
- Pre-call documentation review
- 1-hour architectural design session
- Post-call async support as needed

Timeline: This week's call + 2-3 days completion
Outcome: Full confidence + faster time to launch

**Why Now Matters**
Every week you delay integration:
- Your product team is doing manual data work that APIs could handle
- You're missing out on compliance signals that reduce risk
- Competitors are potentially integrating faster

But honestly, the main thing is just getting started. First conversation is always the hardest part.

**Next Steps**
I'd love to get your team unblocked this week. Here are a few options:

1. **Schedule a 30-minute quick call** (my calendar): {{CALENDAR_LINK}}
   - Just us chatting about your architecture and concerns
   - No pressure, no sales pitch—just engineering talk

2. **Grab the docs and I'll answer questions**: 
   - I'll send over step-by-step guides
   - Slack me when you hit blockers
   - Usually resolves in 2-3 async rounds

3. **Let me know what works for {company}**:
   - Reply with your timeline and team size
   - I'll propose the best approach

Whatever you choose, I'm confident we can get {company} live this week. I've done this 200+ times with teams just like yours, and the integration is genuinely straightforward when you have support.

Looking forward to working with your team. Feel free to reach out if you have any initial questions.

Best regards,

[Your Name]
Senior Customer Success Manager
Blostem Partnerships

P.S. If you want to read ahead, here are the docs for {company}'s tech stack (we detect most stacks automatically, but happy to send specific ones):
- Python/FastAPI: [link]
- Node.js/Express: [link]
- Go: [link]
- Java/Spring: [link]

P.P.S. If right now is bad timing, that's totally fine. Just let me know when your team will have bandwidth and I'll check back in. We're here when you're ready."""
    
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
    
    # Map error codes to detailed explanations
    error_details = {
        "AUTH_FAILED": "authentication/authorization error (invalid API key or insufficient permissions)",
        "MISSING_FIELD": "missing required field in request payload",
        "RATE_LIMIT": "API rate limiting (hitting quota thresholds)",
        "INVALID_REQUEST": "malformed request (wrong format or structure)",
        "TIMEOUT": "request timeout (taking too long to respond)",
        "VERSION_MISMATCH": "API version mismatch between client and server"
    }
    
    error_desc = error_details.get(error_code, "technical integration issue")
    subject = f"{company} — urgent {product} integration support needed"
    
    body = f"""Hello {company} Engineering Team,

I wanted to reach out because I noticed your {product} integration hit a technical blocker in sandbox testing. Looking at the logs, it appears to be a {error_desc}.

I want to be straightforward: this is exactly the kind of thing we see all the time, and it's almost always a 5-15 minute fix once we've got eyes on it together. I've helped dozens of {category} companies resolve the same issue, and I'm confident we can get you unblocked today.

**What I'm Seeing**
Error code: {error_code}
Status: Sandbox integration attempted, but not progressing
Likely cause: {error_desc}

**Why This Matters**
Every day your integration is blocked:
- Your team is context-switching away from the integration work
- Product roadmap features dependent on this integration are delayed
- Time-sensitive compliance signals are being missed

**The Reality of This Fix**
I want to set expectations correctly. Technical blockers like this are usually one of these:

1. **Credential Issue (Most Common - 2 min fix)**
   - API key not properly passed in headers
   - Token expired or incorrectly formatted
   - Permission scope too narrow
   - Fix: Regenerate credentials, update config, test

2. **Request Format Issue (10 min fix)**
   - Field names misspelled (case sensitivity)
   - Required fields missing from payload
   - Wrong data type (string vs. int, etc.)
   - Fix: Validate against schema, adjust payload

3. **Endpoint Configuration Issue (5 min fix)**
   - Wrong environment URL (sandbox vs. prod)
   - Missing query parameters
   - Incorrect HTTP method
   - Fix: Validate endpoint config, test

4. **Version Mismatch (5 min fix)**
   - SDK version incompatible with API version
   - Dependency conflicts in your environment
   - Fix: Update SDK or pin older version

None of these require architectural changes. They're all straightforward once we identify which one it is.

**What I'll Do**
I'm going to schedule a 20-minute call where we:

1. **Screen Share Review (5 min)**
   - Look at your actual error message + stack trace
   - Check your API key configuration
   - Review your request payload

2. **Live Debugging (10 min)**
   - I'll help you identify the exact issue
   - We'll implement the fix together
   - Test with a successful API call

3. **Prevention (5 min)**
   - Document what you did so team members know
   - Set up proper error logging going forward
   - Identify any other potential blockers ahead of time

**Next Steps - Pick One**

Option 1: Let's Go Right Now (Fastest)
Available for an immediate 20-minute call:
- [calendar link for 20-min slots this afternoon]

Option 2: Schedule for This Week
I've got slots throughout the week:
- Tuesday 11 AM - 2 PM IST
- Wednesday 2 PM - 4 PM IST
- Thursday 10 AM - 12 PM IST
- Friday 1 PM - 3 PM IST

Option 3: Send Me Your Error Details + Code
If you prefer, reply with:
- Full error message/stack trace
- Your request code (what you're sending)
- Your API configuration (sanitized)
- Your tech stack (Python/Node/Go/Java/etc)

I'll review and send back the exact fix with explanation.

**Why I Know This Will Work**
I've worked through {error_code} errors with dozens of companies. With your team and full context, we solve these in under 15 minutes. No uncertainty, no back-and-forth emails.

I'm going to be direct: getting unstuck today matters. The longer this sits, the more context your team loses. But once we've resolved it, integration typically moves really fast.

Let me know which option works best. I'm ready to help immediately.

Best regards,

[Your Name]
Senior Technical Success Manager
Blostem Support

P.S. If you want to get a head start, our {category}-specific troubleshooting guide covers 90% of issues like this: [link]. But I'd still want to jump on a quick call to make sure we identify your specific issue correctly.

P.P.S. No blame here—this is completely normal. Integration is hard, and half the teams we work with hit a blocker at this exact stage. The key is just getting eyes on it to resolve quickly."""
    
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
    
    subject = f"{company} is ready for {product} production — let's unblock next steps"
    
    body = f"""Hello {company} Leadership Team,

Great news: your engineering team successfully completed sandbox testing for {product}. All integration tests passed, API connectivity is working perfectly, and the technical team confirmed everything is ready for production.

Here's where we are:
✓ Sandbox testing: Complete (all tests passed)
✓ Integration validation: Confirmed working
✓ Security review: {product} meets fintech compliance standards
✓ Architecture: Approved by your engineering team

What's missing: The decision to deploy to production.

I wanted to reach out because sometimes even when engineering is ready, the path forward isn't always clear. There might be approvals needed, questions about data privacy, compliance concerns, budget confirmation, or just bandwidth on your side. Whatever it is, I can usually help unblock it in one conversation.

**Why This Moment Matters**
Your team did the hard part—they built, tested, and validated the integration. Deploying takes literally 30 minutes. Staying in this "sandbox ready but not live" state costs you:

- **Compliance Gap**: You're missing regulatory data signals that {product} provides
- **Operational Inefficiency**: Your team maintains manual data processes that the API would handle automatically
- **Competitive Risk**: You're relying on older data infrastructure while competitors get faster insights
- **Team Friction**: Your engineering team built this, they're probably wondering why it's not live yet

But here's what matters most: every week you delay is a week you're not getting the business value you signed up for.

**What Might Be Blocking You (And How We Fix It)**

I work with {category} companies on this all the time. The blockers usually fall into these categories:

**1. Compliance / Security Questions**
"Does {product} meet our data residency requirements?"
"Who has access to the data?"
"What's your SOC2/ISO certification status?"
→ We can answer all of this in a 15-minute call with our compliance team

**2. Privacy / Data Governance Questions**
"How is transaction data encrypted?"
"Do you store customer PII?"
"What's your data retention policy?"
→ We have comprehensive privacy documentation, and I can walk you through it

**3. Business Approval Questions**
"Do we need to update our contracts?"
"Is there a cost for production use?"
"What's the SLA for uptime?"
→ All standard questions, all addressable quickly

**4. Integration Validation Questions**
"Will {product} work with our existing systems?"
"What if there's an outage?"
"How do we handle error scenarios?"
→ Your engineering team validated this already, but I can confirm or address any remaining technical concerns

**5. Project Prioritization Questions**
"We have other priorities right now. When can we revisit?"
→ Totally fair. Let's just schedule a specific time so it doesn't get lost

**6. Budget / Procurement Questions**
"Do we need approval for this spend?"
"How does billing work?"
→ I can send over the pricing model and answer any financial questions

**Next Steps - Pick What Applies**

I want to make this as easy as possible. Here's what I'm proposing:

**Option A: Direct Call (Fastest - 1 hour total)**
You pick whoever should be on the call from your end (CEO, CTO, CFO—whoever unblocks this), I bring whoever we need, and we resolve it:
- 30 min: Q&A on compliance/security/privacy (I bring right people)
- 15 min: Address any remaining concerns
- 15 min: Plan deployment timeline

→ Calendar link for this week: [CALENDAR_LINK]

**Option B: Written Response (For Specific Questions)**
If you'd rather not meet, just reply with your specific questions/concerns and I'll provide written answers with documentation.

**Option C: Start with Your Blocker**
Tell me what the specific question/blocker is, and I'll respond with exactly what you need.

**What I Know for Sure**
- Your team did excellent work on the integration
- Everything is technically ready
- Deployment is a 30-minute process
- Whatever the question is, it's one we've answered 50+ times before

I'm confident we can unblock this conversation and get to a deployment plan within one week. The best time to do it is now, while the work is fresh in your team's mind.

Looking forward to getting {company} live.

Best regards,

[Your Name]
Account Manager
Blostem Partnerships

P.S. If you want some background reading before we talk, here are the most common questions answered:
- Production readiness checklist: [link]
- Compliance and security guide: [link]
- Data privacy and residency: [link]
- Production deployment best practices: [link]

P.P.S. If now is genuinely bad timing, that's okay. Just let me know when your team will be ready to think about this, and I'll touch base then. But I do think this is worth a conversation now—you're this close to launching."""
    
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
    """
    import anthropic
    
    with get_db() as conn:
        partner = conn.execute(
            """SELECT p.name, p.category, p.recommended_product
               FROM partners_activated pa
               JOIN prospects p ON pa.prospect_id = p.id
               WHERE pa.prospect_id = ?""",
            (partner_id,)
        ).fetchone()
    
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
        return {
            "success": False,
            "error": str(e),
            "enhancement_note": "Enhancement failed - using original email"
        }

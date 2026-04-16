#!/usr/bin/env python3
"""
INNOVATION 3: Role-Specific Intervention Playbooks
Pre-built intervention sequences for each stakeholder role.
When a role-specific bottleneck is detected, automatically deploy the right playbook.

Key Insight: Different roles have different concerns and need different interventions.
Instead of one-size-fits-all outreach, match intervention to the role's blockers.

Playbook = Email template + supporting resources + escalation path + SLA
"""

from datetime import datetime, timedelta
from database import get_db
from enum import Enum

class PlaybookRole(Enum):
    CTO = "CTO"
    CFO = "CFO"
    VP_PRODUCT = "VP_PRODUCT"
    VP_SALES = "VP_SALES"
    LEGAL_COMPLIANCE = "LEGAL_COMPLIANCE"
    VP_OPERATIONS = "VP_OPERATIONS"

# ============================================================================
# SECTION 1: Playbook Definitions
# ============================================================================

PLAYBOOKS = {
    "CTO": {
        "name": "Technical Integration Playbook",
        "role": "CTO",
        "trigger_categories": ["TECHNICAL"],
        "common_blockers": ["api_auth_failures", "integration_complexity", "security_concerns"],
        "sla_hours": 4,
        "interventions": [
            {
                "sequence": 1,
                "action": "EMAIL_TECHNICAL_BRIEF",
                "template": "cto_architecture_review",
                "subject": "30-min architecture review to unblock your integration",
                "body": """Hi {name},

I noticed you're working on integrating Blostem into your platform. 
We specialize in making complex financial integrations simple.

Would you have 30 minutes this week for an architecture review call? 
We can review your integration design and identify the fastest path to production.

Key discussion points:
- API design best practices for your use case
- Common pitfalls you can avoid
- Architecture optimization for performance
- Security and compliance checklist

When's good for you? I'm flexible with timing.

Best,
{sender_name}
VP Engineering, Blostem""",
                "resources": [
                    "blostem_integration_guide.pdf",
                    "api_code_samples.zip",
                    "oauth_implementation_reference.md"
                ],
                "follow_up_days": 3
            },
            {
                "sequence": 2,
                "action": "SEND_RESOURCES",
                "template": "cto_resources_package",
                "subject": "Blostem Integration Resources",
                "body": """Hi {name},

Per our conversation, here are the resources to accelerate your integration:

1. Integration Guide (20 pages)
   - Step-by-step API walkthrough
   - Common pitfalls and how to avoid them
   - Performance optimization tips

2. Code Samples
   - OAuth2 implementation (Node, Python, Java)
   - Transaction processing example
   - Error handling patterns

3. Architecture Reference
   - System design diagrams
   - Data flow specifications
   - Security architecture

Our API is designed specifically for use cases like yours. 
These resources should get you from sandbox to production in 1-2 weeks.

Any questions as you review? Happy to jump on a call.

Best,
{sender_name}""",
                "resources": [
                    "detailed_integration_guide.pdf",
                    "code_samples_all_languages.zip",
                    "architecture_diagrams.pptx"
                ],
                "follow_up_days": 7
            },
            {
                "sequence": 3,
                "action": "OFFER_PAIRING",
                "template": "cto_pairing_session",
                "subject": "Let's pair on your integration",
                "body": """Hi {name},

How's the integration going? 

If you're hitting any roadblocks, I'd like to offer a pairing session.
Our engineering team can work directly with your devs to troubleshoot.

This is especially valuable if:
- You're stuck on OAuth setup
- You want to optimize performance
- You have questions about handling failures
- You want to review your architecture

Available this week: {available_slots}

Looking forward to helping you succeed.

Best,
{sender_name}""",
                "resources": ["debugging_checklist.md", "performance_tuning_guide.md"],
                "follow_up_days": 7
            },
            {
                "sequence": 4,
                "action": "ESCALATE",
                "template": "cto_vp_engineering_escalation",
                "subject": "CTO to VP Engineering call - Blostem integration",
                "body": """Hi {name},

I want to personally ensure your technical integration succeeds.

I'm the VP of Engineering at Blostem, and I'd love to schedule a 30-min call with you and your CTO.
We can discuss:
- Technical roadmap alignment
- Integration acceleration
- Long-term partnership success

This is not a sales call - just engineering-to-engineering partnership discussion.

When works for both of you?

Best,
{vp_name}
VP Engineering, Blostem""",
                "owner": "VP Engineering",
                "follow_up_days": -1
            }
        ],
        "success_criteria": ["First API call successful", "Sandbox testing underway", "Production timeline clear"],
        "escalation_owner": "VP Engineering"
    },
    "CFO": {
        "name": "Financial Alignment Playbook",
        "role": "CFO",
        "trigger_categories": ["BUSINESS", "PROCUREMENT"],
        "common_blockers": ["cost_concerns", "budget_cycle", "procurement_process", "roi_not_clear"],
        "sla_hours": 24,
        "interventions": [
            {
                "sequence": 1,
                "action": "EMAIL_ROI_CALCULATOR",
                "template": "cfo_roi_proposal",
                "subject": "Blostem ROI: Your numbers in 2 minutes",
                "body": """Hi {name},

I ran the economics for a company like yours using Blostem:

Investment: ${integration_cost:,} (one-time) + ${monthly_cost:,}/month
Revenue potential: ${annual_benefit:,}/year (conservative estimate)

ROI: {roi}% in Year 1

This is based on:
- {transaction_volume:,} potential transactions/month
- ${avg_per_transaction} average transaction value
- {implementation_days} days to production

The attached ROI calculator shows sensitivity analysis for your specific numbers.

When would be good to walk through your scenario?

Best,
{sender_name}
VP Sales, Blostem""",
                "resources": [
                    "roi_calculator.xlsx",
                    "financial_model.pdf",
                    "customer_economics_case_study.pdf"
                ],
                "follow_up_days": 3
            },
            {
                "sequence": 2,
                "action": "OFFER_FLEXIBLE_TERMS",
                "template": "cfo_flexible_pricing",
                "subject": "Flexible payment options for Blostem",
                "body": """Hi {name},

I understand procurement can take time. We're flexible on payment terms.

Options:
1. Traditional: Upfront integration fee + monthly platform fee
2. Performance-based: Lower upfront, higher per-transaction fees (you pay as you earn)
3. Commitment-based: Volume discount if you commit to transaction targets

We can structure something that matches your cash flow and risk tolerance.

Let's schedule 15 minutes to discuss which makes sense for you.

Best,
{sender_name}""",
                "resources": ["pricing_options.pdf", "payment_terms_matrix.xlsx"],
                "follow_up_days": 5
            },
            {
                "sequence": 3,
                "action": "SEND_PROCUREMENT_DOCS",
                "template": "cfo_procurement_package",
                "subject": "Blostem Procurement Documents",
                "body": """Hi {name},

To help expedite your procurement process, here's our complete package:

✓ Standard master services agreement
✓ SOW for your specific implementation
✓ Security & compliance certifications
✓ Insurance certificates
✓ References from similar companies

Our legal team is available if you need modifications to terms.

This should cover everything your legal team needs to approve.
Let me know if there are any gaps.

Best,
{sender_name}""",
                "resources": [
                    "msa_template.docx",
                    "standard_sow.docx",
                    "security_certifications.zip",
                    "insurance_certificates.pdf"
                ],
                "follow_up_days": 7
            },
            {
                "sequence": 4,
                "action": "ESCALATE",
                "template": "cfo_ceo_escalation",
                "subject": "Strategic partnership opportunity - CEO discussion",
                "body": """Hi {name},

I'd like to involve our CEO in the partnership discussion.
She'd love to speak with you about:

- Strategic partnership potential
- Long-term financial alignment
- Exclusive partnership opportunities

This isn't a closed conversation - it's an opportunity to discuss how
we can build a mutually beneficial long-term relationship.

Are you available this week?

Best,
{your_name}""",
                "owner": "CEO",
                "follow_up_days": -1
            }
        ],
        "success_criteria": ["ROI discussions complete", "Procurement approval timeline clear", "Payment terms agreed"],
        "escalation_owner": "CEO"
    },
    "VP_PRODUCT": {
        "name": "Product Alignment Playbook",
        "role": "VP Product",
        "trigger_categories": ["BUSINESS"],
        "common_blockers": ["feature_gap", "roadmap_conflict", "competitive_pressure"],
        "sla_hours": 24,
        "interventions": [
            {
                "sequence": 1,
                "action": "EMAIL_FEATURE_ROADMAP",
                "template": "vp_product_roadmap",
                "subject": "Blostem Product Roadmap + Your Input",
                "body": """Hi {name},

I wanted to share our product roadmap and get your input on features that matter for your platform.

Next quarter, we're prioritizing:
- {feature_1}: For use cases like yours
- {feature_2}: Based on partner feedback
- {feature_3}: Expanding coverage

I'd love to understand:
1. Which features would deliver most value for you?
2. Are there gaps in our current product?
3. How can we make Blostem a strategic advantage for you?

30-minute call this week to discuss?

Best,
{sender_name}
VP Product, Blostem""",
                "resources": [
                    "product_roadmap_public.pdf",
                    "feature_comparison_matrix.xlsx",
                    "customer_feedback_summary.pdf"
                ],
                "follow_up_days": 3
            },
            {
                "sequence": 2,
                "action": "SEND_COMPETITIVE_ANALYSIS",
                "template": "vp_product_competitive",
                "subject": "Competitive Landscape: Why Blostem Wins",
                "body": """Hi {name},

Given your platform, I thought you'd find this competitive analysis valuable.

We compared Blostem vs. the 3 main alternatives on:
- Feature coverage (we're 40% ahead on your use case)
- Integration speed (60% faster than competitor X)
- Cost of operations (50% lower support cost)

Details in the attached analysis.

The big win: you get enterprise features without enterprise complexity.

Let's schedule 15 minutes to discuss this?

Best,
{sender_name}""",
                "resources": [
                    "competitive_feature_matrix.xlsx",
                    "integration_speed_benchmark.pdf",
                    "tco_analysis.pdf"
                ],
                "follow_up_days": 5
            },
            {
                "sequence": 3,
                "action": "OFFER_FEATURE_PARTNERSHIP",
                "template": "vp_product_feature_partnership",
                "subject": "Feature Partnership Opportunity",
                "body": """Hi {name},

What if we built the missing feature together?

If there's a specific capability that would unlock growth for you,
we can prioritize it - sometimes even as a co-developed feature where
you participate in the design.

This is how we work with strategic partners.

What features would have the biggest impact?

Best,
{sender_name}""",
                "resources": ["feature_development_process.pdf", "partner_case_studies.pdf"],
                "follow_up_days": 7
            },
            {
                "sequence": 4,
                "action": "ESCALATE",
                "template": "vp_product_cpo_escalation",
                "subject": "Strategic Product Partnership - CPO Discussion",
                "body": """Hi {name},

I'd like to bring in our Chief Product Officer for a strategic discussion.
She oversees partnerships and can discuss:

- Co-development opportunities
- Product roadmap alignment
- Exclusive feature partnerships

This is an opportunity to shape our roadmap around your success.

When can we schedule?

Best,
{your_name}""",
                "owner": "Chief Product Officer",
                "follow_up_days": -1
            }
        ],
        "success_criteria": ["Feature requirements documented", "Roadmap alignment clear", "Product partnership discussed"],
        "escalation_owner": "Chief Product Officer"
    },
    "LEGAL_COMPLIANCE": {
        "name": "Legal & Compliance Playbook",
        "role": "Legal",
        "trigger_categories": ["COMPLIANCE"],
        "common_blockers": ["contract_review", "regulatory_requirements", "liability_concerns"],
        "sla_hours": 2,
        "interventions": [
            {
                "sequence": 1,
                "action": "EMAIL_LEGAL_BRIEF",
                "template": "legal_compliance_summary",
                "subject": "Blostem Compliance Summary (Legal Review)",
                "body": """Hi {name},

To expedite your legal review, here's a summary of our compliance posture:

Certifications:
✓ SOC 2 Type II certified (audited annually)
✓ ISO 27001 certified
✓ GDPR compliant

Regulatory:
✓ {relevant_regulatory} approved/compliant
✓ No liability limitations on data security
✓ Standard E&O insurance

Our legal team is available to address any specific concerns about:
- Data handling and security
- Liability and indemnification
- Regulatory compliance in your jurisdiction

When would your legal team have 30 minutes to discuss?

Best,
{sender_name}
Chief Legal Officer, Blostem""",
                "resources": [
                    "soc2_audit_report.pdf",
                    "iso27001_certificate.pdf",
                    "privacy_policy.pdf",
                    "data_processing_agreement.docx"
                ],
                "follow_up_days": 1
            },
            {
                "sequence": 2,
                "action": "SEND_REDLINE_DOCS",
                "template": "legal_custom_docs",
                "subject": "Pre-Redlined Agreement for Your Jurisdiction",
                "body": """Hi {name},

We've already pre-redlined our agreement for {jurisdiction} requirements.

Attached:
- MSA with {jurisdiction}-specific language
- DPA compliant with local data laws
- Insurance requirements pre-filled

This speeds up legal review significantly - most clients approve in 3-5 days
rather than weeks of back-and-forth.

Our legal team is standing by if your team has questions.

Best,
{sender_name}""",
                "resources": [
                    "msa_jurisdiction_redlined.docx",
                    "dpa_compliant.docx",
                    "legal_opinion_letter.pdf"
                ],
                "follow_up_days": 2
            },
            {
                "sequence": 3,
                "action": "ESCALATE",
                "template": "legal_clo_call",
                "subject": "CLO to CLO Call - Legal Review Expedite",
                "body": """Hi {name},

I'm our Chief Legal Officer. I wanted to reach out personally to help
accelerate your legal review.

I'm available for a call with you to discuss:
- Any specific legal concerns
- Potential contract modifications
- Expedited approval process

This isn't a negotiation - it's partnership problem-solving.

When works best for you?

Best,
{clo_name}
Chief Legal Officer, Blostem""",
                "owner": "Chief Legal Officer",
                "follow_up_days": -1
            }
        ],
        "success_criteria": ["Legal review complete", "No blockers identified", "Agreement signed"],
        "escalation_owner": "Chief Legal Officer"
    }
}

# ============================================================================
# SECTION 1: Playbook Selection and Execution
# ============================================================================

def get_playbook_for_role(role: str) -> dict:
    """Get playbook for a specific role."""
    
    if role not in PLAYBOOKS:
        return {"error": f"No playbook for role: {role}"}
    
    return PLAYBOOKS[role]

def select_playbook_by_bottleneck(bottleneck_category: str, role: str = None) -> dict:
    """
    Select appropriate playbook based on bottleneck category.
    If role specified, returns playbook for that role.
    If not specified, returns recommended playbook for category.
    """
    
    # Priority: If role specified, use that playbook
    if role:
        return get_playbook_for_role(role)
    
    # Otherwise, select best playbook for bottleneck category
    # Match bottleneck category to playbook trigger categories
    candidates = []
    for pb_role, playbook in PLAYBOOKS.items():
        if bottleneck_category in playbook.get("trigger_categories", []):
            candidates.append(pb_role)
    
    # Map common categories to roles
    if not candidates:
        category_map = {
            "COMPLIANCE": "LEGAL_COMPLIANCE",
            "ADOPTION": "VP_OPERATIONS",
            "SUPPORT": "VP_OPERATIONS"
        }
        if bottleneck_category in category_map:
            candidates = [category_map[bottleneck_category]]
        else:
            return {"error": f"No playbook found for bottleneck: {bottleneck_category}"}
    
    # Return first (highest priority) candidate
    pb_role = candidates[0]
    return get_playbook_for_role(pb_role)

def get_playbook_interventions(role: str) -> list:
    """Get all interventions in a playbook."""
    
    playbook = get_playbook_for_role(role)
    if "error" in playbook:
        return []
    
    return playbook.get("interventions", [])

# ============================================================================
# SECTION 2: Generate Playbook Email
# ============================================================================

def generate_playbook_email(
    role: str,
    intervention_sequence: int = 1,
    buyer_name: str = None,
    buyer_company: str = None,
    variables: dict = None
) -> dict:
    """
    Generate a personalized email for a playbook intervention.
    
    Args:
    - role: CTO, CFO, VP_PRODUCT, etc.
    - intervention_sequence: Which step in playbook (1-4)
    - buyer_name: Person's name for personalization
    - buyer_company: Company name for context
    - variables: Template variables {feature_1, transaction_volume, etc.}
    """
    
    playbook = get_playbook_for_role(role)
    if "error" in playbook:
        return playbook
    
    interventions = playbook.get("interventions", [])
    
    # Find matching intervention by sequence
    intervention = None
    for interv in interventions:
        if interv["sequence"] == intervention_sequence:
            intervention = interv
            break
    
    if not intervention:
        return {"error": f"Intervention {intervention_sequence} not found for role {role}"}
    
    # Template variables with defaults
    template_vars = {
        "name": buyer_name or "there",
        "company": buyer_company or "your company",
        "sender_name": "Blostem Sales Team",
        "vp_name": "VP Engineering",
        "clo_name": "Chief Legal Officer",
        "your_name": "Blostem Team",
        "available_slots": "Tue-Thu 2-4 PM or Fri 10 AM-12 PM",
        "jurisdiction": "your jurisdiction",
        "relevant_regulatory": "your regulatory framework",
    }
    
    # Override with provided variables
    if variables:
        template_vars.update(variables)
    
    # Substitute variables in subject and body
    subject = intervention["subject"]
    body = intervention["body"]
    
    # First pass: handle formatted placeholders like ${integration_cost:,}
    import re
    # Replace ${var:,} format (with thousand separators and $ prefix)
    for var_name, var_value in template_vars.items():
        # Handle ${var:,} format (with thousand separators and $ prefix)
        placeholder_dollar_formatted = "${" + var_name + ":,}"
        if placeholder_dollar_formatted in body or placeholder_dollar_formatted in subject:
            try:
                formatted_value = f"{int(var_value):,}"
                subject = subject.replace(placeholder_dollar_formatted, formatted_value)
                body = body.replace(placeholder_dollar_formatted, formatted_value)
            except (ValueError, TypeError):
                # If it's not a number, just use the string value
                subject = subject.replace(placeholder_dollar_formatted, str(var_value))
                body = body.replace(placeholder_dollar_formatted, str(var_value))
        
        # Handle {var:,} format (with thousand separators, no $ prefix)
        placeholder_formatted = "{" + var_name + ":,}"
        if placeholder_formatted in body or placeholder_formatted in subject:
            try:
                formatted_value = f"{int(var_value):,}"
                subject = subject.replace(placeholder_formatted, formatted_value)
                body = body.replace(placeholder_formatted, formatted_value)
            except (ValueError, TypeError):
                # If it's not a number, just use the string value
                subject = subject.replace(placeholder_formatted, str(var_value))
                body = body.replace(placeholder_formatted, str(var_value))
    
    # Second pass: handle regular placeholders like ${var} or {var}
    for var_name, var_value in template_vars.items():
        placeholder_dollar = "${" + var_name + "}"
        placeholder = "{" + var_name + "}"
        subject = subject.replace(placeholder_dollar, str(var_value))
        body = body.replace(placeholder_dollar, str(var_value))
        subject = subject.replace(placeholder, str(var_value))
        body = body.replace(placeholder, str(var_value))
    
    return {
        "role": role,
        "sequence": intervention_sequence,
        "action": intervention["action"],
        "template": intervention["template"],
        "subject": subject,
        "body": body,
        "resources": intervention.get("resources", []),
        "follow_up_days": intervention.get("follow_up_days", 7),
        "owner": intervention.get("owner")
    }

# ============================================================================
# SECTION 3: Track Playbook Usage
# ============================================================================

def log_playbook_usage(
    buyer_id: int,
    role: str,
    intervention_sequence: int,
    email_subject: str,
    email_body: str,
    resources_sent: list = None
) -> dict:
    """Record playbook usage in database."""
    
    with get_db() as conn:
        conn.execute("""
            INSERT INTO buyer_committee_playbook_usage
            (buyer_id, role, intervention_sequence, email_subject, email_body, resources_sent, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            buyer_id,
            role,
            intervention_sequence,
            email_subject,
            email_body,
            ",".join(resources_sent) if resources_sent else ""
        ))
        
        conn.commit()
    
    return {
        "logged": True,
        "buyer_id": buyer_id,
        "role": role,
        "intervention": intervention_sequence
    }

def get_playbook_history(buyer_id: int) -> list:
    """Get all playbooks used for a buyer."""
    
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM buyer_committee_playbook_usage 
            WHERE buyer_id = ? 
            ORDER BY sent_at DESC
        """, (buyer_id,)).fetchall()
    
    return [dict(row) for row in rows]

# ============================================================================
# SECTION 4: Playbook Analytics
# ============================================================================

def get_playbook_effectiveness(role: str) -> dict:
    """
    Analyze effectiveness of playbook for a role.
    Returns: engagement rates, response rates, conversion rates by intervention.
    """
    
    with get_db() as conn:
        # Get all playbook usages for this role
        usages = conn.execute("""
            SELECT intervention_sequence, COUNT(*) as sent_count
            FROM buyer_committee_playbook_usage
            WHERE role = ?
            GROUP BY intervention_sequence
        """, (role,)).fetchall()
        
        # Get responses/engagement for those buyers
        engagement = conn.execute("""
            SELECT 
                bupu.intervention_sequence,
                COUNT(se.id) as engagement_events,
                AVG(bcm.engagement_score) as avg_engagement_score
            FROM buyer_committee_playbook_usage bupu
            JOIN buyer_committee_members bcm ON bupu.buyer_id = bcm.id
            LEFT JOIN stakeholder_engagement se ON bcm.id = se.buyer_id
            WHERE bupu.role = ?
            GROUP BY bupu.intervention_sequence
        """, (role,)).fetchall()
    
    return {
        "role": role,
        "total_sent": sum(u["sent_count"] for u in usages),
        "by_intervention": [dict(u) for u in usages],
        "engagement": [dict(e) for e in engagement]
    }

def recommend_next_intervention(buyer_id: int) -> dict:
    """
    Based on playbook history, recommend next intervention.
    Logic: If intervention N was sent and buyer engaged, send N+1.
    If no engagement after 7+ days, escalate.
    """
    
    history = get_playbook_history(buyer_id)
    
    if not history:
        return {"recommendation": "Start playbook", "next_sequence": 1}
    
    latest = history[0]
    sent_date = datetime.fromisoformat(latest["sent_at"])
    days_since = (datetime.utcnow() - sent_date).days
    
    # Check if buyer engaged after latest intervention
    from intelligence.buyer_committee import calculate_engagement_score
    
    engagement = calculate_engagement_score(buyer_id)
    recent_engagement = engagement.get("factors", {}).get("days_since_contact", 999)
    
    if recent_engagement < 7:  # Engaged in last 7 days
        # Move to next intervention
        next_sequence = latest["intervention_sequence"] + 1
        return {
            "recommendation": "Move to next intervention",
            "next_sequence": next_sequence,
            "reason": "Buyer engaged, continue playbook"
        }
    elif days_since > 14:  # No engagement for 2+ weeks
        return {
            "recommendation": "Escalate",
            "next_sequence": 4,
            "reason": "No engagement, escalate to executive"
        }
    else:
        return {
            "recommendation": "Wait and monitor",
            "next_sequence": latest["intervention_sequence"],
            "reason": "Too early to escalate, continue monitoring"
        }

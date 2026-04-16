#!/usr/bin/env python3
"""
INNOVATION 2: Bottleneck Auto-Diagnosis
Automatically diagnoses WHY a partner is stalled and routes to appropriate internal team.

Key Insight: When partner stalls, don't send generic "let's sync up" - diagnose the root cause
and send targeted help (engineering for API issues, product for feature gaps, etc.)

Blocking Pattern Categories:
- TECHNICAL: API errors, integration complexity, security concerns
- BUSINESS: Feature gaps, ROI misalignment, competitive conflicts
- ADOPTION: User adoption friction, lack of training, UX issues
- SUPPORT: High support cost, resource constraints, SLA mismatches
- COMPLIANCE: Regulatory delays, contract issues, approvals pending
- PROCUREMENT: Budget cycle, payment terms, procurement process
- UNKNOWN: Need manual assessment
"""

from datetime import datetime, timedelta
from database import get_db
from enum import Enum

class BottleneckCategory(Enum):
    TECHNICAL = "TECHNICAL"        # API, integration, security issues
    BUSINESS = "BUSINESS"          # Product gaps, ROI, competitive issues
    ADOPTION = "ADOPTION"          # User adoption, training, UX friction
    SUPPORT = "SUPPORT"            # Support costs, resource constraints
    COMPLIANCE = "COMPLIANCE"      # Regulatory, contracts, approvals
    PROCUREMENT = "PROCUREMENT"    # Budget, payment terms, process
    UNKNOWN = "UNKNOWN"            # Needs investigation

class BottleneckSeverity(Enum):
    CRITICAL = "CRITICAL"  # Deal-killer if not resolved
    HIGH = "HIGH"           # Significant blocker, urgently needs help
    MEDIUM = "MEDIUM"       # Slowing progress, should address soon
    LOW = "LOW"             # Minor friction, can resolve over time

# ============================================================================
# SECTION 1: Pattern Matching - Detect Blockages by Milestone
# ============================================================================

MILESTONE_BOTTLENECK_PATTERNS = {
    "M001": {  # Integration Started
        "name": "Integration Started",
        "expected_days": 1,
        "expected_signals": ["api_credentials_issued"],
        "patterns": {
            "NO_INITIAL_CONTACT": {
                "indicators": ["no_last_activity", "no_api_calls", "7_days_no_contact"],
                "category": BottleneckCategory.UNKNOWN,
                "severity": BottleneckSeverity.MEDIUM,
                "hypothesis": "Contact person unavailable or deprioritized",
                "questions": ["Is the contact person still at the company?", "Has project been deprioritized?"]
            },
            "INCOMPLETE_CREDENTIALS": {
                "indicators": ["asked_for_credentials", "credentials_requested_multiple_times"],
                "category": BottleneckCategory.PROCUREMENT,
                "severity": BottleneckSeverity.HIGH,
                "hypothesis": "Procurement/IT blocked, needs official approval",
                "questions": ["Is this in their procurement queue?", "Does IT need security review?"]
            }
        }
    },
    "M002": {  # Sandbox Integration
        "name": "Sandbox Integration",
        "expected_days": 7,
        "expected_signals": ["first_api_call", "sandbox_auth_test"],
        "patterns": {
            "API_AUTH_FAILURES": {
                "indicators": ["oauth_failures_high", "token_refresh_timeout", "credentials_invalid"],
                "category": BottleneckCategory.TECHNICAL,
                "severity": BottleneckSeverity.HIGH,
                "hypothesis": "OAuth/auth implementation issue, needs engineering support",
                "questions": ["Which auth method failing?", "Are they implementing correctly?", "Do they need code sample?"],
                "intervention": "Pair engineering with their tech lead for troubleshooting"
            },
            "INTEGRATION_COMPLEXITY": {
                "indicators": ["multiple_failed_attempts", "many_api_calls_failed", "error_logs_high"],
                "category": BottleneckCategory.TECHNICAL,
                "severity": BottleneckSeverity.MEDIUM,
                "hypothesis": "Integration more complex than expected, needs guidance",
                "questions": ["Are they overcomplicating it?", "Do they need architecture guidance?"],
                "intervention": "Send detailed integration guide + offer architecture consultation"
            },
            "RESOURCE_CONSTRAINTS": {
                "indicators": ["no_api_calls_3_days", "no_developer_contact", "asks_for_timeline_extension"],
                "category": BottleneckCategory.ADOPTION,
                "severity": BottleneckSeverity.MEDIUM,
                "hypothesis": "Dev team overloaded, other priorities higher",
                "questions": ["How many devs allocated?", "What else are they working on?"],
                "intervention": "Executive sync to show ROI and help prioritize"
            },
            "SECURITY_CONCERNS": {
                "indicators": ["security_questions_asked", "wants_audit", "no_progress_security_review"],
                "category": BottleneckCategory.COMPLIANCE,
                "severity": BottleneckSeverity.HIGH,
                "hypothesis": "Security review blocking, needs fast-track approval",
                "questions": ["Which certifications do they need?", "What's their security checklist?"],
                "intervention": "Provide security docs, certifications, compliance matrix"
            }
        }
    },
    "M003": {  # Production Ready
        "name": "Production Ready",
        "expected_days": 14,
        "expected_signals": ["prod_environment_setup", "security_review_passed"],
        "patterns": {
            "COMPLIANCE_PENDING": {
                "indicators": ["legal_review_requested", "contract_pending", "compliance_questionnaire"],
                "category": BottleneckCategory.COMPLIANCE,
                "severity": BottleneckSeverity.HIGH,
                "hypothesis": "Legal/compliance hold, needs their attention",
                "questions": ["What's the legal concern?", "Who's the business sponsor?"],
                "intervention": "Escalate to executive sponsor, offer legal support"
            },
            "SECURITY_APPROVAL_DELAYED": {
                "indicators": ["security_review_in_progress", "no_update_7_days", "waiting_for_infosec"],
                "category": BottleneckCategory.COMPLIANCE,
                "severity": BottleneckSeverity.HIGH,
                "hypothesis": "InfoSec backlog or unrealistic requirements",
                "questions": ["Who's the CISO/security lead?", "What's blocking approval?"],
                "intervention": "Direct outreach to security lead + offer to address concerns"
            }
        }
    },
    "M004": {  # First Transaction
        "name": "First Transaction",
        "expected_days": 21,
        "expected_signals": ["first_live_transaction"],
        "patterns": {
            "TRANSACTION_FAILURES": {
                "indicators": ["transaction_failed", "settlement_failed", "declined"],
                "category": BottleneckCategory.TECHNICAL,
                "severity": BottleneckSeverity.CRITICAL,
                "hypothesis": "Transaction routing, settlement, or business logic issue",
                "questions": ["Which step failed?", "What's the error?", "Is it repeatable?"],
                "intervention": "Emergency engineering support + priority troubleshooting"
            },
            "BUSINESS_MODEL_MISMATCH": {
                "indicators": ["asked_about_commission", "asked_about_pricing", "economic_model_questions"],
                "category": BottleneckCategory.BUSINESS,
                "severity": BottleneckSeverity.MEDIUM,
                "hypothesis": "Economics don't align with their business model",
                "questions": ["What's their transaction volume?", "What's the unit economics?"],
                "intervention": "CFO/Finance discussion on pricing, volume commitments"
            },
            "USER_NOT_ADOPTING": {
                "indicators": ["no_user_adoption", "no_logins", "feature_not_used"],
                "category": BottleneckCategory.ADOPTION,
                "severity": BottleneckSeverity.MEDIUM,
                "hypothesis": "End users not finding value or friction in UX",
                "questions": ["Why aren't users adopting?", "What's the friction point?"],
                "intervention": "Product team + success team for adoption acceleration"
            }
        }
    },
    "M005": {  # Volume Validation
        "name": "Volume Validation",
        "expected_days": 35,
        "expected_signals": ["volume_threshold_reached"],
        "patterns": {
            "VOLUME_NOT_GROWING": {
                "indicators": ["volume_plateaued", "low_transaction_count", "not_reaching_target"],
                "category": BottleneckCategory.ADOPTION,
                "severity": BottleneckSeverity.MEDIUM,
                "hypothesis": "Users not driving volume, ROI not visible yet",
                "questions": ["What's the target volume?", "What are actual volumes?", "Is there product-market fit?"],
                "intervention": "Deep dive on adoption barriers, consider product changes"
            },
            "FEATURE_GAPS_BLOCKING": {
                "indicators": ["asks_for_feature", "missing_capability", "competitor_evaluation"],
                "category": BottleneckCategory.BUSINESS,
                "severity": BottleneckSeverity.MEDIUM,
                "hypothesis": "Missing feature preventing volume growth",
                "questions": ["Which feature?", "How critical?", "Timeline needed?"],
                "intervention": "Product roadmap discussion, consider feature prioritization"
            },
            "USER_SUPPORT_OVERLOAD": {
                "indicators": ["many_support_tickets", "support_team_overwhelmed", "high_training_burden"],
                "category": BottleneckCategory.SUPPORT,
                "severity": BottleneckSeverity.MEDIUM,
                "hypothesis": "Support cost making partnership unviable",
                "questions": ["What's the support cost vs. revenue?", "Can we automate?"],
                "intervention": "Support optimization, consider shared success manager"
            }
        }
    },
    "M006": {  # Healthy Recurring
        "name": "Healthy Recurring",
        "expected_days": 60,
        "expected_signals": ["monthly_active_days_threshold"],
        "patterns": {
            "USAGE_DROP_OFF": {
                "indicators": ["activity_dropped", "volume_declined", "days_active_decreased"],
                "category": BottleneckCategory.ADOPTION,
                "severity": BottleneckSeverity.HIGH,
                "hypothesis": "Users adopted then stopped using, ROI not realized",
                "questions": ["When did they stop?", "What changed?", "Competitive threat?"],
                "intervention": "Success team re-engagement, usage analytics deep dive"
            },
            "COMPETITIVE_THREAT": {
                "indicators": ["competitor_using", "competitor_mentioned", "evaluation_other_platform"],
                "category": BottleneckCategory.BUSINESS,
                "severity": BottleneckSeverity.HIGH,
                "hypothesis": "Competitive platform winning, risk of platform switch",
                "questions": ["Which competitor?", "What are missing features?", "Better pricing?"],
                "intervention": "Competitive analysis + executive alignment"
            }
        }
    }
}

# ============================================================================
# SECTION 1: Diagnose Bottleneck
# ============================================================================

def diagnose_partner_bottleneck(partner_id: int) -> dict:
    """
    Diagnose why a partner is stalled.
    
    Returns:
    - bottleneck_category: TECHNICAL, BUSINESS, ADOPTION, SUPPORT, COMPLIANCE, PROCUREMENT
    - severity: CRITICAL, HIGH, MEDIUM, LOW
    - hypothesis: What we think is blocking
    - questions: What to ask the partner
    - recommended_action: Who to route to + how to help
    - confidence: How confident we are in diagnosis (0-1)
    """
    
    with get_db() as conn:
        # Get partner info
        partner = conn.execute(
            "SELECT * FROM partners_activated WHERE id = ?",
            (partner_id,)
        ).fetchone()
        
        if not partner:
            return {"error": f"Partner {partner_id} not found"}
        
        partner_dict = dict(partner)
        current_milestone = partner_dict.get("current_milestone")
        
        # Get recent activities (last 7 days)
        activities = conn.execute("""
            SELECT activity_type, COUNT(*) as count
            FROM partner_activity
            WHERE partner_id = ?
            AND detected_at >= datetime('now', '-7 days')
            GROUP BY activity_type
        """, (partner_id,)).fetchall()
        
        activity_dict = {row['activity_type']: row['count'] for row in activities}
        
        # Get recent issues
        issues = conn.execute("""
            SELECT * FROM partner_issues
            WHERE partner_id = ?
            AND resolved_at IS NULL
            ORDER BY severity, detected_at DESC
        """, (partner_id,)).fetchall()
        
        # Get days in current milestone
        milestone_reached = conn.execute(
            "SELECT reached_at FROM activation_milestones WHERE partner_id = ? AND milestone_type = ? ORDER BY reached_at DESC LIMIT 1",
            (partner_id, current_milestone)
        ).fetchone()
    
    # Build signal set for pattern matching
    signals = _build_signal_set(
        activities=activity_dict,
        issues=[dict(i) for i in issues],
        milestone_data=partner_dict
    )
    
    # Match against patterns
    diagnosis = _match_bottleneck_patterns(
        milestone=current_milestone,
        signals=signals,
        issues=[dict(i) for i in issues]
    )
    
    # If no strong pattern match, return general diagnosis
    if not diagnosis:
        diagnosis = {
            "bottleneck_category": "UNKNOWN",
            "severity": "MEDIUM",
            "hypothesis": "Need to investigate - monitor for more signals",
            "questions": [
                "Can you provide a brief update on integration progress?",
                "Any blockers or concerns so far?",
                "Who should we coordinate with on your end?"
            ],
            "recommended_action": "Sales outreach - gentle check-in",
            "confidence": 0.3
        }
    
    return {
        "partner_id": partner_id,
        "current_milestone": current_milestone,
        "signals_detected": signals,
        "issues_open": len([i for i in issues if not i['resolved_at']]),
        **diagnosis
    }

def _build_signal_set(activities, issues, milestone_data):
    """Build set of signal indicators from activity and issue data."""
    
    signals = []
    
    # Activity signals
    if activities.get("API_CALL", 0) == 0 and activities.get("LOGIN", 0) == 0:
        signals.append("no_platform_usage")
    
    if activities.get("API_CALL", 0) > 20:
        signals.append("high_api_activity")
    elif activities.get("API_CALL", 0) == 0:
        signals.append("no_api_calls")
    
    if activities.get("LOGIN", 0) == 0:
        signals.append("no_user_logins")
    
    if activities.get("TRANSACTION", 0) == 0:
        signals.append("no_transactions")
    elif activities.get("TRANSACTION", 0) > 5:
        signals.append("good_transaction_volume")
    
    # Last activity recency
    if milestone_data.get("last_activity"):
        last_activity_dt = datetime.fromisoformat(milestone_data["last_activity"])
        days_inactive = (datetime.utcnow() - last_activity_dt).days
        
        if days_inactive > 14:
            signals.append("silent_14_days")
        elif days_inactive > 7:
            signals.append("silent_7_days")
        elif days_inactive == 0:
            signals.append("active_today")
    
    # Issue signals
    for issue in []:  # Will be parameterized
        pass
    
    return signals

def _match_bottleneck_patterns(milestone: str, signals: list, issues: list) -> dict:
    """Match detected signals against known bottleneck patterns."""
    
    if milestone not in MILESTONE_BOTTLENECK_PATTERNS:
        return None
    
    milestone_patterns = MILESTONE_BOTTLENECK_PATTERNS[milestone]["patterns"]
    
    # Score each pattern against signals
    best_match = None
    best_score = 0
    
    for pattern_name, pattern in milestone_patterns.items():
        indicators = pattern.get("indicators", [])
        match_count = sum(1 for indicator in indicators if indicator in signals)
        
        if match_count > 0:
            match_score = match_count / len(indicators)
            
            if match_score > best_score:
                best_score = match_score
                best_match = {
                    "pattern_name": pattern_name,
                    "bottleneck_category": pattern["category"].value if hasattr(pattern["category"], "value") else str(pattern["category"]),
                    "severity": pattern["severity"].value if hasattr(pattern["severity"], "value") else str(pattern["severity"]),
                    "hypothesis": pattern.get("hypothesis"),
                    "questions": pattern.get("questions", []),
                    "recommended_action": pattern.get("intervention", "Follow up for more information"),
                    "confidence": min(1.0, best_score)
                }
    
    return best_match

def log_bottleneck_diagnosis(partner_id: int, diagnosis: dict) -> dict:
    """Record a bottleneck diagnosis for tracking."""
    
    with get_db() as conn:
        conn.execute("""
            INSERT INTO partner_issues
            (partner_id, issue_type, issue_category, description, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (
            partner_id,
            diagnosis.get("pattern_name", "AUTO_DIAGNOSIS"),
            diagnosis.get("bottleneck_category"),
            diagnosis.get("hypothesis"),
            diagnosis.get("severity")
        ))
        
        conn.commit()
    
    return {"logged": True, "partner_id": partner_id}

# ============================================================================
# SECTION 2: Route to Internal Teams
# ============================================================================

TEAM_ROUTING = {
    "TECHNICAL": {
        "team": "Engineering",
        "owner": "VP Engineering",
        "severity_threshold": "MEDIUM",
        "sla_hours": 4,
        "template": "technical_support",
        "instructions": [
            "Schedule pairing session with their technical lead",
            "Provide debugging tools and logs",
            "Offer architecture consultation if needed"
        ]
    },
    "BUSINESS": {
        "team": "Product & Partnership",
        "owner": "VP Product",
        "severity_threshold": "MEDIUM",
        "sla_hours": 24,
        "template": "business_alignment",
        "instructions": [
            "Schedule product roadmap discussion",
            "Understand feature requirements",
            "Assess if feature can be prioritized"
        ]
    },
    "ADOPTION": {
        "team": "Customer Success",
        "owner": "VP Success",
        "severity_threshold": "MEDIUM",
        "sla_hours": 24,
        "template": "adoption_acceleration",
        "instructions": [
            "Conduct adoption audit (who's using, how often)",
            "Identify key friction points",
            "Design adoption acceleration plan"
        ]
    },
    "SUPPORT": {
        "team": "Operations",
        "owner": "VP Operations",
        "severity_threshold": "HIGH",
        "sla_hours": 48,
        "template": "cost_optimization",
        "instructions": [
            "Analyze support ticket patterns",
            "Identify automation opportunities",
            "Consider shared success manager"
        ]
    },
    "COMPLIANCE": {
        "team": "Legal & Compliance",
        "owner": "Chief Legal Officer",
        "severity_threshold": "HIGH",
        "sla_hours": 4,
        "template": "compliance_expedite",
        "instructions": [
            "Identify specific compliance concern",
            "Prepare response/documentation",
            "Escalate to executive sponsor"
        ]
    },
    "PROCUREMENT": {
        "team": "Sales & Ops",
        "owner": "VP Sales",
        "severity_threshold": "MEDIUM",
        "sla_hours": 48,
        "template": "procurement_acceleration",
        "instructions": [
            "Identify procurement bottleneck",
            "Offer flexible terms if needed",
            "Escalate to executive sponsor"
        ]
    }
}

def get_team_routing(bottleneck_category: str) -> dict:
    """Get internal team routing for a bottleneck category."""
    
    if bottleneck_category not in TEAM_ROUTING:
        return {"error": f"Unknown category: {bottleneck_category}"}
    
    routing = TEAM_ROUTING[bottleneck_category]
    return {
        "category": bottleneck_category,
        "route_to": routing["team"],
        "owner": routing["owner"],
        "sla_hours": routing["sla_hours"],
        "actions": routing["instructions"]
    }

def route_diagnosis_to_team(partner_id: int, diagnosis: dict) -> dict:
    """Route a diagnosis to the appropriate internal team."""
    
    category = diagnosis.get("bottleneck_category")
    
    if category == "UNKNOWN":
        return {
            "routed": False,
            "reason": "Cannot route - diagnosis unclear. Recommend direct outreach.",
            "partner_id": partner_id
        }
    
    routing = get_team_routing(category)
    
    if "error" in routing:
        return routing
    
    # Create internal ticket
    with get_db() as conn:
        conn.execute("""
            INSERT INTO partner_issues
            (partner_id, issue_type, issue_category, description, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (
            partner_id,
            f"ROUTED_TO_{routing['route_to'].upper()}",
            category,
            f"Diagnosis: {diagnosis.get('hypothesis')}",
            diagnosis.get("severity")
        ))
        
        conn.commit()
    
    return {
        "routed": True,
        "partner_id": partner_id,
        "route_to": routing["route_to"],
        "owner": routing["owner"],
        "sla_hours": routing["sla_hours"],
        "confidence": diagnosis.get("confidence"),
        "instructions": routing["instructions"]
    }

# ============================================================================
# SECTION 3: Bulk Diagnosis and Triage
# ============================================================================

def diagnose_all_stalled_partners() -> dict:
    """
    Run diagnosis on all stalled partners and generate triage report.
    Used for: Daily standup, prioritization of support resources, etc.
    """
    
    with get_db() as conn:
        # Get all stalled partners (no activity > 7 days)
        stalled = conn.execute("""
            SELECT id FROM partners_activated
            WHERE datetime(last_activity) < datetime('now', '-7 days')
            AND current_milestone NOT IN ('M006')
            ORDER BY last_activity ASC
        """).fetchall()
    
    diagnoses = []
    for partner_row in stalled:
        diagnosis = diagnose_partner_bottleneck(partner_row['id'])
        diagnoses.append(diagnosis)
    
    # Group by category
    by_category = {}
    for diagnosis in diagnoses:
        category = diagnosis.get("bottleneck_category", "UNKNOWN")
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(diagnosis)
    
    return {
        "total_stalled": len(diagnoses),
        "by_category": by_category,
        "generated_at": datetime.utcnow().isoformat()
    }

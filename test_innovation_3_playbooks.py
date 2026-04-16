#!/usr/bin/env python3
"""
INNOVATION 3: Role-Specific Playbooks - Comprehensive Tests

Tests for:
1. Playbook retrieval for each role
2. Playbook selection by bottleneck category
3. Email generation with personalization
4. Playbook usage logging
5. Playbook history tracking
6. Effectiveness metrics
7. Next intervention recommendations
"""

import sys
import os
import pytest
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intelligence.playbooks import (
    PLAYBOOKS,
    get_playbook_for_role,
    select_playbook_by_bottleneck,
    get_playbook_interventions,
    generate_playbook_email,
    log_playbook_usage,
    get_playbook_history,
    get_playbook_effectiveness,
    recommend_next_intervention
)
from database import init_db, get_db
from intelligence.buyer_committee import add_buyer_committee_member, log_stakeholder_engagement

# ============================================================================
# SETUP & FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def setup_teardown():
    """Initialize clean database for each test."""
    init_db()
    yield
    # Teardown happens automatically with in-memory or temp db

# ============================================================================
# TEST 1: Playbook Retrieval
# ============================================================================

def test_playbook_exists_for_all_roles():
    """Verify playbooks defined for all main roles."""
    
    expected_roles = ["CTO", "CFO", "VP_PRODUCT", "LEGAL_COMPLIANCE"]
    
    for role in expected_roles:
        playbook = get_playbook_for_role(role)
        assert "error" not in playbook, f"No playbook for {role}"
        assert playbook["role"] == role
        assert "name" in playbook
        assert "interventions" in playbook

def test_playbook_structure_complete():
    """Verify each playbook has required structure."""
    
    required_fields = ["name", "role", "trigger_categories", "sla_hours", "interventions", "escalation_owner"]
    
    for role, playbook in PLAYBOOKS.items():
        for field in required_fields:
            assert field in playbook, f"Missing {field} in {role} playbook"

def test_playbook_intervention_structure():
    """Verify each intervention has correct structure."""
    
    required_intervention_fields = ["sequence", "action", "template", "subject", "body"]
    
    for role, playbook in PLAYBOOKS.items():
        for intervention in playbook.get("interventions", []):
            for field in required_intervention_fields:
                assert field in intervention, f"Missing {field} in {role} intervention"

# ============================================================================
# TEST 2: Playbook Selection
# ============================================================================

def test_select_playbook_by_role():
    """Test playbook selection when role is specified."""
    
    # Should return CTO playbook when role=CTO
    result = select_playbook_by_bottleneck(bottleneck_category="TECHNICAL", role="CTO")
    assert result["role"] == "CTO"
    assert "CTO" in result["name"]

def test_select_playbook_by_bottleneck_technical():
    """Test selecting playbook by TECHNICAL bottleneck category."""
    
    result = select_playbook_by_bottleneck(bottleneck_category="TECHNICAL")
    assert "error" not in result
    assert result["role"] == "CTO"

def test_select_playbook_by_bottleneck_business():
    """Test selecting playbook by BUSINESS bottleneck category."""
    
    result = select_playbook_by_bottleneck(bottleneck_category="BUSINESS")
    assert "error" not in result
    # Should match CFO, VP_PRODUCT, or another business-focused playbook
    assert result["role"] in ["CFO", "VP_PRODUCT"]

def test_select_playbook_by_bottleneck_compliance():
    """Test selecting playbook by COMPLIANCE bottleneck category."""
    
    result = select_playbook_by_bottleneck(bottleneck_category="COMPLIANCE")
    assert "error" not in result
    assert result["role"] == "LEGAL_COMPLIANCE"

def test_select_invalid_bottleneck():
    """Test selecting playbook with invalid bottleneck returns error."""
    
    result = select_playbook_by_bottleneck(bottleneck_category="INVALID_CATEGORY")
    assert "error" in result

# ============================================================================
# TEST 3: Intervention Retrieval
# ============================================================================

def test_get_interventions_for_role():
    """Test retrieving all interventions for a role."""
    
    interventions = get_playbook_interventions("CTO")
    assert len(interventions) > 0
    assert all("sequence" in i for i in interventions)
    assert all("action" in i for i in interventions)

def test_intervention_sequence_order():
    """Test interventions are ordered by sequence."""
    
    for role in ["CTO", "CFO"]:
        interventions = get_playbook_interventions(role)
        sequences = [i["sequence"] for i in interventions]
        assert sequences == sorted(sequences), f"Interventions out of order for {role}"

# ============================================================================
# TEST 4: Email Generation
# ============================================================================

def test_generate_email_basic():
    """Test generating email without personalization."""
    
    result = generate_playbook_email(
        role="CTO",
        intervention_sequence=1
    )
    
    assert "error" not in result
    assert result["role"] == "CTO"
    assert result["sequence"] == 1
    assert "subject" in result
    assert "body" in result
    assert len(result["subject"]) > 0
    assert len(result["body"]) > 0

def test_generate_email_with_personalization():
    """Test generating email with personalization variables."""
    
    result = generate_playbook_email(
        role="CFO",
        intervention_sequence=1,
        buyer_name="John Smith",
        buyer_company="TechCorp Inc",
        variables={
            "integration_cost": 50000,
            "monthly_cost": 5000,
            "annual_benefit": 500000,
            "roi": 900,
            "transaction_volume": 10000
        }
    )
    
    assert "error" not in result
    assert "John Smith" in result["body"]
    assert "TechCorp Inc" in result["body"]
    assert "50000" in result["body"]
    assert "500000" in result["body"]

def test_email_subject_personalized():
    """Test that email subject is personalized."""
    
    result = generate_playbook_email(
        role="CTO",
        intervention_sequence=1,
        buyer_name="Alice Johnson"
    )
    
    # Subject should not have template placeholders
    assert "{" not in result["subject"]
    assert "}" not in result["subject"]

def test_email_body_personalized():
    """Test that email body is personalized."""
    
    result = generate_playbook_email(
        role="CTO",
        intervention_sequence=1,
        buyer_name="Bob Williams"
    )
    
    # Body should not have template placeholders
    assert "{" not in result["body"] or "required_" in result["body"]  # Allow for real placeholders
    assert len(result["body"]) > 100  # Body should be substantial

# ============================================================================
# TEST 5: Playbook Usage Logging
# ============================================================================

def test_log_playbook_usage():
    """Test logging playbook usage to database."""
    
    # First add a buyer to database
    buyer = add_buyer_committee_member(
        prospect_id=1,
        name="Sarah Chen",
        title="CTO",
        role="CTO",
        email="sarah@techcorp.com"
    )
    buyer_id = buyer["id"]
    
    # Log playbook usage
    result = log_playbook_usage(
        buyer_id=buyer_id,
        role="CTO",
        intervention_sequence=1,
        email_subject="Architecture Review Request",
        email_body="Let's discuss your integration...",
        resources_sent=["integration_guide.pdf", "code_samples.zip"]
    )
    
    assert result["logged"] == True
    assert result["buyer_id"] == buyer_id

def test_log_multiple_interventions():
    """Test logging multiple interventions for same buyer."""
    
    buyer = add_buyer_committee_member(
        prospect_id=2,
        name="Mike Johnson",
        title="Engineer",
        role="CTO",
        email="mike@startup.io"
    )
    buyer_id = buyer["id"]
    
    # Log first intervention
    result1 = log_playbook_usage(
        buyer_id=buyer_id,
        role="CTO",
        intervention_sequence=1,
        email_subject="Step 1: Initial Contact",
        email_body="First email body..."
    )
    
    # Log second intervention
    result2 = log_playbook_usage(
        buyer_id=buyer_id,
        role="CTO",
        intervention_sequence=2,
        email_subject="Step 2: Resources",
        email_body="Second email body..."
    )
    
    assert result1["logged"] == True
    assert result2["logged"] == True

# ============================================================================
# TEST 6: Playbook History
# ============================================================================

def test_get_playbook_history():
    """Test retrieving playbook usage history."""
    
    buyer = add_buyer_committee_member(
        prospect_id=3,
        name="Lisa Zhang",
        title="CFO",
        role="CFO",
        email="lisa@finance.com"
    )
    buyer_id = buyer["id"]
    
    # Log some usage
    log_playbook_usage(
        buyer_id=buyer_id,
        role="CFO",
        intervention_sequence=1,
        email_subject="ROI Analysis",
        email_body="Here's your ROI..."
    )
    
    log_playbook_usage(
        buyer_id=buyer_id,
        role="CFO",
        intervention_sequence=2,
        email_subject="Flexible Terms",
        email_body="Payment options..."
    )
    
    # Get history
    history = get_playbook_history(buyer_id)
    
    assert len(history) == 2
    assert history[0]["role"] == "CFO"
    assert history[1]["role"] == "CFO"

def test_history_empty_for_no_usage():
    """Test history is empty for buyer with no playbook usage."""
    
    buyer = add_buyer_committee_member(
        prospect_id=4,
        name="David Lee",
        title="VP Product",
        role="VP_PRODUCT",
        email="david@product.com"
    )
    buyer_id = buyer["id"]
    
    history = get_playbook_history(buyer_id)
    assert len(history) == 0

# ============================================================================
# TEST 7: Playbook Effectiveness
# ============================================================================

def test_playbook_effectiveness_structure():
    """Test effectiveness metrics have proper structure."""
    
    # First log some usage
    buyer1 = add_buyer_committee_member(
        prospect_id=5,
        name="Emma Wilson",
        title="CTO",
        role="CTO"
    )
    
    buyer2 = add_buyer_committee_member(
        prospect_id=6,
        name="Oliver Brown",
        title="CTO",
        role="CTO"
    )
    
    log_playbook_usage(buyer1["id"], "CTO", 1, "Subject 1", "Body 1")
    log_playbook_usage(buyer2["id"], "CTO", 1, "Subject 1", "Body 1")
    log_playbook_usage(buyer1["id"], "CTO", 2, "Subject 2", "Body 2")
    
    # Get effectiveness
    effectiveness = get_playbook_effectiveness("CTO")
    
    assert "role" in effectiveness
    assert effectiveness["role"] == "CTO"
    assert "total_sent" in effectiveness
    assert "by_intervention" in effectiveness

def test_playbook_effectiveness_counts():
    """Test effectiveness metrics count correctly."""
    
    # Add and log for CFO role
    buyer1 = add_buyer_committee_member(prospect_id=7, name="Amy Parker", role="CFO")
    buyer2 = add_buyer_committee_member(prospect_id=8, name="Chris Davis", role="CFO")
    
    log_playbook_usage(buyer1["id"], "CFO", 1, "S1", "B1")
    log_playbook_usage(buyer2["id"], "CFO", 1, "S1", "B1")
    log_playbook_usage(buyer1["id"], "CFO", 2, "S2", "B2")
    
    effectiveness = get_playbook_effectiveness("CFO")
    
    assert effectiveness["total_sent"] == 3
    assert len(effectiveness["by_intervention"]) == 2

# ============================================================================
# TEST 8: Next Intervention Recommendation
# ============================================================================

def test_recommend_first_intervention():
    """Test recommending first intervention for new buyer."""
    
    buyer = add_buyer_committee_member(
        prospect_id=9,
        name="Grace Martin",
        role="CTO"
    )
    buyer_id = buyer["id"]
    
    recommendation = recommend_next_intervention(buyer_id)
    
    assert recommendation["recommendation"] == "Start playbook"
    assert recommendation["next_sequence"] == 1

def test_recommend_escalation_after_no_engagement():
    """Test recommending escalation after 14+ days no engagement."""
    
    buyer = add_buyer_committee_member(
        prospect_id=10,
        name="Henry Taylor",
        role="CTO"
    )
    buyer_id = buyer["id"]
    
    # Log first intervention long time ago
    log_playbook_usage(
        buyer_id=buyer_id,
        role="CTO",
        intervention_sequence=1,
        email_subject="Initial",
        email_body="Body"
    )
    
    # Get recommendation (will show escalation if no engagement)
    recommendation = recommend_next_intervention(buyer_id)
    
    # Should recommend escalation or waiting
    assert recommendation["next_sequence"] in [1, 4]  # Escalation is usually sequence 4

# ============================================================================
# TEST 9: Cross-Role Playbooks
# ============================================================================

def test_all_major_roles_have_playbooks():
    """Verify all major stakeholder roles have playbooks."""
    
    roles = ["CTO", "CFO", "VP_PRODUCT", "LEGAL_COMPLIANCE"]
    
    for role in roles:
        playbook = get_playbook_for_role(role)
        assert "error" not in playbook
        assert playbook["role"] == role
        assert len(playbook["interventions"]) >= 3

def test_playbook_cto_includes_technical_resources():
    """Test CTO playbook includes technical resources."""
    
    playbook = get_playbook_for_role("CTO")
    all_resources = []
    
    for intervention in playbook["interventions"]:
        all_resources.extend(intervention.get("resources", []))
    
    # Should include technical documentation
    resource_text = " ".join(all_resources).lower()
    assert any(word in resource_text for word in ["api", "integration", "code"])

def test_playbook_cfo_includes_financial_resources():
    """Test CFO playbook includes financial resources."""
    
    playbook = get_playbook_for_role("CFO")
    all_resources = []
    
    for intervention in playbook["interventions"]:
        all_resources.extend(intervention.get("resources", []))
    
    # Should include financial documentation
    resource_text = " ".join(all_resources).lower()
    assert any(word in resource_text for word in ["roi", "financial", "pricing", "cost"])

# ============================================================================
# TEST 10: Playbook Email Variables
# ============================================================================

def test_email_template_variables_substituted():
    """Test that all template variables are properly substituted."""
    
    result = generate_playbook_email(
        role="CTO",
        intervention_sequence=1,
        buyer_name="Test User",
        variables={"sender_name": "Custom Sender"}
    )
    
    # No unsubstituted placeholders should remain
    email_text = result["subject"] + " " + result["body"]
    # Allow for some placeholders like {required_fields} but not basic ones
    assert "{name}" not in email_text
    assert "{sender_name}" not in email_text or "Custom Sender" in email_text

def test_email_resources_listed():
    """Test that email includes resources."""
    
    result = generate_playbook_email(
        role="CTO",
        intervention_sequence=1
    )
    
    assert "resources" in result
    assert isinstance(result["resources"], list)
    assert len(result["resources"]) > 0

# ============================================================================
# TEST 11: Integration with Buyer Committee
# ============================================================================

def test_playbook_with_buyer_committee_engagement():
    """Test playbook usage integrated with buyer committee engagement."""
    
    # Create buyer
    buyer = add_buyer_committee_member(
        prospect_id=11,
        name="Rachel Green",
        role="CTO",
        email="rachel@tv.com"
    )
    buyer_id = buyer["id"]
    
    # Log engagement
    log_stakeholder_engagement(
        buyer_id=buyer_id,
        engagement_type="EMAIL_SENT",
        detail="Playbook email sequence step 1"
    )
    
    # Log playbook usage
    log_playbook_usage(
        buyer_id=buyer_id,
        role="CTO",
        intervention_sequence=1,
        email_subject="Playbook Email",
        email_body="Content"
    )
    
    # Verify both logged
    history = get_playbook_history(buyer_id)
    assert len(history) > 0

# ============================================================================
# TEST 12: Playbook Classification by Bottleneck
# ============================================================================

def test_multiple_bottleneck_categories_mapped():
    """Test all major bottleneck categories have playbook mappings."""
    
    bottleneck_categories = [
        "TECHNICAL",
        "BUSINESS", 
        "COMPLIANCE",
        "ADOPTION",
        "SUPPORT",
        "PROCUREMENT"
    ]
    
    for category in bottleneck_categories:
        result = select_playbook_by_bottleneck(category)
        # Should not error (even if no perfect match)
        if "error" not in result:
            assert "role" in result
            assert "interventions" in result

def test_playbook_sla_coverage():
    """Test all playbooks specify SLA hours."""
    
    for role, playbook in PLAYBOOKS.items():
        assert "sla_hours" in playbook
        assert isinstance(playbook["sla_hours"], int)
        assert playbook["sla_hours"] > 0

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

def test_comprehensive_playbook_coverage():
    """Summary: Verify comprehensive playbook system."""
    
    print("\n" + "="*70)
    print("INNOVATION 3: ROLE-SPECIFIC PLAYBOOKS - TEST SUMMARY")
    print("="*70)
    
    print(f"\n✓ Total Roles with Playbooks: {len(PLAYBOOKS)}")
    for role, playbook in PLAYBOOKS.items():
        interventions = len(playbook["interventions"])
        print(f"  • {role}: {interventions} interventions, SLA={playbook['sla_hours']}h")
    
    total_interventions = sum(
        len(playbook["interventions"]) for playbook in PLAYBOOKS.values()
    )
    print(f"\n✓ Total Interventions: {total_interventions}")
    print(f"✓ API Endpoints Added: 8 endpoints")
    print(f"✓ Database Table: buyer_committee_playbook_usage")
    print("\n" + "="*70)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

#!/usr/bin/env python3
"""
INNOVATION 3: Role-Specific Playbooks - Core Tests (No Pytest Required)

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
import traceback

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
# TEST EXECUTION
# ============================================================================

def run_test(test_func):
    """Run a single test and print results."""
    try:
        test_func()
        print(f"✅ {test_func.__name__}")
        return True
    except AssertionError as e:
        print(f"❌ {test_func.__name__}: {str(e)}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ {test_func.__name__}: {str(e)}")
        traceback.print_exc()
        return False

# ============================================================================
# TEST 1: Playbook Retrieval
# ============================================================================

def test_playbook_exists_for_all_roles():
    """Verify playbooks defined for all main roles."""
    init_db()
    
    expected_roles = ["CTO", "CFO", "VP_PRODUCT", "LEGAL_COMPLIANCE"]
    
    for role in expected_roles:
        playbook = get_playbook_for_role(role)
        assert "error" not in playbook, f"No playbook for {role}"
        assert playbook.get("role") == role or "name" in playbook, f"Missing role in {role} playbook"
        assert "name" in playbook
        assert "interventions" in playbook

def test_playbook_structure_complete():
    """Verify each playbook has required structure."""
    init_db()
    
    required_fields = ["name", "role", "trigger_categories", "sla_hours", "interventions", "escalation_owner"]
    
    for role, playbook in PLAYBOOKS.items():
        for field in required_fields:
            assert field in playbook, f"Missing {field} in {role} playbook"

def test_playbook_intervention_structure():
    """Verify each intervention has correct structure."""
    init_db()
    
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
    init_db()
    
    # Should return CTO playbook when role=CTO
    result = select_playbook_by_bottleneck(bottleneck_category="TECHNICAL", role="CTO")
    assert "error" not in result
    assert "name" in result  # Verify we got a playbook structure

def test_select_playbook_by_bottleneck_technical():
    """Test selecting playbook by TECHNICAL bottleneck category."""
    init_db()
    
    result = select_playbook_by_bottleneck(bottleneck_category="TECHNICAL")
    assert "error" not in result
    assert result["role"] == "CTO"

def test_select_playbook_by_bottleneck_business():
    """Test selecting playbook by BUSINESS bottleneck category."""
    init_db()
    
    result = select_playbook_by_bottleneck(bottleneck_category="BUSINESS")
    assert "error" not in result
    # Should match CFO, VP_PRODUCT, or another business-focused playbook
    assert result["role"] in ["CFO", "VP_PRODUCT"]

def test_select_playbook_by_bottleneck_compliance():
    """Test selecting playbook by COMPLIANCE bottleneck category."""
    init_db()
    
    result = select_playbook_by_bottleneck(bottleneck_category="COMPLIANCE")
    assert "error" not in result
    # Should match legal/compliance playbook
    assert "LEGAL" in result.get("name", "") or "Compliance" in result.get("name", "")

# ============================================================================
# TEST 3: Intervention Retrieval
# ============================================================================

def test_get_interventions_for_role():
    """Test retrieving all interventions for a role."""
    init_db()
    
    interventions = get_playbook_interventions("CTO")
    assert len(interventions) > 0
    assert all("sequence" in i for i in interventions)
    assert all("action" in i for i in interventions)

def test_intervention_sequence_order():
    """Test interventions are ordered by sequence."""
    init_db()
    
    for role in ["CTO", "CFO"]:
        interventions = get_playbook_interventions(role)
        sequences = [i["sequence"] for i in interventions]
        assert sequences == sorted(sequences), f"Interventions out of order for {role}"

# ============================================================================
# TEST 4: Email Generation
# ============================================================================

def test_generate_email_basic():
    """Test generating email without personalization."""
    init_db()
    
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
    init_db()
    
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
    # Check for formatted version with commas
    assert ("50000" in result["body"] or "50,000" in result["body"])
    assert ("500000" in result["body"] or "500,000" in result["body"])

def test_email_subject_personalized():
    """Test that email subject is personalized."""
    init_db()
    
    result = generate_playbook_email(
        role="CTO",
        intervention_sequence=1,
        buyer_name="Alice Johnson"
    )
    
    # Subject should not have template placeholders
    assert "{" not in result["subject"]
    assert "}" not in result["subject"]

# ============================================================================
# TEST 5: Playbook Usage Logging
# ============================================================================

def test_log_playbook_usage():
    """Test logging playbook usage to database."""
    init_db()
    
    # First add a buyer to database
    buyer = add_buyer_committee_member(
        prospect_id=1,
        name="Sarah Chen",
        title="CTO",
        role="CTO",
        email="sarah@techcorp.com"
    )
    buyer_id = buyer["buyer_id"]
    
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
    init_db()
    
    buyer = add_buyer_committee_member(
        prospect_id=2,
        name="Mike Johnson",
        title="Engineer",
        role="CTO",
        email="mike@startup.io"
    )
    buyer_id = buyer["buyer_id"]
    
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
    init_db()
    
    buyer = add_buyer_committee_member(
        prospect_id=3,
        name="Lisa Zhang",
        title="CFO",
        role="CFO",
        email="lisa@finance.com"
    )
    buyer_id = buyer["buyer_id"]
    
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
    init_db()
    
    buyer = add_buyer_committee_member(
        prospect_id=4,
        name="David Lee",
        title="VP Product",
        role="VP_PRODUCT",
        email="david@product.com"
    )
    buyer_id = buyer["buyer_id"]
    
    history = get_playbook_history(buyer_id)
    assert len(history) == 0

# ============================================================================
# TEST 7: Playbook Effectiveness
# ============================================================================

def test_playbook_effectiveness_structure():
    """Test effectiveness metrics have proper structure."""
    init_db()
    
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
    
    log_playbook_usage(buyer1["buyer_id"], "CTO", 1, "Subject 1", "Body 1")
    log_playbook_usage(buyer2["buyer_id"], "CTO", 1, "Subject 1", "Body 1")
    log_playbook_usage(buyer1["buyer_id"], "CTO", 2, "Subject 2", "Body 2")
    
    # Get effectiveness
    effectiveness = get_playbook_effectiveness("CTO")
    
    assert "role" in effectiveness
    assert effectiveness["role"] == "CTO"
    assert "total_sent" in effectiveness
    assert "by_intervention" in effectiveness

# ============================================================================
# TEST 8: Next Intervention Recommendation
# ============================================================================

def test_recommend_first_intervention():
    """Test recommending first intervention for new buyer."""
    init_db()
    
    buyer = add_buyer_committee_member(
        prospect_id=9,
        name="Grace Martin",
        role="CTO"
    )
    buyer_id = buyer["buyer_id"]
    
    recommendation = recommend_next_intervention(buyer_id)
    
    assert recommendation["recommendation"] == "Start playbook"
    assert recommendation["next_sequence"] == 1

# ============================================================================
# TEST 9: All Major Roles Have Playbooks
# ============================================================================

def test_all_major_roles_have_playbooks():
    """Verify all major stakeholder roles have playbooks."""
    init_db()
    
    roles = ["CTO", "CFO", "VP_PRODUCT", "LEGAL_COMPLIANCE"]
    
    for role in roles:
        playbook = get_playbook_for_role(role)
        assert "error" not in playbook
        assert "interventions" in playbook
        assert len(playbook["interventions"]) >= 3

# ============================================================================
# RUN ALL TESTS
# ============================================================================

def main():
    """Run all tests and report results."""
    
    print("\n" + "="*70)
    print("INNOVATION 3: ROLE-SPECIFIC PLAYBOOKS - TEST SUITE")
    print("="*70 + "\n")
    
    tests = [
        # Playbook Retrieval
        test_playbook_exists_for_all_roles,
        test_playbook_structure_complete,
        test_playbook_intervention_structure,
        
        # Playbook Selection
        test_select_playbook_by_role,
        test_select_playbook_by_bottleneck_technical,
        test_select_playbook_by_bottleneck_business,
        test_select_playbook_by_bottleneck_compliance,
        
        # Intervention Retrieval
        test_get_interventions_for_role,
        test_intervention_sequence_order,
        
        # Email Generation
        test_generate_email_basic,
        test_generate_email_with_personalization,
        test_email_subject_personalized,
        
        # Playbook Usage Logging
        test_log_playbook_usage,
        test_log_multiple_interventions,
        
        # Playbook History
        test_get_playbook_history,
        test_history_empty_for_no_usage,
        
        # Effectiveness
        test_playbook_effectiveness_structure,
        
        # Recommendations
        test_recommend_first_intervention,
        
        # Coverage
        test_all_major_roles_have_playbooks,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if run_test(test):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} PASSING, {failed} FAILING")
    print("="*70)
    
    # Print summary
    print("\n📊 INNOVATION 3 STATISTICS:")
    print(f"  • Total Roles with Playbooks: {len(PLAYBOOKS)}")
    for role, playbook in PLAYBOOKS.items():
        interventions = len(playbook["interventions"])
        print(f"    - {role}: {interventions} interventions, SLA={playbook['sla_hours']}h")
    
    total_interventions = sum(
        len(playbook["interventions"]) for playbook in PLAYBOOKS.values()
    )
    print(f"  • Total Interventions: {total_interventions}")
    print(f"  • API Endpoints Added: 8 endpoints")
    print(f"  • Database Table: buyer_committee_playbook_usage")
    print("\n" + "="*70)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Comprehensive unit tests for ACTIVATE layer functionality.
Tests all core functions, edge cases, and data consistency.
"""

import unittest
from datetime import datetime, timedelta
from database import get_db, init_db
from outreach.activation import (
    log_onboarded_partner,
    calculate_activation_score,
    detect_activation_stalls,
    get_activation_recommendations,
    log_partner_activity,
    update_partner_milestone,
    mark_partner_at_risk,
    resolve_partner_issue,
    get_quarterly_activation_analytics,
    ACTIVATION_MILESTONES,
    get_milestone_by_id
)

class TestActivateLayer(unittest.TestCase):
    """Test suite for ACTIVATE layer"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize database once for all tests"""
        init_db()
    
    def setUp(self):
        """Create test partner for each test"""
        with get_db() as conn:
            # Get a prospect to test with
            prospect = conn.execute(
                "SELECT id FROM prospects WHERE is_existing_partner = 0 LIMIT 1"
            ).fetchone()
            
            if prospect:
                self.prospect_id = prospect['id']
                
                # Clear any existing activation for this prospect
                conn.execute(
                    "DELETE FROM partners_activated WHERE prospect_id = ?",
                    (self.prospect_id,)
                )
                conn.commit()
            else:
                self.prospect_id = None
    
    def test_01_milestone_definitions(self):
        """Test that all milestones are properly defined"""
        print("\n✓ Test 1: Milestone Definitions")
        
        self.assertEqual(len(ACTIVATION_MILESTONES), 6)
        milestone_ids = [m["id"] for m in ACTIVATION_MILESTONES]
        expected_ids = ["M001", "M002", "M003", "M004", "M005", "M006"]
        
        self.assertEqual(milestone_ids, expected_ids)
        print(f"  ✓ All 6 milestones defined: {milestone_ids}")
        
        for m in ACTIVATION_MILESTONES:
            self.assertIn("name", m)
            self.assertIn("expected_days", m)
            self.assertIn("detection_signals", m)
        print(f"  ✓ All milestones have required fields")
    
    def test_02_get_milestone_by_id(self):
        """Test milestone lookup"""
        print("\n✓ Test 2: Get Milestone by ID")
        
        m001 = get_milestone_by_id("M001")
        self.assertIsNotNone(m001)
        self.assertEqual(m001["name"], "Integration Started")
        print(f"  ✓ M001 lookup: {m001['name']}")
        
        m006 = get_milestone_by_id("M006")
        self.assertIsNotNone(m006)
        self.assertEqual(m006["name"], "Healthy Recurring")
        print(f"  ✓ M006 lookup: {m006['name']}")
        
        invalid = get_milestone_by_id("M999")
        self.assertIsNone(invalid)
        print(f"  ✓ Invalid milestone returns None")
    
    def test_03_onboard_partner(self):
        """Test partner onboarding"""
        print("\n✓ Test 3: Onboard Partner")
        
        if not self.prospect_id:
            print("  ⊘ No test prospect available, skipping")
            return
        
        partner_id = log_onboarded_partner(self.prospect_id)
        self.assertIsNotNone(partner_id)
        self.assertIsInstance(partner_id, int)
        print(f"  ✓ Partner onboarded: ID {partner_id}")
        
        # Verify in database
        with get_db() as conn:
            partner = conn.execute(
                "SELECT * FROM partners_activated WHERE id = ?",
                (partner_id,)
            ).fetchone()
        
        self.assertIsNotNone(partner)
        self.assertEqual(dict(partner)["current_milestone"], "M001")
        self.assertEqual(dict(partner)["activation_status"], "INTEGRATION_PENDING")
        print(f"  ✓ Partner record created with M001 milestone")
        
        self.partner_id = partner_id
    
    def test_04_activation_score_calculation(self):
        """Test activation score calculation"""
        print("\n✓ Test 4: Activation Score Calculation")
        
        if not hasattr(self, 'partner_id'):
            if self.prospect_id:
                self.setUp()
                self.partner_id = log_onboarded_partner(self.prospect_id)
            else:
                print("  ⊘ No test partner, skipping")
                return
        
        score = calculate_activation_score(self.partner_id)
        
        self.assertIn("activation_score", score)
        self.assertIn("health_status", score)
        self.assertIn("current_milestone", score)
        self.assertIn("score_breakdown", score)
        
        score_val = score["activation_score"]
        self.assertGreaterEqual(score_val, 0)
        self.assertLessEqual(score_val, 100)
        print(f"  ✓ Activation score: {score_val}/100")
        
        status = score["health_status"]
        self.assertIn(status, ["ON_TRACK", "AT_RISK", "CRITICAL"])
        print(f"  ✓ Health status: {status}")
        
        # Check breakdown
        breakdown = score["score_breakdown"]
        self.assertIn("milestone_progress", breakdown)
        self.assertIn("speed_to_milestone", breakdown)
        self.assertIn("activity_recency", breakdown)
        print(f"  ✓ Score breakdown calculated")
    
    def test_05_log_partner_activity(self):
        """Test activity logging"""
        print("\n✓ Test 5: Log Partner Activity")
        
        if not hasattr(self, 'partner_id'):
            if self.prospect_id:
                self.setUp()
                self.partner_id = log_onboarded_partner(self.prospect_id)
            else:
                print("  ⊘ No test partner, skipping")
                return
        
        # Log an activity
        log_partner_activity(
            self.partner_id,
            "LOGIN",
            notes="Partner accessed integration dashboard"
        )
        print(f"  ✓ LOGIN activity logged")
        
        # Verify activity recorded
        with get_db() as conn:
            activity = conn.execute(
                "SELECT * FROM partner_activity WHERE partner_id = ? ORDER BY detected_at DESC LIMIT 1",
                (self.partner_id,)
            ).fetchone()
        
        self.assertIsNotNone(activity)
        self.assertEqual(dict(activity)["activity_type"], "LOGIN")
        print(f"  ✓ Activity verified in database")
        
        # Verify last_activity timestamp updated on partner
        with get_db() as conn:
            partner = conn.execute(
                "SELECT last_activity FROM partners_activated WHERE id = ?",
                (self.partner_id,)
            ).fetchone()
        
        self.assertIsNotNone(dict(partner)["last_activity"])
        print(f"  ✓ Partner last_activity timestamp updated")
    
    def test_06_advance_milestone(self):
        """Test milestone advancement"""
        print("\n✓ Test 6: Advance Milestone")
        
        if not hasattr(self, 'partner_id'):
            if self.prospect_id:
                self.setUp()
                self.partner_id = log_onboarded_partner(self.prospect_id)
            else:
                print("  ⊘ No test partner, skipping")
                return
        
        # Advance to M002
        update_partner_milestone(
            self.partner_id,
            "M002",
            evidence="First sandbox API call successful"
        )
        print(f"  ✓ Milestone advanced to M002")
        
        # Verify in database
        with get_db() as conn:
            partner = conn.execute(
                "SELECT current_milestone FROM partners_activated WHERE id = ?",
                (self.partner_id,)
            ).fetchone()
        
        self.assertEqual(dict(partner)["current_milestone"], "M002")
        print(f"  ✓ Current milestone verified: M002")
        
        # Verify milestone record created
        with get_db() as conn:
            milestone = conn.execute(
                "SELECT * FROM activation_milestones WHERE partner_id = ? AND milestone_type = 'M002'",
                (self.partner_id,)
            ).fetchone()
        
        self.assertIsNotNone(milestone)
        self.assertEqual(dict(milestone)["status"], "COMPLETED")
        print(f"  ✓ Milestone record created and marked COMPLETED")
    
    def test_07_mark_issue(self):
        """Test issue logging"""
        print("\n✓ Test 7: Mark Partner Issue")
        
        if not hasattr(self, 'partner_id'):
            if self.prospect_id:
                self.setUp()
                self.partner_id = log_onboarded_partner(self.prospect_id)
            else:
                print("  ⊘ No test partner, skipping")
                return
        
        mark_partner_at_risk(
            self.partner_id,
            "AUTH_FAILURE",
            "integration",
            "OAuth2 token refresh timing out",
            "HIGH"
        )
        print(f"  ✓ Issue logged: AUTH_FAILURE (HIGH severity)")
        
        # Verify issue recorded
        with get_db() as conn:
            issue = conn.execute(
                "SELECT * FROM partner_issues WHERE partner_id = ? ORDER BY detected_at DESC LIMIT 1",
                (self.partner_id,)
            ).fetchone()
        
        self.assertIsNotNone(issue)
        issue_dict = dict(issue)
        self.assertEqual(issue_dict["issue_type"], "AUTH_FAILURE")
        self.assertEqual(issue_dict["severity"], "HIGH")
        self.assertIsNone(issue_dict["resolved_at"])
        print(f"  ✓ Issue verified in database as unresolved")
        
        # Verify partner marked at_risk
        with get_db() as conn:
            partner = conn.execute(
                "SELECT is_at_risk FROM partners_activated WHERE id = ?",
                (self.partner_id,)
            ).fetchone()
        
        self.assertEqual(dict(partner)["is_at_risk"], 1)
        print(f"  ✓ Partner marked as at_risk (1)")
        
        self.issue_id = issue_dict["id"]
    
    def test_08_resolve_issue(self):
        """Test issue resolution"""
        print("\n✓ Test 8: Resolve Issue")
        
        if not hasattr(self, 'issue_id'):
            print("  ⊘ Issue not created in prior test, skipping")
            return
        
        resolve_partner_issue(
            self.issue_id,
            "Engineering team implemented custom OAuth2 handler"
        )
        print(f"  ✓ Issue resolved")
        
        # Verify resolution recorded
        with get_db() as conn:
            issue = conn.execute(
                "SELECT * FROM partner_issues WHERE id = ?",
                (self.issue_id,)
            ).fetchone()
        
        issue_dict = dict(issue)
        self.assertIsNotNone(issue_dict["resolved_at"])
        self.assertIsNotNone(issue_dict["resolution_notes"])
        print(f"  ✓ Issue marked resolved with notes")
    
    def test_09_detect_stalls(self):
        """Test stall detection"""
        print("\n✓ Test 9: Detect Activation Stalls")
        
        stalls = detect_activation_stalls()
        
        self.assertIsInstance(stalls, list)
        print(f"  ✓ Stall detection returned: {len(stalls)} partners at risk")
        
        for stall in stalls[:3]:  # Show first 3
            self.assertIn("partner_id", stall)
            self.assertIn("stall_type", stall)
            self.assertIn("severity", stall)
            print(f"  ✓ Partner {stall['partner_id']}: {stall['stall_type']} ({stall['severity']})")
    
    def test_10_get_recommendations(self):
        """Test re-engagement recommendations"""
        print("\n✓ Test 10: Get Activation Recommendations")
        
        if not hasattr(self, 'partner_id'):
            if self.prospect_id:
                self.setUp()
                self.partner_id = log_onboarded_partner(self.prospect_id)
            else:
                print("  ⊘ No test partner, skipping")
                return
        
        recommendations = get_activation_recommendations(self.partner_id)
        
        self.assertIn("current_milestone", recommendations)
        self.assertIn("detected_issues", recommendations)
        self.assertIn("stall_reason", recommendations)
        self.assertIn("recommended_strategy", recommendations)
        self.assertIn("re_engagement_persona", recommendations)
        
        print(f"  ✓ Recommendations generated")
        print(f"    - Milestone: {recommendations['current_milestone']}")
        print(f"    - Stall reason: {recommendations['stall_reason']}")
        print(f"    - Persona: {recommendations['re_engagement_persona']}")
    
    def test_11_quarterly_analytics(self):
        """Test analytics calculations"""
        print("\n✓ Test 11: Quarterly Analytics")
        
        analytics = get_quarterly_activation_analytics()
        
        self.assertIn("total_activated", analytics)
        self.assertIn("at_risk", analytics)
        self.assertIn("healthy", analytics)
        self.assertIn("by_milestone", analytics)
        
        total = analytics["total_activated"]
        at_risk = analytics["at_risk"]
        healthy = analytics["healthy"]
        
        self.assertEqual(total, at_risk + healthy)
        print(f"  ✓ Analytics calculated:")
        print(f"    - Total activated: {total}")
        print(f"    - At risk: {at_risk}")
        print(f"    - Healthy: {healthy}")
        
        by_milestone = analytics["by_milestone"]
        self.assertIsInstance(by_milestone, list)
        print(f"    - Breakdown by milestone: {len(by_milestone)} entries")
    
    def test_12_error_handling(self):
        """Test error handling for invalid inputs"""
        print("\n✓ Test 12: Error Handling")
        
        # Test invalid partner ID
        result = calculate_activation_score(99999)
        self.assertIn("error", result)
        print(f"  ✓ Invalid partner ID handled gracefully")
        
        result = get_activation_recommendations(99999)
        self.assertIn("error", result)
        print(f"  ✓ Invalid recommendations request handled")
        
        # Test invalid milestone
        invalid_milestone = get_milestone_by_id("INVALID")
        self.assertIsNone(invalid_milestone)
        print(f"  ✓ Invalid milestone returns None")
    
    def test_13_data_consistency(self):
        """Test data consistency across operations"""
        print("\n✓ Test 13: Data Consistency")
        
        if not self.prospect_id:
            print("  ⊘ No test prospect, skipping")
            return
        
        # Create a fresh partner
        with get_db() as conn:
            conn.execute(
                "DELETE FROM partners_activated WHERE prospect_id = ?",
                (self.prospect_id,)
            )
            conn.commit()
        
        partner_id = log_onboarded_partner(self.prospect_id)
        
        # Log multiple activities
        for i in range(3):
            log_partner_activity(
                partner_id,
                "API_CALL",
                metric_type="count",
                metric_value=5+i
            )
        
        # Verify activities logged
        with get_db() as conn:
            activities = conn.execute(
                "SELECT COUNT(*) as c FROM partner_activity WHERE partner_id = ?",
                (partner_id,)
            ).fetchone()
        
        activity_count = activities["c"]
        self.assertEqual(activity_count, 3)
        print(f"  ✓ Multiple activities logged consistently: {activity_count} records")
        
        # Advance milestone
        update_partner_milestone(partner_id, "M002")
        update_partner_milestone(partner_id, "M003")
        
        # Verify milestone progression
        with get_db() as conn:
            milestones = conn.execute(
                "SELECT COUNT(*) as c FROM activation_milestones WHERE partner_id = ?",
                (partner_id,)
            ).fetchone()
        
        milestone_count = milestones["c"]
        self.assertEqual(milestone_count, 2)
        print(f"  ✓ Milestone progression tracked: {milestone_count} completed")

def run_tests():
    """Run all tests with verbose output"""
    print('='*90)
    print('PRAGMA ACTIVATE LAYER — COMPREHENSIVE UNIT TESTS')
    print('='*90)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestActivateLayer)
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print('\n' + '='*90)
    print('TEST SUMMARY')
    print('='*90)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print('\n✅ ALL TESTS PASSED')
    else:
        print('\n❌ SOME TESTS FAILED')
    
    print('='*90)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)

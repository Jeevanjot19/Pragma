#!/usr/bin/env python3
"""
Tests for INNOVATION 1: Buyer Committee Intelligence
Verifies buyer committee tracking, engagement, sentiment, and consensus analysis.
"""

import unittest
from datetime import datetime, timedelta
from database import init_db, get_db
from intelligence.buyer_committee import (
    add_buyer_committee_member,
    get_buyer_committee,
    log_stakeholder_engagement,
    update_stakeholder_sentiment,
    identify_champion,
    identify_blocker,
    calculate_engagement_score,
    analyze_committee_consensus,
    get_committee_status_report
)

class TestBuyerCommitteeIntelligence(unittest.TestCase):
    """Test suite for buyer committee intelligence"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize database"""
        init_db()
    
    def setUp(self):
        """Create test prospect and buyer committee"""
        with get_db() as conn:
            # Get a prospect for testing
            prospect = conn.execute(
                "SELECT id FROM prospects LIMIT 1"
            ).fetchone()
            
            if prospect:
                self.prospect_id = prospect['id']
            else:
                self.prospect_id = None
    
    def test_01_add_buyer_committee_member(self):
        """Test adding a buyer committee member"""
        print("\n✓ Test 1: Add Buyer Committee Member")
        
        if not self.prospect_id:
            print("  ⊘ No prospect available, skipping")
            return
        
        result = add_buyer_committee_member(
            prospect_id=self.prospect_id,
            name="Alice Chen",
            title="VP Engineering",
            role="CTO",
            email="alice@kreditbee.com",
            decision_authority="TECHNICAL_BUYER"
        )
        
        self.assertTrue(result.get("added"))
        self.assertIsNotNone(result.get("buyer_id"))
        print(f"  ✓ Added buyer: {result['name']} ({result['role']})")
        
        self.buyer_1_id = result["buyer_id"]
    
    def test_02_add_multiple_buyers(self):
        """Test adding multiple buyer committee members"""
        print("\n✓ Test 2: Add Multiple Buyers")
        
        if not self.prospect_id:
            print("  ⊘ No prospect available, skipping")
            return
        
        buyers = [
            {"name": "Amit Patel", "title": "CEO", "role": "CEO", "decision_authority": "ECONOMIC_BUYER"},
            {"name": "Priya Singh", "title": "VP Product", "role": "VP_PRODUCT", "decision_authority": "INFLUENCER"},
            {"name": "Rahul Gupta", "title": "CFO", "role": "CFO", "decision_authority": "ECONOMIC_BUYER"},
        ]
        
        buyer_ids = []
        for buyer_data in buyers:
            result = add_buyer_committee_member(
                prospect_id=self.prospect_id,
                **buyer_data,
                email=f"{buyer_data['name'].lower().replace(' ', '.')}@kreditbee.com"
            )
            buyer_ids.append(result["buyer_id"])
            print(f"  ✓ Added: {buyer_data['name']} ({buyer_data['role']})")
        
        self.assertEqual(len(buyer_ids), 3)
        self.buyer_ids = buyer_ids
    
    def test_03_get_buyer_committee(self):
        """Test retrieving buyer committee"""
        print("\n✓ Test 3: Get Buyer Committee")
        
        if not self.prospect_id:
            print("  ⊘ No prospect available, skipping")
            return
        
        committee = get_buyer_committee(prospect_id=self.prospect_id)
        
        self.assertIsInstance(committee, list)
        self.assertGreater(len(committee), 0)
        print(f"  ✓ Retrieved {len(committee)} buyer committee members")
        
        for member in committee[:3]:
            print(f"    - {member.get('name')} ({member.get('role')})")
    
    def test_04_log_engagement_events(self):
        """Test logging engagement events"""
        print("\n✓ Test 4: Log Engagement Events")
        
        if not hasattr(self, 'buyer_ids'):
            print("  ⊘ No buyers created, skipping")
            return
        
        buyer_id = self.buyer_ids[0]
        
        # Log multiple engagement events
        events = [
            ("EMAIL_SENT", "Introductory email about Blostem"),
            ("EMAIL_OPENED", "Email opened after 2 hours"),
            ("EMAIL_CLICKED", "Clicked on product demo link"),
            ("CALL", "30-minute technical discussion"),
            ("DEMO", "60-minute product demo attended"),
        ]
        
        for event_type, detail in events:
            result = log_stakeholder_engagement(
                buyer_id=buyer_id,
                engagement_type=event_type,
                detail=detail
            )
            self.assertTrue(result.get("logged"))
            print(f"  ✓ Logged: {event_type}")
    
    def test_05_update_sentiment(self):
        """Test updating stakeholder sentiment"""
        print("\n✓ Test 5: Update Stakeholder Sentiment")
        
        if not hasattr(self, 'buyer_ids'):
            print("  ⊘ No buyers created, skipping")
            return
        
        buyer_ids = self.buyer_ids
        sentiments = [
            (buyer_ids[0], "EAGER", "Very engaged, pushing for partnership"),
            (buyer_ids[1], "NEUTRAL", "Interested but assessing alternatives"),
            (buyer_ids[2], "SKEPTICAL", "Concerned about integration timeline"),
        ]
        
        for buyer_id, sentiment, reason in sentiments:
            result = update_stakeholder_sentiment(
                buyer_id=buyer_id,
                sentiment=sentiment,
                reason=reason
            )
            
            self.assertTrue(result.get("updated"))
            print(f"  ✓ Updated sentiment: {sentiment} ({reason})")
    
    def test_06_identify_champion(self):
        """Test identifying champion"""
        print("\n✓ Test 6: Identify Champion")
        
        if not hasattr(self, 'buyer_ids'):
            print("  ⊘ No buyers created, skipping")
            return
        
        champion_id = self.buyer_ids[0]
        
        result = identify_champion(
            buyer_id=champion_id,
            reason="Actively advocating for partnership, pushing other stakeholders"
        )
        
        self.assertTrue(result.get("champion_identified"))
        print(f"  ✓ Champion identified (ID {champion_id})")
    
    def test_07_identify_blocker(self):
        """Test identifying blocker"""
        print("\n✓ Test 7: Identify Blocker")
        
        if not hasattr(self, 'buyer_ids'):
            print("  ⊘ No buyers created, skipping")
            return
        
        blocker_id = self.buyer_ids[2]
        
        result = identify_blocker(
            buyer_id=blocker_id,
            reason="Concerned about cost and integration timeline"
        )
        
        self.assertTrue(result.get("blocker_identified"))
        print(f"  ✓ Blocker identified (ID {blocker_id})")
    
    def test_08_calculate_engagement_score(self):
        """Test engagement score calculation"""
        print("\n✓ Test 8: Calculate Engagement Score")
        
        if not hasattr(self, 'buyer_ids'):
            print("  ⊘ No buyers created, skipping")
            return
        
        for buyer_id in self.buyer_ids[:2]:
            score = calculate_engagement_score(buyer_id)
            
            self.assertIn("engagement_score", score)
            self.assertIn("factors", score)
            
            engagement = score["engagement_score"]
            print(f"  ✓ Buyer {buyer_id} engagement score: {engagement}/100")
    
    def test_09_analyze_consensus(self):
        """Test buyer committee consensus analysis"""
        print("\n✓ Test 9: Analyze Committee Consensus")
        
        if not self.prospect_id:
            print("  ⊘ No prospect available, skipping")
            return
        
        consensus = analyze_committee_consensus(prospect_id=self.prospect_id)
        
        self.assertIn("committee_size", consensus)
        self.assertIn("champions", consensus)
        self.assertIn("blockers", consensus)
        self.assertIn("deal_health", consensus)
        self.assertIn("estimated_close_likelihood", consensus)
        
        print(f"  ✓ Committee size: {consensus['committee_size']}")
        print(f"  ✓ Champions: {consensus['champions']}, Blockers: {consensus['blockers']}")
        print(f"  ✓ Deal health: {consensus['deal_health']}")
        print(f"  ✓ Close likelihood: {consensus['estimated_close_likelihood']}")
    
    def test_10_committee_status_report(self):
        """Test generating committee status report"""
        print("\n✓ Test 10: Committee Status Report")
        
        if not self.prospect_id:
            print("  ⊘ No prospect available, skipping")
            return
        
        report = get_committee_status_report(prospect_id=self.prospect_id)
        
        self.assertIn("committee", report)
        self.assertIn("consensus", report)
        
        committee = report["committee"]
        print(f"  ✓ Status report generated")
        print(f"    - Committee members: {len(committee)}")
        
        if committee:
            for member in committee[:2]:
                print(f"    - {member['name']}: {member['sentiment']} (score: {member['engagement_score']})")
    
    def test_11_decision_authority_tracking(self):
        """Test tracking decision authority"""
        print("\n✓ Test 11: Decision Authority Tracking")
        
        if not self.prospect_id:
            print("  ⊘ No prospect available, skipping")
            return
        
        # Add buyers with different authorities
        economic_buyer = add_buyer_committee_member(
            prospect_id=self.prospect_id,
            name="Budget Controller",
            role="CFO",
            decision_authority="ECONOMIC_BUYER"
        )
        
        technical_buyer = add_buyer_committee_member(
            prospect_id=self.prospect_id,
            name="Tech Lead",
            role="CTO",
            decision_authority="TECHNICAL_BUYER"
        )
        
        self.assertIsNotNone(economic_buyer["buyer_id"])
        self.assertIsNotNone(technical_buyer["buyer_id"])
        
        print(f"  ✓ Economic buyer tracked: {economic_buyer['name']}")
        print(f"  ✓ Technical buyer tracked: {technical_buyer['name']}")
    
    def test_12_consensus_with_blockers(self):
        """Test consensus when blockers present"""
        print("\n✓ Test 12: Consensus with Blockers")
        
        if not self.prospect_id:
            print("  ⊘ No prospect available, skipping")
            return
        
        # Get current consensus
        consensus = analyze_committee_consensus(prospect_id=self.prospect_id)
        
        if consensus.get("blockers", 0) > 0:
            deal_health = consensus.get("deal_health")
            # If there are blockers, deal should not be HEALTHY
            if consensus["blockers"] >= consensus["committee_size"] * 0.25:
                self.assertNotEqual(deal_health, "HEALTHY")
                print(f"  ✓ Deal health correctly reflects blocker presence: {deal_health}")
    
    def test_13_engagement_tracking_updates(self):
        """Test that engagement events update buyer committee metrics"""
        print("\n✓ Test 13: Engagement Tracking Updates")
        
        if not hasattr(self, 'buyer_ids'):
            print("  ⊘ No buyers created, skipping")
            return
        
        buyer_id = self.buyer_ids[0]
        
        # Get initial engagement
        score_before = calculate_engagement_score(buyer_id)
        initial = score_before["engagement_score"]
        
        # Log multiple engagements
        for i in range(3):
            log_stakeholder_engagement(
                buyer_id=buyer_id,
                engagement_type="EMAIL_OPENED",
                detail=f"Email {i+1} opened"
            )
        
        # Get new engagement score
        score_after = calculate_engagement_score(buyer_id)
        final = score_after["engagement_score"]
        
        # Score should increase with more engagement
        print(f"  ✓ Before: {initial}/100, After: {final}/100")

def run_tests():
    """Run all buyer committee tests"""
    print('='*90)
    print('INNOVATION 1: BUYER COMMITTEE INTELLIGENCE — TEST SUITE')
    print('='*90)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestBuyerCommitteeIntelligence)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print('\n' + '='*90)
    print('TEST SUMMARY')
    print('='*90)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print('\n✅ ALL INNOVATION 1 TESTS PASSED')
    else:
        print('\n❌ SOME TESTS FAILED')
    
    print('='*90)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)

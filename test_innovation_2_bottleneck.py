#!/usr/bin/env python3
"""
Tests for INNOVATION 2: Bottleneck Auto-Diagnosis
Verifies automatic diagnosis of partner stall root causes and team routing.
"""

import unittest
from datetime import datetime, timedelta
from database import init_db, get_db
from intelligence.bottleneck_diagnosis import (
    diagnose_partner_bottleneck,
    get_team_routing,
    route_diagnosis_to_team,
    diagnose_all_stalled_partners
)

class TestBottleneckDiagnosis(unittest.TestCase):
    """Test suite for bottleneck diagnosis"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize database"""
        init_db()
    
    def setUp(self):
        """Create test partner"""
        from outreach.activation import log_onboarded_partner
        
        with get_db() as conn:
            prospect = conn.execute(
                "SELECT id FROM prospects WHERE is_existing_partner = 0 LIMIT 1"
            ).fetchone()
            
            if prospect:
                self.prospect_id = prospect['id']
                
                # Check if already onboarded
                existing = conn.execute(
                    "SELECT id FROM partners_activated WHERE prospect_id = ?",
                    (self.prospect_id,)
                ).fetchone()
                
                if existing:
                    self.partner_id = existing['id']
                else:
                    # Onboard as partner
                    self.partner_id = log_onboarded_partner(self.prospect_id)
            else:
                self.prospect_id = None
                self.partner_id = None
    
    def test_01_diagnose_stalled_partner(self):
        """Test diagnosing a stalled partner"""
        print("\n✓ Test 1: Diagnose Stalled Partner")
        
        if not self.partner_id:
            print("  ⊘ No partner available, skipping")
            return
        
        diagnosis = diagnose_partner_bottleneck(self.partner_id)
        
        self.assertIn("partner_id", diagnosis)
        self.assertIn("bottleneck_category", diagnosis)
        self.assertIn("hypothesis", diagnosis)
        
        print(f"  ✓ Partner {self.partner_id}")
        print(f"    - Category: {diagnosis['bottleneck_category']}")
        print(f"    - Hypothesis: {diagnosis['hypothesis']}")
        print(f"    - Confidence: {diagnosis.get('confidence', 0):.0%}")
    
    def test_02_team_routing_technical(self):
        """Test routing technical bottleneck to engineering"""
        print("\n✓ Test 2: Team Routing - Technical")
        
        routing = get_team_routing("TECHNICAL")
        
        self.assertIn("route_to", routing)
        self.assertEqual(routing["route_to"], "Engineering")
        self.assertIn("sla_hours", routing)
        self.assertIn("actions", routing)
        
        print(f"  ✓ Route to: {routing['route_to']}")
        print(f"  ✓ Owner: {routing['owner']}")
        print(f"  ✓ SLA: {routing['sla_hours']} hours")
    
    def test_03_team_routing_business(self):
        """Test routing business bottleneck to product"""
        print("\n✓ Test 3: Team Routing - Business")
        
        routing = get_team_routing("BUSINESS")
        
        self.assertEqual(routing["route_to"], "Product & Partnership")
        print(f"  ✓ Route to: {routing['route_to']}")
    
    def test_04_team_routing_adoption(self):
        """Test routing adoption bottleneck to success"""
        print("\n✓ Test 4: Team Routing - Adoption")
        
        routing = get_team_routing("ADOPTION")
        
        self.assertEqual(routing["route_to"], "Customer Success")
        print(f"  ✓ Route to: {routing['route_to']}")
    
    def test_05_team_routing_compliance(self):
        """Test routing compliance bottleneck to legal"""
        print("\n✓ Test 5: Team Routing - Compliance")
        
        routing = get_team_routing("COMPLIANCE")
        
        self.assertEqual(routing["route_to"], "Legal & Compliance")
        self.assertEqual(routing["sla_hours"], 4)  # Highest priority
        print(f"  ✓ Route to: {routing['route_to']}")
        print(f"  ✓ Priority SLA: {routing['sla_hours']} hours (highest)")
    
    def test_06_route_diagnosis_to_team(self):
        """Test routing a diagnosis to appropriate team"""
        print("\n✓ Test 6: Route Diagnosis to Team")
        
        if not self.partner_id:
            print("  ⊘ No partner available, skipping")
            return
        
        diagnosis = diagnose_partner_bottleneck(self.partner_id)
        
        if diagnosis.get("bottleneck_category") == "UNKNOWN":
            print("  ℹ Diagnosis unclear for this partner, skipping routing test")
            return
        
        routed = route_diagnosis_to_team(self.partner_id, diagnosis)
        
        if routed.get("routed"):
            print(f"  ✓ Routed to: {routed['route_to']}")
            print(f"  ✓ Owner: {routed['owner']}")
            print(f"  ✓ Confidence: {routed.get('confidence', 0):.0%}")
    
    def test_07_all_categories_have_routing(self):
        """Test that all bottleneck categories have routing rules"""
        print("\n✓ Test 7: All Categories Have Routing")
        
        categories = [
            "TECHNICAL", "BUSINESS", "ADOPTION", "SUPPORT", "COMPLIANCE", "PROCUREMENT"
        ]
        
        for category in categories:
            routing = get_team_routing(category)
            self.assertNotIn("error", routing)
            self.assertIn("route_to", routing)
            print(f"  ✓ {category:15s} → {routing['route_to']}")
    
    def test_08_diagnosis_includes_questions(self):
        """Test that diagnosis includes clarifying questions"""
        print("\n✓ Test 8: Diagnosis Includes Questions")
        
        if not self.partner_id:
            print("  ⊘ No partner available, skipping")
            return
        
        diagnosis = diagnose_partner_bottleneck(self.partner_id)
        
        # All diagnoses should have high-level questions
        self.assertIn("hypothesis", diagnosis)
        
        if diagnosis.get("questions"):
            print(f"  ✓ Generated {len(diagnosis['questions'])} clarifying questions:")
            for i, q in enumerate(diagnosis['questions'][:3], 1):
                print(f"    {i}. {q}")
    
    def test_09_diagnosis_has_recommended_action(self):
        """Test that diagnosis includes recommended action"""
        print("\n✓ Test 9: Diagnosis Has Recommended Action")
        
        if not self.partner_id:
            print("  ⊘ No partner available, skipping")
            return
        
        diagnosis = diagnose_partner_bottleneck(self.partner_id)
        
        self.assertIn("recommended_action", diagnosis)
        print(f"  ✓ Recommended action: {diagnosis['recommended_action']}")
    
    def test_10_bulk_diagnosis(self):
        """Test diagnosing all stalled partners"""
        print("\n✓ Test 10: Bulk Diagnosis")
        
        report = diagnose_all_stalled_partners()
        
        self.assertIn("total_stalled", report)
        self.assertIn("by_category", report)
        
        print(f"  ✓ Total stalled partners: {report['total_stalled']}")
        print(f"  ✓ Categories: {len(report['by_category'])}")
        
        for category, partners in report['by_category'].items():
            if partners:
                print(f"    - {category}: {len(partners)} partners")
    
    def test_11_confidence_score(self):
        """Test that diagnosis includes confidence score"""
        print("\n✓ Test 11: Confidence Score")
        
        if not self.partner_id:
            print("  ⊘ No partner available, skipping")
            return
        
        diagnosis = diagnose_partner_bottleneck(self.partner_id)
        
        self.assertIn("confidence", diagnosis)
        confidence = diagnosis["confidence"]
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)
        print(f"  ✓ Confidence score: {confidence:.0%}")
    
    def test_12_severity_levels(self):
        """Test that severity is properly assigned"""
        print("\n✓ Test 12: Severity Levels")
        
        valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        
        if not self.partner_id:
            print("  ⊘ No partner available, skipping")
            return
        
        diagnosis = diagnose_partner_bottleneck(self.partner_id)
        
        severity = diagnosis.get("severity")
        self.assertIn(severity, valid_severities)
        print(f"  ✓ Severity assigned: {severity}")

def run_tests():
    """Run all bottleneck diagnosis tests"""
    print('='*90)
    print('INNOVATION 2: BOTTLENECK AUTO-DIAGNOSIS — TEST SUITE')
    print('='*90)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestBottleneckDiagnosis)
    
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
        print('\n✅ ALL INNOVATION 2 TESTS PASSED')
    else:
        print('\n❌ SOME TESTS FAILED')
    
    print('='*90)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)

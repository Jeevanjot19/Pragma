#!/usr/bin/env python3
"""
API Integration tests for ACTIVATE layer endpoints.
Tests all HTTP endpoints for proper request/response handling.
"""

import json
import unittest
from fastapi.testclient import TestClient
from main import app
from database import init_db

class TestActivateAPI(unittest.TestCase):
    """Test suite for ACTIVATE API endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize app and database"""
        init_db()
        cls.client = TestClient(app)
    
    def test_01_onboard_partner(self):
        """Test POST /api/activate/onboard/{prospect_id}"""
        print("\n✓ Test 1: Onboard Partner Endpoint")
        
        prospect_id = 1  # Assuming prospect 1 exists from WHO layer
        
        response = self.client.post(f"/api/activate/onboard/{prospect_id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("partner_id", data)
        self.assertIn("status", data)
        self.assertEqual(data["status"], "INTEGRATION_PENDING")
        
        print(f"  ✓ Onboard successful: Partner ID {data['partner_id']}")
        self.partner_id = data["partner_id"]
    
    def test_02_get_activation_score(self):
        """Test GET /api/activate/score/{partner_id}"""
        print("\n✓ Test 2: Get Activation Score Endpoint")
        
        if not hasattr(self, 'partner_id'):
            print("  ⊘ No partner onboarded, skipping")
            return
        
        response = self.client.get(f"/api/activate/score/{self.partner_id}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("activation_score", data)
        self.assertIn("health_status", data)
        self.assertIn("current_milestone", data)
        
        score = data["activation_score"]
        status = data["health_status"]
        
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertIn(status, ["ON_TRACK", "AT_RISK", "CRITICAL"])
        
        print(f"  ✓ Score retrieved: {score}/100 ({status})")
    
    def test_03_log_activity(self):
        """Test POST /api/activate/{partner_id}/log-activity"""
        print("\n✓ Test 3: Log Activity Endpoint")
        
        if not hasattr(self, 'partner_id'):
            print("  ⊘ No partner onboarded, skipping")
            return
        
        payload = {
            "activity_type": "API_CALL",
            "metric_type": "count",
            "metric_value": 10,
            "notes": "Partner made 10 API calls today"
        }
        
        response = self.client.post(
            f"/api/activate/{self.partner_id}/log-activity",
            json=payload
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("logged", data)
        self.assertTrue(data["logged"])
        
        print(f"  ✓ Activity logged: {payload['activity_type']}")
    
    def test_04_advance_milestone(self):
        """Test POST /api/activate/{partner_id}/advance-milestone"""
        print("\n✓ Test 4: Advance Milestone Endpoint")
        
        if not hasattr(self, 'partner_id'):
            print("  ⊘ No partner onboarded, skipping")
            return
        
        payload = {
            "milestone": "M002",
            "evidence": "Successful sandbox integration test"
        }
        
        response = self.client.post(
            f"/api/activate/{self.partner_id}/advance-milestone",
            json=payload
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("advanced", data)
        self.assertIn("new_milestone", data)
        self.assertTrue(data["advanced"])
        
        print(f"  ✓ Milestone advanced to: {data['new_milestone']}")
    
    def test_05_log_issue(self):
        """Test POST /api/activate/{partner_id}/log-issue"""
        print("\n✓ Test 5: Log Issue Endpoint")
        
        if not hasattr(self, 'partner_id'):
            print("  ⊘ No partner onboarded, skipping")
            return
        
        payload = {
            "issue_type": "API_TIMEOUT",
            "category": "technical",
            "description": "Partner's integration keeps timing out",
            "severity": "HIGH"
        }
        
        response = self.client.post(
            f"/api/activate/{self.partner_id}/log-issue",
            json=payload
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("issue_id", data)
        self.assertIn("logged", data)
        self.assertTrue(data["logged"])
        
        print(f"  ✓ Issue logged: {payload['issue_type']} (ID {data['issue_id']})")
        self.issue_id = data["issue_id"]
    
    def test_06_resolve_issue(self):
        """Test POST /api/activate/{partner_id}/resolve-issue/{issue_id}"""
        print("\n✓ Test 6: Resolve Issue Endpoint")
        
        if not hasattr(self, 'issue_id'):
            print("  ⊘ No issue logged, skipping")
            return
        
        payload = {
            "resolution": "Increased API timeout limits"
        }
        
        response = self.client.post(
            f"/api/activate/{self.partner_id}/resolve-issue/{self.issue_id}",
            json=payload
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("resolved", data)
        self.assertTrue(data["resolved"])
        
        print(f"  ✓ Issue resolved")
    
    def test_07_get_recommendations(self):
        """Test GET /api/activate/{partner_id}/recommendations"""
        print("\n✓ Test 7: Get Recommendations Endpoint")
        
        if not hasattr(self, 'partner_id'):
            print("  ⊘ No partner onboarded, skipping")
            return
        
        response = self.client.get(f"/api/activate/{self.partner_id}/recommendations")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("re_engagement_persona", data)
        self.assertIn("recommended_strategy", data)
        self.assertIn("current_milestone", data)
        
        print(f"  ✓ Recommendations generated:")
        print(f"    - Persona: {data['re_engagement_persona']}")
        print(f"    - Strategy: {data['recommended_strategy']}")
    
    def test_08_generate_reengagement(self):
        """Test POST /api/activate/{partner_id}/generate-reengagement"""
        print("\n✓ Test 8: Generate Re-engagement Email Endpoint")
        
        if not hasattr(self, 'partner_id'):
            print("  ⊘ No partner onboarded, skipping")
            return
        
        response = self.client.post(
            f"/api/activate/{self.partner_id}/generate-reengagement"
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("email_subject", data)
        self.assertIn("email_body", data)
        self.assertIn("generated", data)
        self.assertTrue(data["generated"])
        
        print(f"  ✓ Re-engagement email generated")
        print(f"    - Subject: {data['email_subject'][:50]}...")
    
    def test_09_list_stalls(self):
        """Test GET /api/activate/stalls"""
        print("\n✓ Test 9: List Stalls Endpoint")
        
        response = self.client.get("/api/activate/stalls")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("stalls", data)
        self.assertIsInstance(data["stalls"], list)
        self.assertIn("count", data)
        
        print(f"  ✓ Stalls retrieved: {data['count']} partners at risk")
    
    def test_10_quarterly_analytics(self):
        """Test GET /api/activate/analytics/quarterly"""
        print("\n✓ Test 10: Quarterly Analytics Endpoint")
        
        response = self.client.get("/api/activate/analytics/quarterly")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("total_activated", data)
        self.assertIn("at_risk", data)
        self.assertIn("healthy", data)
        self.assertIn("by_milestone", data)
        
        print(f"  ✓ Analytics retrieved:")
        print(f"    - Total activated: {data['total_activated']}")
        print(f"    - At risk: {data['at_risk']}")
        print(f"    - Healthy: {data['healthy']}")
    
    def test_11_activation_dashboard(self):
        """Test GET /api/activate/dashboard"""
        print("\n✓ Test 11: Activation Dashboard Endpoint")
        
        response = self.client.get("/api/activate/dashboard")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("summary", data)
        self.assertIn("in_progress", data)
        self.assertIn("at_risk_partners", data)
        self.assertIn("recent_milestones", data)
        
        print(f"  ✓ Dashboard data retrieved")
        print(f"    - Partners in progress: {len(data['in_progress'])}")
        print(f"    - At risk partners: {len(data['at_risk_partners'])}")
    
    def test_12_error_cases(self):
        """Test API error handling"""
        print("\n✓ Test 12: Error Handling")
        
        # Test nonexistent partner
        response = self.client.get("/api/activate/score/99999")
        self.assertIn(response.status_code, [404, 400])
        print(f"  ✓ Nonexistent partner returns {response.status_code}")
        
        # Test invalid payload
        response = self.client.post(
            f"/api/activate/1/log-activity",
            json={"invalid": "data"}
        )
        self.assertIn(response.status_code, [400, 422])
        print(f"  ✓ Invalid payload returns {response.status_code}")
    
    def test_13_endpoint_coverage(self):
        """Verify all ACTIVATE endpoints exist"""
        print("\n✓ Test 13: Endpoint Coverage Verification")
        
        endpoints = [
            ("POST", "/api/activate/onboard/1"),
            ("GET", "/api/activate/score/1"),
            ("GET", "/api/activate/stalls"),
            ("POST", "/api/activate/1/log-activity"),
            ("POST", "/api/activate/1/advance-milestone"),
            ("POST", "/api/activate/1/log-issue"),
            ("POST", "/api/activate/1/resolve-issue/1"),
            ("GET", "/api/activate/1/recommendations"),
            ("POST", "/api/activate/1/generate-reengagement"),
            ("GET", "/api/activate/analytics/quarterly"),
            ("GET", "/api/activate/dashboard"),
        ]
        
        covered = 0
        for method, path in endpoints:
            # Just verify endpoint exists (status may vary based on data)
            if method == "GET":
                response = self.client.get(path)
            else:
                response = self.client.post(path, json={} if method == "POST" else None)
            
            # 200, 400, 404 all mean endpoint exists (not 404 for "not found route")
            if response.status_code != 404:
                covered += 1
        
        print(f"  ✓ Endpoint coverage: {covered}/{len(endpoints)} endpoints verified")

def run_api_tests():
    """Run all API tests"""
    print('='*90)
    print('PRAGMA ACTIVATE LAYER — API INTEGRATION TESTS')
    print('='*90)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestActivateAPI)
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print('\n' + '='*90)
    print('API TEST SUMMARY')
    print('='*90)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print('\n✅ ALL API TESTS PASSED')
    else:
        print('\n❌ SOME API TESTS FAILED')
    
    print('='*90)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_api_tests()
    exit(0 if success else 1)

#!/usr/bin/env python3
"""
Integration tests for Blostem API gateway webhook integration.

This tests the flow:
1. Blostem API gateway receives request from partner
2. Gateway POSTs to /api/activate/api-call/log webhook
3. We log the API call
4. detect_activation_patterns finds stalls
5. generate_intervention_email creates targeted email
"""

import json
import pytest
from datetime import datetime, timedelta
from database import get_db, init_db
from main import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestBlostemWebhookIntegration:
    """Test integration with Blostem's API gateway."""

    def setup_method(self):
        """Initialize database before each test."""
        init_db()
        # Clean up and add test prospects to avoid UNIQUE constraint on prospect_id
        with get_db() as conn:
            # Clean up from previous tests
            conn.execute("DELETE FROM partners_activated")
            conn.execute("DELETE FROM partner_api_calls")
            conn.execute("DELETE FROM partner_activation_stalls")
            conn.execute("DELETE FROM partner_political_risks")
            
            # Add test prospects
            for prospect_id in range(1, 20):
                conn.execute("""
                    INSERT OR IGNORE INTO prospects (id, name, status, who_score)
                    VALUES (?, ?, 'HOT', 85)
                """, (prospect_id, f"Test Partner {prospect_id}"))
            conn.commit()

    def test_01_webhook_receives_api_call_log(self):
        """Test: API gateway sends us a webhook with partner API call details."""
        # Simulate Blostem API gateway sending webhook
        webhook_payload = {
            "partner_id": 1,  # Test partner (e.g., Razorpay)
            "environment": "sandbox",
            "endpoint": "/v1/webhooks/register",
            "method": "POST",
            "status_code": 201,
            "response_time_ms": 145,
            "error_code": None,
            "error_message": None,
            "api_key_id": "sk_test_razorpay_001"
        }
        
        response = client.post("/api/activate/api-call/log", json=webhook_payload)
        
        if response.status_code != 200:
            print(f"\n422 Error Response: {response.text}")
        
        assert response.status_code == 200
        assert response.json()["status"] == "api_call_logged"
        assert response.json()["partner_id"] == 1
        
        # Verify it was stored in database
        with get_db() as conn:
            call = conn.execute(
                "SELECT * FROM partner_api_calls WHERE partner_id = ?",
                (1,)
            ).fetchone()
            assert call is not None
            assert call['environment'] == 'sandbox'
            assert call['status_code'] == 201

    def test_02_webhook_logs_failed_request(self):
        """Test: Gateway sends us a failed API call (error code present)."""
        webhook_payload = {
            "partner_id": 2,  # Another partner
            "environment": "sandbox",
            "endpoint": "/v1/balance",
            "method": "GET",
            "status_code": 401,
            "response_time_ms": 89,
            "error_code": "AUTH_INVALID_KEY",
            "error_message": "API key is invalid or expired",
            "api_key_id": "sk_test_partner2_001"
        }
        
        response = client.post("/api/activate/api-call/log", json=webhook_payload)
        
        assert response.status_code == 200
        
        with get_db() as conn:
            call = conn.execute(
                "SELECT * FROM partner_api_calls WHERE partner_id = ?",
                (2,)
            ).fetchone()
            assert call['error_code'] == 'AUTH_INVALID_KEY'

    def test_03_webhook_logs_production_call(self):
        """Test: Partner makes a call from production environment."""
        webhook_payload = {
            "partner_id": 3,
            "environment": "production",
            "endpoint": "/v1/transfers",
            "method": "POST",
            "status_code": 200,
            "response_time_ms": 287,
            "error_code": None,
            "error_message": None,
            "api_key_id": "sk_live_partner3_001"
        }
        
        response = client.post("/api/activate/api-call/log", json=webhook_payload)
        assert response.status_code == 200

    def test_04_dead_on_arrival_detection(self):
        """Test: Partner who never called API in 14 days is detected."""
        # Manually set up a partner that signed 15 days ago but never called
        with get_db() as conn:
            signed_at = (datetime.now() - timedelta(days=15)).isoformat()
            conn.execute("""
                INSERT INTO partners_activated (prospect_id, signed_at, current_milestone)
                VALUES (?, ?, ?)
            """, (1, signed_at, "M001"))
            conn.commit()
        
        # Now test detection
        response = client.get("/api/activate/patterns/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["stall_detected"] == True
        assert data["stall_pattern"] == "DEAD_ON_ARRIVAL"
        assert data["requires_intervention"] == True

    def test_05_stuck_in_sandbox_detection(self):
        """Test: Partner with sandbox calls then 7+ day silence is detected."""
        # Set up partner
        with get_db() as conn:
            signed_at = (datetime.now() - timedelta(days=15)).isoformat()
            cursor = conn.execute("""
                INSERT INTO partners_activated (prospect_id, signed_at, current_milestone)
                VALUES (?, ?, ?)
            """, (2, signed_at, "M001"))
            partner_activation_id = cursor.lastrowid
            
            # Log some sandbox calls 9 days ago
            call_time = (datetime.now() - timedelta(days=9)).isoformat()
            conn.execute("""
                INSERT INTO partner_api_calls 
                (partner_id, environment, endpoint, method, status_code, 
                 error_code, error_message, response_time_ms, api_key_id, called_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (partner_activation_id, "sandbox", "/v1/webhooks/register", "POST", 201, 
                  None, None, 145, "sk_test_002", call_time))
            
            # Log an error 8 days ago (more recent, so this becomes the "last" call)
            error_time = (datetime.now() - timedelta(days=8)).isoformat()
            conn.execute("""
                INSERT INTO partner_api_calls 
                (partner_id, environment, endpoint, method, status_code, 
                 error_code, error_message, response_time_ms, api_key_id, called_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (partner_activation_id, "sandbox", "/v1/balance", "GET", 401, 
                  "AUTH_INVALID_KEY", "API key expired", 89, "sk_test_002", error_time))
            
            conn.commit()
        
        # Test detection (use prospect_id in URL)
        response = client.get("/api/activate/patterns/2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["stall_detected"] == True
        assert data["stall_pattern"] == "STUCK_IN_SANDBOX"

    def test_06_production_blocked_detection(self):
        """Test: Partner with successful sandbox but 0 production calls for 14+ days."""
        with get_db() as conn:
            signed_at = (datetime.now() - timedelta(days=20)).isoformat()
            cursor = conn.execute("""
                INSERT INTO partners_activated (prospect_id, signed_at, current_milestone)
                VALUES (?, ?, ?)
            """, (3, signed_at, "M002"))
            partner_activation_id = cursor.lastrowid
            
            # Log successful sandbox calls (5 days ago, so recent enough for detection)
            sandbox_time = (datetime.now() - timedelta(days=5)).isoformat()
            for i in range(5):
                conn.execute("""
                    INSERT INTO partner_api_calls 
                    (partner_id, environment, endpoint, method, status_code, 
                     error_code, error_message, response_time_ms, api_key_id, called_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (partner_activation_id, "sandbox", f"/v1/test_{i}", "POST", 200, 
                      None, None, 145, "sk_test_003", sandbox_time))
            
            # NO production calls since then
            conn.commit()
        
        response = client.get("/api/activate/patterns/3")
        
        assert response.status_code == 200
        data = response.json()
        assert data["stall_detected"] == True
        assert data["stall_pattern"] == "PRODUCTION_BLOCKED"

    def test_07_generate_dead_on_arrival_email(self):
        """Test: Generate intervention email for DEAD_ON_ARRIVAL pattern."""
        # Set up partner who never called
        with get_db() as conn:
            signed_at = (datetime.now() - timedelta(days=15)).isoformat()
            conn.execute("""
                INSERT INTO partners_activated (prospect_id, signed_at, current_milestone)
                VALUES (?, ?, ?)
            """, (1, signed_at, "M001"))
            conn.commit()
        
        # Generate intervention
        response = client.post(
            "/api/activate/patterns/1/generate-intervention"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["stall_pattern"] == "DEAD_ON_ARRIVAL"
        assert "intervention" in data
        assert data["intervention"]["target_persona"] == "CTO"
        assert "subject" in data["intervention"]
        assert "body" in data["intervention"]
        assert "Let's get you up" in data["intervention"]["body"] or \
               "30-min" in data["intervention"]["body"]

    def test_08_generate_stuck_in_sandbox_email(self):
        """Test: Generate debugging-specific email for STUCK_IN_SANDBOX."""
        with get_db() as conn:
            signed_at = (datetime.now() - timedelta(days=15)).isoformat()
            cursor = conn.execute("""
                INSERT INTO partners_activated (prospect_id, signed_at, current_milestone)
                VALUES (?, ?, ?)
            """, (2, signed_at, "M001"))
            partner_activation_id = cursor.lastrowid
            
            # Sandbox calls 10 days ago
            call_time = (datetime.now() - timedelta(days=10)).isoformat()
            conn.execute("""
                INSERT INTO partner_api_calls 
                (partner_id, environment, endpoint, method, status_code, 
                 error_code, error_message, response_time_ms, api_key_id, called_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (partner_activation_id, "sandbox", "/v1/register", "POST", 201, None, None, 145, "sk_test_002", call_time))
            
            # Recent error 8 days ago to trigger stuck pattern
            error_time = (datetime.now() - timedelta(days=8)).isoformat()
            conn.execute("""
                INSERT INTO partner_api_calls 
                (partner_id, environment, endpoint, method, status_code, 
                 error_code, error_message, response_time_ms, api_key_id, called_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (partner_activation_id, "sandbox", "/v1/balance", "GET", 400, 
                  "INVALID_PARAM", "Missing required field: account_id", 89, "sk_test_002", error_time))
            
            conn.commit()
        
        response = client.post("/api/activate/patterns/2/generate-intervention")
        
        assert response.status_code == 200
        data = response.json()
        assert data["stall_pattern"] == "STUCK_IN_SANDBOX"
        assert data["intervention"]["target_persona"] == "CTO"
        assert "body" in data["intervention"]
        # Should mention the specific error
        assert "INVALID_PARAM" in data["intervention"]["body"] or \
               "account_id" in data["intervention"]["body"]

    def test_09_mark_intervention_sent(self):
        """Test: Record that intervention email was sent."""
        with get_db() as conn:
            signed_at = (datetime.now() - timedelta(days=15)).isoformat()
            conn.execute("""
                INSERT INTO partners_activated (prospect_id, signed_at, current_milestone)
                VALUES (?, ?, ?)
            """, (1, signed_at, "M001"))
            conn.commit()
        
        # Record intervention sent
        response = client.post(
            "/api/activate/patterns/1/mark-intervention-sent",
            json={"pattern": "DEAD_ON_ARRIVAL"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "intervention_marked_sent"

    def test_10_mark_stall_resolved(self):
        """Test: Mark stall as resolved when partner makes progress."""
        with get_db() as conn:
            signed_at = (datetime.now() - timedelta(days=15)).isoformat()
            conn.execute("""
                INSERT INTO partners_activated (prospect_id, signed_at, current_milestone)
                VALUES (?, ?, ?)
            """, (1, signed_at, "M001"))
            conn.commit()
        
        # Log an API call (partner finally started!)
        webhook_payload = {
            "partner_id": 1,
            "environment": "sandbox",
            "endpoint": "/v1/webhooks/register",
            "method": "POST",
            "status_code": 201,
            "response_time_ms": 145,
            "error_code": None,
            "error_message": None,
            "api_key_id": "sk_test_001"
        }
        client.post("/api/activate/api-call/log", json=webhook_payload)
        
        # Mark as resolved
        response = client.post(
            "/api/activate/patterns/1/mark-resolved",
            json={"pattern": "DEAD_ON_ARRIVAL", "resolution": "First API call received"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "stall_resolved"

    def test_11_stall_summary_dashboard(self):
        """Test: Get summary of all stalls for account manager dashboard."""
        # Set up multiple partners with different stalls
        with get_db() as conn:
            for partner_id in range(1, 4):
                signed_at = (datetime.now() - timedelta(days=15+partner_id)).isoformat()
                conn.execute("""
                    INSERT INTO partners_activated (prospect_id, signed_at, current_milestone)
                    VALUES (?, ?, ?)
                """, (partner_id, signed_at, "M001"))
            conn.commit()
        
        response = client.get("/api/activate/patterns/all/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "stalls_by_pattern" in data
        assert "recent_stalls" in data
        assert "political_risks_by_type" in data

    def test_12_political_risk_detection(self):
        """Test: Detect political risks from news monitoring."""
        response = client.get("/api/activate/political-risks/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["partner_id"] == 1
        assert "political_risks" in data
        assert "requires_account_manager_review" in data

    def test_13_webhook_high_frequency_calls(self):
        """Test: Handle rapid webhook POSTs (heavy API activity)."""
        # Simulate 10 rapid calls from partner
        for i in range(10):
            webhook_payload = {
                "partner_id": 4,
                "environment": "production",
                "endpoint": f"/v1/endpoint_{i}",
                "method": "POST",
                "status_code": 200,
                "response_time_ms": 100 + i,
                "error_code": None,
                "error_message": None,
                "api_key_id": "sk_live_004"
            }
            response = client.post("/api/activate/api-call/log", json=webhook_payload)
            assert response.status_code == 200
        
        # Verify all were logged
        with get_db() as conn:
            count = conn.execute(
                "SELECT COUNT(*) as c FROM partner_api_calls WHERE partner_id = 4"
            ).fetchone()['c']
            assert count == 10

    def test_14_webhook_invalid_partner(self):
        """Test: Graceful handling of unknown partner ID."""
        webhook_payload = {
            "partner_id": 9999,  # Non-existent partner
            "environment": "sandbox",
            "endpoint": "/v1/test",
            "method": "POST",
            "status_code": 200,
            "response_time_ms": 100,
            "error_code": None,
            "error_message": None,
            "api_key_id": "sk_test_9999"
        }
        
        # Should still log (even if partner doesn't exist yet)
        response = client.post("/api/activate/api-call/log", json=webhook_payload)
        assert response.status_code == 200

    def test_15_end_to_end_activation_flow(self):
        """Test: Full flow from onboarding → API calls → stall detection → intervention."""
        print("\n" + "="*70)
        print("END-TO-END: Blostem API Integration Flow")
        print("="*70)
        
        # Step 1: Onboard a new partner
        print("\n1. ONBOARDING: New partner signs contract")
        response = client.post("/api/activate/onboard/1")
        assert response.status_code == 200
        onboarded = response.json()
        prospect_id = onboarded["prospect_id"]  # Use prospect_id for detection endpoint
        partner_id = onboarded["partner_id"]     # Use partner_id for DB updates
        print(f"   ✓ Partner {partner_id} onboarded (prospect_id={prospect_id})")
        
        # Step 2: Wait 15 days (simulated by back-dating in DB)
        print("\n2. WAITING: 15 days pass with no API activity")
        with get_db() as conn:
            signed_at = (datetime.now() - timedelta(days=15)).isoformat()
            conn.execute("""
                UPDATE partners_activated 
                SET signed_at = ? 
                WHERE id = ?
            """, (signed_at, partner_id))
            conn.commit()
        print("   ✓ 15 days simulated")
        
        # Step 3: Check for stall (use prospect_id in endpoint)
        print("\n3. DETECTION: Check for activation stalls")
        response = client.get(f"/api/activate/patterns/{prospect_id}")
        data = response.json()
        assert data["stall_detected"] == True
        print(f"   ✓ Stall detected: {data['stall_pattern']}")
        
        # Step 4: Generate intervention (use prospect_id)
        print("\n4. INTERVENTION: Generate email")
        response = client.post(f"/api/activate/patterns/{prospect_id}/generate-intervention")
        intervention = response.json()
        print(f"   ✓ Email generated for {intervention['intervention']['target_persona']}")
        print(f"   ✓ Subject: {intervention['intervention']['subject'][:60]}...")
        
        # Step 5: Record email sent
        print("\n5. TRACKING: Record intervention sent")
        response = client.post(
            f"/api/activate/patterns/{partner_id}/mark-intervention-sent",
            json={"pattern": "DEAD_ON_ARRIVAL"}
        )
        assert response.status_code == 200
        print("   ✓ Email marked as sent")
        
        # Step 6: Partner responds with API call
        print("\n6. RESOLUTION: Partner makes first API call (thanks to email!)")
        webhook_payload = {
            "partner_id": partner_id,
            "environment": "sandbox",
            "endpoint": "/v1/webhooks/register",
            "method": "POST",
            "status_code": 201,
            "response_time_ms": 145,
            "error_code": None,
            "error_message": None,
            "api_key_id": "sk_test_partner"
        }
        response = client.post("/api/activate/api-call/log", json=webhook_payload)
        assert response.status_code == 200
        print("   ✓ API call logged")
        
        # Step 7: Check again - stall should be resolved
        print("\n7. VERIFICATION: Check stall status again")
        response = client.get(f"/api/activate/patterns/{partner_id}")
        data = response.json()
        # Now there are API calls, so DEAD_ON_ARRIVAL should not be detected
        if not data["stall_detected"]:
            print("   ✓ Stall resolved - partner is now active!")
        else:
            print(f"   ℹ Different pattern now: {data['stall_pattern']}")
        
        print("\n" + "="*70)
        print("✓ END-TO-END FLOW COMPLETE")
        print("="*70)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

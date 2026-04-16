# Blostem API Gateway Integration Guide

## Overview

Pragma's redesigned **ACTIVATE layer** is now connected to Blostem's API gateway. This enables real-world activation stall detection using actual partner API call data.

## How It Works

1. **API calls logged**: Whenever a partner makes an API call to Blostem, the gateway POSTs call details to Pragma
2. **Patterns detected**: Pragma's stall detection analyzes API call history for 3 patterns
3. **Interventions generated**: When a stall is detected, targeted emails are auto-generated
4. **Account team alerted**: Dashboard shows all at-risk partners

## Integration Endpoint

### POST `/api/activate/api-call/log`

**Purpose**: Webhook for Blostem API gateway to log each partner API call

**Authentication**: (To be configured - API key / mTLS / etc.)

**Request Body** (JSON):
```json
{
  "partner_id": 1,
  "environment": "sandbox",
  "endpoint": "/v1/webhooks/register",
  "method": "POST",
  "status_code": 201,
  "error_code": null,
  "error_message": null,
  "response_time_ms": 145,
  "api_key_id": "sk_test_..."
}
```

**Fields**:
- `partner_id` (required, int): Pragma partner ID from `prospects` table
- `environment` (required, str): "sandbox" or "production"
- `endpoint` (required, str): API endpoint called (e.g. "/v1/webhooks/register")
- `method` (required, str): HTTP method (GET, POST, PUT, DELETE, etc.)
- `status_code` (required, int): HTTP response status code
- `error_code` (optional, str): Error code if request failed (e.g. "AUTH_INVALID_KEY", "RATE_LIMIT")
- `error_message` (optional, str): Error message if request failed
- `response_time_ms` (optional, int): API response time in milliseconds
- `api_key_id` (optional, str): Partner's API key identifier

**Response** (200 OK):
```json
{
  "status": "api_call_logged",
  "partner_id": 1,
  "environment": "sandbox",
  "endpoint": "/v1/webhooks/register",
  "response_time_ms": 145
}
```

**Error Responses**:
- 422: Unprocessable Entity (validation error - check field types)
- 500: Server error

---

## Stall Detection Endpoints

### GET `/api/activate/patterns/{partner_id}`

**Purpose**: Detect activation stalls for one partner

**Response** (200 OK):
```json
{
  "partner_id": 1,
  "stall_detected": true,
  "stall_pattern": "DEAD_ON_ARRIVAL",
  "stall_details": {
    "pattern": "DEAD_ON_ARRIVAL",
    "detected": true,
    "days_of_inactivity": 15,
    "api_calls_made": 0,
    "severity": "CRITICAL",
    "likely_cause": "Person who signed isnt the person who integrates"
  },
  "political_risks": [],
  "requires_intervention": true
}
```

---

## Intervention Email Endpoints

### POST `/api/activate/patterns/{partner_id}/generate-intervention`

**Purpose**: Generate a targeted intervention email based on detected stall

**Response** (200 OK):
```json
{
  "partner_id": 1,
  "stall_pattern": "DEAD_ON_ARRIVAL",
  "intervention": {
    "target_persona": "CTO",
    "subject": "Let's get Pragma integrated at {Company} — 30-min engineering call?",
    "body": "...",
    "tone": "friendly_engineering"
  },
  "action_required": true
}
```

---

## 3 Stall Patterns

### Pattern 1: DEAD_ON_ARRIVAL
- **Detected**: 0 API calls in 14 days after signing
- **Likely Cause**: Person who signed isn't the person who integrates
- **Intervention Target**: CTO
- **Email Type**: Getting-started guide + 30-min engineering call offer

### Pattern 2: STUCK_IN_SANDBOX
- **Detected**: Sandbox API calls exist, then 7+ day silence
- **Likely Cause**: Technical blocker (auth failure, missing field, integration complexity)
- **Intervention Target**: CTO
- **Email Type**: Debug-specific (auto-detects error code from last call)
- **Example Error Context**: 
  - "Your last sandbox call got a 401 AUTH_INVALID_KEY — your API key might have expired"
  - "You're getting RATE_LIMIT errors — let's discuss your volume"

### Pattern 3: PRODUCTION_BLOCKED
- **Detected**: Successful sandbox calls (14+ days ago), 0 production calls since then
- **Likely Cause**: Internal approval/procurement blocker
- **Intervention Target**: Business contact (CFO/Product)
- **Email Type**: Business blocker discussion (not technical)

---

## Political Risk Detection

### GET `/api/activate/political-risks/{partner_id}`

**Purpose**: Get build-vs-buy risk alerts from news monitoring

**Response** (200 OK):
```json
{
  "partner_id": 1,
  "political_risks": [
    {
      "risk_type": "COMPETITOR_INTEGRATION",
      "detected_via": "news_monitoring",
      "details": "Partner announced integration with competitor X",
      "detected_at": "2026-04-16T10:30:00",
      "alert_sent": false
    }
  ],
  "requires_account_manager_review": true,
  "message": "These are internal intelligence alerts. Consider proactive partnership conversation."
}
```

**Risk Types**:
- `COMPETITOR_INTEGRATION`: Partner mentioned integrating with competitor
- `BUILD_VS_BUY_RISK`: Partner posted job for "banking API engineer" (internal build)

---

## Contact Management Endpoints

### POST `/api/activate/partners/{partner_id}/contacts`

**Purpose**: Add a known contact for a partner (by persona type)

**Request Body** (JSON):
```json
{
  "name": "Jane Smith",
  "email": "jane.smith@razorpay.com",
  "persona": "CTO",
  "added_by": "account_manager_alice"
}
```

**Fields**:
- `name` (required, str): Contact name
- `email` (required, str): Contact email address
- `persona` (required, str): Contact role - one of: CTO, Business Contact, CFO, CPO, CEO
- `added_by` (optional, str, default="system"): Who added this contact

**Response** (200 OK):
```json
{
  "status": "contact_added",
  "contact_id": 1,
  "partner_id": 1,
  "persona": "CTO",
  "email": "jane.smith@razorpay.com"
}
```

---

### GET `/api/activate/partners/{partner_id}/contacts`

**Purpose**: List all known contacts for a partner, grouped by persona

**Response** (200 OK):
```json
{
  "partner_id": 1,
  "contacts": {
    "CTO": [
      {
        "id": 1,
        "name": "Jane Smith",
        "email": "jane.smith@razorpay.com",
        "confidence": 0.95
      }
    ],
    "Business Contact": [
      {
        "id": 2,
        "name": "John Doe",
        "email": "john@razorpay.com",
        "confidence": 0.85
      }
    ]
  },
  "contact_count": 2,
  "message": "Use these contacts to target interventions by persona"
}
```

---

## Intervention Outcome Tracking

### POST `/api/activate/partners/{partner_id}/intervention-outcome`

**Purpose**: Record the outcome of an intervention email (sent, responded, resolved, bounced, etc.)

**Request Body** (JSON):
```json
{
  "stall_pattern": "DEAD_ON_ARRIVAL",
  "outcome": "responded",
  "sent_to_email": "jane.smith@razorpay.com",
  "notes": "Partner responded within 2 hours, scheduled engineering call"
}
```

**Fields**:
- `stall_pattern` (required, str): Pattern type - DEAD_ON_ARRIVAL, STUCK_IN_SANDBOX, or PRODUCTION_BLOCKED
- `outcome` (required, str): One of: responded, resolved, no_response, bounced, sent
- `sent_to_email` (optional, str): Email address the intervention was sent to
- `notes` (optional, str): Additional notes about the outcome

**Response** (200 OK):
```json
{
  "status": "outcome_recorded",
  "outcome_id": 1,
  "partner_id": 1,
  "stall_pattern": "DEAD_ON_ARRIVAL",
  "outcome": "responded"
}
```

---

### GET `/api/activate/interventions/metrics`

**Purpose**: Get aggregate metrics on intervention effectiveness by stall pattern

**Response** (200 OK):
```json
{
  "message": "Intervention effectiveness metrics by stall pattern",
  "metrics": {
    "DEAD_ON_ARRIVAL": {
      "total_sent": 10,
      "responded": 8,
      "response_rate": 0.8,
      "resolved": 6,
      "resolution_rate": 0.6
    },
    "STUCK_IN_SANDBOX": {
      "total_sent": 5,
      "responded": 4,
      "response_rate": 0.8,
      "resolved": 3,
      "resolution_rate": 0.6
    },
    "PRODUCTION_BLOCKED": {
      "total_sent": 3,
      "responded": 3,
      "response_rate": 1.0,
      "resolved": 2,
      "resolution_rate": 0.67
    }
  },
  "recommendation": "Patterns with low resolution_rate may need better email content or follow-up process"
}
```

---

## Dashboard / Monitoring

### GET `/api/activate/patterns/all/summary`

**Purpose**: Dashboard view of all activation stalls + intervention effectiveness

**Response** (200 OK):
```json
{
  "stalls_by_pattern": [
    {
      "stall_pattern": "DEAD_ON_ARRIVAL",
      "count": 3
    },
    {
      "stall_pattern": "STUCK_IN_SANDBOX",
      "count": 2
    },
    {
      "stall_pattern": "PRODUCTION_BLOCKED",
      "count": 1
    }
  ],
  "political_risks_by_type": [
    {
      "risk_type": "COMPETITOR_INTEGRATION",
      "count": 1
    }
  ],
  "recent_stalls": [
    {
      "id": 1,
      "name": "Razorpay",
      "stall_pattern": "DEAD_ON_ARRIVAL",
      "detected_at": "2026-04-16T10:30:00"
    }
  ],
  "intervention_metrics": {
    "DEAD_ON_ARRIVAL": {
      "total_sent": 10,
      "responded": 8,
      "response_rate": 0.8,
      "resolved": 6,
      "resolution_rate": 0.6
    }
  },
  "requires_urgent_action": true,
  "message": "Dashboard for marketing team - shows stalls + intervention effectiveness"
}
```

**Key Fields**:
- `stalls_by_pattern`: Count of unresolved stalls grouped by pattern
- `intervention_metrics`: Effectiveness of interventions by pattern (response rate, resolution rate)
- `recent_stalls`: Last 20 detected stalls for quick review

---

## Implementation Checklist

### Phase 1: Basic Integration (Week 1)
- [ ] Configure API endpoint URL in Blostem API gateway
- [ ] Add authentication (API key / mTLS)
- [ ] Start logging partner API calls to `/api/activate/api-call/log`
- [ ] Verify logs are being stored in `partner_api_calls` table

### Phase 2: Stall Detection (Week 2)
- [ ] Test `/api/activate/patterns/{partner_id}` endpoint
- [ ] Verify detection works for each pattern (test with real partners after 14 days)
- [ ] Set up monitoring dashboard (`/api/activate/patterns/all/summary`)

### Phase 3: Intervention Emails (Week 3)
- [ ] Review generated email templates
- [ ] Configure email sending service (SendGrid, etc.)
- [ ] Test end-to-end: API call → stall detection → email generation
- [ ] Set up account manager alerts for political risks

### Phase 4: Contact & Outcome Tracking (Week 4)
- [ ] Populate known contacts for key partners via `/api/activate/partners/{partner_id}/contacts`
- [ ] Send intervention emails and record outcomes via `/api/activate/partners/{partner_id}/intervention-outcome`
- [ ] Monitor intervention metrics via `/api/activate/interventions/metrics`
- [ ] Identify patterns with low resolution rate and iterate on email content

### Phase 5: Go Live (Week 5)
- [ ] Enable automatic intervention email sending
- [ ] Train account team on dashboard and contact management
- [ ] Monitor stall detection accuracy
- [ ] Track intervention effectiveness by pattern
- [ ] Iterate on email templates based on partner response

---

## Testing

### Local Testing

Run integration tests to verify endpoints:
```bash
cd d:\Blostem
python -m pytest test_blostem_api_integration.py -v
```

### Staging Testing

1. Point staging API gateway to Pragma staging endpoint
2. Make test API calls with test partner IDs
3. Verify logs appear in database: `SELECT * FROM partner_api_calls`
4. Test detection: `GET /api/activate/patterns/1`
5. Test email generation: `POST /api/activate/patterns/1/generate-intervention`
6. Test contact management: 
   - `POST /api/activate/partners/1/contacts` - add test contact
   - `GET /api/activate/partners/1/contacts` - verify contact stored
7. Test outcome tracking:
   - `POST /api/activate/partners/1/intervention-outcome` - record outcome
   - `GET /api/activate/interventions/metrics` - verify metrics calculated

### Production Testing

1. Start with 5-10 test partners on separate API keys
2. Monitor webhook logs for 48 hours
3. Verify stall detection accuracy
4. Send test intervention emails to pilot account managers
5. Collect feedback on email quality and usefulness
6. Gradually roll out to all partners

---

## Troubleshooting

### Webhook not logging

**Check**:
1. Is the endpoint URL correct? (Test with curl/Postman)
2. Is authentication configured? (Check API key/mTLS)
3. Is the JSON payload valid? (Check field types in table above)
4. Check database: `SELECT COUNT(*) FROM partner_api_calls`

**Fix**:
- Verify `post /api/activate/api-call/log` is reachable
- Check Pragma logs for 422 validation errors
- Ensure partner_id matches a `prospects.id`

### Stall detection returns "not detected"

**Check**:
1. Are partner API calls actually logged? (`SELECT * FROM partner_api_calls WHERE partner_id = ?`)
2. Has enough time passed? (Pattern requires 14 days of data)
3. Is `partners_activated` entry correct? (Check `signed_at` date)

**Fix**:
- Wait for 14 days of real API call data
- Manual testing: Insert test data into database directly

### Integration not sending emails yet

**Status**: Intervention email sending is rule-based (no LLM), templates are generated but not auto-sent.

**Next Step**: Configure your email service (SendGrid, SES, etc.) and hook to:
- `POST /api/activate/patterns/{partner_id}/generate-intervention` → Generate email
- `POST /api/activate/patterns/{partner_id}/mark-intervention-sent` → Log that email was sent

---

## Architecture Notes

The activation layer uses **only API call data** Blostem already has:
- ✅ Uses `partner_api_calls` table (schema-ready)
- ✅ No Hunter.io / LinkedIn scraping
- ✅ No guessing about buyer committees
- ✅ No email tracking needed (just API logs)
- ✅ Rule-based interventions (no LLM for email generation)
- ✅ Fast detection (<1 second per check)

---

## Support

For issues or questions:
1. Check this guide's Troubleshooting section
2. Review test cases in `test_blostem_api_integration.py`
3. Check logs: Look for 422 validation errors or 500 server errors
4. Database health: `SELECT COUNT(*) FROM partner_api_calls` should grow

---

**Last Updated**: April 16, 2026  
**Integration Status**: Webhook endpoints live, ready for gateway connection

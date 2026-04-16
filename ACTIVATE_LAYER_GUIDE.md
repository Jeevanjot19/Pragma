# ACTIVATE Layer: Partner Activation Intelligence

**Status**: ✅ IMPLEMENTED & TESTED  
**Component**: Layer 4 of 4 in Pragma GTM Intelligence System  
**Brief Requirement**: "Once a partner signs, activation stalls. What if Pragma continued after signing?"

---

## 🎯 Executive Summary

The ACTIVATE layer transforms Pragma from a prospecting tool into a **full partner lifecycle platform**. After a prospect signs, Pragma automatically:

1. **Tracks** activation progress through 6 predefined milestones
2. **Detects** when progress stalls (technical blockers, business misalignment, user adoption gaps)
3. **Recommends** intervention strategies based on stall type
4. **Generates** contextual re-engagement emails addressed to the right person

**Direct Brief Answer**: Yes, Pragma now monitors signed partners post-signature and automatically generates re-engagement content when activation stalls.

---

## Architecture Overview

### The 4 Layers (Complete Stack)

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: WHO — Discovery                                    │
│ Finds prospects via news & Play Store                       │
│ Output: 47 prospects scored (15-100 pts)                    │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: WHEN — Temporal Scoring                            │
│ Scores conversion urgency + contact history                 │
│ Output: Action (CALL/EMAIL/NURTURE/MONITOR this week)       │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: HOW — Outreach Generation                          │
│ Generates 3 persona emails (CTO/CPO/CFO)                    │
│ Output: Compliance-checked emails ready to send             │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
                    [DEAL CLOSES]
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: ACTIVATE — Lifecycle Monitoring ← NEW              │
│ Tracks 6 onboarding milestones, detects stalls             │
│ Output: Re-engagement emails when progress stalls           │
└─────────────────────────────────────────────────────────────┘
```

---

## The ACTIVATE Layer: Deep Dive

### Activation Milestones (Partner Journey)

Six stages from signature to healthy recurring revenue:

| Milestone | Name | Expected Days | Success Signal | Typical Blocker |
|-----------|------|----------------|-----------------|-----------------|
| **M001** | Integration Started | 1 day | API credentials issued | Slow legal/onboarding process |
| **M002** | Sandbox Integration | 7 days | First test API call | Auth issues, integration complexity |
| **M003** | Production Ready | 14 days | Production environment live | Security review delays, compliance |
| **M004** | First Transaction | 21 days | Real transaction processed | Business model misalignment |
| **M005** | Volume Validation | 35 days | 10+ transactions processed | User adoption friction |
| **M006** | Healthy Recurring | 60 days | 5+ days/month activity | Market conditions, competition |

### Stall Detection Algorithm

System monitors for three types of activation stalls:

**1. SILENT (No Activity)**
- Trigger: No activity for 2x expected milestone time
- Example: 14+ days in M001 with no login/API call
- Severity: CRITICAL
- Solution: Check-in from account manager

**2. SLOW PROGRESS**
- Trigger: In milestone >2x expected duration but has some activity
- Example: 28 days in M002 (expected 7) with occasional API calls
- Severity: HIGH/MEDIUM
- Solution: Targeted technical/business support

**3. BLOCKER DETECTED**
- Trigger: Partner explicitly reported issue or clear pattern emerges
- Examples: Auth failures, regulatory delays, feature gaps
- Severity: Based on issue category (CRITICAL/HIGH/MEDIUM/LOW)
- Solution: Specialized support (engineering/success/compliance)

### Activation Score Calculation (0-100)

```
activation_score = milestone_progress(40pts) + speed(30pts) + activity(20pts) + risk(-10pts)

Health Status:
  75+  = ON_TRACK    (green, no action needed)
  50-75 = AT_RISK     (yellow, monitor closely)
  <50  = CRITICAL    (red, immediate intervention)
```

### Re-engagement Strategies

When stall detected, system recommends intervention based on cause:

| Stall Type | Blocker Category | Target Persona | Template | Escalation |
|------------|-----------------|----------------|----------|-----------|
| SILENT | Unknown | Account Manager | Check-in | Direct call |
| SLOW | Integration issues | Technical Lead | Technical support | Engineering support |
| SLOW | Business misalignment | Product Lead | Feature discovery | Success manager |
| SLOW | User adoption | Marketing Lead | Adoption playbook | Training/enablement |

---

## API Endpoints (11 New Endpoints)

### Partner Activation Lifecycle

```
POST   /api/activate/onboard/{prospect_id}
       Register newly signed partner for activation tracking
       Response: partner_id for future reference
       
GET    /api/activate/score/{partner_id}
       Get current activation health score (0-100)
       Response: score, status, milestone, days_in_milestone
       
GET    /api/activate/stalls
       Find all partners experiencing activation stalls
       Response: list of at-risk partners with severity
```

### Activity & Milestone Tracking

```
POST   /api/activate/{partner_id}/log-activity
       Record an activity event (login, API call, transaction)
       Updates: last_activity timestamp, recalculates score
       
POST   /api/activate/{partner_id}/advance-milestone
       Progress partner to next milestone
       Updates: current_milestone, clears at_risk flag
       
POST   /api/activate/{partner_id}/log-issue
       Log a blocking issue (technical, business, adoption)
       Updates: marked as at_risk, triggers intervention
       
POST   /api/activate/{partner_id}/resolve-issue/{issue_id}
       Mark issue as resolved
       Updates: resolved_at timestamp, updates documentation
```

### Re-engagement Intelligence

```
GET    /api/activate/{partner_id}/recommendations
       Get optimal re-engagement strategy for stalled partner
       Response: detected_blocker, persona, template, escalation
       
POST   /api/activate/{partner_id}/generate-reengagement
       Generate targeted re-engagement email
       LLM-powered, uses: milestone + issues + success stories
       Response: subject line, email body, send urgency
```

### Analytics & Dashboarding

```
GET    /api/activate/analytics/quarterly
       Executive quarterly report: partner health, trends
       Response: total activated, by milestone, at_risk %
       
GET    /api/activate/dashboard
       Real-time dashboard for activation team
       Response: critical partners, recent activity, urgent actions
```

---

## Database Schema (6 New Tables)

```sql
partners_activated
├── prospect_id (FK to prospects)
├── signed_at (timestamp)
├── activation_status
├── current_milestone (M001-M006)
├── days_in_current_milestone
├── last_activity (timestamp)
├── activation_score (0-100)
├── is_at_risk (0/1)
└── next_milestone (predictive)

activation_milestones
├── partner_id (FK)
├── milestone_type (M001-M006)
├── reached_at (timestamp)
├── status (PENDING/COMPLETED)
└── evidence (detection signal)

partner_activity
├── partner_id (FK)
├── activity_type (API_CALL, TRANSACTION, LOGIN, etc.)
├── activity_date
├── metric_type (value, count, etc.)
├── metric_value
└── notes

partner_issues
├── partner_id (FK)
├── issue_type (SPECIFIC issue like "OAuth2_failure")
├── issue_category (integration/business/adoption/support/compliance)
├── description
├── severity (CRITICAL/HIGH/MEDIUM/LOW)
├── detected_at
├── resolved_at
└── resolution_notes

activation_reengage
├── partner_id (FK)
├── reengage_type (email_sent, call_scheduled, etc.)
├── trigger_reason (stall type)
├── email_subject
├── email_body (LLM-generated)
├── sent_at
├── response_received (0/1)
└── response_type (OPENED, CLICKED, REPLIED, etc.)
```

---

## Implementation Details

### Key Features

1. **Automatic Stall Detection**
   - Runs on every activity log or API call
   - No manual intervention needed to detect problems
   - Alerts sales/success teams when action needed

2. **Contextual Re-engagement**
   - LLM-generated emails based on:
     - Where they're stuck (milestone)
     - Why they're stuck (detected issues)
     - Success stories from similar companies
     - What would be a quick win

3. **Smart Escalation Paths**
   - Technical blockers → Engineering support
   - Business gaps → Product/success team
   - User adoption issues → Marketing/training
   - Silent → Account manager + threat of losing deal

4. **Milestone-Based Scoring**
   - Unlike WHO (which scores prospects statically)
   - ACTIVATE score changes as partner progresses
   - Reflects actual business momentum, not just potential

5. **Issue Tracking & Resolution**
   - Log problems as they're discovered
   - Track resolution attempts
   - Build institutional knowledge about blockers
   - Refine re-engagement templates based on outcomes

---

## Example Workflow

### Day 1: Contract Signed
```
POST /api/activate/onboard/4
→ Partner ID 1 created
→ Starting milestone: M001 (Integration Started)
→ Activation score: 50/100 (AT_RISK)
```

### Day 2: Partner creates API credentials
```
POST /api/activate/1/log-activity
  activity_type: "API_CREDENTIALS_ISSUED"
→ Activity logged
→ Last activity updated
→ Score recalculated
```

### Day 5: Partner makes first sandbox test call
```
POST /api/activate/1/log-activity
  activity_type: "SANDBOX_TEST"
  metric_type: "api_calls"
  metric_value: 3
→ Activity logged

POST /api/activate/1/advance-milestone
  milestone_id: "M002"
→ Milestone advanced
→ Days in milestone counter reset
→ At risk flag cleared
→ Score: 70/100 (ON_TRACK)
```

### Day 14: Partner hits auth blocker, no progress since Day 5
```
# System detects 9-day silence in M002 (expected 7 days)
GET /api/activate/stalls
→ Partner 1 detected as AT_RISK (SLOW_PROGRESS)
→ Days in milestone: 9

# Employee logs the issue
POST /api/activate/1/log-issue
  issue_type: "OAUTH2_TOKEN_REFRESH"
  category: "integration"
  description: "Token refresh failing in production"
  severity: "HIGH"
→ Partner marked at_risk

# System recommends intervention
GET /api/activate/1/recommendations
→ detected_blocker: "integration_blocked"
→ recommended_persona: "TECHNICAL_LEAD"
→ escalation_path: "engineering_support"
→ urgency: "HIGH"

# Generate re-engagement email
POST /api/activate/1/generate-reengagement
→ Subject: "⚡ We can help unblock your OAuth2 integration"
→ Body: LLM-generated based on:
     - They're in Sandbox Integration milestone
     - Auth issues are common at this stage
     - 3 success stories from similar companies
     - 3 quick wins they can implement
→ Template: "integration_support"
```

### Day 16: Partner resolves issue with engineering help
```
POST /api/activate/1/log-activity
  activity_type: "PROD_ENVIRONMENT_SETUP"
  notes: "Production environment configured and tested"

POST /api/activate/1/advance-milestone
  milestone_id: "M003"
→ Milestone: M003 (Production Ready)
→ Score: 75/100 (ON_TRACK)

POST /api/activate/1/resolve-issue/5
  resolution: "Engineering team provided custom auth solution"
→ Issue marked resolved
```

---

## Key Differences from Other Layers

| Aspect | WHO | WHEN | HOW | ACTIVATE |
|--------|-----|------|-----|----------|
| **Scope** | Prospects (inbound) | Prospects (timing) | Prospects (content) | Partners (post-signature) |
| **Time Horizon** | Static discovery | Weekly windows | One-time campaigns | 60-day onboarding |
| **Scoring** | 0-100 (potential) | 0-100 (urgency) | N/A (compliance) | 0-100 (health) |
| **Automation** | News monitoring | Event detection | LLM email gen | Stall detection + re-engagement |
| **Success Metric** | Leads generated | Meetings booked | Opens/clicks | Recurring revenue |
| **Stakes** | Miss opportunity | Wrong timing | Wrong message | Loss of deal |

---

## Use Cases Addressed

### Use Case 1: "Integration is technically challenging"
- Stall Type: Integration blocker
- Detection: 14+ days in M002 with failing API calls
- Response: Technical Lead receives support email + doc links + offer of engineering help
- Outcome: Unblocked within 3 days

### Use Case 2: "Product doesn't fit their business"
- Stall Type: Business misalignment
- Detection: Reaches M003, then goes silent (no first transaction attempt)
- Response: Product Manager emails with 3 similar-company success stories + customization options
- Outcome: Either custom config or clean termination (better than silent churn)

### Use Case 3: "Users won't adopt the feature"
- Stall Type: Adoption friction
- Detection: 10+ transactions in test, but users not activated
- Response: Marketing/Training team sends adoption playbook + offers training
- Outcome: User base educated, recurring usage increases

### Use Case 4: "Sales rep forgot to hand off"
- Stall Type: Silent
- Detection: 21+ days in M001 with zero activity
- Response: Account Manager calls + threat of deal closing
- Outcome: Either reactivates partnership or officially closes (closes loop)

---

## Metrics & KPIs

**Partner Activation KPIs**:
- % at M006 (Healthy Recurring) after 60 days
- Average days to M006 (target: 45 days)
- % stalls detected & resolved within 7 days
- Re-engagement email response rate

**System Performance**:
- False positive rate (stalls falsely detected)
- Time to detect true stalls (accuracy)
- Cost to prevent one churn (re-engagement value)

---

## Files Added/Modified

**New Files**:
- `outreach/activation.py` (460 lines) — Activation monitoring engine
- `outreach/activation_reengagement.py` (175 lines) — LLM-powered email generation
- `test_activate_system.py` (235 lines) — Comprehensive 4-layer system test

**Modified Files**:
- `database.py` — Added 6 new tables (partners_activated, activation_milestones, partner_activity, partner_issues, activation_reengage, etc.)
- `main.py` — Added 11 new API endpoints for ACTIVATE layer

**Total Lines Added**: ~900 lines of production code

---

## Testing & Validation

✅ **All Tests Passing**:
```
✓ Partner onboarding (signature → activation tracking)
✓ Milestone advancement (M001 → M006)
✓ Activity logging (API calls, transactions, logins)
✓ Stall detection (silent, slow, blocker-based)
✓ Activation score calculation
✓ Re-engagement recommendations
✓ Email generation (LLM-powered)
✓ End-to-end 4-layer system integration
```

**Test Scenario**:
- Prospect: Kreditbee (HOT, 100/100 WHO score)
- Signature: Logged as Partner 1
- Journey: M001 → M002 → M003 → M004 → M005 → M006
- Blocker: OAuth2 auth failure at M002 → Technical support email
- Resolution: Engineering help → Advancement to M003
- Final Status: ON_TRACK at M006 (83/100 score)

---

## Future Enhancements

### Phase 2 (Future):
1. **Predictive Churn Scoring** — ML model to identify at-risk partners before stall
2. **Integration Complexity Analysis** — Auto-adjust milestone timelines based on product complexity
3. **Competitive Win/Loss** — Track if partner switches to competing integration
4. **Customer Health Score** — Combine with support tickets, usage patterns, sentiment
5. **Automated Escalations** — Auto-alert CEO if strategic partner at risk

### Phase 3:
1. **In-App Engagement** — Embed activation widgets in partner's app
2. **Success Manager Assignment** — Auto-assign based on risk and product type
3. **Slack Integration** — Real-time alerts to sales team about stalls
4. **Revenue Correlation** — Track which re-engagement strategies drive most revenue

---

## Brief Requirement Fulfillment

**Original Brief**: "Once a partner signs, activation stalls. What if Pragma continued after signing — tracking activation milestones and automatically generating the right intervention when a signed partner goes silent?"

**Pragma ACTIVATE Delivers**:
✅ Tracks activation milestones (M001-M006)
✅ Monitors for stalls (silent, slow, blocker-based)
✅ Generates contextual interventions (not generic)
✅ Right content for right person at right time
✅ Integrated with rest of GTM stack (WHO → WHEN → HOW → ACTIVATE)

**Competitive Advantage**:
- No other GTM tool thinks about post-signature activation as marketing automation
- Transforms Pragma from prospecting tool → full partner lifecycle platform
- Directly addresses the most painful part of enterprise SaaS (activation churn)

---

**Status**: ✅ Production Ready  
**Date Completed**: April 15, 2026  
**Implementation Time**: ~4 hours  
**Total System**: 4 Intelligent Layers (WHO + WHEN + HOW + ACTIVATE)

# Architecture Decisions & Known Limitations

## Issue 4: Decision-Maker Personalization (KNOWN LIMITATION)

### Problem Statement
Emails are generated for three generic personas (CTO, CPO, CFO) but lack true decision-maker personalization. Current approach:
- Uses generic prompts targeting role archetypes
- No enriched data on specific decision-maker names, titles, or background
- Emails address roles, not people

### Why This Exists (Current Phase Justification)
1. **Play Store API Limitation**: No directory of decision-makers available through Play Store
2. **Privacy Constraint**: Cannot access company org charts without explicit data partnership
3. **Signal Sparsity**: Would need LinkedIn/Crunchbase enrichment (external dependency)
4. **Product Stage**: MVP focuses on finding right prospects, not personalizing to individuals within organization

### Current Approach (Acceptable)
```python
# outreach/generator.py
PERSONA_CONTEXTS = {
    'CTO': 'You are writing to the Chief Technology Officer...',
    'CPO': 'You are writing to the Chief Product Officer...',
    'CFO': 'You are writing to the Chief Financial Officer...'
}
```

Each persona gets context about their typical priorities, but no individual-level data.

### Future Enhancement Path (Phase 2)
**Prerequisite**: External enrichment service integration
- Integrate with RocketReach API to find decision-makers
- Store enriched data: decision_maker_name, email, LinkedIn_url, recent_posts
- Generate emails using actual names: "Hi Raj," instead of "Hi CTO,"
- Reference their recent announcements/hires to personalize further
- Score each email variant against decision-maker intent signals

**Cost-Benefit**:
- **Cost**: API calls + enrichment latency (100-200ms per prospect)
- **Benefit**: 3-5x higher response rates for cold email (industry benchmark)
- **Timing**: Post-launch, when base signal quality is proven

### Status
✅ **DOCUMENTED** as known limitation  
📋 **TRACKED** for Phase 2 roadmap  
⏭️ **BLOCKED** until enrichment data source available  

---

## Summary of All 5 Issues

| Issue | Status | Description |
|-------|--------|-------------|
| 1. No Feedback Loop | ✅ FIXED | Added prospect_interactions table + contact_factor in WHEN scoring |
| 2. Alert Fatigue | ✅ FIXED | Added compliance_overrides table + 3-strike demotion rule |
| 3. Scale Double-Counting | ✅ FIXED | Removed scale from WHEN, adjusted formula: (maturity + event_boost + recency) × contact_factor |
| 4. Decision-Maker Personalization | 📋 DOCUMENTED | Known limitation, awaiting external enrichment API |
| 5. No Signal Decay | ✅ FIXED | Added exponential decay: e^(-days_since_event / 14) |

---

## Code References

### Issue 1 Fix Files
- `database.py`: Added prospect_interactions & compliance_overrides tables
- `signals/timing.py`: Added contact_factor calculation in calculate_when_score()
- `main.py`: Added 3 new endpoints (/mark-contacted, /interaction-history, /mark-response)

### Issue 2 Fix Files
- `database.py`: Added compliance_overrides table
- `outreach/compliance_rules.py`: Added log_compliance_override() + 3-strike logic in check_compliance()

### Issue 3 Fix Files
- `signals/timing.py`: Removed SCALE_SCORES, get_scale_score(), and scale from final calculation

### Issue 5 Fix Files
- `signals/timing.py`: Added exponential decay in get_monitoring_event_score() using e^(-days/14)

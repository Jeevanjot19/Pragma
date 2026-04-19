#!/usr/bin/env python3
"""
Trace what signals SHOULD be created for Bachatt from its news articles.
"""
print("=" * 70)
print("🔍 SIGNAL EXTRACTION LOGIC AUDIT")
print("=" * 70)

print("""
Current logic in discovery/news_monitor.py:

    # Funding + expansion
    if extracted.get('funding_detected') and expansion:
        add_signal(FUNDING_EXPANSION)
    
    # Leadership hire
    if extracted.get('leadership_hire') and extracted.get('leadership_role'):
        add_signal(LEADERSHIP_HIRE)
    
    # Competitor displacement
    if extracted.get('competitor_mentioned'):
        add_signal(DISPLACEMENT)

PROBLEMS FOUND:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🐛 BUG #1: Missing FUNDING-only signal
   ├─ If LLM detects funding_detected=True but expansion=[]
   ├─ Then NO signal is created (requires BOTH conditions)
   └─ Should create FUNDING signal even if no expansion detected

🐛 BUG #2: Leadership hire requires BOTH conditions
   ├─ If LLM detects leadership_hire=True but role is empty
   ├─ Then signal is skipped
   └─ Role should be required but we should handle missing gracefully

🐛 BUG #3: Expansion signals not being created directly
   ├─ LLM extracts expansion_signals = ['FD', 'Credit Cards']
   ├─ But these are only included in FUNDING_EXPANSION text
   ├─ Individual expansion signals should be created too
   └─ This reduces signal count

🐛 BUG #4: Multiple articles = duplicate PRODUCT_GAP signals
   ├─ If same company appears in 2 articles
   ├─ Then PRODUCT_GAP signal added twice (but add_signal dedupes by type+day)
   ├─ So you get max 1 PRODUCT_GAP per day anyway
   └─ Fine, but inefficient

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BACHELOR'S CASE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Article: "Bachatt raises $12 million in funding led by Accel..."

Expected LLM output:
  {
    "funding_detected": true,
    "funding_amount": "$12 million",
    "expansion_signals": ["fixed deposits", "wealth management"],
    "leadership_hire": false
  }

Current code would create:
  ✓ PRODUCT_GAP (always added)
  ✓ FUNDING_EXPANSION (because funding_detected AND expansion not empty)
  Total: 2 signals

But should create:
  ✓ PRODUCT_GAP
  ✓ FUNDING (because funding_detected=true)
  ✓ FUNDING_EXPANSION (because both detected)
  + Individual EXPANSION signals?
  Total: 3+ signals

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

IMPACT ON SCORE (Bachatt example):

Without fix:
  FUNDING_EXPANSION: H:3 → 25 + (25×0.5×2) = 50
  PRODUCT_GAP:       H:1 → 15
  Scale bonus:       +10
  Convergence:       +5 (only 1 event type: FUNDING)
  TOTAL: 80

With proper FUNDING signals:
  FUNDING:           H:multiple → higher base value
  FUNDING_EXPANSION: H:multiple → 50+ 
  PRODUCT_GAP:       H:1 → 15
  Scale bonus:       +10
  Convergence:       +5
  TOTAL: Could reach 90-100

""")

print("=" * 70)
print("RECOMMENDATION")
print("=" * 70)
print("""
1. Create FUNDING signal if funding_detected, regardless of expansion
2. Create FUNDING_EXPANSION signal if BOTH detected
3. This gives 2 signals per funding event instead of 1 or 0
4. Score increases by 25 points per additional signal

Expected impact:
  - Bachatt: 80 → 95-100
  - Other well-funded companies similar boost
  - Overall "This Week" tab will have 10-20 prospects instead of 0
""")

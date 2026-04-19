#!/usr/bin/env python3
"""
Manually recalculate Bachatt WHO score with the fixes:
1. Fixed signal extraction (FUNDING created even without expansion)
2. PRODUCT_GAP weight from config (35 instead of 15)
"""
print("=" * 70)
print("🔧 RECALCULATION WITH FIXES")
print("=" * 70)

# Bachatt's current signals:
# - 3x FUNDING_EXPANSION (HIGH)
# - 1x PRODUCT_GAP (HIGH)

from config import SIGNAL_WEIGHTS

print(f"\nSignal weights (updated): {SIGNAL_WEIGHTS}")

signal_counts = {
    'FUNDING_EXPANSION': {'HIGH': 3, 'MEDIUM': 0, 'LOW': 0},
    'PRODUCT_GAP': {'HIGH': 1, 'MEDIUM': 0, 'LOW': 0}
}

score = 0

print("\n1️⃣  SIGNAL SCORING (WITH FIXES):")
for signal_type, severities in sorted(signal_counts.items()):
    # Use fixed weight (from config)
    base = SIGNAL_WEIGHTS.get(signal_type, 10)
    
    signal_score = 0
    
    # First instance
    if severities['HIGH'] > 0:
        high_score = int(base * 1.0)
        signal_score += high_score
        print(f"  {signal_type}: HIGH → {base} × 1.0 = {high_score}")
    
    if severities['MEDIUM'] > 0:
        med_score = int(base * 0.6)
        signal_score += med_score
        print(f"  {signal_type}: MEDIUM → {base} × 0.6 = {med_score}")
    
    if severities['LOW'] > 0:
        low_score = int(base * 0.3)
        signal_score += low_score
        print(f"  {signal_type}: LOW → {base} × 0.3 = {low_score}")
    
    # Additional instances
    total_instances = severities['HIGH'] + severities['MEDIUM'] + severities['LOW']
    additional = total_instances - 1
    if additional > 0:
        add_score = int((base * 0.5) * additional)
        signal_score += add_score
        print(f"  {signal_type}: ADDITIONAL ({additional} extra) → {base} × 0.5 × {additional} = {add_score}")
    
    score += signal_score
    print(f"  Subtotal: {signal_score}, Running total: {score}\n")

print(f"2️⃣  SCALE BONUS: +10 (1,000,000+ installs)")
score += 10

print(f"3️⃣  CONVERGENCE BONUS: +5 (1 event type)")
score += 5

print(f"4️⃣  CAP AT 100: {score} → {min(score, 100)}")
score = min(score, 100)

print(f"\n{'='*70}")
print(f"✅ BACHATT NEW SCORE WITH FIXES: {score}/100")
print(f"{'='*70}")

if score >= 65:
    print(f"Status: HOT ✅")
elif score >= 35:
    print(f"Status: WARM")
else:
    print(f"Status: WATCH")

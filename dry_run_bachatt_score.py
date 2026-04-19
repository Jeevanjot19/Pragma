#!/usr/bin/env python3
"""
Manually dry-run WHO score calculation for Bachatt.
"""
from database import get_db
from config import SIGNAL_WEIGHTS

print("=" * 70)
print("🏃 MANUAL DRY-RUN: BACHATT WHO SCORE CALCULATION")
print("=" * 70)

with get_db() as conn:
    # Get Bachatt
    bachatt = conn.execute(
        "SELECT * FROM prospects WHERE name = 'Bachatt'"
    ).fetchone()
    
    if not bachatt:
        print("❌ Bachatt not found")
        exit(1)
    
    bachatt = dict(bachatt)
    prospect_id = bachatt['id']
    
    print(f"\nProspect: {bachatt['name']} (ID: {prospect_id})")
    print(f"Install count: {bachatt['install_count']}")
    print(f"Using competitor: {bachatt['using_competitor']}")
    print(f"Current WHO score in DB: {bachatt['who_score']}")
    
    # Get all signals
    signals = conn.execute(
        "SELECT signal_type, signal_strength FROM signals WHERE prospect_id = ? ORDER BY signal_type",
        (prospect_id,)
    ).fetchall()
    
    print(f"\n📊 SIGNALS ({len(signals)} total):")
    
    signal_counts = {}
    for signal in signals:
        signal_type = signal['signal_type']
        strength = signal['signal_strength']
        
        if signal_type not in signal_counts:
            signal_counts[signal_type] = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        signal_counts[signal_type][strength] += 1
        
        print(f"  • {signal_type:20} ({strength})")
    
    print(f"\n📈 SIGNAL SUMMARY:")
    for signal_type, severities in sorted(signal_counts.items()):
        total = severities['HIGH'] + severities['MEDIUM'] + severities['LOW']
        print(f"  {signal_type:20} → H:{severities['HIGH']} M:{severities['MEDIUM']} L:{severities['LOW']} (total: {total})")

print("\n" + "=" * 70)
print("🧮 SCORE CALCULATION (STEP BY STEP)")
print("=" * 70)

score = 0

print(f"\nSignal weights from config: {SIGNAL_WEIGHTS}")

print("\n1️⃣  SIGNAL SCORING:")
for signal_type, severities in sorted(signal_counts.items()):
    if signal_type == 'PRODUCT_GAP':
        base = 15
    else:
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

print(f"2️⃣  SCALE BONUS:")
SCALE_BONUSES = {
    '100,000,000+': 30,
    '50,000,000+': 25,
    '10,000,000+': 20,
    '5,000,000+': 15,
    '1,000,000+': 10,
    '500,000+': 7,
    '100,000+': 4,
}
install_count = bachatt.get('install_count', '')
print(f"  Install count: {install_count}")
for threshold, bonus in SCALE_BONUSES.items():
    if install_count and threshold == install_count:
        print(f"  Bonus: {threshold} → +{bonus}")
        score += bonus
        break
else:
    print(f"  No matching threshold (not in: {', '.join(SCALE_BONUSES.keys())})")

print(f"  Running total: {score}")

print(f"\n3️⃣  CONVERGENCE BONUS:")
event_types = {'FUNDING_EXPANSION', 'DISPLACEMENT', 'LEADERSHIP_HIRE', 'COMPETITOR_MOVE'}
event_signal_count = len(set(signal_counts.keys()) & event_types)
print(f"  Event-type signals found: {set(signal_counts.keys()) & event_types}")
print(f"  Event signal count: {event_signal_count}")
if event_signal_count >= 3:
    bonus = 20
    print(f"  Bonus (3+ event types): +{bonus}")
    score += bonus
elif event_signal_count >= 2:
    bonus = 10
    print(f"  Bonus (2 event types): +{bonus}")
    score += bonus
elif event_signal_count == 1:
    bonus = 5
    print(f"  Bonus (1 event type): +{bonus}")
    score += bonus
else:
    print(f"  No bonus (0 event types)")

print(f"  Running total: {score}")

print(f"\n4️⃣  DISPLACEMENT FLOOR:")
if bachatt.get('using_competitor'):
    print(f"  Using competitor: YES → min(score, 40)")
    score = max(score, 40)
    print(f"  Score after floor: {score}")
else:
    print(f"  Using competitor: NO → no change")

print(f"\n5️⃣  CAP AT 100:")
score = min(score, 100)
print(f"  Final score: {score}")

# Classify
if score >= 65:
    status = 'HOT'
elif score >= 35:
    status = 'WARM'
else:
    status = 'WATCH'

print(f"\n📌 CLASSIFICATION: {status}")

print("\n" + "=" * 70)
print(f"✅ FINAL: {bachatt['name']} → WHO SCORE = {score}/{100} ({status})")
print("=" * 70)

# Compare with DB
print(f"\n🔍 COMPARISON:")
print(f"  Calculated: {score}")
print(f"  In DB:      {bachatt['who_score']}")
if score == bachatt['who_score']:
    print(f"  ✅ MATCH")
else:
    print(f"  ⚠️  MISMATCH - need to recalculate")

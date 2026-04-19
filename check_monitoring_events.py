#!/usr/bin/env python3
"""
Check if monitoring_events table has data and what prospects they cover.
"""
import sqlite3
from database import get_db
from signals.timing import calculate_when_score

print("=" * 70)
print("📊 MONITORING EVENTS STATUS CHECK")
print("=" * 70)

with get_db() as conn:
    # Check total monitoring_events
    total_events = conn.execute(
        "SELECT COUNT(*) as cnt FROM monitoring_events"
    ).fetchone()['cnt']
    print(f"\n📡 Total monitoring_events in database: {total_events}")
    
    if total_events > 0:
        # Show sample events
        sample = conn.execute("""
            SELECT prospect_id, event_type, title, urgency, detected_at
            FROM monitoring_events
            ORDER BY detected_at DESC
            LIMIT 5
        """).fetchall()
        print("\n  Recent events:")
        for event in sample:
            print(f"    • Prospect {event['prospect_id']}: {event['event_type']} - {event['title']} ({event['urgency']}) @ {event['detected_at']}")
    
    # Check prospects with HOT/WARM status
    hot_warm = conn.execute("""
        SELECT COUNT(*) as cnt FROM prospects
        WHERE status IN ('HOT', 'WARM')
    """).fetchone()['cnt']
    print(f"\n🔥 HOT/WARM prospects: {hot_warm}")
    
    # Check which ones have monitoring events
    covered = conn.execute("""
        SELECT COUNT(DISTINCT prospect_id) as cnt
        FROM monitoring_events
        WHERE prospect_id IN (
            SELECT id FROM prospects WHERE status IN ('HOT', 'WARM')
        )
    """).fetchone()['cnt']
    print(f"  • With monitoring events: {covered}")
    print(f"  • WITHOUT monitoring events: {hot_warm - covered}")

print("\n" + "=" * 70)
print("📋 WHEN SCORE CALCULATION CHECK")
print("=" * 70)

with get_db() as conn:
    hot_warm_prospects = conn.execute("""
        SELECT id, name, who_score, when_score, status
        FROM prospects
        WHERE status IN ('HOT', 'WARM')
        ORDER BY who_score DESC
        LIMIT 10
    """).fetchall()

print(f"\nTop 10 HOT/WARM prospects:")
for p in hot_warm_prospects:
    score = calculate_when_score(p['id'])
    action = score['action']
    when_score = score['when_score']
    has_event = score['has_event_signal']
    print(f"  {p['name']:30} | WHO {p['who_score']:3.0f} → WHEN {when_score:3d} | {action:20} {'✓ event' if has_event else '✗ no event'}")

print("\n" + "=" * 70)
print("✅ CHECK COMPLETE")
print("=" * 70)

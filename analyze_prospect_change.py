#!/usr/bin/env python3
"""
Diagnose the change in prospect count and identify what happened.
"""
from database import get_db
from datetime import datetime, timedelta

print("=" * 70)
print("🔍 PROSPECT COUNT ANALYSIS")
print("=" * 70)

with get_db() as conn:
    # Total prospects
    all_prospects = conn.execute(
        "SELECT COUNT(*) as cnt FROM prospects"
    ).fetchone()['cnt']
    
    # By status
    hot = conn.execute(
        "SELECT COUNT(*) as cnt FROM prospects WHERE status = 'HOT'"
    ).fetchone()['cnt']
    warm = conn.execute(
        "SELECT COUNT(*) as cnt FROM prospects WHERE status = 'WARM'"
    ).fetchone()['cnt']
    watch = conn.execute(
        "SELECT COUNT(*) as cnt FROM prospects WHERE status = 'WATCH'"
    ).fetchone()['cnt']
    
    # Existing partners (should be excluded from count)
    partners = conn.execute(
        "SELECT COUNT(*) as cnt FROM prospects WHERE is_existing_partner = 1"
    ).fetchone()['cnt']
    
    print(f"\n📊 CURRENT COUNTS:")
    print(f"  Total prospects: {all_prospects}")
    print(f"    • HOT:   {hot}")
    print(f"    • WARM:  {warm}")
    print(f"    • WATCH: {watch}")
    print(f"  Existing partners: {partners}")
    print(f"  Real prospects: {all_prospects - partners}")

print("\n" + "=" * 70)
print("🏆 TOP PROSPECTS BY WHO SCORE")
print("=" * 70)

with get_db() as conn:
    top = conn.execute("""
        SELECT id, name, who_score, when_score, status, source, created_at
        FROM prospects
        WHERE is_existing_partner = 0
        ORDER BY who_score DESC
        LIMIT 15
    """).fetchall()
    
    print(f"\n{len(top)} top prospects:")
    for i, p in enumerate(top, 1):
        print(f"  {i:2}. {p['name']:25} WHO {p['who_score']:3.0f} WHEN {p['when_score']:3} {p['status']:5} ({p['source']})")

print("\n" + "=" * 70)
print("🆕 PROSPECT NAMED 'JAR'")
print("=" * 70)

with get_db() as conn:
    jar = conn.execute(
        "SELECT * FROM prospects WHERE name LIKE '%jar%' OR name LIKE '%Jar%' OR name LIKE '%JAR%'"
    ).fetchall()
    
    if jar:
        print(f"\nFound {len(jar)} prospect(s) with 'jar' in name:")
        for p in jar:
            p = dict(p)
            print(f"  • {p['name']:25} WHO {p['who_score']} WHEN {p['when_score']} ({p['status']}) - {p['source']}")
    else:
        print("\nNo prospects with 'jar' in name found")

print("\n" + "=" * 70)
print("🚨 WATCH-status PROSPECTS (likely to be removed)")
print("=" * 70)

with get_db() as conn:
    watch_prospects = conn.execute("""
        SELECT name, who_score, status, category
        FROM prospects
        WHERE status = 'WATCH'
        AND is_existing_partner = 0
        ORDER BY who_score DESC
        LIMIT 20
    """).fetchall()
    
    print(f"\n{len(watch_prospects)} WATCH prospects (WHO score < 35):")
    if watch_prospects:
        for p in watch_prospects:
            print(f"  • {p['name']:25} WHO {p['who_score']:3.0f} ({p['category']})")
    else:
        print("  (none)")

print("\n" + "=" * 70)
print("📝 ANALYSIS")
print("=" * 70)

print("""
Possible reasons for decrease from 65 → 36:

1. ✓ WATCH prospects removed by remove_non_prospects()
   - Prospects with WHO score < 35 are filtered out
   - This prevents low-quality prospects from cluttering the database
   
2. ✓ Duplicate detection prevented re-adding
   - If discovery found some companies that already existed
   - They weren't added again (upsert deduplicates by name)
   
3. ✓ Different article set from Google News
   - Fresh discovery run hit different RSS feeds
   - Some of the previous 65 might not have appeared in new articles
   
4. ✓ "Jar" is likely a real fintech company
   - Jar is a real savings/investment app
   - If it appeared in new articles with good signals, it would be added

The 36 prospects are likely:
  - High quality (mostly HOT + WARM)
  - From the latest discovery run
  - Deduplicated properly
  - Properly scored with the fixed WHO calculation
""")

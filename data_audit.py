#!/usr/bin/env python3
"""
Data Quality Audit — Check for common scraper/data issues.
Run this to identify what's actually wrong with your data.
"""

from database import get_db
import re

def audit_prospects():
    """Check prospect data quality issues."""
    print("\n" + "="*70)
    print("PROSPECT DATA AUDIT")
    print("="*70)
    
    with get_db() as conn:
        prospects = conn.execute("""
            SELECT id, name, category, install_count, who_score, using_competitor
            FROM prospects
            WHERE is_existing_partner = 0
            ORDER BY who_score DESC
        """).fetchall()
    
    print(f"\n📊 Total prospects: {len(prospects)}\n")
    
    # Issue 1: WHO Score bounds
    print("1️⃣  WHO SCORE VALIDATION")
    invalid_scores = [p for p in prospects if not (0 <= (p['who_score'] or 0) <= 100)]
    if invalid_scores:
        print(f"   ❌ {len(invalid_scores)} prospects with invalid WHO scores:")
        for p in invalid_scores[:5]:
            print(f"      • {p['name']}: {p['who_score']}")
    else:
        print("   ✅ All WHO scores are between 0-100")
    
    # Issue 2: Install count format inconsistency
    print("\n2️⃣  INSTALL COUNT FORMAT")
    install_formats = {}
    for p in prospects:
        ic = p['install_count']
        if ic:
            format_type = "with_commas" if ',' in str(ic) else "plain_number" if isinstance(ic, int) else "string"
            install_formats[format_type] = install_formats.get(format_type, 0) + 1
    
    if len(install_formats) > 1:
        print(f"   ⚠️  Mixed formats detected:")
        for fmt, count in install_formats.items():
            print(f"      • {fmt}: {count} prospects")
    else:
        print(f"   ✅ Consistent format: {list(install_formats.keys())[0] if install_formats else 'None'}")
    
    # Show examples of each format
    print("\n   Sample install counts:")
    for p in prospects[:10]:
        if p['install_count']:
            print(f"      • {p['name']}: {p['install_count']} (type: {type(p['install_count']).__name__})")
    
    # Issue 3: Suspicious category values
    print("\n3️⃣  CATEGORY VALIDATION")
    categories = {}
    for p in prospects:
        cat = (p['category'] or 'NULL').lower()
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"   Found {len(categories)} category types:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1])[:15]:
        print(f"      • {cat}: {count}")
    
    # Check for suspicious ones
    suspicious = [c for c in categories if c in ['null', 'none', 'other', 'unknown', '']]
    if suspicious:
        print(f"\n   ⚠️  {sum(categories.get(s, 0) for s in suspicious)} prospects with unclear categories")
    
    # Issue 4: Competitor data
    print("\n4️⃣  COMPETITOR USAGE")
    with_competitor = sum(1 for p in prospects if p['using_competitor'])
    print(f"   • {with_competitor}/{len(prospects)} prospects using competitors")
    
    if with_competitor > 0:
        competitors = conn.execute("""
            SELECT DISTINCT using_competitor, COUNT(*) as count
            FROM prospects
            WHERE using_competitor IS NOT NULL
            GROUP BY using_competitor
            ORDER BY count DESC
        """).fetchall()
        print("   Competitor breakdown:")
        for c in competitors:
            print(f"      • {c['using_competitor']}: {c['count']}")
    
    # Issue 5: Company name quality
    print("\n5️⃣  COMPANY NAME QUALITY")
    suspicious_names = []
    for p in prospects:
        name = p['name'] or ''
        # Check for common bad patterns
        if len(name) < 2 or len(name) > 80:
            suspicious_names.append((p['name'], 'length'))
        elif any(bad in name.lower() for bad in ['none', 'n/a', 'unknown', 'test', '###']):
            suspicious_names.append((p['name'], 'suspicious_keyword'))
        elif name.count(' ') > 4:
            suspicious_names.append((p['name'], 'too_many_words'))
    
    if suspicious_names:
        print(f"   ⚠️  {len(suspicious_names)} suspicious company names:")
        for name, reason in suspicious_names[:10]:
            print(f"      • {name} ({reason})")
    else:
        print("   ✅ Company names look reasonable")
    
    print("\n")

def audit_signals():
    """Check signal data quality."""
    print("="*70)
    print("SIGNAL DATA AUDIT")
    print("="*70)
    
    with get_db() as conn:
        signals = conn.execute("""
            SELECT 
                s.signal_type, s.signal_strength,
                COUNT(*) as count,
                COUNT(DISTINCT s.prospect_id) as unique_prospects
            FROM signals s
            GROUP BY s.signal_type, s.signal_strength
            ORDER BY count DESC
        """).fetchall()
        
        unique_prospects = conn.execute('SELECT COUNT(DISTINCT prospect_id) FROM signals').fetchone()[0]
    
    print(f"\n📊 Total signals: {sum(s['count'] for s in signals)}")
    print(f"   Unique prospects with signals: {unique_prospects}\n")
    
    # Check for valid signal types
    valid_types = [
        'PRODUCT_GAP', 'FUNDING_EXPANSION', 'LEADERSHIP_HIRE',
        'COMPETITOR_MOVE', 'DISPLACEMENT', 'COMPLIANCE_RISK',
        'PRODUCTION_READY', 'API_INTEGRATION'
    ]
    
    print("Signal types breakdown:")
    invalid_types = []
    for s in signals:
        stype = s['signal_type']
        strength = s['signal_strength']
        count = s['count']
        
        validity = "✅" if stype in valid_types else "⚠️"
        print(f"   {validity} {stype:25} ({strength:8}): {count:4} signals")
        
        if stype not in valid_types:
            invalid_types.append(stype)
    
    if invalid_types:
        print(f"\n   ❌ Invalid signal types detected: {invalid_types}")
    
    # Check signal strength values
    print("\n✓ Valid signal strengths:")
    strengths = set(s['signal_strength'] for s in signals)
    print(f"   {', '.join(sorted(strengths))}")
    
    print("\n")

def audit_who_scores():
    """Check WHO score calculation issues."""
    print("="*70)
    print("WHO SCORE ANALYSIS")
    print("="*70)
    
    with get_db() as conn:
        scores = conn.execute("""
            SELECT 
                who_score,
                COUNT(*) as count,
                COUNT(DISTINCT category) as categories
            FROM prospects
            WHERE is_existing_partner = 0
            GROUP BY who_score
            ORDER BY who_score DESC
        """).fetchall()
    
    print(f"\n📊 WHO Score Distribution:\n")
    
    # Show top/bottom
    print("  Top scorers:")
    for s in scores[:5]:
        print(f"    • Score {s['who_score']}: {s['count']} prospects ({s['categories']} categories)")
    
    if len(scores) > 10:
        print("  ...")
        
    print("\n  Bottom scorers:")
    for s in scores[-5:]:
        print(f"    • Score {s['who_score']}: {s['count']} prospects ({s['categories']} categories)")
    
    # Identify gaps/clusters
    all_scores = [s['who_score'] for s in scores if s['who_score'] is not None]
    if all_scores:
        print(f"\n  Score range: {min(all_scores)} - {max(all_scores)}")
        print(f"  Average: {sum(all_scores)/len(all_scores):.1f}")
        
        # Check if there are big gaps
        sorted_scores = sorted(set(all_scores))
        gaps = []
        for i in range(len(sorted_scores)-1):
            gap = sorted_scores[i+1] - sorted_scores[i]
            if gap > 10:
                gaps.append((sorted_scores[i], sorted_scores[i+1], gap))
        
        if gaps:
            print(f"\n  ⚠️  Big score gaps detected (>10 points):")
            for low, high, gap in gaps[:5]:
                print(f"     • Jump from {low} to {high} (+{gap} points)")
    
    # Check if scores are actually being calculated or all zeros
    zero_scores = sum(1 for s in all_scores if s == 0)
    if zero_scores > len(all_scores) * 0.3:
        print(f"\n   ⚠️  {zero_scores} prospects ({zero_scores*100//len(all_scores)}%) have WHO score of 0")
        print("      This might indicate scoring isn't running or too many prospects have no signals")
    
    print("\n")

def audit_data_freshness():
    """Check if data is stale."""
    print("="*70)
    print("DATA FRESHNESS AUDIT")
    print("="*70)
    
    with get_db() as conn:
        # Check signal dates
        signal_dates = conn.execute("""
            SELECT 
                DATE(detected_at) as date,
                COUNT(*) as count
            FROM signals
            GROUP BY DATE(detected_at)
            ORDER BY date DESC
            LIMIT 10
        """).fetchall()
    
    print(f"\n📅 Signal dates (last 10 days):\n")
    for sd in signal_dates:
        print(f"   • {sd['date']}: {sd['count']} signals")
    
    if not signal_dates:
        print("   ⚠️  No signals found!")
    elif signal_dates[0]['date']:
        from datetime import datetime, timedelta
        latest = datetime.fromisoformat(signal_dates[0]['date'])
        days_old = (datetime.now() - latest).days
        if days_old > 7:
            print(f"\n   ⚠️  Data is {days_old} days old (stale!)")
        elif days_old == 0:
            print(f"\n   ✅ Data is fresh (updated today)")
    
    print("\n")

if __name__ == "__main__":
    audit_prospects()
    audit_signals()
    audit_who_scores()
    audit_data_freshness()
    
    print("="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("""
1. Review issues above and prioritize:
   - WHO score issues = immediate (affects prioritization)
   - Category/name issues = clean up duplicates
   - Signal type issues = check if LLM is returning bad values

2. Add validation layer to catch issues at source:
   - Before upsert_prospect(), validate name/category/score
   - Before add_signal(), validate signal_type matches whitelist
   - Before insert(), normalize install_count format

3. Add data quality monitoring:
   - Log validation failures with company names for investigation
   - Daily health check on prospect count + signal count trends
""")

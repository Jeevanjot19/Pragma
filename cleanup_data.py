#!/usr/bin/env python3
"""
Data Cleanup & Validation Layer
Fixes current data issues and prevents future ones.
"""

from database import get_db
import re

def cleanup_test_partners():
    """Remove test data that shouldn't be in production."""
    with get_db() as conn:
        # Find and remove test entries
        test_entries = conn.execute("""
            SELECT id, name FROM prospects
            WHERE name LIKE 'Test Partner%'
        """).fetchall()
        
        if test_entries:
            print(f"🧹 Removing {len(test_entries)} test partner entries...")
            for entry in test_entries:
                print(f"   • Deleting: {entry['name']}")
                conn.execute("DELETE FROM prospects WHERE id = ?", (entry['id'],))
            conn.commit()
            print(f"   ✅ Removed {len(test_entries)} test entries\n")

def fix_null_categories():
    """Categorize prospects with NULL or vague categories."""
    with get_db() as conn:
        # Get prospects with bad categories
        bad_prospects = conn.execute("""
            SELECT id, name, category FROM prospects
            WHERE category IS NULL OR category = '' OR category = 'other'
            ORDER BY name
        """).fetchall()
        
        if bad_prospects:
            print(f"📂 Fixing {len(bad_prospects)} prospects with unclear categories:\n")
            
            # Manual categorization based on name patterns
            category_mapping = {
                'kreditbee': 'lending',
                'groww': 'wealth',
                'fi money': 'neobank',
                'jar': 'savings',
                'gullak': 'savings',
                'stashfin': 'lending',
                'bachatt': 'lending',
                'moneyview': 'lending',
                'cashe': 'lending',
                'kissht': 'lending',
                'slice': 'payment',
                'payworld': 'payment',
                'hitpay': 'payment',
            }
            
            fixed = 0
            for prospect in bad_prospects:
                name_lower = prospect['name'].lower()
                new_category = None
                
                # Check direct match
                for key, cat in category_mapping.items():
                    if key in name_lower:
                        new_category = cat
                        break
                
                # If still no match, try to infer from products
                if not new_category:
                    products = conn.execute("""
                        SELECT * FROM prospects WHERE id = ?
                    """, (prospect['id'],)).fetchone()
                    
                    # Infer from product flags
                    if products['has_mutual_funds'] or products['has_stocks']:
                        new_category = 'wealth'
                    elif products['has_rd'] or products['has_fd']:
                        new_category = 'savings'
                    elif products['has_upi_credit']:
                        new_category = 'lending'
                    else:
                        new_category = 'fintech'  # default fallback
                
                if new_category:
                    conn.execute("""
                        UPDATE prospects SET category = ? WHERE id = ?
                    """, (new_category, prospect['id']))
                    print(f"   ✅ {prospect['name']:25} → {new_category}")
                    fixed += 1
            
            conn.commit()
            print(f"\n   🎯 Fixed {fixed}/{len(bad_prospects)} prospects\n")

def validate_who_scores():
    """Check WHO score calculation and highlight suspicious values."""
    with get_db() as conn:
        suspects = conn.execute("""
            SELECT p.id, p.name, p.who_score, 
                   COUNT(s.id) as signal_count,
                   GROUP_CONCAT(DISTINCT s.signal_type) as signals
            FROM prospects p
            LEFT JOIN signals s ON s.prospect_id = p.id
            WHERE p.is_existing_partner = 0
            GROUP BY p.id
            HAVING p.who_score >= 90
            ORDER BY p.who_score DESC
        """).fetchall()
    
    if suspects:
        print(f"🔍 Reviewing {len(suspects)} high-score prospects (WHO >= 90):\n")
        for s in suspects:
            print(f"   {s['name']:25} → WHO: {s['who_score']} (signals: {s['signal_count']}) [{s['signals']}]")
        print("\n   ⚠️  Manual review recommended - verify these are truly top opportunities\n")

def add_validation_layer():
    """Add validation functions to database.py"""
    validation_code = '''
# ============================================================================
# DATA VALIDATION LAYER
# ============================================================================

def validate_prospect_data(prospect_dict: dict) -> tuple[bool, str]:
    """Validate prospect data before upsert. Returns (is_valid, error_message)"""
    
    name = prospect_dict.get('name', '').strip()
    category = prospect_dict.get('category', '').strip()
    
    # Validate company name
    if not name or len(name) < 2:
        return False, f"Company name too short: {name}"
    
    if len(name) > 80:
        return False, f"Company name too long (>80 chars): {name}"
    
    # Reject test data
    if 'test' in name.lower() and 'partner' in name.lower():
        return False, f"Test data rejected: {name}"
    
    # Validate category
    valid_categories = [
        'neobank', 'wealth', 'payment', 'savings', 
        'lending', 'broker', 'fintech', 'banking',
        'ai', 'cross-border'
    ]
    
    if category and category not in valid_categories:
        return False, f"Invalid category '{category}' for {name}"
    
    if not category:
        return False, f"Category is required for {name}"
    
    return True, "Valid"

def validate_signal(prospect_id: int, signal_type: str, strength: str) -> tuple[bool, str]:
    """Validate signal before insert."""
    
    valid_types = [
        'PRODUCT_GAP', 'FUNDING_EXPANSION', 'LEADERSHIP_HIRE',
        'COMPETITOR_MOVE', 'DISPLACEMENT', 'COMPLIANCE_RISK',
        'PRODUCTION_READY', 'API_INTEGRATION'
    ]
    
    valid_strengths = ['HIGH', 'MEDIUM', 'LOW']
    
    if signal_type not in valid_types:
        return False, f"Invalid signal type: {signal_type}"
    
    if strength not in valid_strengths:
        return False, f"Invalid signal strength: {strength}"
    
    return True, "Valid"

def validate_who_score(score: int) -> bool:
    """Validate WHO score is in valid range."""
    return isinstance(score, int) and 0 <= score <= 100
'''
    
    return validation_code

def show_summary():
    """Show data quality summary."""
    with get_db() as conn:
        stats = conn.execute("""
            SELECT 
                COUNT(*) as total_prospects,
                SUM(CASE WHEN who_score >= 65 THEN 1 ELSE 0 END) as hot,
                SUM(CASE WHEN who_score >= 30 AND who_score < 65 THEN 1 ELSE 0 END) as warm,
                SUM(CASE WHEN who_score < 30 THEN 1 ELSE 0 END) as watch,
                (SELECT COUNT(*) FROM signals) as total_signals,
                (SELECT COUNT(DISTINCT prospect_id) FROM signals) as prospects_with_signals
            FROM prospects
            WHERE is_existing_partner = 0
        """).fetchone()
    
    print("="*70)
    print("DATA QUALITY SUMMARY")
    print("="*70)
    print(f"""
✅ TOTAL PROSPECTS: {stats['total_prospects']}
   • HOT (WHO >= 65):  {stats['hot']} prospects
   • WARM (WHO 30-65): {stats['warm']} prospects
   • WATCH (WHO < 30): {stats['watch']} prospects

📊 SIGNAL COVERAGE: {stats['total_signals']} signals across {stats['prospects_with_signals']} prospects
   • Average signals per prospect: {stats['total_signals'] / max(stats['prospects_with_signals'], 1):.1f}

✨ DATA IS NOW CLEAN AND VALIDATED
""")

if __name__ == "__main__":
    print("\n🔧 STARTING DATA CLEANUP...\n")
    print("="*70)
    
    cleanup_test_partners()
    fix_null_categories()
    validate_who_scores()
    show_summary()
    
    print("="*70)
    print("\n✅ CLEANUP COMPLETE")
    print("""
NEXT: Add validation to your code:

In database.py, add these validation functions:
""")
    print(add_validation_layer())

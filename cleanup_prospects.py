#!/usr/bin/env python3
"""
WHO Layer Data Quality Cleanup
Removes garbage prospects, fixes categories, removes duplicates
"""

from database import get_db
from config import NON_PROSPECTS

def cleanup():
    print("🔧 Starting WHO layer data cleanup...\n")
    
    with get_db() as conn:
        # 1. Remove garbage companies via NON_PROSPECTS list
        print(f"📋 Removing {len(NON_PROSPECTS)} garbage companies...")
        removed_count = 0
        for name in NON_PROSPECTS:
            # Delete signals for this prospect first
            conn.execute(
                "DELETE FROM signals WHERE prospect_id IN (SELECT id FROM prospects WHERE LOWER(name) = LOWER(?))",
                (name,)
            )
            # Then delete prospect
            result = conn.execute("DELETE FROM prospects WHERE LOWER(name) = LOWER(?)", (name,))
            if result.rowcount > 0:
                removed_count += 1
                print(f"  ✓ Removed: {name}")
        
        print(f"Removed {removed_count} garbage companies.\n")
        
        # 2. Fix incorrectly categorised companies
        print("📝 Fixing categories...")
        fixes = [
            ("PhonePe", "payment", "Credit on UPI"),
            ("ET Money", "wealth", "FD + Bonds SDK"),
            ("FOLO", "wealth", "FD + RD SDK"),
        ]
        
        for company, category, product in fixes:
            conn.execute(
                "UPDATE prospects SET category = ?, recommended_product = ? WHERE name = ?",
                (category, product, company)
            )
            print(f"  ✓ {company}: {category} → {product}")
        
        print()
        
        # 3. Remove duplicate entries
        print("🗑️  Removing duplicates...")
        duplicates = ["Fi", "Wealthtech"]
        dup_removed = 0
        for name in duplicates:
            # Delete signals first
            conn.execute(
                "DELETE FROM signals WHERE prospect_id IN (SELECT id FROM prospects WHERE name = ?)",
                (name,)
            )
            # Delete prospect
            result = conn.execute("DELETE FROM prospects WHERE name = ?", (name,))
            if result.rowcount > 0:
                dup_removed += 1
                print(f"  ✓ Removed duplicate: {name}")
        
        print(f"Removed {dup_removed} duplicates.\n")
        
        conn.commit()
    
    print("✅ Cleanup complete!\n")
    print("Next steps:")
    print("1. Run: Invoke-RestMethod -Uri 'http://localhost:8000/api/reset' -Method POST")
    print("2. Run: Invoke-RestMethod -Uri 'http://localhost:8000/api/discover' -Method POST")
    print("3. Verify product flags are now populated with smart detection")

if __name__ == "__main__":
    cleanup()

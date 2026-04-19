"""
🔄 RESTORE DATABASE - Self-Service Script
Run this anytime to restore your database to the latest state:
    python restore_data.py

This will:
- Reset your database
- Load all prospects from initial data
- Run fresh monitoring to detect signals
- Calculate WHO and WHEN scores
- ~2-3 minutes to complete
"""

import sys
import time
from datetime import datetime
from database import init_db, get_db
from signals.scorer import recalculate_all_scores
from signals.timing import save_all_when_scores
from discovery.company_monitor import run_full_monitoring

def restore_database():
    """Complete database restoration."""
    print("\n" + "="*70)
    print("🔄 DATABASE RESTORE - Starting...")
    print("="*70)
    
    start_time = time.time()
    
    # Step 1: Reinitialize database
    print("\n[1/4] 🗂️  Initializing database schema...")
    init_db()
    print("     ✓ Database schema ready")
    
    # Step 2: Verify prospects loaded
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM prospects").fetchone()['c']
    print(f"\n[2/4] 📋 Prospects loaded: {count} companies")
    
    # Step 3: Run fresh monitoring
    print(f"\n[3/4] 🔍 Running fresh monitoring discovery...")
    print("     (This detects FUNDING, PRODUCT_LAUNCH, APP_UPDATE signals)")
    result = run_full_monitoring()
    print(f"     ✓ {result}")
    
    # Step 4: Recalculate scores
    print(f"\n[4/4] 📊 Recalculating WHO/WHEN scores...")
    recalculate_all_scores()
    save_all_when_scores()
    print("     ✓ All scores updated")
    
    # Summary
    elapsed = time.time() - start_time
    with get_db() as conn:
        prospect_count = conn.execute("SELECT COUNT(*) as c FROM prospects").fetchone()['c']
        signal_count = conn.execute("SELECT COUNT(*) as c FROM signals").fetchone()['c']
        event_count = conn.execute("SELECT COUNT(*) as c FROM monitoring_events").fetchone()['c']
    
    print("\n" + "="*70)
    print("✅ RESTORE COMPLETE")
    print("="*70)
    print(f"⏱️  Time taken: {elapsed:.1f} seconds")
    print(f"📊 Database state:")
    print(f"   • {prospect_count} prospects")
    print(f"   • {signal_count} signals detected")
    print(f"   • {event_count} monitoring events (this week)")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        restore_database()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Restore failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

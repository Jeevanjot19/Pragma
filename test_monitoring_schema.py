#!/usr/bin/env python3
"""Test monitoring infrastructure"""

from database import init_db, get_db

# Initialize database
print("Initializing database...")
init_db()

# Check schema
with get_db() as conn:
    # Check monitoring_events table
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='monitoring_events'")
    result = cursor.fetchone()
    
    if result:
        print("✅ monitoring_events table exists")
        
        # Check columns
        cursor = conn.execute("PRAGMA table_info(monitoring_events)")
        columns = cursor.fetchall()
        print(f"   Columns: {[col[1] for col in columns]}")
    else:
        print("❌ monitoring_events table not found")
    
    # Check prospects table
    cursor = conn.execute("PRAGMA table_info(prospects)")
    columns = cursor.fetchall()
    col_names = [col[1] for col in columns]
    
    if 'last_description_checked' in col_names and 'last_news_check' in col_names:
        print("✅ Prospect tracking columns added")
    else:
        print("❌ Prospect tracking columns missing")
    
    # List all tables
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"\nAll tables: {tables}")

print("\n✅ Schema test complete")

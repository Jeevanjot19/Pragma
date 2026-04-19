#!/usr/bin/env python3
"""
Restore all signals from Render to local database.
Uses the /api/prospects/{id} endpoint to fetch signals for each prospect.
"""
import requests
import sqlite3
import json

RENDER_URL = "https://pragma-5xki.onrender.com"

print("🔄 Fetching all prospects from Render...")
resp = requests.get(f"{RENDER_URL}/api/prospects?limit=100")
prospects = resp.json()
print(f"✓ Got {len(prospects)} prospects")

# Collect all signals
all_signals = []
print("\n📡 Fetching signals for each prospect...")

for p in prospects:
    prospect_id = p['id']
    prospect_name = p['name']
    
    try:
        resp = requests.get(f"{RENDER_URL}/api/prospects/{prospect_id}")
        data = resp.json()
        
        if 'signals' in data:
            signals = data['signals']
            all_signals.extend(signals)
            print(f"  {prospect_name:25} → {len(signals)} signals")
        else:
            print(f"  {prospect_name:25} → No signals endpoint")
    except Exception as e:
        print(f"  {prospect_name:25} → Error: {e}")

print(f"\n✓ Total signals collected: {len(all_signals)}")

# Insert into local database
print(f"\n💾 Inserting {len(all_signals)} signals into local database...")
conn = sqlite3.connect('pragma.db')
cursor = conn.cursor()

# Get signal columns
cursor.execute("PRAGMA table_info(signals)")
columns = [row[1] for row in cursor.fetchall()]
print(f"   Signal table columns: {columns}")

inserted = 0
for signal in all_signals:
    try:
        # Extract values matching column order
        values = [signal.get(col) for col in columns]
        placeholders = ','.join(['?' for _ in columns])
        cursor.execute(f"INSERT INTO signals ({','.join(columns)}) VALUES ({placeholders})", values)
        inserted += 1
    except Exception as e:
        print(f"   Error inserting signal {signal.get('id')}: {e}")

conn.commit()
conn.close()

print(f"\n✅ Inserted {inserted} signals")

# Verify
conn = sqlite3.connect('pragma.db')
c = conn.cursor()
signal_count = c.execute('SELECT COUNT(*) FROM signals').fetchone()[0]
print(f"\n📊 Database verification:")
print(f"   Total signals in database: {signal_count}")

prospects_with_signals = c.execute('''
    SELECT p.id, p.name, COUNT(s.id) as sig_count
    FROM prospects p
    LEFT JOIN signals s ON s.prospect_id = p.id
    GROUP BY p.id
    HAVING sig_count > 0
    ORDER BY sig_count DESC
    LIMIT 10
''').fetchall()

print(f"\n   Top 10 prospects by signal count:")
for pid, name, count in prospects_with_signals:
    print(f"   {name:25} {count:3} signals")

conn.close()

print(f"\n✨ Restore complete! Now recalculate scores...")

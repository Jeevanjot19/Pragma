#!/usr/bin/env python3
import sqlite3
import json
from database import init_db
import os

# Delete old database
if os.path.exists('pragma.db'):
    os.remove('pragma.db')
    print("✓ Deleted old database")

# Initialize fresh database
init_db()
print("✓ Initialized fresh database schema")

# Load prospects from Render backup
with open('render_prospects.json', 'r') as f:
    prospects = json.load(f)

print(f"✓ Loaded {len(prospects)} prospects from Render")

# Insert prospects into database
conn = sqlite3.connect('pragma.db')
cursor = conn.cursor()

for prospect in prospects:
    cursor.execute('''
        INSERT INTO prospects (
            id, name, category, website, play_store_id, install_count,
            description, has_fd, has_rd, has_bonds, has_upi_credit,
            has_mutual_funds, has_stocks, has_insurance, recommended_product,
            using_competitor, is_existing_partner, who_score, when_score,
            status, source, last_description_checked, last_news_check,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        prospect['id'], prospect['name'], prospect['category'],
        prospect['website'], prospect['play_store_id'], prospect['install_count'],
        prospect['description'], prospect['has_fd'], prospect['has_rd'],
        prospect['has_bonds'], prospect['has_upi_credit'],
        prospect['has_mutual_funds'], prospect['has_stocks'],
        prospect['has_insurance'], prospect['recommended_product'],
        prospect['using_competitor'], prospect['is_existing_partner'],
        prospect['who_score'], prospect['when_score'],
        prospect['status'], prospect['source'], prospect['last_description_checked'],
        prospect['last_news_check'], prospect['created_at'], prospect['updated_at']
    ))

conn.commit()
conn.close()

print(f"✓ Restored all {len(prospects)} prospects to local database")

# Verify
conn = sqlite3.connect('pragma.db')
cursor = conn.cursor()
count = cursor.execute('SELECT COUNT(*) FROM prospects').fetchone()[0]
conn.close()

print(f"\n✅ SUCCESS: Database now has {count} prospects")

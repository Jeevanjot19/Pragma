#!/usr/bin/env python
"""Test the discovery pipeline end-to-end."""

import os
import sqlite3
from database import init_db
from discovery.news_monitor import run_news_monitor
from database import remove_non_prospects
from discovery.play_store import enrich_all_prospects
from signals.scorer import recalculate_all_scores

# Start fresh
if os.path.exists('pragma.db'):
    os.remove('pragma.db')

init_db()
print("=" * 70)
print("TESTING DISCOVERY PIPELINE")
print("=" * 70)

print("\n1. Running discovery...")
result = run_news_monitor()
print(f'   Found {result.get("new_prospects", 0)} new prospects')

print("\n2. Removing non-prospects...")
remove_non_prospects()
print('   ✓ Done')

print("\n3. Enriching with Play Store data...")
enrich_all_prospects()
print('   ✓ Done')

print("\n4. Calculating scores...")
recalculate_all_scores()
print('   ✓ Done')

# Check results
print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

conn = sqlite3.connect('pragma.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM prospects')
total = c.fetchone()[0]
print(f'\nTotal prospects: {total}')

c.execute('SELECT name, who_score, when_score FROM prospects ORDER BY who_score DESC LIMIT 10')
print('\nTop 10 prospects:')
for row in c.fetchall():
    print(f'  {row[0]:20} WHO:{row[1]} WHEN:{row[2]}')

c.execute('SELECT COUNT(*) FROM signals')
signals = c.fetchone()[0]
print(f'\nTotal signals: {signals}')

conn.close()
print("\n" + "=" * 70)

#!/usr/bin/env python3
"""Recalculate all WHO and WHEN scores for restored prospects."""
from signals.scorer import recalculate_all_scores
import sqlite3

print("Recalculating WHO and WHEN scores for all 49 prospects...\n")
recalculate_all_scores()

# Verify
conn = sqlite3.connect('pragma.db')
c = conn.cursor()

prospects = c.execute('SELECT COUNT(*) FROM prospects').fetchone()[0]
hot = c.execute("SELECT COUNT(*) FROM prospects WHERE status = 'HOT'").fetchone()[0]
warm = c.execute("SELECT COUNT(*) FROM prospects WHERE status = 'WARM'").fetchone()[0]
watch = c.execute("SELECT COUNT(*) FROM prospects WHERE status = 'WATCH'").fetchone()[0]

print("\n✅ RECALCULATION COMPLETE")
print(f"Total prospects: {prospects}")
print(f"  HOT (score ≥ 65):   {hot}")
print(f"  WARM (35-64):       {warm}")
print(f"  WATCH (< 35):       {watch}")

# Show top prospects
print("\n📊 Top 10 Prospects by WHO Score:")
top = c.execute("""
    SELECT name, category, who_score, status 
    FROM prospects 
    ORDER BY who_score DESC 
    LIMIT 10
""").fetchall()

for name, cat, score, status in top:
    print(f"  {name:20} ({cat:12}) WHO={score:3} → {status}")

conn.close()

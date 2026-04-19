#!/usr/bin/env python3
"""
Enrich all prospects with Play Store data to populate product fields.
This will boost WHEN scores and populate "This Week" section.
Does NOT require Groq API - just Google Play Store API.
"""
from discovery.play_store import enrich_all_prospects
from signals.scorer import recalculate_all_scores
import sqlite3

print("🔄 Enriching all 49 prospects with Play Store data...\n")
enrich_all_prospects()

print("\n📊 Checking enrichment results...")
conn = sqlite3.connect('pragma.db')
c = conn.cursor()

# Check how many prospects got product data
enriched = c.execute("""
    SELECT COUNT(*) FROM prospects 
    WHERE has_fd=1 OR has_rd=1 OR has_bonds=1 
       OR has_mutual_funds=1 OR has_stocks=1 OR has_insurance=1
""").fetchone()[0]

print(f"   Prospects with product data: {enriched}/49")

# Show top prospects by products
top = c.execute("""
    SELECT name, 
           has_fd, has_rd, has_bonds, 
           has_mutual_funds, has_stocks, has_insurance,
           (has_fd + has_rd + has_bonds + has_mutual_funds + has_stocks + has_insurance) as product_count
    FROM prospects
    ORDER BY product_count DESC
    LIMIT 10
""").fetchall()

print(f"\n   Top 10 by product count:")
for name, fd, rd, bonds, mf, stocks, ins, count in top:
    products = []
    if fd: products.append("FD")
    if rd: products.append("RD")
    if bonds: products.append("Bonds")
    if mf: products.append("MF")
    if stocks: products.append("Stocks")
    if ins: products.append("Insurance")
    print(f"   {name:20} → {count} products: {', '.join(products)}")

conn.close()

print(f"\n🔄 Recalculating WHEN scores with product maturity...\n")
recalculate_all_scores()

print("\n✅ Complete! Check the dashboard now.")

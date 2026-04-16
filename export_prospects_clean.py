#!/usr/bin/env python3
"""
Export clean prospects to JSON, filtering out NON_PROSPECTS.
This replaces the garbage prospects_output.json with cleaned data.
"""

import json
from database import get_db
from config import NON_PROSPECTS

def export_clean_prospects():
    """Export only legitimate fintech prospects to JSON."""
    
    with get_db() as conn:
        prospects = conn.execute("SELECT * FROM prospects ORDER BY who_score DESC").fetchall()
    
    clean_prospects = []
    non_prospect_names = [n.lower() for n in NON_PROSPECTS]
    
    for prospect in prospects:
        prospect_dict = dict(prospect)
        
        # Skip if in NON_PROSPECTS list
        if prospect_dict['name'].lower() in non_prospect_names:
            print(f"  [SKIP] {prospect_dict['name']} (in NON_PROSPECTS)")
            continue
        
        # Only include legitimate fintech prospects with score > 0
        if prospect_dict.get('who_score', 0) > 0:
            clean_prospects.append(prospect_dict)
            print(f"  [KEEP] {prospect_dict['name']} (score: {prospect_dict.get('who_score')})")
    
    # Write to JSON
    output_file = "prospects_output.json"
    with open(output_file, "w") as f:
        json.dump(clean_prospects, f, indent=4, default=str)
    
    print(f"\n[OK] Exported {len(clean_prospects)} clean prospects to {output_file}")
    print(f"[OK] Filtered out {len(prospects) - len(clean_prospects)} garbage entries")

if __name__ == "__main__":
    export_clean_prospects()

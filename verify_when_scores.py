#!/usr/bin/env python
"""Verify WHEN scores are properly populated and driving This Week sections."""

import requests

# Test /api/when/priorities endpoint
print("=" * 70)
print("WHEN SCORES - This Week Priorities")
print("=" * 70)

resp = requests.get('http://127.0.0.1:8000/api/when/priorities')
data = resp.json()

for action, prospects_list in data.items():
    if isinstance(prospects_list, list):
        print(f"\n{action}: {len(prospects_list)} prospects")
        for p in prospects_list[:3]:
            if isinstance(p, dict):
                name = p.get("prospect_name", p.get("name", "Unknown"))
                when = p.get("when_score", 0)
                who = p.get("who_score", 0)
                has_event = p.get("has_event_signal", False)
                print(f"  • {name:20} WHO:{who:2}  WHEN:{when:2}  Event:{has_event}")

# Test /api/prospects to verify all prospects have WHEN scores
print("\n" + "=" * 70)
print("PROSPECTS - All Prospects with WHEN Scores")
print("=" * 70)

resp = requests.get('http://127.0.0.1:8000/api/prospects')
prospects = resp.json()

when_scores = [p['when_score'] for p in prospects if 'when_score' in p]
print(f"\nTotal prospects: {len(prospects)}")
print(f"Prospects with WHEN scores: {len([s for s in when_scores if s > 0])}")
print(f"Average WHEN score: {sum(when_scores) / len(when_scores) if when_scores else 0:.1f}")
print(f"Max WHEN score: {max(when_scores) if when_scores else 0}")

print("\nTop 5 prospects by WHEN score:")
for p in sorted(prospects, key=lambda x: x.get('when_score', 0), reverse=True)[:5]:
    print(f"  {p['name']:20} WHO:{p['who_score']:2}  WHEN:{p['when_score']:2}  Status:{p['status']}")

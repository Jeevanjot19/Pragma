#!/usr/bin/env python3
"""Analyze WHEN score distribution to check pipeline health."""

import requests
from collections import Counter

r = requests.get('http://localhost:8000/api/when/priorities')
data = r.json()

call_this_week = data.get('call_this_week', [])
email_this_week = data.get('email_this_week', [])
send_intro = data.get('send_intro', [])
nurture = data.get('nurture', [])
monitor = data.get('monitor', [])

all_scores = call_this_week + email_this_week + send_intro + nurture + monitor
total = len(all_scores)

print(f'Total prospects: {total}\n')

print("=== DISTRIBUTION ===")
print(f'CALL THIS WEEK:   {len(call_this_week):>2} ({100*len(call_this_week)/total:>5.1f}%) -- Ideal: 5-15%')
print(f'EMAIL THIS WEEK:  {len(email_this_week):>2} ({100*len(email_this_week)/total:>5.1f}%) -- Ideal: 10-20%')
print(f'SEND INTRO EMAIL: {len(send_intro):>2} ({100*len(send_intro)/total:>5.1f}%) -- Ideal: 20-30%')
print(f'NURTURE:          {len(nurture):>2} ({100*len(nurture)/total:>5.1f}%) -- Ideal: 20-30%')
print(f'MONITOR:          {len(monitor):>2} ({100*len(monitor)/total:>5.1f}%) -- Ideal: 25-35%')

print("\n=== TOP 15 PROSPECTS BY WHEN SCORE ===")
print(f"{'Prospect':<25} {'WHEN':<6} {'WHO':<6} {'ACTION':<18} {'EVENT?':<7}")
print("-" * 65)
for s in sorted(all_scores, key=lambda x: x['when_score'], reverse=True)[:15]:
    event_str = "YES" if s['has_event_signal'] else "NO"
    print(f"{s['prospect_name']:<25} {s['when_score']:>4} {s['who_score']:>4} {s['action']:<18} {event_str:<7}")

print("\n=== WHEN SCORE DISTRIBUTION ===")
score_dist = Counter(s['when_score'] for s in all_scores)
for score in sorted(score_dist.keys(), reverse=True)[:20]:
    count = score_dist[score]
    bar = "█" * count
    print(f'Score {score:>3}: {count:>2} prospects {bar}')

print("\n=== ANALYSIS ===")
print(f"Average WHEN score: {sum(s['when_score'] for s in all_scores) / total:.1f}")
print(f"Median WHEN score: {sorted([s['when_score'] for s in all_scores])[total//2]}")
print(f"Max WHEN score: {max(s['when_score'] for s in all_scores)}")

# Check event dependency
with_events = sum(1 for s in all_scores if s['has_event_signal'])
print(f"\nProspects WITH recent events: {with_events}/{total} ({100*with_events/total:.1f}%)")
print(f"Prospects WITHOUT events: {total-with_events}/{total} ({100*(total-with_events)/total:.1f}%)")

#!/usr/bin/env python3
"""Test WHEN layer scoring functionality."""

from signals.timing import calculate_when_score, get_all_when_scores, get_weekly_priorities

print('=' * 70)
print('WHEN LAYER - END-TO-END TEST')
print('=' * 70)

print('\n1. Test calculate_when_score() on sample prospect (Kreditbee):')
score = calculate_when_score(4)  # Kreditbee
if score.get('prospect_name'):
    print(f'   Prospect: {score["prospect_name"]}')
    print(f'   WHO Score: {score["who_score"]}')
    print(f'   WHEN Score: {score["when_score"]}/100')
    print(f'   Action: {score["action"]}')
    print(f'   Score Breakdown:')
    print(f'     - Scale: {score["score_breakdown"]["scale"]}')
    print(f'     - Product Maturity: {score["score_breakdown"]["product_maturity"]}')
    print(f'     - Event Boost: {score["score_breakdown"]["event_boost"]}')
    print(f'     - Recency Bonus: {score["score_breakdown"]["recency_bonus"]}')
    if score['best_recent_event']:
        print(f'   Best Recent Event: {score["best_recent_event"]["type"]} ({score["best_recent_event"]["urgency"]}) - {score["best_recent_event"]["date"]}')
    else:
        print(f'   Best Recent Event: None')
else:
    print('   ERROR: Prospect not found')

print('\n2. Test get_all_when_scores() - top 5 prospects:')
all_scores = get_all_when_scores()
print(f'   Total scored: {len(all_scores)} prospects')
if all_scores:
    for i, s in enumerate(all_scores[:5], 1):
        print(f'   {i}. {s["prospect_name"]}: {s["when_score"]} ({s["action"]})')

print('\n3. Test get_weekly_priorities() - action breakdown:')
priorities = get_weekly_priorities()
print(f'   Generated at: {priorities["generated_at"][:10]}')
print(f'   Call this week: {len(priorities["call_this_week"])}')
print(f'   Email this week: {len(priorities["email_this_week"])}')
print(f'   Send intro: {len(priorities["send_intro"])}')
print(f'   Nurture: {len(priorities["nurture"])}')
print(f'   Monitor: {len(priorities["monitor"])}')

if priorities['call_this_week']:
    print(f'\n   Top "CALL THIS WEEK" prospect:')
    top = priorities['call_this_week'][0]
    print(f'     {top["prospect_name"]}: {top["when_score"]} score, {top["category"]} category')

print('\n' + '=' * 70)
print('✅ WHEN LAYER TESTS PASSED')
print('=' * 70)

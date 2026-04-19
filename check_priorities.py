from signals.timing import get_weekly_priorities

priorities = get_weekly_priorities()

print('📅 THIS WEEK PRIORITIES:')
print(f"  CALL THIS WEEK: {len(priorities['call_this_week'])}")
print(f"  EMAIL THIS WEEK: {len(priorities['email_this_week'])}")
print(f"  SEND INTRO: {len(priorities['send_intro'])}")

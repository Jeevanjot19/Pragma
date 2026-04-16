from database import get_db

with get_db() as conn:
    prospects = conn.execute(
        "SELECT id, name, status, who_score FROM prospects WHERE status IN ('HOT', 'WARM') LIMIT 5"
    ).fetchall()
    
    print('Available HOT/WARM prospects:')
    for p in prospects:
        print(f"  ID {p[0]}: {p[1]} ({p[2]}) - WHO Score {p[3]}")
    
    if len(prospects) > 0:
        test_id = prospects[0][0]
        print(f'\nTesting with prospect_id={test_id}')

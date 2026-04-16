#!/usr/bin/env python3
"""Display monitoring_events table schema and data"""

from database import get_db

with get_db() as conn:
    # Get table schema
    print('=== monitoring_events TABLE SCHEMA ===\n')
    schema = conn.execute('PRAGMA table_info(monitoring_events)').fetchall()
    
    print('{:<3} {:<25} {:<12} {:<3} {:<10} {:<3}'.format('ID', 'Name', 'Type', 'NN', 'Default', 'PK'))
    print('-' * 70)
    
    for col in schema:
        col_id, name, type_, nn, default, pk = col
        print('{:<3} {:<25} {:<12} {:<3} {:<10} {:<3}'.format(
            col_id, name, type_, 'Y' if nn else 'N', 
            default or 'NULL', 'Y' if pk else ''
        ))
    
    # Show sample data
    print('\n\n=== SAMPLE DATA (3 recent events) ===\n')
    samples = conn.execute('''
        SELECT 
            id, prospect_id, event_type, urgency, title, 
            event_date, detected_at
        FROM monitoring_events 
        ORDER BY detected_at DESC 
        LIMIT 3
    ''').fetchall()
    
    for sample in samples:
        print(f'ID: {sample[0]}')
        print(f'  Prospect ID: {sample[1]}')
        print(f'  Event Type: {sample[2]}')
        print(f'  Urgency: {sample[3]}')
        print(f'  Title: {sample[4]}')
        print(f'  Event Date: {sample[5]}')
        print(f'  Detected At: {sample[6]}')
        print()
    
    # Statistics
    print('\n=== STATISTICS ===\n')
    
    total = conn.execute('SELECT COUNT(*) as cnt FROM monitoring_events').fetchone()['cnt']
    print(f'Total events: {total}')
    
    by_type = conn.execute('''
        SELECT event_type, COUNT(*) as count 
        FROM monitoring_events 
        GROUP BY event_type 
        ORDER BY count DESC
    ''').fetchall()
    
    print(f'\nBy Event Type:')
    for row in by_type:
        print(f'  {row[0]:<20} {row[1]:>3}')
    
    by_urgency = conn.execute('''
        SELECT urgency, COUNT(*) as count 
        FROM monitoring_events 
        GROUP BY urgency 
        ORDER BY count DESC
    ''').fetchall()
    
    print(f'\nBy Urgency:')
    for row in by_urgency:
        print(f'  {row[0]:<20} {row[1]:>3}')
    
    print(f'\nProcessed vs Unprocessed:')
    processed = conn.execute('SELECT COUNT(*) as cnt FROM monitoring_events WHERE is_processed = 1').fetchone()['cnt']
    unprocessed = conn.execute('SELECT COUNT(*) as cnt FROM monitoring_events WHERE is_processed = 0').fetchone()['cnt']
    print(f'  Processed (is_processed=1): {processed}')
    print(f'  Unprocessed (is_processed=0): {unprocessed}')

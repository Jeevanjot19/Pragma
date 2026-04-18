import os
import sqlite3
from database import init_db

# Remove old database
if os.path.exists('pragma.db'):
    os.remove('pragma.db')
    print('✓ Removed old database')

# Initialize with new schema
init_db()
print('✓ Database reinitialized with when_score column')

# Verify column exists
conn = sqlite3.connect('pragma.db')
c = conn.cursor()
c.execute('PRAGMA table_info(prospects)')
cols = [col[1] for col in c.fetchall()]
has_when = 'when_score' in cols
print(f'✓ Has when_score column: {has_when}')

# Run discovery
print('\nRunning discovery pipeline...')
from discovery.news_monitor import run_news_monitor
from database import remove_non_prospects
from discovery.play_store import enrich_all_prospects
from signals.scorer import recalculate_all_scores

result = run_news_monitor()
remove_non_prospects()
enrich_all_prospects()
recalculate_all_scores()

# Check scores
c.execute('SELECT COUNT(*) FROM prospects')
count = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM prospects WHERE when_score > 0')
when_count = c.fetchone()[0]
print(f'\nResults:')
print(f'  Total prospects: {count}')
print(f'  Prospects with WHEN score: {when_count}')

conn.close()
print('✓ Setup complete!')

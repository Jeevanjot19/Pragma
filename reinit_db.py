import os
from database import init_db
import sqlite3

# Remove old database if exists
if os.path.exists('pragma.db'):
    os.remove('pragma.db')
    print('✓ Removed old database')

# Initialize fresh database
init_db()
print('✓ Database initialized')

# Verify tables exist
conn = sqlite3.connect('pragma.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
print(f'✓ Tables created: {len(tables)}')
for table in tables:
    c.execute(f'SELECT COUNT(*) FROM {table}')
    count = c.fetchone()[0]
    print(f'   - {table}: {count} rows')
conn.close()

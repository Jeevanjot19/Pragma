import sqlite3

conn = sqlite3.connect('pragma.db')
c = conn.cursor()

# Check prospect count
c.execute('SELECT COUNT(*) FROM prospects')
count = c.fetchone()[0]
print(f'Total prospects: {count}')

# Check WHEN scores
c.execute('SELECT name, who_score, status FROM prospects LIMIT 5')
print('\nSample prospects:')
for row in c.fetchall():
    print(f'  {row[0]:20} WHO:{row[1]:3} Status:{row[2]}')

# Check table schema
c.execute('PRAGMA table_info(prospects)')
cols = [col[1] for col in c.fetchall()]
print(f'\nTable columns: {", ".join(cols)}')

# Check if WHEN score data exists
c.execute('SELECT when_score FROM prospects LIMIT 1')
try:
    when_score = c.fetchone()[0]
    print(f'Sample when_score value: {when_score}')
except:
    print('when_score column not found in prospects table')

conn.close()

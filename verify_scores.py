import sqlite3
conn = sqlite3.connect('pragma.db')
c = conn.cursor()
hot = c.execute("SELECT COUNT(*) FROM prospects WHERE status = 'HOT'").fetchone()[0]
warm = c.execute("SELECT COUNT(*) FROM prospects WHERE status = 'WARM'").fetchone()[0]
print(f'HOT: {hot}')
print(f'WARM: {warm}')
conn.close()

import sqlite3

conn = sqlite3.connect("memory.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(memory)")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
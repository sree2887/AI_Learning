import sqlite3

conn = sqlite3.connect("memory.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE memory ADD COLUMN embedding BLOB")
    print("Added 'embedding' column successfully.")
except sqlite3.OperationalError as e:
    print("Column may already exist:", e)

conn.commit()
conn.close()
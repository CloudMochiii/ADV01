import sqlite3

conn = sqlite3.connect("boardinghouse.db")

cursor = conn.cursor()

# Rooms table
cursor.execute("""
CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT NOT NULL,
    room_type TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    monthly_rate REAL NOT NULL,
    status TEXT NOT NULL
)
""")

# Reservations table
cursor.execute("""
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    student_id TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    room_id INTEGER NOT NULL,
    reservation_date TEXT NOT NULL,
    status TEXT DEFAULT 'Pending'
)
""")

conn.commit()
conn.close()

print("Database Created Successfully")
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
    status TEXT NOT NULL,
    gender TEXT
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
    status TEXT DEFAULT 'Pending',
    check_in_date TEXT,
    stay_duration INTEGER,
    checkout_date TEXT
)
""")

# Students table
cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT,
    student_id TEXT UNIQUE,
    email TEXT,
    phone TEXT,
    gender TEXT,
    password TEXT,
    student_id_image TEXT
)
""")

# Default rooms (only added if the rooms table is empty)
cursor.execute("SELECT COUNT(*) FROM rooms")

if cursor.fetchone()[0] == 0:

    cursor.execute("""
    INSERT INTO rooms
    (room_number, room_type, capacity, monthly_rate, status, gender)
    VALUES
    ('A101', 'Single', 1, 2500, 'Available', 'Female'),
    ('A102', 'Double', 2, 4500, 'Available', 'Female'),
    ('A103', 'Single', 1, 3000, 'Available', 'Male'),
    ('B201', 'Quadruple', 4, 6500, 'Available', 'Male')
    """)

conn.commit()
conn.close()

print("Database Created Successfully")
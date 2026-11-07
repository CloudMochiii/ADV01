import sqlite3

conn = sqlite3.connect("boardinghouse.db")

cursor = conn.cursor()

rooms = [
    ("A101", "Single", 1, 2500, "Available"),
    ("A102", "Double", 2, 4500, "Available"),
    ("A103", "Single", 1, 3000, "Available"),
    ("B201", "Quadruple", 4, 6500, "Available")
]

cursor.executemany("""
INSERT INTO rooms
(room_number, room_type, capacity, monthly_rate, status)
VALUES (?, ?, ?, ?, ?)
""", rooms)

conn.commit()
conn.close()

print("Rooms Added Successfully")
from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)

app.secret_key = "boardinghouse_secret_key"

@app.route("/")
def home():

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM rooms
    """)

    rooms = cursor.fetchall()

    room_data = []

    for room in rooms:

        cursor.execute("""
        SELECT COUNT(*)
        FROM reservations
        WHERE room_id=?
        AND status='Approved'
        """, (room[0],))

        occupants = cursor.fetchone()[0]

        room_data.append(
            (room, occupants)
        )

    conn.close()

    return render_template(
        "index.html",
        rooms=room_data
    )



@app.route("/reserve/<int:room_id>", methods=["GET", "POST"])
def reserve(room_id):

    if request.method == "POST":

        student_name = request.form["student_name"]
        student_id = request.form["student_id"]
        email = request.form["email"]
        phone = request.form["phone"]
        check_in_date = request.form["check_in_date"]
        stay_duration = request.form["stay_duration"]

        conn = sqlite3.connect("boardinghouse.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO reservations
        (
            student_name,
            student_id,
            email,
            phone,
            room_id,
            reservation_date
        )
        VALUES (?, ?, ?, ?, ?, DATE('now'))
        """,
        (
            student_name,
            student_id,
            email,
            phone,
            room_id
        ))

        conn.commit()
        conn.close()

        return render_template("success.html")

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute(
    "SELECT * FROM rooms WHERE id=?",
    (room_id,)
)

    room = cursor.fetchone()

    conn.close()

    return render_template(
        "reserve.html",
        room=room
)



@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["admin"] = True

            return redirect("/admin")

        return "Invalid Username or Password"

    return render_template("login.html")



@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        reservations.id,
        reservations.student_name,
        reservations.student_id,
        rooms.room_number,
        reservations.reservation_date,
        reservations.status
    FROM reservations
    JOIN rooms
    ON reservations.room_id = rooms.id
    ORDER BY reservations.id DESC
    """)

    reservations = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM reservations"
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM reservations WHERE status='Approved'"
    )
    approved = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM reservations WHERE status='Pending'"
    )
    pending = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM reservations WHERE status='Rejected'"
    )
    rejected = cursor.fetchone()[0]

    cursor.execute(
    "SELECT COUNT(*) FROM reservations WHERE status='Completed'"
    )
    completed = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        reservations=reservations,
        total=total,
        approved=approved,
        pending=pending,
        rejected=rejected,
        completed=completed
    )



@app.route("/approve/<int:id>")
def approve(id):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    # Get room of reservation
    cursor.execute("""
    SELECT room_id
    FROM reservations
    WHERE id=?
    """, (id,))

    room_id = cursor.fetchone()[0]

    # Get room capacity
    cursor.execute("""
    SELECT capacity
    FROM rooms
    WHERE id=?
    """, (room_id,))

    capacity = cursor.fetchone()[0]

    # Count approved occupants
    cursor.execute("""
    SELECT COUNT(*)
    FROM reservations
    WHERE room_id=?
    AND status='Approved'
    """, (room_id,))

    occupants = cursor.fetchone()[0]

    if occupants >= capacity:
        conn.close()
        return "Room capacity reached."

    cursor.execute("""
    UPDATE reservations
    SET status='Approved'
    WHERE id=? AND status='Pending'
    """, (id,))

    cursor.execute("""
    SELECT room_id
    FROM reservations
    WHERE id=?
    """, (id,))

    room_id = cursor.fetchone()[0]

    cursor.execute("""
    UPDATE rooms
    SET status='Occupied'
    WHERE id=?
    """, (room_id,))
   
    conn.commit()
    conn.close()

    return redirect("/admin")



@app.route("/reject/<int:id>")
def reject(id):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE reservations
    SET status='Rejected'
    WHERE id=? AND status='Pending'
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")



@app.route("/delete/<int:id>")
def delete(id):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT room_id, status
    FROM reservations
    WHERE id=?
    """, (id,))

    reservation = cursor.fetchone()

    room_id = reservation[0]
    status = reservation[1]

    if status == "Approved":

        cursor.execute("""
        UPDATE rooms
        SET status='Available'
        WHERE id=?
        """, (room_id,))

        cursor.execute("""
        DELETE FROM reservations
        WHERE id=?
        """, (id,))

    cursor.execute("""
    SELECT status
    FROM reservations
    WHERE id=?
    """, (id,))

    status = cursor.fetchone()[0]

    if status == "Approved":
        return "Approved reservations must be vacated first."
    
    conn.commit()
    conn.close()

    return redirect("/admin")



@app.route("/search")
def search():

    keyword = request.args.get("keyword", "")

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        reservations.id,
        reservations.student_name,
        reservations.student_id,
        rooms.room_number,
        reservations.reservation_date,
        reservations.status
    FROM reservations
    JOIN rooms
    ON reservations.room_id = rooms.id
    WHERE reservations.student_name LIKE ?
    """, ('%' + keyword + '%',))

    reservations = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        reservations=reservations
    )



@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")



@app.route("/vacate/<int:id>")
def vacate(id):

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT room_id
    FROM reservations
    WHERE id=?
    """, (id,))

    room_id = cursor.fetchone()[0]

    cursor.execute("""
    UPDATE rooms
    SET status='Available'
    WHERE id=?
    """, (room_id,))

    cursor.execute("""
    UPDATE reservations
    SET status='Completed'
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")



@app.route("/filter/<status>")
def filter_status(status):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        reservations.id,
        reservations.student_name,
        reservations.student_id,
        rooms.room_number,
        reservations.reservation_date,
        reservations.status
    FROM reservations
    JOIN rooms
    ON reservations.room_id = rooms.id
    WHERE reservations.status = ?
    ORDER BY reservations.id DESC
    """, (status,))

    reservations = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM reservations")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reservations WHERE status='Approved'")
    approved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reservations WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reservations WHERE status='Rejected'")
    rejected = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        reservations=reservations,
        total=total,
        approved=approved,
        pending=pending,
        rejected=rejected
    )



if __name__ == "__main__":
    app.run(debug=True)
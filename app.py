from flask import Flask, render_template, request, redirect, session
import sqlite3

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid

app = Flask(__name__)

app.secret_key = "boardinghouse_secret_key"

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():

    return redirect("/student-login")

@app.route("/student-register", methods=["GET", "POST"])
def student_register():

    if session.get("student_id"):
        return redirect("/home")

    if request.method == "POST":

        name = request.form["student_name"]
        student_id = request.form["student_id"]
        email = request.form["email"]
        phone = request.form["phone"]
        gender = request.form["gender"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match."

        image = request.files["student_id_image"]

        filename = secure_filename(image.filename)

        extension = os.path.splitext(filename)[1].lower()

        if extension not in [".png", ".jpg", ".jpeg"]:
            return "Please upload a PNG or JPG image."

        conn = sqlite3.connect("boardinghouse.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM students
        WHERE student_id=?
        """, (student_id,))

        if cursor.fetchone():

            conn.close()

            return "Student ID already exists."

        cursor.execute("""
        SELECT *
        FROM students
        WHERE email=?
        """, (email,))

        if cursor.fetchone():

            conn.close()

            return "Email already exists."

        filename = uuid.uuid4().hex + "_" + filename

        image.save(
            os.path.join(
                UPLOAD_FOLDER,
                filename
            )
        )

        password = generate_password_hash(password)

        cursor.execute("""
        INSERT INTO students(
            student_name,
            student_id,
            email,
            phone,
            gender,
            password,
            student_id_image
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            student_id,
            email,
            phone,
            gender,
            password,
            filename
        ))

        conn.commit()
        conn.close()

        return redirect("/student-login")

    return render_template("student_register.html")

@app.route("/student-login", methods=["GET", "POST"])
def student_login():

    if session.get("student_id"):
        return redirect("/home")

    if request.method == "POST":

        login = request.form["login"]
        password = request.form["password"]

        conn = sqlite3.connect("boardinghouse.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT student_id, password
        FROM students
        WHERE student_id=? OR email=?
        """, (login, login))

        student = cursor.fetchone()

        conn.close()

        if student and check_password_hash(student[1], password):

            session["student_id"] = student[0]

            return redirect("/home")

        return "Invalid Login"

    return render_template("student_login.html")

@app.route("/student-logout")
def student_logout():

    session.pop("student_id", None)

    return redirect("/student-login")

@app.route("/home")
def home():

    if not session.get("student_id"):
        return redirect("/student-login")

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

    if not session.get("student_id"):
        return redirect("/student-login")

    student_id = session["student_id"]

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        student_name,
        email,
        phone,
        gender
    FROM students
    WHERE student_id=?
    """, (student_id,))

    student = cursor.fetchone()

    if not student:

        conn.close()

        session.pop("student_id", None)

        return redirect("/student-login")

    if request.method == "POST":

        student_name = student[0]
        email = student[1]
        phone = student[2]
        gender = student[3]
        check_in_date = request.form["check_in_date"]
        stay_duration = request.form["stay_duration"]

        cursor.execute("""
        SELECT gender, capacity
        FROM rooms
        WHERE id=?
        """, (room_id,))

        room = cursor.fetchone()

        if not room:
            conn.close()
            return "Room not found."

        room_gender = room[0]
        capacity = room[1]

        if gender != room_gender:
            conn.close()
            return "This room is assigned for the opposite gender."

        cursor.execute("""
        SELECT COUNT(*)
        FROM reservations
        WHERE room_id=?
        AND status='Approved'
        """, (room_id,))

        occupants = cursor.fetchone()[0]

        if occupants >= capacity:
            conn.close()
            return "This room is already full."

        cursor.execute("""
        SELECT *
        FROM reservations
        WHERE student_id=?
        AND status IN ('Pending', 'Approved')
        """, (student_id,))

        if cursor.fetchone():
            conn.close()
            return "You already have an active reservation."

        cursor.execute("""
        INSERT INTO reservations
        (
            student_name,
            student_id,
            email,
            phone,
            room_id,
            reservation_date,
            check_in_date,
            stay_duration
        )
        VALUES (?, ?, ?, ?, ?, DATE('now'), ?, ?)
        """,
        (
            student_name,
            student_id,
            email,
            phone,
            room_id,
            check_in_date,
            stay_duration
        ))

        conn.commit()
        conn.close()

        return render_template("success.html")

    cursor.execute(
    "SELECT * FROM rooms WHERE id=?",
    (room_id,)
)

    room = cursor.fetchone()

    conn.close()

    if not room:
        return "Room not found."

    return render_template(
        "reserve.html",
        room=room,
        student=student
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



@app.route("/students")
def students():

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM students
    """)

    students = cursor.fetchall()

    conn.close()

    return render_template(
        "students.html",
        students=students
    )

@app.route("/delete-student/<int:id>")
def delete_student(id):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM students
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/students")


@app.route("/approve/<int:id>")
def approve(id):

    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("boardinghouse.db")
    cursor = conn.cursor()


    cursor.execute("""
    SELECT room_id
    FROM reservations
    WHERE id=?
    """, (id,))

    room_id = cursor.fetchone()[0]

    cursor.execute("""
    SELECT capacity
    FROM rooms
    WHERE id=?
    """, (room_id,))

    capacity = cursor.fetchone()[0]

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
    SELECT COUNT(*)
    FROM reservations
    WHERE room_id=?
    AND status='Approved'
    """, (room_id,))

    occupants = cursor.fetchone()[0]

    cursor.execute("""
    SELECT capacity
    FROM rooms
    WHERE id=?
    """, (room_id,))

    capacity = cursor.fetchone()[0]

    if occupants >= capacity:

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
    SELECT status
    FROM reservations
    WHERE id=?
    """, (id,))

    reservation = cursor.fetchone()

    if not reservation:

        conn.close()

        return redirect("/admin")

    status = reservation[0]

    if status == "Approved":

        conn.close()

        return "Approved reservations must be vacated first."

    cursor.execute("""
    DELETE FROM reservations
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")



@app.route("/search")
def search():

    if not session.get("admin"):
        return redirect("/login")

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

    cursor.execute("SELECT COUNT(*) FROM reservations")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reservations WHERE status='Approved'")
    approved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reservations WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reservations WHERE status='Rejected'")
    rejected = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reservations WHERE status='Completed'")
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



@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")



@app.route("/vacate/<int:id>")
def vacate(id):

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

    if not reservation or reservation[1] != "Approved":

        conn.close()

        return redirect("/admin")

    room_id = reservation[0]

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

    cursor.execute("SELECT COUNT(*) FROM reservations WHERE status='Completed'")
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



if __name__ == "__main__":
    app.run(debug=True)
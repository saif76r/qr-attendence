from flask import Flask, render_template, request
import sqlite3
from datetime import datetime, date
import qrcode
import io
import base64

app = Flask(__name__)
DB_NAME = "database.db"

# Render public URL
BASE_URL = "https://qr-attendence-and-registration.onrender.com"

# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            name TEXT,
            phone TEXT PRIMARY KEY,
            email TEXT,
            time TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT NOT NULL,
            event_name TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Present',
            FOREIGN KEY(user_phone) REFERENCES users(phone)
        )
    """)
    conn.commit()
    conn.close()

# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            name = request.form.get("name")
            phone = request.form.get("phone")
            email = request.form.get("email")
            reg_time = str(datetime.now())

            # Insert user
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute(
                "INSERT OR IGNORE INTO users (name, phone, email, time) VALUES (?,?,?,?)",
                (name, phone, email, reg_time)
            )
            conn.commit()
            conn.close()

            # Generate QR in memory
            event_name = "SampleEvent"
            qr_data = f"{BASE_URL}/mark_attendance/{phone}/{event_name}"
            qr_img = qrcode.make(qr_data)
            buffer = io.BytesIO()
            qr_img.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()

            return render_template("register.html", message="Registration Successful!", qr_base64=qr_base64)

        except Exception as e:
            import traceback
            return f"<pre>{traceback.format_exc()}</pre>"

    return render_template("register.html")

# -----------------------------
@app.route("/mark_attendance/<phone>/<event_name>")
def mark_attendance(phone, event_name):
    try:
        today = date.today().isoformat()
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM attendance WHERE user_phone=? AND event_name=? AND date=?",
            (phone, event_name, today)
        )
        if c.fetchone():
            conn.close()
            return f"Attendance already marked for {phone}!"
        c.execute(
            "INSERT INTO attendance (user_phone,event_name,date) VALUES (?,?,?)",
            (phone, event_name, today)
        )
        conn.commit()
        conn.close()
        return f"Attendance marked for {phone} for {event_name} on {today}!"
    except Exception as e:
        import traceback
        return f"<pre>{traceback.format_exc()}</pre>"

# -----------------------------
@app.route("/attendance_report")
def attendance_report():
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            SELECT users.name, users.phone, attendance.event_name,
                   attendance.date, attendance.status
              FROM attendance
            JOIN users ON attendance.user_phone = users.phone
        """)
        data = c.fetchall()
        conn.close()
        return render_template("attendance_report.html", data=data)
    except Exception as e:
        import traceback
        return f"<pre>{traceback.format_exc()}</pre>"

# -----------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)

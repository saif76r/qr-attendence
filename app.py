from flask import Flask, render_template, request
import sqlite3, os
from datetime import datetime, date
import qrcode, io, base64

app = Flask(__name__)

# Absolute DB path
DB_NAME = os.path.join(os.path.dirname(__file__), "database.db")

# Render public URL
BASE_URL = "https://qr-attendence-and-registration.onrender.com"

# Initialize DB
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

# Registration
@app.route("/register", methods=["GET","POST"])
def register():
    qr_base64 = None
    message = None
    if request.method=="POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        reg_time = str(datetime.now())

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (name,phone,email,time) VALUES (?,?,?,?)",
                  (name, phone, email, reg_time))
        conn.commit()
        conn.close()

        event_name = "SampleEvent"
        qr_data = f"{BASE_URL}/mark_attendance/{phone}/{event_name}"

        # QR base64
        qr_img = qrcode.make(qr_data)
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")
        qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        message = "Registration Successful!"

    return render_template("register.html", message=message, qr_base64=qr_base64)

# Mark attendance
@app.route("/mark_attendance/<phone>/<event_name>")
def mark_attendance(phone,event_name):
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM attendance WHERE user_phone=? AND event_name=? AND date=?",
              (phone,event_name,today))
    data = c.fetchone()
    if data:
        conn.close()
        return f"Attendance already marked for {phone}!"
    c.execute("INSERT INTO attendance (user_phone,event_name,date) VALUES (?,?,?)",
              (phone,event_name,today))
    conn.commit()
    conn.close()
    return f"Attendance marked for {phone} for {event_name} on {today}!"

# Attendance report
@app.route("/attendance_report")
def attendance_report():
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

if __name__=="__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)

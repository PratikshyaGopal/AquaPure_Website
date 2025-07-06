from flask import Flask, render_template, request, redirect, send_file, session, url_for
import sqlite3
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = 'supersecretkey123'  # change this key in production
DB_PATH = os.path.join(os.path.dirname(__file__), 'orders.db')


# Initialize DB
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                product TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/result", methods=["POST"])
def result():
    name = request.form.get("name")
    email = request.form.get("email")
    product = request.form.get("product")
    quantity = int(request.form.get("quantity"))
    message = request.form.get("message")

    price_per_unit = 10 if product == "1L Bottle" else 25
    total_price = quantity * price_per_unit

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (name, email, product, quantity, total_price, message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, product, quantity, total_price, message))
        conn.commit()

    return render_template("result.html", name=name, email=email, product=product,
                           quantity=quantity, total_price=total_price, message=message)

# Admin Login Route
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "aquapure@123":
            session["admin_logged_in"] = True
            return redirect(url_for("admin"))
        else:
            return render_template("admin_login.html", error="Invalid password.")
    return render_template("admin_login.html")

# Admin Dashboard
@app.route("/admin")
def admin():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders ORDER BY timestamp DESC")
        orders = cursor.fetchall()
    return render_template("admin.html", orders=orders)

# Admin Logout
@app.route("/logout")
def logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

# Excel Export
@app.route("/download")
def download():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM orders", conn)
    file_path = "orders.xlsx"
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)

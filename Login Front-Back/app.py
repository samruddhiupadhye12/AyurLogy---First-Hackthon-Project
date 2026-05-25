from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv("database_hack.env")

app = Flask(__name__)
app.secret_key = "ayurlogy_secret_key"

CORS(app, supports_credentials=True)

# ---------------- DATABASE ----------------
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# ---------------- HOME ----------------
@app.route("/")
def home():
    return jsonify({"status": "Ayurlogy Backend Running"})

# ---------------- REGISTER ----------------
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password")
    if not username or not email or not password:
        return jsonify({"ok": False, "error": "All fields required"}), 400
    try:
        # Hash password before saving – only the hash is stored, never the plain text
        password_bytes = password.encode("utf-8")
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        if mysql and isinstance(e, mysql.connector.IntegrityError):
            return jsonify({"ok": False, "error": "Username or email already exists"}), 400
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------------- LOGIN ----------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password")
    if not username or not password:
        return jsonify({"ok": False, "error": "Username and password required"}), 400
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, username, password FROM users WHERE username=%s",
            (username,),
        )
        user = cur.fetchone()
        cur.close()
        conn.close()
        if not user:
            return jsonify({"ok": False, "error": "Invalid credentials"}), 401

        # Verify password against stored bcrypt hash
        stored_hash = user["password"]
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode("utf-8")
        if not bcrypt.checkpw(password.encode("utf-8"), stored_hash):
            return jsonify({"ok": False, "error": "Invalid credentials"}), 401

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------------- CHECK AUTH ----------------
@app.route("/api/check-auth", methods=["GET"])
def check_auth():
    if "user_id" in session:
        return jsonify({
            "ok": True,
            "username": session["username"]
        })
    return jsonify({"ok": False}), 401

# ---------------- LOGOUT ----------------
@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)

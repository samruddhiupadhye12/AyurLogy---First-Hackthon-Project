from flask import Flask, render_template, request, jsonify, send_from_directory, Response, session, redirect
from flask_cors import CORS
from google import genai
from apscheduler.schedulers.background import BackgroundScheduler
import os
import json
import re
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import bcrypt

# this is the linking of another app.py files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
BACKEND_DIR = os.path.join(PROJECT_DIR, "Login Front-Back")

try:
    from dotenv import load_dotenv
    _env_path = os.path.join(BACKEND_DIR, "database_hack.env")
    if os.path.isfile(_env_path):
        load_dotenv(_env_path)
except ImportError:
    pass

# Use environment variable for API key (never commit real keys to git)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyDW_xq2ZTKlDySwutIYhSKzmw70QOxiYrk")
# old API key =  AIzaSyCKBYet7R3oe5ZwZ5i7bEmi1cQARtDAWNg

# Create a client
client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ayurlogy_secret_key")
CORS(app, supports_credentials=True)

# Path to Frontend AyurLogy hackthon folder
FRONTEND_DIR = BASE_DIR
# Path to Landing -Feedback (Ayush Shop / feedback integration)
LANDING_FEEDBACK_DIR = os.path.join(PROJECT_DIR, "Landing -Feedback")


# --------------- Backend: Database (login/register) ---------------
try:
    import mysql.connector
except ImportError:
    mysql = None

def get_db():
    if mysql is None:
        raise RuntimeError("mysql-connector-python is not installed. Install it for login/register.")
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

# hashing of login and register
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


@app.route("/api/check-auth", methods=["GET"])
def check_auth():
    if "user_id" in session:
        return jsonify({"ok": True, "username": session["username"]})
    return jsonify({"ok": False}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """Save feedback (rating + message) to database."""
    data = request.get_json() or request.form
    rating = data.get("rating")
    message = (data.get("message") or "").strip()
    if not rating:
        return jsonify({"ok": False, "error": "Please select a rating"}), 400
    if not message:
        return jsonify({"ok": False, "error": "Please write your feedback"}), 400
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be 1–5")
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "Invalid rating"}), 400
    if len(message) > 5000:
        return jsonify({"ok": False, "error": "Feedback is too long"}), 400
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO feedback (rating, message) VALUES (%s, %s)",
            (rating, message),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        if mysql and "feedback" in str(e).lower():
            return jsonify({"ok": False, "error": "Feedback table missing. Run: CREATE TABLE IF NOT EXISTS feedback (id INT AUTO_INCREMENT PRIMARY KEY, rating INT NOT NULL, message TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"}), 500
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/start-dosha-reminders", methods=["POST"])
def start_dosha_reminders():
    """Start daily reminder signup for user's dosha. Cron jobs can use this table to send emails."""
    if "user_id" not in session:
        return jsonify({"ok": False, "error": "login_required"}), 401
    data = request.get_json() or {}
    dosha = (data.get("dosha") or "").strip().lower()
    if dosha not in ("vata", "pitta", "kapha"):
        return jsonify({"ok": False, "error": "Invalid dosha"}), 400
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS dosha_reminders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                dosha VARCHAR(20) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            "INSERT INTO dosha_reminders (user_id, dosha) VALUES (%s, %s)",
            (session["user_id"], dosha),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"ok": True, "message": "Daily reminders started. You will receive email notifications."})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500



def send_dosha_reminder_emails():
    """Run by APScheduler daily. Fetch users from dosha_reminders + users and send reminder email."""
    with app.app_context():
        _do_send_dosha_reminder_emails()


def _do_send_dosha_reminder_emails():
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    email_from = os.environ.get("EMAIL_FROM") or smtp_user

    if not smtp_host or not smtp_user or not smtp_password:
        print("[Dosha reminders] SMTP not configured (set SMTP_HOST, SMTP_USER, SMTP_PASSWORD). Skipping email send.")
        return

    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT u.email, u.username, dr.dosha
            FROM dosha_reminders dr
            JOIN users u ON u.id = dr.user_id
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print("[Dosha reminders] DB error:", e)
        return

    if not rows:
        print("[Dosha reminders] No users subscribed. Skipping.")
        return

    dosha_tips = {
        "vata": "Wake calmly, warm meals, gentle movement. Stay grounded today.",
        "pitta": "Cooling foods, avoid excess spice. Take breaks and stay cool.",
        "kapha": "Stay active, light warm foods. Move and energize.",
    }

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        for row in rows:
            to_email = row.get("email") or ""
            username = row.get("username") or "User"
            dosha = (row.get("dosha") or "vata").lower()
            tip = dosha_tips.get(dosha, dosha_tips["vata"])
            subject = f"Ayurlogy – Your {dosha.capitalize()} daily reminder"
            body = f"Hi {username},\n\nYour dosha reminder for today ({dosha.capitalize()}):\n\n{tip}\n\n— Ayurlogy"
            msg = MIMEMultipart()
            msg["From"] = email_from
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            try:
                server.sendmail(email_from, to_email, msg.as_string())
                print("[Dosha reminders] Sent to", to_email)
            except Exception as e:
                print("[Dosha reminders] Failed to send to", to_email, e)
        server.quit()
    except Exception as e:
        print("[Dosha reminders] SMTP error:", e)


def start_scheduler():
    """Start APScheduler for daily dosha reminder emails (e.g. 7:00 AM every day)."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_dosha_reminder_emails, "cron", hour=7, minute=0, id="dosha_reminders")
    scheduler.start()
    print("[Scheduler] Daily dosha reminder job scheduled at 7:00 AM.")


# --------------- Page auth: public vs protected ---------------
# Public: landing, home, explore ayurveda, auth – no login required.
# Protected: chatbot, quiz, ayush shop, products – login required.

def require_page_auth():
    """If user not logged in, redirect to login with ?next= current path."""
    if "user_id" not in session:
        next_url = request.path or "/chat"
        return redirect("/auth.html?next=" + next_url)
    return None


# --------------- Frontend & Chatbot routes ---------------

@app.route("/")
def index():
    """Landing page – main entry point (public)."""
    return send_from_directory(FRONTEND_DIR, "landing.html")


@app.route("/home")
def home_page():
    """Home page (public)."""
    return send_from_directory(FRONTEND_DIR, "home.html")


@app.route("/explore-ayurveda")
def explore_ayurveda():
    """Explore Ayurveda / ideology page (public)."""
    return send_from_directory(FRONTEND_DIR, "ex_ayurveda.html")


@app.route("/chat")
def chat():
    """Chatbot – protected; redirect to login if not authenticated."""
    auth = require_page_auth()
    if auth:
        return auth
    return send_from_directory(FRONTEND_DIR, "chatbot_interface.html")

@app.route("/quiz")
def quiz():
    """Dosha Quiz – protected; redirect to login if not authenticated."""
    auth = require_page_auth()
    if auth:
        return auth
    return send_from_directory(FRONTEND_DIR, "quiz.html")


@app.route("/products")
def products():
    """Ayur-Shop products page – protected."""
    auth = require_page_auth()
    if auth:
        return auth
    return send_from_directory(FRONTEND_DIR, "products.html")

@app.route("/ayush-shop")
def ayush_shop():
    """Ayush Shop – serve products page from Landing -Feedback (with Login/Register in header)."""
    auth = require_page_auth()
    if auth:
        return auth
    return send_from_directory(LANDING_FEEDBACK_DIR, "products.html")


@app.route("/ayush-shop/<path:filename>")
def ayush_shop_file(filename):
    """Serve CSS, images, etc. for Ayush Shop from Landing -Feedback."""
    full = os.path.join(LANDING_FEEDBACK_DIR, filename)
    if os.path.isfile(full):
        return send_from_directory(LANDING_FEEDBACK_DIR, filename)
    from flask import abort
    return abort(404)


@app.route("/login")
def login_page():
    """Serve login page from Landing -Feedback."""
    return send_from_directory(LANDING_FEEDBACK_DIR, "login.html")

@app.route("/register")
def register_page():
    """Serve register page from Landing -Feedback."""
    return send_from_directory(LANDING_FEEDBACK_DIR, "register.html")


@app.route("/landing-static/<path:filename>")
def landing_static(filename):
    """Serve CSS/JS etc. for login/register from Landing -Feedback."""
    full = os.path.join(LANDING_FEEDBACK_DIR, filename)
    if os.path.isfile(full):
        return send_from_directory(LANDING_FEEDBACK_DIR, filename)
    from flask import abort
    return abort(404)


@app.route("/ayush-shop/static/<path:filename>")
def ayush_shop_static(filename):
    """Serve static assets (CSS, images) for Ayush Shop from Landing -Feedback folder."""
    # Try static subfolder first (e.g. static/css/products.css), then root (e.g. products.css)
    for prefix in ("static", ""):
        path = os.path.join(filename) if not prefix else os.path.join(prefix, filename)
        full = os.path.join(LANDING_FEEDBACK_DIR, path)
        if os.path.isfile(full):
            return send_from_directory(LANDING_FEEDBACK_DIR, path)
    from flask import abort
    return abort(404)

@app.route("/api/products")
def get_products():
    """Return products JSON for Ayur-Shop (protected – login required)."""
    if "user_id" not in session:
        return jsonify({"error": "login_required"}), 401
    # Prefer richer product data from Landing -Feedback, fall back to frontend copy.
    candidate_paths = [
        os.path.join(LANDING_FEEDBACK_DIR, "products.json"),
        os.path.join(FRONTEND_DIR, "products.json"),
    ]
    for products_path in candidate_paths:
        if os.path.isfile(products_path):
            with open(products_path, encoding="utf-8") as f:
                data = json.load(f)
            # Normalize shape so frontend always sees {"products": [...]}
            if isinstance(data, list):
                return jsonify({"products": data})
            return jsonify(data)
    return jsonify({"products": []})


@app.route("/frontend/<path:filename>")
def serve_frontend(filename):
    """Serve all frontend files: HTML, CSS, JS, images, header, footer."""
    return send_from_directory(FRONTEND_DIR, filename)


# Protected HTML files: direct URL access requires login (e.g. /quiz.html, /chatbot_interface.html)
PROTECTED_HTML = {"chatbot_interface.html", "quiz.html", "products.html", "ayush_shop.html"}


@app.route("/<path:filename>")
def serve_page(filename):
    """Serve HTML, CSS, JS, images from frontend. Protected pages require login."""
    if filename.startswith("frontend") or filename.startswith("ask") or filename.startswith("api"):
        from flask import abort
        return abort(404)
    if filename in PROTECTED_HTML:
        auth = require_page_auth()
        if auth:
            return auth
    path = os.path.join(FRONTEND_DIR, filename)
    if os.path.isfile(path):
        return send_from_directory(FRONTEND_DIR, filename)
    from flask import abort
    return abort(404)

def require_chat_auth():
    """Return 401 if user is not logged in (chatbot is protected)."""
    if "user_id" not in session:
        return jsonify({"ok": False, "error": "login_required"}), 401
    return None


chat_history = []
@app.route("/ask", methods=["POST"])
def ask():
    auth_err = require_chat_auth()
    if auth_err:
        return auth_err
    data = request.get_json()
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"reply": "Please type a question.", "suggestions": []})

    system_prompt = "Always give a complete, detailed answer. Do not summarize previous responses."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
   
    mode = "independent"  
    if mode == "independent":
        full_prompt = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    else:
        chat_history.append({"role": "user", "content": prompt})
        full_prompt = [{"role": "system", "content": system_prompt}] + chat_history

    try:
        # Ayurveda + GK + general info assistant for Ayurlogy
        full_prompt = (
            "You are Ayurlogy AI, a helpful assistant. You answer: (1) Ayurveda topics (doshas, meditation, yoga, herbs, lifestyle), "
            "(2) General Knowledge (GK) questions, and (3) any other informative questions. "
            "IMPORTANT – OUTPUT FORMAT based on user request:\n"
            "• If user asks for 'chart', 'table', 'tabular', 'in a table', 'compare in table', 'list in table', or similar → "
            "you MUST respond with an HTML <table> structure. and also do not add extra, uneven space while giving response. Use <table>, <thead>, <tbody>, <tr>, <th>, <td>. "
            "Example for 'explain three doshas in chart format': "
            "<table><thead><tr><th>Dosha</th><th>Element</th><th>Traits</th></tr></thead><tbody>"
            "<tr><td>Vata</td><td>Air + Space</td><td>Creative, quick, light</td></tr>...</tbody></table>\n"
            "• For normal questions → use <p>, <strong>, <ul>, <li>, <em>.\n"
            "Use a friendly, concise style. Bold terms with <strong>. Use emojis like 🌿, 🧘, 🍵 when helpful. "
            "Make follow-up suggestions specific to the topic. "
            "Do NOT introduce yourself. Start directly with the answer. "
            "End with a short educational disclaimer (not medical advice). "
            "Respond ONLY as valid JSON: {\"answer\": \"<html content>\", \"suggestions\": [{\"label\": \"...\", \"emoji\": \"🌿\"}, ...]}. "
            "Output ONLY the JSON object. No code fences, no extra text.\n\n"
            f"User question: {prompt}"
        )

        # Retry on 429 (quota/rate limit) – wait and try again up to 2 times
        response = None
        last_error = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                    config={
                        "temperature": 0.6,
                        "top_p": 0.9,
                        "top_k": 32,
                        "max_output_tokens": 8000,
                    },
                )
                break
            except Exception as e:
                last_error = e
                err_str = str(e).upper()
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "QUOTA" in err_str:
                    if attempt < 2:
                        time.sleep(35)  # Wait ~35s as suggested by API
                    else:
                        raise
                else:
                    raise
        raw_text = (response.text or "").strip()

        if raw_text.startswith("```"):
            parts = raw_text.split("```")
            if len(parts) >= 3:
                candidate = parts[1]
               
                if "\n" in candidate:
                    candidate = candidate.split("\n", 1)[1]
                raw_text = candidate.strip()

        # Default: treat whole text as answer
        answer = raw_text

        # 
        try:
            json_candidate = raw_text

            # If there is extra text around JSON, try to grab the first {...} block
            if "{" in raw_text and "}" in raw_text:
                start = raw_text.find("{")
                end = raw_text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    json_candidate = raw_text[start : end + 1]

            parsed = json.loads(json_candidate)
            if isinstance(parsed, dict):
                parsed_answer = str(parsed.get("answer") or "").strip()
                if parsed_answer:
                    answer = parsed_answer
                parsed_suggestions = parsed.get("suggestions") or []
                if isinstance(parsed_suggestions, list):
                    normalized = []
                    for item in parsed_suggestions:
                        # New format: objects with label + emoji
                        if isinstance(item, dict):
                            label = str(item.get("label") or "").strip()
                            emoji = str(item.get("emoji") or "").strip() or "🌿"
                            if label:
                                normalized.append({"label": label, "emoji": emoji})
                        # Backwards compatible: plain string
                        else:
                            label = str(item or "").strip()
                            if label:
                                normalized.append({"label": label, "emoji": "🌿"})
                    suggestions = normalized
        except Exception:
            # If parsing fails, try regex to extract answer from raw JSON-like text
            try:
                match = re.search(
                    r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"suggestions"',
                    raw_text,
                    re.DOTALL,
                )
                if match:
                    answer = match.group(1).encode().decode("unicode_escape")
            except Exception:
                pass
            # else keep raw_text as answer (will be cleaned below)

        # Strip any JSON prefix – use regex to catch all variants (e.g. " { "answer": ", {"answer":")
        _cleaned = re.sub(
            r'^[\s"\']*\{\s*["\']answer["\']\s*:\s*["\']\s*',
            "",
            answer.strip(),
            flags=re.IGNORECASE,
        )
        if _cleaned != answer.strip():
            answer = _cleaned

        # Truncate if Gemini output duplicate JSON mid-stream (e.g. ...text { "answer": ")
        _dup = re.search(r'\s*\{\s*["\']answer["\']\s*:\s*["\']', answer)
        if _dup and _dup.start() > 0:
            answer = answer[: _dup.start()].rstrip()

        # Remove trailing JSON artifacts (e.g. ", "suggestions": [...] or " })
        answer = re.sub(
            r'["\']?\s*,\s*["\']suggestions["\'].*$', "", answer, flags=re.DOTALL | re.IGNORECASE
        ).rstrip()
        answer = answer.rstrip('"\'} ')

        # Best-effort: strip any repeated self-intro if it still appears
        intro_phrases = [
            "Namaste! I am Ayurlogy AI",
            "Namaste! I am **Ayurlogy AI**",
        ]
        for phrase in intro_phrases:
            if answer.lower().startswith(phrase.lower()):
                parts = answer.split("\n\n", 1)
                if len(parts) == 2:
                    answer = parts[1].lstrip()
                break

        reply_text = answer or "I'm sorry, I couldn't generate a response."
    except Exception as e:
        err_str = str(e).upper()
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "QUOTA" in err_str:
            reply_text = (
                "🌿 <strong>API quota reached</strong><br><br>"
                "The free tier limit for today has been reached. Please try again tomorrow, "
                "or check your <a href='https://ai.google.dev/gemini-api/docs/rate-limits' target='_blank'>Gemini API plan</a> "
                "for higher limits."
            )
        else:
            reply_text = f"Sorry, something went wrong. Please try again. (Error: {e})"
        suggestions = []

    return jsonify({"reply": reply_text, "suggestions": suggestions})


STREAM_DELIMITER = "===SUGGESTIONS==="


@app.route("/ask_stream", methods=["POST"])
def ask_stream():
    """Stream the answer as it arrives for faster perceived response."""
    auth_err = require_chat_auth()
    if auth_err:
        return auth_err
    data = request.get_json()
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"reply": "Please type a question.", "suggestions": []})

    full_prompt = (
        "You are Ayurlogy AI. Answer: (1) Ayurveda (doshas, yoga, herbs), (2) GK/General Knowledge, with it's small inforamtion also give about GK question (3) any info questions. "
        "FORMAT: If user asks for 'chart', 'table', 'tabular', 'in a table' → use HTML <table><thead><tbody><tr><th><td>. "
        "For ALL other responses, ALWAYS use structured HTML formatting: "
        "• Wrap section headings in <strong> (e.g. <strong>Morning Routine</strong>) "
        "• Bold key terms, ingredients, and important labels with <strong> (e.g. <strong>Ingredients to Avoid</strong>) "
        "• Use <ul><li> for lists. Use <p> for paragraphs. Use <em> for subtle emphasis. "
        "• Be CONSISTENT: every response must use <strong> for headings and key terms, not plain text. "
        "Emojis 🌿 🧘 🍵 OK. Do NOT introduce yourself. Start with the answer. End with short educational disclaimer. "
        "At the very end, on a new line, write exactly " + STREAM_DELIMITER + " "
        "then a JSON array of 2-4 objects with 'label' and 'emoji'. Example: "
        "===SUGGESTIONS===[{\"label\":\"Diet for Kapha\",\"emoji\":\"🍽️\"},{\"label\":\"Morning routine\",\"emoji\":\"🌅\"}]\n\n"
        f"User question: {prompt}"
    )

    def generate():
        buffer = ""
        suggestions = []
        try:
            stream = None
            for attempt in range(3):
                try:
                    stream = client.models.generate_content_stream(
                        model="gemini-2.5-flash",
                        contents=full_prompt,
                        config={
                            "temperature": 0.6,
                            "top_p": 0.9,
                            "top_k": 32,
                            "max_output_tokens": 8000,
                        },
                    )
                    break
                except Exception as e:
                    err_str = str(e).upper()
                    if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "QUOTA" in err_str) and attempt < 2:
                        time.sleep(35)
                    else:
                        raise

            if stream is None:
                raise Exception("Failed to create stream")
            for chunk in stream:
                if chunk.text:
                    buffer += chunk.text
                    if STREAM_DELIMITER not in buffer:
                        yield f"data: {json.dumps({'type': 'chunk', 'text': chunk.text})}\n\n"
                    else:
                        delim_start = buffer.find(STREAM_DELIMITER)
                        chunk_start = len(buffer) - len(chunk.text)
                        if delim_start > chunk_start:
                            to_send = chunk.text[: delim_start - chunk_start]
                            if to_send:
                                yield f"data: {json.dumps({'type': 'chunk', 'text': to_send})}\n\n"
                        break

            if STREAM_DELIMITER in buffer:
                answer_part, _, suggestions_part = buffer.partition(STREAM_DELIMITER)
                answer = answer_part.strip()
                suggestions_raw = suggestions_part.strip()
                try:
                    parsed = json.loads(suggestions_raw)
                    if isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict):
                                label = str(item.get("label") or "").strip()
                                emoji = str(item.get("emoji") or "🌿").strip() or "🌿"
                                if label:
                                    suggestions.append({"label": label, "emoji": emoji})
                            else:
                                label = str(item or "").strip()
                                if label:
                                    suggestions.append({"label": label, "emoji": "🌿"})
                except Exception:
                    pass
            else:
                answer = buffer.strip()

            answer = re.sub(
                r'^[\s"\']*\{\s*["\']answer["\']\s*:\s*["\']\s*', "", answer, flags=re.IGNORECASE
            )
            answer = answer.rstrip('"\'} ')
            yield f"data: {json.dumps({'type': 'done', 'reply': answer or 'No response.', 'suggestions': suggestions})}\n\n"
        except Exception as e:
            err_str = str(e).upper()
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "QUOTA" in err_str:
                msg = (
                    "🌿 <strong>API quota reached</strong><br><br>"
                    "The free tier limit for today has been reached. Please try again tomorrow."
                )
            else:
                msg = f"Sorry, something went wrong. Please try again. (Error: {e})"
            yield f"data: {json.dumps({'type': 'done', 'reply': msg, 'suggestions': []})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    start_scheduler()
    # use_reloader=False so the scheduler runs only once (otherwise it would start twice in debug)
    app.run(debug=True, port=5000, use_reloader=False)
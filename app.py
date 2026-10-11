import csv
import hmac
import os
import secrets
import threading
import time
from datetime import datetime
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, make_response, redirect, render_template,
    request, send_file, session, url_for
)
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
PDF_PATH = BASE_DIR / "private_books" / "until_28_october.pdf"
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "download_records.csv"
CSV_COLUMNS = [
    "Record ID", "Date", "Time", "Full Name", "Email Address",
    "Book Name", "Download Status"
]
CSV_LOCK = threading.Lock()
RATE_LOCK = threading.Lock()
RECENT_REQUESTS = {}
RATE_WINDOW_SECONDS = 60
RATE_MAX_REQUESTS = 8

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1",
    MAX_CONTENT_LENGTH=16 * 1024,  # Forms should never need large uploads.
)
# If deploying behind a trusted reverse proxy, configure ProxyFix carefully.
# Do not enable it blindly on a directly exposed development server.


def ensure_csv():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_LOCK:
        if not CSV_PATH.exists():
            with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as csv_file:
                csv.writer(csv_file).writerow(CSV_COLUMNS)


def record_download_request(name, email, status="Download Requested"):
    """Append a voluntary request record; this does not prove the PDF was read."""
    ensure_csv()
    now = datetime.now().astimezone()
    record_id = secrets.token_hex(8)
    row = [
        record_id, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"),
        name, email, "Until 28 October", status
    ]
    with CSV_LOCK:
        with CSV_PATH.open("a", newline="", encoding="utf-8-sig") as csv_file:
            csv.writer(csv_file).writerow(row)


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


app.jinja_env.globals["csrf_token"] = csrf_token


def valid_csrf():
    submitted = request.form.get("_csrf_token", "")
    expected = session.get("_csrf_token", "")
    return bool(submitted and expected and hmac.compare_digest(submitted, expected))


def rate_limited(key):
    now = time.time()
    with RATE_LOCK:
        times = [t for t in RECENT_REQUESTS.get(key, []) if now - t < RATE_WINDOW_SECONDS]
        if len(times) >= RATE_MAX_REQUESTS:
            RECENT_REQUESTS[key] = times
            return True
        times.append(now)
        RECENT_REQUESTS[key] = times
        return False


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
        "font-src 'self' https://fonts.gstatic.com; script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; media-src 'self'; object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    )
    return response


@app.route("/")
def index():
    ensure_csv()
    return render_template("index.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/download", methods=["POST"])
def download_book():
    if not valid_csrf():
        flash("Your form session expired. Please try again.", "error")
        return redirect(url_for("index") + "#download")
    # Honeypot field: humans should leave this hidden field blank.
    if request.form.get("website", "").strip():
        abort(400)
    client_key = request.remote_addr or "unknown"
    if rate_limited(client_key):
        flash("Too many requests in a short time. Please wait a minute and try again.", "error")
        return redirect(url_for("index") + "#download")

    name = " ".join(request.form.get("full_name", "").split())
    email = request.form.get("email", "").strip()
    consent = request.form.get("consent") == "yes"

    if not name or len(name) > 100:
        flash("Please enter your name (up to 100 characters).", "error")
        return redirect(url_for("index") + "#download")
    if (len(email) > 254 or "@" not in email or email.startswith("@")
            or email.endswith("@") or any(ch.isspace() for ch in email)):
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("index") + "#download")
    if not consent:
        flash("Please confirm the privacy notice before requesting the book.", "error")
        return redirect(url_for("index") + "#download")

    if not PDF_PATH.is_file():
        flash("The book PDF has not been added yet. Please check back soon.", "error")
        return redirect(url_for("index") + "#download")

    try:
        record_download_request(name, email)
    except OSError:
        app.logger.error("Unable to save a download request record.")
        flash("Sorry, the download could not be processed right now. Please try again later.", "error")
        return redirect(url_for("index") + "#download")

    # The record means the server processed the request, not that the file was opened.
    response = send_file(
        PDF_PATH, as_attachment=True, download_name="Until_28_October.pdf",
        mimetype="application/pdf", conditional=True
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if not valid_csrf():
            flash("Your session expired. Please try again.", "error")
            return redirect(url_for("admin_login"))
        if rate_limited(request.remote_addr or "unknown"):
            flash("Too many attempts. Wait a minute and try again.", "error")
            return render_template("admin_login.html")
        configured_password = os.getenv("ADMIN_PASSWORD", "")
        password = request.form.get("password", "")
        if not configured_password:
            flash("Admin access is not configured. Set ADMIN_PASSWORD in your .env file.", "error")
        elif hmac.compare_digest(password.encode(), configured_password.encode()):
            session.clear()
            session["admin_authenticated"] = True
            session["_csrf_token"] = secrets.token_urlsafe(32)
            return redirect(url_for("admin_home"))
        else:
            flash("That password was not accepted.", "error")
    return render_template("admin_login.html")


@app.route("/admin")
@admin_required
def admin_home():
    ensure_csv()
    return render_template("admin.html", record_count=max(0, sum(1 for _ in CSV_PATH.open(encoding="utf-8-sig")) - 1))


@app.route("/admin/downloads.csv")
@admin_required
def admin_csv():
    ensure_csv()
    response = send_file(CSV_PATH, as_attachment=True, download_name="download_records.csv", mimetype="text/csv")
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    if not valid_csrf():
        abort(400)
    session.clear()
    return redirect(url_for("admin_login"))


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(_error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    ensure_csv()
    # Debug is off by default; never enable it on a public server.
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)

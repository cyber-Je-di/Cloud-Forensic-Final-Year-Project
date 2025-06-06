import os
import sys
import json
import re
import csv
import io
import random
import string

# Add the project root directory (parent of 'dashboard') to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
    Response
)
from functools import wraps
from dashboard.alert import load_alerts_data

app = Flask(__name__)
app.secret_key = "supersecurekey"

USERS_FILE = "users.json"
ACCESS_REQUESTS_FILE = "access_requests.json"
BASE_LOG_DIR = "/var/log"
UPLOAD_DIR = "uploads"


# ---------- Utility Functions ----------

def ensure_json_file(path, default):
    """
    Make sure that path exists on disk. If not, create and write default into it.
    """
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f, indent=4)


def load_users():
    """
    Load users.json. If missing or invalid, re-create as empty dict.
    """
    ensure_json_file(USERS_FILE, {})
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        # Overwrite with fresh data if JSON is corrupted
        with open(USERS_FILE, "w") as f:
            json.dump({}, f, indent=4)
        return {}


def save_users(users):
    """Write the given users dict back to USERS_FILE."""
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def load_access_requests():
    """
    Load access_requests.json. If missing or invalid, create an empty list.
    """
    ensure_json_file(ACCESS_REQUESTS_FILE, [])
    try:
        with open(ACCESS_REQUESTS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        # Overwrite with fresh data if JSON is corrupted
        with open(ACCESS_REQUESTS_FILE, "w") as f:
            json.dump([], f, indent=4)
        return []


def save_access_requests(requests_list):
    """Write the given list of requests back to ACCESS_REQUESTS_FILE."""
    with open(ACCESS_REQUESTS_FILE, "w") as f:
        json.dump(requests_list, f, indent=4)


def get_available_tenants(user):
    """
    If user.role == admin, return ALL “tenant-*” directories under BASE_LOG_DIR.
    Otherwise, return the “authorized_tenants” list from users.json.
    """
    users = load_users()
    if user not in users:
        return []
    if users[user].get("role") == "admin":
        # Return all subdirs in /var/log that begin with “tenant-”
        try:
            return sorted([d for d in os.listdir(BASE_LOG_DIR)
                           if os.path.isdir(os.path.join(BASE_LOG_DIR, d)) and d.startswith("tenant-")])
        except FileNotFoundError:
            return []
    return users[user].get("authorized_tenants", [])


def login_required(role=None):
    """
    Decorator to ensure we’re logged in. Optionally check for a specific role (“admin” or “analyst”).
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                return "Access Denied", 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper


def search_logs(tenant, query=None):
    """
    Look up all *.log files under /var/log/<tenant>/, return lines matching “query” (if any).
    """
    results = []
    tenant_dir = os.path.join(BASE_LOG_DIR, tenant)
    if not os.path.isdir(tenant_dir):
        return results

    for fname in os.listdir(tenant_dir):
        if fname.endswith(".log"):
            path = os.path.join(tenant_dir, fname)
            try:
                with open(path, "r", errors="ignore") as f:
                    for i, line in enumerate(f, start=1):
                        if not query or re.search(query, line, re.IGNORECASE):
                            results.append({
                                "file": fname,
                                "line_num": i,
                                "content": line.rstrip("\n"),
                                "tenant": tenant
                            })
            except Exception:
                # Skip files we cannot open
                continue
    return results


# ---------- Routes ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Standard login: check username/password against users.json.
    If admin → redirect to /admin, else → redirect /select.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_users()
        user_entry = users.get(username)

        if user_entry and user_entry.get("password") == password:
            session["user"] = username
            session["role"] = user_entry.get("role", "")
            if user_entry.get("role") == "admin":
                return redirect(url_for("admin_panel"))
            else:
                return redirect(url_for("select_tenant"))

        flash("Invalid credentials.", "danger")
    return render_template("login.html",
                           logout_url=url_for("logout"))


@app.route("/logout")
def logout():
    """Clear the session and go back to /login."""
    session.clear()
    flash("You have successfully logged out.", "info")
    return redirect(url_for("login"))


@app.route("/select", methods=["GET", "POST"])
@login_required("analyst")
def select_tenant():
    """
    Allow “analyst” users to pick one of their authorized_tenants. Then redirect to /dashboard.
    """
    user = session.get("user")
    tenants = get_available_tenants(user)

    if request.method == "POST":
        selected = request.form.get("tenant")
        if selected in tenants:
            session["selected_tenant"] = selected
            return redirect(url_for("dashboard"))
        else:
            flash("You are not authorized for that tenant.", "warning")

    return render_template("select_tenant.html",
                           tenants=tenants,
                           selected_tenant=session.get("selected_tenant"),
                           logout_url=url_for("logout"))


@app.route("/", methods=["GET", "POST"])
@login_required("analyst")
def dashboard():
    """
    Show logs (and a search field). Analysts can see only their authorized tenants. Admins never use this route.
    """
    user = session.get("user")
    selected_tenant = session.get("selected_tenant", None)
    query = request.form.get("query", "").strip()

    tenants = get_available_tenants(user)
    active_tenants_count = len(tenants) # New: Active tenants count
    all_logs = {}

    # Refined logic for populating all_logs for display:
    display_tenants = []
    if selected_tenant and selected_tenant != "All Tenants":
        if selected_tenant in tenants: # Ensure selected tenant is authorized
            display_tenants = [selected_tenant]
    else: # "All Tenants" or no specific selection, so use all authorized tenants
        display_tenants = tenants

    for tenant_name in display_tenants:
        logs = search_logs(tenant_name, query)
        all_logs[tenant_name] = logs
    
    total_log_entries_count = sum(len(log_list) for log_list in all_logs.values()) # New: Total log entries

    # For the "Logs Per Tenant" chart, show all authorized tenants' log counts
    logs_per_tenant_for_chart = {t: len(search_logs(t, query)) for t in tenants}

    # Example threat stats (replace with load_alerts() or real data)
    # If you want to integrate load_alerts(), just do: stats, ts_data = load_alerts()
    # Keep existing chart_stats for now
    chart_stats = {
        "Critical": 12,
        "High": 28,
        "Medium": 45,
        "Low": 67
    }

    current_total_alerts, current_security_events = load_alerts_data(
        selected_tenant=session.get("selected_tenant"), # Pass the raw value from session
        authorized_tenants=tenants
    )

    return render_template(
        "index.html",
        user=user,
        role=session.get("role"),
        selected_tenant=selected_tenant or "All Tenants",
        query=query,
        all_logs=all_logs, # Contains logs for display (filtered by selection)
        logs_per_tenant=logs_per_tenant_for_chart, # For the chart (all authorized tenants)
        stats=chart_stats, # For the alert statistics chart
        total_alerts_dynamic=current_total_alerts,         # New dynamic value for the card
        security_events_dynamic=current_security_events,   # New dynamic value for the card
        active_tenants_dynamic=active_tenants_count,        # New dynamic value
        total_log_entries_dynamic=total_log_entries_count, # New dynamic value
        logout_url=url_for("logout")
    )


@app.route("/admin", methods=["GET", "POST"])
@login_required("admin")
def admin_panel():
    """
    Admin dashboard: show all users, access requests, allow approving/denying new analysts, and removing existing users.
    """
    users = load_users()
    tenants = get_available_tenants("admin")
    access_requests = load_access_requests()

    if request.method == "POST":
        action = request.form.get("action", "")
        username = request.form.get("username", "").strip()

        # ─── Approve an access request ─────────────────────────────────────────────────
        if action == "approve" and username:
            # Check that this username is in the access_requests list
            matching_requests = [r for r in access_requests if r.get("username") == username]
            if not matching_requests:
                flash(f"No pending request found for '{username}'.", "warning")
            else:
                assigned_tenants = request.form.getlist("tenants")
                # Create a temporary password
                password = "Temp" + "".join(random.choices(string.ascii_letters + string.digits, k=6))

                # Add to users.json as an “analyst”
                users[username] = {
                    "password": password,
                    "role": "analyst",
                    "authorized_tenants": assigned_tenants
                }
                flash(f"Approved '{username}'. Temporary password: {password}", "success")

                # Remove from access_requests
                access_requests = [r for r in access_requests if r.get("username") != username]

        # ─── Delete a pending access request ──────────────────────────────────────────────────
        elif action == "delete_request" and username:
            # Remove from the JSON array
            filtered = [r for r in access_requests if r.get("username") != username]
            if len(filtered) == len(access_requests):
                flash(f"No such pending request for '{username}'.", "warning")
            else:
                flash(f"Deleted access request from '{username}'.", "info")
            access_requests = filtered

        # ─── Remove an existing user ────────────────────────────────────────────────────────
        elif action == "remove_user":
            del_user = request.form.get("delete_user", "").strip()
            if del_user and del_user in users:
                del users[del_user]
                flash(f"User '{del_user}' removed.", "info")
            else:
                flash(f"User '{del_user}' not found.", "warning")

        else:
            flash("Unknown action or missing 'username' field.", "danger")

        # Save updated users.json and access_requests.json
        save_users(users)
        save_access_requests(access_requests)
        return redirect(url_for("admin_panel"))

    return render_template(
        "admin.html",
        users=users,
        requests=access_requests,
        tenants=tenants,
        logout_url=url_for("logout")
    )


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Serve files from the 'uploads' directory."""
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/request-access", methods=["GET", "POST"])
def request_access():
    """
    Unauthenticated “request access” form. Anyone can fill this out (no login required).
    Admin will see it in /admin and can choose to approve or delete.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        nrc = request.form.get("nrc", "").strip()
        license_id = request.form.get("license_id", "").strip()
        reason = request.form.get("reason", "").strip()
        proof = request.files.get("proof")

        if not username or not nrc or not license_id or not reason:
            flash("All fields except ‘proof’ are required.", "danger")
            return redirect(url_for("request_access"))

        # Save uploaded proof (optional)
        filename = ""
        if proof and proof.filename:
            os.makedirs(UPLOAD_DIR, exist_ok=True)
            filename = proof.filename
            proof.save(os.path.join(UPLOAD_DIR, filename))

        # Build a single dict for this request
        request_entry = {
            "username": username,
            "nrc": nrc,
            "license_id": license_id,
            "reason": reason,
            "proof_file": filename
        }

        # Load existing requests and append
        requests_list = load_access_requests()
        requests_list.append(request_entry)
        save_access_requests(requests_list)

        flash("Request submitted. Await admin approval.", "success")
        return redirect(url_for("request_access"))

    return render_template("request_access.html",
                           logout_url=url_for("logout"))


@app.route('/export_logs', methods=['POST'])
@login_required()  # Allows both admin and analysts
def export_logs():
    """
    Export all logs (across all authorized tenants) to a single CSV download.
    """
    user = session.get("user")
    tenants = get_available_tenants(user)
    all_rows = []

    for tenant in tenants:
        logs = search_logs(tenant)
        for log in logs:
            all_rows.append([tenant, log["file"], log["line_num"], log["content"]])

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Tenant', 'Log File', 'Line Number', 'Content'])
    cw.writerows(all_rows)
    output = si.getvalue()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=logs_export.csv"}
    )


# ---------- Run Server ----------

if __name__ == "__main__":
    # Ensure that our JSON files exist before we start
    ensure_json_file(USERS_FILE, {})
    ensure_json_file(ACCESS_REQUESTS_FILE, [])

    # Make sure “uploads/” exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    app.run(host="0.0.0.0", port=5000, debug=True)
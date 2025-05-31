from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import json, os
from flask import send_from_directory
import re
from flask import Response
import csv
import io

app = Flask(__name__)
app.secret_key = 'supersecurekey'

USERS_FILE = "users.json"
BASE_LOG_DIR = "/var/log"

# ---------- Utility Functions ----------

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def get_available_tenants(user):
    users = load_users()
    if users[user]["role"] == "admin":
        return sorted([d for d in os.listdir(BASE_LOG_DIR) if d.startswith("tenant-")])
    return users[user].get("authorized_tenants", [])

def login_required(role=None):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                return "Access Denied", 403
            return f(*args, **kwargs)
        return decorated
    return wrapper

def load_alerts():
    try:
        with open("alerts.json") as f:
            data = json.load(f)
            return data.get("alerts", []), data.get("threat_statistics", {})
    except Exception as e:
        print(f"Error loading alerts.json: {e}")
        return [], {}

def search_logs(tenant, query=None):
    results = []
    tenant_dir = os.path.join(BASE_LOG_DIR, tenant)
    if not os.path.exists(tenant_dir):
        return results

    for fname in os.listdir(tenant_dir):
        if fname.endswith(".log"):
            path = os.path.join(tenant_dir, fname)
            with open(path, 'r', errors='ignore') as f:
                for i, line in enumerate(f, 1):
                    if not query or re.search(query, line, re.IGNORECASE):
                        results.append({
                            'file': fname,
                            'line_num': i,
                            'content': line.strip(),
                            'tenant': tenant
                        })
    return results

# ---------- Routes ----------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        users = load_users()
        user = users.get(username)
        if user and user["password"] == password:
            session["user"] = username
            session["role"] = user["role"]
            return redirect(url_for("admin_panel") if user["role"] == "admin" else url_for("select_tenant"))
        flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/select", methods=["GET", "POST"])
@login_required("analyst")
def select_tenant():
    user = session["user"]
    tenants = get_available_tenants(user)
    if request.method == "POST":
        selected = request.form["tenant"]
        if selected in tenants:
            session["selected_tenant"] = selected
            return redirect(url_for("dashboard"))
    return render_template("select_tenant.html", tenants=tenants)

@app.route("/", methods=["GET", "POST"])
@login_required("analyst")
def dashboard():
    user = session["user"]
    role = session["role"]
    query = request.form.get("query", "")

    tenants = get_available_tenants(user)
    all_data = {}

    alerts, stats = load_alerts()  # Global alert summary for all tenants

    for tenant in tenants:
        logs = search_logs(tenant, query)
        all_data[tenant] = logs

    return render_template("index.html", all_logs=all_data, alerts=alerts, stats=stats, tenants=tenants, query=query, user=user)


@app.route("/admin", methods=["GET", "POST"])
@login_required("admin")
def admin_panel():
    users = load_users()
    tenants = get_available_tenants("admin")

    # Load access requests
    if os.path.exists("access_requests.json"):
        with open("access_requests.json", "r") as f:
            requests = json.load(f)
    else:
        requests = []

    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username")

        if action == "approve":
            assigned_tenants = request.form.getlist("tenants")
            password = "Temp" + ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            users[username] = {
                "password": password,
                "role": "analyst",
                "authorized_tenants": assigned_tenants
            }
            flash(f"Approved {username}. Temporary password: {password}")
            requests = [r for r in requests if r["username"] != username]

        elif action == "delete":
            flash(f"Request from {username} deleted.")
            requests = [r for r in requests if r["username"] != username]

        elif action == "remove_user":
            del_user = request.form.get("delete_user")
            if del_user in users:
                del users[del_user]
                flash(f"User {del_user} removed.")

        # Save updates
        with open("users.json", "w") as f:
            json.dump(users, f, indent=4)
        with open("access_requests.json", "w") as f:
            json.dump(requests, f, indent=4)

    return render_template("admin.html", users=users, requests=requests, tenants=tenants)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory("uploads", filename)


@app.route("/request-access", methods=["GET", "POST"])
def request_access():
    if request.method == "POST":
        username = request.form["username"]
        nrc = request.form["nrc"]
        license_id = request.form["license_id"]
        reason = request.form["reason"]
        proof = request.files["proof"]

        # Save uploaded proof (optional feature)
        if proof:
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            proof.save(os.path.join(upload_dir, proof.filename))

        # Load and save request
        request_entry = {
            "username": username,
            "nrc": nrc,
            "license_id": license_id,
            "reason": reason,
            "proof_file": proof.filename
        }

        if os.path.exists("access_requests.json"):
            with open("access_requests.json", "r") as f:
                requests = json.load(f)
        else:
            requests = []

        requests.append(request_entry)
        with open("access_requests.json", "w") as f:
            json.dump(requests, f, indent=4)

        flash("Request submitted. Await admin approval.")
        return redirect(url_for("request_access"))

    return render_template("request_access.html")

@app.route('/export_logs', methods=['POST'])
@login_required()
def export_logs():
    user = session['user']
    tenants = get_available_tenants(user)
    all_logs = []

    for tenant in tenants:
        logs = search_logs(tenant)
        for log in logs:
            all_logs.append([tenant, log['file'], log['line_num'], log['content']])

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Tenant', 'Log File', 'Line Number', 'Content'])  # CSV header
    cw.writerows(all_logs)

    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=logs_export.csv'}
    )



# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


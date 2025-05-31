from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import json, os
from flask import send_from_directory

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

@app.route("/")
@login_required("analyst")
def dashboard():
    selected = session.get("selected_tenant")
    if not selected:
        return redirect(url_for("select_tenant"))
    return render_template("index.html", tenant=selected)

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


# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///ideas.db")

DEPARTMENTS = [
    "Finance",
    "Sales",
    "Marketing",
    "Operations",
    "Engineering",
    "Product",
    "Customer Experience",
    "Legal",
    "HR",
    "Other"
]

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT id, hash FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["ID"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # ask the user for required info
        username = request.form.get("username")
        password = request.form.get("password")
        FirstName = request.form.get("firstname")
        LastName = request.form.get("lastname")
        email = request.form.get("email")
        department = request.form.get("department")
        confirmation = request.form.get("confirmation")
        password_hash = generate_password_hash(password)
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # error check
        if not username:
            return apology("Username Required", 400)
        if not FirstName:
            return apology("First Name Required", 400)
        if not LastName:
            return apology("Last Name Required", 400)
        if not email:
            return apology("Email Required", 400)
        if not department:
            return apology("Department Required", 400)
        if len(rows) == 1:
            return apology("Username already exists", 400)
        if not password:
            return apology("Password Required", 400)
        if len(password) < 8:
            return apology("Password must have at least 8 characters", 400)
        if not any(c.isdigit() for c in password):
            return apology("Password must contain numbers", 400)
        if not confirmation:
            return apology("Please re-enter password", 400)
        if not password == confirmation:
            return apology("Passwords do not match", 400)

        # if valid then update the user db
        db.execute("INSERT INTO users(username, hash, FirstName, LastName, email, department) VALUES(?, ?, ?, ?, ?, ?)",
        username, password_hash, FirstName, LastName, email, department)

        # automatically login the user after they have registered
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        print(rows)
        session["user_id"] = rows[0]["ID"]
        print(session["user_id"])
        return redirect("/")
    else:
        return render_template("register.html", departments=DEPARTMENTS)

@app.route("/")
@login_required
def index():
    id = session.get("user_id")
    ideas = db.execute("SELECT * FROM ideas ORDER BY title ASC")
    return render_template("index.html", ideas = ideas)

@app.route("/ideas", methods=["GET", "POST"])
@login_required
def ideas():
    if request.method == "POST":
        rows = db.execute("SELECT idea_id FROM ideas")
        title = request.form.get("title")
        row = db.execute("SELECT upvotes FROM ideas WHERE title = ?", title)
        votes = int(row[0]["upvotes"])
        upvotes = votes + 1
        db.execute("UPDATE ideas SET upvotes = ? WHERE title = ?", upvotes, title)
        if upvotes >= 10:
            db.execute("UPDATE ideas SET stage = ? WHERE title = ?", 'review', title)
        return redirect("/ideas")
    else:
        i = 0
        ideas = db.execute("SELECT * FROM ideas ORDER BY title ASC")
        length = len(ideas)
        return render_template("ideas.html", ideas = ideas, i = i, length = length)


@app.route("/vote")
@login_required
def vote():
    user_id = session.get("user_id")
    row = db.execute("SELECT upvotes FROM ideas WHERE title = ?", 'New Idea')
    votes = int(row[0]["upvotes"])
    upvotes = votes + 1
    db.execute("UPDATE ideas SET upvotes = ? WHERE title = ?", upvotes, 'New Idea')
    return redirect("/ideas")

@app.route("/downvote")
@login_required
def downvote():
    user_id = session.get("user_id")
    row = db.execute("SELECT downvotes FROM ideas WHERE title = ?", 'New Idea')
    votes = int(row[0]["downvotes"])
    downvotes = votes + 1
    db.execute("UPDATE ideas SET downvotes = ? WHERE title = ?", downvotes, 'New Idea')
    return redirect("/ideas")

@app.route("/history")
@login_required
def history():
    user_id = session.get("user_id")
    ideas = db.execute(
        "SELECT DISTINCT(ideas.title), ideas.time, actions.action FROM ideas JOIN actions ON ideas.idea_id = actions.idea_id WHERE ideas.user_id = ?",
         user_id)
    return render_template("history.html", ideas=ideas)

@app.route("/review")
@login_required
def review():
    ideas = db.execute("SELECT * FROM ideas WHERE stage = ? ORDER BY title ASC", 'review')
    return render_template("ideas.html", ideas = ideas)

@app.route("/reject")
@login_required
def rejected():
    ideas = db.execute("SELECT * FROM ideas WHERE stage = ? ORDER BY title ASC", 'reject')
    return render_template("ideas.html", ideas = ideas)

@app.route("/accept")
@login_required
def accept():
    ideas = db.execute("SELECT * FROM ideas WHERE stage = ? ORDER BY title ASC", 'accept')
    return render_template("ideas.html", ideas = ideas)

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        id = session.get("user_id")
        title = request.form.get("title")
        notes = request.form.get("notes")
        db.execute("INSERT INTO ideas (user_id, title, notes, stage) VALUES (?, ?, ?, ?)",
                   id, title, notes, "idea")
        row = db.execute("SELECT idea_id FROM ideas WHERE user_id = ? AND title = ?",
                   id, title)
        idea_id = row[0]["idea_id"]
        db.execute("INSERT INTO actions (idea_id, action, user_id) VALUES (?, ?, ?)",
                   idea_id, "submit", id)
        return render_template("submitted.html")
    else:
        return render_template("add.html")

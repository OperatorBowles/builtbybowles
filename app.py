import sqlite3
import myfitnesspal
from django.shortcuts import render
from datetime import datetime
from sqlite3 import Error
from flask import Flask, redirect, request, render_template, session
from flask_session import Session
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DATABASE = r'health.db'

def auth_mfp(email, password):
    client = myfitnesspal.Client(email, password)
    try:
        day = client.get_date(2021, 3, 1)
        return 1
    except:
        return 0

def create_connection(db_file):
    # Create a database connection to a SQLite database
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def get_user(email):
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    try:
        if cur.execute("SELECT EXISTS(SELECT name FROM users WHERE email=?)", (email,)).fetchone() == (1,):
            r = cur.execute("SELECT name FROM users WHERE email=?", (email,)).fetchone()
            return r[0]
    except:
        print("User does not exist. Please register first.")

def add_account(conn, new_acct_info):
    sql = '''INSERT INTO accounts(user_email, account, acct_email, acct_password) VALUES (?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, new_acct_info)
    conn.commit()

def get_progress(user_email):
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    try:
        if cur.execute("SELECT EXISTS(SELECT acct_email FROM accounts WHERE user_email=? AND account=?)", (user_email,"MyFitnessPal",)).fetchone() == (1,):
            r = cur.execute("SELECT acct_email, acct_password FROM accounts WHERE user_email=? AND account=?", (user_email,"MyFitnessPal",)).fetchone()
            client = myfitnesspal.Client(r[0], r[1])
            d = datetime.today()
            macros = client.get_date(d.year, d.month, d.day)
            return macros
    except:
        print("No MyFitnessPal account saved. Please link first.")

@app.route("/profile")
def profile():
    return render_template("pages-profile.html")

@app.route("/")
def index():
    if 'email' in session:
        con = sqlite3.connect("health.db")
        con.row_factory = sqlite3.Row
        
        cur = con.cursor()
        cur.execute("select * from workouts order by 'log_date' ASC")
        rows = cur.fetchall();

        sur = con.cursor()
        sur.execute("select name, sum(volume) as total_volume from workouts group by name order by total_volume DESC")
        sums = sur.fetchall();
        return render_template("dashboard-default.html", rows=rows, sums=sums)
    else:
        return render_template("index.html")

@app.route('/settings', methods=["POST", "GET"])
def settings():
    if request.method == "GET":
        return render_template("pages-settings.html")
    elif request.method == "POST":
        conn = create_connection(DATABASE)
        if request.form["submit_button"] == "mfp":
            auth_success = auth_mfp(request.form.get("inputEmailPal"), request.form.get("inputPasswordPal"))
            if auth_success == 1:
                new_acct_info = (session["email"], "MyFitnessPal", request.form.get("inputEmailPal"), request.form.get("inputPasswordPal"))
                add_account(conn, new_acct_info)
                return render_template("pages-settings.html")
            else:
                return redirect("pages-500.html")
        elif request.form["submit_button"] == "fitbod":
            new_acct_info = (session["email"], "Fitbod", request.form.get("inputEmailFit"), request.form.get("inputPasswordFit"))
            add_account(conn, new_acct_info)
        else:
            return "Not Working"

@app.route('/signout')
def signout():
    session["email"] = None
    return render_template("index.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["email"] = request.form.get("email")
        session["name"] = get_user(session["email"])
        macros = get_progress(session["email"])
        if macros == None:
            print("Nothing to show.")
        else:
            print(macros)
        return redirect("/")
    return render_template("pages-sign-in.html")

@app.route('/workouts', methods=["POST", "GET"])
def workouts():
    if request.method == "POST":
        #Establish connection to DB
        conn = create_connection(DATABASE)
        cur = conn.cursor()
        #Get workout information from form
        workout_name = request.form.get("name")
        workout_log_date = request.form.get("log_date")
        workout_duration = request.form.get("duration")
        workout_exercises = request.form.get("exercises")
        workout_volume = request.form.get("volume")
        workout_calories = request.form.get("calories")
        #Store in new variable
        new_workout = (session["email"], workout_name, workout_log_date, workout_duration, workout_exercises, workout_volume, workout_calories)
        #Write into SQL and commit
        sql = '''INSERT INTO workouts(user_email, name, log_date, duration, exercises, volume, calories) VALUES (?,?,?,?,?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, new_workout)
        conn.commit()
        return render_template("workouts.html")
    else:
        return render_template("workouts.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        
        sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        email text PRIMARY KEY,
                                        name text NOT NULL,
                                        password text NOT NULL
                                    );"""

        sql_create_tracking_table = """ CREATE TABLE IF NOT EXISTS tracking (
                                        id integer PRIMARY KEY,
                                        email text NOT NULL,
                                        entry_date text NOT NULL,
                                        weight float,
                                        carbs integer,
                                        protein integer,
                                        fats integer, 
                                        goal text,
                                        activity text
                                    );"""

        sql_create_current_goals_table = """ CREATE TABLE IF NOT EXISTS current_goals (
                                            email text PRIMARY KEY,
                                            goal text,
                                            activity text,
                                            calories integer,
                                            carbs integer,
                                            protein integer,
                                            fats integer
                                        );"""

        sql_create_accounts_table = """ CREATE TABLE IF NOT EXISTS accounts (
                                            user_email text NOT NULL,
                                            account text NOT NULL,
                                            acct_email text NOT NULL,
                                            acct_password text NOT NULL
                                        );"""

        sql_create_website_data_table = """ CREATE TABLE IF NOT EXISTS web_data (
                                                user_email text NOT NULL,
                                                last_refresh datetime NOT NULL
                                        );"""

        sql_create_workouts_table = """ CREATE TABLE IF NOT EXISTS workouts (
                                        w_id integer PRIMARY KEY,
                                        user_email text,
                                        name text,
                                        log_date date,
                                        duration integer,
                                        exercises integer,
                                        volume integer,
                                        calories integer
                                    ); """
        

        conn = create_connection(DATABASE)
        if conn is not None:
            # Create tables
            create_table(conn, sql_create_users_table)
            create_table(conn, sql_create_tracking_table)
            create_table(conn, sql_create_current_goals_table)
            create_table(conn, sql_create_accounts_table)
            conn.commit()
        else:
            print("Error! Cannot create the database connection.")

        if request.form.get("password") == request.form.get("confirm_password"):
            session["name"] = request.form.get("name")
            session["email"] = request.form.get("email")
            
            # Get variables from the form
            email = request.form.get("email")
            name = request.form.get("name")
            password = request.form.get("password")

            # Register the new user
            user = (email, name, password)
            conn = create_connection(DATABASE)
            register_user(conn, user)

            return redirect("/")
        else:
            return render_template("pages-sign-up.html")
    else:
        return render_template("pages-sign-up.html")

@app.route('/main')
def main():
    return render_template("index.html")
    
@app.route('/signin')
def signin():
    return render_template("pages-sign-in.html")

@app.route('/reset')
def reset():
    return render_template("pages-reset-password.html")

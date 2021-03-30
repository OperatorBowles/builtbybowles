import sqlite3
import myfitnesspal
from django.shortcuts import render
from datetime import datetime
from sqlite3 import Error
from flask import Flask, redirect, request, render_template, session, jsonify, json
from flask_session import Session

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DATABASE = r'health.db'

def create_connection(db_file):
    # Create a database connection to a SQLite database
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
        return d

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def register_user(conn, user):
    sql = '''INSERT INTO users(email, name, password) VALUES (?,?,?);'''
    cur = conn.cursor()
    cur.execute(sql, user)
    conn.commit()
    print("Successfully registered new user")

def new_workout(entry):
        
    #Get workout information from form
    workout_name = entry.get("name")
    workout_log_date = entry.get("log_date")
    workout_duration = entry.get("duration")
    workout_exercises = entry.get("exercises")
    workout_volume = entry.get("volume")
    workout_calories = entry.get("calories")
    
    #Store in new variable
    new_workout = (session["email"], workout_name, workout_log_date, workout_duration, workout_exercises, workout_volume, workout_calories)
    sql = '''INSERT INTO workouts(user_email, name, log_date, duration, exercises, volume, calories) VALUES (?,?,?,?,?,?,?) '''
    new_entry = (sql, new_workout)
    return new_entry

def new_weight(entry):

    #Get workout information from form
    weight_log_date = entry.get("log-date")
    weight_weight = entry.get("weight")
    
    #Store in new variable
    new_weight = (session["email"], weight_log_date, weight_weight)
    sql = '''INSERT INTO weight(user_email, log_date, weight) VALUES (?,?,?) '''
    new_entry = (sql, new_weight)
    return new_entry

def new_food(entry):

    #Get workout information from form
    log_date = entry.get("log-date")
    meal = entry.get('meal')
    calories = entry.get('calories')
    carbs = entry.get('carbs')
    protein = entry.get('protein')
    fats = entry.get('fats')
    entry = str(datetime.now())
    
    #Store in new variable
    new_food = (entry, session["email"], log_date, calories, carbs, protein, fats)
    sql = '''INSERT INTO tracking(entry, email, entry_date, calories, carbs, protein, fats) VALUES (?,?,?,?,?,?,?) '''
    new_entry = (sql, new_food)
    return new_entry

@app.route("/")
def index():
    if 'email' in session:
        
        con = sqlite3.connect("health.db")
        con.row_factory = sqlite3.Row

        try:    
            get_workouts = con.cursor()
            get_workouts.execute("select * from workouts order by 'log_date' ASC")
            workouts = get_workouts.fetchall();

            get_workouts_chart = con.cursor()
            get_workouts_chart.execute("select name, avg(volume) as average_volume from workouts group by name order by average_volume DESC")
            sums = get_workouts_chart.fetchall();
        except:
            print("No workouts logged yet")
            workouts = {
                'data': False,
            }
            sums = {
                'data': False,
            }

        try:
            get_weights = con.cursor()
            get_weights.execute("select * from weight order by 'log_date' ASC LIMIT 10")
            weights = get_weights.fetchall();
        except:
            print("No weight logged yet")
            weights = {0}
      
        try:
            get_macros = con.cursor()
            macros = get_macros.execute("select calories, carbs, protein, fats from tracking order by id DESC LIMIT 1;").fetchone()
            macros = {'calories': macros [0], 'carbs': macros[1], 'protein': macros[2], 'fats': macros[3]}
        except:
            print("No food entries logged yet")
            macros={0,0,0,0}
        
        try:
            get_goals = con.cursor()
            goals = get_goals.execute("select calories, carbs, protein, fats from goals order by id DESC LIMIT 1").fetchone()
            goals = {'calories': goals[0], 'carbs': goals[1], 'protein': goals[2], 'fats': goals[3]}
        except:
            print("No goals logged yet")
            goals={0,0,0,0}

        return render_template("dashboard-default.html", workouts=workouts, sums=sums, weights=weights, macros=macros, goals=goals)

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
        return redirect("/")
    return render_template("pages-sign-in.html")

@app.route('/tracking', methods=["POST", "GET"])
def tracking():
    if request.method == "POST":
        
        print(request.form)
        if 'workouts' in request.form:
            entry = new_workout(request.form)
        elif 'health' in request.form:
            entry = new_weight(request.form)
        else:
            entry = new_food(request.form)

        print(entry)
        #Establish connection to DB
        try:
            conn = create_connection(DATABASE)
            cur = conn.cursor()
            cur.execute(entry)
            conn.commit()
            print("Successfully logged")
            return redirect("/")
        except:
            print("Database error")
            return render_template("tracking.html")

    else:
        return render_template("tracking.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        
        sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        email text PRIMARY KEY,
                                        name text,
                                        password text
                                    );"""

        sql_create_tracking_table = """ CREATE TABLE IF NOT EXISTS tracking (
                                        id integer PRIMARY KEY,
                                        entry text,
                                        email text,
                                        entry_date date,
                                        calories integer,
                                        carbs integer,
                                        protein integer,
                                        fats integer 
                                    );"""

        sql_create_goals_table = """ CREATE TABLE IF NOT EXISTS goals (
                                        email text PRIMARY KEY,
                                        calories integer,
                                        carbs integer,
                                        protein integer,
                                        fats integer 
                                    );"""

        sql_create_accounts_table = """ CREATE TABLE IF NOT EXISTS accounts (
                                            id integer PRIMARY KEY,
                                            user_email text NOT NULL,
                                            account text NOT NULL,
                                            acct_email text NOT NULL,
                                            acct_password text NOT NULL
                                        );"""

        sql_create_workouts_table = """ CREATE TABLE IF NOT EXISTS workouts (
                                        id integer PRIMARY KEY,
                                        user_email text,
                                        name text,
                                        saved_workout text,
                                        log_date date,
                                        duration integer,
                                        exercises integer,
                                        volume integer,
                                        calories integer
                                    ); """
        
        sql_create_weight_table = """ CREATE TABLE IF NOT EXISTS weight (
                                        id integer primary key,
                                        user_email text,
                                        log_date date,
                                        weight real
                                    ); """

        conn = create_connection(DATABASE)
        if conn is not None:
            # Create tables
            create_table(conn, sql_create_users_table)
            create_table(conn, sql_create_accounts_table)
            create_table(conn, sql_create_goals_table)
            create_table(conn, sql_create_tracking_table)
            create_table(conn, sql_create_workouts_table)
            create_table(conn, sql_create_weight_table)
            conn.commit()
        else:
            print("Error! Cannot create the database connection.")

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

@app.route('/main')
def main():
    return render_template("index.html")
    
@app.route('/signin')
def signin():
    return render_template("pages-sign-in.html")


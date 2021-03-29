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

def register_user(conn, user):
    sql = '''INSERT INTO users(email, name, password) VALUES (?,?,?);'''
    cur = conn.cursor()
    cur.execute(sql, user)
    conn.commit()
    print("Successfully registered new user")

def get_progress(user_email):
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    try:
        if cur.execute("SELECT EXISTS(SELECT acct_email FROM accounts WHERE user_email=? AND account=?)", (user_email,"MyFitnessPal",)).fetchone() == (1,):
            r = cur.execute("SELECT acct_email, acct_password FROM accounts WHERE user_email=? AND account=?", (user_email,"MyFitnessPal",)).fetchone()
            client = myfitnesspal.Client(r[0], password=r[1])
            d = datetime.today()
            macros = client.get_date(d.year, d.month, d.day)

            #Store last time was run
            sql = ''' INSERT INTO web_data(user_email, last_refresh) VALUES (?,?) '''
            last_accessed = (session["email"], datetime.now())
            dur = conn.cursor()
            dur.execute(sql, last_accessed)
            conn.commit()
            return macros
        else:
            print("No account linked.")
    except:
        print("Error connecting to MFP.")

def get_weight():
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    r = cur.execute("SELECT acct_email, acct_password FROM accounts").fetchone()
    print(r[0], r[1])
    client = myfitnesspal.Client(r[0], password=r[1])
    try:
        weights = client.get_measurements('Weight')
        print("Successful connection")
    except:
        print("MFP did not connect")
    sql = ''' INSERT INTO weight(user_email, log_date, weight) VALUES (?,?,?) '''
    
    #Adding user email to list of weights from MFP
    new_weight = []
    for weight in weights:
        lst = list(weight)
        lst.insert(0, session["email"])
        new_weight += (tuple(lst),)
    #Add to DB
    cur.executemany(sql, new_weight)
    cur.close()

@app.route("/profile")
def profile():
    return render_template("pages-profile.html")

@app.route('/api/v1/workouts/all', methods=["GET", "POST"])
def api_all():
    conn = create_connection(DATABASE)
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_workouts = cur.execute('SELECT * FROM workouts;').fetchall()

    return jsonify(all_workouts)

@app.route('/api/v1/weight/all', methods=["GET", "POST"])
def api_weights_all():
    if request.method == "GET":
        conn = create_connection(DATABASE)
        conn.row_factory = dict_factory
        cur = conn.cursor()
        all_weights = cur.execute('SELECT * FROM weight;').fetchall()

        return jsonify(all_weights)
    else:
        conn = create_connection(DATABASE)
        cur = conn.cursor()
        #Get workout information from form
        new_weight = (session["email"], request.args.get('log_date'), request.args.get('weight'))
        #Write into SQL and commit
        sql = '''INSERT INTO weight(user_email, log_date, weight) VALUES (?,?,?)'''
        cur = conn.cursor()
        cur.execute(sql, new_weight)
        conn.commit()

        resp = jsonify(success=True)
        return resp

@app.route('/api/v1/workouts', methods=["GET"])
def api_filter():
    query_parameters = request.args
    
    id = query_parameters.get('id')
    logged = query_parameters.get('date')
    user = query_parameters.get('email')

    query = "SELECT * FROM workouts WHERE"
    to_filter = []

    if id:
        query += ' w_id=? AND'
        to_filter.append(id)
    if logged:
        query += ' log_date=? AND'
        to_filter.append(id)
    if user:
        query += ' user_email=? AND'
        to_filter.append(id)
    if not (id or logged or user):
        return page_not_found(404)

    query = query[:-4] + ';'

    conn = create_connection(DATABASE)
    conn.row_factory = dict_factory
    cur = conn.cursor()

    results = cur.execute(query, to_filter).fetchall()

    return jsonify(results)

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404

@app.route("/")
def index():
    if 'email' in session:
        try:
            con = sqlite3.connect("health.db")
            con.row_factory = sqlite3.Row
            
            get_workouts = con.cursor()
            get_workouts.execute("select * from workouts order by 'log_date' ASC")
            rows = get_workouts.fetchall();

            get_weights = con.cursor()
            get_weights.execute("select * from weight order by 'log_date' ASC LIMIT 10")
            weights = get_weights.fetchall();

            get_workouts_chart = con.cursor()
            get_workouts_chart.execute("select name, avg(volume) as average_volume from workouts group by name order by average_volume DESC")
            sums = get_workouts_chart.fetchall();

            get_macros = con.cursor()
            macros = get_macros.execute("select carbs, protein, fats from tracking order by id DESC LIMIT 1;").fetchone()
            macros = {'carbs': macros[0], 'protein': macros[1], 'fats': macros[2]}

            get_goals = con.cursor()
            goals = get_goals.execute("select carbs, protein, fats from goals order by id DESC LIMIT 1").fetchone()
            goals = {'carbs': goals[0], 'protein': goals[1], 'fats': goals[2]}

            return render_template("dashboard-default.html", rows=rows, sums=sums, weights=weights, macros=macros, goals=goals)
        except:
            macros = {0, 0, 0}
            goals = {0, 0, 0}
            return render_template("dashboard-default.html", rows=rows, sums=sums, weights=weights, macros=macros, goals=goals)
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
        get_progress(session["email"])
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
        return redirect("/")
    else:
        return render_template("new_workout.html")

@app.route('/weight', methods=["POST", "GET"])
def weight():
    if request.method == "POST":
        #Establish connection to DB
        conn = create_connection(DATABASE)
        cur = conn.cursor()
        #Get workout information from form
        weight_log_date = request.form.get("log-date")
        weight_weight = request.form.get("weight")
        #Store in new variable
        new_weight = (session["email"], weight_log_date, weight_weight)
        #Write into SQL and commit
        sql = '''INSERT INTO weight(user_email, log_date, weight) VALUES (?,?,?) '''
        cur.execute(sql, new_weight)
        conn.commit()
        return redirect("/")
    else:
        return render_template("new_weight.html")

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
                                        email text,
                                        entry_date datetime,
                                        carbs integer,
                                        protein integer,
                                        fats integer 
                                    );"""

        sql_create_goals_table = """ CREATE TABLE IF NOT EXISTS goals (
                                        id integer PRIMARY KEY,
                                        email text,
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

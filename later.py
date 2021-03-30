# Will come back to you later

def add_account(conn, new_acct_info):
    sql = '''INSERT INTO accounts(user_email, account, acct_email, acct_password) VALUES (?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, new_acct_info)
    conn.commit()

def auth_mfp(email, password):
    client = myfitnesspal.Client(email, password)
    try:
        day = client.get_date(2021, 3, 1)
        return 1
    except:
        return 0

def get_progress(user_email):
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    if cur.execute("SELECT EXISTS(SELECT acct_email FROM accounts WHERE user_email=? AND account=?)", (user_email,"MyFitnessPal",)).fetchone() == (1,):
        r = cur.execute("SELECT acct_email, acct_password FROM accounts WHERE user_email=? AND account=?", (user_email,"MyFitnessPal",)).fetchone()
        try:
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
        except:
            print("Error connecting to MFP.")
    else:
        print("No account linked.")
    
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
import myfitnesspal
import stdiomask

def signin():
    #conn = create_connection(DATABASE)
    #cur = conn.cursor()
    #r = cur.execute("SELECT acct_email, acct_password FROM accounts").fetchone()
    #print(r[0], r[1])
    try:
        client = myfitnesspal.Client('geoffreybowles3', password=stdiomask.getpass())
        return client
    except:
        print("Wrong password or username. Please try again.")

def get_meals():
    client = signin()

    day = client.get_date(2022, 1, 27)
    for i in range(4):
        meal = day.meals[i]
        entries = meal.entries
        print(entries)
    print(f"Total {day.totals}")
    
get_meals()
import myfitnesspal

def get_weight():
    #conn = create_connection(DATABASE)
    #cur = conn.cursor()
    #r = cur.execute("SELECT acct_email, acct_password FROM accounts").fetchone()
    #print(r[0], r[1])
    client = myfitnesspal.Client('geoffreybowles3', password='cfaRangers33po')
    try:
        weights = client.get_measurements('Weight')
        user_weights = {'entry':[], 'weight':[]}
        for key, value in weights.items():
            print(key, value)
            user_weights['entry'].append(key)
            user_weights['weight'].append(value)

        print(user_weights)
    except:
        print("MFP did not connect")
    
    
    #Adding user email to list of weights from MFP
    

get_weight()
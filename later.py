def new_food(entry):

    #Get food information from form
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
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    cur.execute(sql, new_food)
    conn.commit()
    print("Successfully logged new food")
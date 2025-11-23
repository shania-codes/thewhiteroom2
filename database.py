import sqlite3


def get_db():
    db = sqlite3.connect("data.db")
    return db


def init_db():
    db = get_db()
    cursor = db.cursor()

    # userdata table
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS userdata (
                    name TEXT NOT NULL,
                    weightGoal REAL,
                    currentWeight REAL,
                    calorieTarget INTEGER,
                    proteinTarget INTEGER,
                    carbsTarget INTEGER,
                    fatTarget INTEGER,
                    waterTarget INTEGER,
                    allergies TEXT,
                    dietaryPreferences TEXT
                    )""")
    # foodDiary table
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS foodDiary (
                    eatenID INTEGER PRIMARY KEY AUTOINCREMENT,
                    eatenName TEXT,
                    eatenCalories REAL,
                    eatenProtein REAL,
                    eatenCarbs REAL,
                    eatenFat REAL,
                    mealID INTEGER,
                    quantity REAL,
                    FOREIGN KEY (mealID) REFERENCES meals(mealID)
                    )""")
    # meals table
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS meals (
                    mealID INTEGER PRIMARY KEY AUTOINCREMENT,
                    mealDate TEXT NOT NULL,
                    mealName TEXT
                    )""")
    # water table
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS water (
                    waterDate TEXT PRIMARY KEY,
                    amountDrank INTEGER
                    )
                    """)
    # savedItems table
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS savedItems (
                    itemID INTEGER PRIMARY KEY AUTOINCREMENT,
                    itemName TEXT NOT NULL,
                    servingSize REAL,
                    servingUnit TEXT,
                    caloriesPerServing REAL,
                    proteinPerServing REAL,
                    carbsPerServing REAL,
                    fatPerServing REAL,
                    caloriesPer100g REAL,
                    proteinPer100g REAL,
                    carbsPer100g REAL,
                    fatPer100g REAL,
                    purchaseLocation TEXT,
                    pricePerServing REAL,
                    isTool INTEGER DEFAULT 0,
                    pricePerItem REAL,
                    servingsPerItem REAL
                    )""") 
    # tags table
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tags (
                    tagID INTEGER PRIMARY KEY AUTOINCREMENT,
                    tagName TEXT UNIQUE NOT NULL
                    )""")
    # itemTags table
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS itemTags (
                    itemID INTEGER,
                    tagID INTEGER,
                    FOREIGN KEY(itemID) REFERENCES savedItems(itemID) ON DELETE CASCADE,
                    FOREIGN KEY(tagID) REFERENCES tags(tagID) ON DELETE CASCADE,
                    PRIMARY KEY(itemID, tagID)
                    )""")
    # kitchenInventory table
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS kitchenInventory (
                    inventoryID INTEGER PRIMARY KEY AUTOINCREMENT,
                    itemID INTEGER NOT NULL,
                    useByDate TEXT,
                    purchaseDate TEXT,
                    servings REAL,
                    location TEXT,
                    FOREIGN KEY(itemID) REFERENCES savedItems(itemID)ON DELETE CASCADE
                    )""")
    # recipes table
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recipes (
                    recipeID INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipeName TEXT UNIQUE NOT NULL,
                    recipeDescription TEXT,
                    servingsMade INTEGER,
                    estimatedTime INTEGER
                    )""")
    # recipeItems table
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS recipeItems (
                    recipeID INTEGER,
                    itemID INTEGER,
                    quantity REAL DEFAULT 1,
                    FOREIGN KEY(recipeID) REFERENCES recipes(recipeID) ON DELETE CASCADE,
                    FOREIGN KEY(itemID) REFERENCES savedItems(itemID) ON DELETE CASCADE,
                    PRIMARY KEY(recipeID, itemID)
                    )""")
    # tasks
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        due_date TEXT,
        is_complete INTEGER NOT NULL DEFAULT 0,
        description TEXT)""")         
    ## reward_user(s)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reward_user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        balance INTEGER NOT NULL DEFAULT 0,
        coingoal INTEGER NOT NULL DEFAULT 0)""")
    ## rewards
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        cost INTEGER NOT NULL DEFAULT 0,
        count INTEGER NOT NULL DEFAULT 0,
        image TEXT)""") 
    ## redeemed rewards
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS redeemed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    # Create initial user if there isn't one for rewards page (no multi user implemented currently):
    cursor.execute("SELECT COUNT(*) FROM reward_user")
    user_count = cursor.fetchone()[0]
    if user_count == 0:
        cursor.execute("INSERT INTO reward_user (name, balance) VALUES (?, ?)", ("User", 0))

    # chore_users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chore_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL)""")
    # chores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        rrule TEXT)""")
    # assignments (which users must do which chores?)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
        user_id INTEGER,
        chore_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES chore_users(id),
        FOREIGN KEY(chore_id) REFERENCES chores(id))""")
    # steps
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        time INTEGER)""")
    # Chore steps
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chore_steps (
        chore_id INTEGER,
        step_id INTEGER,
        FOREIGN KEY(chore_id) REFERENCES chores(id),
        FOREIGN KEY(step_id) REFERENCES steps(id))""")  

    # Routes
    ## Nodes
    cursor.execute("CREATE TABLE IF NOT EXISTS nodes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, content TEXT, type TEXT, status TEXT DEFAULT 'not_started', estimated_time TEXT)")
    # id, name, content, type (root, text (with support for hyperlinks), task, habit, routine), status (notdone, in_progress, done), estimated_time, metadata (stores task habit or routine details to add the expected item to task management)

    ## Routes
    cursor.execute("CREATE TABLE IF NOT EXISTS routes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, root_node INTEGER, status TEXT DEFAULT 'not_started', FOREIGN KEY (root_node) REFERENCES nodes(id))")
    # id, name, description, root_node(FK node_id), status (notdone, in_progress, done) 

    ## Adjacency List
    cursor.execute("CREATE TABLE IF NOT EXISTS adjacency_list (id INTEGER PRIMARY KEY AUTOINCREMENT, parent INTEGER, child INTEGER, FOREIGN KEY (parent) REFERENCES nodes(id), FOREIGN KEY (child) REFERENCES nodes(id))")
    #id, parent (FK node id), child (FK node id)

    db.commit()
    db.close()
from flask import Flask, render_template, url_for, request, redirect, flash
import os
import sqlite3
from datetime import datetime, timedelta
from dateutil.rrule import rrulestr, rrule
from dateutil.parser import ParserError
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = "worst_admin"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # Make ./static/uploads if it doesn't exist

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# SQL
def get_db():
    db = sqlite3.connect("data.db")
    return db
def init_db(): # Make the database
    with app.app_context():
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
                       recipeInstructions TEXT,
                       servingsMade INTEGER,
                       estimatedTime INTEGER
                       )""")
        # recipeItems table
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS recipeItems (
                       recipeID INTEGER,
                       itemID INTEGER,
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







        db.commit()
        db.close()
init_db()


@app.route("/")
def index():  
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM userdata LIMIT 1")
    result = cursor.fetchone()
    db.close()
    # Check if name exists and is not empty
    if result and result[0].strip():
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("setup"))
    

@app.route("/setup", methods=["GET", "POST"])
def setup():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM userdata LIMIT 1")
    result = cursor.fetchone()

    if result:
        db.close()
        return redirect(url_for("dashboard")) # Redirect to dashboard if username exists

    if request.method == "POST":
        # Get inputs from form and save them to variables
        name = request.form.get("name").strip()
        weightGoal = request.form.get("weightGoal")
        currentWeight = request.form.get("currentWeight")
        calorieTarget = request.form.get("calorieTarget")
        proteinTarget = request.form.get("proteinTarget")
        carbsTarget = request.form.get("carbsTarget")
        fatTarget = request.form.get("fatTarget")
        waterTarget = request.form.get("waterTarget")
        allergies = request.form.get("allergies").strip()
        dietaryPreferences = request.form.get("dietaryPreferences").strip()

        if name != "":
            # Save the value to the userdata table
            cursor.execute("""
                INSERT INTO userdata (
                    name, weightGoal, currentWeight, calorieTarget,
                    proteinTarget, carbsTarget, fatTarget, waterTarget,
                    allergies, dietaryPreferences) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                (name, weightGoal, currentWeight, calorieTarget,proteinTarget, carbsTarget, fatTarget, waterTarget, allergies, dietaryPreferences))
            db.commit() # Save
            db.close()
            return redirect(url_for("dashboard"))
        else:
            flash("Please input a username")
            return redirect(url_for("setup"))

    return render_template("setup.html")


@app.route("/dashboard")
def dashboard():
    # Get name from the database
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name FROM userdata")
    result = cursor.fetchone()
    if result:
        name = result[0]
        return render_template("dashboard.html", name=name)
    
    else:
        return redirect(url_for("setup"))


@app.route("/food/diary", methods=["GET", "POST"])
def fooddiary():
    if request.args.get("date"): # /food/diary?date=12345678
        # print(request.args.get("date")) = 12345678
        today = request.args.get("date") # Not actually todays date it's which day they selected in the date input
    else: # Actually todays date
        today = datetime.today().strftime("%d%m%Y") # DDMMYYYY

    print(request.full_path); # prints /food/diary?date=12345678
    if not os.path.exists("./data.db"):
        return redirect(url_for("setup"))
    # Check if meals with todays date exists
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT mealID FROM meals WHERE mealDate = ?", (today,))
    meal = cursor.fetchone() # Get one meal if it exists
    
    
    # Initialise "Other" meal and Water counter
    if not meal: # If there are no meals for today
        # Make meals for todat
        cursor.execute("INSERT INTO meals (mealDate, mealName) VALUES (?, ?)", (today, "Breakfast"))
        cursor.execute("INSERT INTO meals (mealDate, mealName) VALUES (?, ?)", (today, "Lunch"))
        cursor.execute("INSERT INTO meals (mealDate, mealName) VALUES (?, ?)", (today, "Dinner"))
        cursor.execute("INSERT INTO meals (mealDate, mealName) VALUES (?, ?)", (today, "Other"))
        db.commit()

    # Check if waterDate with today's date exists, if not make it
    cursor.execute("SELECT * FROM water WHERE waterDate = ?", (today, ))
    water = cursor.fetchone()
    if not water:
        cursor.execute("INSERT INTO water (waterDate, amountDrank) VALUES (?, ?)", (today, 0))
        db.commit()


    # Get all of today's added meals, and make a list of their IDs, and names
    cursor.execute("SELECT * FROM meals WHERE mealDate = ?", (today,))
    todaysMeals = cursor.fetchall()

    # Get every food item eaten today 
    allEatenFoods = [] # Initialise list
    for meal in todaysMeals:
        mealID = meal[0]

        # Get all records in mealEntries where mealID = the meals where mealDate = today
        cursor.execute("SELECT * FROM foodDiary WHERE mealID = ?", (mealID,))
        entries = cursor.fetchall()
        allEatenFoods.extend(entries)


    # Get targets from userdata table
    cursor.execute("SELECT calorieTarget, proteinTarget, carbsTarget, fatTarget, waterTarget FROM userdata LIMIT 1")
    targets = cursor.fetchone() # no target = '' ex: (1, '', 3, 4, 5) if no protein target and rest as 1345

    # Get water current from water table (amountDrank WHERE waterDATE = DDMMYYYY)
    cursor.execute("SELECT * FROM water WHERE waterDate = ?", (today, ))
    water = cursor.fetchall() # water example: [('02082025', 0)] amountDrank = water[0][1]


    # kitchenInventory :
    cursor.execute("""
    SELECT ki.inventoryID, ki.itemID, si.itemName, ki.servings, ki.useByDate,
           si.caloriesPerServing, si.proteinPerServing, si.carbsPerServing, si.fatPerServing, ki.location
    FROM kitchenInventory ki
    JOIN savedItems si ON ki.itemID = si.itemID
    WHERE ki.servings > 0
    """)
    inventoryData = cursor.fetchall() 
    # 0 inventoryID, 1 itemId, 2 itemName, 3 servings, 4 useByDate, 
    # 5 caloriesPerServing, 6 ProteinPerServing, 7 carbsPerServing, 8 fatPerServing
    # 9 location where it's stored
    
    # Calculate and store current for calories and macros
    totals = [0,0,0,0]
    for eatenFood in allEatenFoods:
        totals[0] += eatenFood[2]*eatenFood[7]
        totals[1] += eatenFood[3]*eatenFood[7]
        totals[2] += eatenFood[4]*eatenFood[7]
        totals[3] += eatenFood[5]*eatenFood[7]


    # if request method POST
    if request.method == "POST":
        # Add from inventory form
        print(request.form)
        if "quantity" in request.form and "inventoryID" in request.form and "itemID" in request.form:
            quantity = float(request.form.get("quantity"))
            if quantity:
                inventoryID = request.form.get("inventoryID")
                itemID = request.form.get("itemID")
                # Decrement quantity in inventory, if to 0 remove it from inventory
                ## Get number of servings in stock
                cursor.execute("SELECT servings FROM kitchenInventory WHERE inventoryID = ?", (inventoryID))
                servings = (cursor.fetchall()[0][0])
                ## Input has a max value so it is unnecessary to check if servings>servings in stock
                ## Update servings to be servings - quantity used
                servingsLeft = servings-quantity
                # Remove item from inventory since it is now OOS
                if servingsLeft == 0:
                    cursor.execute("DELETE FROM kitchenInventory WHERE inventoryID = ?", (inventoryID))
                    db.commit()
                # Update servings left to new value
                else:
                    cursor.execute("UPDATE kitchenInventory SET servings = ? WHERE inventoryID = ?", (servingsLeft, inventoryID))
                    db.commit()
                    
                
                # Update food diary to add the quantity to todays diary
                cursor.execute("SELECT caloriesPerServing, proteinPerServing, carbsPerServing, fatPerServing, itemName FROM savedItems WHERE itemID = ?", (itemID, ))
                temp = cursor.fetchone()

                calories = temp[0] or 0
                protein = temp[1] or 0
                carbs = temp[2] or 0
                fat = temp[3] or 0
                itemName = temp [4]
                mealID = request.form.get("mealID")

                cursor.execute("INSERT INTO foodDiary (eatenName, eatenCalories, eatenProtein, eatenCarbs, eatenFat, mealID, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)", (itemName, calories, protein, carbs, fat, mealID, quantity))
                db.commit()

                return redirect(url_for('fooddiary')) # refresh page to update value

        # Add Meal form
        if "mealName" in request.form: 
            mealName = (request.form["mealName"]) # Store user input the new meal's name
            if mealName: # As long as meal name isn't empty save it as a new meal
                cursor.execute("INSERT INTO meals (mealDate, mealName) VALUES (?, ?)", (today, mealName))
                db.commit()

            return redirect(url_for("fooddiary")) # Refresh page
        
        # Add Eaten Food form
        if "mealID" in request.form:
            mealID = request.form["mealID"]
            eatenName = request.form.get("eatenName")
            eatenQuantity = request.form.get("eatenQuantity") or 1
            
            eatenCalories = request.form.get("eatenCalories") or 0
            eatenProtein = request.form.get("eatenProtein") or 0
            eatenCarbs = request.form.get("eatenCarbs") or 0
            eatenFat = request.form.get("eatenFat") or 0

            # Make eatenName if left empty
            if not eatenName:
                if eatenCalories:
                    eatenName = str(eatenCalories)+" calories food"
                elif eatenProtein:
                    eatenName = str(eatenProtein)+"g protein food"
                elif eatenCarbs:
                    eatenName = str(eatenCarbs)+"g carbs food"
                elif eatenFat:
                    eatenName = str(eatenFat)+"g fat food"
                else:
                    eatenName = "unnamed food with unknown nutrition"

            # Save to foodDiary table
            cursor.execute("INSERT INTO foodDiary (eatenName, eatenCalories, eatenProtein, eatenCarbs, eatenFat, mealID, quantity) VALUES (?, ?, ?, ?, ?, ?, ?)", (eatenName, eatenCalories, eatenProtein, eatenCarbs, eatenFat, mealID, eatenQuantity))

            #eatenID = cursor.lastrowid
            db.commit()

            return redirect(url_for("fooddiary")) # I'm fresh like F5 (refresh the page to show updated info)

        # Water add and subtract
        if "action" in request.form: 
            action = request.form.get("action") # "add" or "subtract"
            waterAmount = request.form.get("waterAmount") or 0
            if action == "add":
                cursor.execute("SELECT * FROM water WHERE waterDate = ?", (today, ))
                water = cursor.fetchone() #water[0] = DDMMYYYY date
                #currentWater = water[1]
                newWater = water[1] + int(waterAmount)
                cursor.execute("UPDATE water SET amountDrank = ? WHERE waterDate = ?", (newWater, today))
                db.commit()
                return redirect(url_for("fooddiary"))
            elif action == "subtract":
                cursor.execute("SELECT * FROM water WHERE waterDate = ?", (today, ))
                water = cursor.fetchone() #water[0] = DDMMYYYY date
                newWater = max(0, water[1] - int(waterAmount)) # Whichever is higher 0 or old water - subtracted amount
                cursor.execute("UPDATE water SET amountDrank = ? WHERE waterDate = ?", (newWater, today))
                db.commit()
                return redirect(url_for("fooddiary"))
        
        # Delete eaten food form
        if "deleteFoodID" in request.form: 
            foodID = request.form["deleteFoodID"]
            cursor.execute("DELETE FROM foodDiary WHERE eatenID = ?", (foodID, ))
            db.commit()
            return redirect(url_for("fooddiary"))
        
        # Edit eaten food form
        if "editFoodID" in request.form:
            foodID = request.form["editFoodID"]
            eatenName = request.form.get("eatenName")
            eatenCalories = request.form.get("eatenCalories") or 0
            eatenProtein = request.form.get("eatenProtein") or 0
            eatenCarbs = request.form.get("eatenCarbs") or 0
            eatenFat = request.form.get("eatenFat") or 0
            quantity = request.form.get("quantity") or 0

            # If no eaten name make one with the provided information
            if not eatenName:
                if eatenCalories:
                    eatenName = str(eatenCalories)+" calories food"
                elif eatenProtein:
                    eatenName = str(eatenProtein)+"g protein food"
                elif eatenCarbs:
                    eatenName = str(eatenCarbs)+"g carbs food"
                elif eatenFat:
                    eatenName = str(eatenFat)+"g fat food"
                else: # there is no point in this except marking that you did eat something?
                    eatenName = "unnamed food with unknown nutrition"

            cursor.execute("UPDATE foodDiary SET eatenName = ?, eatenCalories = ?, eatenProtein = ?, eatenCarbs = ?, eatenFat = ?, quantity = ? WHERE eatenID = ?", (eatenName, eatenCalories, eatenProtein, eatenCarbs, eatenFat, quantity, foodID))
            db.commit()
            return redirect(url_for("fooddiary"))
        
        # Delete a meal form 
        if "deleteMealID" in request.form:
            mealID = request.form["deleteMealID"]

            cursor.execute("SELECT * FROM meals WHERE mealDate = ?", (today, ))
            todaysMeals = (cursor.fetchall()) # All of today's meals
            if (len(todaysMeals)) > 1:
                cursor.execute("DELETE FROM foodDiary WHERE mealID = ?", (mealID,)) # Delete all food diary entries that were in that meal
                cursor.execute("DELETE FROM meals WHERE mealID = ?", (mealID, )) # Delete the meal 
                db.commit()
            
            return redirect(url_for("fooddiary"))
        
        # Edit meal form (change it's name)
        if "editMealID" in request.form:
            mealID = request.form["editMealID"]
            newName = request.form.get("newMealName")
            if newName:
                cursor.execute("UPDATE meals SET mealName = ? WHERE mealID = ?", (newName, mealID))
                db.commit()
            return redirect(url_for("fooddiary"))

    return render_template("fooddiary.html", inventoryData=inventoryData ,current=totals, waterDrank=water[0][1], targets=targets, todaysMeals=todaysMeals, allEatenFoods=allEatenFoods)


@app.route("/food/inventory", methods=["GET", "POST"])
def inventory():
    db = get_db()
    cursor = db.cursor()
    # Get kitchenInventory table (all items that exist in user's real kitchen/house)
    cursor.execute("SELECT * FROM kitchenInventory WHERE servings > 1;")
    kitchenInventory=cursor.fetchall()

    
    # Get savedItems table (all saved products that the user plans on rebuying)
    cursor.execute("SELECT * FROM savedItems")
    savedItems=cursor.fetchall()

    # get all items that are are in inventory, get ingredients first and then tools
    cursor.execute("""
    SELECT 
    kitchenInventory.inventoryID,
    savedItems.itemName,
    kitchenInventory.servings,
    kitchenInventory.useByDate,
    savedItems.isTool,
    kitchenInventory.location
    FROM kitchenInventory
    JOIN savedItems ON savedItems.itemID = kitchenInventory.itemID
    ORDER BY savedItems.isTool ASC, kitchenInventory.useByDate ASC
    """)
    currentInventory = cursor.fetchall()


    # get all locations
    cursor.execute("SELECT DISTINCT location FROM kitchenInventory")
    allLocations = [row[0] for row in cursor.fetchall()]

    # get all items that have templates but have NULL or 0 servings
    cursor.execute("""
        SELECT 
            s.itemID, 
            s.itemName, 
            s.purchaseLocation,
            s.pricePerItem,
            s.servingsPerItem,
            s.pricePerServing
        FROM savedItems s
        LEFT JOIN (
            SELECT itemID, SUM(servings) as totalServings
            FROM kitchenInventory
            GROUP BY itemID
        ) ki ON s.itemID = ki.itemID
        LEFT JOIN (
            SELECT itemID, location
            FROM kitchenInventory
            WHERE inventoryID IN (
                SELECT MAX(inventoryID)
                FROM kitchenInventory
                GROUP BY itemID
            )
        ) latest ON s.itemID = latest.itemID
        WHERE ki.totalServings IS NULL OR ki.totalServings = 0
        ORDER BY s.itemName ASC
        """)
    missingItems = cursor.fetchall() # [(2, 'Frying Pan', "Sainsbury's", None, None),(id, name, store, pricePerItem, servingsPerItem, pricePerServing)]


    if request.method == "POST":
        # Add new product template to savedItems table
        if "newItemName" in request.form and not "editItemID" in request.form:
            itemName = request.form.get("newItemName") # Check whether adding two items of the same name breaks anything
            servingSize = request.form.get("servingSizeNew") or 0
            servingUnit = request.form.get("servingUnitNew")
            caloriesPerServing = request.form.get("caloriesPerServingNew") or 0
            proteinPerServing = request.form.get("proteinPerServingNew") or 0
            carbsPerServing = request.form.get("carbsPerServingNew") or 0
            fatPerServing = request.form.get("fatPerServingNew") or 0
            caloriesPer100g = request.form.get("caloriesPer100gNew") or 0
            proteinPer100g = request.form.get("proteinPer100gNew") or 0
            carbsPer100g = request.form.get("carbsPer100gNew") or 0
            fatPer100g = request.form.get("fatPer100gNew") or 0
            purchaseLocation = request.form.get("purchaseLocationNew")
            pricePerItem = float(request.form.get("pricePerItemNew") or 0)
            servingsPerItem = float(request.form.get("servingsPerItemNew") or 1)
            
            # Calculate pricePerServing
            if pricePerItem and servingsPerItem:
                pricePerServing = round(pricePerItem/servingsPerItem, 2)
                print(pricePerServing)

            else:
                pricePerServing = 0

            isTool = 1 if request.form.get("isTool") == "1" else 0

            cursor.execute("INSERT INTO savedItems (itemName, servingSize, servingUnit, caloriesPerServing, proteinPerServing, carbsPerServing, fatPerServing, caloriesPer100g, proteinPer100g, carbsPer100g, fatPer100g, purchaseLocation, pricePerServing, isTool, pricePerItem, servingsPerItem) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(itemName, servingSize, servingUnit, caloriesPerServing, proteinPerServing, carbsPerServing, fatPerServing, caloriesPer100g, proteinPer100g, carbsPer100g, fatPer100g, purchaseLocation, pricePerServing, isTool, pricePerItem, servingsPerItem))
            db.commit()
            return redirect(url_for("inventory"))
        
        # Add instance of an item template to kitchen inventory
        if "itemID" in request.form:
            itemID = request.form.get("itemID")
            purchaseDate = request.form.get("purchaseDate")
            useByDate = request.form.get("useByDate")
            servings = request.form.get("servings")
            location = request.form.get("location")

            cursor.execute("INSERT INTO kitchenInventory (itemID, purchaseDate, useByDate, servings, location) VALUES (?, ?, ?, ?, ?)", (itemID, purchaseDate, useByDate, servings, location))
            db.commit()
            return redirect(url_for("inventory"))
        
        # Edit item template form
        if "editItemID" in request.form:
            editItemID = request.form.get("editItemID")
            itemName = request.form.get("newItemName")
            servingSize = request.form.get("servingSize") or 0
            servingUnit = request.form.get("servingUnit")
            caloriesPerServing = request.form.get("caloriesPerServing") or 0
            proteinPerServing = request.form.get("proteinPerServing") or 0
            carbsPerServing = request.form.get("carbsPerServing") or 0
            fatPerServing = request.form.get("fatPerServing") or 0
            caloriesPer100g = request.form.get("caloriesPer100g") or 0
            proteinPer100g = request.form.get("proteinPer100g") or 0
            carbsPer100g = request.form.get("carbsPer100g") or 0
            fatPer100g = request.form.get("fatPer100g") or 0
            purchaseLocation = request.form.get("purchaseLocation")
            pricePerItem = float(request.form.get("pricePerItem") or 0)
            servingsPerItem = float(request.form.get("servingsPerItem") or 0)
            
            # Calculate pricePerServing
            if pricePerItem and servingsPerItem:
                pricePerServing = round(pricePerItem/servingsPerItem, 2)
                print(pricePerServing)

            else:
                pricePerServing = 0

            isTool = 1 if request.form.get("isTool") == "1" else 0

            cursor.execute("""
            UPDATE savedItems
            SET itemName = ?, servingSize = ?, servingUnit = ?, caloriesPerServing = ?, proteinPerServing = ?, carbsPerServing = ?, fatPerServing = ?, caloriesPer100g = ?, proteinPer100g = ?, carbsPer100g = ?, fatPer100g = ?, purchaseLocation = ?, pricePerServing = ?, isTool = ?, pricePerItem = ?, servingsPerItem = ?
            WHERE itemID = ?""", 
            (itemName, servingSize, servingUnit, caloriesPerServing, proteinPerServing, carbsPerServing, fatPerServing, caloriesPer100g, proteinPer100g, carbsPer100g, fatPer100g, purchaseLocation, pricePerServing, isTool, pricePerItem, servingsPerItem, editItemID))
            db.commit()
            return redirect(url_for("inventory"))

        # Delete item template form
        if "deleteItemTemplate" in request.form:
            deleteItemID = request.form.get("deleteItemTemplate")
            cursor.execute("DELETE FROM savedItems WHERE itemID = ?", (deleteItemID, ))
            
            # Also delete from kitchenInventory
            cursor.execute("DELETE FROM kitchenInventory WHERE itemID = ?", (deleteItemID,))
            
            db.commit()
            return redirect(url_for("inventory"))

        # Edit item in inventory
        if "editInventoryItemID" in request.form:
            inventoryID = request.form.get("editInventoryItemID")
            editServings = request.form.get("editServings")
            editUseByDate = request.form.get("editUseByDate")
            editLocation = request.form.get("editLocation")

            cursor.execute("UPDATE kitchenInventory SET servings = ?, useByDate = ?, location = ? WHERE inventoryID = ?",
                           (editServings, editUseByDate, editLocation, inventoryID))
            db.commit()
            return redirect(url_for("inventory"))

        # Delete item from inventory
        if "deleteInventoryItemID" in request.form:
            inventoryID = request.form.get("deleteInventoryItemID")
            cursor.execute("DELETE FROM kitchenInventory WHERE inventoryID = ?", (inventoryID, ))
            db.commit()
            return redirect(url_for("inventory"))


    return render_template("inventory.html", missingItems = missingItems, allLocations = allLocations, savedItems=savedItems, kitchenInventory=kitchenInventory, currentInventory=currentInventory, now=datetime.now) 


@app.route("/settings", methods=["GET", "POST"])
def settings():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST": #When submit button is pressed
        # Get inputs from form and save them to variables
        name = request.form.get("name") 
        weightGoal = request.form.get("weightGoal")
        currentWeight = request.form.get("currentWeight")
        calorieTarget = request.form.get("calorieTarget")
        proteinTarget = request.form.get("proteinTarget")
        carbsTarget = request.form.get("carbsTarget")
        fatTarget = request.form.get("fatTarget")
        waterTarget = request.form.get("waterTarget")
        allergies = request.form.get("allergies")
        dietaryPreferences = request.form.get("dietaryPreferences")

        cursor.execute("""
            UPDATE userdata SET
                name = ?,
                weightGoal = ?,
                currentWeight = ?,
                calorieTarget = ?,
                proteinTarget = ?,
                carbsTarget = ?,
                fatTarget = ?,
                waterTarget = ?,
                allergies = ?,
                dietaryPreferences = ?""", 
                (name, weightGoal, currentWeight, calorieTarget, proteinTarget, carbsTarget, fatTarget, waterTarget, allergies, dietaryPreferences))
        db.commit()

    cursor.execute("SELECT * FROM userdata")
    userdata = cursor.fetchone()
    return render_template("settings.html", userdata=userdata)


@app.route("/food/recipes")
def recipes():
    if request.method == "POST":
    # Add new recipe form
        if newRecipeName in request.form:
            print("test")
            
    return render_template("recipes.html", recipes=getRecipesTable())


# Add Linear progression routines and other routines too 
# /weightlifting


@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if request.method == "POST":
        # Add task (name, due date, description)
        if "new_task_name" in request.form:
            new_task_name = request.form["new_task_name"]
            description = request.form["description"]
            
            # SQL to add the new task to DB
            db = get_db()
            cursor = db.cursor()

            if request.form["due_date"]:
                due_date = request.form["due_date"] # yyyy-mm-dd
                cursor.execute("INSERT INTO tasks (name, due_date, description) VALUES (?, ?, ?)", (new_task_name, due_date, description,))
            else:
                cursor.execute("INSERT INTO tasks (name, description) VALUES (?, ?)", (new_task_name, description,))
            flash("Task added")
            db.commit()
            db.close()
        
        # Delete task
        if "delete_task_id" in request.form:
            delete_task_id = request.form["delete_task_id"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (delete_task_id,))
            flash("Task deleted")
            db.commit()
            db.close()

        # Mark task as (in)complete
        if "completed_task_id" in request.form:
            completed_task_id = request.form["completed_task_id"]
            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE tasks SET is_complete = 1 - is_complete WHERE id = ?", (completed_task_id,)) 
            db.commit()
            db.close()

        # Edit task
        if "edited_task_id" in request.form:
            task_id = request.form["edited_task_id"]
            new_name = request.form["edited_name"]
            new_due_date = request.form["edited_due_date"] or None
            new_description = request.form["edited_description"] or None

            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE tasks SET name = ?, due_date = ?, description = ? WHERE id = ?", (new_name, new_due_date, new_description, task_id))
            flash("Task updated")
            db.commit()
            db.close()


    return render_template("tasks.html", all_tasks=get_all_tasks())


@app.route("/rewards", methods=["GET", "POST"])
def rewards():
    if request.method == "POST":
        print(request.form)
        # Add reward (name, description, coins)
        if "new_reward_name" in request.form:
            new_reward_name = request.form["new_reward_name"]
            description = request.form["description"]
            cost = request.form["coins"]

            db = get_db()
            cursor = db.cursor()
            
            file = request.files["image"]
            if file.filename == "": # if no file is uploaded
                filename = None 
            elif file and allowed_file(file.filename): # If the file exists and it has an allowed name and file extension then save it
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # TODO replace file name with hash of the file to support images that are the same not being duplicated and images of the same name but are different not overwriting each other

            cursor.execute("INSERT INTO rewards (name, description, cost, image) VALUES (?, ?, ?, ?)", (new_reward_name, description, cost, filename))
            
            
            flash("Reward added")
            db.commit()
            db.close()

        # Edit reward
        if "edited_reward" in request.form:
            edited = request.form["edited_reward"]
            new_reward_name = request.form["reward_name"]
            new_description = request.form["description"]
            new_cost = request.form["coins"]
            
            db = get_db()
            cursor = db.cursor()


            file = request.files["image"]
            if file.filename == "": # if no new file is uploaded
                cursor.execute("UPDATE rewards SET name = ?, description = ?, cost = ? WHERE id = ?", (new_reward_name, new_description, new_cost, edited))
            elif file and allowed_file(file.filename): # If a new file is uploaded
                # delete old file
                cursor.execute("SELECT image FROM rewards WHERE id = ?", (edited,))
                old_file = cursor.fetchone()[0]
                if old_file:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_file)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                

                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) # upload new file
                cursor.execute("UPDATE rewards SET name = ?, description = ?, cost = ?, image = ? WHERE id = ?", (new_reward_name, new_description, new_cost, filename, edited)) # Update DB with new file


            flash("Reward updated")
            db.commit()
            db.close()
        
        # Delete reward
        if "delete_reward" in request.form:
            delete = request.form["reward_id"]

            db = get_db()
            cursor = db.cursor()

            # delete old file
            cursor.execute("SELECT image FROM rewards WHERE id = ?", (delete,))
            old_file = cursor.fetchone()[0]
            if old_file:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_file)
                if os.path.exists(old_path):
                    os.remove(old_path)

            cursor.execute("DELETE FROM rewards WHERE id = ?", (delete,))

            flash("Reward deleted")
            db.commit()
            db.close()

        # Add coins
        if request.form.get("action") == "add":
            coins = request.form["coins"]
            reason = request.form.get("reason") or "No reason given"

            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE reward_user SET balance = balance + ?", (coins,))
            log = coins + " coins added - " + reason
            cursor.execute("INSERT INTO redeemed (log) VALUES (?)", (log,))
            db.commit()
            db.close()
            flash("Added coins")

        # Subtract coins
        if request.form.get("action") == "subtract":
            coins = int(request.form["coins"])
            reason = request.form.get("reason") or "No reason given"
            balance = int(get_coin_balance())

            db = get_db()
            cursor = db.cursor()

            if balance >= coins: # in this case balance - coins can't be negative only 0 or more
                cursor.execute("UPDATE reward_user SET balance = balance - ? WHERE id = 1", (coins,))
                
                log = f"{coins} coins removed - {reason}"
                cursor.execute("INSERT INTO redeemed (log) VALUES (?)", (log,))
                
                db.commit()
                db.close()
                flash("Subtracted coins") 
            else:
                flash("Not enough coins in balance")

        # Redeem reward
        if "redeemed_id" in request.form:
            reward_id = request.form["redeemed_id"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT cost, name FROM rewards WHERE id = ?", (reward_id,))
            cost_name = cursor.fetchone() # Reward cost, reward name
            cursor.execute("SELECT balance FROM reward_user")
            balance = cursor.fetchone()[0] # User coin balance

            if balance >= cost_name[0]:
                # Deduct coins
                cursor.execute("UPDATE reward_user SET balance = balance - ? WHERE id = 1", (cost_name[0],))
                # Log redemption
                log = str(cost_name[0]) + " coins spent - " + cost_name[1]
                cursor.execute("INSERT INTO redeemed (log) VALUES (?)", (log,))
                cursor.execute("UPDATE rewards SET count = count + 1 WHERE id = 1")
                db.commit()
                flash("Reward redeemed!")
            else:
                flash("Not enough coins to redeem this reward.")

            db.close()

        # Delete redeem log entry
        if "entry_id" in request.form:
            entry_id = request.form["entry_id"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM redeemed WHERE id = ?", (entry_id,))
            db.commit()
            db.close()
            flash("Deleted redeem log entry")

        # Redeem log clear
        if "redeem" in request.form:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM redeemed")
            db.commit()
            db.close()
            flash("Redemption log cleared")

        # Set coin goal
        if "coin_goal" in request.form:
            goal = request.form["coin_goal"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE reward_user SET coingoal = ?", (goal,))
            db.commit()
            db.close()
            flash("Coin goal updated")


    return render_template("rewards.html", coin_balance=get_coin_balance(), rewards=get_all_rewards(), log=get_redemption_log(), coin_goal=get_coin_goal())


@app.route("/timers")
def timers(): # TODO rewrite it but works better
    return render_template("timers.html")


@app.route("/chores", methods=["GET", "POST"])
def chores():
    if request.method == "POST":
        if "add_new_user" in request.form and request.form["new_username"] != "":
            new_username = request.form["new_username"]

            # TODO: refactor this pattern is repeated in many places in code, also in TWR 
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO chore_users (name) VALUES (?)", (new_username,))
            db.commit()
            db.close()

        if "delete_user" in request.form:
            delete = request.form["delete_user"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM chore_users WHERE id = ?", (delete,))
            db.commit()
            db.close()            

        if "add_chore" in request.form:
            name = request.form["chore_name"] # Required
            description = request.form.get("chore_desc") # Optional
            rrule = request.form.get("chore_rrule")

            # Check rrule validity TODO: Refactor, used in two places
            try:
                if rrule:
                    rrulestr(rrule)
            except Exception as e:
                return f"<p>Invalid rrule: {e}</p>"

            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO chores (name, description, rrule) VALUES (?, ?, ?)",(name, description, rrule))
            db.commit()
            db.close()

        if "edit_chore" in request.form:
            chore_id = request.form["chore_id"]
            name = request.form["chore_name"]
            desc = request.form["chore_desc"]
            rrule_str = request.form.get("chore_rrule", None)

            # Check rrule validity TODO: Refactor, used in two places
            try:
                if rrule_str:
                    rrulestr(rrule_str)
            except Exception as e:
                return f"<p>Invalid RRULE: {e}</p>"

            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE chores SET name = ?, description = ? WHERE id = ?",(name, desc, chore_id))
            db.commit()
            db.close()

        if "add_step" in request.form:
            name = request.form["step_name"]
            desc = request.form.get("step_desc")
            time = request.form.get("step_time")
            chore_id = request.form["chore_id"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO steps (name, description, time) VALUES (?, ?, ?)",(name, desc, time))
            step_id = cursor.lastrowid
            cursor.execute("INSERT INTO chore_steps (chore_id, step_id) VALUES (?, ?)", (chore_id, step_id))
            db.commit()
            db.close()

        if "edit_step" in request.form:
            step_id = request.form["step_id"]
            name = request.form["step_name"]
            desc = request.form["step_desc"]
            time = request.form.get("step_time")

            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE steps SET name = ?, description = ?, time = ? WHERE id = ?",(name, desc, time, step_id))
            db.commit()
            db.close()

        if "delete_step" in request.form:
            step_id = request.form["delete_step"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM chore_steps WHERE step_id = ?", (step_id,))
            cursor.execute("DELETE FROM steps WHERE id = ?", (step_id,))
            db.commit()
            db.close()

        if "delete_chore" in request.form:
            chore_id = request.form["delete_chore"]

            db = get_db()
            cursor = db.cursor()

            # Clean up related records
            cursor.execute("DELETE FROM chore_steps WHERE chore_id = ?", (chore_id,))
            cursor.execute("DELETE FROM assignments WHERE chore_id = ?", (chore_id,))
            cursor.execute("DELETE FROM chores WHERE id = ?", (chore_id,))
            # Delete orphaned steps:
            cursor.execute("DELETE FROM steps WHERE id NOT IN (SELECT step_id FROM chore_steps)")

            db.commit()
            db.close()

        if "assign_user" in request.form:
            chore_id = request.form["chore_id"]
            user_id = request.form["user_id"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM assignments WHERE chore_id = ?", (chore_id,)) # Delete old assignment
            cursor.execute("INSERT INTO assignments (user_id, chore_id) VALUES (?, ?)", (user_id, chore_id))
            db.commit()
            db.close()


    all_chores = get_all_chores()
    chore_steps_map = {chore[0]: get_steps_for_chore(chore[0]) for chore in all_chores}
    assignments = get_chore_assignments()
    sorted_next = get_chore_next_occurrences()

    return render_template("chores.html", all_users=get_all_users(), all_chores=all_chores, chore_steps_map=chore_steps_map, assignments=assignments, sorted_next=sorted_next, now=datetime.now())









# Database functions
## Recipes
### Get all recipes
def getRecipesTable():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM recipes;")
    return cursor.fetchall()


## Tasks
### Get all tasks
def get_all_tasks():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY due_date IS NULL, due_date ASC") # earliest due date first, DESC opposite
    tasks = cursor.fetchall()
    db.close()
    return tasks


## Rewards
### Get all rewards
def get_all_rewards():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM rewards ORDER BY cost DESC") # most expensive first, ASC for cheapest rewards first
    rewards = cursor.fetchall()
    db.close()
    return rewards

### Get coin balance
def get_coin_balance():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT balance FROM reward_user") 
    coin_balance = cursor.fetchone()[0]
    db.close()
    return coin_balance

### Get redemption log
def get_redemption_log():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM redeemed")
    log = cursor.fetchall()
    db.close()
    return log

### Get coin goal
def get_coin_goal():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT coingoal FROM reward_user")
    goal = cursor.fetchone()[0]
    db.close()
    return goal


## Chores
### Get all chore users
def get_all_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM chore_users")
    all = cursor.fetchall()
    db.close()
    return all
### Get all chores
def get_all_chores():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM chores")
    all = cursor.fetchall()
    db.close()
    return all
### Get steps for chores
def get_steps_for_chore(chore_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT steps.id, steps.name, steps.description, steps.time FROM chore_steps JOIN steps ON chore_steps.step_id = steps.id WHERE chore_steps.chore_id = ?", (chore_id,))
    results = cursor.fetchall()
    db.close()
    return results
### Get chore assignments
def get_chore_assignments():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT chores.id, chore_users.id, chore_users.name
        FROM chores
        LEFT JOIN assignments ON chores.id = assignments.chore_id
        LEFT JOIN chore_users ON assignments.user_id = chore_users.id
    """)
    rows = cursor.fetchall()
    db.close()
    # returns: {chore_id: (user_id, user_name)}
    return {row[0]: (row[1], row[2]) if row[1] else (None, None) for row in rows}
### Get chore next occurrences
def get_chore_next_occurrences():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, name, description, rrule FROM chores WHERE rrule IS NOT NULL")
    rows = cursor.fetchall()
    db.close()

    occurrences = []
    now = datetime.now()

    for chore_id, name, desc, rrule_str in rows:
        try:
            rule = rrulestr(rrule_str, dtstart=now)
            next_occurrence = rule.after(now)
            occurrences.append((next_occurrence, chore_id, name, desc))
        except Exception as e:
            occurrences.append((f"Invalid RRULE: {e}", chore_id, name, desc))

    # Sort: put datetime objects first, then strings (errors)
    def sort_key(item):
        return item[0] if isinstance(item[0], datetime) else datetime.max

    occurrences.sort(key=sort_key)

    return occurrences



# Error Handling
@app.errorhandler(404)
def page_not_found(error):
    return "<p>404 error</p>"
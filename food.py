from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
import os
from database import get_db
from database_functions import *

food_bp = Blueprint("food", __name__)



@food_bp.route("/food/diary", methods=["GET", "POST"])
def fooddiary():
    if request.args.get("date"): # /food/diary?date=12345678
        # print(request.args.get("date")) = 12345678
        today = request.args.get("date") # Not actually todays date it's which day they selected in the date input
    else: # Load diary for today's date
        today = datetime.today().strftime("%d%m%Y") # DDMMYYYY

    if not os.path.exists("./data.db"):
        return redirect(url_for("setup"))
    # Check if meals with todays date exists
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT mealID FROM meals WHERE mealDate = ?", (today,))
    meal = cursor.fetchone() # Get one meal if it exists
    
    
    # Initialise "Other" meal and Water counter
    if not meal: # If there are no meals for today
        # Make meals for today
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

    # Get all of today's saved meals
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
    targets = cursor.fetchone() # no target = '' ex: (1, '', 3, 4, 5) if no protein target and rest as 1,3,4,5

    # Get water current from water table (amountDrank WHERE waterDATE = DDMMYYYY)
    cursor.execute("SELECT * FROM water WHERE waterDate = ?", (today, ))
    water = cursor.fetchall() # water example: [('02082025', 0)] amountDrank = water[0][1]


    # get kitchen inventory
    inventoryData = get_inventory_data()
    # 0 inventoryID, 1 itemId, 2 itemName, 3 servings, 4 useByDate, 5 caloriesPerServing, 6 ProteinPerServing, 7 carbsPerServing, 8 fatPerServing, 9 location where it's stored
    
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


@food_bp.route("/food/inventory", methods=["GET", "POST"])
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


@food_bp.route("/food/recipes", methods=["GET", "POST"]) # TODO
def recipes():
    if request.method == "POST":
        # Add new recipe form
        if "recipeName" in request.form:
            db = get_db()
            cursor = db.cursor()
            recipeName = request.form["recipeName"].strip()
            recipeDescription = request.form["recipeDescription"].strip() or None
            servingsMade = request.form["servingsMade"].strip() or None
            estimatedTime = request.form["estimatedTime"].strip() or None
            #print(recipeName,recipeDescription,servingsMade,estimatedTime)

            cursor.execute("INSERT INTO recipes (recipeName, recipeDescription, servingsMade, estimatedTime) VALUES (?, ?, ?, ?)", (recipeName, recipeDescription, servingsMade, estimatedTime, ))

            db.commit() # If this fail db locks up or something
            db.close()
            flash(f"Recipe: {recipeName} saved")

        if "deleteRecipe" in request.form:
            deletedID = request.form["deleteRecipe"]
            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM recipes WHERE recipeID = ?", (deletedID,))
            flash("Recipe deleted")
            # TODO, update when other features are added
            db.commit()
            db.close()

        if "recipeID" in request.form:
            recipeID = request.form["recipeID"]
            addedItem = request.form["item"]
            quantity = request.form["quantity"] or 1

            db = get_db()
            cursor = db.cursor()

            cursor.execute("SELECT recipeName FROM recipes WHERE recipeID = ?", (recipeID,))
            recipe_name = cursor.fetchone()[0]
            cursor.execute("SELECT itemName FROM savedItems WHERE itemID = ?", (addedItem,))
            item_name = cursor.fetchone()[0]

            cursor.execute("INSERT OR IGNORE INTO recipeItems (recipeID, itemID, quantity) VALUES (?, ?, ?)", (recipeID, addedItem, quantity))
            db.commit()
            db.close()
            flash(f"Added {quantity}x {item_name} to {recipe_name}") # TODO include item name and recipe name

        if "deleteIngredient" in request.form:
            recipeID = request.form["recipe_ID"]
            itemID = request.form["deleteIngredient"]

            db = get_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM recipeItems WHERE recipeID = ? AND itemID = ?", (recipeID, itemID))
            db.commit()
            db.close()

            flash("Ingredient removed from recipe")


    return render_template("recipes.html", recipes=getRecipesTable(), inventoryData=get_inventory_data(), savedItems=get_all_saved_items(), ingredients=get_ingredients())

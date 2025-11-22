from database import get_db
from datetime import datetime


# Database Functions
## def fetchall

## def fetchone

## def execute


## Recipes
### Get all recipes
def getRecipesTable():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM recipes;")
    return cursor.fetchall()

### Get inventory data
def get_inventory_data():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT ki.inventoryID, ki.itemID, si.itemName, ki.servings, ki.useByDate,
            si.caloriesPerServing, si.proteinPerServing, si.carbsPerServing, si.fatPerServing, ki.location
        FROM kitchenInventory ki
        JOIN savedItems si ON ki.itemID = si.itemID
        WHERE ki.servings > 0""")
    data = cursor.fetchall()
    db.close()
    return data

### Get all saved items
def get_all_saved_items():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM savedItems")
    savedItems=cursor.fetchall()
    db.close()
    return savedItems

### Get ingredients
def get_ingredients():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT r.recipeID, si.itemID, si.itemName, ri.quantity
        FROM recipeItems ri
        JOIN savedItems si ON si.itemID = ri.itemID
        JOIN recipes r ON r.recipeID = ri.recipeID
    """)
    rows = cursor.fetchall()
    db.close()

    ingredients = {}
    for recipeID, itemID, itemName, quantity in rows:
        if recipeID not in ingredients:
            ingredients[recipeID] = []
        ingredients[recipeID].append({
            "itemID": itemID,
            "itemName": itemName,
            "quantity": quantity
        })
    return ingredients


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
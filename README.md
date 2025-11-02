# The White Room
A project inspired by Classroom of the Elite.
A holistic self management tool. (Work in Progress)

DEMO: http://46.101.90.169:5000/dashboard

## Features
### Updates from v1 to v2 (this repo/siege week)
- Read me
- Added icons for Tasks, Rewards, Timers and Chores
- Added Taskly, as tasks page
- Changed db functions and setup pages logic
- Added self reward system and fixed setup logic
- Added Timers, needs updating
- Added multi-user chore system
- Made icons for the new pages
- Indentation and comment changes
- Update schema, refactor some code into a function, delete recipe and add recipe forms + logic and deleted some files
- Add button for recipes page (no icon yet)
- Recipes page which allows you to save recipes, added icon

### Food Diary 
Save eaten foods and amount of water drank, include as much or as little detail as you like.
Optionally add foods from your inventory so you only have to write the amount eaten.
### Kitchen Inventory
Save products you buy and the amount of it you have in stock and where you keep it in your house.
When you run out of a saved product it shows up in your shopping list instead showing which store you bought if from and the price for the product.
### Recipes
- Make recipes with names, description, servings made, estimated time
- Add saved items to recipe with quantity (and you can delete ingredients from a recips)
- Has the start of a React.js version but it's not complete.

### Settings
To modify username, current and goal weight, calorie water and macro targets, allergies and dietary preferences
### Tasks
- E-ink display adapted user interface, but still looks good on desktop  
- Create tasks including due dates  
- Delete tasks  
- View all tasks ordered by earliest due date first  
- Mark tasks as (in)complete  
- Task descriptions  
- Edit task (name and date and description)  
- Message flashing for visual feedback of user's actions  
![alt text](tasks_demo.gif)
<!--
#### Planned Features: 
- Make different lists  
- Sub tasks  
- Priority levels  
- Customisable task tagging (none, habit, chore, and custom tags) (can have multiple tags)  
- Time tags (morning afternoon evening night)  
- Due date and time not just date  
- Searching and Filtering tasks (by Name, Tag, Datetime, )  
- Reminders (visual indicator for upcoming tasks)   
- Repeating checklists AKA Routines  
- Reoccuring tasks (Habits, have Habit tag by default)  
- Backup and import  
- Display current time on screen somewhere  
-->

### Self Reward System
Once fully integrated coins will be accumulated by completing to-do tasks, habits, and any items on your calendar (optional, you set the coin reward values yourself)
However in the demo you can only get coins by adding them to your balance manually
- E-ink display adapted user interface, but still looks good on desktop  
- View current coin balance  
- Add and subtract coins from balance  
- Add, view and delete saved rewards: name, description, and cost  
- Redeemed rewards are logged each entry can be deleted, and the whole log can be cleared   
- Redeem log can be expanded and hidden
- Coin addition and subtraction reasons can be optionally written  
- Store redemption count and display it  
- Save a coin goal / reward goal and progress bar for it  
- Show a lock emoji when you don't have enough coins to redeem  
- Custom image for rewards  
- Save "rewards" with negative cost, ex: something you do and you can earn that many coins each time you redeem, feature not a bug  
- Save "rewards" with 0 coin cost that just save data to the log (in the form "0 coins spent - reward name - timestamp"), feature not a bug  
<!--
#### Planned Features:
- Export log
- Reward tags/categories  
- Improved CSS  
- Redemption limits, ex: only redeem once a week  
- Time-based rewards, ex: only redeemable on weekends  
- Tag-based redemption limits, ex: you can only redeem a reward with tag food once per day
- Option to redeem based on coins earned in a certain time frame instead of balance, ex: save 20 coins this week and only then can you redeem a certain reward even if you already have 20 or more coins
- BUG timestamp is UTC not user timezone, so instead only display date or figure out a fix  
- Search/filter coin added reasons  
- Delete all log entries for displayed filter  
-->

![rewards demo](rewards_demo.png)

### Interval Timers
An alternative to "Time Out" the macOS app. However Trixie Timer is web based and therefore cross platform, furthermore there are no features locked behind paywalls.  
Pretty much needs a full rewrite but so does the rest of the code.

#### Planned features
- Custom "timer queues" to allow the user to do creative things such as make a custom running interval timer with TTS or other custom audio (just songs for example).  
- Button for the user to press that doesn't do anything (makes sure autoplay of timer sounds works)  
- Optionally each time a break starts open a CS2 style case for what you are going to do during the break (Defaults: Cat-Cow stretch, Plank, Deadhang, etc... but these "drops" are customisable so you can change it with drop percentage chances too)  

### Chore tracker and sharing system
A multi-user chore tracker to help divide and keep track of chores, and is specific to the chores required in your house.
Features:
- Adding multiple users  
- Assign chores to specific users  
- Show a list of chores with their next date  
- Each chore can be made up of detailed steps each with their own estimated time  
![chores demo](chores_demo.png)
<!--
Planned Features:  
- Start chore button that displays a timer for each step in the chore depending on it's estimated time
- Users have colours to highlight which upcoming chores are theirs, and make sure that user's colours are not similar to any other user's colours
- Instead of all upcoming chores only show one's either today or this week
- Have boxes similar to a kanban board one column for each user and you can just drag the chores to their column to assign it to them
- Add checkboxes and store their value to tell if they were completed or not to make the upcoming chores list more like a chores to do list
- Make the CSS more touch screen friendly for small displays
-->


## Self-Hosting Guide
install python if you don't have it  

```sh
git clone https://github.com/shania-codes/thewhiteroom  
cd thewhiteroom  

Windows: python -m venv venv  
macOS/Linux: python3 -m venv venv  

Windows: venv\Scripts\activate  
macOS/Linux: source venv/bin/activate  

pip install flask python-dateutil 

flask run   
```
Visit: https://127.0.0.1:5000/  


<!--
### Docker/Podman  
```sh
mkdir twr
cd twr
nano docker-compose.yml  
change (?)
sudo docker compose up -d  
```
open https://127.0.0.1:5000/ in browser  
-->
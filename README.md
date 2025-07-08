# BNB Financial Manager

Personal finance app to track your bank transactions and spending.

## How to run this

### Step 1: Get Docker
- Go to docker.com
- Download "Docker Desktop" for your computer
- Install it
- Restart your computer

### Step 2: Get this code
- Click the green "Code" button at the top of this page
- Click "Download ZIP"
- Extract the ZIP file to your desktop

### Step 3: Run the app:
Open up the extracted zip folder and click on the run-docker.bat.
This should work, but if it fails do the following:

Open terminal/command prompt
- Windows: Press Windows key + R, type "cmd", press Enter
- Mac: Press Cmd + Space, type "terminal", press Enter
- Linux: Ctrl + Alt + T

### Step 3.1: Navigate to the folder
```
cd Desktop/BNB-Financial-Manager-main
```

### Step 3.2: Start the app
```
docker-compose up
```

### Step 4: Open your browser
Go to: http://localhost:8000


## Quick Start Guide:
1. Go to the Accounts screen and add an account for each bank account that you want to import transactions from
    - This app doesn't connect with your bank yet, so the bsb and acc numbers will accept any value
2. Go to the tranasction screen and import all the qif files from each of your bank accounts.
    - You can do multiple at once if you have many accounts
    - I find that .qif files work the best, I've been getting some errors with .csv that I haven't got around to fixing yet
    - If you click on the 'preview' thing, it'll likely load up larger than your computer screen - I'll need to fix this too
3. Go to the Categories screen and add as many categories as you want.
    - Group Categories are just folders that you can store transaction categories to. For example, under expenses you could put "Kid #1", "Kid #2", and under each kid, you could put some transactions categories like "School Fees", "Roblox / V-Bucks giftcards"
    - Transaction categories are the actual things that you assign your transactions to (ie; rent, food, mortgage, automotive etc.)
    - You can try putting stuff under equity / liabilities, but I haven't finished implementing these features yet, all my stuff just goes under expenses or income
    - You can double click on a defined transaction category, and it'll show all the transactions that you've assigned to these categories
4. Go to Auto Rules if you would like to define some automatic rules to assign transactions. 
    - These run each time you import new transcations, you can also run them on command by pressing the button
    - For example, you could create one for Groceries with the keywords "Woolworths" or "Coles" or "Aldi"

5. Once you've finished assigning all your transactions, you can go to the "Charts" menu and start analysing your data.
    - Clicking on a "Group" in the category filter will select all transaction categories underneath that group.
    - You can also select individual transaction categories if you wish
    - If you like a certain plot, you can save it as a "View", that way, you can come back to this setup at any time in the future.
    - Some of the UI is a bit clunky here, so if you have any tips or things you would like to see I would appreciate the feedback 

## Privacy
All your data gets saved into a local database called finance.db, so it works without the internet and doesn't need any log ins
This just gets created automatically when you run the app for the first time
This file gets saved in the same folder as the run-docker.bat

## Troubleshooting

**"docker-compose not found"**
- Docker Desktop isn't installed or running

**"Port already in use"**
- Something else is using port 8000
- Close other programs and try again
- Sometimes a good ol turn it off and on again works well

**Can't import CSV**
- Your CSV needs Date, Description, Amount columns
- Try using QIF
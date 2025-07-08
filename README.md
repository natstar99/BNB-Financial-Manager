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

### Step 3: Open terminal/command prompt
- Windows: Press Windows key + R, type "cmd", press Enter
- Mac: Press Cmd + Space, type "terminal", press Enter
- Linux: Ctrl + Alt + T

### Step 4: Navigate to the folder
```
cd Desktop/BNB-Financial-Manager-main
```

### Step 5: Start the app
```
docker-compose up
```

### Step 6: Open your browser
Go to: http://localhost:8000

## What this does

- Import bank statements (QIF/CSV files)
- Categorise your transactions
- See charts of your spending
- Track expenses by category

## File formats supported

- QIF has been tested the most, CSV files still not the most reliable. But give it a go if you can' tuse QID

## Troubleshooting

**"docker-compose not found"**
- Docker Desktop isn't installed or running

**"Port already in use"**
- Something else is using port 8000
- Close other programs and try again

**Can't import CSV**
- Your CSV needs Date, Description, Amount columns
- Try using QIF

## Development

If you want to modify the code:

1. Install Python 3.8+
2. Install Node.js 16+
3. Run the backend: `python -m uvicorn api.main:app --reload --port 8000`
4. Run the frontend: `cd frontend && npm run dev`
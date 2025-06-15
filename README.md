# Telegram Bot for Name and Phone Collection

A FastAPI + Telegram bot to collect user names and phone numbers inside Telegram chat.

## Features
- Collects full name and phone number
- Accepts phone number via button OR text input
- Prevents duplicate registration
- Stores data in MongoDB Atlas

## Setup

1. Clone this project
2. Create a `.env` file using `.env.example`:

```
BOT_TOKEN=your_bot_token
MONGO_URI=your_mongo_connection
```

3. Install dependencies:

```
pip install -r requirements.txt
```

4. Run it:

```
uvicorn main:app --reload
```

## Deployment
Use services like [Render](https://render.com), [Railway](https://railway.app), or [Fly.io](https://fly.io) and set your environment variables (`BOT_TOKEN` and `MONGO_URI`) via their dashboard.


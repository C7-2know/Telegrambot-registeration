import os
import asyncio
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pymongo import MongoClient
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
from dotenv import load_dotenv

# Load .env
load_dotenv()

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
collection = mongo_client.telegramdb.users

# Telegram bot setup
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
bot_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# In-memory state tracking
user_states = {}     # { user_id: "awaiting_name" | "awaiting_phone" }
temp_user_data = {}  # { user_id: { "name": ... } }

# Check if user is already registered
def is_user_registered(user_id: int) -> bool:
    return collection.count_documents({ "user_id": user_id }) > 0

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id

   
    user_states[user_id] = "awaiting_name"
    await context.bot.send_message(chat_id=user_id, text="👋 እንኳን ደህና መጡ! እባክዎ ሙሉ ስምዎን ያስገቡ።")

# Message handler
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    message = update.message

    # if is_user_registered(user_id):
    #     await context.bot.send_message(chat_id=user_id, text="✅ You're already registered.")
    #     return

    state = user_states.get(user_id)

    if state == "awaiting_name":
        temp_user_data[user_id] = {
            "user_id": user_id,
            "name": message.text
        }
        user_states[user_id] = "awaiting_phone"

        button = KeyboardButton("📞 Share your phone", request_contact=True)
        markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, resize_keyboard=True)
        await message.reply_text("Please share your phone number or type it manually:", reply_markup=markup)

    elif state == "awaiting_phone":
        phone = message.contact.phone_number if message.contact else message.text

        data = temp_user_data[user_id]
        data["phone"] = phone

        if not is_user_registered(user_id):
            collection.insert_one(data)
            await message.reply_text("✅ ስለተመዘገቡ እናመሰግናለን፤ እንደ እግዚአብሔር ፈቃድ የጉዞ ቀን እሁድ ሰኔ 16 2017፤ ጠዋት 02:00 ሰዓት፤  መነሻ ቦታ 5 ኪሎ ዶርም ግቢ በር ነው። ሰላመ እግዚአብሔር አይለየን🙏")

        user_states.pop(user_id, None)
        temp_user_data.pop(user_id, None)

        await message.reply_text("You can now close the chat.", reply_markup=ReplyKeyboardRemove())

    else:
        await message.reply_text("Please type /start to begin.")

# Register handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, message_handler))

# FastAPI lifespan (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔄 Starting Telegram bot polling...")
    await bot_app.initialize()
    await bot_app.start()
    asyncio.create_task(bot_app.updater.start_polling())  # This just starts polling in the background

    yield

    print("🛑 Stopping bot...")
    await bot_app.updater.stop()
    await bot_app.stop()
    await bot_app.shutdown()

# FastAPI app instance with lifespan
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, replace with your frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
def read_root():
    return {"status": "Bot is running"}

# Endpoint to get registered users
@app.get("/users")
def get_registered_users():
    users = list(collection.find({}, {"_id": 0, "name": 1, "phone": 1}))
    return {"users": users}

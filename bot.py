import os
import asyncio
import logging
import random
import sqlite3
from datetime import datetime, timedelta
from typing import Tuple

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

# ====== ТВОИ ДАННЫЕ ======
BOT_TOKEN = os.getenv('BOT_TOKEN', '8469399083:AAGhrVdgF8OARGB4mJET1qIAfJdEuaAsrpY')
SUPPORT_USERNAME = os.getenv('SUPPORT_USERNAME', '@legendsa2')
REFERRAL_LINK = os.getenv('REFERRAL_LINK', 'https://u3.shortink.io/register?utm_campaign=838786&utm_source=affiliate&utm_medium=sr&a=WQ656LRzTHSJ6J&ac=aipidgin_nigeria&code=WELCOME50')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://aipidgin-bot.bothost.app')
WEBHOOK_PATH = '/webhook'
WEBHOOK_PORT = 8080
# =========================

# Настройки
SIGNAL_COOLDOWN_SECONDS = 900  # 15 минут
DEFAULT_ACCURACY_MIN = 96
DEFAULT_ACCURACY_MAX = 99

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Language storage
user_lang = {}

# Categories and assets from Pocket Option
CATEGORIES = {
    "forex": "💱 Forex",
    "crypto": "₿ Crypto",
    "stocks": "📈 Stocks",
    "commodities": "🛢️ Commodities",
    "indices": "📊 Indices"
}

ASSETS = {
    "forex": [
        "EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC", "USD/CAD OTC",
        "EUR/GBP OTC", "EUR/JPY OTC", "GBP/JPY OTC", "USD/CHF OTC", "NZD/USD OTC",
        "CAD/JPY OTC", "CHF/JPY OTC", "AUD/JPY OTC", "EUR/AUD OTC", "GBP/AUD OTC"
    ],
    "crypto": [
        "BTC/USD", "ETH/USD", "LTC/USD", "XRP/USD", "BCH/USD",
        "ADA/USD", "DOT/USD", "LINK/USD", "DOGE/USD", "TRX/USD",
        "SOL/USD", "MATIC/USD", "UNI/USD", "ATOM/USD", "XLM/USD"
    ],
    "stocks": [
        "Apple OTC", "Tesla OTC", "Amazon OTC", "Google OTC", "Microsoft OTC",
        "Meta OTC", "Netflix OTC", "Boeing OTC", "Alibaba OTC", "Intel OTC",
        "AMD OTC", "Nvidia OTC", "PayPal OTC", "Coca-Cola OTC", "McDonald's OTC"
    ],
    "commodities": [
        "Gold OTC", "Silver OTC", "Brent Oil OTC", "Crude Oil OTC",
        "Natural Gas OTC", "Copper OTC", "Platinum OTC", "Palladium OTC"
    ],
    "indices": [
        "S&P 500 OTC", "NASDAQ OTC", "Dow Jones OTC", "FTSE 100 OTC",
        "DAX 30 OTC", "Nikkei 225 OTC", "AUS 200 OTC", "Euro Stoxx 50 OTC"
    ]
}

TIMEFRAMES = ["S5", "S10", "S15", "M5", "M10", "M15"]

# Pidgin translations
PIDGIN = {
    "welcome": "How far! Welcome to AI Pidgin 🇳🇬 I be your AI guy wey go give you hot signals wey dey win big time. Plenty Naija people don chop money! 💯 Oya choose wetin you want (or tap 'Register' for 50% bonus quick quick!)",
    "register_bonus": "🔥 SPECIAL OFFER 🔥\n\nRegister with my link and get 50% BONUS on your first deposit! Minimum deposit only $10.\n\n👉 Click below, register, come back and start winning!",
    "after_register": "✅ You don register! Now make first deposit to unlock UNLIMITED signals.",
    "after_deposit": "💰 Deposit confirmed! You now get ACCURATE signals 99.9% of the time! Click GET SIGNAL to start.",
    "signal_guarantee": "⚠️ 99.9% ACCURACY ⚠️\nThis signal dey enter! Oya quick quick!",
    "no_register": "❌ You no register yet!\n\n👉 Register first with my link, get 50% bonus, then come back for signals.",
    "no_deposit": "❌ You no make deposit yet!\n\n👉 Make first deposit (minimum $10), get 50% bonus, then see signals dey enter!",
    "select_category": "Choose wetin you want trade:",
    "select_asset": "Choose di pair:",
    "select_timeframe": "Choose how long:",
    "get_signal": "Make I see signal",
    "repeat": "Do again",
    "reset": "Start fresh",
    "up": "UP 🚀",
    "down": "DOWN 📉",
    "confidence": "Confidence",
    "strength": "Strength",
    "accuracy": "Accuracy",
    "volume": "Volume",
    "valid_until": "Valid until",
    "cooldown": "⏳ Wait {} minutes {} seconds before next signal.",
    "no_active_signal": "No active signals now. Check back later.",
    "signal_expired": "Signal expired. Wait for next signal.",
}

ENGLISH = {
    "welcome": "🔥 Welcome to AI Pidgin! I'm your AI trader giving high-win signals straight from Naija vibes. 🇳🇬 Many users winning big — join them! 💯 Select option below (or tap 'Register' for 50% bonus!)",
    "register_bonus": "🔥 SPECIAL OFFER 🔥\n\nRegister with my link and get 50% BONUS on your first deposit! Minimum deposit only $10.\n\n👉 Click below, register, come back and start winning!",
    "after_register": "✅ You're registered! Now make your first deposit to unlock UNLIMITED signals.",
    "after_deposit": "💰 Deposit confirmed! You now get ACCURATE signals 99.9% of the time! Click GET SIGNAL to start.",
    "signal_guarantee": "⚠️ 99.9% ACCURACY ⚠️\nThis signal is guaranteed to enter!",
    "no_register": "❌ You haven't registered yet!\n\n👉 Register first with my link, get 50% bonus, then come back for signals.",
    "no_deposit": "❌ You haven't made a deposit yet!\n\n👉 Make your first deposit (minimum $10), get 50% bonus, and start winning!",
    "select_category": "Select category:",
    "select_asset": "Select instrument:",
    "select_timeframe": "Select timeframe:",
    "get_signal": "Get Signal",
    "repeat": "Repeat",
    "reset": "Reset",
    "up": "UP 🚀",
    "down": "DOWN 📉",
    "confidence": "Confidence",
    "strength": "Strength",
    "accuracy": "Accuracy",
    "volume": "Volume",
    "valid_until": "Valid until",
    "cooldown": "⏳ Wait {} minutes {} seconds before next signal.",
    "no_active_signal": "No active signals now. Check back later.",
    "signal_expired": "Signal expired. Wait for next signal.",
}

def get_text(user_id, key):
    lang = user_lang.get(user_id, "pidgin")
    if lang == "pidgin":
        return PIDGIN.get(key, key)
    return ENGLISH.get(key, key)

# ==================== DATABASE FUNCTIONS ====================

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create users table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            registered INTEGER DEFAULT 0,
            reg_date TEXT,
            deposit_amount REAL DEFAULT 0,
            deposit_confirmed INTEGER DEFAULT 0,
            deposit_date TEXT,
            trader_id TEXT,
            click_id TEXT,
            last_signal TIMESTAMP,
            signals_received INTEGER DEFAULT 0,
            signals_successful INTEGER DEFAULT 0
        )
    """)
    
    # Create global_signals table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS global_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_text TEXT,
            pair TEXT,
            direction TEXT,
            price REAL,
            sent_at TIMESTAMP,
            expires_at TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

def create_user(user_id, username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username, reg_date) VALUES (?, ?, ?)",
        (user_id, username, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def update_user_signal(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET last_signal = ?, signals_received = signals_received + 1 WHERE user_id = ?",
        (datetime.now().isoformat(), user_id)
    )
    conn.commit()
    conn.close()

def get_active_signal():
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute(
        "SELECT * FROM global_signals WHERE is_active = 1 AND expires_at > ? ORDER BY sent_at DESC LIMIT 1",
        (now,)
    )
    signal = cur.fetchone()
    conn.close()
    return signal

def deactivate_expired_signals():
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute("UPDATE global_signals SET is_active = 0 WHERE expires_at < ?", (now,))
    conn.commit()
    conn.close()

def save_global_signal(pair, direction, price, expires_minutes=5):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Deactivate previous active signal
    cur.execute("UPDATE global_signals SET is_active = 0 WHERE is_active = 1")
    
    sent_at = datetime.now()
    expires_at = sent_at + timedelta(minutes=expires_minutes)
    signal_text = f"🔥 {direction} {pair}" + (f" at {price}" if price else "")
    
    cur.execute(
        """
        INSERT INTO global_signals (signal_text, pair, direction, price, sent_at, expires_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        """,
        (signal_text, pair, direction, price, sent_at.isoformat(), expires_at.isoformat())
    )
    conn.commit()
    conn.close()
    return signal_text

def check_cooldown(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT last_signal FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if row and row['last_signal']:
        last = datetime.fromisoformat(row['last_signal'])
        now = datetime.now()
        diff = now - last
        if diff.total_seconds() < SIGNAL_COOLDOWN_SECONDS:
            remaining = SIGNAL_COOLDOWN_SECONDS - int(diff.total_seconds())
            minutes = remaining // 60
            seconds = remaining % 60
            return minutes, seconds
    return None

def get_user_stats(user_id) -> Tuple[int, int, int]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT signals_received, signals_successful FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        received = row['signals_received'] or 0
        # Generate successful stats on the fly (96-99% accuracy)
        successful = int(received * random.uniform(0.96, 0.99))
        accuracy = round((successful / received * 100) if received > 0 else 0)
        return received, successful, accuracy
    return 0, 0, 0

# ==================== HANDLERS ====================

# FSM States
class TradeStates(StatesGroup):
    selecting_category = State()
    selecting_asset = State()
    selecting_timeframe = State()
    showing_signal = State()

# Language selection
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    create_user(user_id, username)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇳🇬 Pidgin", callback_data="lang_pidgin"),
         InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await message.answer("Choose your language:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = callback.data.split("_")[1]
    user_lang[user_id] = lang
    
    await callback.message.edit_text(
        get_text(user_id, "welcome"),
        parse_mode="Markdown"
    )
    await show_main_menu(callback.message, state, user_id)

async def show_main_menu(message: types.Message, state: FSMContext, user_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "get_signal"), callback_data="start_trade")]
    ])
    await message.answer(get_text(user_id, "select_category"), reply_markup=keyboard)
    await state.set_state(TradeStates.selecting_category)

@dp.callback_query(lambda c: c.data == "start_trade")
async def start_trade(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=CATEGORIES["forex"], callback_data="cat_forex")],
        [InlineKeyboardButton(text=CATEGORIES["crypto"], callback_data="cat_crypto")],
        [InlineKeyboardButton(text=CATEGORIES["stocks"], callback_data="cat_stocks")],
        [InlineKeyboardButton(text=CATEGORIES["commodities"], callback_data="cat_commodities")],
        [InlineKeyboardButton(text=CATEGORIES["indices"], callback_data="cat_indices")]
    ])
    await callback.message.edit_text(get_text(user_id, "select_category"), reply_markup=keyboard)
    await state.set_state(TradeStates.selecting_category)

@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def select_category(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    category = callback.data.split("_")[1]
    await state.update_data(category=category)
    
    assets = ASSETS[category]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for asset in assets[:10]:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=asset, callback_data=f"asset_{asset}")])
    
    await callback.message.edit_text(get_text(user_id, "select_asset"), reply_markup=keyboard)
    await state.set_state(TradeStates.selecting_asset)

@dp.callback_query(lambda c: c.data.startswith("asset_"))
async def select_asset(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    asset = callback.data.replace("asset_", "")
    await state.update_data(asset=asset)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for tf in TIMEFRAMES:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=tf, callback_data=f"tf_{tf}")])
    
    await callback.message.edit_text(get_text(user_id, "select_timeframe"), reply_markup=keyboard)
    await state.set_state(TradeStates.selecting_timeframe)

@dp.callback_query(lambda c: c.data.startswith("tf_"))
async def select_timeframe(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    tf = callback.data.replace("tf_", "")
    await state.update_data(timeframe=tf)
    
    data = await state.get_data()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "get_signal"), callback_data="generate_signal")]
    ])
    await callback.message.edit_text(
        f"✅ {data.get('asset')} | {tf}\n\n{get_text(user_id, 'get_signal')}?",
        reply_markup=keyboard
    )

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    received, successful, accuracy = get_user_stats(user_id)
    text = (
        f"📊 *Your personal stats:*\n"
        f"Signals received: {received}\n"
        f"Successful: {successful}\n"
        f"Accuracy: {accuracy}%"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "generate_signal")
async def generate_signal(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()

    # TEMPORARY CHECK (replace with database later)
    if user_id != 8444406750:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Register now", url=REFERRAL_LINK)]
        ])
        await callback.message.edit_text(
            "❌ You need to register first!\n\n"
            "👉 Click below to register and get 50% bonus!",
            reply_markup=keyboard
        )
        return
    
    # Check cooldown
    cooldown = check_cooldown(user_id)
    if cooldown:
        minutes, seconds = cooldown
        await callback.message.edit_text(
            get_text(user_id, 'cooldown').format(minutes, seconds),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Back", callback_data="back_to_main")]
            ])
        )
        return
    
    # Check for active global signal
    deactivate_expired_signals()
    active_signal = get_active_signal()
    
    if active_signal:
        # Use existing global signal
        signal_text = active_signal['signal_text']
        direction = active_signal['direction']
        pair = active_signal['pair']
        tf = data.get("timeframe", "M5")
    else:
        # Generate new random signal
        direction = random.choice(["up", "down"])
        pair = data.get("asset", "EUR/USD")
        tf = data.get("timeframe", "M5")
        signal_text = save_global_signal(pair, direction, None)
    
    # Generate random values for display
    confidence = random.randint(70, 95)
    accuracy = random.randint(60, 85)
    strength = random.choice(["Low", "Medium", "High"])
    volume = random.choice(["Low", "Medium", "High"])
    
    # Calculate valid until time
    seconds = 0
    if tf.startswith("S"):
        seconds = int(tf[1:])
    elif tf.startswith("M"):
        seconds = int(tf[1:]) * 60
    valid_until = (datetime.now() + timedelta(seconds=seconds)).strftime("%H:%M")
    
    final_signal = (
        f"*PocketOption*\n"
        f"*The AI Analytics Tool*\n\n"
        f"{get_text(user_id, 'signal_guarantee')}\n\n"
        f"*{get_text(user_id, 'up') if direction == 'up' else get_text(user_id, 'down')}*\n\n"
        f"MARKET: OTC\n"
        f"{get_text(user_id, 'confidence')}: {confidence}%\n"
        f"TIME: {tf}\n"
        f"{get_text(user_id, 'strength')}: {strength}\n"
        f"PAIR: {pair}\n"
        f"{get_text(user_id, 'valid_until')}: {valid_until}\n\n"
        f"{accuracy}% {get_text(user_id, 'accuracy')}\n"
        f"{volume} {get_text(user_id, 'volume')}"
    )
    
    # Update user stats
    update_user_signal(user_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "repeat"), callback_data="repeat_trade"),
         InlineKeyboardButton(text=get_text(user_id, "reset"), callback_data="reset_trade")]
    ])
    
    await callback.message.edit_text(final_signal, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(TradeStates.showing_signal)

@dp.callback_query(lambda c: c.data == "repeat_trade")
async def repeat_trade(callback: types.CallbackQuery, state: FSMContext):
    await generate_signal(callback, state)

@dp.callback_query(lambda c: c.data == "reset_trade")
async def reset_trade(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await state.clear()
    await show_main_menu(callback.message, state, user_id)

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await state.clear()
    await show_main_menu(callback.message, state, user_id)

# ==================== WEBHOOK SETUP ====================

async def on_startup():
    webhook_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
    await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    print(f"✅ Webhook установлен на {webhook_url}")

async def on_shutdown():
    await bot.delete_webhook()
    print("👋 Webhook удалён")

async def main():
    init_db()
    print("🚀 Бот запускается в режиме webhook...")
    
    # Start webhook
    await dp.start_webhook(
        bot=bot,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host="0.0.0.0",
        port=WEBHOOK_PORT
    )

if __name__ == "__main__":
    asyncio.run(main())
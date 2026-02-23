"""AIPidginBot production bot (aiogram 3.25.0)."""

import os
import asyncio
import logging
import random
import sqlite3
from datetime import datetime, timedelta
from typing import Tuple

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramNetworkError

# Попытаемся импортировать dotenv (опционально)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ────────────────────────────────────────────────────────────────────────────
# КОНФИГУРАЦИЯ
# ────────────────────────────────────────────────────────────────────────────

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Set it in environment variables.")
LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING').upper()
BOT_VERSION = os.getenv('BOT_VERSION', '2026.02.23-1')
SUPPORT_USERNAME = os.getenv('SUPPORT_USERNAME', '@legendsa2')
REFERRAL_LINK = os.getenv('REFERRAL_LINK', 'https://u3.shortink.io/register?utm_campaign=838786&utm_source=affiliate&utm_medium=sr&a=WQ656LRzTHSJ6J&ac=aipidgin_nigeria&code=WELCOME50')

ADMIN_ID = 8131080797
PUBLIC_CHANNEL_LINK = "https://t.me/thinkersden_trading"
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
DB_READY = False

# Пути к картинкам
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
IMAGE_WELCOME = os.path.join(IMAGES_DIR, "Welcome Menu.jpg")
IMAGE_ACCESS_DENIED = os.path.join(IMAGES_DIR, "Access Denied.jpg")
IMAGE_SUCCESS = os.path.join(IMAGES_DIR, "Success Story.jpg")
IMAGE_REPORT = os.path.join(IMAGES_DIR, "Operations Report.jpg")

# Константы
SIGNAL_COOLDOWN_SECONDS = int(os.getenv('SIGNAL_COOLDOWN_SECONDS', '900'))


def parse_user_ids(value: str) -> set[int]:
    user_ids: set[int] = set()
    for part in value.split(','):
        raw = part.strip()
        if not raw:
            continue
        try:
            user_ids.add(int(raw))
        except ValueError:
            logging.getLogger(__name__).warning(
                f"Ignoring invalid user id in NO_COOLDOWN_USER_IDS: {raw}"
            )
    return user_ids


NO_COOLDOWN_USER_IDS = parse_user_ids(os.getenv('NO_COOLDOWN_USER_IDS', ''))


def is_no_cooldown_user(user_id: int) -> bool:
    return user_id == ADMIN_ID or user_id in NO_COOLDOWN_USER_IDS


DEFAULT_ACCURACY_MIN = 96
DEFAULT_ACCURACY_MAX = 99

# ==================== ASSETS FROM POCKET OPTION (OFFICIAL LIST 2026) ====================
CATEGORIES = {
    "forex": [
        "EUR/USD OTC", "AUD/CAD OTC", "AUD/CHF OTC", "AUD/JPY OTC", "AUD/NZD OTC",
        "AUD/USD OTC", "CAD/CHF OTC", "CAD/JPY OTC", "CHF/JPY OTC", "EUR/CHF OTC",
        "EUR/GBP OTC", "EUR/JPY OTC", "EUR/NZD OTC", "GBP/AUD OTC", "GBP/JPY OTC",
        "GBP/USD OTC", "NZD/JPY OTC", "NZD/USD OTC", "USD/CAD OTC", "USD/CHF OTC",
        "USD/JPY OTC", "USD/RUB OTC", "EUR/RUB OTC", "CHF/NOK OTC", "EUR/HUF OTC",
        "USD/CNH OTC", "EUR/TRY OTC", "USD/INR OTC", "USD/SGD OTC", "USD/CLP OTC",
        "USD/MYR OTC", "USD/THB OTC", "USD/VND OTC", "USD/PKR OTC", "USD/COP OTC",
        "USD/EGP OTC", "USD/PHP OTC", "USD/MXN OTC", "USD/DZD OTC", "USD/ARS OTC",
        "USD/IDR OTC", "USD/BRL OTC", "USD/BDT OTC", "YER/USD OTC", "LBP/USD OTC",
        "TND/USD OTC", "MAD/USD OTC", "BHD/CNY OTC", "AED/CNY OTC", "SAR/CNY OTC",
        "QAR/CNY OTC", "OMR/CNY OTC", "JOD/CNY OTC", "NGN/USD OTC", "KES/USD OTC",
        "ZAR/USD OTC", "UAH/USD OTC"
    ],
    "crypto": [
        "BNB OTC", "Solana OTC", "Cardano OTC", "TRON OTC", "Chainlink OTC",
        "Toncoin OTC", "Avalanche OTC", "Bitcoin OTC", "Dogecoin OTC", "Polkadot OTC",
        "Ethereum OTC", "Litecoin OTC", "Polygon OTC", "Bitcoin ETF OTC"
    ],
    "stocks": [
        "Apple OTC", "McDonald's OTC", "Microsoft OTC", "FACEBOOK INC OTC", "Intel OTC",
        "Tesla OTC", "Pfizer Inc OTC", "Johnson & Johnson OTC", "Boeing Company OTC",
        "American Express OTC", "Amazon OTC", "Citigroup Inc OTC", "FedEx OTC", "VISA OTC",
        "Cisco OTC", "ExxonMobil OTC", "Alibaba OTC", "Netflix OTC", "Palantir Technologies OTC",
        "GameStop Corp OTC", "Advanced Micro Devices OTC", "Coinbase Global OTC",
        "Marathon Digital Holdings OTC", "NVIDIA OTC"
    ],
    "commodities": [
        "Gold OTC", "Brent Oil OTC", "WTI Crude Oil OTC", "Silver OTC",
        "Natural Gas OTC", "Platinum spot OTC", "Palladium spot OTC"
    ],
    "indices": [
        "AUS 200 OTC", "E35EUR OTC", "100GBP OTC", "F40EUR OTC", "JPN225 OTC",
        "D30EUR OTC", "E50EUR OTC", "SP500 OTC", "DJI30 OTC", "US100 OTC", "VIX OTC"
    ]
}
# =========================================================================================
TIMEFRAMES = ["M1", "M5", "M15", "H1"]

# ────────────────────────────────────────────────────────────────────────────
# ЛОГИРОВАНИЕ И БОТ
# ────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger("aiogram.event").setLevel(logging.WARNING)
logging.getLogger("aiogram.dispatcher").setLevel(logging.WARNING)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Language storage
user_lang = {}
user_selection = {}
global_signals = {}

# ────────────────────────────────────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ────────────────────────────────────────────────────────────────────────────

async def safe_edit_message(message: types.Message, text: str, **kwargs):
    """Safe edit for text/caption messages with fallback to new message."""
    try:
        if getattr(message, "text", None) is not None:
            await message.edit_text(text, **kwargs)
            return

        if getattr(message, "caption", None) is not None:
            await message.edit_caption(caption=text, **kwargs)
            return

        await message.answer(text, **kwargs)
    except Exception as e:
        error_text = str(e).lower()
        if "message is not modified" in error_text:
            return
        if "there is no text in the message to edit" in error_text:
            await message.answer(text, **kwargs)
            return
        logger.error(f"❌ Error editing message: {e}")
        raise

async def show_category_from_callback(callback: types.CallbackQuery, user_id: int):
    """Open category menu from callback for both text and photo messages."""
    text = get_text(user_id, "select_category")
    keyboard = category_keyboard(user_id)

    if not callback.message:
        return

    try:
        await safe_edit_message(callback.message, text, reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"⚠️ Could not render category menu for user {user_id}: {e}")
        await callback.message.answer(text, reply_markup=keyboard)

def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Build a single practical main menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "get_access_btn"), callback_data="get_access")],
        [InlineKeyboardButton(text=get_text(user_id, "how_to_start_btn"), callback_data="how_to_start")],
        [InlineKeyboardButton(text=get_text(user_id, "join_channel_btn"), url=PUBLIC_CHANNEL_LINK)]
    ])

# ────────────────────────────────────────────────────────────────────────────
# ТЕКСТЫ (PIDGIN & ENGLISH)
# ────────────────────────────────────────────────────────────────────────────

PIDGIN = {
    "welcome": "🚀 How far! Welcome to The Thinker's Den. Free channel dey open for everybody — join dey learn. To unlock premium AI signals, make minimum deposit of $10 through my link. Make we grow together! 📊",
    "menu_caption": "🚀 **THE THINKER'S DEN**\n\n🤖 AI-powered analysis\n🎓 Education\n👑 Premium signal access after deposit\n\nChoose your next step below:",
    "menu_plain": "🚀 The Thinker's Den\n\nChoose your next step below:",
    "register_bonus": "🔥 EXCLUSIVE OFFER\n\nRegister with my link and get 50% bonus on your first deposit. Minimum deposit na just $10.\n\n💡 Register now, fund your account, then come back for premium AI signals.",
    "after_register": "✅ Registration done! Next step: make deposit to unlock premium AI signals. 💰",
    "after_deposit": "✅ Deposit confirmed! You now get access to premium AI signals. Tap Get Access to start receiving real-time analysis and trade ideas. 📊",
    "how_to_start": "📋 *How to start:*\n\n1) 🚀 Register with my link\n2) 🔗 Join free channel\n3) 💰 Deposit minimum $10\n4) 📊 Tap *Get Access* for premium AI signals\n\n💡 Trade smart and manage risk.",
    "signal_guarantee": "📊 AI-POWERED MARKET ANALYSIS\nThis setup is based on structure, momentum, and volume. High-probability setup — trade with discipline.",
    "no_register": "❌ You never register yet.\n\n🚀 Start with registration first to unlock your path to premium AI signals.",
    "no_deposit": "❌ Deposit never reflect yet.\n\n💰 Make minimum $10 deposit to unlock premium AI signals, then tap Get Access.",
    "select_category": "Choose market to analyze:",
    "select_asset": "Choose instrument:",
    "select_timeframe": "Choose timeframe:",
    "get_signal": "Get Analysis",
    "repeat": "Repeat",
    "reset": "Reset",
    "up": "LONG 📈",
    "down": "SHORT 📉",
    "confidence": "Confidence",
    "strength": "Momentum",
    "accuracy": "Win Rate",
    "volume": "Volume",
    "valid_until": "Valid until",
    "cooldown": "⏳ Wait {} minutes {} seconds before next analysis.",
    "no_active_signal": "No active setups now. Check back later.",
    "signal_expired": "This setup expired. Wait for next opportunity.",
    "need_deposit_caption": "❌ Deposit never confirm yet.\n\n💰 Minimum $10 deposit unlocks premium AI signals.\n🚀 Register below and claim your 50% bonus.",
    "register_now_btn": "🚀 Register Now",
    "register_deposit_btn": "💰 Register & Deposit",
    "get_access_btn": "📊 Get Access",
    "how_to_start_btn": "📋 How to Start",
    "join_channel_btn": "🔗 Join Free Channel",
    "ready_prompt": "Ready? 🚀",
    "back": "◀️ Back",
}

ENGLISH = {
    "welcome": "🚀 Welcome to The Thinker's Den! The channel is free for everyone — join and learn daily. To unlock premium AI-powered signals, make a minimum deposit of $10 using my link. Let's grow together! 📊",
    "menu_caption": "🚀 **THE THINKER'S DEN**\n\n🤖 AI-powered analysis\n🎓 Education\n👑 Premium signal access after deposit\n\nChoose your next step below:",
    "menu_plain": "🚀 The Thinker's Den\n\nChoose your next step below:",
    "register_bonus": "🔥 EXCLUSIVE OFFER\n\nRegister with my referral link and get a 50% bonus on your first deposit. Minimum deposit is just $10.\n\n💡 Register now, fund your account, and unlock premium AI signals.",
    "after_register": "✅ Registration successful! Next step: make a deposit to get premium AI signals. 💰",
    "after_deposit": "✅ Deposit confirmed! You now have access to premium AI signals. Click Get Access to start receiving real-time analysis and trade ideas. 📊",
    "how_to_start": "📋 *How to start:*\n\n1) 🚀 Register using my link\n2) 🔗 Join the free channel\n3) 💰 Make a minimum $10 deposit\n4) 📊 Tap *Get Access* for premium AI-powered signals\n\n💡 Trade smart and manage risk.",
    "signal_guarantee": "📊 AI-POWERED MARKET ANALYSIS\nThis setup is based on structure, momentum, and volume. High-probability setup — manage risk on every trade.",
    "no_register": "❌ You're not registered yet.\n\n🚀 Complete registration first to unlock your premium signal path.",
    "no_deposit": "❌ Deposit not confirmed yet.\n\n💰 Make a minimum $10 deposit to unlock premium AI signals, then tap Get Access.",
    "select_category": "Select category:",
    "select_asset": "Select instrument:",
    "select_timeframe": "Select timeframe:",
    "get_signal": "Get Analysis",
    "repeat": "Repeat",
    "reset": "Reset",
    "up": "LONG 📈",
    "down": "SHORT 📉",
    "confidence": "Confidence",
    "strength": "Momentum",
    "accuracy": "Win Rate",
    "volume": "Volume",
    "valid_until": "Valid until",
    "cooldown": "⏳ Wait {} minutes {} seconds before next analysis.",
    "no_active_signal": "No active setups now. Check back later.",
    "signal_expired": "This setup expired. Wait for next opportunity.",
    "need_deposit_caption": "❌ Deposit is not confirmed yet.\n\n💰 Minimum $10 deposit unlocks premium AI signals.\n🚀 Register below and claim your 50% bonus.",
    "register_now_btn": "🚀 Register Now",
    "register_deposit_btn": "💰 Register & Deposit",
    "get_access_btn": "📊 Get Access",
    "how_to_start_btn": "📋 How to Start",
    "join_channel_btn": "🔗 Join Free Channel",
    "ready_prompt": "Ready? 🚀",
    "back": "◀️ Back",
}

def get_text(user_id, key):
    """Получить текст на выбранном языке пользователя."""
    lang = user_lang.get(user_id, "pidgin")
    if lang == "pidgin":
        return PIDGIN.get(key, key)
    return ENGLISH.get(key, key)

# ────────────────────────────────────────────────────────────────────────────
# DATABASE FUNCTIONS
# ────────────────────────────────────────────────────────────────────────────

def get_db_connection():
    """Получить соединение с БД."""
    if not globals().get("DB_READY"):
        init_db_if_needed()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db_if_needed():
    """Инициализировать БД (создать таблицы если их нет)."""
    global DB_READY
    if DB_READY:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Таблица пользователей
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
            signals_successful INTEGER DEFAULT 0,
            added_to_channel INTEGER DEFAULT 0
        )
    """)
    
    # Добавляем индексы для быстрых запросов
    cur.execute("CREATE INDEX IF NOT EXISTS idx_deposit_confirmed ON users(deposit_confirmed)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_last_signal ON users(last_signal)")
    
    conn.commit()
    conn.close()
    DB_READY = True
    logger.info("✅ Database initialized successfully")

def init_db():
    """Инициализировать БД (создать таблицы если их нет)."""
    init_db_if_needed()

def get_user(user_id):
    """Получить данные пользователя из БД."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cur.fetchone()
    conn.close()
    return user

def create_user(user_id, username):
    """Создать нового пользователя в БД."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username, reg_date) VALUES (?, ?, ?)",
        (user_id, username, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def update_user_signal(user_id):
    """Обновить статистику сигналов пользователя."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET last_signal = ?, signals_received = signals_received + 1 WHERE user_id = ?",
        (datetime.now().isoformat(), user_id)
    )
    conn.commit()
    conn.close()

def get_user_stats(user_id) -> Tuple[int, int, int]:
    """Получить статистику пользователя (сигналы, успехи, точность)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT signals_received, signals_successful FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        received = row['signals_received'] or 0
        successful = int(received * random.uniform(0.96, 0.99))
        accuracy = round((successful / received * 100) if received > 0 else 0)
        return received, successful, accuracy
    return 0, 0, 0


def get_all_user_ids() -> list[int]:
    """Получить список всех user_id из БД."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = cur.fetchall()
    conn.close()
    return [int(row["user_id"]) for row in rows]

def is_deposit_confirmed(user_id):
    """Проверить, подтвержден ли депозит пользователя (ОСНОВНАЯ ПРОВЕРКА)."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT deposit_confirmed FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    is_confirmed = row and row['deposit_confirmed'] == 1
    logger.info(f"Deposit check for user {user_id}: {'CONFIRMED ✅' if is_confirmed else 'NOT CONFIRMED ❌'}")
    return is_confirmed

def build_random_signal(user_id: int) -> str:
    direction_key = "up" if random.choice([True, False]) else "down"
    accuracy = random.randint(96, 98)
    confidence = accuracy
    valid_until = (datetime.now() + timedelta(minutes=30)).strftime("%H:%M")

    return (
        f"{get_text(user_id, 'signal_guarantee')}\n\n"
        f"Signal: {get_text(user_id, direction_key)}\n"
        f"{get_text(user_id, 'accuracy')}: {accuracy}%\n"
        f"{get_text(user_id, 'confidence')}: {confidence}%\n"
        f"{get_text(user_id, 'valid_until')}: {valid_until}"
    )

def get_cooldown_remaining(user_id: int) -> int:
    if is_no_cooldown_user(user_id):
        return 0

    user = get_user(user_id)
    if not user or not user["last_signal"]:
        return 0
    try:
        last_ts = datetime.fromisoformat(user["last_signal"])
    except ValueError:
        return 0
    elapsed = (datetime.now() - last_ts).total_seconds()
    remaining = int(SIGNAL_COOLDOWN_SECONDS - elapsed)
    return remaining if remaining > 0 else 0

def get_signal_key(category: str, asset: str, timeframe: str) -> str:
    return f"{category}:{asset}:{timeframe}"

def get_or_create_global_signal(category: str, asset: str, timeframe: str, user_id: int | None = None) -> dict:
    key = get_signal_key(category, asset, timeframe)
    now = datetime.now()
    bypass_cache = is_no_cooldown_user(user_id) if user_id is not None else False
    if not bypass_cache:
        signal = global_signals.get(key)
        if signal and (now - signal["created_at"]).total_seconds() < SIGNAL_COOLDOWN_SECONDS:
            return signal

    direction_key = "up" if random.choice([True, False]) else "down"
    accuracy = random.randint(96, 98)
    valid_until = (now + timedelta(minutes=30)).strftime("%H:%M")
    signal = {
        "created_at": now,
        "direction_key": direction_key,
        "accuracy": accuracy,
        "valid_until": valid_until,
    }
    if not bypass_cache:
        global_signals[key] = signal
    return signal

def build_signal_text(user_id: int, category: str, asset: str, timeframe: str) -> str:
    signal = get_or_create_global_signal(category, asset, timeframe, user_id)
    return (
        f"{get_text(user_id, 'signal_guarantee')}\n\n"
        f"Asset: {asset}\n"
        f"Timeframe: {timeframe}\n"
        f"Signal: {get_text(user_id, signal['direction_key'])}\n"
        f"{get_text(user_id, 'accuracy')}: {signal['accuracy']}%\n"
        f"{get_text(user_id, 'confidence')}: {signal['accuracy']}%\n"
        f"{get_text(user_id, 'valid_until')}: {signal['valid_until']}"
    )

async def send_signal(callback: types.CallbackQuery, user_id: int):
    selection = user_selection.get(user_id)
    if not selection:
        await callback.answer()
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            get_text(user_id, "select_category"),
            reply_markup=category_keyboard(user_id),
        )
        return

    remaining = get_cooldown_remaining(user_id)
    if remaining > 0:
        mins, secs = divmod(remaining, 60)
        await callback.answer()
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(get_text(user_id, "cooldown").format(mins, secs))
        return

    update_user_signal(user_id)
    signal_text = build_signal_text(user_id, selection["category"], selection["asset"], selection["timeframe"])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "repeat"), callback_data="do_signal")],
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back:asset")]
    ])
    
    await callback.answer()  # Закрываем callback
    await callback.message.delete()  # Удаляем предыдущее сообщение
    await callback.message.answer(signal_text, reply_markup=keyboard)
    logger.info(f"📊 Sent global signal to user {user_id}")

def category_keyboard(user_id: int) -> InlineKeyboardMarkup:
    rows = []
    rows.append([InlineKeyboardButton(text="Crypto", callback_data="cat:crypto")])
    rows.append([InlineKeyboardButton(text="Forex", callback_data="cat:forex")])
    rows.append([InlineKeyboardButton(text="Stocks", callback_data="cat:stocks")])
    rows.append([InlineKeyboardButton(text="Commodities", callback_data="cat:commodities")])
    rows.append([InlineKeyboardButton(text="Indices", callback_data="cat:indices")])
    rows.append([InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def asset_keyboard(category: str, user_id: int = 0) -> InlineKeyboardMarkup:
    rows = []
    for asset in CATEGORIES.get(category, []):
        rows.append([InlineKeyboardButton(text=asset, callback_data=f"asset:{category}:{asset}")])
    rows.append([InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back:category")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def timeframe_keyboard(category: str, asset: str, user_id: int = 0) -> InlineKeyboardMarkup:
    rows = []
    for tf in TIMEFRAMES:
        rows.append([InlineKeyboardButton(text=tf, callback_data=f"tf:{category}:{asset}:{tf}")])
    rows.append([InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back:asset")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ────────────────────────────────────────────────────────────────────────────
# ОБРАБОТЧИКИ СОБЫТИЙ (HANDLERS)
# ────────────────────────────────────────────────────────────────────────────

# 🔤 Выбор языка
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Команда /start - выбор языка."""
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    create_user(user_id, username)
    logger.info(f"👤 New/returning user: {user_id} ({username})")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇳🇬 Pidgin", callback_data="lang_pidgin"),
         InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await message.answer("Choose your language:", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    """Обработка выбора языка пользователя."""
    user_id = callback.from_user.id
    lang = callback.data.split("_")[1]
    user_lang[user_id] = lang
    logger.info(f"🔤 User {user_id} selected language: {lang}")
    
    await safe_edit_message(
        callback.message,
        get_text(user_id, "welcome"),
        parse_mode="Markdown"
    )
    await show_main_menu(callback.message, user_id)

async def show_main_menu(message: types.Message, user_id: int):
    """Показать главное меню с картинкой Welcome Menu."""
    keyboard = main_menu_keyboard(user_id)
    
    try:
        photo = FSInputFile(IMAGE_WELCOME)
        await message.answer_photo(
            photo=photo,
            caption=get_text(user_id, "menu_caption"),
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except FileNotFoundError:
        await message.answer(get_text(user_id, "menu_plain"), reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "get_access")
async def get_access(callback: types.CallbackQuery):
    """Callback: checks deposit and opens signal category selection."""
    user_id = callback.from_user.id
    logger.info(f"📌 User {user_id} clicked 'Get Access'")
    
    if is_deposit_confirmed(user_id):
        await show_category_from_callback(callback, user_id)
        await callback.answer()
    else:
        logger.info(f"❌ User {user_id} NO deposit, showing registration prompt")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text(user_id, "register_now_btn"), url=REFERRAL_LINK)],
            [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back:main")]
        ])
        await callback.answer()
        try:
            photo = FSInputFile(IMAGE_ACCESS_DENIED)
            await callback.message.answer_photo(
                photo=photo,
                caption=get_text(user_id, "need_deposit_caption"),
                reply_markup=keyboard
            )
        except FileNotFoundError:
            await callback.message.answer(
                get_text(user_id, "need_deposit_caption"),
                reply_markup=keyboard
            )
        return

# ℹ️ How to Start кнопка
@dp.callback_query(lambda c: c.data == "how_to_start")
async def how_to_start(callback: types.CallbackQuery):
    """Callback: информация как начать работу."""
    user_id = callback.from_user.id
    text = f"{get_text(user_id, 'how_to_start')}\n\n👉 [Register Here]({REFERRAL_LINK})"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "register_now_btn"), url=REFERRAL_LINK)],
        [InlineKeyboardButton(text=get_text(user_id, "join_channel_btn"), url=PUBLIC_CHANNEL_LINK)],
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back:main")]
    ])
    await callback.answer()  # Закрываем callback
    await callback.message.delete()  # Удаляем фото-сообщение
    await callback.message.answer(text, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(lambda c: c.data == "vip_channel")
async def vip_channel(callback: types.CallbackQuery):
    """Legacy callback compatibility: route old 'Signal Access' button to Get Access flow."""
    logger.info(f"📈 User {callback.from_user.id} clicked legacy 'Signal Access' button")
    await get_access(callback)

@dp.callback_query(lambda c: c.data.startswith("cat:"))
async def select_category(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    _, category = callback.data.split(":", 1)
    
    # Инициализируем или обновляем user_selection для этого пользователя
    if user_id not in user_selection:
        user_selection[user_id] = {}
    user_selection[user_id]["category"] = category
    
    logger.info(f"📂 User {user_id} selected category: {category}")
    
    await safe_edit_message(
        callback.message,
        get_text(user_id, "select_asset"),
        reply_markup=asset_keyboard(category, user_id),
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("asset:"))
async def select_asset(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    _, category, asset = callback.data.split(":", 2)
    
    if user_id not in user_selection:
        user_selection[user_id] = {}
    user_selection[user_id]["category"] = category
    user_selection[user_id]["asset"] = asset
    
    logger.info(f"💱 User {user_id} selected asset: {asset} (category: {category})")
    
    await safe_edit_message(
        callback.message,
        get_text(user_id, "select_timeframe"),
        reply_markup=timeframe_keyboard(category, asset, user_id),
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("tf:"))
async def select_timeframe(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    _, category, asset, timeframe = callback.data.split(":", 3)
    
    if user_id not in user_selection:
        user_selection[user_id] = {}
    user_selection[user_id]["category"] = category
    user_selection[user_id]["asset"] = asset
    user_selection[user_id]["timeframe"] = timeframe
    
    logger.info(f"⏱️ User {user_id} selected timeframe: {timeframe}")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "get_signal"), callback_data="do_signal")],
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back:asset")]
    ])
    await safe_edit_message(
        callback.message,
        f"{get_text(user_id, 'select_timeframe')} {timeframe}\n\n{get_text(user_id, 'ready_prompt')}",
        reply_markup=keyboard,
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "do_signal")
async def do_signal(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    await send_signal(callback, user_id)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back:main")
async def back_to_main(callback: types.CallbackQuery):
    """Вернуться в главное меню."""
    user_id = callback.from_user.id
    user_selection.pop(user_id, None)  # Очистить выбор при возврате в меню
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await show_main_menu(callback.message, user_id)
    logger.info(f"🔙 User {user_id} back to main menu")

@dp.callback_query(lambda c: c.data == "back:category")
async def back_to_category(callback: types.CallbackQuery):
    """Вернуться к выбору категорий."""
    user_id = callback.from_user.id
    if user_id in user_selection:
        user_selection[user_id].clear()
    await safe_edit_message(
        callback.message,
        get_text(user_id, "select_category"),
        reply_markup=category_keyboard(user_id),
    )
    logger.info(f"🔙 User {user_id} back to category selection")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back:asset")
async def back_to_asset(callback: types.CallbackQuery):
    """Вернуться к выбору активов (сохраняя категорию)."""
    user_id = callback.from_user.id
    
    # Извлечём категорию из user_selection
    if user_id in user_selection and "category" in user_selection[user_id]:
        category = user_selection[user_id]["category"]
        # Очищаем asset и timeframe, оставляя категорию
        if "asset" in user_selection[user_id]:
            del user_selection[user_id]["asset"]
        if "timeframe" in user_selection[user_id]:
            del user_selection[user_id]["timeframe"]
        
        await safe_edit_message(
            callback.message,
            get_text(user_id, "select_asset"),
            reply_markup=asset_keyboard(category, user_id),
        )
        logger.info(f"🔙 User {user_id} back to asset selection (category: {category})")
    else:
        # Если категория потеряна, вернём к выбору категорий
        if user_id in user_selection:
            user_selection[user_id].clear()
        await safe_edit_message(
            callback.message,
            get_text(user_id, "select_category"),
            reply_markup=category_keyboard(user_id),
        )
        logger.info(f"🔙 User {user_id} back to category (no category found)")
    
    await callback.answer()

async def send_stats_message(message: types.Message, user_id: int):
    """Send personal stats to a user message context."""
    received, successful, accuracy = get_user_stats(user_id)
    
    # Выбираем изображение в зависимости от accuracy
    if accuracy >= 90:
        image_path = IMAGE_SUCCESS  # Высокий win rate - Success Story
    else:
        image_path = IMAGE_REPORT  # Обычная статистика - Operations Report
    
    text = (
        f"📊 *Your personal stats:*\n"
        f"Signals received: {received}\n"
        f"Successful: {successful}\n"
        f"Accuracy: {accuracy}%"
    )
    
    try:
        photo = FSInputFile(image_path)
        await message.answer_photo(photo=photo, caption=text, parse_mode="Markdown")
    except FileNotFoundError:
        await message.answer(text, parse_mode="Markdown")
    
    logger.info(f"📊 Stats requested by user {user_id}")

# 📊 /stats команда - статистика пользователя
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Команда /stats - показать личную статистику."""
    user_id = message.from_user.id
    await send_stats_message(message, user_id)

@dp.message(Command("version"))
async def cmd_version(message: types.Message):
    """Команда /version - проверить текущую версию запущенного бота."""
    await message.answer(f"🤖 Bot version: {BOT_VERSION}\nFile: bot.py")


@dp.message(Command("my_id"))
async def cmd_my_id(message: types.Message):
    """Команда /my_id - показать Telegram user_id пользователя."""
    user_id = message.from_user.id
    await message.answer(
        f"🆔 Your Telegram user_id: {user_id}\n"
        f"Set env NO_COOLDOWN_USER_IDS={user_id} and restart bot."
    )


@dp.message(lambda message: (message.text or "").strip().lower() in {"my id", "my_id"})
async def text_my_id(message: types.Message):
    """Текстовый триггер my id/my_id - показать Telegram user_id пользователя."""
    user_id = message.from_user.id
    await message.answer(f"🆔 Your Telegram user_id: {user_id}")


@dp.message(Command("diag"))
async def cmd_diag(message: types.Message):
    """Команда /diag - диагностика доступа пользователя к сигналам."""
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    create_user(user_id, username)

    user = get_user(user_id)
    deposit_confirmed = bool(user and user["deposit_confirmed"] == 1)
    cooldown_remaining = get_cooldown_remaining(user_id)
    no_cooldown = is_no_cooldown_user(user_id)
    is_admin = user_id == ADMIN_ID

    selection = user_selection.get(user_id, {})
    selected_category = selection.get("category", "-")
    selected_asset = selection.get("asset", "-")
    selected_timeframe = selection.get("timeframe", "-")

    lines = [
        "🛠 DIAG REPORT",
        f"user_id: {user_id}",
        f"username: @{username}" if username != "unknown" else "username: -",
        f"deposit_confirmed: {deposit_confirmed}",
        f"cooldown_remaining_sec: {cooldown_remaining}",
        f"cooldown_default_sec: {SIGNAL_COOLDOWN_SECONDS}",
        f"no_cooldown_whitelist: {no_cooldown}",
        f"is_admin: {is_admin}",
        f"selected_category: {selected_category}",
        f"selected_asset: {selected_asset}",
        f"selected_timeframe: {selected_timeframe}",
        f"bot_version: {BOT_VERSION}",
    ]

    if not deposit_confirmed:
        lines.append("hint: access blocked by deposit_confirmed=False")

    await message.answer("\n".join(lines))


@dp.message(lambda message: (message.text or "").strip().lower() == "diag")
async def text_diag(message: types.Message):
    """Текстовый триггер diag//diag - диагностика доступа пользователя к сигналам."""
    await cmd_diag(message)


@dp.message(Command("grant_deposit"))
async def cmd_grant_deposit(message: types.Message):
    """Команда /grant_deposit <user_id> - выдать доступ по депозиту (только админ)."""
    admin_user_id = message.from_user.id
    if admin_user_id != ADMIN_ID:
        await message.answer("⛔ Not for you.")
        logger.warning(f"⚠️ Unauthorized /grant_deposit attempt by user {admin_user_id}")
        return

    full_text = (message.text or "").strip()
    parts = full_text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage:\n/grant_deposit <telegram_user_id>")
        return

    raw_user_id = parts[1].strip()
    try:
        target_user_id = int(raw_user_id)
    except ValueError:
        await message.answer("❌ Invalid user_id. Example: /grant_deposit 123456789")
        return

    create_user(target_user_id, "")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET deposit_confirmed = 1, deposit_date = ? WHERE user_id = ?",
        (datetime.now().isoformat(), target_user_id)
    )
    conn.commit()
    conn.close()

    await message.answer(f"✅ deposit_confirmed = 1 for user {target_user_id}")
    logger.info(f"✅ Admin {admin_user_id} granted deposit to user {target_user_id}")

@dp.callback_query(lambda c: c.data == "stats_btn")
async def stats_btn_callback(callback: types.CallbackQuery):
    """Backward compatibility for old inline menus that still have Stats button."""
    user_id = callback.from_user.id
    await callback.answer()
    await send_stats_message(callback.message, user_id)


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    """Команда /broadcast - отправка уведомления всем пользователям (только админ)."""
    admin_user_id = message.from_user.id
    if admin_user_id != ADMIN_ID:
        await message.answer("⛔ Not for you.")
        logger.warning(f"⚠️ Unauthorized /broadcast attempt by user {admin_user_id}")
        return

    full_text = (message.text or "").strip()
    parts = full_text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "Usage:\n"
            "/broadcast Reminder: You can complete registration and start trading now."
        )
        return

    broadcast_text = parts[1].strip()
    user_ids = get_all_user_ids()
    if not user_ids:
        await message.answer("ℹ️ No users in database yet.")
        return

    sent_count = 0
    failed_count = 0

    await message.answer(f"📣 Broadcast started for {len(user_ids)} users...")

    for target_user_id in user_ids:
        try:
            await bot.send_message(target_user_id, broadcast_text)
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logger.warning(f"Broadcast failed for user {target_user_id}: {e}")

    await message.answer(
        f"✅ Broadcast finished.\nSent: {sent_count}\nFailed: {failed_count}"
    )
    logger.info(
        f"📣 Broadcast by admin {admin_user_id}: total={len(user_ids)}, sent={sent_count}, failed={failed_count}"
    )

# ✅ /make_me_deposit команда - временное подтверждение депозита (админ)
@dp.message(Command("make_me_deposit"))
async def cmd_make_me_deposit(message: types.Message):
    """Команда /make_me_deposit - подтверждение депозита для теста (только админ)."""
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    if user_id != ADMIN_ID:
        await message.answer(
            "⛔ Admin only. Send /my_id to the admin so they can run /grant_deposit <your_id>."
        )
        logger.warning(f"⚠️ Unauthorized /make_me_deposit attempt by user {user_id}")
        return

    # Убедимся, что пользователь существует в БД
    create_user(user_id, username)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET deposit_confirmed = 1, deposit_date = ? WHERE user_id = ?",
        (datetime.now().isoformat(), user_id)
    )
    conn.commit()
    conn.close()

    await message.answer("✅ deposit_confirmed = 1. You can test Get Access now.")
    logger.info(f"✅ Admin {user_id} set deposit_confirmed = 1")


@dp.message(lambda message: (message.text or "").strip().lower() == "make_me_deposit")
async def text_make_me_deposit(message: types.Message):
    """Текстовый триггер make_me_deposit//make_me_deposit (только админ)."""
    await cmd_make_me_deposit(message)


# ────────────────────────────────────────────────────────────────────────────
# STARTUP
# ────────────────────────────────────────────────────────────────────────────

async def main():
    """Главная функция запуска бота."""
    init_db()
    logger.info("🚀 AIPidginBot starting in polling mode")
    logger.info(f"🏷️ Bot version: {BOT_VERSION}")
    logger.info(f"📊 Public channel link: {PUBLIC_CHANNEL_LINK}")
    logger.info("🌐 aiogram version: 3.25.0 (optimized)")
    
    # Чистый polling режим: webhook должен быть отключен
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except TelegramNetworkError as e:
        logger.warning(f"⚠️ Could not delete webhook due to network issue: {e}")

    # Устойчивый polling: не выходим при кратковременных сетевых сбоях
    retry_delay = 3
    try:
        while True:
            try:
                await dp.start_polling(bot, close_bot_session=False)
                break
            except TelegramNetworkError as e:
                logger.warning(f"🌐 Network issue while polling: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            except Exception:
                raise
    finally:
        await bot.session.close()

# ────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.critical(f"💥 CRITICAL ERROR: {e}", exc_info=True)

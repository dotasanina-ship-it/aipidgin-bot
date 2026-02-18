import asyncio
import logging
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ====== ТВОИ ДАННЫЕ ======
BOT_TOKEN = "8469399083:AAGhrVdgF8OARGB4mJET1qIAfJdEuaAsrpY"
SUPPORT_USERNAME = "@legendsa2"
REFERRAL_LINK = "https://u3.shortink.io/register?utm_campaign=838786&utm_source=affiliate&utm_medium=sr&a=WQ656LRzTHSJ6J&ac=aipidgin_nigeria&code=WELCOME50"
# =========================

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
    "welcome": "How far! Welcome to *AI Pidgin* 🇳🇬\n\nI go give you ACCURATE trading signals. 99.9% of my signals enter! 💯\n\nChoose wetin you want:",
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
    "valid_until": "Valid until"
}

ENGLISH = {
    "welcome": "🔥 Welcome to *AI Pidgin*!\n\nI give you ACCURATE trading signals. 99.9% of my signals win! 💯\n\nSelect option below:",
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
    "valid_until": "Valid until"
}

def get_text(user_id, key):
    lang = user_lang.get(user_id, "pidgin")
    if lang == "pidgin":
        return PIDGIN.get(key, key)
    return ENGLISH.get(key, key)

# FSM States
class TradeStates(StatesGroup):
    selecting_category = State()
    selecting_asset = State()
    selecting_timeframe = State()
    showing_signal = State()

# Language selection
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
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
    for asset in assets[:10]:  # Show first 10 to avoid too many buttons
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

@dp.callback_query(lambda c: c.data == "generate_signal")
async def generate_signal(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()

    # TEMPORARY CHECK (replace with database later)
    if user_id != 8444406750:  # Only admin has access for now
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Register now", url=REFERRAL_LINK)]
        ])
        await callback.message.edit_text(
            "❌ You need to register first!\n\n"
            "👉 Click below to register and get 50% bonus!",
            reply_markup=keyboard
        )
        return
    
    # Random signal generation
    direction = random.choice(["up", "down"])
    confidence = random.randint(70, 95)
    accuracy = random.randint(60, 85)
    strength = random.choice(["Low", "Medium", "High"])
    volume = random.choice(["Low", "Medium", "High"])
    
    # Calculate valid until time
    tf = data.get("timeframe", "M5")
    seconds = 0
    if tf.startswith("S"):
        seconds = int(tf[1:])
    elif tf.startswith("M"):
        seconds = int(tf[1:]) * 60
    valid_until = (datetime.now() + timedelta(seconds=seconds)).strftime("%H:%M")
    
    signal_text = (
        f"*PocketOption*\n"
        f"*The AI Analytics Tool*\n\n"
        f"{get_text(user_id, 'signal_guarantee')}\n\n"
        f"*{get_text(user_id, 'up') if direction == 'up' else get_text(user_id, 'down')}*\n\n"
        f"MARKET: OTC\n"
        f"{get_text(user_id, 'confidence')}: {confidence}%\n"
        f"TIME: {data.get('timeframe')}\n"
        f"{get_text(user_id, 'strength')}: {strength}\n"
        f"PAIR: {data.get('asset')}\n"
        f"{get_text(user_id, 'valid_until')}: {valid_until}\n\n"
        f"{accuracy}% {get_text(user_id, 'accuracy')}\n"
        f"{volume} {get_text(user_id, 'volume')}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "repeat"), callback_data="repeat_trade"),
         InlineKeyboardButton(text=get_text(user_id, "reset"), callback_data="reset_trade")]
    ])
    
    await callback.message.edit_text(signal_text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(TradeStates.showing_signal)

@dp.callback_query(lambda c: c.data == "repeat_trade")
async def repeat_trade(callback: types.CallbackQuery, state: FSMContext):
    await generate_signal(callback, state)

@dp.callback_query(lambda c: c.data == "reset_trade")
async def reset_trade(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await state.clear()
    await show_main_menu(callback.message, state, user_id)

async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


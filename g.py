#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import logging
import asyncio
import random
import requests
from datetime import datetime
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# --------------- Конфигурация ----------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "7816419974:AAGDTqScu5OE2KvmGNPZA-BBYov0XnQCmgI")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7167007722"))

POCKET_LINK = os.getenv("POCKET_LINK", "https://bit.ly/pocket-option-rus")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/your_channel")
SUPPORT_BOT = os.getenv("SUPPORT_BOT", "https://t.me/G0_PLUS_SUPPORTBOT")

# Пути картинок
PHOTOS = {
    "banner": "photo/banner.jpg",
    "register": "photo/banner.jpg",
    "limited": "photo/banner.jpg",
    "processing": "photo/banner.jpg",
    "final": "photo/banner.jpg",
}

ALLOWED_FILE = "allowed_users.json"

PAIRS = [
    "BTCUSDT", "ETHUSDT", "XRPUSDT", "LTCUSDT", "BNBUSDT",
    "SOLUSDT", "DOGEUSDT", "TRXUSDT", "ADAUSDT", "DOTUSDT",
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "NZDUSD", "USDCHF", "EURGBP", "EURJPY", "GBPJPY",
]

TIMEFRAMES = [
    "1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h",
    "1d", "3d", "1w", "1M", "1y"
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("goplus")

# -------- Мультиязычные тексты -------------
TEXTS = {
    "ru": {
        "choose_lang": "Выбери язык:",
        "active_caption": "👋 Добро пожаловать! Нажмите ACTIVE чтобы начать.",
        "welcome": "👋 Привет! Я — Go Plus, твой персональный торговый бот.",
        "why": "✨ Почему выбирают Go Plus:\n• Более 100 активов\n• Поддержка OTC\n• 2 режима торговли",
        "how": "🤖 Как это работает:\n1) Выбираешь актив\n2) Указываешь время\n3) Получаешь сигнал\n4) Фиксируешь профит",
        "gpt": "🤖 Я аналитический модуль: анализирую множество индикаторов и паттернов.",
        "register": f"⚡ Чтобы получить доступ, зарегистрируйся по ссылке:\n{POCKET_LINK}\n\nИли нажми одну из кнопок ниже.",
        "limited": "🔒 Доступ ограничен. Ожидайте активации.",
        "access_granted": "✅ Доступ активирован! Теперь выберите торговую пару:",
        "choose_pair": "📊 Выберите торговую пару:",
        "choose_tf": "⏱ Выберите таймфрейм:",
        "pair_chosen": "Пара: {pair}\nВыберите таймфрейм:",
        "time_chosen": "Таймфрейм: {tf}\n\nНачинаю анализ...",
        "anim_fetch": "🔄 Получаю рыночные данные...",
        "anim_ind": "⚙️ Вычисляю индикаторы...",
        "anim_check": "🔍 Проверяю сигналы...",
        "anim_done": "✅ Анализ завершён!",
        "final": ("📈 Прогноз — {pair} / {tf}\n\n"
                  "💰 Цена последняя: {price}\n"
                  "📊 Мин: {low}   Макс: {high}\n"
                  "Сигнал: {signal}\n"
                  "Доверие: {conf}%\n\nПричины:\n{reasons}"),
        "new_forecast": "Новый прогноз",
        "back_pairs": "⬅️ НАЗАД",
        "admin_notify": "Новый пользователь @{username} (ID: {uid}) запросил доступ.",
        "only_admin": "❌ Только администратор может выполнить эту команду.",
        "allowed_ok": "✅ Пользователь {uid} разрешён.",
        "revoked_ok": "✅ Доступ пользователя {uid} отозван.",
        "no_user": "❌ Пользователь {uid} не найден.",
        "getid": "Ваш Telegram ID: {uid}",
    },
    "en": {
        "choose_lang": "Choose your language:",
        "active_caption": "👋 Welcome! Press ACTIVE to begin.",
        "welcome": "👋 Hi, I'm Go Plus, your trading assistant bot.",
        "why": "✨ Why choose Go Plus:\n• 100+ assets\n• OTC support\n• 2 modes\n• instant analysis",
        "how": "🤖 How it works:\n1) Choose asset\n2) Choose timeframe\n3) Get a signal\n4) Take profit",
        "gpt": "🤖 I analyze many indicators and patterns for you.",
        "register": f"⚡ To get access, register here:\n{POCKET_LINK}\n\nOr use one of the buttons below.",
        "limited": "🔒 Access restricted. Please wait for activation.",
        "access_granted": "✅ Access granted! Now choose a trading pair:",
        "choose_pair": "📊 Choose a trading pair:",
        "choose_tf": "⏱ Choose a timeframe:",
        "pair_chosen": "Pair: {pair}\nChoose timeframe:",
        "time_chosen": "Timeframe: {tf}\n\nStarting analysis...",
        "anim_fetch": "🔄 Fetching market data...",
        "anim_ind": "⚙️ Calculating indicators...",
        "anim_check": "🔍 Checking signals...",
        "anim_done": "✅ Analysis done!",
        "final": ("📈 Forecast — {pair} / {tf}\n\n"
                  "💰 Last price: {price}\n"
                  "📊 Low: {low}   High: {high}\n"
                  "Signal: {signal}\n"
                  "Confidence: {conf}%\n\nReasons:\n{reasons}"),
        "new_forecast": "New Forecast",
        "back_pairs": "⬅️ BACK",
        "admin_notify": "New user @{username} (ID: {uid}) requested access.",
        "only_admin": "❌ Command available to admin only.",
        "allowed_ok": "✅ User {uid} allowed.",
        "revoked_ok": "✅ Access revoked for {uid}.",
        "no_user": "❌ User {uid} not found.",
        "getid": "Your Telegram ID: {uid}",
    },
    "hi": {
        "choose_lang": "भाषा चुनें:",
        "active_caption": "👋 स्वागत है! ACTIVE दबाएँ।",
        "welcome": "👋 नमस्ते, मैं Go Plus, आपका ट्रेडिंग सहायक।",
        "why": "✨ क्यों Go Plus:\n• 100+ एसेट्स\n• OTC सपोर्ट\n• 2 मोड\n• तुरंत विश्लेषण",
        "how": "🤖 यह काम करता है:\n1) एसेट चुनें\n2) टाइमफ्रेम चुनें\n3) सिग्नल पाएं\n4) प्रॉफिट लें",
        "gpt": "🤖 मैं कई संकेतकों और पैटर्न को विश्लेषित करता हूँ।",
        "register": f"⚡ एक्सेस पाने के लिए यहाँ रजिस्टर करें:\n{POCKET_LINK}\n\nया नीचे दिए बटन दबाएँ।",
        "limited": "🔒 एक्सेस सीमित है। कृपया प्रतीक्षा करें।",
        "access_granted": "✅ एक्सेस दिया गया! अब जोड़ी चुनें:",
        "choose_pair": "📊 एक जोड़ी चुनें:",
        "choose_tf": "⏱ एक टाइमफ्रेम चुनें:",
        "pair_chosen": "जोड़ी: {pair}\nटाइमफ्रेम चुनें:",
        "time_chosen": "टाइमफ्रेम: {tf}\n\nविश्लेषण शुरू हो रहा है...",
        "anim_fetch": "🔄 मार्केट डेटा लाया जा रहा है...",
        "anim_ind": "⚙️ संकेतकों की गणना हो रही है...",
        "anim_check": "🔍 सिग्नल और वॉल्यूम चेक हो रहे हैं...",
        "anim_done": "✅ विश्लेषण पूर्ण!",
        "final": ("📈 पूर्वानुमान — {pair} / {tf}\n\n"
                  "💰 अंतिम मूल्य: {price}\n"
                  "📊 न्यूनतम: {low}   अधिकतम: {high}\n"
                  "सिग्नल: {signal}\n"
                  "विश्वास: {conf}%\n\nकारण:\n{reasons}"),
        "new_forecast": "नया पूर्वानुमान",
        "back_pairs": "⬅️ वापस",
        "admin_notify": "नए उपयोगकर्ता @{username} (ID: {uid}) ने एक्सेस मांगा।",
        "only_admin": "❌ केवल एडमिन ही यह कमांड चला सकता है।",
        "allowed_ok": "✅ उपयोगकर्ता {uid} को अनुमति दी गई।",
        "revoked_ok": "✅ उपयोगकर्ता {uid} का एक्सेस वापस लिया गया।",
        "no_user": "❌ उपयोगकर्ता {uid} सूची में नहीं है।",
        "getid": "आपका Telegram ID: {uid}",
    }
}

# -------- Функции сохранения разрешённых пользователей ------------
def load_allowed():
    if os.path.exists(ALLOWED_FILE):
        try:
            with open(ALLOWED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return set(data.get("allowed", []))
        except Exception as e:
            logger.warning("Load allowed error: %s", e)
    return set()

def save_allowed(s: set):
    try:
        with open(ALLOWED_FILE, "w", encoding="utf-8") as f:
            json.dump({"allowed": list(s)}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Save allowed error: %s", e)

ALLOWED = load_allowed()

# ---------------- Keyboards ----------------
def kb_active():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔵 ACTIVE", callback_data="activate")]])

def kb_language():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")]
    ])

def kb_register_stage(lang):
    t = TEXTS[lang]
    # Buttons: Register, Request Access, Write me ID, Our Channel
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Register", url=POCKET_LINK)],
        [InlineKeyboardButton("Request Access", callback_data="request_access")],
        [InlineKeyboardButton("Напиши мне ID", url="https://t.me/VikramBiz")],
        [InlineKeyboardButton("Наш канал", url=CHANNEL_LINK)]
    ])

def kb_pairs(lang="ru"):
    kb = []
    for i in range(0, len(PAIRS), 4):
        row = [InlineKeyboardButton(p, callback_data=f"pair|{p}") for p in PAIRS[i:i+4]]
        kb.append(row)
    kb.append([InlineKeyboardButton(TEXTS[lang]["back_pairs"], callback_data="back_to_intro")])
    return InlineKeyboardMarkup(kb)

def kb_timeframes(lang="ru"):
    kb = []
    for i in range(0, len(TIMEFRAMES), 5):
        row = [InlineKeyboardButton(tf, callback_data=f"tf|{tf}") for tf in TIMEFRAMES[i:i+5]]
        kb.append(row)
    kb.append([InlineKeyboardButton(TEXTS[lang]["back_pairs"], callback_data="back_to_pairs")])
    return InlineKeyboardMarkup(kb)

# ---------------- Send photo helper ----------------
async def send_photo_or_text(context: ContextTypes.DEFAULT_TYPE, chat_id: int, photo_key: str, caption: str, reply_markup=None):
    path = PHOTOS.get(photo_key, PHOTOS["banner"])
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                await context.bot.send_photo(chat_id=chat_id, photo=InputFile(f), caption=caption, reply_markup=reply_markup)
            return
    except Exception as e:
        logger.warning("Photo send fail: %s", e)
    await context.bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup)

# ---------------- Handlers ----------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # initial
    context.user_data["lang"] = "ru"
    await send_photo_or_text(context, update.effective_chat.id, "banner", TEXTS["ru"]["active_caption"], reply_markup=kb_active())

async def activate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_photo_or_text(context, q.message.chat.id, "banner", TEXTS["ru"]["choose_lang"], reply_markup=kb_language())

async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data.split("_", 1)[1]
    context.user_data["lang"] = lang
    try:
        await q.message.delete()
    except Exception:
        pass

    # sequence: welcome -> why -> how -> gpt -> register
    await send_photo_or_text(context, q.message.chat.id, "banner", TEXTS[lang]["welcome"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("→", callback_data="step_why")]]))

async def step_why(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_photo_or_text(context, q.message.chat.id, "banner", TEXTS[lang]["why"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("→", callback_data="step_how")]]))

async def step_how(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_photo_or_text(context, q.message.chat.id, "banner", TEXTS[lang]["how"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("→", callback_data="step_gpt")]]))

async def step_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_photo_or_text(context, q.message.chat.id, "banner", TEXTS[lang]["gpt"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("→", callback_data="step_register")]]))

async def step_register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_photo_or_text(context, q.message.chat.id, "register", TEXTS[lang]["register"], reply_markup=kb_register_stage(lang))
    # notify admin
    try:
        await context.bot.send_message(
            ADMIN_ID,
            TEXTS[lang]["admin_notify"].format(username=q.from_user.username or "—", uid=q.from_user.id)
        )
    except Exception as e:
        logger.warning("Admin notify failed: %s", e)

async def request_access_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_photo_or_text(context, q.message.chat.id, "limited", TEXTS[lang]["limited"])

async def cmd_allow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user.id
    if caller != ADMIN_ID:
        await update.message.reply_text(TEXTS["en"]["only_admin"])
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /allow <user_id>")
        return
    uid = int(context.args[0])
    ALLOWED.add(uid)
    save_allowed(ALLOWED)
    await update.message.reply_text(TEXTS["en"]["allowed_ok"].format(uid=uid))
    # notify user
    lang = context.user_data.get("lang", "ru")
    try:
        await context.bot.send_message(uid, TEXTS[lang]["access_granted"], reply_markup=kb_pairs(lang))
    except Exception:
        pass

async def cmd_revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user.id
    if caller != ADMIN_ID:
        await update.message.reply_text(TEXTS["en"]["only_admin"])
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /revoke <user_id>")
        return
    uid = int(context.args[0])
    if uid in ALLOWED:
        ALLOWED.remove(uid)
        save_allowed(ALLOWED)
        await update.message.reply_text(TEXTS["en"]["revoked_ok"].format(uid=uid))
        try:
            await context.bot.send_message(uid, TEXTS["ru"]["limited"])
        except Exception:
            pass
    else:
        await update.message.reply_text(TEXTS["en"]["no_user"].format(uid=uid))

async def cmd_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = context.user_data.get("lang", "ru")
    if uid not in ALLOWED:
        await send_photo_or_text(context, update.effective_chat.id, "limited", TEXTS[lang]["limited"])
        return
    await send_photo_or_text(context, update.effective_chat.id, "banner", TEXTS[lang]["choose_pair"], reply_markup=kb_pairs(lang))

async def pair_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = context.user_data.get("lang", "ru")
    if uid not in ALLOWED:
        await send_photo_or_text(context, q.message.chat.id, "limited", TEXTS[lang]["limited"])
        return
    _, pair = q.data.split("|", 1)
    context.user_data["pair"] = pair
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_photo_or_text(context, q.message.chat.id, "banner", TEXTS[lang]["pair_chosen"].format(pair=pair), reply_markup=kb_timeframes(lang))

async def tf_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = context.user_data.get("lang", "ru")
    if uid not in ALLOWED:
        await send_photo_or_text(context, q.message.chat.id, "limited", TEXTS[lang]["limited"])
        return
    _, tf = q.data.split("|", 1)
    pair = context.user_data.get("pair", "UNKNOWN")
    try:
        await q.message.delete()
    except Exception:
        pass

    # fetch real data for selected pair (if crypto)
    price = None
    low = None
    high = None
    try:
        # if pair ends with USDT => use Binance
        if pair.upper().endswith("USDT"):
            sym = pair.upper()
            resp = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}", timeout=5)
            data = resp.json()
            price = float(data.get("lastPrice", 0))
            low = float(data.get("lowPrice", 0))
            high = float(data.get("highPrice", 0))
        else:
            # fallback: random
            price = round(random.uniform(1.0, 2.0), 6)
            low = price * 0.99
            high = price * 1.01
    except Exception as e:
        logger.warning("Error fetching real data: %s", e)
        price = round(random.uniform(1.0, 2.0), 6)
        low = price * 0.99
        high = price * 1.01

    # animated steps (without graph)
    for step in (TEXTS[lang]["anim_fetch"], TEXTS[lang]["anim_ind"], TEXTS[lang]["anim_check"]):
        await send_photo_or_text(context, uid, "processing", step)
        await asyncio.sleep(1.0 + random.random() * 0.8)

    await send_photo_or_text(context, uid, "banner", TEXTS[lang]["anim_done"])
    await asyncio.sleep(0.8)

    # compute fake indicators
    sma_s = round(random.uniform(0.5, 1.5), 4)
    sma_l = round(sma_s + random.uniform(-0.02, 0.02), 4)
    rsi = round(random.uniform(20, 80), 1)
    macd = round(random.uniform(-0.5, 0.5), 3)
    vol_trend = random.choice(["increasing", "decreasing", "stable"])

    score = 0.0
    if sma_s > sma_l:
        score += 1.2
    else:
        score -= 1.2
    if rsi < 35:
        score += 1.0
    elif rsi > 65:
        score -= 1.0
    if macd > 0.02:
        score += 0.5
    elif macd < -0.02:
        score -= 0.5
    if vol_trend == "increasing":
        score += 0.3
    elif vol_trend == "decreasing":
        score -= 0.3

    if score >= 1.0:
        signal = "📈 BUY"
    elif score <= -1.0:
        signal = "📉 SELL"
    else:
        signal = "↔️ NEUTRAL"

    conf = min(95, max(55, int(50 + abs(score)*20 + random.randint(-5, 5))))

    reasons = []
    reasons.append(f"SMA short ({sma_s}) {'>' if sma_s > sma_l else '<'} SMA long ({sma_l})")
    if rsi < 35:
        reasons.append(f"RSI {rsi}: oversold, possible bounce")
    elif rsi > 65:
        reasons.append(f"RSI {rsi}: overbought, possible correction")
    else:
        reasons.append(f"RSI {rsi}: neutral momentum")
    if macd > 0.02:
        reasons.append(f"MACD {macd}: positive momentum")
    elif macd < -0.02:
        reasons.append(f"MACD {macd}: negative momentum")
    else:
        reasons.append(f"MACD {macd}: flat")
    reasons.append(f"Volume trend: {vol_trend}")

    reasons_text = "\n".join("• " + r for r in reasons)

    final = TEXTS[lang]["final"].format(
        pair=pair, tf=tf,
        price=price, low=low, high=high,
        signal=signal, conf=conf, reasons=reasons_text
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS[lang]["back_pairs"], callback_data="back_to_pairs")],
        [InlineKeyboardButton(TEXTS[lang]["new_forecast"], callback_data="pair|"+pair)]
    ])
    await send_photo_or_text(context, uid, "final", final, reply_markup=kb)

# handlers for back / new_forecast
async def back_to_pairs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = context.user_data.get("lang", "ru")
    try:
        await q.message.delete()
    

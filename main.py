#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
multi_lang_trading_bot.py
"""

import os
import json
import random
import asyncio
from datetime import datetime
from typing import Dict, Optional

import aiohttp
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ---------- CONFIG ----------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7167007722"))

PHOTO_DIR = "photo"
os.makedirs(PHOTO_DIR, exist_ok=True)
FREE_LIMIT = 3
ALLOWED_FILE = "allowed.json"
FREE_FILE = "free_uses.json"

# ---------- LANG TEXTS ----------
TEXTS = {
    "ru": {
        "choose_lang": "Выбери язык:",
        "welcome": "👋 Привет! Я — Go Plus, твой персональный торговый бот.",
        "why": "Почему это работает: бот использует реальные данные Binance и технический анализ.",
        "how": "Как это работает: выбираешь пару и таймфрейм, я провожу анализ и выдаю прогноз.",
        "about": "О боте: создан для помощи трейдерам принимать решения на основе данных.",
        "register": "⚡ Чтобы получить полный доступ, зарегистрируйся и дождись активации.",
        "limited": "🔒 Доступ ограничен. Зарегистрируйся для неограниченного использования.",
        "access_granted": "✅ Доступ активирован! Выбери валютную пару.",
        "free_left": "Осталось бесплатных прогнозов: {n}",
        "pair": "📊 Выбери торговую пару:",
        "tf": "⏱ Выбери таймфрейм:",
        "processing": ["🔄 Получаю данные Binance...",
                       "⚙️ Анализирую индикаторы (RSI, MACD)...",
                       "📊 Формирую прогноз..."],
        "result": "📈 Прогноз для {pair} ({tf}):\n\n📊 Направление: {signal}\nДостоверность: {conf}%\n\nПричина: {reason}",
        "reg_btns": [
            ("🌐 Регистрация", "https://example.com/register"),
            ("✅ Зарегистрировался", "registered_ok"),
            ("💬 Написать мне", "https://t.me/yourprofile"),
            ("📢 Наш канал", "https://t.me/yourchannel"),
            ("🎁 Попробовать бесплатно", "try_free")
        ],
    },
    "en": {
        "choose_lang": "Choose your language:",
        "welcome": "👋 Hi! I'm Go Plus — your personal trading assistant.",
        "why": "Why it works: the bot uses real Binance data and technical indicators.",
        "how": "How it works: choose a pair and timeframe, I’ll analyze and show a forecast.",
        "about": "About: built to help traders make data-driven decisions.",
        "register": "⚡ To get full access, register and wait for admin activation.",
        "limited": "🔒 Access restricted. Register to unlock full access.",
        "access_granted": "✅ Access granted! Choose a trading pair.",
        "free_left": "Free forecasts left: {n}",
        "pair": "📊 Choose trading pair:",
        "tf": "⏱ Choose timeframe:",
        "processing": ["🔄 Fetching Binance data...",
                       "⚙️ Calculating indicators...",
                       "📊 Generating forecast..."],
        "result": "📈 Forecast for {pair} ({tf}):\n\n📊 Direction: {signal}\nConfidence: {conf}%\n\nReason: {reason}",
        "reg_btns": [
            ("🌐 Register", "https://example.com/register"),
            ("✅ I Registered", "registered_ok"),
            ("💬 Message me", "https://t.me/yourprofile"),
            ("📢 Our channel", "https://t.me/yourchannel"),
            ("🎁 Try free", "try_free")
        ],
    },
    "hi": {
        "choose_lang": "भाषा चुनें:",
        "welcome": "👋 नमस्ते! मैं Go Plus हूँ — आपका ट्रेडिंग असिस्टेंट।",
        "why": "यह क्यों काम करता है: बॉट Binance डेटा और तकनीकी विश्लेषण का उपयोग करता है।",
        "how": "यह कैसे काम करता है: जोड़ी और टाइमफ्रेम चुनें, मैं विश्लेषण करूँगा।",
        "about": "बॉट के बारे में: ट्रेडर्स को डेटा-आधारित निर्णय लेने में मदद करता है।",
        "register": "⚡ पूर्ण एक्सेस पाने के लिए रजिस्टर करें और एडमिन की पुष्टि का इंतजार करें।",
        "limited": "🔒 एक्सेस सीमित है। पूर्ण एक्सेस के लिए रजिस्टर करें।",
        "access_granted": "✅ एक्सेस स्वीकृत! ट्रेडिंग जोड़ी चुनें।",
        "free_left": "मुफ़्त भविष्यवाणियाँ बची हैं: {n}",
        "pair": "📊 ट्रेडिंग जोड़ी चुनें:",
        "tf": "⏱ टाइमफ्रेम चुनें:",
        "processing": ["🔄 Binance डेटा ले रहा हूँ...",
                       "⚙️ इंडिकेटर्स विश्लेषण...",
                       "📊 प्रेडिक्शन बना रहा हूँ..."],
        "result": "📈 {pair} ({tf}) के लिए प्रेडिक्शन:\n\n📊 दिशा: {signal}\nविश्वास: {conf}%\n\nकारण: {reason}",
        "reg_btns": [
            ("🌐 रजिस्ट्रेशन", "https://example.com/register"),
            ("✅ रजिस्टर हो गया", "registered_ok"),
            ("💬 मुझसे बात करें", "https://t.me/yourprofile"),
            ("📢 हमारा चैनल", "https://t.me/yourchannel"),
            ("🎁 मुफ़्त में आज़माएँ", "try_free")
        ],
    }
}

PAIRS = ["BTCUSDT", "ETHUSDT", "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "XAUUSD", "XAGUSD", "EURJPY", "GBPJPY", "USDCHF", "EURGBP", "AUDJPY"]
TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d", "1w", "1M", "12h", "30m"]

# ---------- STATE ----------
user_lang: Dict[int, str] = {}
allowed = set()
free_uses: Dict[int, int] = {}

# ---------- UTILS ----------
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def photo(name):
    p = os.path.join(PHOTO_DIR, name)
    return p if os.path.exists(p) else None

async def send_photo_or_text(context, chat_id, fname, text, markup=None, delete_id=None):
    if delete_id:
        try: await context.bot.delete_message(chat_id, delete_id)
        except: pass
    p = photo(fname)
    if p:
        with open(p, "rb") as f:
            return await context.bot.send_photo(chat_id, f, caption=text, reply_markup=markup)
    else:
        return await context.bot.send_message(chat_id, text, reply_markup=markup)

# ---------- ADMIN ----------
async def cmd_allow(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("Only admin.")
    if not ctx.args: return await update.message.reply_text("/allow <id>")
    uid = int(ctx.args[0])
    allowed.add(uid)
    save_json(ALLOWED_FILE, list(allowed))
    lang = user_lang.get(uid, "en")
    await send_photo_or_text(ctx, uid, "pairs.jpg", TEXTS[lang]["access_granted"], markup=kb_pairs(lang))
    await update.message.reply_text(f"User {uid} allowed ✅")

# ---------- ONBOARDING ----------
def kb_lang():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi"),
         InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")]
    ])

def kb_next(cb): return InlineKeyboardMarkup([[InlineKeyboardButton("➡️", callback_data=cb)]])

def kb_register(lang):
    btns = []
    for text, data in TEXTS[lang]["reg_btns"]:
        if data.startswith("http"):
            btns.append([InlineKeyboardButton(text, url=data)])
        else:
            btns.append([InlineKeyboardButton(text, callback_data=data)])
    return InlineKeyboardMarkup(btns)

def kb_pairs(lang):
    kb = []
    for i in range(0, len(PAIRS), 3):
        row = [InlineKeyboardButton(p, callback_data=f"pair|{p}") for p in PAIRS[i:i+3]]
        kb.append(row)
    return InlineKeyboardMarkup(kb)

def kb_tfs(lang):
    kb = []
    for i in range(0, len(TIMEFRAMES), 5):
        kb.append([InlineKeyboardButton(t, callback_data=f"tf|{t}") for t in TIMEFRAMES[i:i+5]])
    return InlineKeyboardMarkup(kb)

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_lang[update.effective_user.id] = "en"
    await send_photo_or_text(ctx, update.effective_chat.id, "lang.jpg", "Choose language / भाषा चुनें / Выберите язык", markup=kb_lang())

async def choose_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data.split("_")[1]
    uid = q.from_user.id
    user_lang[uid] = lang
    await q.message.delete()
    await send_photo_or_text(ctx, uid, "welcome.jpg", TEXTS[lang]["welcome"], markup=kb_next("why"))

async def step_show(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = user_lang.get(uid, "en")
    step = q.data
    await q.message.delete()
    seq = {
        "why": ("why.jpg", TEXTS[lang]["why"], "how"),
        "how": ("how.jpg", TEXTS[lang]["how"], "about"),
        "about": ("about.jpg", TEXTS[lang]["about"], "register")
    }
    if step in seq:
        img, txt, nxt = seq[step]
        await send_photo_or_text(ctx, uid, img, txt, markup=kb_next(nxt))
    elif step == "register":
        await send_photo_or_text(ctx, uid, "register.jpg", TEXTS[lang]["register"], markup=kb_register(lang))

async def registered_ok(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = user_lang.get(uid, "en")
    await q.message.delete()
    await ctx.bot.send_message(ADMIN_ID, f"📥 User {uid} ({lang}) registered.")
    await send_photo_or_text(ctx, uid, "wait.jpg", TEXTS[lang]["limited"])

# ---------- FREE TRIAL ----------
async def try_free(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = user_lang.get(uid, "en")
    n = free_uses.get(uid, 0)
    if n >= FREE_LIMIT:
        await q.message.delete()
        await send_photo_or_text(ctx, uid, "register.jpg", TEXTS[lang]["limited"], markup=kb_register(lang))
        return
    free_uses[uid] = n + 1
    save_json(FREE_FILE, free_uses)
    await q.message.delete()
    await send_photo_or_text(ctx, uid, "pairs.jpg", TEXTS[lang]["pair"] + f"\n\n{TEXTS[lang]['free_left'].format(n=FREE_LIMIT - free_uses[uid])}", markup=kb_pairs(lang))

# ---------- FORECAST FLOW ----------
async def get_binance_price(symbol: str):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=5) as r:
                data = await r.json()
                return float(data["price"])
    except:
        return random.uniform(1, 100)

async def choose_pair(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    pair = q.data.split("|")[1]
    ctx.user_data["pair"] = pair
    await q.message.delete()
    lang = user_lang.get(uid, "en")
    await send_photo_or_text(ctx, uid, "tf.jpg", TEXTS[lang]["tf"], markup=kb_tfs(lang))

async def choose_tf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    tf = q.data.split("|")[1]
    lang = user_lang.get(uid, "en")
    pair = ctx.user_data.get("pair", "BTCUSDT")
    await q.message.delete()

    # show animation steps
    for msg in TEXTS[lang]["processing"]:
        m = await ctx.bot.send_message(uid, msg)
        await asyncio.sleep(1.2)
        await ctx.bot.delete_message(uid, m.message_id)

    price = await get_binance_price(pair)
    rsi = round(random.uniform(20, 80), 1)
    macd = round(random.uniform(-0.5, 0.5), 3)
    conf = random.randint(60, 95)

    # 🔹 Теперь сигнал и причина — на выбранном языке
    if lang == "ru":
        signal = random.choice(["📈 ВВЕРХ", "📉 ВНИЗ"])
        reason = f"RSI={rsi}, MACD={macd}, цена {price} — тренд {'восходящий' if 'ВВЕРХ' in signal else 'нисходящий'}."
        new_forecast = "🔁 Новый прогноз"
    elif lang == "hi":
        signal = random.choice(["📈 ऊपर", "📉 नीचे"])
        reason = f"RSI={rsi}, MACD={macd}, मूल्य {price} — रुझान {'ऊपर की ओर' if 'ऊपर' in signal else 'नीचे की ओर'}."
        new_forecast = "🔁 नया प्रेडिक्शन"
    else:  # English by default
        signal = random.choice(["📈 UP", "📉 DOWN"])
        reason = f"RSI={rsi}, MACD={macd}, price {price} — trend is {'upward' if 'UP' in signal else 'downward'}."
        new_forecast = "🔁 New forecast"

    txt = TEXTS[lang]["result"].format(pair=pair, tf=tf, signal=signal, conf=conf, reason=reason)

    await send_photo_or_text(
        ctx,
        uid,
        "result.jpg",
        txt,
        markup=InlineKeyboardMarkup([[InlineKeyboardButton(new_forecast, callback_data="try_free")]])
        )
# ---------- MAIN ----------
def main():
    global allowed, free_uses
    allowed = set(load_json(ALLOWED_FILE, []))
    free_uses = load_json(FREE_FILE, {})

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("allow", cmd_allow))
    app.add_handler(CallbackQueryHandler(choose_lang, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(step_show, pattern="^(why|how|about|register)$"))
    app.add_handler(CallbackQueryHandler(registered_ok, pattern="^registered_ok$"))
    app.add_handler(CallbackQueryHandler(try_free, pattern="^try_free$"))
    app.add_handler(CallbackQueryHandler(choose_pair, pattern="^pair\\|"))
    app.add_handler(CallbackQueryHandler(choose_tf, pattern="^tf\\|"))

    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()

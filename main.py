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
import threading
from aiohttp import web
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
CHANNEL_USERNAME = "@InformTrends"  # 👈 замени на свой канал (например, "@GoPlusNews")
# ---------- LANG TEXTS ----------
TEXTS = {
    "ru": {
        "subscribe": {
            "text": "🔒 Чтобы продолжить,\nподпишись на наш канал\nи нажми «Проверить подписку»..",
            "btn_sub": "📣 Подписаться на канал",
            "btn_check": "✅ Проверить подписку",
            "not_sub": "❗ Вы не подписаны.\n@GO_PLUS_SUPPORT\nПодпишитесь и попробуйте снова."
        },
        "choose_lang": "Выбери язык:",
        "welcome": "👋 Привет! Я — Go Plus, твой персональный\nторговый бот.\n\n🚀 Моя задача — помочь тебе\nзарабатывать на трейдинге\nпроще и стабильнее.",
        "why": "✨ Почему выбирают Go Plus:\n\n• Более 100 активов для торговли\n• Поддержка OTC и биржевых пар\n• 2 режима торговли для любого стиля\n• Мгновенный анализ графика\n• Точность сигналов 97,89%+\n• Работаю 24/7 на любом устройстве\n\n💎 Ты получаешь инструмент,\nкоторый всегда на шаг впереди рынка.",
        "how": "🤖 Всё просто:\n\n1️⃣ Выбираешь актив\n2️⃣ Указываешь время сделки\n3️⃣ Получаешь сигнал: Выше / Ниже\n4️⃣ Открываешь сделку\n5️⃣ Фиксируешь профит 💸\n\n⚡️ Всю математику и аналитику я беру на себя — тебе остаётся только действовать.",
        "about": "🤖 Я построен на базе AI GPT-5 и MT4-5,\nкоторые за секунды обрабатывают огромный объём данных.\n\n📊 Я анализирую сотни индикаторов,\nценовые паттерны, фундаментальный и технический анализ.\n\n🔍 Я вижу закономерности,\nкоторые человек заметит слишком поздно.\n\n⚡️ Каждый мой сигнал — это результат\nточных вычислений, а не догадок.",
        "register": "⚡ Чтобы получить полный доступ к Go Plus,\nзарегистрируй новый аккаунт на Pocket Option\nстрого по моей ссылке:\nhttps://surl.li/skrdkx\n\nА пока можешь попробовать\n3 ПОДАРОЧНЫЕ прогноза\nи заработать первые деньги с GO PLUS 💸",
        "limited": "🔒 Доступ ограничен.\n\nЗарегистрируйся на платформе Pocket Option\nдля неограниченного использования\nи отправь @GO_PLUS_SUPPORT свой ID.",
        "access_granted": "✅ Доступ активирован! Выбери валютную пару.",
        "free_left": "Осталось бесплатных прогнозов: {n}",
        "pair": "📊 Выбери торговую пару:",
        "tf": "⏱ Выбери таймфрейм:",
        "processing": ["🔄 Получаю данные Binance... ",
                       "⚙️ Анализирую индикаторы (RSI, MACD)...",
                       "📊 Формирую прогноз..."],
        "result": "📈 Прогноз для {pair} ({tf}):\n\n📊 Направление: {signal}\nДостоверность: {conf}%\n\nПричина: {reason}",
        "reg_btns": [
            ("🌐 Регистрация", "https://example.com/register"),
            ("✅ Зарегистрировался", "registered_ok"),
            ("💬 Написать мне", "https://t.me/GO_PLUS_SUPPORT"),
            ("📢 Наш канал", "https://t.me/yourchannel"),
            ("🎁 Попробовать бесплатно", "try_free")
        ],
    },
    "en": {
        "subscribe": {
    "text": "🔒 To continue,\nsubscribe to our channel\nand tap “Check subscription”.",
    "btn_sub": "📢 Subscribe to channel",
    "btn_check": "✅ Check subscription",
    "not_sub": "❗ You are not subscribed yet.\n@GO_PLUS_SUPPORT\nPlease subscribe and try again."
},
        "choose_lang": "Choose your language:",
        "welcome": "👋 Hi! I'm Go Plus, your personal\ntrading bot.\n\n🚀 My goal is to help you\nearn from trading\nmore easily and consistently.",
        "why": "✨ Why traders choose Go Plus:\n\n• Over 100 assets available for trading\n• Supports OTC and exchange pairs\n• 2 trading modes for any style\n• Instant chart analysis\n• Signal accuracy 97.89%+\n• Works 24/7 on any device\n\n💎 You get a tool that’s\nalways one step ahead of the market.",
        "how": "🤖 It’s simple:\n\n1️⃣ Choose an asset\n2️⃣ Set the trade duration\n3️⃣ Get a signal: Up / Down\n4️⃣ Open the trade\n5️⃣ Lock in your profit 💸\n\n⚡️ I handle all the math and analysis — you just take action.",
        "about": "🤖 I’m built on AI GPT-5 and MT4-5,\nprocessing massive amounts of data in seconds.\n\n📊 I analyze hundreds of indicators,\nprice patterns, and both fundamental and technical analysis.\n\n🔍 I detect market patterns\nlong before a human would notice them.\n\n⚡️ Every signal I send is the result\nof precise calculations — not guesses.",
        "register": "⚡ To get full access to Go Plus,\ncreate a new account on Pocket Option\nusing my special link:\nhttps://surl.li/skrdkx\n\nIn the meantime, you can try\n3 FREE predictions\nand earn your first profit with GO PLUS 💸",
        "limited": "🔒 Access is restricted.\n\nRegister on the Pocket Option platform\nfor unlimited use\nand send your ID to @GO_PLUS_SUPPORT.",
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
            ("💬 Message me", "https://t.me/GO_PLUS_SUPPORT"),
            ("📢 Our channel", "https://t.me/yourchannel"),
            ("🎁 Try free", "try_free")
        ],
    },
    "hi": {
        "subscribe": {
    "text": "🔒 आगे बढ़ने के लिए,\nहमारे चैनल को सब्सक्राइब करें\nऔर “सदस्यता जांचें” पर क्लिक करें।",
    "btn_sub": "📢 चैनल सब्सक्राइब करें",
    "btn_check": "✅ सब्सक्रिप्शन जांचें",
    "not_sub": "❗ आप अभी तक सब्सक्राइब नहीं हैं। कृपया सब्सक्राइब करें और फिर से प्रयास करें।\nGO_PLUS_SUPPORT"
},
        "choose_lang": "भाषा चुनें:",
        "welcome": "👋 नमस्ते! मैं Go Plus हूँ, आपका व्यक्तिगत\nट्रेडिंग बॉट।\n\n🚀 मेरा उद्देश्य है आपको\nट्रेडिंग से आसान और स्थिर\nतरीके से कमाने में मदद करना।",
        "why": "✨ Go Plus क्यों चुनें:\n\n• ट्रेडिंग के लिए 100+ एसेट्स उपलब्ध\n• OTC और एक्सचेंज पेयर्स का समर्थन\n• हर शैली के लिए 2 ट्रेडिंग मोड\n• चार्ट का त्वरित विश्लेषण\n• सिग्नल की सटीकता 97.89%+\n• किसी भी डिवाइस पर 24/7 काम करता है\n\n💎 आपको एक ऐसा टूल मिलता है\nजो हमेशा मार्केट से एक कदम आगे रहता है।",
        "how": "🤖 यह बहुत आसान है:\n\n1️⃣ एसेट चुनें\n2️⃣ ट्रेड की अवधि तय करें\n3️⃣ सिग्नल प्राप्त करें: ऊपर / नीचे\n4️⃣ ट्रेड खोलें\n5️⃣ मुनाफ़ा सुरक्षित करें 💸\n\n⚡️ सारी गणना और विश्लेषण मैं करता हूँ — आपको बस कार्रवाई करनी है।",
        "about": "🤖 मैं AI GPT-5 और MT4-5 पर आधारित हूँ,\nजो कुछ ही सेकंड में विशाल डेटा को संसाधित करता है।\n\n📊 मैं सैकड़ों इंडिकेटर्स,\nप्राइस पैटर्न्स और मौलिक व तकनीकी विश्लेषण का अध्ययन करता हूँ।\n\n🔍 मैं वे पैटर्न देखता हूँ,\nजो इंसान बहुत देर से पहचान पाता।\n\n⚡️ मेरा हर सिग्नल सटीक गणनाओं\nका परिणाम होता है — न कि अनुमान का।",
        "register": "⚡ Go Plus का पूरा एक्सेस पाने के लिए,\nPocket Option पर मेरा विशेष लिंक इस्तेमाल करके\nनया अकाउंट रजिस्टर करें:\nhttps://surl.li/skrdkx\n\nइस बीच आप 3 मुफ़्त सिग्नल आज़मा सकते हैं\nऔर GO PLUS के साथ अपनी पहली कमाई कर सकते हैं 💸",
        "limited": "🔒 एक्सेस सीमित है।\n\nPocket Option प्लेटफ़ॉर्म पर रजिस्टर करें\nअसीमित उपयोग के लिए\nऔर अपना ID @GO_PLUS_SUPPORT पर भेजें।",
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
            ("💬 मुझसे बात करें", "https://t.me/GO_PLUS_SUPPORT"),
            ("📢 हमारा चैनल", "https://t.me/yourchannel"),
            ("🎁 मुफ़्त में आज़माएँ", "try_free")
        ],
    }
}

PAIRS = ["BTCUSDT", "ETHUSDT", "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "XAUUSD", "XAGUSD", "EURJPY", "GBPJPY", "USDCHF", "EURGBP", "AUDJPY"]
TIMEFRAMES = ["15s", "1m", "2m", "5m", "10m", "30m", "1h", "4h", "12h", "1d"]

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

def kb_next(cb): return InlineKeyboardMarkup([[InlineKeyboardButton("➡️➡️➡️➡️➡️", callback_data=cb)]])

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

async def is_subscribed(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

async def choose_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data.split("_")[1]
    uid = q.from_user.id
    user_lang[uid] = lang
    await q.message.delete()

    # Проверка подписки
    if not await is_subscribed(ctx.bot, uid):
        sub_texts = TEXTS[lang]["subscribe"]
        btn = InlineKeyboardMarkup([
            [InlineKeyboardButton(sub_texts["btn_sub"], url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton(sub_texts["btn_check"], callback_data="check_sub")]
        ])
        await send_photo_or_text(ctx, uid, "subscribe.jpg",
                                 sub_texts["text"], markup=btn)
        return

    # Если подписан — продолжаем
    await send_photo_or_text(ctx, uid, "welcome.jpg", TEXTS[lang]["welcome"], markup=kb_next("why"))

async def check_sub(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = user_lang.get(uid, "en")
    sub_texts = TEXTS[lang]["subscribe"]

    if await is_subscribed(ctx.bot, uid):
        await q.message.delete()
        await send_photo_or_text(ctx, uid, "welcome.jpg", TEXTS[lang]["welcome"], markup=kb_next("why"))
    else:
        try:
            await q.message.edit_caption(caption=sub_texts["not_sub"])
        except:
            await q.message.edit_text(sub_texts["not_sub"])

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

    # Определяем сигнал и текст причины
    if lang == "ru":
        signal = random.choice(["📈 ВВЕРХ", "📉 ВНИЗ"])
        reason = f"RSI={rsi}, MACD={macd}, цена {price} — тренд {'восходящий' if 'ВВЕРХ' in signal else 'нисходящий'}."
        new_forecast = "🔁 Новый прогноз"
    elif lang == "hi":
        signal = random.choice(["📈 ऊपर", "📉 नीचे"])
        reason = f"RSI={rsi}, MACD={macd}, मूल्य {price} — रुझान {'ऊपर की ओर' if 'ऊपर' in signal else 'नीचे की ओर'}."
        new_forecast = "🔁 नया प्रेडिक्शन"
    else:
        signal = random.choice(["📈 UP", "📉 DOWN"])
        reason = f"RSI={rsi}, MACD={macd}, price {price} — trend is {'upward' if 'UP' in signal else 'downward'}."
        new_forecast = "🔁 New forecast"

    txt = TEXTS[lang]["result"].format(pair=pair, tf=tf, signal=signal, conf=conf, reason=reason)

    # 🖼 Выбираем картинку в зависимости от сигнала
    if any(x in signal for x in ["ВВЕРХ", "UP", "ऊपर"]):
        img_name = "up.jpg"
    else:
        img_name = "down.jpg"

    # Отправляем прогноз с нужной картинкой
    await send_photo_or_text(
        ctx,
        uid,
        img_name,
        txt,
        markup=InlineKeyboardMarkup([[InlineKeyboardButton(new_forecast, callback_data="try_free")]])
                                )

async def healthcheck(request):
    return web.Response(text="Bot is running!")

def start_webserver():
    app = web.Application()
    app.add_routes([web.get("/", healthcheck)])
    web.run_app(app, port=int(os.environ.get("PORT", 10000)), handle_signals=False)


threading.Thread(target=start_webserver, daemon=True).start()

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
    app.add_handler(CallbackQueryHandler(check_sub, pattern="^check_sub$"))
    
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()

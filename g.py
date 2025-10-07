#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOPLUS — full flow bot (multilang) with:
- start -> ACTIVE -> language -> Start/How/Why/GPT/Register flow -> auto-send admin user id
- manual admin approval: /allow <id> and /revoke <id>
- 20 trading pairs, 15 timeframes
- step-by-step animated analysis (text) — each step accompanied by a local image (photo/banner.jpg by default)
- old messages deleted for clean UI
- persistence of allowed users to allowed_users.json
"""

import os
import json
import asyncio
import logging
import random
from datetime import datetime
from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
)

# ---------------- Config ----------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "7816419974:AAGDTqScu5OE2KvmGNPZA-BBYov0XnQCmgI")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7167007722"))

POCKET_LINK = os.getenv("POCKET_LINK", "https://bit.ly/pocket-option-rus")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/your_channel")
SUPPORT_BOT = os.getenv("SUPPORT_BOT", "https://t.me/G0_PLUS_SUPPORTBOT")

# photo files (you can replace them later in the photo/ folder)
PHOTOS = {
    "banner": "photo/banner.jpg",         # used for steps (default single image)
    "start":  "photo/banner.jpg",         # fallbacks to banner
    "lang":   "photo/banner.jpg",
    "intro":  "photo/banner.jpg",
    "why":    "photo/banner.jpg",
    "how":    "photo/banner.jpg",
    "gpt":    "photo/banner.jpg",
    "register":"photo/banner.jpg",
    "limited":"photo/banner.jpg",
    "processing":"photo/banner.jpg",
    "final":  "photo/banner.jpg",
}

# allowed users persistence
ALLOWED_FILE = "allowed_users.json"

# Pairs (20) and Timeframes (15)
PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD",
    "USD/CAD", "NZD/USD", "EUR/JPY", "GBP/JPY", "EUR/GBP",
    "BTC/USD", "ETH/USD", "LTC/USD", "XAU/USD", "XAG/USD",
    "USD/TRY", "USD/ZAR", "EUR/CHF", "GBP/CHF", "AUD/JPY",
]

TIMEFRAMES = [
    "15 sec", "30 sec", "1 min", "2 min", "5 min", "10 min", "15 min", "30 min",
    "1 hour", "2 hours", "4 hours", "8 hours", "12 hours", "1 day", "1 week"
]

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("goplus")

# ---------------- Multilang texts ----------------
TEXTS = {
    "ru": {
        "choose_lang": "Выбери язык:",
        "active_caption": "👋 Добро пожаловать! Нажмите ACTIVE чтобы начать.",
        "welcome": "👋 Привет! Я — Go Plus, твой персональный торговый бот.",
        "why": "✨ Почему выбирают Go Plus:\n• Более 100 активов\n• Поддержка OTC\n• 2 режима торговли\n• Мгновенный анализ",
        "how": "🤖 Как это работает:\n1) Выбираешь актив\n2) Указываешь время\n3) Получаешь сигнал\n4) Фиксируешь профит",
        "gpt": "🤖 Мощный аналитический модуль — обрабатываю сотни сигналов за секунды.",
        "register": f"⚡ Чтобы получить доступ, зарегистрируйся по ссылке:\n{POCKET_LINK}\n\nПосле регистрации — дождись активации (админ получит ваш ID).",
        "limited": "🔒 Доступ ограничен. Ожидайте активации от администрации.",
        "access_granted": "✅ Доступ активирован! Теперь выберите торговую пару:",
        "choose_pair": "📊 Выберите торговую пару:",
        "choose_tf": "⏱ Выберите таймфрейм:",
        "pair_chosen": "Пара выбрана: {pair}\nТеперь выберите таймфрейм:",
        "time_chosen": "Таймфрейм выбран: {time}\n\nНачинаю анализ...",
        "anim_fetch": "🔄 Получаю последние данные...",
        "anim_ind": "⚙️ Вычисляю индикаторы (SMA, RSI, MACD)...",
        "anim_check": "🔍 Сверяю сигналы и объёмы...",
        "anim_done": "✅ Анализ завершён!",
        "final": "📈 Прогноз — {pair} / {time}\n\nСигнал: {signal}\nДоверие: {conf}%\n\nПричины:\n{reasons}",
        "new_forecast": "Сделать новый прогноз",
        "back_pairs": "⬅️ НАЗАД",
        "admin_notify": "Новый пользователь @{username} (ID: {uid}) запросил доступ. Можешь дать /allow {uid}",
        "only_admin": "❌ Команда доступна только администратору.",
        "allowed_ok": "✅ Пользователь {uid} добавлен в разрешённые.",
        "revoked_ok": "✅ Доступ пользователя {uid} отозван.",
        "no_user": "❌ Пользователь {uid} не найден в разрешённых.",
        "getid": "Ваш Telegram ID: {uid}",
    },
    "en": {
        "choose_lang": "Choose your language:",
        "active_caption": "👋 Welcome! Press ACTIVE to begin.",
        "welcome": "👋 Hi — I'm Go Plus, your personal trading bot.",
        "why": "✨ Why choose Go Plus:\n• 100+ assets\n• OTC support\n• 2 trading modes\n• Instant analysis",
        "how": "🤖 How it works:\n1) Choose asset\n2) Select timeframe\n3) Get a signal\n4) Take profit",
        "gpt": "🤖 Powerful analytics engine — processing hundreds of signals per second.",
        "register": f"⚡ To get access, register here:\n{POCKET_LINK}\n\nAfter registration, wait for admin activation.",
        "limited": "🔒 Access restricted. Wait for admin activation.",
        "access_granted": "✅ Access granted! Now choose a trading pair:",
        "choose_pair": "📊 Choose trading pair:",
        "choose_tf": "⏱ Choose timeframe:",
        "pair_chosen": "Pair selected: {pair}\nNow choose timeframe:",
        "time_chosen": "Timeframe selected: {time}\n\nStarting analysis...",
        "anim_fetch": "🔄 Fetching latest candles...",
        "anim_ind": "⚙️ Calculating indicators (SMA, RSI, MACD)...",
        "anim_check": "🔍 Checking signals & volumes...",
        "anim_done": "✅ Analysis complete!",
        "final": "📈 Forecast — {pair} / {time}\n\nSignal: {signal}\nConfidence: {conf}%\n\nReasons:\n{reasons}",
        "new_forecast": "Make new forecast",
        "back_pairs": "⬅️ BACK",
        "admin_notify": "New user @{username} (ID: {uid}) requested access. Approve with /allow {uid}",
        "only_admin": "❌ Command available to admin only.",
        "allowed_ok": "✅ User {uid} added to allowed list.",
        "revoked_ok": "✅ Access revoked for user {uid}.",
        "no_user": "❌ User {uid} not found in allowed list.",
        "getid": "Your Telegram ID: {uid}",
    },
    "hi": {
        "choose_lang": "भाषा चुनें:",
        "active_caption": "👋 स्वागत है! शुरू करने के लिए ACTIVE दबाएँ।",
        "welcome": "👋 नमस्ते — मैं Go Plus, आपका ट्रेडिंग बॉट।",
        "why": "✨ क्यों Go Plus:\n• 100+ एसेट्स\n• OTC सपोर्ट\n• 2 ट्रेडिंग मोड\n• त्वरित विश्लेषण",
        "how": "🤖 तरीका:\n1) एसेट चुनें\n2) टाइमफ्रेम चुनें\n3) सिग्नल पाएं\n4) प्रॉफिट लें",
        "gpt": "🤖 शक्तिशाली एनालिटिक्स — सैकड़ों सिग्नल प्रति सेकंड।",
        "register": f"⚡ एक्सेस पाने के लिए रजिस्टर करें:\n{POCKET_LINK}\n\nरजिस्ट्रेशन के बाद एडमिन सक्रिय करेगा।",
        "limited": "🔒 एक्सेस प्रतिबंधित है। एडमिन की अनुमति का इंतज़ार करें।",
        "access_granted": "✅ एक्सेस जारी! अब ट्रेडिंग जोड़ी चुनें:",
        "choose_pair": "📊 एक ट्रेडिंग जोड़ी चुनें:",
        "choose_tf": "⏱ टाइमफ्रेम चुनें:",
        "pair_chosen": "जोड़ी चुनी गई: {pair}\nअब टाइमफ्रेम चुनें:",
        "time_chosen": "टाइमफ्रेम चुना गया: {time}\n\nविश्लेषण शुरू कर रहा हूँ...",
        "anim_fetch": "🔄 कैंडल्स लाया जा रहा है...",
        "anim_ind": "⚙️ इंडिकेटर्स कैलकुलेट कर रहा हूँ (SMA, RSI, MACD)...",
        "anim_check": "🔍 सिग्नल और वॉल्यूम चेक कर रहा हूँ...",
        "anim_done": "✅ विश्लेषण पूरा!",
        "final": "📈 पूर्वानुमान — {pair} / {time}\n\nसिग्नल: {signal}\nविश्वास: {conf}%\n\nकारण:\n{reasons}",
        "new_forecast": "नया पूर्वानुमान करें",
        "back_pairs": "⬅️ वापस",
        "admin_notify": "नया उपयोगकर्ता @{username} (ID: {uid}) ने एक्सेस मांगा। /allow {uid}",
        "only_admin": "❌ यह कमान केवल एडमिन के लिए है।",
        "allowed_ok": "✅ उपयोगकर्ता {uid} को अनुमति दी गई।",
        "revoked_ok": "✅ उपयोगकर्ता {uid} की अनुमति रद्द की गई।",
        "no_user": "❌ उपयोगकर्ता {uid} अनुमति सूची में नहीं है।",
        "getid": "आपका Telegram ID: {uid}",
    }
}

# ---------------- Utilities: allowed users persistence ----------------
def load_allowed():
    if os.path.exists(ALLOWED_FILE):
        try:
            with open(ALLOWED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return set(int(x) for x in data.get("allowed", []))
        except Exception as e:
            logger.warning("Failed to load allowed file: %s", e)
            return set()
    return set()


def save_allowed(allowed_set):
    try:
        with open(ALLOWED_FILE, "w", encoding="utf-8") as f:
            json.dump({"allowed": list(allowed_set)}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Failed to save allowed file: %s", e)


ALLOWED_USERS = load_allowed()

# ---------------- Keyboards ----------------
def kb_active():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔵 ACTIVE", callback_data="activate")]])


def kb_language():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")]
    ])


def kb_start_flow(lang):
    # single big Start button
    return InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]["choose_lang"], callback_data="noop")]])


def kb_intro_start(lang):
    return InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang].get("active_caption", "Start"), callback_data="flow_start")]])


def kb_flow_step(next_label, callback):
    return InlineKeyboardMarkup([[InlineKeyboardButton(next_label, callback_data=callback)]])


def build_pairs_keyboard():
    kb = []
    # 4 per row
    for i in range(0, len(PAIRS), 4):
        row = [InlineKeyboardButton(p, callback_data=f"pair|{p}") for p in PAIRS[i:i+4]]
        kb.append(row)
    kb.append([InlineKeyboardButton(TEXTS["ru"]["back_pairs"], callback_data="back_to_intro")])
    return InlineKeyboardMarkup(kb)


def build_tfs_keyboard():
    kb = []
    for i in range(0, len(TIMEFRAMES), 5):
        row = [InlineKeyboardButton(tf, callback_data=f"tf|{tf}") for tf in TIMEFRAMES[i:i+5]]
        kb.append(row)
    kb.append([InlineKeyboardButton(TEXTS["ru"]["back_pairs"], callback_data="back_to_pairs")])
    return InlineKeyboardMarkup(kb)


# ---------------- Helper: send local photo with fallback ----------------
async def send_local_photo(context: ContextTypes.DEFAULT_TYPE, chat_id: int, photo_key: str, caption: str = None, reply_markup=None):
    path = PHOTOS.get(photo_key) or PHOTOS.get("banner")
    try:
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                await context.bot.send_photo(chat_id=chat_id, photo=InputFile(f), caption=caption or "", reply_markup=reply_markup)
            return
    except Exception as e:
        logger.warning("Failed to send local photo %s: %s", path, e)

    # fallback to text message if photo not available
    await context.bot.send_message(chat_id=chat_id, text=caption or "", reply_markup=reply_markup)


# ---------------- Handlers ----------------

# /start -> show activation image + ACTIVE button
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    # default language RU for the initial message
    lang = "ru"
    # store in user data for later
    context.user_data["lang"] = lang
    caption = TEXTS[lang]["active_caption"]
    await send_local_photo(context, update.effective_chat.id, "start", caption=caption, reply_markup=kb_active())


# ACTIVE pressed -> show language choices
async def activate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_local_photo(context, q.message.chat.id, "lang", caption=TEXTS["ru"]["choose_lang"], reply_markup=kb_language())


# Language chosen -> proceed to intro sequence (Start -> How -> Why -> GPT -> Register)
async def choose_lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = q.data.split("_", 1)[1]
    context.user_data["lang"] = lang
    user_id = q.from_user.id
    user_language = lang  # save for this session (not persisted across restarts)
    # delete previous
    try:
        await q.message.delete()
    except Exception:
        pass

    # Step 1: welcome + Start button
    caption = TEXTS[lang]["welcome"]
    await send_local_photo(context, q.message.chat.id, "intro", caption=caption, reply_markup=kb_flow_step(TEXTS[lang].get("active_caption", "Start"), "flow_start"))

    # store language mapping for admin notification/use
    # user_language_map kept in memory; send admin notification AFTER registration stage
    context.user_data["chosen_lang"] = lang


# flow_start -> How page
async def flow_start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("chosen_lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    caption = TEXTS[lang]["why"]
    await send_local_photo(context, q.message.chat.id, "why", caption=caption, reply_markup=kb_flow_step(TEXTS[lang]["how"], "flow_how"))


# flow_how -> Why page (in our naming: shows "how" text then "why" button leads to gpt)
async def flow_how_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("chosen_lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    caption = TEXTS[lang]["how"]
    await send_local_photo(context, q.message.chat.id, "how", caption=caption, reply_markup=kb_flow_step(TEXTS[lang].get("why", "Why"), "flow_why"))


# flow_why -> GPT page
async def flow_why_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("chosen_lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    caption = TEXTS[lang]["gpt"]
    await send_local_photo(context, q.message.chat.id, "gpt", caption=caption, reply_markup=kb_flow_step(TEXTS[lang].get("register", "Register"), "flow_register"))


# flow_register -> show register info, send admin notification with user's id, then show limited message
async def flow_register_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("chosen_lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    # show register page
    caption = TEXTS[lang]["register"]
    # offer register link + "Request access" button (the user should wait — bot not require them to send id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Register", url=POCKET_LINK)],
        [InlineKeyboardButton("Request Access", callback_data="request_access")]
    ])
    await send_local_photo(context, q.message.chat.id, "register", caption=caption, reply_markup=kb)

    # Notify admin automatically (include language and username)
    try:
        admin_text = TEXTS[lang]["admin_notify"].format(username=q.from_user.username or "—", uid=q.from_user.id)
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception as e:
        logger.warning("Failed to notify admin: %s", e)


# request_access pressed (user requests activation) -> notify admin (again) and show limited message
async def request_access_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    lang = context.user_data.get("chosen_lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    # notify admin with user's id
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=TEXTS[lang]["admin_notify"].format(username=q.from_user.username or "—", uid=q.from_user.id))
    except Exception as e:
        logger.warning("Failed to notify admin: %s", e)

    # tell user to wait / give support link
    await send_local_photo(context, q.message.chat.id, "limited", caption=TEXTS[lang]["limited"])


# Admin commands: /allow <id> and /revoke <id>
async def cmd_allow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user.id
    if caller != ADMIN_ID:
        await update.message.reply_text(TEXTS["en"]["only_admin"])
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /allow <user_id>")
        return
    uid = int(args[0])
    ALLOWED_USERS.add(uid)
    save_allowed(ALLOWED_USERS)
    await update.message.reply_text(TEXTS["en"]["allowed_ok"].format(uid=uid))
    # send user notification (if we can)
    try:
        lang = "ru"  # default
        await context.bot.send_message(chat_id=uid, text=TEXTS[lang]["access_granted"])
        # also send pairs keyboard right away
        await context.bot.send_message(chat_id=uid, text=TEXTS[lang]["choose_pair"], reply_markup=build_pairs_keyboard())
    except Exception:
        pass


async def cmd_revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user.id
    if caller != ADMIN_ID:
        await update.message.reply_text(TEXTS["en"]["only_admin"])
        return
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Usage: /revoke <user_id>")
        return
    uid = int(args[0])
    if uid in ALLOWED_USERS:
        ALLOWED_USERS.remove(uid)
        save_allowed(ALLOWED_USERS)
        await update.message.reply_text(TEXTS["en"]["revoked_ok"].format(uid=uid))
        try:
            await context.bot.send_message(chat_id=uid, text="❗ Ваш доступ был отозван.")
        except Exception:
            pass
    else:
        await update.message.reply_text(TEXTS["en"]["no_user"].format(uid=uid))


# /getid helper
async def cmd_getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = context.user_data.get("chosen_lang", "ru")
    await update.message.reply_text(TEXTS[lang]["getid"].format(uid=uid))


# Shortcut: user asks signals directly -> check allowed -> show pairs
async def cmd_signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = context.user_data.get("chosen_lang", "ru")
    if uid not in ALLOWED_USERS:
        await send_local_photo(context, update.effective_chat.id, "limited", caption=TEXTS[lang]["limited"])
        # notify admin too
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=TEXTS[lang]["admin_notify"].format(username=update.effective_user.username or "—", uid=uid))
        except Exception:
            pass
        return
    # allowed -> show pair selection
    await update.message.reply_text(TEXTS[lang]["choose_pair"], reply_markup=build_pairs_keyboard())


# Pair selected -> show tf keyboard (delete previous)
async def pair_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = context.user_data.get("chosen_lang", "ru")
    if uid not in ALLOWED_USERS:
        await send_local_photo(context, q.message.chat.id, "limited", caption=TEXTS[lang]["limited"])
        return
    # parse pair
    _, pair = q.data.split("|", 1)
    context.user_data["pair"] = pair
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_local_photo(context, q.message.chat.id, "banner", caption=TEXTS[lang]["pair_chosen"].format(pair=pair), reply_markup=build_tfs_keyboard())


# Timeframe selected -> run animated analysis and send final forecast (no graph)
async def tf_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = context.user_data.get("chosen_lang", "ru")
    if uid not in ALLOWED_USERS:
        await send_local_photo(context, q.message.chat.id, "limited", caption=TEXTS[lang]["limited"])
        return
    _, tf = q.data.split("|", 1)
    pair = context.user_data.get("pair", "unknown")
    # delete selection message
    try:
        await q.message.delete()
    except Exception:
        pass

    # Animated sequence using local image (send -> wait -> delete -> next)
    steps = [
        TEXTS[lang]["anim_fetch"],
        TEXTS[lang]["anim_ind"],
        TEXTS[lang]["anim_check"],
    ]
    last_msg = None
    try:
        for step in steps:
            # send step photo + caption
            if os.path.exists(PHOTOS.get("processing", PHOTOS["banner"])):
                with open(PHOTOS.get("processing", PHOTOS["banner"]), "rb") as f:
                    sent = await context.bot.send_photo(chat_id=uid, photo=InputFile(f), caption=step)
            else:
                sent = await context.bot.send_message(chat_id=uid, text=step)
            await asyncio.sleep(1.0 + random.random() * 1.2)
            # delete previous step message to create animation effect
            try:
                await sent.delete()
            except Exception:
                pass

        # final "done" pause
        done_msg = await context.bot.send_message(chat_id=uid, text=TEXTS[lang]["anim_done"])
        await asyncio.sleep(0.8)
        try:
            await done_msg.delete()
        except Exception:
            pass

    except Exception as e:
        logger.exception("Animation error: %s", e)

    # Build fake indicators and decision
    sma_short = round(random.uniform(0.5, 1.5), 4)
    sma_long = round(sma_short + random.uniform(-0.03, 0.03), 4)
    rsi = round(random.uniform(20, 80), 1)
    macd = round(random.uniform(-0.6, 0.6), 3)
    vol_trend = random.choice(["increasing", "decreasing", "stable"])

    score = 0.0
    if sma_short > sma_long:
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

    conf = min(95, max(55, int(50 + abs(score) * 20 + random.randint(-5, 5))))

    reasons = []
    reasons.append(f"SMA short ({sma_short}) {'>' if sma_short> sma_long else '<'} SMA long ({sma_long})")
    if rsi < 35:
        reasons.append(f"RSI {rsi}: oversold — possible bounce")
    elif rsi > 65:
        reasons.append(f"RSI {rsi}: overbought — possible pullback")
    else:
        reasons.append(f"RSI {rsi}: neutral")
    if macd > 0.02:
        reasons.append(f"MACD {macd}: positive momentum")
    elif macd < -0.02:
        reasons.append(f"MACD {macd}: negative momentum")
    else:
        reasons.append(f"MACD {macd}: flat")
    reasons.append(f"Volume: {vol_trend}")

    reasons_text = "\n".join(f"• {r}" for r in reasons)

    final_text = TEXTS[lang]["final"].format(pair=pair, time=tf, signal=signal, conf=conf, reasons=reasons_text)

    # send final explanation with banner image and two buttons (Back and New forecast)
    kb_final = InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS[lang]["back_pairs"], callback_data="back_to_pairs")],
        [InlineKeyboardButton(TEXTS[lang]["new_forecast"], callback_data="new_forecast")]
    ])
    await send_local_photo(context, uid, "final", caption=final_text, reply_markup=kb_final)

    # clear saved pair
    context.user_data.pop("pair", None)


# Back to pairs
async def back_to_pairs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = context.user_data.get("chosen_lang", "ru")
    # delete old message
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_local_photo(context, uid, "banner", caption=TEXTS[lang]["choose_pair"], reply_markup=build_pairs_keyboard())


# New forecast -> returns to pairs
async def new_forecast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = context.user_data.get("chosen_lang", "ru")
    try:
        await q.message.delete()
    except Exception:
        pass
    await send_local_photo(context, uid, "banner", caption=TEXTS[lang]["choose_pair"], reply_markup=build_pairs_keyboard())


# Fallback / unknown callback
async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()  # do nothing


# ---------------- Wiring and startup ----------------
def register_handlers(app):
    # commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("getid", cmd_getid))
    app.add_handler(CommandHandler("allow", cmd_allow))
    app.add_handler(CommandHandler("revoke", cmd_revoke))
    app.add_handler(CommandHandler("signals", cmd_signals))

    # callbacks
    app.add_handler(CallbackQueryHandler(activate_handler, pattern="^activate$"))
    app.add_handler(CallbackQueryHandler(choose_lang_handler, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(flow_start_handler, pattern="^flow_start$"))
    app.add_handler(CallbackQueryHandler(flow_how_handler, pattern="^flow_how$"))
    app.add_handler(CallbackQueryHandler(flow_why_handler, pattern="^flow_why$"))
    app.add_handler(CallbackQueryHandler(flow_register_handler, pattern="^flow_register$|^flow_go$|^flow_register$"))  # uniform route
    app.add_handler(CallbackQueryHandler(request_access_handler, pattern="^request_access$"))
    app.add_handler(CallbackQueryHandler(pair_callback, pattern="^pair\\|"))
    app.add_handler(CallbackQueryHandler(tf_callback, pattern="^tf\\|"))
    app.add_handler(CallbackQueryHandler(back_to_pairs_callback, pattern="^back_to_pairs$"))
    app.add_handler(CallbackQueryHandler(new_forecast_callback, pattern="^new_forecast$"))
    app.add_handler(CallbackQueryHandler(noop_callback, pattern="^noop$"))

    # message handler for text (optional)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: None))


def main():
    logger.info("Starting GOPLUS bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    register_handlers(app)
    app.run_polling()


if __name__ == "__main__":
    main()

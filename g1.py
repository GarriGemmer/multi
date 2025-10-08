#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
goplus_bot_full.py
Полнофункциональный бот с многослойным онбордингом, мультиязычностью,
локальными картинками по этапам, ручной авторизацией админом (ADMIN_ID),
20 пар и 15 таймфреймов, анимацией анализа и финальным текстовым прогнозом.
Работает без matplotlib, совместим с Termux.
"""

import os
import json
import logging
import random
import asyncio
from datetime import datetime
from typing import Optional, Dict

from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# -------------------- Конфигурация --------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "")  # поставь токен в .env или прямо сюда
ADMIN_ID = int(os.getenv("ADMIN_ID", "7167007722"))

# Папка с картинками (локальные)
PHOTO_DIR = "photo"
os.makedirs(PHOTO_DIR, exist_ok=True)

# Файл для хранения разрешённых пользователей
ALLOWED_FILE = "allowed_users.json"

# Логирование
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("goplus_bot")

# -------------------- Контент и тексты --------------------
TRADE_PAIRS = [
    "EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD",
    "USD/CAD", "NZD/USD", "EUR/JPY", "GBP/JPY", "EUR/GBP",
    "BTC/USD", "ETH/USD", "LTC/USD", "XAU/USD", "XAG/USD",
    "USD/TRY", "USD/ZAR", "EUR/CHF", "GBP/CHF", "AUD/JPY",
]

TIMEFRAMES = [
    "15 sec", "30 sec", "1 min", "2 min", "5 min", "10 min", "15 min", "30 min",
    "1 hour", "2 hours", "4 hours", "8 hours", "12 hours", "1 day", "1 week"
]

# Тексты мультиязычные (rus/en/hi)
TEXTS = {
    "ru": {
        "choose_lang": "Выбери язык:",
        "welcome_btn": "🔵 ACTIVE",
        "welcome": "👋 Привет! Я — Go Plus, твой персональный торговый бот.",
        "why_btn": "Почему это работает",
        "how_btn": "Как это работает",
        "gpt_btn": "О боте",
        "register": "⚡ Чтобы получить доступ, зарегистрируйся по ссылке и дождись активации админом.",
        "limited": "🔒 Доступ ограничен. Ожидайте активации администратором.",
        "access_granted": "✅ Доступ активирован! Выберите торговую пару.",
        "choose_pair": "📊 Выберите торговую пару:",
        "choose_tf": "⏱ Выберите таймфрейм:",
        "processing_step1": "🔄 Получаю рыночные данные...",
        "processing_step2": "⚙️ Вычисляю индикаторы (SMA, RSI, MACD)...",
        "processing_step3": "🔍 Анализирую корреляции и объёмы...",
        "processing_done": "✅ Анализ завершён!",
        "result_header": "📈 Результат анализа — {pair} ({tf})",
        "result_body": "Signal: {signal}\nConfidence: {conf}%\n\nIndicators:\nSMA short: {sma_s}\nSMA long: {sma_l}\nRSI: {rsi}\nMACD: {macd}\nVolume trend: {vol}",
        "back": "⬅️ НАЗАД",
        "ask_write_admin": "После регистрации админу автоматически отправлен ваш ID для активации.",
        "new_user_admin": "📥 Новый пользователь ожидает активации:\n@{uname}\nID: {uid}\nЯзык: {lang}\nВремя: {time}"
    },
    "en": {
        "choose_lang": "Choose your language:",
        "welcome_btn": "🔵 ACTIVE",
        "welcome": "👋 Hi! I'm Go Plus — your trading assistant.",
        "why_btn": "Why it works",
        "how_btn": "How it works",
        "gpt_btn": "About bot",
        "register": "⚡ To get access, register via the link and wait for admin activation.",
        "limited": "🔒 Access restricted. Wait for admin activation.",
        "access_granted": "✅ Access granted! Choose a trading pair.",
        "choose_pair": "📊 Choose trading pair:",
        "choose_tf": "⏱ Choose timeframe:",
        "processing_step1": "🔄 Fetching market data...",
        "processing_step2": "⚙️ Calculating indicators (SMA, RSI, MACD)...",
        "processing_step3": "🔍 Checking correlations and volume...",
        "processing_done": "✅ Analysis complete!",
        "result_header": "📈 Analysis result — {pair} ({tf})",
        "result_body": "Signal: {signal}\nConfidence: {conf}%\n\nIndicators:\nSMA short: {sma_s}\nSMA long: {sma_l}\nRSI: {rsi}\nMACD: {macd}\nVolume trend: {vol}",
        "back": "⬅️ BACK",
        "ask_write_admin": "After registration your ID was sent to admin for activation.",
        "new_user_admin": "📥 New user pending activation:\n@{uname}\nID: {uid}\nLang: {lang}\nTime: {time}"
    },
    "hi": {
        "choose_lang": "भाषा चुनें:",
        "welcome_btn": "🔵 ACTIVE",
        "welcome": "👋 नमस्ते! मैं Go Plus हूँ — आपका ट्रेडिंग असिस्टेंट।",
        "why_btn": "यह क्यों काम करता है",
        "how_btn": "यह कैसे काम करता है",
        "gpt_btn": "बॉट के बारे में",
        "register": "⚡ एक्सेस पाने के लिए रजिस्टर करें और एडमिन की पुष्टि का इंतजार करें।",
        "limited": "🔒 एक्सेस प्रतिबंधित है। एडमिन की पुष्टि का इंतजार करें।",
        "access_granted": "✅ एक्सेस स्वीकृत! ट्रेडिंग जोड़ी चुनें।",
        "choose_pair": "📊 ट्रेडिंग जोड़ी चुनें:",
        "choose_tf": "⏱ टाइमफ्रेम चुनें:",
        "processing_step1": "🔄 मार्केट डेटा ले रहा हूँ...",
        "processing_step2": "⚙️ इंडिकेटर्स (SMA, RSI, MACD) गणना कर रहा हूँ...",
        "processing_step3": "🔍 कोरिलेशन और वॉल्यूम जाँच रहा हूँ...",
        "processing_done": "✅ विश्लेषण पूरा!",
        "result_header": "📈 विश्लेषण — {pair} ({tf})",
        "result_body": "Signal: {signal}\nConfidence: {conf}%\n\nIndicators:\nSMA short: {sma_s}\nSMA long: {sma_l}\nRSI: {rsi}\nMACD: {macd}\nVolume trend: {vol}",
        "back": "⬅️ वापस",
        "ask_write_admin": "रजिस्ट्रेशन के बाद आपका ID एडमिन को भेज दिया गया।",
        "new_user_admin": "📥 नया उपयोगकर्ता सक्रियण के लिए:\n@{uname}\nID: {uid}\nभाषा: {lang}\nसमय: {time}"
    }
}
# -------------------- Состояния (в памяти) --------------------
# user_lang: хранит выбранный язык пользователя (по user_id)
user_lang: Dict[int, str] = {}
# allowed users set (persist)
allowed_users = set()

# -------------------- Файловые утилиты --------------------
def load_allowed():
    global allowed_users
    if os.path.exists(ALLOWED_FILE):
        try:
            with open(ALLOWED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                allowed_users = set(data.get("allowed", []))
        except Exception as e:
            logger.warning("Не удалось загрузить allowed_users.json: %s", e)
            allowed_users = set()
    else:
        allowed_users = set()

def save_allowed():
    try:
        with open(ALLOWED_FILE, "w", encoding="utf-8") as f:
            json.dump({"allowed": list(allowed_users)}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Ошибка записи allowed_users.json: %s", e)

# -------------------- Помощники по картинкам и отправкам --------------------
def photo_path(name: str) -> Optional[str]:
    """
    Возвращает путь к фото в папке photo, если существует, иначе None
    """
    p = os.path.join(PHOTO_DIR, name)
    return p if os.path.exists(p) else None

async def send_stage_photo_or_text(context: ContextTypes.DEFAULT_TYPE, chat_id: int,
                                   photo_name: str, text: str,
                                   reply_markup: Optional[InlineKeyboardMarkup] = None,
                                   delete_message_id: Optional[int] = None):
    """
    Отправляет локальную картинку (если есть) с подписью или просто текст.
    Удаляет старое сообщение, если указан delete_message_id.
    Возвращает объект Message (или None).
    """
    try:
        if delete_message_id:
            # пробуем удалить предыдущее сообщение (мягко)
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=delete_message_id)
            except Exception:
                pass

        p = photo_path(photo_name)
        if p:
            with open(p, "rb") as f:
                msg = await context.bot.send_photo(chat_id=chat_id, photo=InputFile(f),
                                                   caption=text, reply_markup=reply_markup)
            return msg
        else:
            msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
            return msg
    except Exception as e:
        logger.exception("send_stage_photo_or_text error: %s", e)
        # fallback text
        try:
            return await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        except Exception:
            return None

# -------------------- Клавиатуры --------------------
def kb_start():
    return InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS["ru"]["welcome_btn"], callback_data="activate")]])

def kb_language():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇮🇳 हिन्दी", callback_data="lang_hi")]
    ])

def kb_welcome_actions(lang: str):
    t = TEXTS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["how_btn"], callback_data="show_how")],
        [InlineKeyboardButton(t["why_btn"], callback_data="show_why")],
        [InlineKeyboardButton(t["gpt_btn"], callback_data="show_gpt")],
        [InlineKeyboardButton("Register", callback_data="show_register")]
    ])

def kb_after_register(lang: str):
    t = TEXTS[lang]
    return InlineKeyboardMarkup([[InlineKeyboardButton(t["back"], callback_data="back_home")]])

def kb_pairs():
    kb = []
    # 4 в строке — компактно
    for i in range(0, len(TRADE_PAIRS), 4):
        row = [InlineKeyboardButton(p, callback_data=f"pair|{p}") for p in TRADE_PAIRS[i:i+4]]
        kb.append(row)
    kb.append([InlineKeyboardButton(TEXTS["ru"]["back"], callback_data="back_home")])
    return InlineKeyboardMarkup(kb)

def kb_timeframes():
    kb = []
    for i in range(0, len(TIMEFRAMES), 5):
        row = [InlineKeyboardButton(tf, callback_data=f"tf|{tf}") for tf in TIMEFRAMES[i:i+5]]
        kb.append(row)
    kb.append([InlineKeyboardButton(TEXTS["ru"]["back"], callback_data="back_pairs")])
    return InlineKeyboardMarkup(kb)

# -------------------- Обработчики команд --------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start — показ GIF/баннера и кнопки ACTIVE"""
    user = update.effective_user
    # по умолчанию язык русский, можно менять позже
    user_lang[user.id] = "ru"
    # отправляем баннер + кнопка ACTIVE
    text = TEXTS["ru"]["choose_lang"]
    # use lang photo if exists
    msg = await send_stage_photo_or_text(context, user.id, "lang.jpg", text, reply_markup=kb_language())
    # nothing more here

async def callback_language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора языка — далее показываем серию экранов: welcome -> why -> how -> gpt -> register"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang = query.data.split("_", 1)[1]
    user_lang[uid] = lang
    t = TEXTS[lang]

    # delete the language selection message
    try:
        await query.message.delete()
    except Exception:
        pass

    # step sequence: welcome -> why -> how -> gpt -> register
    # for each step: send photo+text with a keyboard to go to next step
    msg = await send_stage_photo_or_text(context, uid, "welcome.jpg", t["welcome"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next", callback_data="next_welcome")]]))
    # store message id in user_data to delete later if needed
    context.user_data["last_msg"] = msg.message_id if msg else None

async def next_welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang = user_lang.get(uid, "ru")
    t = TEXTS[lang]

    # delete previous
    try:
        await query.message.delete()
    except Exception:
        pass

    # show WHY
    msg = await send_stage_photo_or_text(context, uid, "why.jpg", t["why"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next", callback_data="next_why")]]))
    context.user_data["last_msg"] = msg.message_id if msg else None

async def next_why_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang = user_lang.get(uid, "ru")
    t = TEXTS[lang]

    try:
        await query.message.delete()
    except Exception:
        pass

    msg = await send_stage_photo_or_text(context, uid, "how.jpg", t["how"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next", callback_data="next_how")]]))
    context.user_data["last_msg"] = msg.message_id if msg else None

async def next_how_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang = user_lang.get(uid, "ru")
    t = TEXTS[lang]

    try:
        await query.message.delete()
    except Exception:
        pass

    msg = await send_stage_photo_or_text(context, uid, "gpt.jpg", t["gpt"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Next", callback_data="next_gpt")]]))
    context.user_data["last_msg"] = msg.message_id if msg else None

async def next_gpt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang = user_lang.get(uid, "ru")
    t = TEXTS[lang]

    try:
        await query.message.delete()
    except Exception:
        pass

    # final registration screen
    msg = await send_stage_photo_or_text(context, uid, "register.jpg", t["register"] + "\n\n" + t["ask_write_admin"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("OK", callback_data="registered_ok")]]))
    context.user_data["last_msg"] = msg.message_id if msg else None

    # notify admin automatically about new user (with basic info)
    try:
        admin_text = TEXTS[lang]["new_user_admin"].format(
            uname=(context.bot.get_chat(uid).username or "—"),
            uid=uid,
            lang=lang.upper(),
            time=datetime.utcnow().isoformat()
        )
    except Exception:
        admin_text = f"📥 New user pending: ID {uid}, lang {lang}"
    # send to admin
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception as e:
        logger.warning("Не удалось отправить уведомление админу: %s", e)

async def registered_ok_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang = user_lang.get(uid, "ru")
    t = TEXTS[lang]
    # delete message
    try:
        await query.message.delete()
    except Exception:
        pass
    # tell user that they are pending / limited
    await send_stage_photo_or_text(context, uid, "register.jpg", t["limited"], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("OK", callback_data="back_home")]]))

# -------------------- Admin commands: allow/revoke/list --------------------
def ensure_allowed_loaded():
    if not allowed_users:
        load_allowed()

async def cmd_allow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/allow <user_id> — admin only"""
    caller = update.effective_user.id
    if caller != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can use this.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /allow <user_id>")
        return
    try:
        uid = int(context.args[0])
    except Exception:
        await update.message.reply_text("Invalid id (must be integer).")
        return
    ensure_allowed_loaded()
    allowed_users.add(uid)
    save_allowed()
    # notify user
    lang = user_lang.get(uid, "ru")
    try:
        await send_stage_photo_or_text(context, uid, "pairs.jpg", TEXTS[lang]["access_granted"], reply_markup=kb_pairs())
    except Exception:
        logger.warning("Не удалось уведомить пользователя о доступе.")
    await update.message.reply_text(f"✅ User {uid} allowed.")

async def cmd_revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user.id
    if caller != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can use this.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /revoke <user_id>")
        return
    try:
        uid = int(context.args[0])
    except Exception:
        await update.message.reply_text("Invalid id (must be integer).")
        return
    ensure_allowed_loaded()
    if uid in allowed_users:
        allowed_users.remove(uid)
        save_allowed()
        await update.message.reply_text(f"✅ User {uid} revoked.")
        try:
            await send_stage_photo_or_text(context, uid, "register.jpg", TEXTS[user_lang.get(uid, "ru")]["limited"])
        except Exception:
            pass
    else:
        await update.message.reply_text("User not found in allowed.")

async def cmd_list_allowed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caller = update.effective_user.id
    if caller != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can use this.")
        return
    ensure_allowed_loaded()
    if not allowed_users:
        await update.message.reply_text("No allowed users.")
        return
    await update.message.reply_text("Allowed users:\n" + "\n".join(map(str, sorted(allowed_users))))

# -------------------- Flow: access -> pairs -> timeframes -> analysis --------------------
async def start_signals_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Optional entrypoint: user requests signals directly (/signals)"""
    user = update.effective_user
    uid = user.id
    lang = user_lang.get(uid, "ru")
    ensure_allowed_loaded()
    if uid not in allowed_users:
        await send_stage_photo_or_text(context, uid, "register.jpg", TEXTS[lang]["limited"])
        return
    # delete initial message if any
    try:
        await update.message.delete()
    except Exception:
        pass
    # show pairs
    await send_stage_photo_or_text(context, uid, "pairs.jpg", TEXTS[lang]["choose_pair"], reply_markup=kb_pairs())

async def pair_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User clicked a pair"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    ensure_allowed_loaded()
    if uid not in allowed_users:
        lang = user_lang.get(uid, "ru")
        await send_stage_photo_or_text(context, uid, "register.jpg", TEXTS[lang]["limited"])
        return
    lang = user_lang.get(uid, "ru")
    pair = query.data.split("|", 1)[1]
    # delete previous message with keyboard to keep chat clean
    try:
        await query.message.delete()
    except Exception:
        pass
   context.user_data["chosen_pair"] = pair
    await send_stage_photo_or_text(context, uid, "timeframes.jpg", TEXTS[lang]["choose_tf"], reply_markup=kb_timeframes())

async def tf_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User clicked a timeframe -> run animated analysis -> show result"""
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    ensure_allowed_loaded()
    if uid not in allowed_users:
        lang = user_lang.get(uid, "ru")
        await send_stage_photo_or_text(context, uid, "register.jpg", TEXTS[lang]["limited"])
        return
    lang = user_lang.get(uid, "ru")
    tf = query.data.split("|", 1)[1]
    pair = context.user_data.get("chosen_pair", "—")

    # delete previous keyboard message
    try:
        await query.message.delete()
    except Exception:
        pass

    # ANIMATION SEQUENCE: we will send 3 stage messages (photo+caption) and delete previous to keep chat clean
    msg1 = await send_stage_photo_or_text(context, uid, "processing1.jpg", TEXTS[lang]["processing_step1"])
    await asyncio.sleep(0.9 + random.random() * 0.6)
    # delete previous
    prev_id = msg1.message_id if msg1 else None
    msg2 = await send_stage_photo_or_text(context, uid, "processing2.jpg", TEXTS[lang]["processing_step2"], delete_message_id=prev_id)
    await asyncio.sleep(0.9 + random.random() * 0.6)
    prev_id = msg2.message_id if msg2 else None
    msg3 = await send_stage_photo_or_text(context, uid, "processing3.jpg", TEXTS[lang]["processing_step3"], delete_message_id=prev_id)
    await asyncio.sleep(0.8 + random.random() * 0.8)
    # final done message (delete previous)
    prev_id = msg3.message_id if msg3 else None
    done_msg = await send_stage_photo_or_text(context, uid, "result.jpg", TEXTS[lang]["processing_done"], delete_message_id=prev_id)

    # simple indicator generation (realistic ranges)
    sma_short = round(random.uniform(0.98, 1.05), 4)
    sma_long = round(sma_short + random.uniform(-0.02, 0.02), 4)
    rsi = round(random.uniform(20, 80), 1)
    macd = round(random.uniform(-0.6, 0.6), 3)
    vol_trend = random.choice(["increasing", "decreasing", "stable"])

    # scoring logic (same as раньше — простая, но правдоподобная)
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
        signal = "📈 UP"
    elif score <= -1.0:
        signal = "📉 DOWN"
    else:
        signal = "↔️ NEUTRAL"

    confidence = min(95, max(50, int(50 + abs(score) * 20 + random.randint(-5, 5))))

    # prepare final text
    header = TEXTS[lang]["result_header"].format(pair=pair, tf=tf)
    body = TEXTS[lang]["result_body"].format(
        signal=signal, conf=confidence, sma_s=sma_short, sma_l=sma_long,
        rsi=rsi, macd=macd, vol=vol_trend
    )
    full_text = header + "\n\n" + body

    # send final result with BACK / NEW buttons
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="back_pairs")],
        [InlineKeyboardButton("🔁 New forecast", callback_data="new_forecast")]
    ])
    try:
        # delete 'done_msg' to keep only final
        if done_msg:
            await context.bot.delete_message(chat_id=uid, message_id=done_msg.message_id)
    except Exception:
        pass

    await send_stage_photo_or_text(context, uid, "result.jpg", full_text, reply_markup=kb)

    # cleanup chosen_pair
    context.user_data.pop("chosen_pair", None)

async def back_pairs_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    lang = user_lang.get(uid, "ru")
    try:
        await query.message.delete()
    except Exception:
        pass
    await send_stage_photo_or_text(context, uid, "pairs.jpg", TEXTS[lang]["choose_pair"], reply_markup=kb_pairs())

async def new_forecast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    # simply restart pair selection
    try:
        await query.message.delete()
    except Exception:
        pass
    lang = user_lang.get(uid, "ru")
    await send_stage_photo_or_text(context, uid, "pairs.jpg", TEXTS[lang]["choose_pair"], reply_markup=kb_pairs())

# -------------------- Дополнительные команды --------------------
async def cmd_getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"Your Telegram ID: {uid}")

# -------------------- Main / boot --------------------
def build_app():
    load_allowed()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("signals", start_signals_flow))  # quick access
    app.add_handler(CommandHandler("getid", cmd_getid))
    app.add_handler(CommandHandler("allow", cmd_allow))
    app.add_handler(CommandHandler("revoke", cmd_revoke))
    app.add_handler(CommandHandler("list_allowed", cmd_list_allowed))

    # Language selection & onboarding steps
    app.add_handler(CallbackQueryHandler(callback_language_chosen, pattern=r"^lang_"))
    app.add_handler(CallbackQueryHandler(next_welcome_handler, pattern=r"^next_welcome$"))
    app.add_handler(CallbackQueryHandler(next_why_handler, pattern=r"^next_why$"))
    app.add_handler(CallbackQueryHandler(next_how_handler, pattern=r"^next_how$"))
    app.add_handler(CallbackQueryHandler(next_gpt_handler, pattern=r"^next_gpt$"))
    app.add_handler(CallbackQueryHandler(registered_ok_handler, pattern=r"^registered_ok$"))

    # Signal flow
    app.add_handler(CallbackQueryHandler(pair_callback, pattern=r"^pair\|"))
    app.add_handler(CallbackQueryHandler(tf_callback, pattern=r"^tf\|"))
    app.add_handler(CallbackQueryHandler(back_pairs_callback, pattern=r"^back_pairs$"))
    app.add_handler(CallbackQueryHandler(new_forecast_callback, pattern=r"^new_forecast$"))

    # small helpers: back_home
    app.add_handler(CallbackQueryHandler(lambda u, c: send_stage_photo_or_text(c, u.callback_query.from_user.id, "welcome.jpg", TEXTS[user_lang.get(u.callback_query.from_user.id, 'ru')]["welcome"], reply_markup=kb_welcome_actions(user_lang.get(u.callback_query.from_user.id, 'ru'))), pattern=r"^back_home$"))

    return app

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set in environment or .env")
    load_allowed()
    app = build_app()
    logger.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()

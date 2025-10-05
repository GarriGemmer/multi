
#!/usr/bin/env python3
import os
import logging
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ----------------- Настройка -----------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
POCKET_LINK = os.getenv("POCKET_LINK", "https://bit.ly/pocket-option-rus")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/your_channel")
SUPPORT_BOT = os.getenv("SUPPORT_BOT", "https://t.me/G0_PLUS_SUPPORTBOT")

# ссылки из .env (можно оставить пустыми — есть запасные)
IMAGES = {
    "start": os.getenv("BANNER_START_URL", "https://via.placeholder.com/900x400.png?text=Go+Plus+Start"),
    "why": os.getenv("BANNER_WHY_URL", "https://via.placeholder.com/900x400.png?text=Why+Go+Plus"),
    "how": os.getenv("BANNER_HOW_URL", "https://via.placeholder.com/900x400.png?text=How"),
    "gpt": os.getenv("BANNER_GPT_URL", "https://via.placeholder.com/900x400.png?text=GPT-5"),
    "register": os.getenv("BANNER_REGISTER_URL", "https://via.placeholder.com/900x400.png?text=Register"),
}

if not BOT_TOKEN:
    raise RuntimeError("Добавь BOT_TOKEN в .env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- callback constants ----------
LANG_RU = "lang_ru"
LANG_EN = "lang_en"
LANG_HI = "lang_hi"

BTN_START = "btn_start"
BTN_HOW = "btn_how"
BTN_WHY = "btn_why"
BTN_GO = "btn_go"

# ---------- тексты (multilang) ----------
TEXTS = {
    "ru": {
        "choose_lang": "“Choose your language:",
        "welcome": "👋 Привет! Я — Go Plus, твой персональный торговый бот.\n\n🚀 Моя задача — помочь тебе зарабатывать на трейдинге проще и стабильнее.",
        "why": "✨ Почему выбирают Go Plus:\n\n• Более 100 активов для торговли\n• Поддержка OTC и биржевых пар\n• 2 режима торговли для любого стиля\n• Мгновенный анализ графика\n• Точность сигналов 97,89%+\n• Работаю 24/7 на любом устройстве\n\n💎 Ты получаешь инструмент, который всегда на шаг впереди рынка.",
        "how": "🤖 Всё просто:\n\n1️⃣ Выбираешь актив\n2️⃣ Указываешь время сделки\n3️⃣ Получаешь сигнал: Выше / Ниже\n4️⃣ Открываешь сделку\n5️⃣ Фиксируешь профит 💸\n\n⚡️ Всю математику и аналитику я беру на себя — тебе остаётся только действовать.",
        "gpt": "🤖 Я построен на базе AI GPT-5 и Meta Trader 5 который за секунды обрабатывает огромный объём данных.\n\n📊 Я анализирую сотни индикаторов, ценовые паттерны и технический анализ.\n\n🔍 Я вижу закономерности, которые человек заметит слишком поздно.\n\n⚡️ Каждый мой сигнал — результат точных вычислений, а не догадок.",
        "register": f"⚡ Чтобы получить доступ к Go Plus, зарегистрируй новый аккаунт на Pocket Option строго по моей ссылке:\n{POCKET_LINK}",
        "start": "Начать",
        "how_btn": "Как это работает",
        "why_btn": "Почему это работает",
        "go": "Давай начнем",
        "reg1": "Зарегистрироваться",
        "reg2": "Напиши мне свой ID",
        "reg3": "Наш канал",
    },
    "en": {
        "choose_lang": "Choose your language:",
        "welcome": "👋 Hi! I'm Go Plus, your personal trading bot.\n\n🚀 My goal is to help you earn from trading easily and consistently.",
        "why": "✨ Why choose Go Plus:\n\n• 100+ assets for trading\n• Support for OTC and exchange pairs\n• 2 trading modes for any style\n• Instant chart analysis\n• Signal accuracy 97.89%+\n• Works 24/7 on any device\n\n💎 You get a tool that stays one step ahead of the market.",
        "how": "🤖 It’s simple:\n\n1️⃣ Choose an asset\n2️⃣ Set trade time\n3️⃣ Get a signal: Up / Down\n4️⃣ Open the trade\n5️⃣ Take profit 💸\n\n⚡️ I handle all the math and analytics — you just act.",
        "gpt": "🤖 I’m built on AI GPT-5 and Meta Trader 5 that processes massive data in seconds.\n\n📊 I analyze hundreds of indicators, price patterns, and technical data.\n\n🔍 I spot trends long before humans do.\n\n⚡️ Every signal is based on precise calculations — not guesses.",
        "register": f"⚡ To get access to Go Plus, register a new account on Pocket Option via my link:\n{POCKET_LINK}",
        "start": "Start",
        "how_btn": "How it works",
        "why_btn": "Why it works",
        "go": "Let's go",
        "reg1": "Register",
        "reg2": "Send me your ID",
        "reg3": "Our channel",
    },
    "hi": {
        "choose_lang": "भाषा चुनें:",
        "welcome": "👋 नमस्ते! मैं Go Plus हूँ — आपका पर्सनल ट्रेडिंग बॉट।\n\n🚀 मेरा काम है आपको आसान और स्थिर तरीके से ट्रेडिंग से कमाई कराना।",
        "why": "✨ Go Plus क्यों चुनें:\n\n• 100+ ट्रेडिंग एसेट्स\n• OTC और एक्सचेंज पेयर्स सपोर्ट\n• हर स्टाइल के लिए 2 मोड\n• तुरंत चार्ट विश्लेषण\n• सिग्नल सटीकता 97.89%+\n• 24/7 काम करता है हर डिवाइस पर\n\n💎 आपको एक ऐसा टूल मिलता है जो मार्केट से हमेशा एक कदम आगे है।",
        "how": "🤖 बहुत आसान है:\n\n1️⃣ एसेट चुनें\n2️⃣ ट्रेड समय सेट करें\n3️⃣ सिग्नल पाएं: ऊपर / नीचे\n4️⃣ ट्रेड खोलें\n5️⃣ प्रॉफिट लें 💸\n\n⚡️ सारे गणित और विश्लेषण मैं संभालता हूँ — आपको बस कार्य करना है।",
        "gpt": "🤖 मैं GPT-5 AI Meta Trader 5 पर आधारित हूँ जो सेकंडों में भारी डेटा प्रोसेस करता है।\n\n📊 मैं सैकड़ों इंडिकेटर्स, प्राइस पैटर्न और तकनीकी विश्लेषण देखता हूँ।\n\n🔍 मैं वो ट्रेंड पकड़ता हूँ जो इंसान देर से देखेगा।\n\n⚡️ हर सिग्नल सटीक गणना पर आधारित है — अनुमान पर नहीं।",
        "register": f"⚡ Go Plus का उपयोग करने के लिए, मेरी लिंक से Pocket Option पर नया अकाउंट बनाएँ:\n{POCKET_LINK}",
        "start": "शुरू करें",
        "how_btn": "यह कैसे काम करता है",
        "why_btn": "यह क्यों काम करता है",
        "go": "चलो शुरू करें",
        "reg1": "रजिस्टर करें",
        "reg2": "मुझे अपना ID भेजें",
        "reg3": "हमारा चैनल",
    }
}

# ---------- клавиатуры ----------
def keyboard_language():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data=LANG_RU)],
        [InlineKeyboardButton("🇬🇧 English", callback_data=LANG_EN)],
        [InlineKeyboardButton("🇮🇳 हिन्दी", callback_data=LANG_HI)],
    ])

# helper: отправляет фото (или текст если картинка не доступна)
async def send_image(context: ContextTypes.DEFAULT_TYPE, chat_id: int, img_key: str, caption: str, keyboard=None):
    img = IMAGES.get(img_key)
    try:
        if img and os.path.exists(img):
            with open(img, "rb") as f:
                await context.bot.send_photo(chat_id=chat_id, photo=InputFile(f), caption=caption, reply_markup=keyboard)
            return
        if img and (img.startswith("http://") or img.startswith("https://")):
            await context.bot.send_photo(chat_id=chat_id, photo=img, caption=caption, reply_markup=keyboard)
            return
    except Exception as e:
        logger.warning("Не получилось отправить картинку: %s", e)

    await context.bot.send_message(chat_id=chat_id, text=caption, reply_markup=keyboard)

# ---------- команды ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(context, update.effective_chat.id, "start", TEXTS["ru"]["choose_lang"], keyboard_language())

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    chat_id = q.message.chat_id

    if data in (LANG_RU, LANG_EN, LANG_HI):
        lang = data.split("_")[1]
        context.user_data["lang"] = lang
        t = TEXTS[lang]
        try:
            await q.message.delete()
        except Exception:
            pass
        await send_image(context, chat_id, "start", t["welcome"], InlineKeyboardMarkup([[InlineKeyboardButton(t["start"], callback_data=BTN_START)]]))
        return

    lang = context.user_data.get("lang", "ru")
    t = TEXTS[lang]

    if data == BTN_START:
        try:
            await q.message.delete()
        except Exception:
            pass
        await send_image(context, chat_id, "why", t["why"], InlineKeyboardMarkup([[InlineKeyboardButton(t["how_btn"], callback_data=BTN_HOW)]]))
        return

    if data == BTN_HOW:
        try:
            await q.message.delete()
        except Exception:
            pass
        await send_image(context, chat_id, "how", t["how"], InlineKeyboardMarkup([[InlineKeyboardButton(t["why_btn"], callback_data=BTN_WHY)]]))
        return

    if data == BTN_WHY:
        try:
            await q.message.delete()
        except Exception:
            pass
        await send_image(context, chat_id, "gpt", t["gpt"], InlineKeyboardMarkup([[InlineKeyboardButton(t["go"], callback_data=BTN_GO)]]))
        return

    if data == BTN_GO:
        try:
            await q.message.delete()
        except Exception:
            pass
        kb = [
            [InlineKeyboardButton(t["reg1"], url=POCKET_LINK)],
            [InlineKeyboardButton(t["reg2"], url="https://t.me/ТВОЙ_ПРОФИЛЬ")],
            [InlineKeyboardButton(t["reg3"], url=CHANNEL_LINK)],
        ]
        await send_image(context, chat_id, "register", t["register"], InlineKeyboardMarkup(kb))
        return

    await context.bot.send_message(chat_id=chat_id, text="Команда не распознана.")

# ---------- запуск ----------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()

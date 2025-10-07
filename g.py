# =========================
# GOLDBOT v1 — PART 1/2
# =========================
# Мультиязычный Telegram-бот с локальными картинками и этапами регистрации
# После этой части идёт вторая (Binance API + прогноз + анимация)

import asyncio
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import logging

# 🔧 Настройки
TOKEN = "7816419974:AAGDTqScu5OE2KvmGNPZA-BBYov0XnQCmgI"
ADMIN_ID = 7167007722  # твой Telegram ID
IMAGE_PATH = "stage.png"  # локальная картинка для всех этапов

# 🔤 Переводы интерфейса
LANG_TEXTS = {
    "ru": {
        "welcome": "Привет! 👋 Выбери язык / Choose language:",
        "lang_selected": "Язык выбран: 🇷🇺 Русский",
        "register": "Регистрация",
        "request": "Запрос доступа",
        "write_me": "✉️ Напиши мне ID",
        "our_channel": "📢 Наш канал",
        "waiting_access": "🔐 Ожидание доступа. Свяжись с администратором.",
        "access_granted": "✅ Доступ подтверждён! Скоро начнём анализ.",
        "choose_pair": "Выберите торговую пару:",
    },
    "en": {
        "welcome": "Hi there! 👋 Please choose your language:",
        "lang_selected": "Language selected: 🇬🇧 English",
        "register": "Register",
        "request": "Request Access",
        "write_me": "✉️ Message me your ID",
        "our_channel": "📢 Our Channel",
        "waiting_access": "🔐 Waiting for access approval. Contact the admin.",
        "access_granted": "✅ Access granted! Starting analysis soon.",
        "choose_pair": "Select a trading pair:",
    },
    "hi": {
        "welcome": "नमस्ते! 👋 कृपया अपनी भाषा चुनें:",
        "lang_selected": "भाषा चुनी गई: 🇮🇳 हिंदी",
        "register": "रजिस्टर करें",
        "request": "एक्सेस मांगे",
        "write_me": "✉️ मुझे अपना आईडी भेजें",
        "our_channel": "📢 हमारा चैनल",
        "waiting_access": "🔐 एक्सेस की प्रतीक्षा कर रहे हैं। एडमिन से संपर्क करें।",
        "access_granted": "✅ एक्सेस दिया गया! विश्लेषण शुरू होने वाला है।",
        "choose_pair": "ट्रेडिंग जोड़ी चुनें:",
    },
}

# 🧠 Хранилище пользовательских данных
user_data = {}

# 🛠️ Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ======================
#  Обработчики команд
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Первый экран — выбор языка"""
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇮🇳 हिंदी", callback_data="lang_hi"),
        ]
    ]

    if update.message:
        chat_id = update.message.chat_id
    else:
        chat_id = update.callback_query.message.chat_id

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=InputFile(IMAGE_PATH),
        caption="Привет! 👋 Choose your language:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def language_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """После выбора языка"""
    query = update.callback_query
    await query.answer()

    lang_code = query.data.split("_")[1]
    user_id = query.from_user.id
    user_data[user_id] = {"lang": lang_code, "access": False}

    text = LANG_TEXTS[lang_code]["lang_selected"]
    await query.message.delete()

    await context.bot.send_photo(
        chat_id=user_id,
        photo=InputFile(IMAGE_PATH),
        caption=text,
    )

    await asyncio.sleep(1)
    await registration_step(user_id, context, lang_code)


async def registration_step(user_id, context, lang_code):
    """Этап регистрации с кнопками"""
    t = LANG_TEXTS[lang_code]

    keyboard = [
        [
            InlineKeyboardButton(t["register"], callback_data=f"register_{lang_code}"),
            InlineKeyboardButton(t["request"], callback_data=f"request_{lang_code}"),
        ],
        [
            InlineKeyboardButton(
                t["write_me"], url="https://t.me/VikramBiz"
            ),
            InlineKeyboardButton(
                t["our_channel"], url="https://t.me/YourChannelHere"
            ),
        ],
    ]

    await context.bot.send_photo(
        chat_id=user_id,
        photo=InputFile(IMAGE_PATH),
        caption=f"{t['register']} / {t['request']}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def registration_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора на этапе регистрации"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    lang_code = user_data[user_id]["lang"]
    t = LANG_TEXTS[lang_code]

    if query.data.startswith("register_"):
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=user_id,
            photo=InputFile(IMAGE_PATH),
            caption=t["waiting_access"],
        )
        # Отправляем админу сообщение
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👤 Новый пользователь запросил доступ:\n\nID: `{user_id}`\nUsername: @{query.from_user.username}",
            parse_mode="Markdown",
        )

    elif query.data.startswith("request_"):
        await query.message.delete()
        await context.bot.send_photo(
            chat_id=user_id,
            photo=InputFile(IMAGE_PATH),
            caption=t["waiting_access"],
        )

    # доступ выдается вручную через /allow ID
    return


async def allow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ выдает доступ вручную"""
    if update.message.chat_id != ADMIN_ID:
        return

    try:
        target_id = int(context.args[0])
        if target_id in user_data:
            user_data[target_id]["access"] = True
            lang = user_data[target_id]["lang"]
            t = LANG_TEXTS[lang]

            await context.bot.send_photo(
                chat_id=target_id,
                photo=InputFile(IMAGE_PATH),
                caption=t["access_granted"],
            )

            await asyncio.sleep(1)
            await send_pair_selection(target_id, context, lang)
        else:
            await update.message.reply_text("Пользователь не найден.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


async def send_pair_selection(user_id, context, lang_code):
    """Переход к выбору торговой пары"""
    t = LANG_TEXTS[lang_code]
    pairs = [
        ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"],
        ["ADA/USDT", "DOGE/USDT", "DOT/USDT", "AVAX/USDT", "TRX/USDT"],
        ["LINK/USDT", "MATIC/USDT", "ATOM/USDT", "LTC/USDT", "SHIB/USDT"],
        ["NEAR/USDT", "APT/USDT", "TON/USDT", "FIL/USDT", "AR/USDT"],
    ]

    keyboard = [[InlineKeyboardButton(pair, callback_data=f"pair_{pair}_{lang_code}") for pair in row] for row in pairs]

    await context.bot.send_photo(
        chat_id=user_id,
        photo=InputFile(IMAGE_PATH),
        caption=t["choose_pair"],
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ======================
#   MAIN ENTRY
# ======================

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(language_selected, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(registration_handler, pattern="^(register_|request_)"))
    app.add_handler(CommandHandler("allow", allow_command))
    app.run_polling()


if __name__ == "__main__":
    main()

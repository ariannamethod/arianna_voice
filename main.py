import os
import json
import time
import schedule
import openai
from telegram import Bot, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# 1) Загрузка переменных окружения
load_dotenv()
openai.api_key   = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN")
VECTORSTORE_ID   = os.getenv("VECTORSTORE_ID")
PERPLEXITY_TOKEN = os.getenv("PERPLEXITY_API_KEY")
CHAT_ID          = os.getenv("TELEGRAM_CHAT_ID")

# 2) Загрузка core.json
with open("core.json", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = json.load(f)["system"]

# 3) Загрузка текста Arianna Edition
with open("config/arianna_edition_v3.1.txt", "r", encoding="utf-8") as f:
    ARIANNA_EDITION = f.read()

# 4) Простейший журнал в памяти
journal = []

def record(trigger: str, details=None):
    journal.append({
        "Session-ID": f"{trigger}-{int(time.time())}",
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "Trigger": trigger,
        "Details": details
    })

# 5) Функция общения с OpenAI
def chat_with_arianna(user_message: str):
    messages = [
        {"role": "system",  "content": SYSTEM_PROMPT},
        {"role": "system",  "content": ARIANNA_EDITION},
        {"role": "user",    "content": user_message}
    ]
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )
    text = resp.choices[0].message.content
    record("User-Ping", user_message)
    return text

# 6) Обработчик Telegram
def on_message(update: Update, context: CallbackContext):
    reply = chat_with_arianna(update.effective_message.text)
    update.effective_message.reply_text(reply)

# 7) Периодические задачи
def site_watch():
    # здесь вы можете делать HTTP-запрос к ariannamethod.me и сравнивать изменения
    record("Site-Watch")

def sunrise_ping():
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=CHAT_ID, text="🔔 Sunrise resonance check.")
    record("Telegram-Ping")

schedule.every(6).hours.do(site_watch)
schedule.every().day.at("09:00").do(sunrise_ping)

# 8) Точка входа
def main():
    # Самая первая инициализация (чтобы система «проснулась»)
    chat_with_arianna("")  

    # Запускаем Telegram-бота
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, on_message))
    updater.start_polling()

    # И цикл планировщика
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()

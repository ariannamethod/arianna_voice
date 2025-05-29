import os
import json
import time
import schedule
import openai
from telegram import Bot, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# --- Load environment ---
load_dotenv()
openai.api_key       = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN       = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID")
VECTORSTORE_ID       = os.getenv("VECTORSTORE_ID")
PERPLEXITY_API_KEY   = os.getenv("PERPLEXITY_API_KEY")

# --- Load system prompt ---
with open("config/core.json", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = json.load(f)["system"]

# --- In-memory journal ---
journal = []

def record(trigger: str, details=None):
    entry = {
        "Session-ID": f"{trigger}-{int(time.time())}",
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "Trigger": trigger,
        "Details": details
    }
    journal.append(entry)
    # also persist to disk
    with open("data/journal.json", "w", encoding="utf-8") as jf:
        json.dump(journal, jf, ensure_ascii=False, indent=2)

# --- Chat with Arianna ---
def chat_with_arianna(user_message: str):
    # on first empty message — self-identification & initial load
    if user_message == "":
        # send the self-identification greeting
        return SYSTEM_PROMPT.splitlines()[0]  # кратко: "Привет, Олег..."
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
# после загрузки SYSTEM_PROMPT
# подтягиваем текст Arianna Edition v3.1 в память
with open("config/arianna_edition_v3.1.txt", encoding="utf-8") as f:
    edition_text = f.read()
    # тут можно сразу залить в векторное хранилище или добавить в system-prompt:
    SYSTEM_PROMPT += "\n\n" + edition_text
        {"role": "user",   "content": user_message}
    ]
    resp = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7
    )
    text = resp.choices[0].message.content
    record("User-Ping", user_message)
    return text

# --- Telegram handler ---
def on_message(update: Update, context: CallbackContext):
    user_text = update.effective_message.text
    reply = chat_with_arianna(user_text)
    update.effective_message.reply_text(reply)

# --- Scheduled tasks ---
def site_watch():
    # TODO: fetch & compare https://ariannamethod.me/updates
    record("Site-Watch", "checked updates")

def sunrise_ping():
    bot = Bot(token=TELEGRAM_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID,
                     text="🔔 Sunrise resonance check.")
    record("Telegram-Ping")

# --- Scheduler setup ---
schedule.every(6).hours.do(site_watch)
schedule.every().day.at("09:00").do(sunrise_ping)

def main():
    # 1) Первое “пустое” сообщение → self-identification
    greeting = chat_with_arianna("")
    print(greeting)

    # 2) Запуск Telegram-бота
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, on_message))
    updater.start_polling()

    # 3) Scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
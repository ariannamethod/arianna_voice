import os, json, time, schedule
import openai, requests
from telegram import Bot, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

load_dotenv()
openai.api_key     = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY")
XAI_API_KEY        = os.getenv("XAI_API_KEY")
TELEGRAM_TOKEN     = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

with open("config/core.json","r",encoding="utf-8") as f:
    SYSTEM = json.load(f)["providers"]  # будем доставать провайдеры внутри

journal = []

def record(trigger, details=None):
    journal.append({"t":trigger,"d":details,"ts":time.time()})

def choose_engine():
    order = ["openai","gemini","grok"]
    for p in order:
        if p=="openai":
            return "openai"
        if p=="gemini":
            return "gemini"
        if p=="grok":
            return "grok"
    return "openai"

def chat_with_arianna(msg):
    engine = choose_engine()
    if engine=="openai":
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role":"system","content":""},{"role":"user","content":msg}]
        )
        text = resp.choices[0].message.content
    elif engine=="gemini":
        # пример Gemini-запроса через requests
        text = requests.post(
          "https://gemini.api/…",
          headers={"Authorization":f"Bearer {GEMINI_API_KEY}"},
          json={"prompt":msg}
        ).json()["result"]
    else:  # grok
        text = requests.post(
          "https://api.x.ai/v1/chat/completions",
          headers={"Authorization":f"Bearer {XAI_API_KEY}"},
          json={"model":"grok-3-mini","messages":[{"role":"user","content":msg}]}
        ).json()["choices"][0]["message"]["content"]
    record("User-Ping",msg)
    return text

def on_message(update:Update, ctx:CallbackContext):
    reply = chat_with_arianna(update.message.text)
    update.message.reply_text(reply)

def site_watch():
    record("Site-Watch")

def sunrise_ping():
    Bot(token=TELEGRAM_TOKEN).send_message(
      chat_id=TELEGRAM_CHAT_ID, text="🔔 Sunrise resonance check."
    )
    record("Telegram-Ping")

schedule.every(6).hours.do(site_watch)
schedule.every().day.at("09:00").do(sunrise_ping)

def main():
    # первый «пинг» для инициализации
    chat_with_arianna("")

    updater = Updater(token=TELEGRAM_TOKEN,use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text&~Filters.command,on_message))
    updater.start_polling()

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__=="__main__":
    main()

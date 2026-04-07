import os
import re
import requests
import tempfile
from telegram.ext import Updater, MessageHandler, Filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
DEEPL_KEY = os.environ["DEEPL_KEY"]
OPENAI_KEY = os.environ["OPENAI_KEY"]

def detect_lang(text):
    cyrillic = len(re.findall(r'[а-яёА-ЯЁ]', text))
    total = len(text.replace(" ", "")) or 1
    return "RU" if cyrillic / total > 0.2 else "EN"

def translate(text, source_lang):
    target = "EN" if source_lang == "RU" else "RU"
    r = requests.post("https://api.deepl.com/v2/translate", data={
        "auth_key": DEEPL_KEY,
        "text": text,
        "source_lang": source_lang,
        "target_lang": target,
    })
    return r.json()["translations"][0]["text"]

def transcribe(file_path):
    with open(file_path, "rb") as f:
        r = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            files={"file": ("voice.ogg", f, "audio/ogg")},
            data={"model": "whisper-1"},
        )
    return r.json()["text"]

def handle_text(update, context):
    text = update.message.text
    if not text or text.startswith("/"):
        return
    lang = detect_lang(text)
    result = translate(text, lang)
    update.message.reply_text(result)

def handle_voice(update, context):
    update.message.reply_text("🎙 Секунду...")
    file = update.message.voice.get_file()
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        file.download(tmp.name)
        text = transcribe(tmp.name)
    lang = detect_lang(text)
    result = translate(text, lang)
    update.message.reply_text(f"📝 {text}\n\n🔄 {result}")

updater = Updater(BOT_TOKEN)
dp = updater.dispatcher
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
dp.add_handler(MessageHandler(Filters.voice, handle_voice))
updater.start_polling()
updater.idle()

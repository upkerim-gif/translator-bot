import os
import re
import requests
import tempfile
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ["BOT_TOKEN"]
DEEPL_KEY = os.environ["DEEPL_KEY"]
OPENAI_KEY = os.environ["OPENAI_KEY"]

def detect_lang(text):
    cyrillic = len(re.findall(r'[а-яёА-ЯЁ]', text))
    total = len(text.replace(" ", "")) or 1
    return "RU" if cyrillic / total > 0.2 else "EN"

def translate(text, source_lang):
    target = "EN" if source_lang == "RU" else "RU"
    r = requests.post("https://api-free.deepl.com/v2/translate",
        headers={"Authorization": f"DeepL-Auth-Key {DEEPL_KEY}"},
        json={"text": [text], "source_lang": source_lang, "target_lang": target}
    )
    data = r.json()
    if "translations" not in data:
        return f"Ошибка: {data}"
    return data["translations"][0]["text"]

def transcribe(file_path):
    with open(file_path, "rb") as f:
        r = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
            files={"file": ("voice.ogg", f, "audio/ogg")},
            data={"model": "whisper-1"},
        )
    return r.json()["text"]

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text or text.startswith("/"):
        return
    lang = detect_lang(text)
    result = translate(text, lang)
    await update.message.reply_text(result)

async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎙 Секунду...")
    file = await ctx.bot.get_file(update.message.voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        text = transcribe(tmp.name)
    lang = detect_lang(text)
    result = translate(text, lang)
    await update.message.reply_text(f"📝 {text}\n\n🔄 {result}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.run_polling()

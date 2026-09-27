import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبا! ابعثلي رابط تيك توك، يوتيوب، ولا انستقرام وناخذلك الفيديو.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("جاري التحميل، صبر شوية...")

    ydl_opts = {
        'outtmpl': 'video.%(ext)s',
        'format': 'mp4/best',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await update.message.reply_video(video=open(filename, 'rb'))
        os.remove(filename)
    except Exception as e:
        await update.message.reply_text(
            "ما قدرتش نحمل الفيديو 😕\nابعثلي الرابط فحسابي الرئيسي وحلها معاك: @memarwan7"
        )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()

if __name__ == "__main__":
    main()

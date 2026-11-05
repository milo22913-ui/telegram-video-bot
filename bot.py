# -*- coding: utf-8 -*-
"""
بوت تلغرام لتحميل فيديوهات تيك توك / يوتيوب / انستغرام بلا علامة مائية.
مجهز باش يخدم فوق Render (الطبقة المجانية) بلا توقف، بفضل:
  1. سيرفر Flask صغير داخلي (Render يحتاج بورت مفتوح باش يعتبر الخدمة "شغالة")
  2. البوت يخدم بالـ polling فـ thread منفصل
  3. UptimeRobot (خدمة خارجية مجانية) تبعث طلب كل 5 دقايق على رابط هذا
     السيرفر، باش Render ما يرقدش البوت
"""

import os
import logging
import threading
import tempfile

from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import yt_dlp

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# التوكن يُقرأ من متغير بيئة (Environment Variable) اسمو BOT_TOKEN
# فـ Render: Settings -> Environment -> Add Environment Variable
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

SUPPORTED_DOMAINS = ("tiktok.com", "youtube.com", "youtu.be", "instagram.com")


# =========================================================
# سيرفر Flask صغير - غرضو الوحيد إبقاء Render "صاحي"
# =========================================================

web_app = Flask(__name__)


@web_app.route("/")
def health_check():
    return "Bot is alive ✅"


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# =========================================================
# منطق تحميل الفيديو
# =========================================================

def download_video(url: str) -> str:
    """يحمل الفيديو ويرجع المسار تاع الملف فالسيرفر."""
    tmp_dir = tempfile.mkdtemp()
    output_template = os.path.join(tmp_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename


# =========================================================
# معالجات تلغرام
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "مرحباً! ابعثلي رابط تيك توك، يوتيوب، ولا انستقرام وناخذلك الفيديو."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()

    if not any(domain in text for domain in SUPPORTED_DOMAINS):
        await update.message.reply_text(
            "ابعثلي رابط صحيح من تيك توك، يوتيوب، ولا انستقرام."
        )
        return

    status_msg = await update.message.reply_text("جاري التحميل، صبر شوية...")

    try:
        file_path = download_video(text)
        with open(file_path, "rb") as video_file:
            await update.message.reply_video(video=video_file)
        await status_msg.delete()
        os.remove(file_path)
    except Exception as e:
        logger.error(f"خطأ فالتحميل: {e}")
        await status_msg.edit_text(
            "ما قدرتش نحمل الفيديو 😕\n"
            "تأكد من الرابط وحاول مرة أخرى."
        )


# =========================================================
# نقطة الانطلاق
# =========================================================

def run_bot() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("البوت بدا يخدم (polling)...")
    app.run_polling(close_loop=False)


def main() -> None:
    # نخليو البوت يخدم فـ thread منفصل
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # السيرفر Flask يخدم فـ thread رئيسي (هو لي Render يشوفو "شغال")
    run_web_server()


if __name__ == "__main__":
    main()

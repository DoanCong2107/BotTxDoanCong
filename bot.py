import os
import telebot
import yt_dlp
import tempfile
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import signal
import sys

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ Chưa set BOT_TOKEN!")

bot = telebot.TeleBot(TOKEN)

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        f"""🎵 **BOT NHẠC RAILWAY V4** 🎵 (Đã fix 409 & YouTube)

👋 Chào {message.from_user.first_name}!

✅ Đã fix lỗi Telegram 409 khi redeploy
✅ Bypass YouTube không cần cookies (nâng cao hơn)

📌 Dùng lệnh:
/play Anh nhớ em nhiều lắm remix

Thử ngay đi! 🔥""",
        parse_mode='Markdown', reply_markup=main_kb())

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "✅ Chỉ cần gõ `/play tên bài hát` là được.\nKhông cần cookies nữa!", parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    if text in ['🎵 tìm nhạc', '🎵 Tìm nhạc']:
        bot.reply_to(message, "Gõ `/play tên bài hát` nhé!")
        return
    if text in ['❓ hướng dẫn', '❓ Hướng dẫn']:
        help_cmd(message)
        return

    if not text.lower().startswith(('/play ', 'play ')):
        return

    query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
    if not query:
        bot.reply_to(message, "❌ Nhập tên bài hát hoặc link YouTube!")
        return

    status = bot.reply_to(message, "🔍 Đang tìm + tải (đã bypass YouTube)...")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'default_search': 'ytsearch',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,  # vẫn dùng nếu có
            'extractor_args': {
                'youtube': {
                    'player_client': ['web_safari', 'ios', 'android', 'web', 'web_embedded', 'ios_music'],
                    'player_skip': [],
                    'skip': ['dash', 'hls']
                }
            },
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Mobile/15E148 Safari/604.1',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Mobile/15E148 Safari/604.1',
                'Accept-Language': 'vi-VN,vi;q=0.9'
            },
            'geo_bypass': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')

            filename = ydl.prepare_filename(info)
            if not filename.endswith('.mp3'):
                filename = filename.rsplit('.', 1)[0] + '.mp3'

            if duration > 1800:
                bot.edit_message_text("❌ Bài quá dài (>30 phút)", status.chat.id, status.message_id)
                return

        bot.edit_message_text(f"⬇️ Đang gửi: **{title}**...", status.chat.id, status.message_id, parse_mode='Markdown')

        with open(filename, 'rb') as audio:
            bot.send_audio(
                message.chat.id, audio,
                caption=f"🎵 **{title}**\n👤 {uploader}\n⏱ {time.strftime('%M:%S', time.gmtime(duration))}",
                title=title, performer=uploader,
                parse_mode='Markdown',
                reply_to_message_id=message.message_id
            )

        bot.delete_message(status.chat.id, status.message_id)

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        err = str(e)[:200]
        if "Sign in" in err or "confirm you're not a bot" in err:
            txt = "❌ Vẫn lỗi YouTube.\n✅ Thử lại sau 5 phút hoặc dùng máy tính lấy cookies.txt gửi mình."
        else:
            txt = f"❌ Lỗi: {err}"
        bot.edit_message_text(txt, status.chat.id, status.message_id)

# === PHẦN FIX LỖI 409 KHI REDEPLOY ===
def signal_handler(sig, frame):
    print("🛑 Nhận lệnh tắt từ Railway... Đang dừng bot.")
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

print("🚀 Bot Nhạc V4 (đã fix 409) đang chạy trên Railway...")
bot.infinity_polling()
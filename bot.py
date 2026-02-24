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
        f"""🎵 **BOT NHẠC RAILWAY V6** 🎵 (Fix YouTube 2026)

👋 Chào {message.from_user.first_name}!

✅ Đã nâng cấp bypass "Sign in to confirm you're not a bot" (cookies + user-agent mới)
✅ Fix tìm kiếm nếu không có kết quả

📌 Dùng lệnh:
/play Anh nhớ em nhiều lắm remix

Thử lại ngay! 🔥""",
        parse_mode='Markdown', reply_markup=main_kb())

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "✅ Chỉ cần gõ `/play tên bài hát` hoặc link. Đã fix lỗi tìm kiếm và format!", parse_mode='Markdown')

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
        bot.reply_to(message, "❌ Nhập tên bài hoặc link!")
        return

    status = bot.reply_to(message, "🔍 Đang tìm + tải (đã bypass YouTube)...")

    try:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',  # Fallback
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
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'web', 'web_safari', 'ios_music', 'web_embedded'],
                    'player_skip': ['js', 'configs', 'web_prereqs'],
                    'skip': ['dash', 'hls', 'authcheck']
                }
            },
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',  # Mới 2026
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
            },
            'geo_bypass': True,
            'prefer_ffmpeg': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                if not info['entries']:
                    raise Exception("Không tìm thấy bài hát nào! Thử tên chính xác hơn hoặc link khác.")
                info = info['entries'][0]

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')

            filename = ydl.prepare_filename(info)
            if not filename.endswith('.mp3'):
                filename = filename.rsplit('.', 1)[0] + '.mp3'

            if duration > 1800:
                bot.edit_message_text("❌ Bài quá dài (>30 phút)", status.chat.id, status.message_id)
                if os.path.exists(filename):
                    os.remove(filename)
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
            txt = "❌ Lỗi YouTube: Cookies.txt hết hạn hoặc không khớp. Lấy mới từ Chrome và upload lại!"
        elif "index out of range" in err:
            txt = "❌ Không tìm thấy bài hát! Th
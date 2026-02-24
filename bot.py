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
    raise ValueError("❌ Chưa set BOT_TOKEN trên Railway!")

bot = telebot.TeleBot(TOKEN)

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"""🎵 **BOT NHẠC RAILWAY V6** 🎵 (Python 3.12.3)

Chào {message.from_user.first_name}!

✅ Đã fix lỗi "Sign in to confirm you're not a bot"
✅ Fix lỗi tìm kiếm không có kết quả
✅ Fix lỗi format audio không khả dụng

Dùng lệnh:
/play tên bài hát
/play link YouTube

Thử ngay: /play Anh nhớ em nhiều lắm remix

Chúc nghe nhạc vui! 🔥""",
        parse_mode='Markdown',
        reply_markup=main_kb()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        """✅ Chỉ cần gõ `/play tên bài hát` hoặc link YouTube.
Đã fix lỗi tìm kiếm và format audio.
Nếu vẫn lỗi YouTube → lấy cookies.txt mới và upload lại.""",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip().lower()

    if text in ['🎵 tìm nhạc', 'tìm nhạc']:
        bot.reply_to(message, "Gõ lệnh `/play tên bài hát` nhé!")
        return

    if text in ['❓ hướng dẫn', 'hướng dẫn']:
        help_cmd(message)
        return

    if not text.startswith(('/play ', 'play ')):
        return

    query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
    if not query:
        bot.reply_to(message, "❌ Vui lòng nhập tên bài hát hoặc link YouTube!")
        return

    status = bot.reply_to(message, "🔍 Đang tìm và tải nhạc...")

    try:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
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
                    'player_client': ['ios', 'android', 'web', 'web_safari', 'ios_music'],
                    'player_skip': ['js', 'configs', 'web_prereqs'],
                    'skip': ['dash', 'hls', 'authcheck']
                }
            },
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
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
                    raise Exception("Không tìm thấy kết quả nào phù hợp!")
                info = info['entries'][0]

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')

            filename = ydl.prepare_filename(info)
            if not filename.endswith('.mp3'):
                filename = filename.rsplit('.', 1)[0] + '.mp3'

            if duration > 1800:  # > 30 phút
                bot.edit_message_text(
                    "❌ Bài hát quá dài (>30 phút), không hỗ trợ!",
                    status.chat.id, status.message_id
                )
                if os.path.exists(filename):
                    os.remove(filename)
                return

        bot.edit_message_text(
            f"⬇️ Đang gửi file: **{title}**...",
            status.chat.id, status.message_id,
            parse_mode='Markdown'
        )

        with open(filename, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=f"🎵 **{title}**\n👤 {uploader}\n⏱ {time.strftime('%M:%S', time.gmtime(duration))}",
                title=title,
                performer=uploader,
                parse_mode='Markdown',
                reply_to_message_id=message.message_id
            )

        bot.delete_message(status.chat.id, status.message_id)

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        err_str = str(e)[:250]
        if "Sign in to confirm you're not a bot" in err_str:
            msg = "❌ Lỗi YouTube: cần cookies.txt mới. Hãy lấy lại từ Chrome và upload lên Railway!"
        elif "Không tìm thấy kết quả" in err_str or "entries" in err_str:
            msg = "❌ Không tìm thấy bài hát. Thử tên chính xác hơn hoặc dùng link YouTube đầy đủ!"
        elif "format is not available" in err_str:
            msg = "❌ Video không hỗ trợ tải audio chất lượng cao. Thử link khác!"
        else:
            msg = f"❌ Lỗi: {err_str}"

        bot.edit_message_text(msg, status.chat.id, status.message_id)

# Graceful shutdown để tránh lỗi 409 khi redeploy
def signal_handler(sig, frame):
    print("🛑 Railway yêu cầu dừng bot... Đang shutdown.")
    bot.stop_polling()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

print("🚀 Bot Nhạc đang chạy trên Python 3.12.3...")
bot.infinity_polling()
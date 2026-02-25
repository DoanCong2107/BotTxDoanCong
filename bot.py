import os
import telebot
import yt_dlp
import tempfile
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

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
        f"""🎵 **BOT TẢI NHẠC MP3 (Speed 1.15x)**

Chào {message.from_user.first_name}!
Tất cả nhạc sẽ tự động được tăng tốc lên **1.15x**.

📌 Gõ lệnh:
/play tên bài hát
/play link YouTube

Ví dụ:
/play Anh nhớ em nhiều lắm remix""",
        parse_mode='Markdown',
        reply_markup=main_kb()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        """🎵 **HƯỚNG DẪN CHI TIẾT**

/play tên bài hát hoặc link YouTube
Hệ thống tự động apply filter `atempo=1.15`.

Nếu lỗi:
- Cần file `nixpacks.toml` trên Railway để chạy FFmpeg.
- "Sign in..." → Cập nhật cookies.txt mới.

Chúc nghe nhạc vui! 🎧""",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    if text.lower() in ['🎵 tìm nhạc', 'tìm nhạc']:
        bot.reply_to(message, "Gõ /play tên bài hát hoặc link nhé!")
        return
    if text.lower() in ['❓ hướng dẫn', 'hướng dẫn']:
        help_cmd(message)
        return

    if not text.lower().startswith(('/play ', 'play ')):
        return

    query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
    if not query:
        bot.reply_to(message, "❌ Nhập tên bài hát hoặc link YouTube!")
        return

    status = bot.reply_to(message, "🔍 Đang tìm + tải nhạc (Speed 1.15x)...")

    try:
        # Cấu hình tối ưu để tránh lỗi format và lỗi xử lý file trên Railway
        ydl_opts = {
            'format': 'bestaudio/best', # Lấy audio tốt nhất sẵn có
            'default_search': 'ytsearch1',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            # Lưu bằng ID để FFmpeg xử lý không bị lỗi ký tự đặc biệt
            'outtmpl': 'track_%(id)s.%(ext)s', 
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # TĂNG TỐC 1.15x
            'postprocessor_args': [
                '-filter:a', 'atempo=1.15'
            ],
            'noplaylist': True,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            new_duration = int(duration / 1.15) # Thời lượng thực tế sau khi tăng tốc
            uploader = info.get('uploader', 'Unknown')

            # Xác định tên file sau khi FFmpeg đã convert sang mp3
            filename = f"track_{info['id']}.mp3"

            if duration > 2400: # Giới hạn 40 phút
                bot.edit_message_text("❌ Bài quá dài (>40 phút)", status.chat.id, status.message_id)
                if os.path.exists(filename): os.remove(filename)
                return

        bot.edit_message_text(f"⬇️ Đang gửi file: **{title}** (1.15x)...", status.chat.id, status.message_id, parse_mode='Markdown')

        with open(filename, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=f"🎵 **{title} (1.15x)**\n👤 {uploader}\n⏱ {time.strftime('%M:%S', time.gmtime(new_duration))}",
                title=f"{title} (1.15x)",
                performer=uploader,
                parse_mode='Markdown',
                reply_to_message_id=message.message_id
            )

        bot.delete_message(status.chat.id, status.message_id)
        if os.path.exists(filename): os.remove(filename)

    except Exception as e:
        err = str(e)[:200]
        bot.edit_message_text(f"❌ Lỗi: {err}", status.chat.id, status.message_id)
        # Dọn dẹp file rác nếu lỗi
        for f in os.listdir('.'):
            if f.startswith("track_"): os.remove(f)

print("🚀 Bot Nhạc 1.15x đang chạy...")
bot.infinity_polling()

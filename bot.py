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

📌 Cách dùng:
/play tên bài hát
/play link YouTube""",
        parse_mode='Markdown',
        reply_markup=main_kb()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        """🎵 **HƯỚNG DẪN**
- Dùng `/play` kèm tên bài hoặc link.
- Nếu lỗi: Đảm bảo server đã cài FFmpeg.
- Tốc độ mặc định: 1.15x (vừa đủ hay, không méo giọng).""",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    if text.lower() in ['🎵 tìm nhạc', 'tìm nhạc']:
        bot.reply_to(message, "Gõ /play + tên bài hát nhé!")
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

    status = bot.reply_to(message, "🔍 Đang xử lý 1.15x (Vui lòng đợi)...")

    try:
        # Cấu hình yt-dlp tối ưu
        ydl_opts = {
            # Chọn audio tốt nhất bất kể định dạng nào để tránh lỗi "format not available"
            'format': 'bestaudio/best',
            'default_search': 'ytsearch1',
            'quiet': True,
            'no_warnings': True,
            # Lưu file bằng ID để tránh lỗi ký tự đặc biệt trong tên file
            'outtmpl': '%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # Tăng tốc 1.15x bằng FFmpeg
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
            new_duration = int(duration / 1.15)
            uploader = info.get('uploader', 'Unknown')
            
            # File sau khi xử lý xong sẽ có đuôi .mp3
            filename = f"{info['id']}.mp3"

            if duration > 2400: # Giới hạn 40 phút
                bot.edit_message_text("❌ Video quá dài!", status.chat.id, status.message_id)
                if os.path.exists(filename): os.remove(filename)
                return

        bot.edit_message_text(f"📤 Đang gửi: **{title}**", status.chat.id, status.message_id, parse_mode='Markdown')

        with open(filename, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=f"🎵 **{title} (1.15x)**\n⏱ {time.strftime('%M:%S', time.gmtime(new_duration))}",
                title=f"{title} (1.15x)",
                performer=uploader,
                reply_to_message_id=message.message_id
            )

        bot.delete_message(status.chat.id, status.message_id)
        if os.path.exists(filename): os.remove(filename)

    except Exception as e:
        error_str = str(e)
        bot.edit_message_text(f"❌ Lỗi: {error_str[:150]}", status.chat.id, status.message_id)
        # Dọn dẹp nếu có file rác
        for f in os.listdir('.'):
            if f.endswith((".mp3", ".webm", ".m4a")):
                 if len(f) > 5: os.remove(f)

print("🚀 Bot đã sẵn sàng!")
bot.infinity_polling()

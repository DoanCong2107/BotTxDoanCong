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

SPEED = 1.15  # Lock tốc độ ở 1.15x

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"""🎵 **BOT NHẠC MP3 TỰ ĐỘNG 1.15x**

Chào {message.from_user.first_name}!

Tất cả bài hát sẽ tự động được tăng tốc độ phát lên **1.15x** (nhạc nhanh hơn 15%) mà không cần chọn.

📌 Gõ lệnh:
/play tên bài hát
/play link YouTube

Ví dụ:
/play Anh nhớ em nhiều lắm remix

Chơi nhạc vui nhé! 🔥""",
        parse_mode='Markdown',
        reply_markup=main_kb()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        """🎵 **HƯỚNG DẪN**

/play tên bài hát hoặc link YouTube

Tất cả nhạc sẽ tự động phát ở tốc độ **1.15x** (nhanh hơn 15%).

Nếu lỗi:
- "Sign in..." → upload cookies.txt mới từ Chrome (extension Get cookies.txt LOCALLY)
- "Không hỗ trợ audio..." → thử link dài hơn
- "Video unavailable" → video bị chặn, thử bài khác

Thêm bot vào group cũng dùng được!""",
        parse_mode='Markdown'
    )

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    if text in ['🎵 tìm nhạc', 'tìm nhạc']:
        bot.reply_to(message, "Gõ /play tên bài hát hoặc link nhé!")
        return
    if text in ['❓ hướng dẫn', 'hướng dẫn']:
        help_cmd(message)
        return

    if not text.lower().startswith(('/play ', 'play ')):
        return

    query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
    if not query:
        bot.reply_to(message, "❌ Nhập tên bài hát hoặc link YouTube!")
        return

    status = bot.reply_to(message, f"🔍 Đang tìm + xử lý nhạc ở tốc độ {SPEED}x...")

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
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                if not info['entries']:
                    raise Exception("Không tìm thấy bài hát!")
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

        # Tạo file mới với tốc độ 1.15x
        temp_dir = tempfile.gettempdir()
        spedup_filename = os.path.join(temp_dir, f"spedup_{SPEED}_{os.path.basename(filename)}")

        # FFmpeg tăng tốc độ phát (atempo filter)
        os.system(f'ffmpeg -y -i "{filename}" -filter:a "atempo={SPEED}" -vn "{spedup_filename}" -loglevel quiet')

        if not os.path.exists(spedup_filename):
            raise Exception("Không thể tăng tốc độ file")

        bot.edit_message_text(f"⬇️ Đang gửi file ở tốc độ {SPEED}x: **{title}**...", status.chat.id, status.message_id, parse_mode='Markdown')

        with open(spedup_filename, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=f"🎵 **{title}** (tốc độ {SPEED}x)\n👤 {uploader}\n⏱ {time.strftime('%M:%S', time.gmtime(duration / SPEED))}",
                title=f"{title} ({SPEED}x)",
                performer=uploader,
                reply_to_message_id=message.message_id
            )

        bot.delete_message(status.chat.id, status.message_id)

        # Xóa file tạm
        os.remove(filename)
        os.remove(spedup_filename)

    except Exception as e:
        err = str(e)[:200]
        if "Sign in" in err or "confirm you're not a bot" in err:
            msg = "❌ Lỗi YouTube: cần cookies.txt mới. Lấy từ Chrome và upload lại!"
        elif "unavailable" in err or "not available" in err:
            msg = "❌ Video không khả dụng hoặc bị chặn khu vực. Thử tên/link khác!"
        elif "format" in err or "not available" in err:
            msg = "❌ Video không hỗ trợ audio chất lượng cao. Thử link video dài hơn!"
        else:
            msg = f"❌ Lỗi: {err}"
        bot.edit_message_text(msg, status.chat.id, status.message_id)

print("🚀 Bot Nhạc MP3 tự động 1.15x đang chạy...")
bot.infinity_polling()
import os
import telebot
import yt_dlp
import tempfile
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ Chưa set BOT_TOKEN trên Railway!")

bot = telebot.TeleBot(TOKEN)

# Lưu dữ liệu tạm cho từng user khi chọn speed
user_data = {}

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

def speed_kb():
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("1x (Bình thường)", callback_data="speed_1.0"),
        InlineKeyboardButton("1.15x", callback_data="speed_1.15"),
        InlineKeyboardButton("1.25x", callback_data="speed_1.25"),
        InlineKeyboardButton("1.5x", callback_data="speed_1.5"),
        InlineKeyboardButton("2x (Nhanh)", callback_data="speed_2.0")
    )
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"""🎵 **BOT TẢI NHẠC MP3** (YouTube → MP3)

Chào {message.from_user.first_name}!

📌 Gõ lệnh:
/play tên bài hát
/play link YouTube

Sau khi bot tìm được bài, anh có thể chọn **tốc độ phát** bằng nút (1x, 1.15x, 1.25x, 1.5x, 2x)!

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

Sau khi tìm thấy bài, chọn tốc độ phát bằng nút (1x, 1.15x, 1.25x, 1.5x, 2x).

Nếu lỗi:
- "Sign in..." → upload cookies.txt mới từ Chrome
- "Video unavailable" → thử tên bài + "full" hoặc "lyrics"
- "Không hỗ trợ audio..." → thử link video dài hơn

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

    user_data[message.from_user.id] = {'query': query}  # Lưu query tạm

    status = bot.reply_to(message, "🔍 Đang tìm nhạc...")

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

        # Lưu filename để dùng khi chọn speed
        user_data[message.from_user.id]['filename'] = filename
        user_data[message.from_user.id]['title'] = title
        user_data[message.from_user.id]['uploader'] = uploader
        user_data[message.from_user.id]['duration'] = duration

        bot.edit_message_text(
            f"🎵 **Tìm thấy: {title}**\nChọn tốc độ phát:",
            status.chat.id, status.message_id,
            parse_mode='Markdown',
            reply_markup=speed_kb()
        )

    except Exception as e:
        err = str(e)[:200]
        if "Sign in" in err or "confirm you're not a bot" in err:
            msg = "❌ Lỗi YouTube: cần cookies.txt mới. Lấy từ Chrome và upload lại!"
        else:
            msg = f"❌ Lỗi: {err}"
        bot.edit_message_text(msg, status.chat.id, status.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('speed_'))
def callback_speed(call):
    user_id = call.from_user.id
    if user_id not in user_data or 'filename' not in user_data[user_id]:
        bot.answer_callback_query(call.id, "Hết hạn, hãy tìm bài mới bằng /play!")
        return

    speed = float(call.data.split('_')[1])
    data = user_data[user_id]
    filename = data['filename']
    title = data['title']
    uploader = data['uploader']
    duration = data['duration']

    bot.answer_callback_query(call.id, f"Đang xử lý ở tốc độ {speed}x...")

    try:
        temp_dir = tempfile.gettempdir()
        spedup_filename = os.path.join(temp_dir, f"spedup_{speed}_{os.path.basename(filename)}")

        # FFmpeg tăng tốc độ phát
        os.system(f'ffmpeg -y -i "{filename}" -filter:a "atempo={speed}" -vn "{spedup_filename}" -loglevel quiet')

        if not os.path.exists(spedup_filename):
            raise Exception("Không thể tăng tốc độ file")

        bot.send_audio(
            call.message.chat.id,
            open(spedup_filename, 'rb'),
            caption=f"🎵 **{title}** (tốc độ {speed}x)\n👤 {uploader}\n⏱ {time.strftime('%M:%S', time.gmtime(duration / speed))}",
            title=f"{title} ({speed}x)",
            performer=uploader,
            reply_to_message_id=call.message.message_id
        )

        os.remove(spedup_filename)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Lỗi khi tăng tốc: {str(e)[:200]}")

    finally:
        if os.path.exists(filename):
            os.remove(filename)
        if user_id in user_data:
            del user_data[user_id]

print("🚀 Bot Nhạc MP3 với nút chọn speed đang chạy...")
bot.infinity_polling()
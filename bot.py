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

# Hàm tạo bàn phím chính
def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"Chào {message.from_user.first_name}! Gửi /play + tên bài hát để tải nhạc nhé.",
        reply_markup=main_kb()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    help_text = "📌 **Hướng dẫn:**\n/play [tên bài hát]\n/play [link youtube]\n\nVí dụ: `/play Chạy ngay đi`"
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

# Sử dụng command handler thay vì lọc text thủ công
@bot.message_handler(commands=['play'])
def play_handler(message):
    # Lấy phần nội dung sau lệnh /play
    query = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    
    if not query:
        bot.reply_to(message, "❌ Vui lòng nhập tên bài hát! (VD: /play Em của ngày hôm qua)")
        return

    status = bot.reply_to(message, "🔍 Đang xử lý... (Vui lòng đợi 10-30s)")

    # Tạo thư mục tạm an toàn
    tmp_dir = tempfile.gettempdir()
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1', # Tìm 1 kết quả duy nhất nếu là text
        'quiet': True,
        'no_warnings': True,
        'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'), # Dùng ID để tránh lỗi ký tự đặc biệt ở tên file
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # Fix lỗi YouTube chặn bot
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Trích xuất thông tin
            info = ydl.extract_info(query, download=True)
            
            # Nếu tìm kiếm bằng từ khóa, lấy phần tử đầu tiên
            if 'entries' in info:
                video_info = info['entries'][0]
            else:
                video_info = info

            title = video_info.get('title', 'Music')
            file_id = video_info.get('id')
            duration = video_info.get('duration', 0)
            uploader = video_info.get('uploader', 'Unknown')
            # Đường dẫn file sau khi convert (luôn là .mp3 do postprocessor)
            expected_filename = os.path.join(tmp_dir, f"{file_id}.mp3")

            if duration > 1200: # Giới hạn 20 phút để tránh quá tải
                bot.edit_message_text("❌ Video quá dài (giới hạn 20p).", status.chat.id, status.message_id)
                if os.path.exists(expected_filename): os.remove(expected_filename)
                return

            # Gửi file
            bot.edit_message_text(f"📤 Đang tải lên: {title}", status.chat.id, status.message_id)
            
            with open(expected_filename, 'rb') as audio:
                bot.send_audio(
                    message.chat.id,
                    audio,
                    caption=f"🎵 {title}\n👤 {uploader}",
                    title=title,
                    performer=uploader,
                    reply_to_message_id=message.message_id
                )

            bot.delete_message(status.chat.id, status.message_id)
            
            # Dọn dẹp file
            if os.path.exists(expected_filename):
                os.remove(expected_filename)

    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        bot.edit_message_text(f"❌ Có lỗi xảy ra: {error_msg[:100]}...", status.chat.id, status.message_id)

# Xử lý nút bấm từ bàn phím
@bot.message_handler(func=lambda m: True)
def text_handler(message):
    if "tìm nhạc" in message.text.lower():
        bot.reply_to(message, "Hãy dùng lệnh: `/play + tên bài hát`", parse_mode='Markdown')
    elif "hướng dẫn" in message.text.lower():
        help_cmd(message)

print("🚀 Bot is running...")
bot.infinity_polling()

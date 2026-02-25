import os
import telebot
import yt_dlp
import tempfile
import time
import subprocess
import shutil

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# ====================== CẤU HÌNH BOT ======================
# Lấy token từ biến môi trường Railway
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ Chưa set BOT_TOKEN trên Railway!")

# Khởi tạo bot
bot = telebot.TeleBot(TOKEN)

# ====================== CẤU HÌNH TĂNG TỐC ======================
# Tốc độ bạn muốn (1.15x là nhẹ nhàng, tự nhiên nhất)
SPEED_FACTOR = 1.15
SPEED_TEXT = f"{SPEED_FACTOR}x"

# ====================== KEYBOARD MENU ======================
def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

# ====================== LỆNH /START ======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"""🎵 **BOT TẢI NHẠC MP3 TĂNG TỐC {SPEED_TEXT}**

Chào {message.from_user.first_name}!

📌 Gõ lệnh:
/play tên bài hát
/play link YouTube

✅ Tự động tăng tốc {SPEED_TEXT} (giữ nguyên cao độ giọng nói)
✅ Chất lượng audio gì cũng được (128kbps, đủ nghe)
⚠️ File tối đa \~50MB (giới hạn Telegram)
⚠️ Nếu lỗi Sign in → upload cookies.txt mới

Chơi nhạc vui nhé! 🔥""",
        parse_mode='Markdown',
        reply_markup=main_kb()
    )

# ====================== LỆNH /HELP ======================
@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        f"""🎵 **HƯỚNG DẪN CHI TIẾT**

/play vinagang
/play Anh nhớ em nhiều lắm remix
/play https://youtu.be/...

✅ Tăng tốc {SPEED_TEXT} bằng ffmpeg
✅ Hỗ trợ TẤT CẢ nhạc Việt (kể cả remix ngắn, Short, DJ)

Lỗi thường gặp:
• "không hỗ trợ audio" → giờ đã fix, thử lại!
• "Sign in to confirm..." → upload cookies.txt mới
• "Video không khả dụng" → thử tên bài khác

Thêm bot vào group cũng dùng được!

Chúc nghe nhạc vui vẻ! 🎧""",
        parse_mode='Markdown'
    )

# ====================== XỬ LÝ TẤT CẢ TIN NHẮN ======================
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip().lower()

    # Xử lý nút keyboard
    if text in ['🎵 tìm nhạc', 'tìm nhạc']:
        bot.reply_to(message, "Gõ /play tên bài hát hoặc link YouTube nhé!")
        return
    if text in ['❓ hướng dẫn', 'hướng dẫn']:
        help_cmd(message)
        return

    # Chỉ xử lý lệnh bắt đầu bằng /play hoặc play
    if not text.startswith(('/play ', 'play ')):
        return

    # Lấy nội dung sau /play
    query = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not query:
        bot.reply_to(message, "❌ Nhập tên bài hát hoặc link YouTube!")
        return

    # Gửi thông báo đang xử lý
    status = bot.reply_to(message, "🔍 Đang tìm + tải + tăng tốc...")

    # Tạo file tạm thời
    temp_dir = tempfile.gettempdir()
    original_mp3 = os.path.join(temp_dir, f"orig_{int(time.time())}.mp3")
    spedup_mp3 = os.path.join(temp_dir, f"sped_{int(time.time())}.mp3")

    try:
        # Cấu hình yt-dlp - ĐÃ CHỈNH CHO CHẤT LƯỢNG GÌ CŨNG ĐƯỢC
        ydl_opts = {
            'format': 'best',                     # ← DÒNG QUAN TRỌNG: lấy bất kỳ format nào có audio
            'default_search': 'ytsearch',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'outtmpl': original_mp3,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',        # ← Hạ xuống 128kbps để dễ tải hơn, vẫn nghe tốt
            }],
            'noplaylist': True,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8'
            },
            'geo_bypass': True,
        }

        # Tải nhạc
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                if not info['entries']:
                    raise Exception("Không tìm thấy bài hát nào!")
                info = info['entries'][0]

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')

            if duration > 1800:
                raise Exception("Bài quá dài (>30 phút)")

        # Thông báo đang tăng tốc
        bot.edit_message_text(f"⚡ Đang tăng tốc {SPEED_TEXT} + gửi file: **{title}**...", 
                              status.chat.id, status.message_id, parse_mode='Markdown')

        # Kiểm tra ffmpeg
        if not shutil.which("ffmpeg"):
            raise Exception("❌ FFmpeg NOT found in PATH!")

        # Chạy ffmpeg tăng tốc
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", original_mp3,
            "-filter:a", f"atempo={SPEED_FACTOR}",
            "-b:a", "128k",                       # ← Hạ bitrate để file nhẹ
            spedup_mp3
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ffmpeg lỗi: {result.stderr[:150]}")

        # Tính thời lượng mới
        new_duration = int(duration / SPEED_FACTOR)

        # Gửi file
        bot.edit_message_text(f"⬇️ Đang gửi file tăng tốc {SPEED_TEXT}: **{title}**...", 
                              status.chat.id, status.message_id, parse_mode='Markdown')

        with open(spedup_mp3, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=f"🎵 **{title}** (tăng tốc {SPEED_TEXT})\n👤 {uploader}\n⏱ {time.strftime('%M:%S', time.gmtime(new_duration))}",
                title=f"{title} ({SPEED_TEXT})",
                performer=uploader,
                parse_mode='Markdown',
                reply_to_message_id=message.message_id
            )

        bot.delete_message(status.chat.id, status.message_id)

    except Exception as e:
        err = str(e)[:250]
        if "format is not available" in err:
            msg = "❌ Vẫn không tải được (hiếm). Thử link video dài hơn hoặc tên bài khác!"
        elif "Sign in" in err or "confirm you're not a bot" in err:
            msg = "❌ Lỗi YouTube: cần cookies.txt mới!"
        elif "unavailable" in err or "not available" in err:
            msg = "❌ Video không khả dụng hoặc bị chặn khu vực!"
        elif "ffmpeg" in err:
            msg = "❌ Lỗi tăng tốc ffmpeg. Redeploy lại!"
        else:
            msg = f"❌ Lỗi: {err}"
        bot.edit_message_text(msg, status.chat.id, status.message_id)

    finally:
        # Xóa file tạm
        for f in [original_mp3, spedup_mp3]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

# ====================== KHỞI ĐỘNG BOT ======================
print("🚀 Bot Nhạc MP3 Tăng Tốc đang chạy...")
bot.infinity_polling()
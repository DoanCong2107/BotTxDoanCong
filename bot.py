import os
import telebot
import yt_dlp
import tempfile
import time
import subprocess
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ Chưa set BOT_TOKEN trên Railway!")

bot = telebot.TeleBot(TOKEN)

# Cấu hình tốc độ - bạn chỉnh ở đây
SPEED_FACTOR = 1.15          # 1.25, 1.5, 1.75, 2.0, hoặc chain như "2.0,1.5" cho 3x
SPEED_TEXT = f"{SPEED_FACTOR}x" if ',' not in str(SPEED_FACTOR) else "3x"  # hiển thị caption

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"""🎵 **BOT TẢI NHẠC MP3 TĂNG TỐC** (YouTube → MP3 {SPEED_TEXT})

Chào {message.from_user.first_name}!

📌 Gõ lệnh:
/play tên bài hát
/play link YouTube

Ví dụ:
/play Anh nhớ em nhiều lắm remix
/play https://youtu.be/...

✅ Tự động tăng tốc {SPEED_TEXT} (nghe nhanh hơn, vẫn giữ giọng tự nhiên)
✅ Chất lượng cao nhất có thể (192kbps+)
⚠️ File max \~50MB (giới hạn Telegram)
⚠️ Nếu lỗi "Sign in..." → upload cookies.txt mới

Chơi nhạc vui nhé! 🔥""",
        parse_mode='Markdown',
        reply_markup=main_kb()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,
        f"""🎵 **HƯỚNG DẪN CHI TIẾT**

/play tên bài hát hoặc link YouTube

Tính năng:
- Tự động tăng tốc {SPEED_TEXT} bằng ffmpeg (atempo)
- Giữ nguyên cao độ giọng nói
- Caption có ghi rõ tốc độ

Nếu lỗi:
- "Sign in..." → Lấy cookies.txt mới từ Chrome → upload lên Railway
- "Video unavailable" → Thử bài khác
- File quá lớn → Do bài dài + tăng tốc vẫn >50MB, thử bài ngắn hơn

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

    status = bot.reply_to(message, "🔍 Đang tìm + tải + tăng tốc...")

    try:
        # Tạo thư mục tạm nếu cần
        temp_dir = tempfile.gettempdir()
        original_mp3 = os.path.join(temp_dir, f"orig_{int(time.time())}.mp3")
        spedup_mp3 = os.path.join(temp_dir, f"sped_{int(time.time())}.mp3")

        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'default_search': 'ytsearch',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'outtmpl': original_mp3,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
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

        bot.edit_message_text(f"⚡ Đang tăng tốc {SPEED_TEXT} + gửi file: **{title}**...", 
                              status.chat.id, status.message_id, parse_mode='Markdown')

        # Tăng tốc bằng ffmpeg
        atempo_filter = f"atempo={SPEED_FACTOR}" if ',' not in str(SPEED_FACTOR) else SPEED_FACTOR

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", original_mp3,
            "-filter:a", atempo_filter,
            "-b:a", "192k",
            spedup_mp3
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"ffmpeg lỗi: {result.stderr[:150]}")

        # Tính duration mới (ước lượng)
        new_duration = int(duration / float(SPEED_FACTOR)) if ',' not in str(SPEED_FACTOR) else int(duration / 3)

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
        err = str(e)[:200]
        if "Sign in" in err or "confirm you're not a bot" in err:
            msg = "❌ Lỗi YouTube: cần cookies.txt mới!"
        elif "unavailable" in err or "not available" in err:
            msg = "❌ Video không khả dụng hoặc bị chặn khu vực!"
        elif "format" in err or "audio" in err:
            msg = "❌ Video không hỗ trợ audio chất lượng cao. Thử link khác!"
        elif "ffmpeg" in err:
            msg = f"❌ Lỗi tăng tốc: {err}"
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

print("🚀 Bot Nhạc MP3 Tăng Tốc đang chạy...")
bot.infinity_polling()
import os
import telebot
import yt_dlp
import tempfile
import time
import subprocess
import shutil
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ Chưa set BOT_TOKEN trên Railway!")

bot = telebot.TeleBot(TOKEN)

# ================== CẤU HÌNH TỐC ĐỘ ==================
SPEED_FACTOR = 1.15          # Bạn muốn đổi thì sửa ở đây (1.25, 1.5, 2.0...)
SPEED_TEXT = f"{SPEED_FACTOR}x"

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"""🎵 **BOT TẢI NHẠC MP3 TĂNG TỐC** ({SPEED_TEXT})

Chào {message.from_user.first_name}!

📌 Gõ:
/play tên bài hát
/play link YouTube

✅ Tự động tăng tốc {SPEED_TEXT} (giữ giọng tự nhiên)
✅ Chất lượng 192kbps
⚠️ File ≤ 50MB (Telegram giới hạn)

Chơi nhạc vui nhé! 🔥""",
        parse_mode='Markdown',
        reply_markup=main_kb()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, f"""🎵 **HƯỚNG DẪN**

/play vinagang
/play Anh nhớ em nhiều lắm
/play https://youtu.be/...

Tính năng:
• Tăng tốc {SPEED_TEXT} bằng ffmpeg
• Hỗ trợ hầu hết nhạc Việt (remix, DJ...)

Lỗi thường gặp:
• "không hỗ trợ audio" → thử link video dài hơn
• "Sign in..." → upload cookies.txt mới

Chúc nghe vui! 🎧""", parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip().lower()
    if text in ['🎵 tìm nhạc', 'tìm nhạc']:
        bot.reply_to(message, "Gõ /play tên bài hát hoặc link nhé!")
        return
    if text in ['❓ hướng dẫn', 'hướng dẫn']:
        help_cmd(message)
        return

    if not text.startswith(('/play ', 'play ')):
        return

    query = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not query:
        bot.reply_to(message, "❌ Nhập tên bài hát hoặc link YouTube!")
        return

    status = bot.reply_to(message, "🔍 Đang tìm + tải + tăng tốc...")

    temp_dir = tempfile.gettempdir()
    original_mp3 = os.path.join(temp_dir, f"orig_{int(time.time())}.mp3")
    spedup_mp3 = os.path.join(temp_dir, f"sped_{int(time.time())}.mp3")

    try:
        ydl_opts = {
            'format': 'bestaudio/best',           # ← ĐÃ SỬA: linh hoạt hơn cho nhạc Việt
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
                    raise Exception("Không tìm thấy bài hát!")
                info = info['entries'][0]

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')

            if duration > 1800:
                raise Exception("Bài quá dài (>30 phút)")

        bot.edit_message_text(f"⚡ Đang tăng tốc {SPEED_TEXT} + gửi: **{title}**...", 
                              status.chat.id, status.message_id, parse_mode='Markdown')

        # Debug ffmpeg
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            print(f"✅ FFmpeg found at: {ffmpeg_path}")
        else:
            raise Exception("❌ FFmpeg NOT found in PATH!")

        # Tăng tốc
        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", original_mp3,
            "-filter:a", f"atempo={SPEED_FACTOR}",
            "-b:a", "192k",
            spedup_mp3
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"ffmpeg lỗi: {result.stderr[:150]}")

        new_duration = int(duration / SPEED_FACTOR)

        bot.edit_message_text(f"⬇️ Đang gửi file {SPEED_TEXT}: **{title}**...", 
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
            msg = "❌ Video không hỗ trợ audio chất lượng cao (thường là remix ngắn/Short). Thử link video dài hơn!"
        elif "Sign in" in err or "confirm you're not a bot" in err:
            msg = "❌ Cần cookies.txt mới! Export từ Chrome rồi upload lại lên Railway."
        elif "unavailable" in err or "not available" in err:
            msg = "❌ Video không khả dụng hoặc bị chặn khu vực. Thử tên/link khác!"
        elif "ffmpeg" in err or "FFmpeg NOT found" in err:
            msg = "❌ Lỗi ffmpeg. Kiểm tra nixpacks.toml hoặc redeploy lại."
        else:
            msg = f"❌ Lỗi: {err}"
        bot.edit_message_text(msg, status.chat.id, status.message_id)

    finally:
        for f in [original_mp3, spedup_mp3]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass

print("🚀 Bot Nhạc MP3 Tăng Tốc đang chạy...")
bot.infinity_polling()
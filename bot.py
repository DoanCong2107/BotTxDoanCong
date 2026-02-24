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

# Keyboard chính
def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f"""🎵 **BOT NHẠC RAILWAY** 🎵

👋 Chào {message.from_user.first_name}!

📌 Gõ lệnh:
• `/play tên bài hát`   (tìm và tải MP3)
• `/play link YouTube`

✅ Bot sẽ tải nhạc chất lượng cao (192kbps) và gửi file audio.

⚠️ Lưu ý:
• Chỉ hỗ trợ nhạc công khai (YouTube)
• File tối đa \~50MB (Telegram giới hạn)
• Railway có thể hạn chế nếu lạm dụng nhạc bản quyền → dùng có trách nhiệm!

Bắt đầu nào! 🔥""",
        parse_mode='Markdown',
        reply_markup=main_kb()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, """🎵 **HƯỚNG DẪN SỬ DỤNG**

✅ Tìm và tải nhạc:
• `/play shape of you`
• `/play https://youtu.be/...`

📊 Lệnh khác:
• `/start` - Menu chính
• Bấm nút **🎵 Tìm nhạc** hoặc **❓ Hướng dẫn**

💡 Mẹo:
• Gõ tên bài hát càng chính xác càng tốt
• Hỗ trợ cả link YouTube Shorts

Chơi nhạc vui vẻ! 🎧""", parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    uid = message.from_user.id

    if text == '🎵 tìm nhạc' or text == '🎵 Tìm nhạc':
        bot.reply_to(message, "Gõ lệnh `/play tên bài hát` nhé!")
        return

    if text == '❓ hướng dẫn' or text == '❓ Hướng dẫn':
        help_cmd(message)
        return

    if not text.lower().startswith(('/play ', 'play ')):
        if any(x in text.lower() for x in ['play', 'nhạc', 'music', 'bài']):
            bot.reply_to(message, "✅ Dùng lệnh: `/play tên bài hát` hoặc `/play link`")
        return

    # Xử lý /play
    query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
    if not query:
        bot.reply_to(message, "❌ Vui lòng nhập tên bài hát hoặc link!\nVí dụ: `/play em của ngày hôm qua`")
        return

    status_msg = bot.reply_to(message, "🔍 Đang tìm kiếm...")

    try:
        # Tìm kiếm hoặc lấy link
        ydl_opts = {
            'format': 'bestaudio/best',
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
            'noplaylist': True,   # chỉ lấy video đầu tiên
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:  # là kết quả tìm kiếm
                info = info['entries'][0]

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')

            # Đường dẫn file mp3
            filename = ydl.prepare_filename(info)
            if not filename.endswith('.mp3'):
                filename = filename.rsplit('.', 1)[0] + '.mp3'

            if duration > 1800:  # >30 phút
                bot.edit_message_text("❌ Bài quá dài (>30 phút), không hỗ trợ!", status_msg.chat.id, status_msg.message_id)
                if os.path.exists(filename):
                    os.remove(filename)
                return

        # Đang tải
        bot.edit_message_text(f"⬇️ Đang tải: **{title}**...", status_msg.chat.id, status_msg.message_id, parse_mode='Markdown')

        # Gửi file audio
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

        bot.delete_message(status_msg.chat.id, status_msg.message_id)

        # Xóa file sau khi gửi
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        error_msg = str(e)
        if "Private video" in error_msg or "Video unavailable" in error_msg:
            txt = "❌ Video riêng tư hoặc không tồn tại!"
        elif "Unable to extract" in error_msg:
            txt = "❌ Không tìm thấy bài hát, thử tên khác nhé!"
        else:
            txt = f"❌ Lỗi: {error_msg[:200]}"
        
        bot.edit_message_text(txt, status_msg.chat.id, status_msg.message_id)
        # Xóa file nếu có
        for f in os.listdir(tempfile.gettempdir()):
            if f.endswith('.mp3') and 'temp' in f.lower():
                try: os.remove(os.path.join(tempfile.gettempdir(), f))
                except: pass

print("🚀 Bot Nhạc đang chạy trên Railway...")
bot.infinity_polling()
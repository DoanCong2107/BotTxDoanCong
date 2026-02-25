import os
import telebot
import yt_dlp
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Lấy Token từ môi trường Railway
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ Chưa set BOT_TOKEN trên Railway!")

bot = telebot.TeleBot(TOKEN)

# Hàm định dạng số view cho đẹp (VD: 1.5M, 200K)
def format_views(n):
    if not n: return "0"
    if n >= 1000000: return f"{n/1000000:.1f}M"
    if n >= 1000: return f"{n/1000:.1f}K"
    return str(n)

# Bàn phím chính dưới khung chat
def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    welcome = (
        f"👋 **Chào mừng {message.from_user.first_name}!**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎧 **Bot Tải Nhạc MP3 Premium**\n"
        "⚡ Tốc độ xử lý: **1.15x Speed**\n"
        "✨ Chất lượng: **192kbps High Quality**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👇 Nhấn nút hoặc gõ `/play + tên bài` để nghe nhạc!"
    )
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=main_kb())

@bot.message_handler(commands=['help'])
def help_cmd(message):
    help_text = (
        "📖 **HƯỚNG DẪN SỬ DỤNG**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ Gõ `/play` kèm tên bài hát hoặc link.\n"
        "   Ví dụ: `/play Em của ngày hôm qua`\n"
        "2️⃣ Đợi bot tìm kiếm và xử lý tốc độ 1.15x.\n"
        "3️⃣ Nhận file MP3 và thưởng thức!\n\n"
        "⚠️ *Lưu ý:* Video dài trên 40 phút sẽ bị từ chối để đảm bảo tốc độ server."
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    
    # Xử lý các nút bấm bàn phím
    if text.lower() in ['🎵 tìm nhạc', 'tìm nhạc']:
        bot.reply_to(message, "🎶 **Bạn muốn nghe gì hôm nay?**\nHãy gõ `/play` kèm tên bài hát nhé!")
        return
    if text.lower() in ['❓ hướng dẫn', 'hướng dẫn']:
        help_cmd(message)
        return

    # Kiểm tra lệnh /play hoặc play
    if not text.lower().startswith(('/play ', 'play ')):
        return

    query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
    if not query:
        bot.reply_to(message, "❌ **Đại ca ơi, nhập tên bài hát nữa chứ!**\nVí dụ: `/play Anh nhà ở đâu thế`", parse_mode='Markdown')
        return

    # Bước 1: Giao diện tìm kiếm
    status = bot.reply_to(message, "🔍 **Đang tìm kiếm bài hát...**\n`[ ░░░░░░░░░░ ] 0%`", parse_mode='Markdown')

    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'default_search': 'ytsearch1',
            'quiet': True,
            'no_warnings': True,
            'outtmpl': 'track_%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # Xử lý tăng tốc 1.15x
            'postprocessor_args': ['-filter:a', 'atempo=1.15'],
            'noplaylist': True,
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Bước 2: Hiệu ứng xử lý
            bot.edit_message_text("⚡ **Đang xử lý âm thanh 1.15x...**\n`[ ██████░░░░ ] 60%`", status.chat.id, status.message_id, parse_mode='Markdown')
            
            info = ydl.extract_info(query, download=True)
            if 'entries' in info: info = info['entries'][0]
            
            title = info.get('title', 'Unknown')
            views = info.get('view_count', 0)
            uploader = info.get('uploader', 'Unknown')
            webpage_url = info.get('webpage_url')
            duration = info.get('duration', 0)
            filename = f"track_{info['id']}.mp3"
            new_duration = int(duration / 1.15)

            if duration > 2400:
                bot.edit_message_text("❌ **Video quá dài!**\nVui lòng chọn bài dưới 40 phút.", status.chat.id, status.message_id)
                if os.path.exists(filename): os.remove(filename)
                return

        # Nút bấm Inline
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📺 Xem Video gốc", url=webpage_url))
        markup.row(InlineKeyboardButton("🔄 Tìm bài khác", switch_inline_query_current_chat=""))

        bot.edit_message_text("✅ **Đã xong! Đang gửi nhạc...**\n`[ ██████████ ] 100%`", status.chat.id, status.message_id, parse_mode='Markdown')

        # Gửi file nhạc cuối cùng
        with open(filename, 'rb') as audio:
            bot.send_audio(
                message.chat.id, 
                audio,
                caption=(
                    f"🎵 **{title.upper()}**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"👤 **Ca sĩ:** {uploader}\n"
                    f"⏱ **Dài:** {time.strftime('%M:%S', time.gmtime(new_duration))} *(Speed 1.15x)*\n"
                    f"👁 **Lượt xem:** {format_views(views)}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🔥 *Chúc bạn nghe nhạc vui vẻ!*"
                ),
                title=f"{title} (1.15x)",
                performer=uploader,
                reply_markup=markup,
                parse_mode='Markdown'
            )

        bot.delete_message(status.chat.id, status.message_id)
        if os.path.exists(filename): os.remove(filename)

    except Exception as e:
        bot.edit_message_text(f"❌ **Lỗi rồi đại ca ơi:**\n`{str(e)[:150]}`", status.chat.id, status.message_id, parse_mode='Markdown')
        # Dọn dẹp file rác nếu có lỗi
        for f in os.listdir('.'):
            if f.startswith("track_"): os.remove(f)

print("🚀 Bot Nhạc MP3 Giao diện mới đang chạy...")
bot.infinity_polling()

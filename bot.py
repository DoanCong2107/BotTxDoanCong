import os
import telebot
import yt_dlp
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Lấy Token từ Railway Environment
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Bộ nhớ tạm để lưu thông tin bài hát
user_cache = {}

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    welcome = (
        f"👋 **Chào đại ca {message.from_user.first_name}!**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔥 **BOT NHẠC SIÊU CẤP 2026**\n"
        "⚡ Hỗ trợ: Speed up, Nightcore, Bass Boost\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👇 Nhập tên bài hát hoặc link YouTube:"
    )
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=main_kb())

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    if text.lower() in ['🎵 tìm nhạc', 'tìm nhạc']:
        bot.reply_to(message, "🎶 Gõ `/play + tên bài` để hiện menu chế độ!")
        return

    if not text.lower().startswith(('/play ', 'play ')): return
    query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
    if not query: return

    status = bot.reply_to(message, "🔍 **Đang lấy dữ liệu từ YouTube...**", parse_mode='Markdown')

    # Cấu hình lấy thông tin cực nhẹ để tránh bị YouTube quét
    ydl_info_opts = {
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1',
        'noplaylist': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info: info = info['entries'][0]
            
            v_id = info['id']
            user_cache[v_id] = {
                'title': info.get('title', 'Unknown'),
                'url': info.get('webpage_url'),
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0)
            }

            # Menu nút bấm cực xịn
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("▶️ Bản Gốc", callback_data=f"mode_orig_{v_id}"),
                InlineKeyboardButton("⚡ Speed 1.15x", callback_data=f"mode_sp115_{v_id}"),
                InlineKeyboardButton("🍬 Nightcore (Méo)", callback_data=f"mode_night_{v_id}"),
                InlineKeyboardButton("🔊 Bass Boost", callback_data=f"mode_bass_{v_id}")
            )

            bot.edit_message_text(
                f"🎵 **Đã tìm thấy:** `{info['title']}`\n\n👇 **Đại ca muốn nghe kiểu gì?**",
                message.chat.id, status.message_id, reply_markup=markup, parse_mode='Markdown'
            )
    except Exception as e:
        bot.edit_message_text(f"❌ Lỗi: {str(e)[:100]}", message.chat.id, status.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('mode_'))
def process_audio(call):
    _, m_type, v_id = call.data.split('_')
    data = user_cache.get(v_id)
    if not data:
        bot.answer_callback_query(call.id, "❌ Hết hạn, hãy tìm lại bài hát!")
        return

    bot.edit_message_text(f"⚙️ **Đang render chế độ {m_type.upper()}...**\nVui lòng đợi giây lát!", call.message.chat.id, call.message.message_id, parse_mode='Markdown')

    ffmpeg_args = []
    suffix = ""
    new_dur = data['duration']

    # Thiết lập bộ lọc âm thanh
    if m_type == "sp115":
        ffmpeg_args = ['-filter:a', 'atempo=1.15']
        suffix = " [1.15x Speed]"
        new_dur /= 1.15
    elif m_type == "night":
        # Méo giọng kiểu Nightcore (Tăng cao độ + Tăng tốc)
        ffmpeg_args = ['-filter:a', 'asetrate=44100*1.25,atempo=1.25/1.25,atempo=1.1']
        suffix = " [Nightcore Mode]"
        new_dur /= 1.35
    elif m_type == "bass":
        ffmpeg_args = ['-filter:a', 'bass=g=10:f=100:w=0.5']
        suffix = " [Bass Boosted]"
    else:
        suffix = " [Original]"

    # Fix lỗi "Function not implemented" bằng cách dùng %(id)s
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'%(id)s.%(ext)s', 
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'postprocessor_args': ffmpeg_args,
        'quiet': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([data['url']])
            filename = f"{v_id}.mp3"

        if os.path.exists(filename):
            with open(filename, 'rb') as audio:
                bot.send_audio(
                    call.message.chat.id, audio,
                    caption=f"🎵 **{data['title']}{suffix}**\n👤 {data['uploader']}\n⏱ {time.strftime('%M:%S', time.gmtime(int(new_dur)))}",
                    title=f"{data['title']}{suffix}",
                    performer="Gemini Music Bot",
                    reply_to_message_id=call.message.reply_to_message.message_id
                )
            os.remove(filename) # Xóa file ngay sau khi gửi để nhẹ server

        bot.delete_message(call.message.chat.id, call.message.message_id)
        
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Lỗi xử lý âm thanh: {str(e)[:100]}")
    
    if v_id in user_cache: del user_cache[v_id]

print("🚀 Bot Music Pro Max đã sẵn sàng!")
bot.infinity_polling()

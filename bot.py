import os
import telebot
import yt_dlp
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Khởi tạo Token
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Bộ nhớ tạm lưu thông tin video
user_cache = {}

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('❓ Hướng dẫn'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    welcome = (
        f"👋 **Chào {message.from_user.first_name}!**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎧 **MUSIC PRO MAX DOWNLOADER**\n"
        "✨ Tùy chọn: Speed up, Nightcore, Bass Boost\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "👇 Nhập tên bài hát hoặc link bên dưới:"
    )
    bot.send_message(message.chat.id, welcome, parse_mode='Markdown', reply_markup=main_kb())

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.strip()
    if text.lower() in ['🎵 tìm nhạc', 'tìm nhạc']:
        bot.reply_to(message, "🎶 Gõ `/play + tên bài` để hiện menu chọn chế độ!")
        return
    if text.lower() in ['❓ hướng dẫn', 'hướng dẫn']:
        bot.reply_to(message, "Gõ `/play tên bài` -> Chọn chế độ (Gốc/Speed/Méo giọng) -> Nhận nhạc.")
        return

    if not text.lower().startswith(('/play ', 'play ')): return
    query = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
    if not query: return

    status = bot.reply_to(message, "🔍 **Đang tìm kiếm bài hát...**", parse_mode='Markdown')

    try:
        # Chỉ lấy thông tin, chưa tải
        with yt_dlp.YoutubeDL({'quiet': True, 'default_search': 'ytsearch1', 'noplaylist': True}) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info: info = info['entries'][0]
            
            v_id = info['id']
            user_cache[v_id] = {
                'title': info.get('title', 'Unknown'),
                'url': info.get('webpage_url'),
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0)
            }

            # Menu chọn chế độ
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("▶️ Bản Gốc", callback_data=f"mode_orig_{v_id}"),
                InlineKeyboardButton("⚡ Speed 1.15x", callback_data=f"mode_sp115_{v_id}"),
                InlineKeyboardButton("🍬 Nightcore (Méo giọng)", callback_data=f"mode_night_{v_id}"),
                InlineKeyboardButton("🔊 Bass Boost", callback_data=f"mode_bass_{v_id}")
            )

            bot.edit_message_text(
                f"🎵 **Đã tìm thấy:** `{info['title']}`\n\n👇 **Đại ca muốn xử lý bài này thế nào?**",
                message.chat.id, status.message_id, reply_markup=markup, parse_mode='Markdown'
            )

    except Exception as e:
        bot.edit_message_text(f"❌ Lỗi: {str(e)[:100]}", message.chat.id, status.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('mode_'))
def process_audio(call):
    # Callback format: mode_TYPE_ID
    _, m_type, v_id = call.data.split('_')
    data = user_cache.get(v_id)

    if not data:
        bot.answer_callback_query(call.id, "❌ Hết hạn, hãy tìm lại bài hát!")
        return

    bot.edit_message_text(f"⚙️ **Đang render chế độ {m_type.upper()}...**\n`[ ██████░░░░ ] 60%`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')

    # Cấu hình FFmpeg Filter dựa trên nút bấm
    ffmpeg_args = []
    suffix = ""
    new_dur = data['duration']

    if m_type == "sp115":
        ffmpeg_args = ['-filter:a', 'atempo=1.15']
        suffix = " [1.15x Speed]"
        new_dur /= 1.15
    elif m_type == "night":
        # Tăng cao độ (Pitch) + Tăng tốc độ = Giọng Nightcore 
        ffmpeg_args = ['-filter:a', 'asetrate=44100*1.25,atempo=1.25/1.25,atempo=1.1']
        suffix = " [Nightcore]"
        new_dur /= 1.35
    elif m_type == "bass":
        ffmpeg_args = ['-filter:a', 'bass=g=10:f=100:w=0.5']
        suffix = " [Bass Boosted]"
    else:
        suffix = " [Original]"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'track_{v_id}.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'postprocessor_args': ffmpeg_args,
        'quiet': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([data['url']])
            filename = f"track_{v_id}.mp3"

        with open(filename, 'rb') as audio:
            bot.send_audio(
                call.message.chat.id, audio,
                caption=f"🎵 **{data['title']}{suffix}**\n👤 {data['uploader']}\n⏱ {time.strftime('%M:%S', time.gmtime(int(new_dur)))}",
                title=f"{data['title']}{suffix}",
                performer="Gemini Music Bot",
                reply_to_message_id=call.message.reply_to_message.message_id
            )
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        if os.path.exists(filename): os.remove(filename)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Lỗi: {str(e)[:100]}")
    
    # Dọn dẹp cache
    if v_id in user_cache: del user_cache[v_id]

bot.infinity_polling()
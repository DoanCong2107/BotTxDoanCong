import os
import telebot
import yt_dlp
import time
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Cấu hình hệ thống
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Bộ nhớ tạm (Database giả lập)
user_data = {} # Lưu level, số bài đã tải
task_cache = {} # Lưu thông tin bài hát đang xử lý

def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('🎵 Tìm nhạc'), KeyboardButton('📊 Cá nhân'), KeyboardButton('🔥 Xu hướng'), KeyboardButton('❓ Trợ giúp'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in user_data:
        user_data[uid] = {"count": 0, "level": "Tân thủ"}
    
    welcome = (
        f"👑 **NIGHTCORE SUPREME PRO**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Người dùng:** {message.from_user.first_name}\n"
        f"🎖 **Cấp độ:** {user_data[uid]['level']}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ Đã sẵn sàng xử lý nhạc. Nhập tên bài hát ngay!"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=main_kb(), parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = str(message.from_user.id)
    text = message.text.strip()

    if text == '📊 Cá nhân':
        count = user_data.get(uid, {}).get('count', 0)
        lvl = user_data.get(uid, {}).get('level', 'Tân thủ')
        bot.reply_to(message, f"📈 **Thống kê của bạn:**\n- Số bài đã méo: `{count}`\n- Danh hiệu: `*{lvl}*`", parse_mode='Markdown')
        return

    if text == '🔥 Xu hướng':
        bot.reply_to(message, "🌟 **Top bài đang hot:**\n1. Sơn Tùng MTP - Đừng làm trái tim anh đau\n2. HIEUTHUHAI - Trình\n3. tlinh - Nữ siêu anh hùng", parse_mode='Markdown')
        return

    if text.startswith('/') or text in ['🎵 Tìm nhạc', '❓ Trợ giúp']: return

    status = bot.reply_to(message, "🔍 **Đang tìm kiếm bài hát...**\n`[ ░░░░░░░░░░ ] 0%`", parse_mode='Markdown')

    try:
        ydl_opts = {'quiet': True, 'default_search': 'ytsearch1', 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=False)
            if 'entries' in info: info = info['entries'][0]
            v_id = info['id']
            
            task_cache[v_id] = {
                'url': info['webpage_url'], 
                'title': info['title'], 
                'duration': info['duration'],
                'status_id': status.message_id
            }

            # Chỉ giữ lại Nightcore và Trim (Cắt nhạc)
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("🍬 Chế độ Nightcore", callback_data=f"v|night|{v_id}"),
                InlineKeyboardButton("✂️ Cắt 30s Nightcore (Làm nhạc chuông)", callback_data=f"v|trim|{v_id}")
            )
            
            bot.edit_message_text(
                f"🎵 **Tìm thấy:** `{info['title']}`\n\n👇 **Chọn chế độ xử lý:**",
                message.chat.id, status.message_id, reply_markup=markup, parse_mode='Markdown'
            )
    except:
        bot.edit_message_text("❌ Không tìm thấy bài hát. Thử tên khác nhé!", message.chat.id, status.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('v|'))
def handle_vip_features(call):
    parts = call.data.split('|')
    mode = parts[1]
    v_id = parts[2]
    data = task_cache.get(v_id)
    uid = str(call.from_user.id)

    if not data:
        bot.answer_callback_query(call.id, "❌ Yêu cầu hết hạn!")
        return

    bot.edit_message_text(f"⚙️ **Đang áp dụng hiệu ứng {mode.upper()}...**\n`[ ████████░░ ] 80%`", call.message.chat.id, call.message.message_id, parse_mode='Markdown')

    ffmpeg_cmd = []
    
    if mode == "night":
        # Nightcore chuẩn
        ffmpeg_cmd = ['-filter:a', 'asetrate=44100*1.25,atempo=1.25/1.25,atempo=1.05']
    elif mode == "trim":
        # Cắt 30s và làm Nightcore
        ffmpeg_cmd = ['-t', '30', '-filter:a', 'asetrate=44100*1.25,atempo=1.25/1.25']

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{v_id}.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'postprocessor_args': ffmpeg_cmd,
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
                    caption=f"✅ **Xử lý hoàn tất!**\n🔥 Chế độ: `{mode.upper()}`\n🍬 Chúc đại ca nghe nhạc vui vẻ!",
                    title=f"{data['title']} ({mode})",
                    performer="Nightcore Pro"
                )
            os.remove(filename)
        
        bot.delete_message(call.message.chat.id, data['status_id'])
        
        # Cập nhật Level người dùng
        user_data[uid]['count'] = user_data.get(uid, {}).get('count', 0) + 1
        if user_data[uid]['count'] > 5: user_data[uid]['level'] = "Chuyên gia Méo"
        if user_data[uid]['count'] > 20: user_data[uid]['level'] = "Huyền thoại Nightcore"
        
        del task_cache[v_id]
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Lỗi xử lý: `{str(e)[:50]}`")

bot.infinity_polling()

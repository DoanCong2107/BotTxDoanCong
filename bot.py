import os
import telebot
import yt_dlp
import time
import threading
import logging
from telebot import types
from datetime import datetime

# === CẤU HÌNH HỆ THỐNG ===
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=10)
MY_BRAND = "DoanCong🥷"

# Thiết lập Log để đại ca dễ theo dõi lỗi
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Database giả lập (Trong thực tế nên dùng SQLite/Redis)
user_db = {} 
processing_tasks = {}

# Hệ thống 10 danh hiệu Remix Đẳng Cấp
TITLES = [
    (0, "🐣 Tân thủ Remix"), (5, "🥉 Học việc Remix"), (15, "🥈 Tay chơi Bass"),
    (30, "🥇 Phù thủy Remix"), (50, "🔥 Chiến thần Nhạc sàn"), (80, "💎 Cao thủ Mix nhạc"),
    (120, "👑 Bậc thầy Remix"), (200, "⚡ Siêu nhân Vinahouse"), (350, "🌟 Huyền thoại Remix"),
    (500, "🌌 Chúa tể dòng nhạc Remix")
]

def get_title(count):
    for threshold, title in reversed(TITLES):
        if count >= threshold: return title
    return TITLES[0][1]

# === GIAO DIỆN ===
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton('🎵 Tìm nhạc'), 
        types.KeyboardButton('📊 Hồ sơ VIP'),
        types.KeyboardButton('🔥 Xu hướng'), 
        types.KeyboardButton('❓ Trợ giúp')
    )
    return markup

def inline_options(v_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(f"🍬 Remix Méo Tiếng (Style {MY_BRAND})", callback_data=f"opt:night:{v_id}"),
        types.InlineKeyboardButton(f"⚡ Tăng Tốc Speed Up (Style {MY_BRAND})", callback_data=f"opt:speed:{v_id}")
    )
    return markup

# === XỬ LÝ LỆNH ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    uid = str(message.from_user.id)
    if uid not in user_db:
        user_db[uid] = {'count': 0, 'join_date': datetime.now().strftime("%d/%m/%Y")}
    
    welcome_text = (
        f"👑 **MUSIC PRO MAX - EXCLUSIVE BY {MY_BRAND}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Chủ nhân:** {message.from_user.first_name}\n"
        f"🎖 **Danh hiệu:** {get_title(user_db[uid]['count'])}\n"
        f"📅 **Ngày tham gia:** {user_db[uid]['join_date']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 **Đại ca hãy dán link YouTube hoặc gõ tên bài hát!**\n"
        f"⚠️ *Hệ thống tự động đóng dấu bản quyền {MY_BRAND} vào file.*"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard(), parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = str(message.from_user.id)
    if uid not in user_db: user_db[uid] = {'count': 0, 'join_date': "N/A"}
    text = message.text.strip()

    # Xử lý các nút Menu
    if text == '📊 Hồ sơ VIP':
        count = user_db[uid]['count']
        bot.reply_to(message, f"📈 **THỐNG KÊ DOANCONG SYSTEM:**\n━━━━━━━━━━━━━\n✅ Sản phẩm đã làm: `{count}` bài\n🎖 Đẳng cấp: `*{get_title(count)}*`", parse_mode='Markdown')
        return
    
    if text == '🔥 Xu hướng':
        bot.reply_to(message, "🔥 **TOP SEARCHING:**\n1. Vinahouse DoanCong Mix\n2. TikTok Remix 2026\n3. Bass Boosted VIP")
        return

    if text in ['🎵 Tìm nhạc', '❓ Trợ giúp']:
        bot.reply_to(message, "Dán link hoặc gõ tên bài để em phục vụ đại ca nhé!")
        return

    # Bắt đầu tìm kiếm
    search_msg = bot.reply_to(message, "🔍 **Đang quét máy chủ YouTube...**", parse_mode='Markdown')
    
    def search_task():
        try:
            ydl_opts = {
                'quiet': True, 'default_search': 'ytsearch1', 'noplaylist': True,
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
                if 'entries' in info: info = info['entries'][0]
                
                v_id = info['id']
                processing_tasks[v_id] = {
                    'url': info['webpage_url'], 
                    'title': info['title'], 
                    'status_id': search_msg.message_id,
                    'chat_id': message.chat.id
                }

                bot.edit_message_text(
                    f"🎵 **Phát hiện:** `{info['title']}`\n"
                    f"⏱ **Thời lượng:** {time.strftime('%M:%S', time.gmtime(info['duration']))}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👇 **Đại ca {MY_BRAND} chọn kiểu xử lý:**",
                    message.chat.id, search_msg.message_id, 
                    reply_markup=inline_options(v_id), parse_mode='Markdown'
                )
        except Exception as e:
            bot.edit_message_text(f"❌ Không tìm thấy nhạc hoặc lỗi server: {str(e)[:50]}", message.chat.id, search_msg.message_id)

    threading.Thread(target=search_task).start()

@bot.callback_query_handler(func=lambda call: call.data.startswith('opt:'))
def callback_handler(call):
    _, mode, v_id = call.data.split(':')
    data = processing_tasks.get(v_id)
    uid = str(call.from_user.id)

    if not data:
        bot.answer_callback_query(call.id, "⚠️ Yêu cầu quá hạn!")
        return

    bot.edit_message_text(f"⚙️ **Đang render & Mod Metadata...**\n`[ ████████░░ ] 80%`", data['chat_id'], data['status_id'], parse_mode='Markdown')

    def download_and_process():
        try:
            # Metadata bá đạo: Ghi đè thông tin DoanCong🥷
            meta_args = [
                '-metadata', f'title={data["title"]} (Remix {MY_BRAND})',
                '-metadata', f'artist={MY_BRAND}',
                '-metadata', f'album={MY_BRAND} Exclusive 2026',
                '-metadata', f'composer=DoanCong_Production'
            ]

            filter_audio = 'asetrate=44100*1.25,atempo=1.25/1.25,atempo=1.05' if mode == 'night' else 'atempo=1.20'
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{v_id}.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'postprocessor_args': ['-filter:a', filter_audio] + meta_args,
                'quiet': True,
                'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([data['url']])
            
            filename = f"{v_id}.mp3"
            if os.path.exists(filename):
                user_db[uid]['count'] += 1
                current_title = get_title(user_db[uid]['count'])

                with open(filename, 'rb') as audio:
                    bot.send_audio(
                        data['chat_id'], audio,
                        caption=f"✅ **Sản phẩm của đại ca {MY_BRAND}!**\n━━━━━━━━━━━━━\n🔥 Mode: `{mode.upper()}`\n🎖 Đẳng cấp: {current_title}",
                        performer=MY_BRAND,
                        title=f"{data['title']} (Remix)"
                    )
                os.remove(filename)

            bot.delete_message(data['chat_id'], data['status_id'])
            del processing_tasks[v_id]

        except Exception as e:
            bot.send_message(data['chat_id'], f"❌ Lỗi render: {str(e)[:100]}")

    threading.Thread(target=download_and_process).start()

# === CHẠY BOT ===
if __name__ == '__main__':
    print(f"--- BOT {MY_BRAND} ĐANG CHẠY ---")
    bot.infinity_polling()

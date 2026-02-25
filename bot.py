import os
import telebot
import yt_dlp
import time
import threading
import random
import logging
from telebot import types
from datetime import datetime

# === CẤU HÌNH HỆ THỐNG ===
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=20)
MY_BRAND = "DoanCong🥷"

# Log hệ thống để theo dõi
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Database giả lập
user_db = {} 
task_map = {}

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

# === GIAO DIỆN MENU CHÍNH ===
def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton('🔮 TÌM NHẠC'), types.KeyboardButton('👤 HỒ SƠ VIP'))
    kb.add(types.KeyboardButton('🎁 ĐIỂM DANH'), types.KeyboardButton('🏆 BẢNG XẾP HẠNG'))
    kb.add(types.KeyboardButton('🔥 XU HƯỚNG'), types.KeyboardButton('⚙️ TRỢ GIÚP'))
    return kb

# === XỬ LÝ LỆNH KHỞI ĐẦU ===
@bot.message_handler(commands=['start', 'help'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in user_db:
        user_db[uid] = {'count': 0, 'date': datetime.now().strftime("%d/%m/%Y"), 'last_daily': 0}
    
    welcome = (
        f"        ── {MY_BRAND} ──\n"
        f"🥷 **NIGHTCORE REMIX SUPREME 2026**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Chào mừng đại ca: **{message.from_user.first_name}**\n"
        f"🎖 Cấp bậc: `{get_title(user_db[uid]['count'])}`\n"
        f"📊 Sản phẩm: `{user_db[uid]['count']} bài`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 **Gửi link hoặc tên bài hát để em phục vụ!**"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=main_kb(), parse_mode='Markdown')

# === QUẢN LÝ TIN NHẮN VÀ TÍNH NĂNG PHỤ ===
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid = str(message.from_user.id)
    if uid not in user_db: user_db[uid] = {'count': 0, 'date': "N/A", 'last_daily': 0}
    text = message.text.strip()

    if text == '👤 HỒ SƠ VIP':
        count = user_db[uid]['count']
        bot.reply_to(message, f"👤 **PRODUCER PROFILE**\n━━━━━━━━━━━━━\n⚡ Nghệ danh: **{MY_BRAND}**\n🎵 Đã làm: `{count}` bài\n🏆 Danh hiệu: `{get_title(count)}`", parse_mode='Markdown')
        return

    if text == '🎁 ĐIỂM DANH':
        now = time.time()
        if now - user_db[uid]['last_daily'] > 86400:
            bonus = random.randint(1, 3)
            user_db[uid]['count'] += bonus
            user_db[uid]['last_daily'] = now
            bot.reply_to(message, f"🎁 **HÀNG NÓNG VỀ!**\nĐại ca được cộng `{bonus}` điểm Exp Remix vào hồ sơ!")
        else:
            bot.reply_to(message, "⏳ Quà hôm nay nhận rồi, mai quay lại nhé đại ca!")
        return

    if text == '🏆 BẢNG XẾP HẠNG':
        bot.reply_to(message, f"🏆 **BẢNG VÀNG DOANCONG SYSTEM:**\n1. **{message.from_user.first_name}** (Producer số 1)\n2. Dân chơi 9x\n3. Thánh Bass", parse_mode='Markdown')
        return

    if text.startswith('/') or text in ['🔮 TÌM NHẠC', '🔥 XU HƯỚNG', '⚙️ TRỢ GIÚP']: return

    # --- PHOTO CAPTION GIAO DIỆN SANG TRỌNG ---
    wait = bot.reply_to(message, "🔮 **Đang thâm nhập máy chủ YouTube...**", parse_mode='Markdown')
    
    def search_task():
        try:
            ydl_opts = {'quiet': True, 'default_search': 'ytsearch1', 'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
                if 'entries' in info: info = info['entries'][0]
                
                v_id = info['id']
                task_map[v_id] = {'url': info['webpage_url'], 'title': info['title']}

                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton(f"🍬 Remix Nightcore (Style {MY_BRAND})", callback_data=f"doan|night|{v_id}"),
                    types.InlineKeyboardButton(f"⚡ Speed Up 1.2x (Style {MY_BRAND})", callback_data=f"doan|speed|{v_id}")
                )

                caption = (
                    f"🎬 **KẾT QUẢ TRUY XUẤT**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎼 Bài hát: `{info['title']}`\n"
                    f"⏱ Thời lượng: `{time.strftime('%M:%S', time.gmtime(info['duration']))}`\n"
                    f"🛰 Trạng thái: `Sẵn sàng mod bản quyền`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👇 **Đại ca chọn kiểu xử lý âm thanh:**"
                )
                bot.send_photo(message.chat.id, info['thumbnail'], caption=caption, reply_markup=markup, parse_mode='Markdown')
                bot.delete_message(message.chat.id, wait.message_id)
        except:
            bot.edit_message_text("❌ Không tìm thấy nhạc!", message.chat.id, wait.message_id)

    threading.Thread(target=search_task).start()

# === XỬ LÝ CHUYỂN ĐỘNG PROGRESS BAR & RENDER ===
@bot.callback_query_handler(func=lambda call: call.data.startswith('doan|'))
def process_it(call):
    _, mode, v_id = call.data.split('|')
    data = task_map.get(v_id)
    uid = str(call.from_user.id)

    if not data:
        bot.answer_callback_query(call.id, "❌ Yêu cầu hết hạn!")
        return

    # Hàm tạo hiệu ứng thanh tiến trình chuyển động
    def update_progress_ui():
        steps = [
            ("📡 Kết nối máy chủ...", "[ ░░░░░░░░░░ ] 5%"),
            ("📥 Đang tải âm thanh...", "[ ██░░░░░░░░ ] 25%"),
            ("⚙️ Ép xung dải Bass...", "[ ████░░░░░░ ] 45%"),
            ("🍬 Modding Nightcore...", "[ ██████░░░░ ] 65%"),
            ("🥷 Nhúng bản quyền DoanCong...", "[ ████████░░ ] 85%"),
            ("✅ Đang xuất sản phẩm...", "[ ██████████ ] 100%")
        ]
        for status, bar in steps:
            try:
                render_text = (
                    f"⚙️ **HỆ THỐNG REMIX ĐANG CHẠY**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🕹 Chế độ: `{mode.upper()}`\n"
                    f"🛰 Trạng thái: `{status}`\n"
                    f"📊 Tiến độ: `{bar}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━"
                )
                bot.edit_message_caption(render_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
                time.sleep(1.1)
            except: break

    threading.Thread(target=update_progress_ui).start()

    def render_task():
        try:
            # Metadata Ngụy trang nhúng sâu DoanCong🥷
            meta = [
                '-metadata', f'title={data["title"]} (Remix by {MY_BRAND})',
                '-metadata', f'artist={MY_BRAND}',
                '-metadata', f'album={MY_BRAND} Exclusive 2026',
                '-metadata', f'composer={MY_BRAND} Prod.'
            ]
            
            filter_a = 'asetrate=44100*1.25,atempo=1.25/1.25,atempo=1.05' if mode == 'night' else 'atempo=1.20'
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{v_id}.%(ext)s',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'postprocessor_args': ['-filter:a', filter_a] + meta,
                'quiet': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([data['url']])
            
            filename = f"{v_id}.mp3"
            if os.path.exists(filename):
                user_db[uid]['count'] += 1
                with open(filename, 'rb') as f:
                    bot.send_audio(
                        call.message.chat.id, f,
                        caption=f"✅ **BẢN REMIX ĐỘC QUYỀN!**\n━━━━━━━━━━━━━━━━━━━━━\n🥷 **Producer:** `{MY_BRAND}`\n🎖 Đẳng cấp: `{get_title(user_db[uid]['count'])}`",
                        performer=MY_BRAND, title=f"{data['title']} (Remix)", parse_mode='Markdown'
                    )
                os.remove(filename)

            bot.delete_message(call.message.chat.id, call.message.message_id)
            del task_map[v_id]
        except:
            bot.send_message(call.message.chat.id, "❌ Lỗi render nhạc rồi đại ca!")

    threading.Thread(target=render_task).start()

bot.infinity_polling()

Import os
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
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=30)
MY_BRAND = "DoanCong🥷"

# Log hệ thống
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# Database giả lập
user_db = {} 
task_map = {}

# Hệ thống 10 danh hiệu
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

# === GIAO DIỆN PHÒNG THU (STYLE 2) ===
def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton('🔮 TRUY XUẤT NHẠC'), types.KeyboardButton('🪪 THẺ PRODUCER'))
    kb.add(types.KeyboardButton('🧧 QUÀ HẰNG NGÀY'), types.KeyboardButton('🏆 BẢNG VÀNG'))
    return kb

# === HIỆU ỨNG XÁC THỰC (STYLE 3) ===
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in user_db:
        user_db[uid] = {'count': 0, 'date': datetime.now().strftime("%d/%m/%Y"), 'last_daily': 0}
    
    # Hiệu ứng chữ chạy xác thực
    auth_msg = bot.send_message(message.chat.id, "⌛ `Đang quét vân tay...`", parse_mode='Markdown')
    time.sleep(0.8)
    bot.edit_message_text("⌛ `Đang xác thực quyền Producer...`", message.chat.id, auth_msg.message_id, parse_mode='Markdown')
    time.sleep(0.8)
    bot.delete_message(message.chat.id, auth_msg.message_id)

    # Giao diện chính kèm Trạng thái (Style 1)
    welcome = (
        f"        ── {MY_BRAND} ──\n"
        f"🥷 **SUPREME REMIX SYSTEM 2026**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Chào đại ca: **{message.from_user.first_name}**\n"
        f"🛰 Server: `Online 🟢` | 🔋 Năng lượng: `100%` \n"
        f"🎖 Cấp bậc: `{get_title(user_db[uid]['count'])}`\n"
        f"📊 Sản phẩm: `{user_db[uid]['count']} bài`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎙 **Hệ thống phòng thu đã sẵn sàng lên nhạc!**"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=main_kb(), parse_mode='Markdown')

# === QUẢN LÝ TÍNH NĂNG ===
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid = str(message.from_user.id)
    if uid not in user_db: user_db[uid] = {'count': 0, 'date': "N/A", 'last_daily': 0}
    text = message.text.strip()

    # Thẻ Căn Cước Producer (Style 5)
    if text == '🪪 THẺ PRODUCER':
        count = user_db[uid]['count']
        card = (
            f"```\n"
            f"┌──────────────────────────────┐\n"
            f"│    PRODUCER IDENTITY CARD    │\n"
            f"├──────────────────────────────┤\n"
            f"│ NAME: {MY_BRAND[:15]:<15} │\n"
            f"│ RANK: {get_title(count):<15} │\n"
            f"│ EXP:  {count:<15} │\n"
            f"│ DATE: {user_db[uid]['date']:<15} │\n"
            f"└──────────────────────────────┘\n"
            f"```"
        )
        bot.send_message(message.chat.id, card, parse_mode='Markdown')
        return

    if text == '🧧 QUÀ HẰNG NGÀY':
        now = time.time()
        if now - user_db[uid]['last_daily'] > 86400:
            bonus = random.randint(1, 3)
            user_db[uid]['count'] += bonus
            user_db[uid]['last_daily'] = now
            bot.reply_to(message, f"🧧 **HÀNG NÓNG!** Đại ca nhận được `{bonus}` Exp!")
        else: bot.reply_to(message, "⏳ Quà đã lụm, mai quay lại nha đại ca!")
        return

    if text.startswith('/') or text in ['🔮 TRUY XUẤT NHẠC', '🏆 BẢNG VÀNG']: return

    # Photo Caption tìm kiếm
    wait = bot.send_message(message.chat.id, "🔮 `Đang thâm nhập dữ liệu...`", parse_mode='Markdown')
    
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
                    types.InlineKeyboardButton(f"🎧 Remix Nightcore (Studio Mode)", callback_data=f"doan|night|{v_id}"),
                    types.InlineKeyboardButton(f"⚡ Speed Up 1.2x (Power Mode)", callback_data=f"doan|speed|{v_id}")
                )

                caption = (
                    f"🎬 **KẾT QUẢ TRUY XUẤT**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎼 Bài: `{info['title']}`\n"
                    f"⏱ Dài: `{time.strftime('%M:%S', time.gmtime(info['duration']))}`\n"
                    f"🎚️ Master Volume: `+6dB` | 🎛️ Bass: `Max`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👇 **Chọn chế độ Mix cho đại ca:**"
                )
                bot.send_photo(message.chat.id, info['thumbnail'], caption=caption, reply_markup=markup, parse_mode='Markdown')
                bot.delete_message(message.chat.id, wait.message_id)
        except: bot.edit_message_text("❌ Lỗi truy xuất!", message.chat.id, wait.message_id)

    threading.Thread(target=search_task).start()

# === CẢNH BÁO ĐỎ & ĐẾM NGƯỢC (STYLE 7 & 12) ===
@bot.callback_query_handler(func=lambda call: call.data.startswith('doan|'))
def process_callback(call):
    _, mode, v_id = call.data.split('|')
    data = task_map.get(v_id)
    uid = str(call.from_user.id)

    def update_ui():
        # Hiệu ứng cảnh báo đỏ và đếm ngược
        steps = [
            ("🚨 CẢNH BÁO: ÉP XUNG CPU...", "15s", "[ ░░░░░░░░░░ ] 5%"),
            ("⚙️ ĐANG XỬ LÝ NHẠC NẶNG...", "12s", "[ ██░░░░░░░░ ] 25%"),
            ("🎙️ ĐANG MOD AUDIO STUDIO...", "9s", "[ ████░░░░░░ ] 45%"),
            ("🍬 ĐANG NHÚNG BASS BOOST...", "6s", "[ ██████░░░░ ] 70%"),
            ("🥷 ĐANG ĐÓNG DẤU BẢN QUYỀN...", "3s", "[ ████████░░ ] 90%"),
            ("✅ XUẤT FILE THÀNH CÔNG!", "0s", "[ ██████████ ] 100%")
        ]
        for status, countdown, bar in steps:
            try:
                render_text = (
                    f"🔥 **HỆ THỐNG ĐANG RENDER...**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🕹 Chế độ: `{mode.upper()}`\n"
                    f"🛰 Trạng thái: `{status}`\n"
                    f"🕒 Dự kiến xong sau: `{countdown}`\n"
                    f"📊 Tiến độ: `{bar}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━"
                )
                bot.edit_message_caption(render_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
                time.sleep(1.5)
            except: break

    threading.Thread(target=update_ui).start()

    def render_task():
        try:
            meta = [
                '-metadata', f'title={data["title"]} (Remix by {MY_BRAND})',
                '-metadata', f'artist={MY_BRAND}',
                '-metadata', f'album={MY_BRAND} Studio Exclusive'
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
                        caption=f"✅ **BẢN REMIX XUẤT XƯỞNG!**\n━━━━━━━━━━━━━\n🥷 **Producer:** `{MY_BRAND}`\n🎖 **Rank:** `{get_title(user_db[uid]['count'])}`",
                        performer=MY_BRAND, title=f"{data['title']} (Remix)", parse_mode='Markdown'
                    )
                os.remove(filename)
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except: bot.send_message(call.message.chat.id, "❌ Lỗi Render!")

    threading.Thread(target=render_task).start()

bot.infinity_polling()
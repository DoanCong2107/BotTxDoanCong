import os
import telebot
import yt_dlp
import time
import threading
import random
import logging
import json
from telebot import types
from datetime import datetime

# === CẤU HÌNH HỆ THỐNG ===
TOKEN = os.getenv('BOT_TOKEN') # Thay bằng Token thật của m nếu chạy máy cá nhân
bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=30)
MY_BRAND = "DoanCong🥷"
DB_FILE = 'user_data.json'

# Log hệ thống
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# === HỆ THỐNG LƯU TRỮ ===
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_db():
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_db, f, ensure_ascii=False, indent=4)

user_db = load_db()
task_map = {}

# Hệ thống danh hiệu (Tính theo số bài đã làm)
TITLES = [
    (0, "🐣 Producer Nghèo"), (5, "🥉 Học việc Remix"), (15, "🥈 Tay chơi Bass"),
    (30, "🥇 Phù thủy Remix"), (50, "🔥 Chiến thần Nhạc sàn"), (100, "💎 Cao thủ Mix nhạc"),
    (200, "👑 Bậc thầy Remix"), (500, "🌌 Chúa tể dòng nhạc Remix")
]

def get_title(count):
    for threshold, title in reversed(TITLES):
        if count >= threshold: return title
    return TITLES[0][1]

# === GIAO DIỆN PHÒNG THU ===
def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(types.KeyboardButton('🔮 TRUY XUẤT NHẠC'), types.KeyboardButton('🪪 THẺ PRODUCER'))
    kb.add(types.KeyboardButton('⚖️ TÀI XỈU'), types.KeyboardButton('🎲 BẦU CUA'))
    kb.add(types.KeyboardButton('🧧 QUÀ HẰNG NGÀY'), types.KeyboardButton('🏆 BẢNG VÀNG'))
    return kb

# === LỆNH KHỞI ĐỘNG ===
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.from_user.id)
    if uid not in user_db:
        user_db[uid] = {'balance': 5000, 'total_made': 0, 'date': datetime.now().strftime("%d/%m/%Y"), 'last_daily': 0}
        save_db()
    
    auth_msg = bot.send_message(message.chat.id, "⌛ `Đang quét vân tay...`", parse_mode='Markdown')
    time.sleep(0.5)
    bot.edit_message_text("⌛ `Đang xác thực quyền Producer...`", message.chat.id, auth_msg.message_id, parse_mode='Markdown')
    time.sleep(0.5)
    bot.delete_message(message.chat.id, auth_msg.message_id)

    welcome = (
        f"        ── {MY_BRAND} ──\n"
        f"🥷 **SUPREME REMIX SYSTEM 2026**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 Chào đại ca: **{message.from_user.first_name}**\n"
        f"💰 Tài khoản: `{user_db[uid]['balance']:,} VNĐ` \n"
        f"🎖 Cấp bậc: `{get_title(user_db[uid]['total_made'])}`\n"
        f"📊 Sản phẩm: `{user_db[uid]['total_made']} bài`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎙 **Hệ thống phòng thu & Sòng bài sẵn sàng!**"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=main_kb(), parse_mode='Markdown')

# === LỆNH CHUYỂN TIỀN ===
@bot.message_handler(commands=['pay'])
def pay_money(message):
    uid = str(message.from_user.id)
    try:
        args = message.text.split()
        if len(args) < 3 or not message.reply_to_message:
            return bot.reply_to(message, "❌ Cách dùng: Rep tin nhắn người nhận và gõ `/pay [số tiền]`")
        
        amount = int(args[1])
        target_id = str(message.reply_to_message.from_user.id)

        if amount <= 0 or user_db[uid]['balance'] < amount:
            return bot.reply_to(message, "❌ Tiền đâu mà chuyển đại ca?")

        user_db[uid]['balance'] -= amount
        if target_id not in user_db:
            user_db[target_id] = {'balance': 0, 'total_made': 0, 'date': "N/A", 'last_daily': 0}
        
        user_db[target_id]['balance'] += amount
        save_db()
        bot.reply_to(message, f"✅ Đã chuyển `{amount:,} VNĐ` cho {message.reply_to_message.from_user.first_name}!")
    except:
        bot.reply_to(message, "❌ Lỗi giao dịch!")

# === XỬ LÝ SỰ KIỆN CHÍNH ===
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid = str(message.from_user.id)
    if uid not in user_db: 
        user_db[uid] = {'balance': 5000, 'total_made': 0, 'date': datetime.now().strftime("%d/%m/%Y"), 'last_daily': 0}
    text = message.text.strip()

    if text == '🪪 THẺ PRODUCER':
        data = user_db[uid]
        card = (
            f"```\n"
            f"┌──────────────────────────────┐\n"
            f"│    PRODUCER IDENTITY CARD    │\n"
            f"├──────────────────────────────┤\n"
            f"│ NAME: {message.from_user.first_name[:15]:<15} │\n"
            f"│ RANK: {get_title(data['total_made']):<15} │\n"
            f"│ CASH: {data['balance']:>11,} đ   │\n"
            f"│ MADE: {data['total_made']:>11} bài  │\n"
            f"└──────────────────────────────┘\n"
            f"```"
        )
        bot.send_message(message.chat.id, card, parse_mode='Markdown')
        return

    if text == '🧧 QUÀ HẰNG NGÀY':
        now = time.time()
        if now - user_db[uid]['last_daily'] > 86400:
            bonus = random.randint(1000, 5000)
            user_db[uid]['balance'] += bonus
            user_db[uid]['last_daily'] = now
            save_db()
            bot.reply_to(message, f"🧧 **LỤM LÚA!** Đại ca nhận được `{bonus:,} VNĐ`!")
        else: bot.reply_to(message, "⏳ Mai quay lại bú tiếp đại ca!")
        return

    if text == '🏆 BẢNG VÀNG':
        top = sorted(user_db.items(), key=lambda x: x[1]['balance'], reverse=True)[:5]
        leader_text = "🏆 **TOP 5 ĐẠI GIA PRODUCER** 🏆\n━━━━━━━━━━━━━━━━━━━━━\n"
        for i, (id, d) in enumerate(top):
            leader_text += f"{i+1}. `{get_title(d['total_made'])}` - {d['balance']:,}đ\n"
        bot.send_message(message.chat.id, leader_text, parse_mode='Markdown')
        return

    if text == '⚖️ TÀI XỈU':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌑 TÀI (11-18)", callback_data="tx|tai"),
                   types.InlineKeyboardButton("🌕 XỈU (3-10)", callback_data="tx|xiu"))
        bot.send_message(message.chat.id, "⚖️ **SÒNG TÀI XỈU**\nCược: `2,000đ`. Chọn đi đại ca!", reply_markup=markup, parse_mode='Markdown')
        return

    if text == '🎲 BẦU CUA':
        markup = types.InlineKeyboardMarkup(row_width=3)
        icons = {"bau": "🎃", "cua": "🦀", "tom": "🦞", "ca": "🐟", "ga": "🐓", "nai": "🦌"}
        btns = [types.InlineKeyboardButton(v, callback_data=f"bc|{k}") for k, v in icons.items()]
        markup.add(*btns)
        bot.send_message(message.chat.id, "🎲 **SÒNG BẦU CUA**\nCược: `5,000đ`. Đặt con gì đại ca?", reply_markup=markup, parse_mode='Markdown')
        return

    if text.startswith('/') or text == '🔮 TRUY XUẤT NHẠC': return

    # --- PHẦN RENDER NHẠC ---
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
                    types.InlineKeyboardButton("🎧 Remix Nightcore", callback_data=f"mix|night|{v_id}"),
                    types.InlineKeyboardButton("⚡ Speed Up 1.2x", callback_data=f"mix|speed|{v_id}")
                )
                bot.send_photo(message.chat.id, info['thumbnail'], caption=f"🎬 **KẾT QUẢ**\n🎼 `{info['title']}`\n👇 Chọn chế độ Mix:", reply_markup=markup, parse_mode='Markdown')
                bot.delete_message(message.chat.id, wait.message_id)
        except: bot.edit_message_text("❌ Lỗi tìm kiếm!", message.chat.id, wait.message_id)
    threading.Thread(target=search_task).start()

# === CALLBACK XỬ LÝ GAME & MIX ===
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = str(call.from_user.id)
    data = call.data.split('|')

    # Tài Xỉu
    if data[0] == 'tx':
        bet = 2000
        if user_db[uid]['balance'] < bet: return bot.answer_callback_query(call.id, "Hết tiền!", show_alert=True)
        user_db[uid]['balance'] -= bet
        dices = [random.randint(1, 6) for _ in range(3)]
        total = sum(dices)
        res = "tai" if total >= 11 else "xiu"
        msg = f"🎲 Kết quả: `{' + '.join(map(str, dices))}` = **{total}**\n"
        if data[1] == res:
            user_db[uid]['balance'] += bet * 2
            msg += "🎊 **HÚP LÚA!**"
        else: msg += "💀 **XỊT!**"
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        save_db()

    # Bầu Cua
    elif data[0] == 'bc':
        bet = 5000
        if user_db[uid]['balance'] < bet: return bot.answer_callback_query(call.id, "Hết tiền!", show_alert=True)
        user_db[uid]['balance'] -= bet
        icons = {"bau": "🎃", "cua": "🦀", "tom": "🦞", "ca": "🐟", "ga": "🐓", "nai": "🦌"}
        res = [random.choice(list(icons.keys())) for _ in range(3)]
        match = res.count(data[1])
        msg = f"🎲 Kết quả: {' '.join([icons[r] for r in res])}\n"
        if match > 0:
            win = bet * (match + 1)
            user_db[uid]['balance'] += win
            msg += f"🎊 **HÚP!** Nhận `{win:,}đ`"
        else: msg += "💀 **XỊT!**"
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        save_db()

    # Mix Nhạc
    elif data[0] == 'mix':
        _, mode, v_id = data
        info = task_map.get(v_id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        render_msg = bot.send_message(call.message.chat.id, "⚙️ `Đang Render nhạc...`", parse_mode='Markdown')
        
        def render_thread():
            try:
                filter_a = 'asetrate=44100*1.25,atempo=1.25/1.25,atempo=1.05' if mode == 'night' else 'atempo=1.20'
                ydl_opts = {
                    'format': 'bestaudio/best', 'outtmpl': f'{v_id}.%(ext)s',
                    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                    'postprocessor_args': ['-filter:a', filter_a], 'quiet': True
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([info['url']])
                
                with open(f"{v_id}.mp3", 'rb') as f:
                    salary = random.randint(1000, 3000)
                    user_db[uid]['balance'] += salary
                    user_db[uid]['total_made'] += 1
                    save_db()
                    bot.send_audio(call.message.chat.id, f, caption=f"✅ **Xong!** Đại ca nhận `{salary:,}đ` tiền lương.\n🎖 Rank: `{get_title(user_db[uid]['total_made'])}`", parse_mode='Markdown')
                os.remove(f"{v_id}.mp3")
                bot.delete_message(call.message.chat.id, render_msg.message_id)
            except: bot.send_message(call.message.chat.id, "❌ Lỗi Render!")
        threading.Thread(target=render_thread).start()

bot.infinity_polling()

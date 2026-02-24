import os
import random
import time
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv('TOKEN')
if not TOKEN:
    raise ValueError("❌ Chưa set BOT_TOKEN trên Railway! Hãy thêm vào Variables.")

bot = telebot.TeleBot(TOKEN)

# Balance người chơi (in-memory, reset khi redeploy)
users = {}

def get_balance(user_id):
    if user_id not in users:
        users[user_id] = 100000  # Tặng 100k lần đầu
    return users[user_id]

def update_balance(user_id, amount):
    users[user_id] = get_balance(user_id) + amount

# Emoji xúc xắc đẹp
DICE = [' ', '⚀', '⚁', '⚂', '⚃', '⚄', '⚅']

def roll_dice():
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    emojis = ''.join(DICE[d] for d in dice)
    
    if total == 3 or total == 18:
        result = "BỘ BA"
        is_tai = False
        is_xiu = False
    elif total >= 11:
        result = "TÀI"
        is_tai = True
        is_xiu = False
    else:
        result = "XỈU"
        is_tai = False
        is_xiu = True
    
    return dice, total, emojis, result, is_tai, is_xiu

# Keyboard
def main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton('💰 Số dư'), KeyboardButton('❓ Hướng dẫn'))
    kb.add(KeyboardButton('💵 Nạp tiền (100k)'))
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    bot.send_message(
        message.chat.id,
        f"""🎲 **BOT TÀI XỈU RAILWAY** 🎲

👋 Chào {message.from_user.first_name}!

💰 Số dư: **{get_balance(uid):,} VNĐ**

📌 **Cách chơi nhanh:**
• Gõ: `tài 50000` hoặc `xỉu 100000`
• Hoặc dùng lệnh `/tai 50000` / `/xiu 100000`

Quy tắc:
✅ XỈU: tổng 4–10
✅ TÀI: tổng 11–17
❌ Bộ ba (3 hoặc 18): Thua hết!

Thắng ăn **1:1** (nhận lại tiền cược + lãi bằng tiền cược)

Chơi vui & thắng lớn nhé! 🍀""",
        parse_mode='Markdown',
        reply_markup=main_kb()
    )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, """🎲 **HƯỚNG DẪN CHI TIẾT**

✅ Cược Tài/Xỉu:
• `tài 50000`
• `xỉu 200000`
• `/tai 100000`
• `/xiu 50000`

📊 Lệnh khác:
• `/so_du` hoặc bấm 💰 Số dư
• `/nap` hoặc bấm 💵 Nạp tiền (100k)
• `/start` - Menu chính

⚠️ Lưu ý:
• Tiền chỉ lưu trong phiên (reset khi redeploy)
• Nhà cái ăn bộ ba (3 & 18)

Chúc bạn đỏ tay! 🔥""", parse_mode='Markdown')

@bot.message_handler(commands=['so_du', 'balance'])
def so_du(message):
    uid = message.from_user.id
    bot.reply_to(message, f"💰 **Số dư hiện tại:** {get_balance(uid):,} VNĐ")

@bot.message_handler(commands=['nap'])
def nap_tien(message):
    uid = message.from_user.id
    update_balance(uid, 100000)
    bot.reply_to(message, f"✅ Đã nạp **100.000 VNĐ**!\n💰 Số dư mới: **{get_balance(uid):,} VNĐ**")

# Xử lý cược (cả lệnh và tin nhắn thường)
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    uid = message.from_user.id
    text = message.text.strip().lower()
    
    # Nạp tiền từ nút
    if text == '💵 nạp tiền (100k)':
        update_balance(uid, 100000)
        bot.reply_to(message, f"✅ Nạp thành công **100.000 VNĐ**!\n💰 Số dư: **{get_balance(uid):,} VNĐ**")
        return
    
    if text == '💰 số dư':
        bot.reply_to(message, f"💰 **Số dư:** {get_balance(uid):,} VNĐ")
        return
    
    if text == '❓ hướng dẫn':
        help_cmd(message)
        return

    # Xử lý cược
    bet_type = None
    amount = None
    
    if text.startswith('tài ') or text.startswith('/tai '):
        bet_type = 'tai'
        try:
            amount = int(text.split()[1])
        except:
            pass
    elif text.startswith('xỉu ') or text.startswith('xiu ') or text.startswith('/xiu ') or text.startswith('/xỉu '):
        bet_type = 'xiu'
        try:
            amount = int(text.split()[1])
        except:
            pass
    
    if not bet_type or not amount or amount <= 0:
        if any(k in text for k in ['tài', 'tai', 'xỉu', 'xiu']):
            bot.reply_to(message, "❌ Sai cú pháp!\n✅ Ví dụ đúng: `tài 50000` hoặc `/xiu 100000`")
        return

    balance = get_balance(uid)
    if amount > balance:
        bot.reply_to(message, f"❌ Không đủ tiền! Bạn chỉ có **{balance:,} VNĐ**")
        return

    # Trừ tiền cược ngay
    update_balance(uid, -amount)
    
    # Lắc
    msg = bot.reply_to(message, "🎲 **Đang lắc xúc xắc...**")
    time.sleep(1.8)  # Tạo cảm giác thật

    dice, total, emojis, result, is_tai, is_xiu = roll_dice()
    
    win = (bet_type == 'tai' and is_tai) or (bet_type == 'xiu' and is_xiu)
    
    if win:
        profit = amount * 2  # Trả lại gốc + lãi
        update_balance(uid, amount)  # + gốc + lãi = +amount lần nữa
        outcome = f"🎉 **THẮNG RỒI!** +{amount:,} VNĐ"
    else:
        outcome = f"😢 **THUA** -{amount:,} VNĐ"
    
    final_balance = get_balance(uid)
    
    result_text = f"""🎲 **KẾT QUẢ**

{emojis[0]} {emojis[1]} {emojis[2]}
**Tổng điểm = {total} → {result}**

Bạn cược **{bet_type.upper()}** {amount:,} VNĐ
{outcome}

💰 Số dư mới: **{final_balance:,} VNĐ**"""

    bot.edit_message_text(result_text, msg.chat.id, msg.message_id, parse_mode='Markdown')

print("🚀 Bot Tài Xỉu đang chạy trên Railway...")
bot.infinity_polling()
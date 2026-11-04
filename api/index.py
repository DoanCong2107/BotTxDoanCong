from flask import Flask, request
import telebot
import os

# 1. Khởi tạo ứng dụng Flask (Đây chính là biến "app" mà Vercel đang đòi)
app = Flask(__name__)

# 2. Khởi tạo Bot (Lấy token từ biến môi trường của Vercel để bảo mật)
# Nhớ cài đặt biến BOT_TOKEN trong phần Environment Variables của Vercel
BOT_TOKEN = os.getenv('BOT_TOKEN', 'ĐIỀN_TOKEN_CỦA_BẠN_VÀO_ĐÂY_NẾU_KHÔNG_DÙNG_BIẾN_MÔI_TRƯỜNG')
bot = telebot.TeleBot(BOT_TOKEN)

# 3. Các lệnh của bot (Ví dụ lệnh /start)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Xin chào! Bot đang chạy vĩnh viễn trên Vercel ⚡")

# 4. Cổng nhận tin nhắn từ Telegram (Webhook)
@app.route('/', defaults={'path': ''}, methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def webhook(path):
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

# 5. Cổng kiểm tra xem server có sống không (Truy cập bằng trình duyệt)
@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def index(path):
    return "Server Bot đang hoạt động bình thường!", 200

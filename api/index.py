from flask import Flask, request
import telebot
import logging

# Bật tính năng in lỗi ra màn hình Logs của Vercel
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

app = Flask(__name__)

# DÁN TRỰC TIẾP TOKEN VÀO ĐÂY (Trong dấu ngoặc kép)
BOT_TOKEN = "9259423979:AAEko_cFsBG199E5TtMYxTlYW9jEgkurcgo"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Tuyệt vời! Bot đã phản hồi thành công từ Vercel ⚡")

@app.route('/', defaults={'path': ''}, methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def webhook(path):
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def index(path):
    return "Server Bot đang hoạt động tốt!", 200

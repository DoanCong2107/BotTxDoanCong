from flask import Flask, request
import telebot
import os
import yt_dlp
import threading # Thêm thư viện luồng chạy nền

app = Flask(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN', 'ĐIỀN_TOKEN_CỦA_BẠN_VÀO_ĐÂY')
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot đã sống lại trên Vercel ⚡! Gửi lệnh: /yt <link_youtube> để tải nhạc.")

# Hàm thực thi tải nhạc độc lập
def process_youtube_download(message, url):
    msg = bot.reply_to(message, "⏳ Đang xử lý tải nhạc ngầm, vui lòng đợi 15-30s...")
    
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': '/tmp/%(id)s.%(ext)s', 
        'max_filesize': 50000000, 
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f"/tmp/{info['id']}.m4a"
            title = info.get('title', 'Audio')

        with open(filename, 'rb') as audio:
            bot.send_audio(message.chat.id, audio, title=title)
        
        os.remove(filename)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Lỗi tải nhạc: {str(e)}", message.chat.id, msg.message_id)

@bot.message_handler(commands=['yt'])
def download_youtube(message):
    text = message.text.split()
    if len(text) < 2:
        bot.reply_to(message, "Sai cú pháp! Hãy gõ: /yt <link_youtube>")
        return
    
    url = text[1]
    
    # ÉP CHẠY NGẦM: Bắt đầu tải nhạc ở một luồng riêng để Vercel không bị treo
    download_thread = threading.Thread(target=process_youtube_download, args=(message, url))
    download_thread.start()
    # Sau khi đẩy việc sang luồng mới, hàm này lập tức kết thúc

@app.route('/', defaults={'path': ''}, methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def webhook(path):
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        # Báo cho Telegram và Vercel biết là "đã nhận được tín hiệu" ngay lập tức
        return "OK", 200
    return "Forbidden", 403

@app.route('/', defaults={'path': ''}, methods=['GET'])
@app.route('/<path:path>', methods=['GET'])
def index(path):
    return "Server Bot đang hoạt động tốt!", 200

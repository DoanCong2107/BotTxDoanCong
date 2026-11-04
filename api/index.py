from flask import Flask, request
import telebot
import os
import yt_dlp

app = Flask(__name__)

# Thay chuỗi bên dưới bằng Token bot của bạn nếu bạn chưa cài trong Vercel
BOT_TOKEN = os.getenv('BOT_TOKEN', 'ĐIỀN_TOKEN_CỦA_BẠN_VÀO_ĐÂY')
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot đã sống lại trên Vercel ⚡! Gửi lệnh: /yt <link_youtube> để tải nhạc.")

@bot.message_handler(commands=['yt'])
def download_youtube(message):
    text = message.text.split()
    if len(text) < 2:
        bot.reply_to(message, "Sai cú pháp! Hãy gõ: /yt <link_youtube>")
        return
    
    url = text[1]
    msg = bot.reply_to(message, "⏳ Đang tải nhạc, đợi bot một chút nhé...")
    
    # TỐI ƯU CHO VERCEL: 
    # 1. Tải định dạng m4a (Telegram hỗ trợ tốt, không cần dùng FFmpeg để ép sang mp3)
    # 2. Bắt buộc lưu vào thư mục /tmp vì Vercel chặn ghi file ở các thư mục khác
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': '/tmp/%(id)s.%(ext)s', 
        'max_filesize': 50000000, # Giới hạn 50MB
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f"/tmp/{info['id']}.m4a"
            title = info.get('title', 'Audio')

        # Gửi file nhạc lên Telegram
        with open(filename, 'rb') as audio:
            bot.send_audio(message.chat.id, audio, title=title)
        
        # Xóa file rác trong /tmp sau khi gửi xong và xóa tin nhắn "Đang tải..."
        os.remove(filename)
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ Lỗi tải nhạc: {str(e)}", message.chat.id, msg.message_id)

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

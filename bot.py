import telebot
import os
import yt_dlp
import threading
from flask import Flask

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot đã hoạt động 🚀! Gửi lệnh /yt <link> để tải nhạc.")

@bot.message_handler(commands=['yt'])
def download_youtube(message):
    text = message.text.split()
    if len(text) < 2:
        bot.reply_to(message, "Sai cú pháp! Hãy gõ: /yt <link_youtube>")
        return
    
    url = text[1]
    msg = bot.reply_to(message, "⏳ Đang tải nhạc, đợi bot chút nhé...")
    filename = None
    
    # 1. Bỏ giới hạn max_filesize để tránh lỗi "Format not available"
    # 2. Thêm client iOS để đa dạng hóa định dạng lấy được
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best', 
        'outtmpl': '%(id)s.%(ext)s', 
        'cookiefile': 'cookies.txt',
        'noplaylist': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}}
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Audio')

        # Gửi thẳng file âm thanh gốc lên Telegram
        with open(filename, 'rb') as audio:
            bot.send_audio(message.chat.id, audio, title=title)
        
        # Dọn rác sau khi gửi thành công
        os.remove(filename)
        bot.delete_message(message.chat.id, msg.message_id)
        
    except Exception as e:
        error_msg = str(e)
        # Bắt lỗi Telegram không cho gửi file quá 50MB
        if "Entity Too Large" in error_msg or "too large" in error_msg.lower():
            bot.edit_message_text("❌ Lỗi: Bài hát quá dài hoặc chất lượng quá cao (Vượt giới hạn 50MB của nền tảng Telegram).", message.chat.id, msg.message_id)
        else:
            bot.edit_message_text(f"❌ Lỗi: {error_msg}", message.chat.id, msg.message_id)
        
        # Xóa file rác trong máy chủ nếu quá trình gửi thất bại
        if filename and os.path.exists(filename):
            os.remove(filename)

# Web Server giả để Render không tắt bot và để cron-job ping vào
@app.route('/')
def index():
    return "Server Bot đang chạy trên Render!"

def run_bot():
    bot.polling(non_stop=True)

if __name__ == "__main__":
    # Chạy bot ở luồng phụ
    threading.Thread(target=run_bot).start()
    # Chạy web server ở luồng chính theo Port của Render
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)

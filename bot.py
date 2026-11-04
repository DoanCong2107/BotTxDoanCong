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
    
    # Cấu hình bao trọn gói: Lấy audio tốt nhất, bỏ giả lập thiết bị để tránh bị YouTube giấu định dạng
    ydl_opts = {
        'format': 'bestaudio/best', 
        'outtmpl': '%(id)s.%(ext)s', 
        'cookiefile': 'cookies.txt',
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Lấy chính xác tên file vừa tải về (có thể là .webm hoặc .m4a)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Audio')

        # MẸO: Đổi đuôi file thành .mp3 để lừa Telegram nhận diện đây là file âm thanh
        if filename and os.path.exists(filename):
            mp3_filename = f"{info['id']}.mp3"
            os.rename(filename, mp3_filename)
            
            with open(mp3_filename, 'rb') as audio:
                bot.send_audio(message.chat.id, audio, title=title)
            
            # Dọn rác
            os.remove(mp3_filename)
            bot.delete_message(message.chat.id, msg.message_id)
        
    except Exception as e:
        error_msg = str(e)
        if "Entity Too Large" in error_msg or "too large" in error_msg.lower():
            bot.edit_message_text("❌ Lỗi: Bài hát vượt quá giới hạn 50MB của Telegram.", message.chat.id, msg.message_id)
        else:
            bot.edit_message_text(f"❌ Lỗi: {error_msg}", message.chat.id, msg.message_id)
        
        # Dọn file rác nếu bị lỗi giữa chừng
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

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
    bot.reply_to(message, "Bot đã chạy thành công từ file bot.py trên Render 🚀! Gửi lệnh /yt <link> để tải nhạc.")

@bot.message_handler(commands=['yt'])
def download_youtube(message):
    text = message.text.split()
    if len(text) < 2:
        bot.reply_to(message, "Sai cú pháp! Hãy gõ: /yt <link_youtube>")
        return
    
    url = text[1]
    msg = bot.reply_to(message, "⏳ Đang tải nhạc, đợi bot chút nhé...")
    
    # Sửa lại format: Ưu tiên m4a, nếu không có thì tự động lấy audio tốt nhất hiện có
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': '%(id)s.%(ext)s', 
        'max_filesize': 50000000, 
        'cookiefile': 'cookies.txt',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Tải file về
            info = ydl.extract_info(url, download=True)
            
            # Tự động lấy tên file vừa tải (không gán cứng đuôi .m4a nữa)
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'Audio')

        # Đổi đuôi ảo sang .mp3 để Telegram nhận diện là bài hát (dù gốc là webm)
        new_filename = f"{info['id']}.mp3"
        os.rename(filename, new_filename)

        with open(new_filename, 'rb') as audio:
            bot.send_audio(message.chat.id, audio, title=title)
        
        # Xóa file rác
        os.remove(new_filename)
        bot.delete_message(message.chat.id, msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Lỗi: {str(e)}", message.chat.id, msg.message_id)

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

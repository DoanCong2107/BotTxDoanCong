import telebot
import os
import requests
import threading
from flask import Flask

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bot đã lột xác sang dùng API Vượt rào 🚀! Gửi lệnh /yt <link> để tải nhạc.")

@bot.message_handler(commands=['yt'])
def download_youtube(message):
    text = message.text.split()
    if len(text) < 2:
        bot.reply_to(message, "Sai cú pháp! Hãy gõ: /yt <link_youtube>")
        return
    
    url = text[1]
    msg = bot.reply_to(message, "⏳ Đang kết nối với Server API Vượt rào...")
    filename = None
    
    try:
        # 1. GỌI API ĐỂ LẤY LINK TẢI TRỰC TIẾP
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }
        payload = {
            "url": url,
            "isAudioOnly": True # Yêu cầu API bóc tách lấy riêng âm thanh
        }
        
        api_res = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers)
        api_data = api_res.json()
        
        if api_res.status_code != 200 or api_data.get('status') == 'error':
            bot.edit_message_text(f"❌ Server API từ chối tải: {api_data.get('text', 'Lỗi không xác định')}", message.chat.id, msg.message_id)
            return
            
        download_url = api_data.get('url')
        if not download_url:
            bot.edit_message_text("❌ Không lấy được link tải trực tiếp từ API.", message.chat.id, msg.message_id)
            return
            
        # 2. RENDER TẢI FILE VỀ
        bot.edit_message_text("⬇️ API nhả link thành công! Đang kéo file về bot...", message.chat.id, msg.message_id)
        
        file_res = requests.get(download_url, stream=True)
        filename = f"{message.message_id}_audio.mp3"
        
        with open(filename, 'wb') as f:
            for chunk in file_res.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    
        # Kiểm tra dung lượng xem có vượt quá 50MB của Telegram không
        filesize = os.path.getsize(filename)
        if filesize > 50 * 1024 * 1024:
            bot.edit_message_text("❌ File nhạc nặng hơn 50MB, Telegram chặn không cho gửi.", message.chat.id, msg.message_id)
            os.remove(filename)
            return

        # 3. GỬI LÊN TELEGRAM
        bot.edit_message_text("📤 Kéo xong! Đang gửi nhạc lên Telegram của bạn...", message.chat.id, msg.message_id)
        
        with open(filename, 'rb') as audio:
            bot.send_audio(message.chat.id, audio)
            
        # Dọn dẹp sạch sẽ
        bot.delete_message(message.chat.id, msg.message_id)
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.edit_message_text(f"❌ Lỗi hệ thống: {str(e)}", message.chat.id, msg.message_id)
        if filename and os.path.exists(filename):
            os.remove(filename)

# Web Server giả để Render không tắt bot và để cron-job ping vào
@app.route('/')
def index():
    return "Server Bot đang chạy trên Render bằng API Vượt rào!"

def run_bot():
    bot.polling(non_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)

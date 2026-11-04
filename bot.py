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
    bot.reply_to(message, "Bot đã lột xác sang dùng Ma trận API Vượt rào 🚀! Gửi lệnh /yt <link> để tải nhạc.")

@bot.message_handler(commands=['yt'])
def download_youtube(message):
    text = message.text.split()
    if len(text) < 2:
        bot.reply_to(message, "Sai cú pháp! Hãy gõ: /yt <link_youtube>")
        return
    
    url = text[1]
    msg = bot.reply_to(message, "⏳ Đang lùng sục các Server API để bốc nhạc...")
    filename = None
    download_url = None
    
    try:
        # CHIẾN THUẬT: Thử gõ cửa lần lượt các Server Cobalt cộng đồng (Chuẩn V9 mới nhất)
        cobalt_servers = [
            "https://cobalt.q-n-d.de",
            "https://cobalt.twi.cx",
            "https://cobalt.cacko.net"
        ]
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Cấu hình payload chuẩn của Cobalt V9 để ép lấy file âm thanh
        payload = {
            "url": url,
            "downloadMode": "audio",
            "audioFormat": "mp3"
        }

        for server in cobalt_servers:
            try:
                res = requests.post(server, json=payload, headers=headers, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    if 'url' in data:
                        download_url = data['url']
                        break # Lấy được link là thoát vòng lặp ngay lập tức
            except:
                continue # Nếu server này chết, tự động bỏ qua và thử server tiếp theo
                
        # NẾU COBALT CHẾT HẾT -> Dùng API dự phòng chuyên cho Bot Telegram
        if not download_url:
            try:
                res = requests.get(f"https://api.siputzx.my.id/api/d/ytmp3?url={url}", timeout=15)
                if res.status_code == 200:
                    download_url = res.json().get('data', {}).get('dl')
            except:
                pass

        if not download_url:
            bot.edit_message_text("❌ Toàn bộ Server API đều từ chối hoặc đang bảo trì. Bạn thử lại sau nhé!", message.chat.id, msg.message_id)
            return
            
        # RENDER TẢI FILE VỀ TỪ LINK API CHỈ ĐỊNH
        bot.edit_message_text("⬇️ Đã ép API nhả link! Đang kéo nhạc về server...", message.chat.id, msg.message_id)
        
        file_res = requests.get(download_url, stream=True)
        filename = f"{message.message_id}_audio.mp3"
        
        with open(filename, 'wb') as f:
            for chunk in file_res.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    
        # Kiểm tra giới hạn 50MB của nền tảng Telegram
        filesize = os.path.getsize(filename)
        if filesize > 50 * 1024 * 1024:
            bot.edit_message_text("❌ Nhạc bốc về thành công nhưng nặng hơn 50MB, Telegram chặn không cho gửi.", message.chat.id, msg.message_id)
            os.remove(filename)
            return

        # GỬI LÊN TELEGRAM
        bot.edit_message_text("📤 Kéo xong! Đang ném lên Telegram cho bạn...", message.chat.id, msg.message_id)
        
        with open(filename, 'rb') as audio:
            bot.send_audio(message.chat.id, audio)
            
        # Dọn dẹp sạch sẽ ổ cứng sau khi gửi
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
    return "Server Bot đang chạy trên Render bằng Ma trận API Vượt rào!"

def run_bot():
    bot.polling(non_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)

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
    bot.reply_to(message, "Bot đã cập nhật Ma trận API Châu Á 🚀! Gửi lệnh /yt <link> để tải nhạc.")

@bot.message_handler(commands=['yt'])
def download_youtube(message):
    text = message.text.split()
    if len(text) < 2:
        bot.reply_to(message, "Sai cú pháp! Hãy gõ: /yt <link_youtube>")
        return
    
    url = text[1]
    msg = bot.reply_to(message, "⏳ Đang gọi các Server API Châu Á VIP...")
    filename = None
    download_url = None
    
    try:
        # CHIẾN THUẬT: Đổi sang các API không khắt khe về IP Datacenter
        # 1. API Ryzendesu (Cực kỳ trâu bò)
        try:
            res = requests.get(f"https://api.ryzendesu.vip/api/downloader/ytmp3?url={url}", timeout=15)
            data = res.json()
            download_url = data.get('url') or (data.get('data') and (data['data'].get('url') or data['data'].get('dl')))
        except:
            pass

        # 2. API Siputzx
        if not download_url:
            try:
                res = requests.get(f"https://api.siputzx.my.id/api/d/ytmp3?url={url}", timeout=15)
                download_url = res.json().get('data', {}).get('dl')
            except:
                pass

        # 3. API Betabotz (Dự phòng cuối cùng)
        if not download_url:
            try:
                res = requests.get(f"https://api.betabotz.eu.org/api/download/ytmp3?url={url}&apikey=beta-thang", timeout=15)
                download_url = res.json().get('result', {}).get('mp3')
            except:
                pass

        # NẾU CẢ 3 API ĐỀU CHẾT
        if not download_url:
            bot.edit_message_text("❌ IP Render đã bị chặn sạch mạng lưới API. Hết cứu! Bạn bắt buộc phải chuyển nhà sang Kerit Cloud thôi.", message.chat.id, msg.message_id)
            return
            
        # KÉO FILE VỀ
        bot.edit_message_text("⬇️ Trúng link rồi! Đang kéo nhạc về server...", message.chat.id, msg.message_id)
        
        file_res = requests.get(download_url, stream=True)
        filename = f"{message.message_id}_audio.mp3"
        
        with open(filename, 'wb') as f:
            for chunk in file_res.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    
        # KIỂM TRA DUNG LƯỢNG
        filesize = os.path.getsize(filename)
        if filesize > 50 * 1024 * 1024:
            bot.edit_message_text("❌ Nhạc kéo về thành công nhưng nặng hơn 50MB, Telegram chặn không cho gửi.", message.chat.id, msg.message_id)
            os.remove(filename)
            return

        # GỬI LÊN TELEGRAM
        bot.edit_message_text("📤 Đang ném lên Telegram cho bạn...", message.chat.id, msg.message_id)
        with open(filename, 'rb') as audio:
            bot.send_audio(message.chat.id, audio)
            
        # Dọn dẹp ổ cứng
        bot.delete_message(message.chat.id, msg.message_id)
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.edit_message_text(f"❌ Lỗi hệ thống: {str(e)}", message.chat.id, msg.message_id)
        if filename and os.path.exists(filename):
            os.remove(filename)

@app.route('/')
def index():
    return "Server Bot đang chạy trên Render!"

def run_bot():
    bot.polling(non_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host="0.0.0.0", port=port)

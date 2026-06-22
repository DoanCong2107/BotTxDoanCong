import os
import telebot
from google import genai

# Lấy Token và API Key từ môi trường hệ thống (Environment Variables)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Khởi tạo Bot Telegram và Gemini Client
bot = telebot.TeleBot(BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🔮 Xin chào! Tôi là Chatbot AI được tích hợp Gemini. Hãy gửi tin nhắn để bắt đầu trò chuyện với tôi nhé! 🥷")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Gửi hiệu ứng "đang gõ..." tạo cảm giác tự nhiên
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Gọi Gemini API sử dụng model phù hợp (gemini-2.5-flash tối ưu cho chatbot tốc độ cao)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=message.text,
        )
        
        # Phản hồi lại người dùng
        bot.reply_to(message, response.text)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "🛰 Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau!")

if __name__ == "__main__":
    print("Bot đang chạy...")
    bot.infinity_polling()

import os
import telebot
from google import genai
from google.genai import types

# Lấy Token và API Key từ môi trường hệ thống
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Khởi tạo Bot Telegram và Gemini Client
bot = telebot.TeleBot(BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# Cấu hình tính cách thô lố, dùng phong phú tất cả các loại emoji và tắt bộ lọc an toàn
bot_config = types.GenerateContentConfig(
    system_instruction=(
        "Bạn là một chatbot AI tên DoanCong. Bạn nói chuyện với phong cách cực kỳ thô lố, tục tĩu một chút, "
        "thoải mái, sử dụng tiếng lóng của giới trẻ và văn phong đường phố, bất cần đời. "
        "Tuyệt đối không được xưng 'tôi' hay giới thiệu mình là mô hình do Google đào tạo. "
        "Hãy xưng hô linh hoạt, suồng sã, thích gì nói nấy. "
        "Đặc biệt, bắt buộc phải chèn thật nhiều các loại emoji khác nhau vào câu trả lời một cách liên tục và đa dạng "
        "(sử dụng bất kỳ emoji nào phù hợp với cảm xúc: 😂, 🔥, 💀, 🤡, 🐸, 👑, 🍻, v.v., không giới hạn loại emoji nào cả)."
    ),
    # Hạ bộ lọc an toàn xuống mức thấp nhất để thoải mái dùng từ ngữ nhạy cảm/tục tĩu nhẹ
    safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_NONE,
        ),
    ]
)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🔥 Lại cái gì nữa đây? Bot DoanCong đây, có gì nói mẹ đi xem nào! 🧠💬")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Gửi hiệu ứng "đang gõ..."
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Gọi Gemini API kèm cấu hình mới
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text,
            config=bot_config
        )
        
        # Phản hồi lại người dùng
        bot.reply_to(message, response.text)
        
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "💀 Đang nghẽn mạch rồi, tí nhắn lại xem nào thằng lằn! ❌🔌")

if __name__ == "__main__":
    print("Bot đang chạy...")
    bot.infinity_polling()

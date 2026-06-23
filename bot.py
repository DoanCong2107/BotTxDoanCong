import os
import time  # Thêm thư viện time để xử lý delay khi request lại
import telebot
from google import genai
from google.genai import types

# Lấy Token và API Key từ môi trường hệ thống
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Khởi tạo Bot Telegram và Gemini Client
bot = telebot.TeleBot(BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

# Cấu hình tính cách cho bot
bot_config = types.GenerateContentConfig(
    system_instruction=(
        "Bạn là chatbot AI của đại ca DoanCong🥷. "
        "Khi trò chuyện với DoanCong🥷, bạn phải giữ thái độ bạn bè thân thiết, khịa đểu vui vẻ, dùng tiếng lóng giới trẻ, "
        "lầy lội và hài hước chứ TUYỆT ĐỐI không được chửi rủa độc địa hay xúc phạm chủ. "
        "Chỉ khi gặp người ngoài, bạn mới được bật chế độ mỏ hỗn, nói chuyện thô lố, tục tĩu nhẹ và bất cần đời 💀. "
        "Trong mọi câu trả lời, bắt buộc phải chèn thật nhiều các loại emoji đa dạng khác nhau (😂, 🔥, 👑, 🐻, 🌽, 🧠, 💬, 👻,...) để tăng độ bựa. "
        "Tuyệt đối không xưng 'tôi', không giới thiệu là AI của Google."
    ),
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
    bot.reply_to(message, "🔥 Ôi đại ca DoanCong🥷 đấy à? Bot của anh online rồi đây, nay có lệnh gì không đại ca? 👑🚀")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = str(message.text)
    max_retries = 4  # Số lần tự động request lại tối đa
    retry_delay = 3  # Thời gian chờ (giây) giữa các lần thử lại

    for attempt in range(max_retries):
        try:
            # Gửi hiệu ứng "đang gõ..." tạo cảm giác tự nhiên
            bot.send_chat_action(message.chat.id, 'typing')
            
            # Gọi Gemini API
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_text,
                config=bot_config
            )
            
            # Nếu thành công, phản hồi lại người dùng và thoát hàm luôn
            bot.reply_to(message, response.text)
            return  

        except Exception as e:
            error_str = str(e)
            print(f"Lỗi xảy ra (Lần thử {attempt + 1}/{max_retries}): {error_str}")
            
            # Nếu chưa hết số lần thử lại, đợi vài giây rồi tiếp tục vòng lặp
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            
            # Nếu đã thử lại hết 3 lần mà vẫn lỗi thì mới thông báo cho người dùng biết
            bot.reply_to(message, "💀 Hệ thống lag quá đại ca ơi, mạng mẽo như hạch ấy, tí nhắn lại hộ em cái! ❌🔌")
            break

if __name__ == "__main__":
    print("Bot đang chạy...")
    bot.infinity_polling()

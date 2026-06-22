import os
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Load từ environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Lưu lịch sử chat theo từng user
chat_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Chào! Mình là AI Assistant của DoanCong🥷\n"
        "Cứ nhắn gì đó để bắt đầu chat!\n\n"
        "Dùng /clear để xóa lịch sử chat."
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_histories[user_id] = []
    await update.message.reply_text("🗑️ Đã xóa lịch sử chat!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Khởi tạo lịch sử nếu chưa có
    if user_id not in chat_histories:
        chat_histories[user_id] = []

    # Thêm tin nhắn user vào lịch sử
    chat_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Giới hạn lịch sử 20 tin nhắn để tránh tốn token
    if len(chat_histories[user_id]) > 20:
        chat_histories[user_id] = chat_histories[user_id][-20:]

    # Gọi Claude API
    await update.message.chat.send_action("typing")
    
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="Bạn là AI Assistant thân thiện, trả lời bằng tiếng Việt. Hãy trả lời ngắn gọn, dễ hiểu.",
        messages=chat_histories[user_id]
    )

    reply = response.content[0].text

    # Lưu reply của AI vào lịch sử
    chat_histories[user_id].append({
        "role": "assistant",
        "content": reply
    })

    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()

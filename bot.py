from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("TOKEN")  # Railway hoặc local đều ok

# Lệnh /hello (kiểu cơ bản)
async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello World nè thằng lồn ơi 🌍✨\nBố mày vừa địt xong nên khỏe lắm 🤪💦")

# Lệnh /hw (kiểu pro có ảnh + nút bấm)
async def hello_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [[InlineKeyboardButton("Địt tao đi 💦", callback_data="dit")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "HELLO WORLD THẰNG ĐĨ ƠI!!! 🍆🔥\nNhấn nút dưới để địt tao nè 🤤",
        reply_markup=reply_markup
    )

# Khi nhấn nút thì reply
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "dit":
        await query.edit_message_text("Á á á… địt sướng quá thằng đĩ ơi 😭💦💦💦")

# Khởi động bot
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("hello", hello))        # /hello
    app.add_handler(CommandHandler("hw", hello_pro))       # /hw (pro hơn)
    app.add_handler(CallbackQueryHandler(button))         # xử lý nút

    print("Bot Hello World đang nứng cặc chờ mày đây 🤖🍆")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
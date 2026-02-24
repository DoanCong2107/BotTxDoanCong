import asyncio
import os
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from ntgcalls import NTgCalls
from ntgcalls.types.input_stream import AudioPiped
from ntgcalls.types.input_stream.quality import HighQualityAudio
from yt_dlp import YoutubeDL

# Lấy từ Railway Variables
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = "musicbot"  # Tên file session sẽ tạo

app = Client(session_name, api_id=api_id, api_hash=api_hash)
calls = NTgCalls(app)

# Cấu hình yt-dlp để tải audio tốt nhất
ydl_opts = {
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "outtmpl": "downloads/%(id)s.%(ext)s",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "m4a",
        "preferredquality": "192",
    }],
}

# Tạo thư mục downloads nếu chưa có
os.makedirs("downloads", exist_ok=True)

@app.on_message(filters.command("play") & filters.group)
async def play(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Gõ lệnh: /play <tên bài hát hoặc link YouTube>")

    query = " ".join(message.command[1:])
    reply = await message.reply("🔍 Đang tìm và chuẩn bị nhạc...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if "entries" in info:
                if not info["entries"]:
                    return await reply.edit("❌ Không tìm thấy bài hát nào!")
                info = info["entries"][0]
            title = info.get("title", "Unknown")
            file_path = ydl.prepare_filename(info)

        chat_id = message.chat.id
        await calls.join_group_call(
            chat_id,
            AudioPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
            )
        )

        await reply.edit(
            f"🎵 **Đang phát trong voice chat:**\n"
            f"**{title}**\n"
            f"👤 {info.get('uploader', 'Unknown')}\n"
            f"⏱ {time.strftime('%M:%S', time.gmtime(info.get('duration', 0)))}"
        )
    except Exception as e:
        await reply.edit(f"❌ Lỗi: {str(e)[:200]}")

@app.on_message(filters.command("stop") & filters.group)
async def stop(client: Client, message: Message):
    try:
        chat_id = message.chat.id
        await calls.leave_group_call(chat_id)
        await message.reply("⏹ Đã dừng nhạc và rời voice chat!")
    except Exception as e:
        await message.reply(f"Không có nhạc đang phát hoặc lỗi: {str(e)}")

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply(
        "🎤 **Bot Phát Nhạc Voice Chat**\n\n"
        "Lệnh:\n"
        "/play <tên bài hát hoặc link YouTube> — Phát nhạc trong voice chat\n"
        "/stop — Dừng và rời voice chat\n\n"
        "Thêm bot làm admin group + quyền Manage Voice Chats!"
    )

async def main():
    await app.start()
    print("🚀 Bot đang chạy...")
    await calls.start()
    print("NTgCalls đã khởi động")
    await asyncio.Event().wait()  # Giữ bot sống

if __name__ == "__main__":
    asyncio.run(main())
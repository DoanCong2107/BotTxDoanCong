import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from py_tgcalls import PyTgCalls  # tên mới: py_tgcalls (hoặc pytgcalls nếu alias)
from py_tgcalls.types.input_stream import AudioPiped
from py_tgcalls.types.input_stream.quality import HighQualityAudio
from yt_dlp import YoutubeDL

# Biến môi trường
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = "musicbot"

app = Client(session_name, api_id, api_hash)
calls = PyTgCalls(app)

ydl_opts = {
    "format": "bestaudio[ext=m4a]",
    "quiet": True,
    "no_warnings": True,
    "outtmpl": "downloads/%(id)s.%(ext)s",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "m4a",
        "preferredquality": "192",
    }],
}

@app.on_message(filters.command("play") & filters.group)
async def play(_, message: Message):
    if len(message.command) < 2:
        return await message.reply("Gõ /play <tên bài hát hoặc link YouTube>")

    query = " ".join(message.command[1:])
    reply = await message.reply("🔍 Đang tìm nhạc...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            file_path = ydl.prepare_filename(info)

        chat_id = message.chat.id
        await calls.join_group_call(
            chat_id,
            AudioPiped(
                file_path,
                audio_parameters=HighQualityAudio(),
            ),
        )
        await reply.edit(f"🎵 Đang phát: **{info['title']}** trong voice chat!")
    except Exception as e:
        await reply.edit(f"Lỗi: {str(e)}")

@app.on_message(filters.command("stop") & filters.group)
async def stop(_, message: Message):
    chat_id = message.chat.id
    await calls.leave_group_call(chat_id)
    await message.reply("⏹ Đã dừng nhạc và rời voice chat!")

async def main():
    await app.start()
    print("Bot đang chạy...")
    await calls.start()
    await asyncio.Event().wait()  # Giữ bot sống

if __name__ == "__main__":
    asyncio.run(main())
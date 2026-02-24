import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from ntgcalls import NTgCalls, AudioPiped
from ntgcalls.types.input_stream.quality import HighQualityAudio
from yt_dlp import YoutubeDL

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session_name = "musicbot"

app = Client(session_name, api_id, api_hash)
calls = NTgCalls(app)

ydl_opts = {
    "format": "bestaudio[ext=m4a]",
    "quiet": True,
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
        return await message.reply("Gõ /play <tên bài hát hoặc link>")

    query = " ".join(message.command[1:])
    reply = await message.reply("🔍 Đang tìm...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=True)
            if 'entries' in info:
                info = info['entries'][0]
            file_path = ydl.prepare_filename(info)

        chat_id = message.chat.id
        await calls.join_group_call(
            chat_id,
            AudioPiped(file_path, audio_parameters=HighQualityAudio())
        )
        await reply.edit(f"🎵 Phát: **{info['title']}**")
    except Exception as e:
        await reply.edit(f"Lỗi: {str(e)}")

@app.on_message(filters.command("stop") & filters.group)
async def stop(_, message: Message):
    await calls.leave_group_call(message.chat.id)
    await message.reply("⏹ Dừng và rời voice chat!")

async def main():
    await app.start()
    print("Bot chạy...")
    await calls.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
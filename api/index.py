import yt_dlp
import os

def download_yt_audio(url, chat_id, bot):
    # Cấu hình chỉ tải audio và convert sang mp3
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192', # Chất lượng 192kbps
        }],
        'outtmpl': '%(id)s.%(ext)s', # Đặt tên file theo ID video
        'max_filesize': 50000000, # Giới hạn 50MB (Limit của Telegram)
    }

    try:
        # Tải file
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = f"{info['id']}.mp3"
            title = info.get('title', 'Audio')

        # Gửi file mp3 qua Telegram
        with open(filename, 'rb') as audio:
            bot.send_audio(chat_id, audio, title=title)
        
        # Xóa file sau khi gửi xong để nhẹ server
        os.remove(filename)

    except Exception as e:
        bot.send_message(chat_id, f"Lỗi khi tải: {str(e)}")

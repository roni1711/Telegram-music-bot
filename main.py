import os
from pyrogram import Client, filters
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import Update
from pytgcalls.types.input_stream import AudioPiped
from youtube_search import YoutubeSearch
import yt_dlp

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = Client("musicbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
vc = PyTgCalls(app)

def yt_search(query):
    results = YoutubeSearch(query, max_results=1).to_dict()
    if not results:
        return None
    return f"https://www.youtube.com{results[0]['url_suffix']}"

def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': 'downloads/audio.%(ext)s',
        'noplaylist': True,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("🎧 Welcome! Use /play <song name> to stream music in VC.")

@app.on_message(filters.command("play"))
async def play(client, message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        return await message.reply("Please provide a song name.")
    query = " ".join(message.command[1:])
    url = yt_search(query)
    if not url:
        return await message.reply("Song not found.")
    file_path = download_audio(url)
    await vc.join_group_call(chat_id, AudioPiped(file_path))
    await message.reply(f"🎶 Now playing: {query}")

@app.on_message(filters.command("pause"))
async def pause(_, message):
    await vc.pause_stream(message.chat.id)
    await message.reply("⏸️ Paused.")

@app.on_message(filters.command("resume"))
async def resume(_, message):
    await vc.resume_stream(message.chat.id)
    await message.reply("▶️ Resumed.")

@app.on_message(filters.command("stop"))
async def stop(_, message):
    await vc.leave_group_call(message.chat.id)
    await message.reply("🛑 Stopped music and left voice chat.")

@vc.on_stream_end()
async def stream_end_handler(_, update: Update):
    await vc.leave_group_call(update.chat_id)

async def run():
    await app.start()
    await vc.start()
    print("✅ Bot is running...")
    await idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())

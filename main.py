import discord
from discord.ext import commands
from datetime import datetime
from flask import Flask
from threading import Thread
import os

# --- Flask Webサーバー（Replitのスリープ回避） ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Discord Botのインテント設定 ---
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- 対象のリアクションとファイル拡張子 ---
TARGET_REACTION = "📷"
VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov", ".webm", ".pdf")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    if str(payload.emoji.name) != TARGET_REACTION:
        return

    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if not message.attachments:
        return

    photo_channel = discord.utils.get(guild.channels, name="写真")
    if photo_channel is None:
        print("写真チャンネルが見つかりません")
        return

    for attachment in message.attachments:
        if attachment.filename.lower().endswith(VALID_EXTENSIONS):
            timestamp = message.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
            message_url = f"https://discord.com/channels/{guild.id}/{channel.id}/{message.id}"

            forward_text = (
                f"📎 {message.author.name} がリアクションされた投稿を転送しました\n"
                f"🕒 投稿日時: {timestamp}\n"
                f"🔗 [元メッセージへ移動]({message_url})"
            )

            await photo_channel.send(
                forward_text,
                file=await attachment.to_file(),
                suppress_embeds=True
            )

# --- WebサーバーでReplitスリープ防止 ---
keep_alive()

# --- Botを起動（.envファイルからトークン取得） ---
bot.run(os.getenv("TOKEN"))
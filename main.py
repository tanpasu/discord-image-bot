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

# --- リアクションごとの転送先チャンネル名を設定 ---
TARGET_REACTIONS = {
    "📷": "写真",
    "🐶": "画像"
}

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mov", ".webm", ".pdf")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    emoji_name = str(payload.emoji.name)
    
    # リアクションが対象外ならスキップ
    if emoji_name not in TARGET_REACTIONS:
        return

    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if not message.attachments:
        return

    # 転送先チャンネル名を取得
    target_channel_name = TARGET_REACTIONS[emoji_name]
    target_channel = discord.utils.get(guild.channels, name=target_channel_name)
    
    if target_channel is None:
        print(f"{target_channel_name} チャンネルが見つかりません")
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

            await target_channel.send(
                forward_text,
                file=await attachment.to_file(),
                suppress_embeds=True
            )

# --- WebサーバーでReplitスリープ防止 ---
keep_alive()

# --- Botを起動（.envファイルからトークン取得） ---
bot.run(os.getenv("TOKEN"))

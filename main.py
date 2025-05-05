"""
Telegraph Uploader Bot

This module defines a Telegram bot that can upload photos to Telegra.ph and 
create instant view links for text messages.
The bot is built using the Pyrogram library and the Telegraph API.

Features:
- Upload photos to Telegra.ph and return the URL.
- Create Telegra.ph posts from text messages, with support for custom titles and emoji removal.

Classes:
- Bot: A subclass of Pyrogram's Client, representing the Telegram bot.

Functions:
- start_handlers: Handles the /start command to provide a welcome message.
- photo_handler: Handles incoming photo messages, uploads them to Telegra.ph,
                 and sends the URL to the user.
- text_handler: Handles incoming text messages, creates Telegra.ph posts, 
                and sends the URL to the user.

Patterns:
- EMOJI_PATTERN: Regular expression to match <emoji> tags in the text.
- TITLE_PATTERN: Regular expression to match title lines in the text.

Usage:
1. Send a /start command to receive a welcome message.
2. Send a photo to upload it to Telegra.ph and get the link.
3. Send a text message in the format 
        Title: {title}
        {content}
    to create a Telegra.ph post.
"""

import os
import re
import time
import logging
import logging.config

from telegraph import upload_file, Telegraph
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from utils import progress

try:
    import uvloop # https://docs.pyrogram.org/topics/speedups#uvloop
    uvloop.install()
except ImportError:
    pass

# Get logging configurations
logging.config.fileConfig("logging.conf")
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class Bot(Client):  # pylint: disable=too-many-ancestors
    """Telegram bot client for uploading photos and creating posts on Telegra.ph."""

    def __init__(self):
        """Initializes the bot with the provided configuration."""
        super().__init__(
            "telegraph",
            bot_token=Config.BOT_TOKEN,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
        )

    async def start(self):
        """Starts the bot and prints the bot username."""
        await super().start()
        print(f"Bot Started at @{self.me.username}")

    async def stop(self, *args, **kwargs):
        """Stops the bot and prints a stop message."""
        await super().stop(*args, **kwargs)
        print("Session Stopped...")


bot = Bot()
EMOJI_PATTERN = re.compile(r'<emoji id="\d+">')
TITLE_PATTERN = re.compile(r"title:? (.*)", re.IGNORECASE)


@bot.on_message(filters.command("start") & filters.incoming & filters.private)
async def start_handlers(_: Bot, message: Message) -> None:
    """Handles the /start command to provide a welcome message to the user."""

    await message.reply(
        "ʜᴇʟʟᴏ **ᴅᴇᴀʀ!**\n\n"
        "👋 **ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴛᴇʟᴇɢʀᴀ.ᴘʜ ᴜᴘʟᴏᴀᴅᴇʀ ʙᴏᴛ!**\n\n"
        "ᴡɪᴛʜ ᴛʜɪꜱ ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ:\n"
        " • **ᴜᴘʟᴏᴀᴅ ᴘʜᴏᴛᴏꜱ**: ꜱᴇɴᴅ ᴍᴇ ᴀ ᴘʜᴏᴛᴏ, ᴀɴᴅ "
        "ɪ'ʟʟ ᴜᴘʟᴏᴀᴅ ɪᴛ ᴛᴏ ᴛᴇʟᴇɢʀᴀ.ᴘʜ, ᴘʀᴏᴠɪᴅɪɴɢ ʏᴏᴜ ᴡɪᴛʜ ᴀ ʟɪɴᴋ.\n"
        " • **ᴄʀᴇᴀᴛᴇ ɪɴꜱᴛᴀɴᴛ ᴠɪᴇᴡ ʟɪɴᴋꜱ**: ꜱᴇɴᴅ ᴍᴇ ᴀ ᴛᴇxᴛ, ᴀɴᴅ "
        "ɪ'ʟʟ ᴄʀᴇᴀᴛᴇ ᴀɴ ɪɴꜱᴛᴀɴᴛ ᴠɪᴇᴡ ʟɪɴᴋ ꜰᴏʀ ɪᴛ.\n\n"
        "📌 **ᴜꜱᴀɢᴇ**:\n"
        "• ꜱᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ ᴅɪʀᴇᴄᴛʟʏ ᴛᴏ ᴜᴘʟᴏᴀᴅ ɪᴛ.\n"
        "• ꜱᴇɴᴅ ᴀ ᴛᴇxᴛ ᴍᴇꜱꜱᴀɢᴇ ɪɴ ᴛʜᴇ ꜰᴏʀᴍᴀᴛ ᴍᴇɴᴛɪᴏɴᴇᴅ ʙᴇʟᴏᴡ "
        "ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ ᴛᴇʟᴇɢʀᴀ.ᴘʜ ᴘᴏꜱᴛ.\n\n"
        "🔗 **ᴀʙᴏᴜᴛ ᴛᴇʟᴇɢʀᴀ.ᴘʜ**:\n"
        "ᴛᴇʟᴇɢʀᴀ.ᴘʜ ɪꜱ ᴀ ᴍɪɴɪᴍᴀʟɪꜱᴛ ᴘᴜʙʟɪꜱʜɪɴɢ ᴛᴏᴏʟ ᴛʜᴀᴛ ᴀʟʟᴏᴡꜱ "
        "ʏᴏᴜ ᴛᴏ ᴄʀᴇᴀᴛᴇ ʀɪᴄʜʟʏ ꜰᴏʀᴍᴀᴛᴛᴇᴅ ᴘᴏꜱᴛꜱ ᴡɪᴛʜ ᴘʜᴏᴛᴏꜱ, ᴠɪᴅᴇᴏꜱ, ᴀɴᴅ "
        "ᴀʟʟ ꜱᴏʀᴛꜱ ᴏꜰ ᴇᴍʙᴇᴅᴅᴇᴅ ᴄᴏɴᴛᴇɴᴛ.\n\n"
        "🌟 **ɢᴇᴛ ꜱᴛᴀʀᴛᴇᴅ**: ᴊᴜꜱᴛ ꜱᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ ᴏʀ ᴛᴇxᴛ ᴍᴇꜱꜱᴀɢᴇ, ᴀɴᴅ ʟᴇᴛ ᴍᴇ ᴅᴏ ᴛʜᴇ ʀᴇꜱᴛ!\n\n"
        "🛠 **ꜱᴏᴜʀᴄᴇ ᴄᴏᴅᴇ**: "
        "[ꜰᴏʀᴋ ᴏɴ ɢɪᴛʜᴜʙ](https://github.com/Ns-AnoNymouS/Telegraph-Uploader)\n\n"
        "📝 **ᴄᴜꜱᴛᴏᴍ ᴛɪᴛʟᴇ**:\n"
        "```txt\n"
        "ᴛɪᴛʟᴇ: {title}\n{content}```\n\n"
        "📝 **ᴇxᴀᴍᴘʟᴇ**:\n"
        "```txt\n"
        "ᴛɪᴛʟᴇ: ᴍʏ ꜰɪʀꜱᴛ ᴛᴇʟᴇɢʀᴀᴘʜ ᴘᴏꜱᴛ\n"
        "ᴛʜɪꜱ ɪꜱ ᴛʜᴇ ᴄᴏɴᴛᴇɴᴛ ᴏꜰ ᴍʏ ꜰɪʀꜱᴛ ᴛᴇʟᴇɢʀᴀᴘʜ ᴘᴏꜱᴛ!\n"
        "ɪ'ᴍ ᴜꜱɪɴɢ ᴛʜᴇ ᴛᴇʟᴇɢʀᴀ.ᴘʜ ᴜᴘʟᴏᴀᴅᴇʀ ʙᴏᴛ ᴛᴏ ᴘᴜʙʟɪꜱʜ ᴛʜɪꜱ.\n\n"
        "ʜᴇʀᴇ'ꜱ ᴀ ʟɪꜱᴛ ᴏꜰ ᴡʜᴀᴛ ɪ ʟɪᴋᴇ:\n"
        "- ᴘʀᴏɢʀᴀᴍᴍɪɴɢ 💻\n"
        "- ʀᴇᴀᴅɪɴɢ 📚\n"
        "- ᴛʀᴀᴠᴇʟɪɴɢ ✈️\n"
        "- ᴍᴜꜱɪᴄ 🎵\n\n"
        "ʏᴏᴜ ᴄᴀɴ ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴘᴏꜱᴛꜱ ᴛᴏᴏ. ᴊᴜꜱᴛ ꜰᴏʟʟᴏᴡ ᴛʜᴇ ꜰᴏʀᴍᴀᴛ ᴀɴᴅ ᴇɴᴊᴏʏ!"
        "```\n",
        disable_web_page_preview=True,
        quote=True,
    )


@bot.on_message(filters.photo & filters.incoming & filters.private)
async def photo_handler(_: Bot, message: Message) -> None:
    """
    Handles incoming photo messages by uploading the photo to Telegra.ph
    and sending the link to the user.
    """

    try:
        msg = await message.reply_text("ᴘʀᴏᴄᴇꜱꜱɪɴɢ...⏳", quote=True)
        location = f"./{message.from_user.id}{time.time()}/"
        start_time = time.time()
        file = await message.download(
            location, progress=progress, progress_args=(msg, start_time)
        )
        media_upload = upload_file(file)
        telegraph_link = f"https://telegra.ph{media_upload[0]}"
        await msg.edit(telegraph_link)
        os.remove(file)
        os.rmdir(location)
    except FileNotFoundError:
        pass
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(e)
        await msg.edit(f"**ᴇʀʀᴏʀ:**\n{e}")


@bot.on_message(filters.text & filters.incoming & filters.private)
async def text_handler(_: Bot, message: Message) -> None:
    """
    Handles incoming text messages
    by creating a Telegra.ph post
    and sending the link to the user.
    """

    try:
        msg = await message.reply_text("ᴘʀᴏᴄᴇꜱꜱɪɴɢ...⏳", quote=True)

        short_name = "Ns Bots"
        user = Telegraph().create_account(short_name=short_name)
        access_token = user.get("access_token")
        content = message.text.html
        content = re.sub(EMOJI_PATTERN, "", content).replace("</emoji>", "")

        title = re.findall(TITLE_PATTERN, content)
        if len(title) != 0:
            title = title[0]
            content = "\n".join(content.splitlines()[1:])
        else:
            title = message.from_user.first_name
        content = content.replace("\n", "<br>")
        author_url = (
            f"https://telegram.dog/{message.from_user.username}"
            if message.from_user.id
            else None
        )

        response = Telegraph(access_token=access_token).create_page(
            title=title,
            html_content=content,
            author_name=str(message.from_user.first_name),
            author_url=author_url,
        )
        path = response["path"]
        await msg.edit(f"https://telegra.ph/{path}")
    except ValueError as e:
        logger.error(e)
        await msg.edit("ᴜɴᴀʙʟᴇ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ɪɴꜱᴛᴀɴᴛ ᴠɪᴇᴡ ʟɪɴᴋ.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(e)
        await msg.edit(f"**ᴇʀʀᴏʀ:**\n{e}")


if __name__ == "__main__":
    bot.run()

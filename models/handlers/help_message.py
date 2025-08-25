from aiogram import types
from aiogram.utils.markdown import html_decoration as hd
from models.utils.config import *

async def handler_help_message(self, message: types.Message) -> None:
    await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return
    await message.reply(
        await self.get_translation(
            message.from_user.id,
            "helpMessage",
            self.bot_username, CHAT_LIVE_EVENTS_LINK,
        ), reply_markup=await self.get_reply_keyboard_by_message(message), disable_web_page_preview=True
    )
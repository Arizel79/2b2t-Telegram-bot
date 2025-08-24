from aiogram.enums import ChatType
from aiogram import types
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models.utils.utils import is_valid_minecraft_username, is_valid_minecraft_uuid
import json
from models.utils.config import *

import re

async def handler_get_player_stats(self, message: types.Message, register_msg: bool = True) -> None:
    print("1dqsd122e")
    if register_msg:
        await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return
    text = message.text
    lang = (await self.db.get_user_stats(message.from_user.id))["lang"]
    try:
        query = text.split(maxsplit=1)[1] if message.text.startswith("/") else message.text
    except IndexError as e:
        await message.reply(await self.get_translation(message.from_user.id, "playerStatsCommandUsage"))
        return
    lst = text.split()
    self.logger.info(f"Lst: {lst}")
    if lst[0] == "/start":
        self.logger.info(f"Handling start command in handler_get_player_stats: {query}")
        pattern = r'^/start pl_(\S+)$'
        match = re.match(pattern, message.text)
        if match:
            player =  match.group(1)
            self.logger.info(f"detected player: {player}")
        else:
            return
    else:
        if len(lst) > 1:
            await message.reply(await self.get_translation(message.from_user.id, "userError"))
            return
        else:
            player = query

    msg = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))

    await self.get_player_stats_and_edit_message(message.from_user.id, player, msg)
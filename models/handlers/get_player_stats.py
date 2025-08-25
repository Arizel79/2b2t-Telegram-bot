from aiogram.enums import ChatType
from aiogram import types
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models.utils.utils import is_valid_minecraft_username, is_valid_minecraft_uuid
import json
from models.utils.config import *

import re


async def handler_get_player_stats(self, message: types.Message, register_msg: bool = True) -> None:
    if register_msg:
        await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return
    text = message.text
    lang = (await self.db.get_user_stats(message.from_user.id))["lang"]

    # Определяем, является ли сообщение командой с параметром
    if text.startswith('/'):
        # Обработка команды /start с параметром
        if text.startswith('/start'):
            pattern = r'^/start pl_(\S+)$'
            match = re.match(pattern, text)
            if match:
                player = match.group(1)
                self.logger.info(f"detected player from /start: {player}")
            else:
                return
        # Обработка других команд (например, /pl, /stats)
        else:
            # Разделяем команду и аргументы
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                await message.reply(await self.get_translation(message.from_user.id, "playerStatsCommandUsage"), reply_markup=await self.get_reply_keyboard_by_message(message))
                return
            player = parts[1].strip()
    else:
        # Обработка простого текста (не команды)
        player = text.strip()

    # Проверяем валидность имени игрока
    if not is_valid_minecraft_username(player):
        await message.reply(await self.get_translation(message.from_user.id, "userError"), reply_markup=await self.get_reply_keyboard_by_message(message))
        return

    msg = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"), reply_markup=await self.get_reply_keyboard_by_message(message))
    await self.get_player_stats_and_edit_message(message.from_user.id, player, msg)
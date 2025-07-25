from aiogram.enums import ChatType
from aiogram import types
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models.utils.utils import is_valid_minecraft_username, is_valid_minecraft_uuid
import json
from models.utils.config import *



async def handler_get_player_stats(self, message: types.Message, register_msg: bool = True) -> None:
    if register_msg:
        await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return



    lang = (await self.db.get_user_stats(message.from_user.id))["lang"]
    try:
        query = message.text.split(maxsplit=1)[1] if message.text.startswith("/") else message.text
    except IndexError as e:
        await message.reply(await self.get_translation(message.from_user.id, "playerStatsCommandUsage"))
        return

    if len(query.split()) > 1:
        await message.reply(await self.get_translation(message.from_user.id, "userError"))
        return

    msg = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))

    try:
        answer_ = await self.get_player_stats_answer(query, message.from_user.id, register_query_id=True)
        if len(answer_) == 2:
            answer, query_id = answer_
            await msg.edit_text(answer,
                                reply_markup=await self.get_player_stats_keyboard(message.from_user.id, query_id))
        else:
            return

    except self.api_2b2t.Api2b2tError as e:
        self.logger.error(e)
        await msg.edit_text(await self.get_translation(message.from_user.id, "userError"))

    except Exception as e:
        self.logger.error(e)
        await msg.edit_text(await self.get_translation(message.from_user.id, "error"))

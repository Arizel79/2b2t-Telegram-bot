from aiogram.enums import ChatType
from aiogram import types
from models.utils.utils import is_valid_minecraft_username, is_valid_minecraft_uuid
import json


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
        if is_valid_minecraft_uuid(query):
            answer = await self.api_2b2t.get_printaleble_player_stats(message.from_user.id, uuid=query)
        elif is_valid_minecraft_username(query):
            answer = await self.api_2b2t.get_printaleble_player_stats(message.from_user.id, player=query)
        else:
            await msg.edit_text(await self.get_translation(message.from_user.id, "userError"))
            return
        await msg.edit_text(answer)
    except self.api_2b2t.Api2b2tError as e:
        self.logger.error(e)
        await msg.edit_text(await self.get_translation(message.from_user.id, "userError"))

    except Exception as e:
        self.logger.error(e)
        await msg.edit_text(await self.get_translation(message.from_user.id, "error"))

from aiogram import types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from models.utils.utils import is_valid_minecraft_username, is_valid_minecraft_uuid
from aiogram.filters import CommandObject
import math
from models.utils.config import *

async def handler_tracking_command(self, message: types.Message, register_msg: bool = True) -> None:
    if register_msg:
        await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return

    class FakeCallback:
        def __init__(self, from_user, message):
            self.from_user = from_user
            self.message = message

    callback = FakeCallback(message.from_user, message)
    await self.show_tracking_list( callback, 0)


async def handler_tracking_add_command(self, message: types.Message, command: CommandObject):
    await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return
    
    user_id = message.from_user.id

    if not command.args:
        text = await self.get_translation(user_id, "trackingAddUsage")
        await message.reply(text)
        return

    player_name = command.args.strip()

    if not is_valid_minecraft_username(player_name):
        text = await self.get_translation(user_id, "trackingInvalidUsername")
        await message.reply(text)
        return

    try:
        uuid = await self.api_2b2t.get_uuid_from_username(player_name)
        if not uuid:
            text = await self.get_translation(user_id, "trackingPlayerNotFound")
            await message.reply(text.format(username=player_name))
            return

        username = await self.api_2b2t.get_username_from_uuid(uuid)
        if not username:
            username = player_name

        existing = await self.db.get_player_tracking(user_id, player_username=username, player_uuid=uuid)
        if existing:
            text = await self.get_translation(user_id, "trackingAlreadyExists")
            await message.reply(text.format(username=username))
            return

        tracking_id = await self.db.add_player_tracking(
            user_id=user_id,
            player_username=username,
            player_uuid=uuid
        )

        text = await self.get_translation(user_id, "trackingAdded", username)
        await message.reply(text.format(username=username))

    except Exception as e:
        self.logger.error(f"Error adding tracking: {e}")
        text = await self.get_translation(user_id, "trackingAddingError")
        await message.reply(text)

from models.utils.config import *
from aiogram.enums import ChatType
from aiogram import types
import json


from models.handlers.help_message import *
from models.handlers.start_message import *
from models.handlers.callback_settings import *
from models.handlers.command_set_language import *
from models.handlers.callback_set_language import *
from models.handlers.settings import *
from models.handlers.search_chat import *
from models.handlers.get_player_stats import *
from models.handlers.get_2b2t_info import *
from models.handlers.get_2b2t_tablist import *


async def handler_text(self, message: types.Message) -> None:
    await self.on_msg(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return
    if message.chat.type == ChatType.PRIVATE:
        user_configs = (await self.db.get_user_stats(message.from_user.id))["configs"]
        config_mode = None

        if message.text == await self.get_translation(message.from_user.id, "get2b2tinfo"):
            await self.handler_get_2b2t_info( message, register_msg=False)
            return
        elif message.text == await self.get_translation( message.from_user.id, "getPlayerStats"):
            config_mode = "player_stats"
            await message.reply(await self.get_translation(message.from_user.id, "enterPlayer"))

        elif message.text == await self.get_translation(message.from_user.id, "getSettings"):
            await self.handler_settings_message(message, register_msg=False)
            return

        elif message.text == await self.translator.get_translation(message.from_user.id, "searchChat"):
            await message.reply(await self.translator.get_translation(message.from_user.id, "enterChatSearchQuery"))
            config_mode = CHAT_SERACH_MODE

        elif user_configs.get("mode", None) == "player_stats":
            await self.handler_get_player_stats(message, register_msg=False)
            return

        elif user_configs.get("mode", None) == CHAT_SERACH_MODE:
            await self.handler_search_chat(message, register_msg=False)
            return

        else:
            await self.handler_start(message, register_msg=False)

        if not config_mode is None:
            user_configs["mode"] = config_mode
            await self.db.update_configs(message.from_user.id, json.dumps(user_configs))

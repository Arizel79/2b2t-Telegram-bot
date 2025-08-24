import html
from aiogram import types
import json
from random import randint
from models.utils.config import *


async def handler_search_chat(self, message: types.Message, register_msg: bool = True) -> None:
    user_id = message.from_user.id
    if register_msg:
        await self.on_event(message)

    if not await self.is_handler_msgs(message.from_user.id):
        return

    if self.is_command(message.text):

        lst = message.text.split()
        if len(lst) > 1:
            query = " ".join(lst[1:])
        else:
            await message.reply(await self.get_translation(message.from_user.id, "searchCommandUsage"))
            return
    else:
        query = message.text

    user_configs = (await self.db.get_user_stats(message.from_user.id))["configs"]

    await self.db.update_configs(message.from_user.id, json.dumps(user_configs))
    if 3 > len(query) or len(query) > 50: # ! chatSearchInvalidQueryLength  # 3 and 50
        msg_my = await message.reply(await self.get_translation(message.from_user.id, "chatSearchInvalidQueryLength"))
        return
    query_id = await self.db.add_saved_state({"type": "search_chat", "word": query, "page": 1,
                                             "user_id": message.from_user.id, "page_size": SEARCH_PAGE_SIZE})

    msg_my = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))

    try:
        answer = await self.api_2b2t.get_printable_2b2t_chat_search_page(query_id)
        await msg_my.edit_text(answer, reply_markup=await self.get_markup_chat_search(query_id))

    except self.api_2b2t.Api2b2tError as e:
        self.logger.error(f"Error in handler_search_chat: {e}")
        self.logger.exception(e)
        await msg_my.edit_text(await self.get_translation(message.from_user.id, "error"))

    except Exception as e:
        self.logger.error(f"Error in handler_search_chat: {e}")
        self.logger.exception(e)
        await msg_my.edit_text(await self.get_translation(message.from_user.id, "unknownError"))

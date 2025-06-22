import logging
from aiogram import types
import json

async def handler_search_chat(self, message: types.Message, register_msg: bool = True) -> None:
    user_id = message.from_user.id
    if register_msg:
        await self.on_msg(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return

    if self.is_command(message.text):
        lst = message.text.split()
        if len(lst) > 1:
            query = lst[1:]
            print("q: ", query)
    else:
        query = message.text

    user_configs = (await self.db.get_user_stats(message.from_user.id))["configs"]
    # user_configs["mode"] = CHAT_SERACH_MODE
    await self.db.update_configs(message.from_user.id, json.dumps(user_configs))
    await message.reply("функция пока не работает")
    # await message.reply(await self.get_translation(user_id, "enterChatSearchQuery"))
    return

    msg_my = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))
    try:
        answer = await self.search_2b2t_chat(message.from_user.id, query)
        await msg_my.edit_text(answer)
    except api.Api2b2tError as e:
        logging.error(f"Api2b2tError: {e}")
        await message.reply(await self.get_translation(message.from_user.id, "error"))
    except Exception as e:
        logging.error(f"API Error: {type(e).__name__}: {e}")
        await message.reply(await self.get_translation(message.from_user.id, "userError"))

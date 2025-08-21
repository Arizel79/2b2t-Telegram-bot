import html
import logging
from aiogram import types
import json
from random import randint
from models.utils.utils import *
from models.utils.config import *


async def handler_search_messages_from_player(self, message: types.Message, register_msg: bool = True) -> None:
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
            await message.reply(await self.get_translation(message.from_user.id, "searchMessagesFromPlayerCommandUsage"))
            return
    else:
        query = message.text

    user_configs = (await self.db.get_user_stats(message.from_user.id))["configs"]

    await self.db.update_configs(message.from_user.id, json.dumps(user_configs))
    saved_state = {"type": "msgs from player", "page": 1,
                                             "user_id": message.from_user.id, "page_size":SEARCH_FROM_PLAYER_PAGE_SIZE}
    if is_valid_minecraft_username(query):
        saved_state["player_username"] = query
    elif is_valid_minecraft_uuid(query):
        saved_state["player_uuid"] = query
    else:
        await message.reply(await self.get_translation(message.from_user.id, "userError"))
        return
    query_id = await self.db.add_saved_state(saved_state)

    msg_my = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))
    try:
        answer = await self.api_2b2t.get_printable_messages_from_player_in_2b2t_chat(query_id)
        await msg_my.edit_text(answer, reply_markup=await self.get_markup_search_messages_from_player(query_id))

    except self.api_2b2t.PlayerNeverWasOn2b2tError as e:

        await msg_my.edit_text(await self.get_translation(message.from_user.id, "playerWasNotOn2b2t", query))
    except self.api_2b2t.Api2b2tError as e:
        logging.error(f"Api2b2tError: {e}")
        await msg_my.edit_text(await self.get_translation(message.from_user.id, "userError"))
    # except Exception as e:
    #     logging.error(f"{type(e).__name__}: {e}")
    #     await message.reply(await self.get_translation(message.from_user.id, "error") + f"\n\n<code>{type(e).__name__}: {html.escape(str(e))}</code>")
    finally:
        pass

from aiogram import types
from models.utils import api_wrapper
from models.utils.config import *


async def handler_get_playtime_top(self, message: types.Message, register_msg: bool = True) -> None:
    if register_msg:
        await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return

    msg_my = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))
    query_id = await self.db.add_saved_state({"type": "playtime_top", "page": 1,
                                              "user_id": message.from_user.id, "page_size": PLAYTIME_TOP_PAGE_SIZE})

    try:
        answer = await self.api_2b2t.get_printable_playtime_top(query_id)
        await msg_my.edit_text(answer, reply_markup=await self.get_nav_markup(query_id))
    finally:
        pass
    # except self.api_2b2t.Api2b2tError as e:
    #     self.logger.error(f"Api2b2tError: {e}")
    # #     await message.reply(await self.get_translation(message.from_user.id, "error"))
    # except Exception as e:
    #     self.logger.error(f"API Error: {type(e).__name__}: {e}")
    #     await message.reply(await self.get_translation(message.from_user.id, "userError"))

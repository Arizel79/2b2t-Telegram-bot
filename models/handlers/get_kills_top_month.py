from aiogram import types
from models.utils import api
from models.utils.config import *


async def handler_get_kills_top_month(self, message: types.Message, register_msg: bool = True) -> None:
    if register_msg:
        await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return

    msg_my = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))
    query_id = await self.db.add_saved_state({"type": "kills_top_month", "page": 1,
                                              "user_id": message.from_user.id, "page_size": KILLS_TOP_MONTH_PAGE_SIZE})
    try:
        answer = await self.api_2b2t.get_printable_kills_top_month(query_id)
        await msg_my.edit_text(answer, reply_markup=await self.get_nav_markup(query_id))

    except Exception as e:
        self.logger.error('Error in handler_get_kills_top_month:')
        self.logger.exception(e)
        await msg_my.edit_text(await self.get_translation(message.from_user.id, "error"))
    finally:
        pass


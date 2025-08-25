from aiogram import types
from aiogram.utils.markdown import html_decoration as hd
from models.utils import api_wrapper
from models.utils.config import *

async def handler_get_2b2t_tablist(self, message: types.Message, register_msg: bool = True) -> None:
    if register_msg:
        await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return

    try:
        msg = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))
        query_id = await self.db.add_saved_state({"type": "tablist", "page": 1,
                                                  "user_id": message.from_user.id, "page_size": TABLIST_PAGE_SIZE})

        answer = await self.api_2b2t.get_printable_2b2t_tablist_page(query_id)
        tl_pages_count = await self.api_2b2t.get_2b2t_tablist_pages_count(TABLIST_PAGE_SIZE)
        await msg.edit_text(answer, reply_markup=await self.get_markup_tablist(query_id))

    except self.api_2b2t.Api2b2tError as e:
        self.logger.error(f"Error in handler_get_2b2t_tablist: {e}")
        self.logger.exception(e)
        await msg.edit_text(await self.get_translation(message.from_user.id, "userError"))

    except Exception as e:
        self.logger.error(f"Error in handler_get_2b2t_tablist: {e}")
        self.logger.exception(e)
        await msg.edit_text(await self.get_translation(message.from_user.id, "error"))

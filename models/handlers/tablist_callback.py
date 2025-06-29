from aiogram import types
from models.utils import api


async def handler_tablist_callback(self, message: types.Message, register_msg: bool = True) -> None:
    if register_msg:
        await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return

    msg_my = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))
    try:
        answer = await self.api_2b2t.get_printable_2b2t_info(message.from_user.id)
        await msg_my.edit_text(answer)
    finally:
        pass
    # except self.api_2b2t.Api2b2tError as e:
    #     self.logger.error(f"Api2b2tError: {e}")
    # #     await message.reply(await self.get_translation(message.from_user.id, "error"))
    # except Exception as e:
    #     self.logger.error(f"API Error: {type(e).__name__}: {e}")
    #     await message.reply(await self.get_translation(message.from_user.id, "userError"))

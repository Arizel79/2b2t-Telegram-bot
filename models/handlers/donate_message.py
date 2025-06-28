from aiogram import types
from aiogram.utils.markdown import html_decoration as hd


async def handler_donate_message(self, message: types.Message, register_msg=True) -> None:
    if register_msg:
        await self.on_msg(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return
    donate_text = await self.get_translation(message.from_user.id, "donateText")
    await message.reply(
        donate_text, disable_web_page_preview=True
    )

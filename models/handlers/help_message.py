from aiogram import types
from aiogram.utils.markdown import html_decoration as hd


async def handler_help_message(self, message: types.Message) -> None:
    await self.on_msg(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return
    await message.reply(
        await self.get_translation(
            message.from_user.id,
            "helpMessage",
            hd.quote(message.from_user.first_name)
        )
    )
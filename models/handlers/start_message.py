from aiogram import types
from aiogram.utils.markdown import html_decoration as hd


async def handler_start_message(self, message: types.Message, register_msg=True) -> None:
    if register_msg:
        await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return

    self.logger.info(f"Bot start command: {message.text}")
    cmd = message.text.split()[1]
    if cmd.startswith("pl_"):
        await self.handler_get_player_stats(message, register_msg=False)
        return

    await message.reply(
        await self.get_translation(
            message.from_user.id,
            "startMessage",
            hd.quote(message.from_user.first_name)
        ), reply_markup=await self.get_reply_kbd(message.from_user.id, message.chat.type)
    )

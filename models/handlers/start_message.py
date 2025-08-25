import asyncio
from aiogram import types
from aiogram.utils.markdown import html_decoration as hd

async def handler_start_message(self, message: types.Message, register_msg=True) -> None:
    if register_msg:
        await self.on_event(message)
    for i in range(500):
        if not await self.is_handler_msgs(message.from_user.id):
            self.logger.debug("Waiting before user selected lang...")
        else:
            break
        await asyncio.sleep(1)

    self.logger.info(f"Bot start command: {message.text}")
    try:
        cmd = message.text.split()[1]
    except IndexError:
        cmd = ""
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

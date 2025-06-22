from aiogram import types


async def handler_settings_message(self, message: types.Message, register_msg=True) -> None:
    if register_msg:
        await self.on_msg(message)
    await message.reply(await self.get_translation(message.from_user.id, "settingsMenuTitle"),
                        reply_markup=await self.get_settings_keyboard(message.from_user.id))

from aiogram import types


async def handler_command_set_language(self, message: types.Message) -> None:
    await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) != 2:
        await message.reply("Usage: /setlang en|ru")
        return

    new_lang = parts[-1]
    if new_lang not in ["en", "ru"]:
        await message.reply("Available languages: en, ru")
        return

    await self.db.update_lang(message.from_user.id, new_lang)
    await message.reply(f"Language changed to {new_lang}")

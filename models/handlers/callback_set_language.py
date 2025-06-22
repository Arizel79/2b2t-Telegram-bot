from aiogram.types import CallbackQuery
from aiogram.utils.markdown import html_decoration as hd
from aiogram.exceptions import TelegramForbiddenError


async def handler_callback_set_language(self, callback: CallbackQuery) -> None:
    try:
        if not callback.message.reply_to_message.from_user.id == callback.from_user.id:
            await callback.answer("Access denied!", show_alert=True)
            return

        print("callback.data: ", callback.data)
        lst = callback.data.split()
        if len(lst) != 3:
            await callback.answer("Invalid language selection", show_alert=True)

        lang = callback.data.split()[-1]
        user_id = int(callback.data.split()[1])

        if lang in ["en", "ru"]:
            await self.db.update_lang(callback.from_user.id, lang)
            await callback.message.edit_text(
                await self.get_translation(
                    callback.from_user.id,
                    "langSelected"
                ),
                reply_markup=None
            )
            # await callback.answer("Язык выбран")
            try:
                await self.bot.send_message(
                    callback.from_user.id,
                    await self.get_translation(
                        callback.from_user.id,
                        "startMessage",
                        hd.quote(callback.from_user.first_name)
                    )
                )
            except TelegramForbiddenError as e:
                print("TelegramForbiddenError", e, 'asda871h183eu1')
        else:
            await callback.answer("Invalid language selection", show_alert=True)
    except Exception as e:
        print(f"callback err asdaweasd: {type(e).__name__}: {e}")

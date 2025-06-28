from aiogram.types import CallbackQuery
from aiogram.utils.markdown import html_decoration as hd
from aiogram.exceptions import TelegramForbiddenError


async def handler_callback_set_language(self, callback: CallbackQuery) -> None:
    try:
        # Проверка доступа
        if not callback.message.reply_to_message.from_user.id == callback.from_user.id:
            await callback.answer("Access denied!", show_alert=True)
            return

        # Разбираем callback.data безопасно
        try:
            data_parts = callback.data.split()
            if len(data_parts) != 3:
                await callback.answer("Invalid language selection", show_alert=True)
                return

            _, user_id_str, lang = data_parts
            user_id = int(user_id_str)
        except (ValueError, IndexError, AttributeError) as e:
            print(f"Error parsing callback data: {e}")
            await callback.answer("Invalid request", show_alert=True)
            return

        # Проверяем допустимость языка
        if lang not in ["en", "ru"]:
            await callback.answer("Invalid language selection", show_alert=True)
            return

        # Обновляем язык
        try:
            await self.db.update_lang(user_id, lang)
            await callback.message.edit_text(
                await self.get_translation(user_id, "langSelected"),
                reply_markup=None
            )

            # Отправляем стартовое сообщение
            try:
                await self.bot.send_message(
                    user_id,
                    await self.get_translation(
                        user_id,
                        "startMessage",
                        hd.quote(callback.from_user.first_name)
                    )
                )
            except TelegramForbiddenError as e:
                print(f"Can't send message to user {user_id}: {e}")

        except ZeroDivisionError as db_error:
            print(f"Database error: {db_error}")
            await callback.answer("Error updating language", show_alert=True)

    except ZeroDivisionError as e:
        print(f"Unexpected error in language selection: {type(e).__name__}: {e}")
        await callback.answer("An error occurred", show_alert=True)
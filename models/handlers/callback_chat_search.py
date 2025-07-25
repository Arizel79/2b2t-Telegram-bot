from aiogram.types import CallbackQuery
from aiogram.utils.markdown import html_decoration as hd
from aiogram.exceptions import TelegramForbiddenError
from models.utils.config import *
import html

async def handler_chat_search_callback(self, callback: CallbackQuery) -> None:
    await self.on_event(callback)
    try:
        spl = callback.data.split()
        assert spl[0] == CALLBACK_CHAT_SEARCH
        if spl[1] == "none":
            await callback.answer(await self.get_translation(callback.from_user.id, "nothingHere"), show_alert=True)

        try:
            query_id = int(spl[1])
        except ValueError:
            return
        q_data = await self.db.get_saved_state(query_id)

        if q_data is None:
            await callback.message.edit_text("!!!\n\nСессия устарела. Повторите запрос")
            return

        if spl[2] == "goto":
            q_data["page"] = int(spl[3])

            if not q_data["user_id"] == callback.from_user.id:
                await callback.answer(await self.get_translation(callback.from_user.id, "accessDenied"), show_alert=True)
                return
            await self.db.update_saved_state(query_id, q_data)
            await callback.message.edit_text(f"{callback.message.html_text}\n\n{await self.get_translation(callback.from_user.id, 'waitPlease')}") # await self.get_translation(callback.message.from_user.id, "waitPlease")
            try:
                answer = await self.api_2b2t.get_printable_2b2t_chat_search_page(query_id)
                await callback.message.edit_text(answer, reply_markup=await self.get_markup_chat_search(query_id))
            except self.api_2b2t.Api2b2tError as e:
                self.logger.error(f"Api2b2tError: {e}")
                await callback.message.reply(await self.get_translation(callback.from_user.id, "error"))
            except Exception as e:
                self.logger.error(f"{type(e).__name__}: {e}")
                await callback.message.reply(await self.get_translation(callback.from_user.id,
                                                               "error") + f"\n\n<pre>{type(e).__name__}: {html.escape(str(e))}</pre>")

        elif spl[2] == "info":
            await callback.answer(f"Page: {q_data['page']} / {q_data['pages_count']}\nTotal: {q_data['total']}", show_alert=True)



    finally:
        pass
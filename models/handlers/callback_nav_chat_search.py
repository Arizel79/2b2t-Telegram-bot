from aiogram.types import CallbackQuery
from aiogram.utils.markdown import html_decoration as hd
from aiogram.exceptions import TelegramForbiddenError


async def handler_nav_chat_search(self, callback: CallbackQuery) -> None:
    print(f"dasdaw7123 callback nav cs: {callback.data}")

    try:
        spl = callback.data.split()
        assert spl[0] == "chat_search"
        try:
            query_id = int(spl[1])
        except ValueError:
            return
        q_data = self.api_2b2t.recent_querys.get(query_id, None)
        if q_data is None:
            await callback.message.edit_text("Сессия устарела. Повторите запрос")
            return

        if spl[2] == "goto":
            q_data["page"] = int(spl[3])

            if not q_data["user_id"] == callback.from_user.id:
                await callback.answer("Access denied!", show_alert=True)
                return

            await callback.message.edit_text(f"{callback.message.html_text}\n\nWait...") # await self.get_translation(callback.message.from_user.id, "waitPlease")
            try:
                answer = await self.api_2b2t.get_printable_2b2t_chat_search_page(query_id)
                await callback.message.edit_text(answer, reply_markup=await self.get_nav_chat_search(query_id))
            finally:
                pass


    finally:
        pass
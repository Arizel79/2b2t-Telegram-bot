from aiogram.types import CallbackQuery, Message, DateTime, Chat
from aiogram.utils.markdown import html_decoration as hd
from aiogram.exceptions import TelegramForbiddenError
from models.utils.config import *




async def handler_search_messages_from_player_callback(self, callback: CallbackQuery) -> None:
    await self.on_event(callback)


    try:
        spl = callback.data.split()
        assert spl[0] == CALLBACK_MESSAGES_FROM_PLAYER
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
                answer = await self.api_2b2t.get_printable_messages_from_player_in_2b2t_chat(query_id)
                await callback.message.edit_text(answer, reply_markup=await self.get_markup_search_messages_from_player(
                    query_id))
            except self.api_2b2t.Api2b2tError:
                await callback.message.edit_text(await self.get_translation(callback.from_user.id, "error"))

            finally:
                pass
        elif spl[2] == "info":
            await callback.answer(f"Page: {q_data['page']} / {q_data['pages_count']}\nTotal: {q_data['total']}", show_alert=True)

        elif spl[2] == CALLBAK_VIEW_PLAYER_STATS:
            if not q_data["user_id"] == callback.from_user.id:
                await callback.answer(await self.get_translation(callback.from_user.id, "accessDenied"),
                                      show_alert=True)
                return

            await callback.message.edit_text(
                f"{callback.message.html_text}\n\n{await self.get_translation(callback.from_user.id, 'waitPlease')}")
            if q_data["use_uuid"]:
                query = q_data["player_uuid"]
            else:
                query = q_data["player_username"]
            await self.get_player_stats_and_edit_message(callback.from_user.id, query, callback.message)

            # $$$######5
            # try:
            #     if not q_data["user_id"] == callback.from_user.id:
            #         await callback.answer(await self.get_translation(callback.from_user.id, "accessDenied"), show_alert=True)
            #         return
            #     await callback.message.edit_text(
            #         f"{callback.message.html_text}\n\n{await self.get_translation(callback.from_user.id, 'waitPlease')}")
            #     await callback.message.edit_text(await self.get_player_stats_answer(q_data.get("player_name", q_data.get("player_uuid", "invalid_ay6y1381")),callback.from_user.id),
            #                                      reply_markup=await self.get_player_stats_keyboard(callback.from_user.id, query_id))
            # except self.api_2b2t.Api2b2tError as e:
            #     self.logger.error(e)
            #     await callback.message.edit_text(await self.get_translation(callback.message.from_user.id, "userError"))
            #
            # except Exception as e:
            #     self.logger.error(e)
            #     await callback.message.edit_text(await self.get_translation(callback.message.from_user.id, "error"))
    except Exception as e:
        self.logger.error("Error in handler_search_messages_from_player_callback:")
        self.logger.exception(e)
        await callback.message.edit_text(str(await self.get_translation(callback.message.from_user.id, "unknownError")))
    finally:
        pass
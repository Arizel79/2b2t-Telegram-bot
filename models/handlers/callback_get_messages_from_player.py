from aiogram.types import CallbackQuery, Message, DateTime, Chat
from aiogram.utils.markdown import html_decoration as hd
from aiogram.exceptions import TelegramForbiddenError
from models.utils.config import *
import aiogram



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
            await self.edit_message_text_or_caption(callback.message, "!!!\n\nСессия устарела. Повторите запрос")
            return

        if spl[2] == "goto":
            q_data["page"] = int(spl[3])

            if not q_data["user_id"] == callback.from_user.id:
                await callback.answer(await self.get_translation(callback.from_user.id, "accessDenied"), show_alert=True)
                return
            await self.db.update_saved_state(query_id, q_data)
            if callback.message.text:
                await self.edit_message_text_or_caption(callback.message, f"{callback.message.html_text}\n\n{await self.get_translation(callback.from_user.id, 'waitPlease')}")
            try:
                answer = await self.api_2b2t.get_printable_messages_from_player_in_2b2t_chat(query_id)
                await self.edit_message_text_or_caption(callback.message, answer["text"], reply_markup=await self.get_markup_search_messages_from_player(
                    query_id))
            except self.api_2b2t.Api2b2tError:
                await self.edit_message_text_or_caption(callback.message, await self.get_translation(callback.from_user.id, "error"))
            except (aiogram.exceptions.TelegramBadRequest, aiogram.exceptions.TelegramBadRequest) as e:
                self.logger.error(f"Error in handler_search_messages_from_player_callback (goto): {e}")
                self.logger.exception(e)
            except Exception as e:
                raise
            finally:
                pass
        elif spl[2] == "info":
            await callback.answer(f"Page: {q_data['page']} / {q_data['pages_count']}\nTotal: {q_data['total']}", show_alert=True)

        elif spl[2] == CALLBAK_VIEW_PLAYER_STATS:
            if not q_data["user_id"] == callback.from_user.id:
                await callback.answer(await self.get_translation(callback.from_user.id, "accessDenied"),
                                      show_alert=True)
                return

            await self.edit_message_text_or_caption(callback.message,
                f"{callback.message.html_text}\n\n{await self.get_translation(callback.from_user.id, 'waitPlease')}")
            if q_data["use_uuid"]:
                query = q_data["player_uuid"]
            else:
                query = q_data["player_username"]
            await self.get_player_stats_and_edit_message(callback.from_user.id, query, callback.message)
    except aiogram.exceptions.TelegramBadRequest as e:
        self.logger.exception(e)

    except Exception as e:
        self.logger.error("Error in handler_search_messages_from_player_callback:")
        self.logger.exception(e)
        await self.edit_message_text_or_caption(callback.message, str(await self.get_translation(callback.message.from_user.id, "unknownError")))

    finally:
        pass
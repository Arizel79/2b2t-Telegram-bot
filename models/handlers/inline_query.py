import time

from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto, InputMediaPhoto
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
from models.utils.utils import *
from models.utils.config import *
import html


def get_random_id():
    return str(time.time())


async def handler_inline_query(self, inline_query):
    await self.on_event(inline_query)
    user_id = inline_query.from_user.id

    self.logger.debug(f"Inline query: {inline_query}")
    q = query = inline_query.query.rstrip()
    results = []
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=await self.get_translation(user_id, "inlineOpenBot"),
                url=f"https://t.me/{self.bot_username}?start=ref{user_id}&from_inline"
            ),

        ]
    ])

    # InlineKeyboardButton(
    #     text="🔍 Искать ещё",
    #     switch_inline_query_current_chat=""
    # )

    if query == "":
        # Если запрос пустой
        results.append(
            InlineQueryResultArticle(
                id=get_random_id(),
                title=await self.get_translation(user_id, "inlineEnterPlayerUsernameTitle"),
                input_message_content=InputTextMessageContent(
                    message_text="---"
                ),
                description=await self.get_translation(user_id, "inlineEnterPlayerUsernameSubtitle"),
                reply_markup=reply_markup
            )

        )

    if query == "":
        status_2b2t = await self.api_2b2t.get_2b2t_info()
        status_2b2t_to_send = await self.api_2b2t.get_printable_2b2t_info(user_id)
        img_url = URL_2B2T_LOGO_INLINE
        results.append(
            InlineQueryResultArticle(
                id=get_random_id(),
                title=await self.get_translation(user_id, "inlineGet2b2tInfoTitle"),
                thumbnail_url=img_url,
                input_message_content=InputTextMessageContent(
                    message_text=status_2b2t_to_send
                ),
                description=await self.get_translation(user_id, "inlineGet2b2tInfoSubtitle", status_2b2t["regular"]),
                reply_markup=reply_markup
            )
        )

    if query.rstrip() != "":
        try:
            if is_valid_minecraft_username(query):
                uuid = await self.api_2b2t.get_uuid_from_username(query)
                username = await self.api_2b2t.get_username_from_uuid(uuid)
            elif is_valid_minecraft_uuid(query):
                username = await self.api_2b2t.get_username_from_uuid(query)
            else:
                raise ValueError(f"Player {query} not found")
            username = query

            player_stats_to_send = await self.api_2b2t.get_printable_player_stats(user_id, username=username)
            try:
                player_stats = await self.api_2b2t.get_player_stats(username=username)
                print(player_stats)
                playtime = await self.api_2b2t.seconds_to_hms(player_stats["playtimeSeconds"], user_id=user_id)
                desc = await self.get_translation(user_id, "inlineGetPlayerStatsSubtitlePlayerWasOn2b2t", username,
                                                  playtime)


            except self.api_2b2t.PlayerNeverWasOn2b2tError:
                desc = await self.get_translation(user_id, "inlineGetPlayerStatsSubtitlePlayerNeverWasOn2b2t", username)
            urls = await self.api_2b2t.get_visage_urls(username)
            skin_url = urls["face"]
            results.append(
                InlineQueryResultArticle(
                    id=get_random_id(),
                    title=await self.get_translation(user_id, "inlineGetPlayerStatsTitle", username),
                    input_message_content=InputTextMessageContent(
                        message_text=player_stats_to_send["text"]
                    ),
                    description=desc,
                    thumbnail_url=skin_url,
                    reply_markup=reply_markup

                )
            )



        except ValueError as e:
            self.logger.info(f"inline: {e}")
        except (self.api_2b2t.PlayerNotFoundByUsername, self.api_2b2t.PlayerNotFoundByUUID):
            results.append(
                InlineQueryResultArticle(
                    id=get_random_id(),
                    title=f"Player not found!",
                    input_message_content=InputTextMessageContent(
                        message_text=f"Вы искали: {html.escape(query)}"
                    ),
                    description=f"Player {query} not found",
                    reply_markup=reply_markup
                )
            )
        except Exception as e:
            self.logger.error(f"Error in handler_inline_query: {e}")
            self.logger.exception(e)

    # Отправляем результаты
    await inline_query.answer(
        results,
        cache_time=1,
        is_personal=True
    )

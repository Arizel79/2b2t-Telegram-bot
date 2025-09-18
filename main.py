import logging

from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot
from aiogram import F
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineQuery
from aiogram.types import BufferedInputFile
import pytz
from datetime import datetime
from models.utils.orm import AsyncDatabaseSession
from models.utils.translations import *
from models.handlers.donate_message import *
from models.handlers.get_playtime_top import *
from models.handlers.get_kills_top_month import *
from models.handlers.callback_get_kills_top_month import *
from models.handlers.callback_chat_search import *
from models.handlers.callback_get_messages_from_player import *
from models.handlers.search_messages_from_player import *
from models.handlers.callback_tablist import *
from models.handlers.callback_get_playtime_top import *
from models.handlers.text import *
from models.handlers.inline_query import *
from models.handlers.tracking import *
from models.handlers.callback_tracking import *
from models.utils.live_events import *
from models.utils.tracking import *
from models.utils.keyboards import *

import os


class Stats2b2tBot:
    handler_start_message = handler_start_message
    handler_callback_settings = handler_callback_settings
    handler_command_set_language = handler_command_set_language
    handler_donate_message = handler_donate_message
    handler_callback_set_language = handler_callback_set_language
    handler_settings_message = handler_settings_message
    handler_search_chat = handler_search_chat
    handler_get_player_stats = handler_get_player_stats
    handler_get_2b2t_info = handler_get_2b2t_info
    handler_get_2b2t_tablist = handler_get_2b2t_tablist
    handler_text = handler_text
    handler_help_message = handler_help_message
    handler_chat_search_callback = handler_chat_search_callback
    handler_tablist_callback = handler_tablist_callback
    handler_search_messages_from_player = handler_search_messages_from_player
    handler_search_messages_from_player_callback = handler_search_messages_from_player_callback
    handler_get_playtime_top = handler_get_playtime_top
    handler_playtime_top_callback = handler_playtime_top_callback
    handler_get_kills_top_month = handler_get_kills_top_month
    handler_kills_top_month_callback = handler_kills_top_month_callback
    handler_inline_query = handler_inline_query
    handler_tracking_callback = handler_tracking_callback
    handler_tracking_command = handler_tracking_command
    show_tracking_management = show_tracking_management
    show_tracking_list = show_tracking_list
    handler_tracking_add_command = handler_tracking_add_command

    get_reply_kbd = get_reply_kbd
    get_reply_keyboard_by_message = get_reply_keyboard_by_message
    get_markup_chat_search = get_markup_chat_search
    get_markup_search_messages_from_player = get_markup_search_messages_from_player
    get_markup_tablist = get_markup_tablist
    get_nav_buttons = get_nav_buttons
    get_nav_markup = get_nav_markup
    get_markup_playtime_top = get_markup_playtime_top
    get_nav_markup = get_nav_markup
    get_markup_playtime_top = get_markup_playtime_top
    get_player_stats_keyboard = get_player_stats_keyboard
    get_lang_keyboard = get_lang_keyboard

    async def get_translation(self, *kwargs):
        return await self.translator.get_translation(*kwargs)

    def __init__(self, token: str):
        os.makedirs("logs", exist_ok=True)
        self.logger = setup_logger("bot", "logs/bot.log", logging.INFO)
        self.bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.bot_username = None
        self.dp = Dispatcher()
        self.db = AsyncDatabaseSession()
        self.translator = Translator("translations.json", self.db)

        self.live_events_handler = LiveEventsManager(self)
        self.tracking_manager = TrackingManager(self)

        self.api_2b2t = api_wrapper.Api2b2tWrapper(self)

        self.logger.info("Program started")

    async def initialize(self):
        self.bot_username = (await self.bot.get_me()).username
        await self.db.create_all()

        await self._register_handlers()

    async def is_handler_msgs(self, user_id):
        return await self.db.is_user_select_lang(user_id)

    async def is_user_banned(self, user_id):
        return False

    async def _register_handlers(self):

        self.dp.inline_query()(self.handler_inline_query)

        self.dp.message(Command("start"))(self.handler_start_message)
        self.dp.message(Command("settings"))(self.handler_settings_message)
        self.dp.message(Command("help", "h"))(self.handler_help_message)
        self.dp.message(Command("donate"))(self.handler_donate_message)
        self.dp.message(Command("messages", "m", "chat", "search", "s", "chat_search", "chats"))(
            self.handler_search_chat)

        self.dp.callback_query(F.data.startswith("settings"))(self.handler_callback_settings)
        self.dp.callback_query(F.data.startswith(CALLBACK_CHAT_SEARCH))(self.handler_chat_search_callback)
        self.dp.callback_query(F.data.startswith("tablist"))(self.handler_tablist_callback)
        self.dp.callback_query(F.data.startswith(CALLBACK_MESSAGES_FROM_PLAYER))(
            self.handler_search_messages_from_player_callback)
        self.dp.callback_query(F.data.startswith("setlang"))(self.handler_callback_set_language)
        self.dp.callback_query(F.data.startswith(CALLBACK_PLAYTIME_TOP))(self.handler_playtime_top_callback)
        self.dp.callback_query(F.data.startswith(CALLBACK_KILLS_TOP_MONTH))(self.handler_kills_top_month_callback)
        self.dp.callback_query(F.data.startswith("tracking"))(self.handler_tracking_callback)

        self.dp.message(Command("player", "pl", "p"))(self.handler_get_player_stats)
        self.dp.message(Command("i", "info", "stats", "stat", "status"))(self.handler_get_2b2t_info)
        self.dp.message(Command("tab", "pl_list", "tablist"))(self.handler_get_2b2t_tablist)
        self.dp.message(Command("from"))(self.handler_search_messages_from_player)
        self.dp.message(Command("track", "tracking", "t", ""))(self.handler_tracking_command)
        self.dp.message(Command("track_add", "tracking_add", "t_add"))(self.handler_tracking_add_command)

        self.dp.message(Command("pt_top", "playtime_top", "playtimetop", "pttop"))(self.handler_get_playtime_top)
        self.dp.message(Command("kills_top_month", "kills_top", "killstopmonth", "kstop"))(
            self.handler_get_kills_top_month)

        self.dp.message()(self.handler_text)
        # no handlers down!!!

    async def get_printable_user(self, from_user: types.User=None, from_chat: types.Chat = None, formatting=False,
                                 user_id=None) -> str:
        if user_id is not None:
            # Получаем пользователя из БД
            user_from_db = await self.db.get_user(user_id)

            if formatting:
                return (
                        f"{html.escape(user_from_db.name)}"
                        f" ({f'{user_from_db.username}, ' if user_from_db.username else ''}"
                        f"<a href=\"{'tg://user?id=' + str(user_from_db.id)}\">" + str(user_from_db.id) + "</a>)"
                )
            else:
                return (
                    f"{user_from_db.name}"
                    f" ({f'{user_from_db.username}, ' if user_from_db.username else ''}"
                    f"id: {user_from_db.id})"
                )
        else:
            # Используем переданные from_user и from_chat
            if formatting:
                return (
                        f"{html.escape(from_user.first_name)}"
                        f"{'' if not from_user.last_name else f' {html.escape(from_user.last_name)}'}"
                        f" ({f'@{from_user.username}, ' if from_user.username else ''}"
                        f"<a href=\"{'tg://user?id=' + str(from_user.id)}\">" + str(from_user.id) + "</a>"
                                                                                                    f"{(', chat: ' + '<code>' + str(from_chat.id) + '</code>') if from_chat is not None else ''})"
                )
            else:
                return (
                    f"{from_user.first_name}"
                    f"{'' if not from_user.last_name else f' {from_user.last_name}'}"
                    f" ({f'@{from_user.username}, ' if from_user.username else ''}"
                    f"id: {from_user.id}"
                    f"{(', chat: ' + str(from_chat.id)) if from_chat is not None else ''})"
                )

    async def get_printable_time(self, unix_time=None) -> str:
        # Указываем вашу временную зону
        timezone = pytz.timezone("Europe/Moscow")

        # Если передан объект datetime, преобразуем его в timestamp
        if isinstance(unix_time, datetime):
            unix_time = unix_time.timestamp()

        if unix_time:
            # Создаем объект времени из Unix-времени
            dt_utc = datetime.fromtimestamp(unix_time, tz=pytz.utc)
            # Конвертируем в нужную временную зону
            dt_local = dt_utc.astimezone(timezone)
        else:
            # Получаем текущее время в нужной временной зоне
            dt_local = datetime.now(timezone)

        return dt_local.strftime("%H:%M.%S %d.%m.%Y")

    async def write_msg(self, msg: str, unix_timestamp=None) -> None:
        with open("msgs.txt", "a+", encoding="utf-8") as f:
            text = f"[{await self.get_printable_time(unix_timestamp)}] {msg}"
            f.write(text + "\n")
            self.logger.info(text)



    async def get_player_stats_answer(self, query, user_id, register_query_id=False):
        page_size = SEARCH_FROM_PLAYER_PAGE_SIZE_IN_CAPTION
        if is_valid_minecraft_uuid(query):
            answer = await self.api_2b2t.get_printable_player_stats(user_id, uuid=query)
            query_id = None

            if register_query_id and answer["show_kbd"]:
                saved_state = {"type": "msgs from player", "player_uuid": query, "player_username": answer["username"],
                               "page": 1,
                               "user_id": user_id, "page_size": page_size,
                               "via_player_stats": True, "use_uuid": True}
                query_id = await self.db.add_saved_state(saved_state)
            return {"answer": answer['text'], "query_id": query_id, "show_kbd": answer['show_kbd'],
                    "player_username": answer.get("username"), "player_uuid": answer.get("uuid")}

        elif is_valid_minecraft_username(query):
            answer = await self.api_2b2t.get_printable_player_stats(user_id, username=query)
            self.logger.info(f"Ans: {answer}")
            query_id = None
            if register_query_id and answer["show_kbd"]:
                saved_state = {"type": "msgs from player", "player_uuid": answer["uuid"], "player_username": query,
                               "page": 1,
                               "user_id": user_id, "page_size": page_size,
                               "via_player_stats": True, "use_uuid": True}
                query_id = await self.db.add_saved_state(saved_state)
            return {"answer": answer['text'], "query_id": query_id, "show_kbd": answer['show_kbd'],
                    "player_username": answer.get("username"), "player_uuid": answer.get("uuid")}
        else:
            raise self.api_2b2t.Api2b2tError(f"{query} is not a valid username/uuid")



    async def send_message_to_logs_chat(self, message, *args, **kwargs):
        if SEND_LOGS:
            self.logger.info(f"Sending to admin: {message}, {args}, {kwargs}")
            await self.bot.send_message(LOGS_GROUP_ID,
                                        message, *args, **kwargs,
                                        message_thread_id=LOGS_GROUP_THREAD_ID)

    async def on_event(self, event) -> None:
        user_id = event.from_user.id
        await self.db.update_credentials(event)
        if not await self.db.is_user_select_lang(event.from_user.id):

            user_lang_code_tg = event.from_user.language_code
            if user_lang_code_tg in LANG_CODES:
                await self.db.update_lang(user_id, user_lang_code_tg)
            else:
                await self.db.update_lang(user_id, DEFAULT_LANG_CODE)

        if type(event) == types.Message:
            await self.write_msg(
                f"{await self.get_printable_user(event.from_user, from_chat=event.chat)}: {event.text}")

            if SEND_LOGS:
                await self.send_message_to_logs_chat(
                    f"{await self.get_printable_user(event.from_user, from_chat=event.chat, formatting=True)}:\n <code>{html.escape(event.text)}</code>")

            if not await self.db.check_user_found(user_id):
                await self.db.get_user(user_id)
                await self.write_msg(
                    f"{await self.get_printable_user(event.from_user, from_chat=event.chat)} new user!")

                await event.reply(
                    "Select language\nВыбери язык\n",
                    reply_markup=self.get_lang_keyboard(event.from_user.id)
                )

            await self.db.increment_requests(user_id)

        elif type(event) == CallbackQuery:
            user_id = event.from_user.id
            await self.write_msg(f"{await self.get_printable_user(event.from_user)} callback: {event.data}")
            if SEND_LOGS:
                await self.send_message_to_logs_chat(
                    f"{await self.get_printable_user(event.from_user, formatting=True)} callback:\n <code>{html.escape(event.data)}</code>")

        elif type(event) == InlineQuery:
            user_id = event.from_user.id
            await self.write_msg(f"{await self.get_printable_user(event.from_user)} inline query: {event.query}")
            if SEND_LOGS:
                await self.send_message_to_logs_chat(f"{await self.get_printable_user(event.from_user, formatting=True)} inline query:\n <code>{html.escape(event.query)}</code>")

    async def get_player_stats_and_edit_message(self, user_id, query, msg):
        chat_id = msg.chat.id
        try:
            answer_ = await self.get_player_stats_answer(query, user_id, register_query_id=True)

            if answer_["show_kbd"]:
                image_buffer = await self.api_2b2t.download_visage_image(answer_["player_username"], "face", scale=200)

                input_file = BufferedInputFile(
                    file=image_buffer.getvalue(),
                    filename="skin.png"
                )
                message_thread_id = msg.message_thread_id if msg.message_thread_id else None
                try:
                    await self.bot.send_photo(
                        chat_id=chat_id,
                        message_thread_id=msg.message_thread_id,
                        photo=input_file,
                        caption=answer_["answer"],
                        reply_markup=await self.get_player_stats_keyboard(user_id, answer_["query_id"])
                    )
                except aiogram.exceptions.TelegramBadRequest as e:
                    if "message thread not found" in str(e) or "TOPIC_CLOSED" in str(e):
                        # Отправляем в основную тему без указания message_thread_id
                        await self.bot.send_photo(
                            chat_id=chat_id,
                            photo=input_file,
                            caption=answer_["answer"],
                            reply_markup=await self.get_player_stats_keyboard(user_id, answer_["query_id"])
                        )
                    else:
                        raise
                # await self.bot.edit_text(answer_["answer"],
                #                     reply_markup=await self.get_player_stats_keyboard(user_id,
                #                                                                       answer_["query_id"]))
                await self.bot.delete_message(msg.chat.id, msg.message_id)
            else:
                await msg.edit_text(answer_["answer"])

        except self.api_2b2t.PlayerNeverWasOn2b2tError as e:
            self.logger.error(e)
            await msg.edit_text(await self.get_translation(user_id, "userError"))


        except self.api_2b2t.Api2b2tError as e:
            self.logger.error(e)
            await msg.edit_text(await self.get_translation(user_id, "userError"))

        except Exception as e:
            self.logger.error(f"Error in get_player_stats_and_edit_message: {e}")
            self.logger.exception(e)
            await msg.edit_text(await self.get_translation(msg.from_user.id, "error"))

    async def edit_message_text_or_caption(self, message, new_text, **kwargs):
        if message.text:
            await message.edit_text(new_text, **kwargs)
        elif message.caption:
            await message.edit_caption(caption=new_text, **kwargs)

    async def get_settings_keyboard(self, user_id):
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "menuEditLang"),
                                 callback_data=f"settings editlang"),
            InlineKeyboardButton(text=await self.get_translation(user_id, "menuHelp"), callback_data=f"settings help")
        )
        builder.adjust(1)
        return builder.as_markup()

    async def run_bot(self) -> None:
        await self.dp.start_polling(self.bot)

    async def run(self) -> None:
        bot_task = asyncio.create_task(self.run_bot())
        live_events_tasks = await self.live_events_handler.get_tasks()
        tasks = [bot_task, *live_events_tasks]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError as e:
            self.logger.info(f"CancelledError")
            self.logger.exception(e)


async def main():
    bot = Stats2b2tBot(TELEGRAM_BOT_TOKEN)
    await bot.initialize()

    try:
        await bot.run()
    finally:
        print("Bot finished")


if __name__ == '__main__':
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Завершение работы по Ctrl+C")

from email.message import Message

from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot
from aiogram import F
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import pytz
import html
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from models.utils.orm import AsyncDatabaseSession
from models.utils.translations import *
from models.handlers.help_message import *
from models.handlers.start_message import *
from models.handlers.donate_message import *
from models.handlers.callback_settings import *
from models.handlers.command_set_language import *
from models.handlers.callback_set_language import *
from models.handlers.settings import *
from models.handlers.search_chat import *
from models.handlers.get_player_stats import *
from models.handlers.get_2b2t_info import *
from models.handlers.get_2b2t_tablist import *
from models.handlers.get_playtime_top import *
from models.handlers.get_kills_top_month import *
from models.handlers.callback_get_kills_top_month import *
from models.handlers.callback_tablist import *
from models.handlers.callback_chat_search import *
from models.handlers.callback_get_messages_from_player import *
from models.handlers.search_messages_from_player import *
from models.handlers.callback_tablist import *
from models.handlers.callback_get_playtime_top import *
from models.handlers.text import *
from models.utils.live_events import *
from models.handlers.inline_query import handler_inline_query


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

    async def get_translation(self, *kwargs):
        return await self.translator.get_translation(*kwargs)

    def __init__(self, token: str):
        self.bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dp = Dispatcher()
        self.db = AsyncDatabaseSession()
        self.translator = Translator("translations.json", self.db)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.live_events = LiveEvents(LIVE_EVENTS, self)

        self.api_2b2t = api.Api2b2t(self)

        self.logger.info("Program started")

    async def initialize(self):
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

        self.dp.message(Command("player", "pl", "p"))(self.handler_get_player_stats)
        self.dp.message(Command("i", "info", "stats", "stat"))(self.handler_get_2b2t_info)
        self.dp.message(Command("tab", "t", "tablist"))(self.handler_get_2b2t_tablist)
        self.dp.message(Command("from"))(self.handler_search_messages_from_player)

        self.dp.message(Command("pt_top", "playtime_top", "playtimetop", "pttop"))(self.handler_get_playtime_top)
        self.dp.message(Command("kills_top_month", "kills_top", "killstopmonth", "kstop"))(
            self.handler_get_kills_top_month)

        self.dp.message()(self.handler_text)
        # no handlers down!!!

    async def get_printable_user(self, from_user: types.User, from_chat: types.Chat = None, formatting=False) -> str:
        if formatting:
            return (
                    f"{html.escape(from_user.first_name)}"
                    f"{'' if not from_user.last_name else f' {html.escape(from_user.last_name)}'}"
                    f" ({f'@{from_user.username}, ' if from_user.username else ''}"
                    f"<a href=\"{'tg://user?id=' + str(from_user.id)}\">" + str(from_user.id) + "</a>"
                                                                                                 f"{(', chat: ' + '<code>' + str(from_chat.id) + '</code>') if not from_chat is None else ''})"
            )
        else:
            return (
                f"{from_user.first_name}"
                f"{'' if not from_user.last_name else f' {from_user.last_name}'}"
                f" ({f'@{from_user.username}, ' if from_user.username else ''}"
                f"{f'id: {from_user.id}'}"
                f"{(', chat: ' + str(from_chat.id)) if not from_chat is None else ''})")


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

    async def get_reply_kbd(self, user_id, chat_type):
        if chat_type == ChatType.PRIVATE:
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text=await self.get_translation(user_id, "get2b2tinfo")),
                        KeyboardButton(text=await self.get_translation(user_id, "getPlayerStats"))
                    ],
                    [
                        KeyboardButton(text=await self.get_translation(user_id, "getSettings")),
                        KeyboardButton(text=await self.get_translation(user_id, "getTablist"))
                    ],
                    [
                        KeyboardButton(text=await self.get_translation(user_id, "getPlaytimeTop")),
                        KeyboardButton(text=await self.get_translation(user_id, "getKillsTopMonth"))

                    ],
                    [
                        KeyboardButton(text=await self.get_translation(user_id, "sendDonate")),
                        KeyboardButton(text=await self.get_translation(user_id, "getSettings"))

                    ]
                ],

                resize_keyboard=True,  # автоматическое изменение размера кнопок
                one_time_keyboard=False,  # скрыть клавиатуру после нажатия
                input_field_placeholder=""  # подсказка в поле ввода
            )
            return keyboard

    async def get_markup_chat_search(self, query_id, user_id=None):
        builder = InlineKeyboardBuilder()
        q_data = await self.db.get_saved_state(query_id)
        if q_data['page'] > 1:
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "startPage"),
                                     callback_data=f"{CALLBACK_CHAT_SEARCH} {query_id} goto 1"))
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "backPage"),
                                     callback_data=f"{CALLBACK_CHAT_SEARCH} {query_id} goto {q_data['page'] - 1}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_CHAT_SEARCH} none")
                )
        builder.add(
            InlineKeyboardButton(text=f"{q_data['page']} / {q_data['pages_count']}",
                                 callback_data=f"{CALLBACK_CHAT_SEARCH} {query_id} info"))
        if q_data['page'] < q_data["pages_count"]:

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "nextPage"),
                                     callback_data=f"{CALLBACK_CHAT_SEARCH} {query_id} goto {q_data['page'] + 1}")
            )

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "endPage"),
                                     callback_data=f"{CALLBACK_CHAT_SEARCH} {query_id} goto {q_data['pages_count']}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_CHAT_SEARCH} none")
                )
        builder.adjust(5)
        return builder.as_markup()

    async def get_markup_search_messages_from_player(self, query_id):
        builder = InlineKeyboardBuilder()
        q_data = await self.db.get_saved_state(query_id)

        if q_data['page'] > 1:
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "startPage"),
                                     callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} goto 1"))
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "backPage"),
                                     callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} goto {q_data['page'] - 1}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} none")
                )
        builder.add(
            InlineKeyboardButton(text=f"{q_data['page']} / {q_data['pages_count']}",
                                 callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} info"))
        if q_data['page'] < q_data["pages_count"]:

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "nextPage"),
                                     callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} goto {q_data['page'] + 1}")
            )

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "endPage"),
                                     callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} goto {q_data['pages_count']}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} none")
                )
        if q_data.get("via_player_stats", False):
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "menuBack"),
                                     callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} {CALLBAK_VIEW_PLAYER_STATS}")
            )
        builder.adjust(5)
        return builder.as_markup()

    async def get_markup_tablist(self, query_id):
        builder = InlineKeyboardBuilder()
        saved_state = await self.db.get_saved_state(query_id)
        assert saved_state["type"] == "tablist"
        user_id = str(saved_state["user_id"])
        current_page = int(saved_state["page"])
        page_size = int(saved_state["page_size"])
        pages_count = await self.api_2b2t.get_2b2t_tablist_pages_count(page_size)

        if current_page > 1:
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "startPage"),
                                     callback_data=f"{CALLBACK_TABLIST} {query_id} goto 1"))
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "backPage"),
                                     callback_data=f"{CALLBACK_TABLIST} {query_id} goto {current_page - 1}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_TABLIST} none")
                )
        builder.add(
            InlineKeyboardButton(text=f"{current_page} / {pages_count}",
                                 callback_data=f"{CALLBACK_TABLIST} {query_id} info"))
        if current_page < pages_count:

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "nextPage"),
                                     callback_data=f"{CALLBACK_TABLIST} {query_id} goto {current_page + 1}")
            )

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "endPage"),
                                     callback_data=f"{CALLBACK_TABLIST} {query_id} goto {pages_count}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_TABLIST} none")
                )
        builder.adjust(5)
        return builder.as_markup()

    async def get_nav_markup(self, query_id):
        builder = InlineKeyboardBuilder()
        saved_state = await self.db.get_saved_state(query_id)
        user_id = str(saved_state["user_id"])
        current_page = int(saved_state["page"])
        page_size = int(saved_state["page_size"])

        if saved_state["type"] == "tablist":
            callback_ = CALLBACK_TABLIST
            pages_count = await self.api_2b2t.get_2b2t_tablist_pages_count(page_size)
        elif saved_state["type"] == "playtime_top":
            callback_ = CALLBACK_PLAYTIME_TOP
            pages_count = await self.api_2b2t.get_playtime_top_pages_count(page_size)

        elif saved_state["type"] == "kills_top_month":
            callback_ = CALLBACK_KILLS_TOP_MONTH
            pages_count = await self.api_2b2t.get_kills_top_month_pages_count(page_size)
        else:
            assert False, f"Unknown saved state type: {saved_state['type']}"

        if current_page > 1:
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "startPage"),
                                     callback_data=f"{callback_} {query_id} goto 1"))
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "backPage"),
                                     callback_data=f"{callback_} {query_id} goto {current_page - 1}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{callback_} none")
                )
        builder.add(
            InlineKeyboardButton(text=f"{current_page} / {pages_count}",
                                 callback_data=f"{callback_} {query_id} info"))
        if current_page < pages_count:

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "nextPage"),
                                     callback_data=f"{callback_} {query_id} goto {current_page + 1}")
            )

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "endPage"),
                                     callback_data=f"{callback_} {query_id} goto {pages_count}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{callback_} none")
                )
        builder.adjust(5)
        return builder.as_markup()

    async def get_markup_playtime_top(self, query_id):
        builder = InlineKeyboardBuilder()
        saved_state = await self.db.get_saved_state(query_id)
        assert saved_state["type"] == "playtime_top"
        user_id = str(saved_state["user_id"])
        current_page = int(saved_state["page"])
        page_size = int(saved_state["page_size"])
        pages_count = await self.api_2b2t.get_2b2t_tablist_pages_count(page_size)

        if current_page > 1:
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "startPage"),
                                     callback_data=f"{CALLBACK_PLAYTIME_TOP} {query_id} goto 1"))
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "backPage"),
                                     callback_data=f"{CALLBACK_PLAYTIME_TOP} {query_id} goto {current_page - 1}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_PLAYTIME_TOP} none")
                )
        builder.add(
            InlineKeyboardButton(text=f"{current_page} / {pages_count}",
                                 callback_data=f"{CALLBACK_PLAYTIME_TOP} {query_id} info"))
        if current_page < pages_count:

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "nextPage"),
                                     callback_data=f"{CALLBACK_PLAYTIME_TOP} {query_id} goto {current_page + 1}")
            )

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "endPage"),
                                     callback_data=f"{CALLBACK_TABLIST} {query_id} goto {pages_count}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_TABLIST} none")
                )
        builder.adjust(5)
        return builder.as_markup()

    async def get_player_stats_answer(self, query, user_id, register_query_id=False):
        if is_valid_minecraft_uuid(query):
            answer = await self.api_2b2t.get_printable_player_stats(user_id, uuid=query)
            query_id = None
            if register_query_id and answer["show_kbd"]:
                saved_state = {"type": "msgs from player", "player_uuid": query, "player_username": answer["username"],
                               "page": 1,
                               "user_id": user_id, "page_size": SEARCH_FROM_PLAYER_PAGE_SIZE,
                               "via_player_stats": True, "use_uuid": True}
                query_id = await self.db.add_saved_state(saved_state)
            return {"answer": answer['text'], "query_id": query_id, "show_kbd": answer['show_kbd']}


        elif is_valid_minecraft_username(query):
            answer = await self.api_2b2t.get_printable_player_stats(user_id, username=query)
            query_id = None
            if register_query_id and answer["show_kbd"]:
                saved_state = {"type": "msgs from player", "player_uuid": answer["uuid"], "player_username": query,
                               "page": 1,
                               "user_id": user_id, "page_size": SEARCH_FROM_PLAYER_PAGE_SIZE,
                               "via_player_stats": True, "use_uuid": True}
                query_id = await self.db.add_saved_state(saved_state)
            return {"answer": answer['text'], "query_id": query_id, "show_kbd": answer['show_kbd']}
        else:
            raise self.api_2b2t.Api2b2tError(f"{query} is not a valid username/uuid")

    async def get_player_stats_keyboard(self, user_id, query_id):
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "getPlayerChatMessagesViaPlayerStats"),
                                 callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} goto 1"))
        return builder.as_markup()

    def get_lang_keyboard(self, user_id):
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="🇬🇧 English", callback_data=f"setlang {user_id} en"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data=f"setlang {user_id} ru")
        )
        builder.adjust(2)
        return builder.as_markup()

    async def on_event(self, event) -> None:
        user_id = event.from_user.id
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
                await self.bot.send_message(LOGS_GROUP_ID,
                                            f"{await self.get_printable_user(event.from_user, from_chat=event.chat, formatting=True)}:\n <code>{html.escape(event.text)}</code>",
                                            message_thread_id=LOGS_GROUP_THREAD_ID)

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
                await self.bot.send_message(LOGS_GROUP_ID,
                                            f"{await self.get_printable_user(event.from_user, formatting=True)} callback:\n <code>{html.escape(event.data)}</code>",
                                            message_thread_id=LOGS_GROUP_THREAD_ID)

    async def get_player_stats_and_edit_message(self, user_id, query, msg):
        try:
            answer_ = await self.get_player_stats_answer(query, user_id, register_query_id=True)

            if answer_["show_kbd"]:
                await msg.edit_text(answer_["answer"],
                                    reply_markup=await self.get_player_stats_keyboard(user_id,
                                                                                      answer_["query_id"]))
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

    async def get_settings_keyboard(self, user_id):
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "menuEditLang"),
                                 callback_data=f"settings editlang"),
            InlineKeyboardButton(text=await self.get_translation(user_id, "menuHelp"), callback_data=f"settings help")
        )
        builder.adjust(1)
        return builder.as_markup()

    def is_command(self, text):
        if text.startswith("/"):
            return True
        return False

    async def run(self) -> None:
        await self.dp.start_polling(self.bot)


async def main():
    bot = Stats2b2tBot(TELEGRAM_BOT_TOKEN)
    await bot.initialize()

    bot_task = asyncio.create_task(bot.run())
    tasks = [bot_task]
    tasks += bot.live_events.tasks

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass  # Ожидаемое завершение

    finally:
        print("Bot finished")


if __name__ == '__main__':
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Завершение работы по Ctrl+C")

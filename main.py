from email.message import Message

from aiogram import Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram import Bot
from aiogram import F
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import html
import time
import requests

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
from models.handlers.tablist_callback import *
from models.handlers.chat_search_callback import *
from models.handlers.text import *



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

        self.dp.message(Command("start"))(self.handler_start_message)
        self.dp.message(Command("settings"))(self.handler_settings_message)
        self.dp.message(Command("help", "h"))(self.handler_help_message)
        self.dp.message(Command("donate"))(self.handler_donate_message)
        self.dp.message(Command("messages", "m", "chat", "search", "s", "chat_search", "chats"))(self.handler_search_chat)
        self.dp.callback_query(F.data.startswith("settings"))(self.handler_callback_settings)
        self.dp.callback_query(F.data.startswith("chat_search"))(self.handler_chat_search_callback)
        self.dp.callback_query(F.data.startswith("tablist"))(self.handler_tablist_callback)
        self.dp.message(Command("player", "pl", "p"))(self.handler_get_player_stats)
        self.dp.message(Command("i", "info", "stats", "stat"))(self.handler_get_2b2t_info)
        self.dp.message(Command("tab", "t", "tablist"))(self.handler_get_2b2t_tablist)
        self.dp.message()(self.handler_text)
        self.dp.callback_query(F.data.startswith("setlang"))(self.handler_callback_set_language)

    async def get_printable_user(self, from_user: types.User, from_chat: types.Chat = None, formatting=False) -> str:
        if formatting:
            return (
                    f"{html.escape(from_user.first_name)}"
                    f"{'' if not from_user.last_name else f' {html.escape(from_user.last_name)}'}"
                    f" ({f'@{from_user.username}, ' if from_user.username else ''}"
                    f"<a href=\"{'tg://user?id=' + str(from_user.id)})\">" + str(from_user.id) + "</a>"
                                                                                                 f"{(', chat: ' + '<code>' + str(from_chat.id) + '</code>') if not from_chat is None else ''})"
            )
        else:
            return (
                f"{from_user.first_name}"
                f"{'' if not from_user.last_name else f' {from_user.last_name}'}"
                f" ({f'@{from_user.username}, ' if from_user.username else ''}"
                f"{'tg://user?id=' + str(from_user.id)}"
                f"{(', chat_id: ' + str(from_chat.id)) if not from_chat is None else ''})")

    async def get_printable_time(self) -> str:
        return time.strftime("%H:%M.%S %d.%m.%Y", time.localtime())

    async def write_msg(self, msg: str) -> None:
        with open("msgs.txt", "a+", encoding="utf-8") as f:
            text = f"[{await self.get_printable_time()}] {msg}\n"
            f.write(text)
            print(text, end="")

    async def get_reply_kbd(self, user_id, chat_type):
        if chat_type == ChatType.PRIVATE:
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text=await self.get_translation(user_id, "get2b2tinfo")),
                        KeyboardButton(text=await self.get_translation(user_id, "getPlayerStats"))
                    ],
                    [
                        KeyboardButton(text=await self.get_translation(user_id, "searchChat")),
                        KeyboardButton(text=await self.get_translation(user_id, "getSettings"))
                    ],
                    [
                        KeyboardButton(text=await self.get_translation(user_id, "sendDonate"))

                    ]
                ],

                resize_keyboard=True,  # автоматическое изменение размера кнопок
                one_time_keyboard=False,  # скрыть клавиатуру после нажатия
                input_field_placeholder="Выберите действие..."  # подсказка в поле ввода
            )
            return keyboard
    async def get_nav_chat_search(self, query_id, user_id=None):
        builder = InlineKeyboardBuilder()
        q_data = await self.db.get_saved_state(query_id)
        if q_data['page'] > 1:
            builder.add(
                InlineKeyboardButton(text="back page",
                                     callback_data=f"chat_search {query_id} goto {q_data['page'] - 1}"))
        else:
             builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"chat_search none"))
        builder.add(
            InlineKeyboardButton(text=f"{q_data['page']} / {q_data['pages_count']}",
                                 callback_data=f"chat_search {query_id} info"))
        if q_data['page'] < q_data["pages_count"]:
            builder.add(
                InlineKeyboardButton(text="next page",
                                     callback_data=f"chat_search {query_id} goto {q_data['page'] + 1}")
            )
        else:
            builder.add(
                InlineKeyboardButton(text=" ",
                                     callback_data=f"chat_search none")
            )
        builder.adjust(3)
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
        if type(event) == types.Message:
            user_id = event.from_user.id
            await self.write_msg(f"{await self.get_printable_user(event.from_user, from_chat=event.chat)}: {event.text}")

            if SEND_LOGS:
                await self.bot.send_message(LOGS_GROUP_ID,
                                            f"{await self.get_printable_user(event.from_user, from_chat=event.chat, formatting=True)}:\n <code>{html.escape(event.text)}</code>",
                                            message_thread_id=LOGS_GROUP_THREAD_ID)


            if not await self.db.check_user_found(user_id):
                await self.db.get_user(user_id)
                await self.write_msg(f"{await self.get_printable_user(event.from_user, from_chat=event.chat)} new user!")

            if not await self.db.is_user_select_lang(event.from_user.id):
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
    await bot.run()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())

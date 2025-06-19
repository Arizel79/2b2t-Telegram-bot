import json
import logging
import time
import html
from config import *
from aiogram.enums import ChatType
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import html_decoration as hd
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramForbiddenError
import json

from pyexpat.errors import messages
from sqlalchemy.util import await_only

import api
from orm import AsyncDatabaseSession
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.WARN)

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", ""))
LOGS_GROUP_ID = int(os.getenv("LOGS_GROUP_ID", ""))
LOGS_GROUP_THREAD_ID = int(os.getenv("LOGS_GROUP_THREAD_ID", "0"))

assert TELEGRAM_BOT_TOKEN != "", "TELEGRAM_BOT_TOKEN is invalid"


class Stats2b2tBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dp = Dispatcher()
        self.ses = AsyncDatabaseSession()
        self.load_translations()

    async def initialize(self):
        """Инициализация базы данных перед запуском бота"""
        await self.ses.create_all()  # Создаем таблицы если их нет
        await self._register_handlers()

    def load_translations(self):
        with open("translations.json", "r", encoding="utf-8") as f:
            self.translations = json.loads(f.read())

    async def is_handler_msgs(self, user_id):
        return await self.ses.is_user_select_lang(user_id)

    async def is_user_banned(self, user_id):
        return False

    async def _register_handlers(self):

        self.dp.message(Command("start"))(self.handler_start)
        self.dp.message(Command("settings"))(self.handler_settings)
        self.dp.message(Command("help"))(self.handler_help)
        self.dp.message(Command("messages", "m", "chat", "search", "s", "chat_search"))(self.handler_search_chat)
        self.dp.callback_query(F.data.startswith("setlang"))(self.handler_callback_set_lang)
        self.dp.callback_query(F.data.startswith("settings"))(self.handler_callback_settings)
        # self.dp.message(Command("s"))(self.handler_callback_set_lang)
        self.dp.message(Command("player", "pl", "p"))(self.handler_player_stats)
        self.dp.message(Command("i", "info", "stats", "stat"))(self.handler_2b2t_info)
        self.dp.message(F.text.lower() == "Состояние 2b2t")(self.handler_2b2t_info)
        self.dp.message(Command("tab", "t", "tablist"))(self.handler_2b2t_tablist)
        self.dp.message()(self.handler_text)

        self.dp.callback_query(F.data.startswith("setlang"))(self.handler_set_lang)

    async def get_printable_user(self, from_user: types.User, from_chat: types.Chat=None, formatting=False) -> str:
        if formatting:
            return (
            f"{html.escape(from_user.first_name)}"
            f"{'' if not from_user.last_name else f' {html.escape(from_user.last_name)}'}"
            f" ({f'@{from_user.username}, ' if from_user.username else ''}"
            f"<a href=\"{'tg://user?id='+str(from_user.id)})\">"+ str(from_user.id)+ "</a>"
            f"{(', chat: ' + '<code>' +str(from_chat.id) + '</code>') if not from_chat is None else ''})"

        )
        else:
            return (
            f"{from_user.first_name}"
            f"{'' if not from_user.last_name else f' {from_user.last_name}'}"
            f" ({f'@{from_user.username}, ' if from_user.username else ''}"
            f"{'tg://user?id='+str(from_user.id)}"
            f"{(', chat_id: ' +str(from_chat.id)) if not from_chat is None else ''})")

    async def get_printable_time(self) -> str:
        return time.strftime("%H:%M.%S %d.%m.%Y", time.localtime())

    async def write_msg(self, msg: str) -> None:
        with open("msgs.txt", "a+", encoding="utf-8") as f:
            text = f"[{await self.get_printable_time()}] {msg}\n"
            f.write(text)
            print(text, end="")

    async def get_translation(self, user_id: int, what: str, *format_args) -> str:
        data = await self.ses.get_user_stats(user_id)
        lang = data["lang"]
        try:
            return self.translations[lang][what].format(*format_args)
        except KeyError:
            error = f"!!! KeyError(translation NOT FOUND) lang={lang}, what={what} !!!"
            print(error)
            return error
        except IndexError:
            error = f"!!! IndexError(translation format_args not correct N) lang={lang}, what={what}, format_args={format_args} !!!"
            print(error)
            return error

    async def get_reply_kbd(self, user_id, chat_type):
        if chat_type  == ChatType.PRIVATE:
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text=await self.get_translation(user_id, "get2b2tinfo")),
                        KeyboardButton(text=await self.get_translation(user_id, "getPlayerStats"))
                    ],
                    [
                        KeyboardButton(text=await self.get_translation(user_id, "searchChat")),
                        KeyboardButton(text=await self.get_translation(user_id, "getSettings"))
                    ]
                ],

                resize_keyboard=True,  # автоматическое изменение размера кнопок
                one_time_keyboard=False,  # скрыть клавиатуру после нажатия
                input_field_placeholder="Выберите действие..."  # подсказка в поле ввода
            )
            return keyboard

    def get_lang_keyboard(self, user_id):
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="🇬🇧 English", callback_data=f"setlang {user_id} en"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data=f"setlang {user_id} ru")
        )
        builder.adjust(2)
        return builder.as_markup()

    async def on_msg(self, msg: types.Message) -> None:
        await self.write_msg(f"{await self.get_printable_user(msg.from_user, from_chat=msg.chat)}: {msg.text}")
        await self.bot.send_message(LOGS_GROUP_ID,
                                f"{await self.get_printable_user(msg.from_user, from_chat=msg.chat, formatting=True)}:\n <code>{html.escape(msg.text)}</code>",
                                    message_thread_id=LOGS_GROUP_THREAD_ID)
        user_id = msg.from_user.id
        if not await self.ses.check_user_found(user_id):
            await self.ses.get_user(user_id)
            await self.write_msg(f"{await self.get_printable_user(msg.from_user, from_chat=msg.chat)} new user!")

        if not await self.ses.is_user_select_lang(msg.from_user.id):
            await msg.reply(
                "Select language\nВыбери язык\n",
                reply_markup=self.get_lang_keyboard(msg.from_user.id)
            )

        await self.ses.increment_requests(user_id)

    async def handler_start(self, message: types.Message, register_msg=True) -> None:
        if register_msg:
            await self.on_msg(message)
        if not await self.is_handler_msgs(message.from_user.id):
            return

        await message.reply(
            await self.get_translation(
                message.from_user.id,
                "startMessage",
                hd.quote(message.from_user.first_name)
            ), reply_markup=await self.get_reply_kbd(message.from_user.id, message.chat.type)
        )

    async def handler_help(self, message: types.Message) -> None:
        await self.on_msg(message)
        if not await self.is_handler_msgs(message.from_user.id):
            return
        await message.reply(
            await self.get_translation(
                message.from_user.id,
                "helpMessage",
                hd.quote(message.from_user.first_name)
            )
        )

    async def get_settings_keyboard(self, user_id):
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "menuEditLang"),
                                 callback_data=f"settings editlang"),
            InlineKeyboardButton(text=await self.get_translation(user_id, "menuHelp"), callback_data=f"settings help")
        )
        builder.adjust(1)
        return builder.as_markup()

    async def handler_callback_settings(self, callback: CallbackQuery):
        user_id = callback.from_user.id
        assert callback.data.startswith("settings")
        lst = callback.data.split()
        if len(lst) == 2:
            if lst[1] == "editlang":
                builder = InlineKeyboardBuilder()
                builder.add(
                    InlineKeyboardButton(text=self.translations["ru"]["langName"],
                                         callback_data=f"settings editlang ru"),
                    InlineKeyboardButton(text=self.translations["en"]["langName"],
                                         callback_data=f"settings editlang en"),
                    InlineKeyboardButton(text=await self.get_translation(user_id, "menuBack"),
                                         callback_data=f"settings mainmenu")
                )
                builder.adjust(1)
                await callback.message.edit_text(await self.get_translation(user_id, "settingsEditLang"),
                                                 reply_markup=builder.as_markup())
            elif lst[1] == "mainmenu":
                await callback.message.edit_text(await self.get_translation(user_id, "settingsMenuTitle"),
                                                 reply_markup=await self.get_settings_keyboard(user_id))
            elif lst[1] == "help":
                builder = InlineKeyboardBuilder()
                builder.add(
                    InlineKeyboardButton(text=await self.get_translation(user_id, "menuBack"),
                                         callback_data=f"settings mainmenu")
                )
                builder.adjust(1)
                await callback.message.edit_text(await self.get_translation(user_id, "helpMessage"),
                                                 reply_markup=builder.as_markup())
        elif len(lst) == 3:
            if lst[1] == "editlang":
                lang = lst[2]
                if lang not in ["en", "ru"]:
                    lang = "en"
                await self.ses.update_lang(user_id, lang)

                builder = InlineKeyboardBuilder()
                builder.add(
                    InlineKeyboardButton(text=await self.get_translation(user_id, "menuBack"),
                                         callback_data=f"settings mainmenu")
                )
                builder.adjust(1)

                await callback.message.edit_text(await self.get_translation(user_id, "settingsLangEdited",
                                                                            await self.get_translation(
                                                                                user_id, "langName")),
                                                 reply_markup=builder.as_markup())


                await self.bot.send_message(user_id, await self.get_translation(user_id, "startMessage",
                                                                                callback.from_user.first_name),
                                            reply_markup=await self.get_reply_kbd(user_id, callback.chat.type))

    async def handler_callback_set_lang(self, callback: CallbackQuery) -> None:
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
                await self.ses.update_lang(callback.from_user.id, lang)
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

    async def handler_set_lang(self, message: types.Message) -> None:
        await self.on_msg(message)
        if not await self.is_handler_msgs(message.from_user.id):
            return
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("Usage: /setlang en|ru")
            return

        new_lang = parts[-1]
        if new_lang not in ["en", "ru"]:
            await message.reply("Available languages: en, ru")
            return

        await self.ses.update_lang(message.from_user.id, new_lang)
        await message.reply(f"Language changed to {new_lang}")

    async def handler_settings(self, message: types.Message, register_msg=True) -> None:
        if register_msg:
            await self.on_msg(message)
        await message.reply(await self.get_translation(message.from_user.id, "settingsMenuTitle"),
                            reply_markup=await self.get_settings_keyboard(message.from_user.id))

    async def handler_player_stats(self, message: types.Message, register_msg: bool = True) -> None:
        if register_msg:
            await self.on_msg(message)
        if not await self.is_handler_msgs(message.from_user.id):
            return

        lang = (await self.ses.get_user_stats(message.from_user.id))["lang"]
        try:
            query = message.text.split(maxsplit=1)[1] if message.text.startswith("/") else message.text
        except IndexError as e:
            user_configs = (await self.ses.get_user_stats(message.from_user.id))["configs"]

            user_configs["mode"] = "player_stats"
            await self.ses.update_configs(message.from_user.id, json.dumps(user_configs))
            if message.chat.type == ChatType.PRIVATE:
                await message.reply(await self.get_translation(message.from_user.id, "enterPlayer"))
            else:
                await message.reply(await self.get_translation(message.from_user.id, "enterPlayerInCommand"))
            return
        if not query:
            user_configs = (await self.ses.get_user_stats(message.from_user.id))["configs"]

            user_configs["mode"] = "player_stats"
            await self.ses.update_configs(message.from_user.id, json.dumps(user_configs))

        if len(query.split()) > 1:
            await message.reply(await self.get_translation(message.from_user.id, "userError"))
            return

        msg = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))

        try:
            if "-" in query:
                answer = await self.get_player_stats(message.from_user.id, uuid=query)
            else:
                answer = await self.get_player_stats(message.from_user.id, player=query)

            await msg.edit_text(answer)
        except api.Api2b2tError as e:
            logging.error(f"Api2b2tError: {e}")
            await message.reply(await self.get_translation(message.from_user.id, "userError"))
        except Exception as e:
            logging.error(f"API Error: {type(e).__name__}: {e}")
            await message.reply(await self.get_translation(message.from_user.id, "error"))

    async def search_2b2t_chat(self, user_id, args):
        return "ПОИСК ВЫПОЛНЕН 0"
    def is_command(self, text):
        if text.startswith("/"):
            return True
        return False
    async def handler_2b2t_info(self, message: types.Message, register_msg: bool = True) -> None:
        if register_msg:
            await self.on_msg(message)
        if not await self.is_handler_msgs(message.from_user.id):
            return

        msg_my = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))
        try:
            answer = await self.get_2b2t_info(message.from_user.id)
            await msg_my.edit_text(answer)
        except api.Api2b2tError as e:
            logging.error(f"Api2b2tError: {e}")
            await message.reply(await self.get_translation(message.from_user.id, "error"))
        except Exception as e:
            logging.error(f"API Error: {type(e).__name__}: {e}")
            await message.reply(await self.get_translation(message.from_user.id, "userError"))

    async def handler_search_chat(self, message: types.Message, register_msg: bool = True) -> None:
        print(983)
        user_id = message.from_user.id
        if register_msg:
            await self.on_msg(message)
        if not await self.is_handler_msgs(message.from_user.id):
            return

        if self.is_command(message.text):
            lst = message.text.split()
            if len(lst) > 1:
                query = lst[1:]
                print("q: ", query)
        else:
            query = message.text


        user_configs = (await self.ses.get_user_stats(message.from_user.id))["configs"]
        # user_configs["mode"] = CHAT_SERACH_MODE
        await self.ses.update_configs(message.from_user.id, json.dumps(user_configs))
        await message.reply("функция пока не работает")
        # await message.reply(await self.get_translation(user_id, "enterChatSearchQuery"))
        return

        msg_my = await message.reply(await self.get_translation(message.from_user.id, "waitPlease"))
        try:
            answer = await self.search_2b2t_chat(message.from_user.id, query)
            await msg_my.edit_text(answer)
        except api.Api2b2tError as e:
            logging.error(f"Api2b2tError: {e}")
            await message.reply(await self.get_translation(message.from_user.id, "error"))
        except Exception as e:
            logging.error(f"API Error: {type(e).__name__}: {e}")
            await message.reply(await self.get_translation(message.from_user.id, "userError"))

    async def handler_2b2t_tablist(self, message: types.Message, register_msg: bool = True) -> None:
        if register_msg:
            await self.on_msg(message)
        if not await self.is_handler_msgs(message.from_user.id):
            return

        try:
            data = api.get_2b2t_tablist()
            answer = (
                '<b>Tablist of 2b2t</b>\n'
                f'<pre language="motd">{hd.quote(data["header"])}</pre>\n'
                '---\n'
            )

            await message.reply(answer)

        except api.Api2b2tError as e:
            logging.error(f"Api2b2tError: {e}")
            await message.reply(await self.get_translation(message.from_user.id, "userError"))
        except Exception as e:
            logging.error(f"API Error: {type(e).__name__}: {e}")
            await message.reply(await self.get_translation(message.from_user.id, "error"))

    async def handler_text(self, message: types.Message) -> None:
        await self.on_msg(message)
        if not await self.is_handler_msgs(message.from_user.id):
            return
        if message.chat.type == ChatType.PRIVATE:
            user_configs = (await self.ses.get_user_stats(message.from_user.id))["configs"]
            config_mode = None

            if message.text == await self.get_translation(message.from_user.id, "get2b2tinfo"):
                await self.handler_2b2t_info(message, register_msg=False)
                return
            elif message.text == await self.get_translation(message.from_user.id, "getPlayerStats"):
                config_mode = "player_stats"
                await message.reply(await self.get_translation(message.from_user.id, "enterPlayer"))

            elif message.text == await self.get_translation(message.from_user.id, "getSettings"):
                await self.handler_settings(message, register_msg=False)
                return

            elif message.text == await self.get_translation(message.from_user.id, "searchChat"):
                await message.reply(await self.get_translation(message.from_user.id, "enterChatSearchQuery"))
                config_mode = CHAT_SERACH_MODE

            elif user_configs.get("mode", None) == "player_stats":
                await self.handler_player_stats(message, register_msg=False)
                return

            elif user_configs.get("mode", None) == CHAT_SERACH_MODE:
                await self.handler_search_chat(message, register_msg=False)
                return

            else:
                await self.handler_start(message, register_msg=False)

            if not config_mode is None:
                user_configs["mode"] = config_mode
                await self.ses.update_configs(message.from_user.id, json.dumps(user_configs))

    async def run(self) -> None:
        await self.dp.start_polling(self.bot)

    async def get_2b2t_info(self, user_id):
        data = api.get_2b2t_info()
        return await self.get_translation(user_id, "2b2tInfo", data["online"], data["regular"], data["prio"])

    async def get_player_stats(self, user_id, player=None, uuid=None):
        is_player_online = False
        tablist = api.get_2b2t_tablist()

        if player is not None:
            is_player_online = any(p["playerName"] == player for p in tablist["players"])
        elif uuid is not None:
            is_player_online = any(p["uuid"] == uuid for p in tablist["players"])

        data = api.get_player_stats(player, uuid)
        online = ("\n" + await self.get_translation(user_id, 'isPlayerOnline')) if is_player_online else ''

        if not data.get("firstSeen", False):
            return await self.get_translation(user_id, "playerWasNotOn2b2t", player, player)
        text = await self.get_translation(user_id, "playerStats",
                                          player, online, api.format_iso_time(data['firstSeen']),
                                          api.format_iso_time(data['lastSeen']), data['chatsCount'], data['deathCount'],
                                          data['killCount'],
                                          data['joinCount'], data['leaveCount'],
                                          api.seconds_to_hms(data['playtimeSeconds']),
                                          api.seconds_to_hms(data['playtimeSecondsMonth']),
                                          await self.get_translation(user_id, "prioActive") if data['prio'] else '')
        return text
        #     return f"""
    # <b>Статистика <code>{player}</code> на 2b2t</b>
    # {online}
    # 📅 Первый заход: <code>{api.format_iso_time(data['firstSeen'])}</code>
    # 📅 Последний заход: <code>{api.format_iso_time(data['lastSeen'])}</code>
    # 💬 Сообщений в чате: <code>{data['chatsCount']}</code>
    # 💀 Смертей: <code>{data['deathCount']}</code>
    # ☠️ Убийств: <code>{data['killCount']}</code>
    # ➡️ Заходил на сервер: <code>{data['joinCount']}</code> раз
    # ⬅️ Выходил с сервера: <code>{data['leaveCount']}</code> раз
    # 🕒 Сколько играл: <code>{api.seconds_to_hms(data['playtimeSeconds'])}</code>
    # 🕒 Сколько играл за месяц: <code>{api.seconds_to_hms(data['playtimeSecondsMonth'])}</code>
    # {'⭐️ Приорететная очередь активна' if data['prio'] else ''}
    #     """


async def main():
    bot = Stats2b2tBot(TELEGRAM_BOT_TOKEN)
    await bot.initialize()
    await bot.run()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())

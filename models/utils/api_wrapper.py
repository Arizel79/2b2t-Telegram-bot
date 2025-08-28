import asyncio
import html
import json
import time
from pprint import pprint
from urllib.parse import urlencode, quote
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import requests

from datetime import datetime, timezone
from typing import Dict, Any
import aiohttp
from sqlalchemy.util import await_only

from models.utils.config import *
from models.utils.utils import *
import logging
import asyncio
from typing import Callable, Awaitable
import json
from models.utils.api import *


class Api2b2tWrapper(Api2b2t):
    def __init__(self, bot=None):
        self.bot = bot
        super().__init__()

    async def get_printable_2b2t_tablist_page(self, query_id):
        saved_state = await self.bot.db.get_saved_state(query_id)

        user_id = str(saved_state["user_id"])
        page = int(saved_state["page"])
        page_size = int(saved_state["page_size"])
        pages_count = await self.get_2b2t_tablist_pages_count()

        out = await self.bot.get_translation(user_id, "getTablistHeader") + "\n"
        tl = tablist = await self.get_2b2t_tablist_page(page, page_size)
        info = await self.get_2b2t_info()

        out += await self.get_printable_2b2t_info(user_id=user_id, with_header=False)
        out += "\n"

        for n, pl in enumerate(tablist["players"]):
            out += f"{await self.get_player_link(pl['playerName'], pl['uuid'])}{', ' if n + 1 < page_size else ''}"
        out += "\n\n"

        return out

    async def get_printable_2b2t_info(self, user_id=None, with_header=True):
        info = await self.get_2b2t_info()
        tl = await self.get_2b2t_tablist()

        text = ""
        if with_header:
            text += await self.bot.get_translation(user_id, "2b2tInfoHeader") + "\n"

        text += await self.bot.get_translation(user_id, "2b2tInfo",
                                               tl['count'],
                                               tl['prioCount'],
                                               int(tl['prioCount'] / tl['count'] * 100),
                                               tl['nonPrioCount'],
                                               int(tl['nonPrioCount'] / tl['count'] * 100),
                                               info["regular"],
                                               info["prio"],
                                               await self.seconds_to_hms(info["regular_eta_sec"], user_id),

                                               )
        return text

    async def get_printable_playtime_top(self, query_id):

        saved_state = await self.bot.db.get_saved_state(query_id)
        assert saved_state["type"] == "playtime_top"
        user_id = str(saved_state["user_id"])
        page = int(saved_state["page"])
        page_size = int(saved_state["page_size"])
        pages_count = await self.get_playtime_top_pages_count()

        out = await self.bot.get_translation(user_id, "playtimeTopHeader") + "\n"
        pttop = playtime_top = await self.get_playtime_top_page(page, page_size)

        for n, i in enumerate(playtime_top["players"]):
            n_in_top = (page - 1) * page_size + n + 1
            out += f"{n_in_top}. <code>{await self.seconds_to_hms(i['playtimeSeconds'], user_id)}</code> {await self.get_player_link(i['playerName'], i['uuid'])}\n"
        return out

    async def get_printable_kills_top_month(self, query_id):

        saved_state = await self.bot.db.get_saved_state(query_id)
        assert saved_state["type"] == "kills_top_month"
        user_id = str(saved_state["user_id"])
        page = int(saved_state["page"])
        page_size = int(saved_state["page_size"])
        pages_count = await self.get_kills_top_month_pages_count()

        out = await self.bot.get_translation(user_id, "killsTopMonthHeader") + "\n"
        kills_top_month = await self.get_kills_top_month_page(page, page_size)

        for n, i in enumerate(kills_top_month["players"]):
            n_in_top = (page - 1) * page_size + n + 1
            out += f"{n_in_top}. ☠️ <code>{html.escape(str(i['count']))}</code> kills {await self.get_player_link(i['playerName'], i['uuid'])}\n"
        return out

    async def get_printable_player_stats(self, user_id, username=None, uuid=None):
        try:
            self.logger.info(f"User {user_id} gets stats of username={username} / uuid={uuid}")
            result = {}
            if uuid is not None:
                use_uuid = True
            elif username is not None:
                use_uuid = False
            else:
                raise RuntimeError("no uuid or username!!1")
            result["by_uuid"] = use_uuid

            if use_uuid:
                username = await self.get_username_from_uuid(uuid)
            elif not use_uuid:
                uuid = await self.get_uuid_from_username(username)
            else:
                assert False

            result.update({"username": username, "uuid": uuid})
            if use_uuid:
                data = await self.get_player_stats(uuid=uuid)
            else:
                data = await self.get_player_stats(username=username)

            tablist = await self.get_2b2t_tablist()

            if not use_uuid:
                view_player = username
                is_player_online = any(p["playerName"].lower() == username.lower() for p in tablist["players"])
            elif use_uuid:
                view_player = uuid
                is_player_online = any(p["uuid"] == uuid for p in tablist["players"])
            else:
                raise RuntimeError()
            online = ("\n" + await self.bot.get_translation(user_id, 'isPlayerOnline')) if is_player_online else ''

            text = await self.bot.get_translation(user_id, "playerStats",
                                                  await self.get_player_link(data["username"], data["uuid"]), online, data["username"],
                                                  data["uuid"],
                                                  await self.format_user_time(user_id, data['firstSeen'], with_closers=False),
                                                  await self.format_user_time(user_id, data['lastSeen'],  with_closers=False),
                                                  data['chatsCount'],
                                                  data['deathCount'],
                                                  data['killCount'],
                                                  data['joinCount'], data['leaveCount'],
                                                  await self.seconds_to_hms(data['playtimeSeconds'], user_id),
                                                  await self.seconds_to_hms(data['playtimeSecondsMonth'], user_id),
                                                  await self.bot.get_translation(user_id, "prioActive") if data[
                                                      'prio'] else '')
            # return {"text": text, "show_kbd": True, }
            result.update({"text": text, "show_kbd": True})
            return result
        except self.PlayerNotFoundByUUID:
            text = await self.bot.get_translation(user_id, "playerNotFoundByUUID", uuid)
            result.update({"text": text, "show_kbd": False})
            return result
        except self.PlayerNotFoundByUsername:
            text = await self.bot.get_translation(user_id, "playerNotFoundByUsername", username)
            result.update({"text": text, "show_kbd": False})
            return result
        except self.PlayerNeverWasOn2b2tError:
            text = await self.bot.get_translation(user_id, "playerWasNotOn2b2t", username)
            result.update({"text": text, "show_kbd": False})
            return result
        except self.Api2b2tError as e:
            text = await self.bot.get_translation(user_id, "error")
            result.update({"text": text, "show_kbd": False})
            return result

        except Exception as e:
            self.logger.error("Error in get_printaleble_player_stats:")
            self.logger.exception(e)
            text = await self.bot.get_translation(user_id, "error")
            result.update({"text": text, "show_kbd": False})
            return result

    async def format_time(self, time, only_time=False, with_closers=True,to_tz=None):
        if with_closers:
            start, end = "[", "]"
        else:
            start, end = "", ""
        return f"{start}{html.escape(self.format_iso_time(time, only_time=only_time, to_tz=to_tz))}{end}"

    async def format_user_time(self, user_id, time=None, only_time=False, with_closers=True, to_tz=None):
        return f"{await self.format_time(time, only_time=only_time, with_closers=with_closers, to_tz=to_tz)}" # [usertime: {user_id}]

    async def format_chat_message(self, message, with_time=True, only_time=False, to_tz=None, lang=DEFAULT_LANG_CODE):
        if with_time:
            time_ = await self.format_time(message['time'],  only_time=only_time, to_tz=to_tz)#f"[<code>{html.escape(self.format_iso_time(message['time'], only_time=only_time))}</code>]"
        else:
            time_ = ""
        message_ = f"<code>{html.escape(message['chat'])}</code>"
        if bool(message.get("playerName", False)):
            uuid = message.get("playerUuid") or message.get("uuid")
            player = await self.get_player_link(message["playerName"], uuid)
            return await self.bot.translator.get_get_translation_by_lang(lang, "playerChatMessage", time_, " " + player,
                                                                         message_)
        else:
            return await self.bot.translator.get_get_translation_by_lang(lang, "playerChatMessage", time_, "", message_)

    async def format_death_message(self, message, with_time=True, only_time=False, lang=DEFAULT_LANG_CODE, to_tz=None):
        if with_time:
            time_ = await self.format_time(message['time'],  only_time=only_time, to_tz=to_tz) + " "
        else:
            time_ = ""
        victim = await self.get_player_link(message["victimPlayerName"], message["victimPlayerUuid"])
        death_message = message["deathMessage"]
        if not message["killerPlayerName"] is None:
            killer = await self.get_player_link(message["killerPlayerName"], message["killerPlayerUuid"])
            return await self.bot.translator.get_get_translation_by_lang(lang, "playerKilledByPlayer", time_, killer, victim, f"<code>{html.escape(death_message)}</code>")
        else:
            return await self.bot.translator.get_get_translation_by_lang(lang, "playerNormalDeath", time_, victim, f"<code>{html.escape(death_message)}</code>")

    async def format_connection_message(self, message, with_time=True, only_time=False, lang=DEFAULT_LANG_CODE, to_tz=None):
        if with_time:
            time_ = await self.format_time(message['time'],  only_time=only_time, to_tz=to_tz)
        else:
            time_ = ""
        type_ = message["connection"]
        player = await self.get_player_link(message["playerName"], message["playerUuid"])
        tm = time_ + " " if with_time else ""
        if type_ == "JOIN":
            return await self.bot.translator.get_get_translation_by_lang(lang, "playerJoinServer", tm, player)
        elif type_ == "LEAVE":
            return await self.bot.translator.get_get_translation_by_lang(lang, "playerLeftServer", tm, player)

    def get_namemc_link(self, username, uuid=None, formatting=True):
        url = f"https://namemc.com/{username}"
        if formatting:
            out = f"<a href='{url}'>{username}</a>"
        else:
            out = f"{url}"
        return out

    async def get_player_stats_link(self, username, uuid, formatting=True):
        if not is_valid_minecraft_uuid(uuid):
            uuid = username
        url = f"https://t.me/{self.bot.bot_username}?start=pl_{uuid}"
        if formatting:
            out = f"<a href='{html.escape(url)}'>{html.escape(username)}</a>"
        else:
            out = f"{url}"
        return out

    async def get_player_link(self, username, uuid, formatting=True):
        return await  self.get_player_stats_link(username, uuid, formatting)
        # if formatting:
        #     out = f"<code>{html.escape(username)}</code>"
        # else:
        #     out = f"{username}"
        # return out

    async def get_printable_2b2t_chat_search_page(self, query_id):
        try:
            saved_state = await self.bot.db.get_saved_state(query_id)
            search_query = str(saved_state["word"])
            search_page = int(saved_state["page"])

            page_size = int(saved_state["page_size"])
            data = await self.get_2b2t_chat_search_page(search_query, search_page, page_size=page_size)

            pages_count = saved_state["pages_count"] = int(data["pageCount"])

            total_results = saved_state["total"] = int(data["total"])
            out = await self.bot.get_translation(saved_state["user_id"], "outputChatSearchHeader",
                                                 html.escape(search_query), html.escape(str(search_page)),
                                                 html.escape(str(pages_count)), html.escape(str(total_results)))
            out += "\n"
            for i in data["chats"]:
                out += await self.format_chat_message(i) + "\n"

            await self.bot.db.update_saved_state(query_id, saved_state)
            return out

        except self.MessagesNotFound as e:
            out = await self.bot.get_translation(saved_state["user_id"], "chatMessagesBySearchQueryNotFound", html.escape(saved_state["word"]))
            return out
        except Exception as e:
            raise self.Api2b2tError(f"{type(e).__name__}: {e}")

    async def get_printable_messages_from_player_in_2b2t_chat(self, query_id):
        try:
            saved_state = await self.bot.db.get_saved_state(query_id)
            current_page = saved_state["page"]
            via_player_stats = saved_state.get("via_player_stats", False)
            page_size = saved_state["page_size"]

            username = saved_state["player_username"]
            uuid = saved_state["player_uuid"]
            use_uuid = saved_state["use_uuid"]

            user_id = saved_state["user_id"]

            result = {"username": username, "uuid": uuid, "show_nav_kbd": False}
            if use_uuid:
                player = uuid
            else:
                player = username

            if use_uuid:
                data = await self.get_messages_from_player_in_2b2t_chat(uuid=uuid, page=current_page,
                                                                        page_size=page_size)
            else:
                data = await self.get_messages_from_player_in_2b2t_chat(username=username, page=current_page,
                                                                        page_size=page_size)

            pages_count = saved_state["pages_count"] = int(data["pageCount"])
            total = saved_state["total"] = int(data["total"])
            out = await self.bot.get_translation(user_id, "outputSearchMessagesFromPlayerHeader",
                                                 html.escape(username), html.escape(uuid),
                                                 html.escape(str(current_page)),
                                                 html.escape(str(pages_count)), html.escape(str(total)))

            out += "\n"

            for i in data["chats"]:
                out += await self.format_chat_message(i) + "\n"

            await self.bot.db.update_saved_state(query_id, saved_state)

            result.update({"text": out, "show_nav_kbd": True})
            return result

        except self.PlayerNotFoundByUUID:
            text = await self.bot.get_translation(user_id, "playerNotFoundByUUID", uuid)
            result.update({"text": text})
            return result
        except self.PlayerNotFoundByUsername:
            text = await self.bot.get_translation(user_id, "playerNotFoundByUsername", username)
            result.update({"text": text})
            return result
        except self.PlayerNeverWasOn2b2tError:
            self.logger.info("Result: playerWasNotOn2b2t")
            text = await self.bot.get_translation(user_id, "playerWasNotOn2b2t", username)
            result.update({"text": text})
            return result
        except self.MessagesNotFound:
            text = await self.bot.get_translation(user_id, "messagesFromPlayerNotFound", username)
            result.update({"text": text})
            return result
        except self.Api2b2tError as e:
            self.logger.error("Error in get_printable_messages_from_player_in_2b2t_chat:")
            self.logger.exception(e)
            text = await self.bot.get_translation(user_id, "error")
            result.update({"text": text})
            return result

    async def seconds_to_hms(self, seconds: int, user_id) -> str:
        """
        Конвертирует секунды в формат [ДНИд]ЧЧ:ММ:СС

        :param seconds: Количество секунд (int)
        :return: Строка в формате [ДНИдней] HH:MM:SS
        """

        days = seconds // 86400
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        days_word = await self.bot.get_translation(user_id, "days")
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        if days > 0:
            time_str = f"{days} {days_word} {time_str}"
        return time_str

    def parse_iso_time(self, iso_string: str) -> datetime:
        try:
            if '.' in iso_string:
                iso_string = iso_string.split('.')[0]
            if '+' in iso_string:
                iso_string = iso_string.split('+')[0]
            if 'Z' in iso_string:
                iso_string = iso_string.split('Z')[0]

            return datetime.fromisoformat(iso_string)
        except ValueError as e:
            raise ValueError(f"Не удалось распарсить время: {e}")

    def format_iso_time(self, iso_string: str, only_time: bool = False, to_tz=None) -> str:
        try:
            dt = self.parse_iso_time(iso_string)

            # Конвертируем в указанную временную зону, если нужно
            if to_tz is not None:
                # Если передан строковый идентификатор временной зоны
                if isinstance(to_tz, str):
                    try:
                        import pytz
                        target_tz = pytz.timezone(to_tz)
                    except ImportError:
                        # Для Python 3.9+ используем zoneinfo
                        from zoneinfo import ZoneInfo
                        target_tz = ZoneInfo(to_tz)
                else:
                    target_tz = to_tz

                # Если datetime наивный (без временной зоны), считаем что это UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=pytz.UTC if 'pytz' in locals() else ZoneInfo('UTC'))

                # Конвертируем в целевую временную зону
                dt = dt.astimezone(target_tz)

            if only_time:
                return dt.strftime('%H:%M.%S')
            else:
                return dt.strftime('%H:%M.%S %d.%m.%Y')

        except ValueError as e:
            self.logger.error(f"Error in format_iso_time: {e}")
            self.logger.exception(e)
            return iso_string  # возвращаем исходную строку в случае ошибки
        except Exception as e:
            self.logger.error(f"Unexpected error in format_iso_time: {e}")
            self.logger.exception(e)
            return iso_string  # возвращаем исходную строку в случае ошибки


async def main():
    pass


if __name__ == '__main__':
    asyncio.run(main())

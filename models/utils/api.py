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
from models.utils.config import *

import asyncio
from typing import Callable, Awaitable
import json


class Api2b2t:
    GET_2B2T_INFO_CACHE_TIME = 60  # sec
    GET_2B2T_TABLIST_CACHE_TIME = 60  # sec
    GET_2B2T_PLAYTIME_TOP = 60 * 30  # sec
    GET_2B2T_KILLS_TOP = 10  # sec
    GET_2B2T_DEATHS_TOP = 10  # sec

    def __init__(self, bot=None):
        self.bot = bot

        # CACHE
        self.old_time_get_2b2t_info = 0
        self.cached_2b2t_info = None

        self.old_time_get_2b2t_tablist = 0
        self.cached_2b2t_tablist = None

        self.old_time_get_2b2t_playtime_top = 0
        self.cached_2b2t_playtime_top = None

        self.last_time_get_2b2t_chat_history = datetime.now(tz=timezone.utc)

    class Api2b2tError(Exception):
        pass

    class PlayerNeverWasOn2b2tError(Exception):
        pass

    class SSEError(Exception):
        pass

    async def get_2b2t_tablist(self):
        if time.time() > self.old_time_get_2b2t_tablist + self.GET_2B2T_TABLIST_CACHE_TIME:
            try:
                url = "https://api.2b2t.vc/tablist/info"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        self.cached_2b2t_tablist = data = await response.json()
                        self.old_time_get_2b2t_tablist = time.time()
                        return data

            except Exception as e:
                raise self.Api2b2tError(f"{type(e).__name__}: {e}")
        else:
            return self.cached_2b2t_tablist

    async def get_2b2t_tablist_page(self, page=1, page_size=20):
        start = (page - 1) * page_size
        end = start + page_size

        tablist = dict(await self.get_2b2t_tablist())
        tablist["players"] = tablist["players"][start:end]
        return tablist

    async def get_playtime_top_page(self, page=1, page_size=20):
        start = (page - 1) * page_size
        end = start + page_size

        playtime_top = dict(await self.get_playtime_top())
        playtime_top["players"] = playtime_top["players"][start:end]
        return playtime_top

    async def get_2b2t_tablist_pages_count(self, page_size=TABLIST_PAGE_SIZE) -> int:
        n = (await self.get_2b2t_tablist())["count"] / page_size
        if n == int(n):
            return int(n) - 1
        else:
            return int(n)

    async def get_playtime_top_pages_count(self, page_size=PLAYTIME_TOP_PAGE_SIZE) -> int:
        n = len((await self.get_playtime_top())["players"]) / page_size
        if n == int(n):
            return int(n) - 1
        else:
            return int(n)

    async def get_printable_2b2t_tablist_page(self, query_id):

        saved_state = await self.bot.db.get_saved_state(query_id)
        assert saved_state["type"] == "tablist"
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
            out += f"<code>{pl['playerName']}</code>{', ' if n + 1 < page_size else ''}"
        out += "\n\n"

        return out

    async def get_2b2t_info(self):
        if time.time() > self.old_time_get_2b2t_info + self.GET_2B2T_INFO_CACHE_TIME:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.2b2t.vc/queue") as response:
                        data = await response.json()

                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.2b2t.vc/queue/eta-equation") as response:
                        data.update(await response.json())

                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.mcsrvstat.us/3/2b2t.org") as response:
                        online = (await response.json())["players"]["online"]
                data["online"] = online

                # https://api.2b2t.vc/queue/eta-equation

                data["regular_eta_sec"] = data["factor"] * (data["regular"] ** data["pow"])

                self.cached_2b2t_info = data
                self.old_time_get_2b2t_info = time.time()

                return data
            except Exception as e:
                raise self.Api2b2tError(f"{type(e).__name__}: {e}")
        else:
            return self.cached_2b2t_info

    async def get_printable_2b2t_info(self, user_id=None, with_header=True):
        ''' "<b>ℹ\uFE0F 2b2t</b>\n\n\uD83D\uDFE2 Онлайн: {}\
        n\uD83D\uDE34 Очередь: {}\n⭐\uFE0F Прио. очередь: {}\n
          out += f\"Онлайн: <code>{tablist['count']}</code>\\n\"\n
                out += f\"С прио: <code>{tablist['prioCount']}</code>
                 ({int(tablist['prioCount'] / tablist['count'] * 100)})%\\n\"\n        out += f\"Без прио: <code>{tablist['nonPrioCount']}</code> ({int(tablist['nonPrioCount'] / tablist['count'] * 100)}%)\\n\"",
'''
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

    async def get_playtime_top(self):
        if time.time() > self.old_time_get_2b2t_playtime_top + self.GET_2B2T_PLAYTIME_TOP:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.2b2t.vc/playtime/top") as response:
                        data = await response.json()

                self.cached_2b2t_playtime_top = data
                self.old_time_get_2b2t_playtime_top = time.time()

                return data
            except Exception as e:
                raise self.Api2b2tError(f"{type(e).__name__}: {e}")
        else:
            return self.cached_2b2t_playtime_top

    async def get_printable_playtime_top(self, query_id):

        saved_state = await self.bot.db.get_saved_state(query_id)
        assert saved_state["type"] == "playtime_top"
        user_id = str(saved_state["user_id"])
        page = int(saved_state["page"])
        page_size = int(saved_state["page_size"])
        pages_count = await self.get_2b2t_tablist_pages_count()

        out = await self.bot.get_translation(user_id, "playtimeTopHeader") + "\n"
        pttop = playtime_top = await self.get_playtime_top_page(page, page_size)

        for n, i in enumerate(playtime_top["players"]):
            n_in_top = page * page_size + n
            out += f"{n_in_top}. <code>{await self.seconds_to_hms(i['playtimeSeconds'], user_id)}</code> - <code>{i['playerName']}</code>\n"
        return out

    async def get_player_stats(self, player: str = None, uuid: str = None) -> Dict[str, Any] or None:
        assert (not player is None) or (not uuid is None)

        if not player is None:
            is_uuid = False
            url = f"https://api.2b2t.vc/stats/player?playerName={player}"
        elif not uuid is None:
            is_uuid = True
            url = f"https://api.2b2t.vc/stats/player?uuid={uuid}"
        else:
            raise self.Api2b2tError("player and uuid are invalid")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:

                    result = {}
                    if is_uuid:
                        result["uuid"] = uuid
                    else:
                        result["player"] = player

                    result.update(await response.json())

                    return result
        except aiohttp.client_exceptions.ContentTypeError as e:
            raise self.PlayerNeverWasOn2b2tError
        except Exception as e:
            raise self.Api2b2tError(f"{type(e).__name__}: {e}")

    async def get_printaleble_player_stats(self, user_id, player=None, uuid=None):
        is_player_online = False
        tablist = await self.get_2b2t_tablist()
        use_uuid = False
        if player is not None:

            view_player = player
            is_player_online = any(p["playerName"].lower() == player.lower() for p in tablist["players"])
        elif uuid is not None:
            use_uuid = True
            view_player = uuid
            is_player_online = any(p["uuid"] == uuid for p in tablist["players"])

        data = await self.get_player_stats(player, uuid)
        online = ("\n" + await self.bot.get_translation(user_id, 'isPlayerOnline')) if is_player_online else ''

        if not data.get("firstSeen", False):
            return await self.bot.get_translation(user_id, "playerWasNotOn2b2t", player, player)
        text = await self.bot.get_translation(user_id, "playerStats",
                                              view_player, online, self.format_iso_time(data['firstSeen']),
                                              self.format_iso_time(data['lastSeen']), data['chatsCount'],
                                              data['deathCount'],
                                              data['killCount'],
                                              data['joinCount'], data['leaveCount'],
                                              await self.seconds_to_hms(data['playtimeSeconds'], user_id),
                                              await self.seconds_to_hms(data['playtimeSecondsMonth'], user_id),
                                              await self.bot.get_translation(user_id, "prioActive") if data[
                                                  'prio'] else '')
        return text

    async def get_2b2t_chat_history(
            self,
            start_date: datetime,
            end_date: datetime,
            page: int = 1,
            page_size=CHAT_HISTORY_PAGE_SIZE,
            sort=None,
    ):
        '''
dt = datetime.now(tz=timezone.utc)
formatted_str = dt.isoformat(timespec='milliseconds')  # Форматирование в строку
print(formatted_str)  # 2022-10-31T01:30:00.000'''
        try:
            base_url = "https://api.2b2t.vc/chats/window"
            params = {"startDate": start_date.isoformat(timespec='milliseconds'),
                      "endDate": end_date.isoformat(timespec='milliseconds'), "page": page, "pageSize": page_size}

            if sort is not None:
                assert sort in ["asc", "desc"]
                params["sort"] = sort

            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params) as resp:
                    print("URL:", resp.url)
                    data = await resp.json()
                    return data

        except Exception as e:
            raise self.Api2b2tError(f"{type(e).__name__}: {e}")

        except requests.exceptions.JSONDecodeError:
            raise self.Api2b2tError(f"requests.exceptions.JSONDecodeError ({data.text}")

    async def get_new_2b2t_chat_messages(self):
        now = datetime.now(tz=timezone.utc)
        data = await self.get_2b2t_chat_history(self.last_time_get_2b2t_chat_history, now)

        self.last_time_get_2b2t_chat_history = now

        return data

    async def get_2b2t_chat_search_page(
            self,
            query: str = None,
            page: int = 1,
            page_size=10,
            sort=None,
    ):
        try:
            url = "https://api.2b2t.vc/chats/search"
            params = {"word": query, "page": page, "pageSize": page_size}

            if sort is not None:
                assert sort in ["asc", "desc"]
                params["sort"] = sort

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    return data

        except Exception as e:
            raise self.Api2b2tError(f"{type(e).__name__}: {e}")
            # params = {"page": page, "pageSize": page_size}
            # if from_player:
            #     params['playerName'] = from_player
            #
            # elif not query is None:
            #     params['word'] = query
            #
            #
            #
            # if not start_date is None:
            #     params["startDate"] = json.dumps(start_date.isoformat())
            #
            # if not end_date is None:
            #     params["endDate"] = json.dumps(end_date.isoformat())
            #

        except requests.exceptions.JSONDecodeError:
            raise self.Api2b2tError(f"requests.exceptions.JSONDecodeError ({data.text}")

    async def get_messages_from_player_in_2b2t_chat(self, player_name: str = None, uuid=None, page: int = 1,
                                                    page_size=10, sort=None, check_player_was_on_2b2t=False):
        '''
        :return {
        "chats": [
        {
          "time": "2025-06-30T09:42:03.228Z",
          "chat": "string"
        }
        ],
        "total": 0,
        "pageCount": 0
        }
        '''

        try:
            url = "https://api.2b2t.vc/chats"
            params = {"page": page, "pageSize": page_size}
            if not player_name is None:
                params["playerName"] = player_name
            elif not uuid is None:
                params["uuid"] = uuid

            if sort is not None:
                assert sort in ["asc", "desc"]
                params["sort"] = sort

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 204:
                        raise self.PlayerNeverWasOn2b2tError
                        # return {"chats": [], "total": 0, "pageCount": 0}
                    data = await resp.json()
                    return data
        except self.PlayerNeverWasOn2b2tError:
            raise self.PlayerNeverWasOn2b2tError
        except Exception as e:
            raise self.Api2b2tError(f"{type(e).__name__}: {e}")

        except requests.exceptions.JSONDecodeError:
            raise self.Api2b2tError(f"requests.exceptions.JSONDecodeError ({data.text}")

    def format_chat_message(self, message, with_time=True):
        if with_time:
            time_ = f"[<code>{html.escape(self.format_iso_time(message["time"]))}</code>]"
        else:
            time_ = ""
        if bool(message.get("playerName", False)):
            return f'💬 <code>{html.escape(message["playerName"])}</code> {time_}: <code>{html.escape(message["chat"])}</code>'
        return f'💬 {time_ + ": " if with_time else ''}<code>{html.escape(message["chat"])}</code>'

    async def get_printable_2b2t_chat_search_page(self, query_id):
        try:
            saved_state = await self.bot.db.get_saved_state(query_id)
            search_query = str(saved_state["word"])
            search_page = int(saved_state["page"])

            page_size = int(saved_state["page_size"])
            data = await self.get_2b2t_chat_search_page(search_query, search_page, page_size=page_size)

            pages_count = saved_state["pages_count"] = int(data["pageCount"])

            total_results = saved_state["total"] = int(data["total"])

            # out = (f"<b>2b2t chat search</b>\n"
            #        f"\n"
            #        f"🔍 Search query: {html.escape(search_query)}\n"
            #        f"ℹ️ Page: <code>{html.escape(str(search_page))}</code> / <code>{html.escape(str(pages_count))}</code>\n"
            #        f"💬 Results: <code>{html.escape(str(total_results))}</code>\n"
            #        f"\n")
            out = await self.bot.get_translation(saved_state["user_id"], "outputChatSearchHeader",
                                                 html.escape(search_query), html.escape(str(search_page)),
                                                 html.escape(str(pages_count)), html.escape(str(total_results)))
            out += "\n"

            for i in data["chats"]:
                out += self.format_chat_message(i) + "\n"

            await self.bot.db.update_saved_state(query_id, saved_state)
            return out
        except Exception as e:
            raise self.Api2b2tError(f"{type(e).__name__}: {e}")

    async def get_printable_messages_from_player_in_2b2t_chat(self, query_id):
        try:
            saved_state = await self.bot.db.get_saved_state(query_id)
            current_page = saved_state["page"]
            page_size = saved_state["page_size"]

            player_name = saved_state.get("player_name", None)
            uuid = saved_state.get("player_uuid", None)

            if not uuid is None:
                use_uuid = True
                player = uuid
            else:
                use_uuid = False
                player = player_name
                assert not player_name is None

            if use_uuid:
                data = await self.get_messages_from_player_in_2b2t_chat(uuid=uuid, page=current_page,
                                                                        page_size=page_size)
            else:
                data = await self.get_messages_from_player_in_2b2t_chat(player_name=player_name, page=current_page,
                                                                        page_size=page_size)

            pages_count = saved_state["pages_count"] = int(data["pageCount"])
            total = saved_state["total"] = int(data["total"])
            out = await self.bot.get_translation(saved_state["user_id"], "outputSearchMessagesFromPlayerHeader",
                                                 "<code>" + html.escape(player) + "</code>",
                                                 html.escape(str(current_page)),
                                                 html.escape(str(pages_count)), html.escape(str(total)))

            out += "\n"

            for i in data["chats"]:
                out += self.format_chat_message(i) + "\n"

            await self.bot.db.update_saved_state(query_id, saved_state)

            return out
        except self.PlayerNeverWasOn2b2tError:
            raise self.PlayerNeverWasOn2b2tError
        except Exception as e:
            raise self.Api2b2tError(f"{type(e).__name__}: {e}")

    async def listen_to_chat_feed(self, callback: Awaitable[dict]):
        """
        Подключается к SSE-потоку /feed/chats и вызывает callback при новых сообщениях.
        """
        url = "https://api.2b2t.vc/feed/chats"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers={"Accept": "text/event-stream"}) as resp:
                    if resp.status != 200:
                        raise self.Api2b2tError(f"Error: HTTP {resp.status}")

                    # Читаем поток событий
                    async for line in resp.content:
                        if line.startswith(b"data:"):
                            try:
                                message = json.loads(line[5:].strip())
                                await callback(message)
                            except json.JSONDecodeError as e:
                                raise self.Api2b2tError(f"Error parsing JSON: {e}")


            except Exception as e:
                raise self.Api2b2tError(f"Ошибка в SSE-подключении: {e}")

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

    def format_iso_time(self, iso_string: str) -> str:
        try:
            dt = self.parse_iso_time(iso_string)
            return dt.strftime('%H:%M.%S %d.%m.%Y')
        except ValueError as e:
            return f"Ошибка: {str(e)}"


async def main():
    api = Api2b2t()

    # print(await api.get_messages_from_player_in_2b2t_chat(player_name="babwy", page=1))
    # print(await api.get_2b2t_tablist())
    # pprint(await api.get_2b2t_info())
    # pprint(await api.get_2b2t_tablist_pages_count(20))
    async def on_chat_msg(event):
        print("ev:", event)

    while True:
        await api.listen_to_chat_feed(on_chat_msg)
        await asyncio.sleep(2)

    # print(await api.get_2b2t_tablist_page(1, 3))
    # print(await api.get_2b2t_tablist_page(2, 3))


if __name__ == '__main__':
    asyncio.run(main())

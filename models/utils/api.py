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
from models.utils.utils import *
import logging
import asyncio
from typing import Callable, Awaitable
import json


class Api2b2t:
    GET_2B2T_INFO_CACHE_TIME = 60  # sec
    GET_2B2T_TABLIST_CACHE_TIME = 60  # sec
    GET_2B2T_PLAYTIME_TOP = 60 * 30  # sec
    GET_2B2T_KILLS_TOP_MONTH = 10  # sec
    GET_2B2T_DEATHS_TOPA_MONTH = 10  # sec

    def __init__(self, bot=None):
        self.bot = bot
        self.logger = setup_logger("api_2b2t", "api_2b2t.log", logging.INFO)
        # CACHE
        self.old_time_get_2b2t_info = 0
        self.cached_2b2t_info = None

        self.old_time_get_2b2t_tablist = 0
        self.cached_2b2t_tablist = None

        self.old_time_get_2b2t_playtime_top = 0
        self.cached_2b2t_playtime_top = None

        self.old_time_get_2b2t_kills_top_month = 0
        self.cached_2b2t_kills_top_month = None

        self.old_time_get_2b2t_deaths_top_month = 0
        self.cached_2b2t_deaths_top_month = None

        self.last_time_get_2b2t_chat_history = datetime.now(tz=timezone.utc)
        self.mc_skins_api_base = "https://mineskin.eu"

    class Api2b2tError(Exception):
        pass

    class PlayerNeverWasOn2b2tError(Exception):
        pass

    class SSEError(Exception):
        pass

    class PlayerNotFound(Exception):
        pass

    class PlayerNotFoundByUUID(PlayerNotFound):
        pass

    class PlayerNotFoundByUsername(PlayerNotFound):
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

    async def get_2b2t_tablist_pages_count(self, page_size=TABLIST_PAGE_SIZE) -> int:
        n = (await self.get_2b2t_tablist())["count"] / page_size
        if n == int(n):
            return int(n) - 1
        else:
            return int(n)

    async def get_playtime_top_page(self, page=1, page_size=PLAYTIME_TOP_PAGE_SIZE):
        start = (page - 1) * page_size
        end = start + page_size

        playtime_top = dict(await self.get_playtime_top())
        playtime_top["players"] = playtime_top["players"][start:end]
        return playtime_top

    async def get_playtime_top_pages_count(self, page_size=PLAYTIME_TOP_PAGE_SIZE) -> int:
        n = len((await self.get_playtime_top())["players"]) / page_size
        if n == int(n):
            return int(n) - 1
        else:
            return int(n)

    async def get_kills_top_month_page(self, page=1, page_size=KILLS_TOP_MONTH_PAGE_SIZE):
        start = (page - 1) * page_size
        end = start + page_size

        kills_top_month = dict(await self.get_kills_top_month())
        kills_top_month["players"] = kills_top_month["players"][start:end]
        return kills_top_month

    async def get_kills_top_month_pages_count(self, page_size=KILLS_TOP_MONTH_PAGE_SIZE) -> int:
        n = len((await self.get_kills_top_month())["players"]) / page_size
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

    async def get_kills_top_month(self):
        if time.time() > self.old_time_get_2b2t_kills_top_month + self.GET_2B2T_KILLS_TOP_MONTH:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.2b2t.vc/kills/top/month") as response:
                        data = await response.json()

                self.cached_2b2t_kills_top_month = data
                self.old_time_get_2b2t_kills_top_month = time.time()

                return data
            except Exception as e:
                raise self.Api2b2tError(f"{type(e).__name__}: {e}")
        else:
            return self.cached_2b2t_kills_top_month

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
        pages_count = await self.get_playtime_top_pages_count()

        out = await self.bot.get_translation(user_id, "playtimeTopHeader") + "\n"
        pttop = playtime_top = await self.get_playtime_top_page(page, page_size)

        for n, i in enumerate(playtime_top["players"]):
            n_in_top = page * page_size + n
            out += f"{n_in_top}. <code>{await self.seconds_to_hms(i['playtimeSeconds'], user_id)}</code> - <code>{i['playerName']}</code>\n"
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
            n_in_top = page * page_size + n
            out += f"{n_in_top}. ☠️ <code>{html.escape(str(i['count']))}</code> kills - <code>{html.escape(i['playerName'])}</code>\n"
        return out

    async def get_player_stats(self, username: str = None, uuid: str = None) -> Dict[str, Any] or None:
        assert (not username is None) or (not uuid is None)

        if username is None:
            is_uuid = True
            url = f"https://api.2b2t.vc/stats/player?uuid={uuid}"
        elif uuid is None:
            is_uuid = False
            url = f"https://api.2b2t.vc/stats/player?playerName={username}"

        else:
            raise self.Api2b2tError("player and uuid are invalid")

        if is_uuid:
            username = await self.get_username_from_uuid(uuid)
        elif not is_uuid:
            uuid = await self.get_uuid_from_username(username)
        else:
            assert False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    result = {}
                    if is_uuid:
                        result["uuid"] = uuid
                    else:
                        result["player"] = username

                    result.update(await response.json())
                    result["username"] = username
                    result["uuid"] = uuid

                    if result["firstSeen"] is None:
                        raise self.PlayerNeverWasOn2b2tError("!!DQ")

                    return result

        except aiohttp.client_exceptions.ContentTypeError as e:
            raise self.PlayerNeverWasOn2b2tError("!!!eee")

        except Exception as e:
            if isinstance(e,
                          (self.PlayerNeverWasOn2b2tError, self.PlayerNotFoundByUsername, self.PlayerNotFoundByUUID)):
                raise
            else:
                raise self.Api2b2tError(f"{type(e).__name__}: {e}")

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
                                                  self.get_player_link(data["username"]), online, data["username"], data["uuid"],
                                                  self.format_iso_time(data['firstSeen']),
                                                  self.format_iso_time(data['lastSeen']), data['chatsCount'],
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

    async def get_messages_from_player_in_2b2t_chat(self, username: str = None, uuid=None, page: int = 1,
                                                    page_size=SEARCH_FROM_PLAYER_PAGE_SIZE, sort=None):
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
            if username is None:
                is_uuid = True
            elif uuid is None:
                is_uuid = False
            else:
                raise self.Api2b2tError("player and uuid are invalid")

            if is_uuid:
                username = await self.get_username_from_uuid(uuid)
            elif not is_uuid:
                uuid = await self.get_uuid_from_username(username)
            else:
                assert False

            url = "https://api.2b2t.vc/chats"
            params = {"page": page, "pageSize": page_size}
            if not username is None:
                params["playerName"] = username
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

                    data["username"] = username
                    data["uuid"] = uuid
                    return data

        except Exception as e:
            if isinstance(e,
                          (self.PlayerNeverWasOn2b2tError, self.PlayerNotFoundByUsername, self.PlayerNotFoundByUUID)):
                raise
            else:
                raise self.Api2b2tError(f"{type(e).__name__}: {e}")


        except requests.exceptions.JSONDecodeError:
            raise self.Api2b2tError(f"requests.exceptions.JSONDecodeError ({data.text}")

    def format_chat_message(self, message, with_time=True):
        if with_time:
            time_ = f"[<code>{html.escape(self.format_iso_time(message['time']))}</code>]"
        else:
            time_ = ""
        if bool(message.get("playerName", False)):
            uuid = message.get("playerUuid") or message.get("uuid")
            player = self.get_player_link(message["playerName"], uuid)
            return f'💬 {player} {time_}: <code>{html.escape(message["chat"])}</code>'
        else:
            return f'💬 {time_ + ": " if with_time else ""}<code>{html.escape(message["chat"])}</code>'

    def format_death_message(self, message, with_time=True):
        if with_time:
            time_ = f"[<code>{html.escape(self.format_iso_time(message['time']))}</code>]"
        else:
            time_ = ""
        victim = self.get_player_link(message["victimPlayerName"], message["victimPlayerUuid"])
        death_message = message["deathMessage"]
        if not message["killerPlayerName"] is None:
            killer = self.get_player_link(message["killerPlayerName"], message["killerPlayerUuid"])
            return f'☠️ {time_} {killer} killed {victim}: <code>{html.escape(death_message)}</code>'
        else:
            return f'☠️ {time_} {victim} death: <code>{html.escape(death_message)}</code>'

    def format_connection_message(self, message, with_time=True):
        if with_time:
            time_ = f"[<code>{html.escape(self.format_iso_time(message['time']))}</code>]"
        else:
            time_ = ""
        type_ = message["connection"]
        player = self.get_player_link(message["playerName"], message["playerUuid"])
        if type_ == "JOIN":
            return f'➡️ {time_ + " " if with_time else ""} {player} joined'
        elif type_ == "LEAVE":
            return f'⬅️ {time_ + " " if with_time else ""} {player} left'

    def get_namemc_link(self, username, uuid=None, formatting=True):
        url = f"https://namemc.com/{username}"
        if formatting:
            out = f"<a href='{url}'>{username}</a>"
        else:
            out = f"{url}"
        return out

    def get_player_stats_link(self, player, formatting=True):

        url = f"https://t.me/{self.bot.bot_username}?start=pl_{player}"
        if formatting:
            out = f"<b><a href='{url}'>{player}</a></b>"
        else:
            out = f"{url}"
        return out

    def get_player_link(self, username, uuid=None, formatting=True):
        return self.get_player_stats_link(username,formatting)
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
            via_player_stats = saved_state.get("via_player_stats", False)
            page_size = saved_state["page_size"]


            username = saved_state["player_username"]
            uuid = saved_state["player_uuid"]
            use_uuid = saved_state["use_uuid"]

            user_id = saved_state["user_id"]

            result = {"username": username, "uuid": uuid}
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
                out += self.format_chat_message(i) + "\n"

            await self.bot.db.update_saved_state(query_id, saved_state)

            result.update({"text": out})
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
            text = await self.bot.get_translation(user_id, "playerWasNotOn2b2t", username)
            result.update({"text": text})
            return result
        except self.Api2b2tError as e:
            self.logger.error("Error in get_printable_messages_from_player_in_2b2t_chat:")
            self.logger.exception(e)
            text = await self.bot.get_translation(user_id, "error")
            result.update({"text": text})
            return result
    async def safe_listen_sse_stream(self, url, callback: Awaitable):
        while True:
            try:
                await self.listen_sse_stream(url, callback)
            except Exception as e:
                self.logger.error(f"Error in safe_listen_sse_stream: {e}")
                self.logger.exception(e)
    async def listen_sse_stream(self, url, callback: Awaitable):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers={"Accept": "text/event-stream"}) as resp:
                    if resp.status != 200:
                        raise self.Api2b2tError(f"Error: HTTP {resp.status}")

                    async for line in resp.content:
                        if line.startswith(b"data:"):
                            try:
                                message = json.loads(line[5:].strip())
                                await callback(message)
                            except json.JSONDecodeError as e:
                                raise self.Api2b2tError(f"Error parsing JSON: {e}")


            except Exception as e:
                self.logger.error(f"Error in listen_sse_steam: {e}")
                self.logger.exception(e)
                raise self.Api2b2tError(f"SSE-connection error: {e}")

    async def listen_to_chats_feed(self, callback: Awaitable[dict]):
        await self.safe_listen_sse_stream("https://api.2b2t.vc/feed/chats", callback)
    async def listen_to_connections_feed(self, callback: Awaitable[dict]):
        await self.safe_listen_sse_stream("https://api.2b2t.vc/feed/connections", callback)

    async def listen_to_deaths_feed(self, callback: Awaitable[dict]):
        await self.safe_listen_sse_stream("https://api.2b2t.vc/feed/deaths", callback)


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

    async def get_uuid_from_username(self, username):
        """Получает UUID игрока по его никнейму (асинхронно)."""
        url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
        self.logger.debug(f"Getting UUID for username: {username}")

        if not is_valid_minecraft_username(username):
            raise ValueError(f"username {username} is not valid!")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    uuid = data.get("id")
                    if '-' not in uuid:
                        formatted_uuid = f"{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}"
                    else:
                        formatted_uuid = uuid
                    self.logger.debug(f"Recieved uuid: {uuid} for username: {username}")
                    return formatted_uuid
                else:
                    self.logger.error(f"While getting uuid for username={username}: Error code {response.status}: ")
                    raise self.PlayerNotFoundByUsername(f"Player {username} not found")

    async def get_username_from_uuid(self, uuid):
        """Получает текущий никнейм игрока по его UUID (асинхронно)."""

        self.logger.debug(f"Getting username for UUID: {uuid}")
        if not is_valid_minecraft_uuid(uuid):
            raise ValueError(f"Invalid UUID: {uuid}")
        uuid = uuid.replace("-", "")

        url = f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status in [200, 400]:
                    data = await response.json()
                    username = data.get("name")
                    self.logger.info(f"Received username for uuid={uuid}: {username}")
                    return username
                else:
                    self.logger.error(f"While getting username for uuid={uuid}: Error code {response.status}")
                    if response.status in (204,):
                        raise self.PlayerNotFoundByUUID(f"UUID {uuid} not found")

                    else:
                        raise self.Api2b2tError(f"HTTP status: {response.status}; uuid={uuid}")

    async def get_visage_urls(self, username: str, scale: int=1000) -> dict:
        """Получает скины через Visage API"""
        return {
            "face": f"{self.mc_skins_api_base}/helm/{username}/{scale}.png",
            "front": f"{self.mc_skins_api_base}/armor/body/{username}/{scale}.png",
            "full": f"{self.mc_skins_api_base}/armor/body/{username}/{scale}.png",
            "bust": f"{self.mc_skins_api_base}/armor/bust/{username}/{scale}.png"
        }

    async def download_visage_image(self, username: str, type: str = "face", scale: int=1000) -> io.BytesIO:
        """Скачивает из Visage"""
        urls = await self.get_visage_urls(username, scale=scale)
        skin_url = urls.get(type, urls["face"])

        async with aiohttp.ClientSession() as session:
            async with session.get(skin_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    return io.BytesIO(image_data)
        return None


async def main():
    pass


if __name__ == '__main__':
    asyncio.run(main())

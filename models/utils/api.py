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

    class MessagesNotFound(Exception):
        pass

    def __init__(self):
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
                        raise self.MessagesNotFound
                        # return {"chats": [], "total": 0, "pageCount": 0}
                    data = await resp.json()

                    data["username"] = username
                    data["uuid"] = uuid
                    return data

        except Exception as e:
            self.logger.error(f"Error handled and reraised in get_messages_from_player_in_2b2t_chat: {e}")
            self.logger.exception(e)
            if isinstance(e,
                          (self.MessagesNotFound, self.PlayerNeverWasOn2b2tError, self.PlayerNotFoundByUsername, self.PlayerNotFoundByUUID)):
                raise
            else:
                raise self.Api2b2tError(f"{type(e).__name__}: {e}")


        except requests.exceptions.JSONDecodeError:
            raise self.Api2b2tError(f"requests.exceptions.JSONDecodeError ({data.text}")

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
                    resp.raise_for_status()
                    data = await resp.json()
                    return data
        except aiohttp.client_exceptions.ContentTypeError:
            raise self.MessagesNotFound("Messages not found!")
        except Exception as e:
            raise self.Api2b2tError(f"{type(e).__name__}: {e}")

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

    async def get_visage_urls(self, username: str, scale: int = 1000) -> dict:
        """Получает скины через Visage API"""
        return {
            "face": f"{self.mc_skins_api_base}/helm/{username}/{scale}.png",
            "front": f"{self.mc_skins_api_base}/armor/body/{username}/{scale}.png",
            "full": f"{self.mc_skins_api_base}/armor/body/{username}/{scale}.png",
            "bust": f"{self.mc_skins_api_base}/armor/bust/{username}/{scale}.png"
        }

    async def download_visage_image(self, username: str, type: str = "face", scale: int = 1000) -> io.BytesIO:
        """Скачивает из Visage"""
        urls = await self.get_visage_urls(username, scale=scale)
        skin_url = urls.get(type, urls["face"])

        async with aiohttp.ClientSession() as session:
            async with session.get(skin_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    return io.BytesIO(image_data)
        return None
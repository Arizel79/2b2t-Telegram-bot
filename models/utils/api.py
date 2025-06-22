import time

import requests
from datetime import datetime
from typing import Dict, Any



class Api2b2t:
    GET_2B2T_INFO_CACHE_TIME = 5 # sec
    def __init__(self, bot):
        self.bot = bot
        self.old_time_get_2b2t_info = 0
        self.cached_2b2t_info = None


    class Api2b2tError(Exception):
        pass

    def get_2b2t_tablist(self):
        try:
            data = requests.get("https://api.2b2t.vc/tablist")
            data = data.json()
            data["header"] = data["header"].replace("\n\n", "\n")[1:-1]
            return data
        except requests.exceptions.ConnectionError:
            print("Connection Error")
            raise self.Api2b2tError("Ошибка запроса к API")

    def get_2b2t_info(self):
        if time.time() > self.old_time_get_2b2t_info + self.GET_2B2T_INFO_CACHE_TIME:
            try:
                data = requests.get("https://api.2b2t.vc/queue")
                data = data.json()
                online = requests.get("https://api.mcsrvstat.us/3/2b2t.org").json()["players"]["online"]
                data["online"] = online

                self.cached_2b2t_info = data
                self.old_time_get_2b2t_info = time.time()
                return data
            except requests.exceptions.ConnectionError:
                print("Connection Error")
                raise self.Api2b2tError("Ошибка запроса к API")
        else:
            return self.cached_2b2t_info

    def get_player_stats(self, player: str = None, uuid: str = None) -> Dict[str, Any] or None:
        assert (not player  is None) or (not uuid is None)

        if not player is None:
            is_uuid = False
            url = f"https://api.2b2t.vc/stats/player?playerName={player}"
        elif not uuid is None:
            is_uuid = True
            url = f"https://api.2b2t.vc/stats/player?uuid={uuid}"
        else:
            raise self.Api2b2tError("player and uuid are invalid")

        response = requests.get(url)

        result = {}
        if is_uuid:
            result["uuid"] = uuid
        else:
            result["player"] = player
        if response.status_code == 200:
            result.update(response.json())

        elif response.status_code == 204:
            pass
        else:
            raise self.Api2b2tError(f"code: {response.status_code}")

        return result

    async def get_printable_2b2t_info(self, user_id):
        data = self.get_2b2t_info()
        return await self.bot.get_translation(user_id, "2b2tInfo", data["online"], data["regular"], data["prio"])


    async def get_printaleble_player_stats(self, user_id, player=None, uuid=None):
        is_player_online = False
        tablist = self.get_2b2t_tablist()

        if player is not None:
            is_player_online = any(p["playerName"] == player for p in tablist["players"])
        elif uuid is not None:
            is_player_online = any(p["uuid"] == uuid for p in tablist["players"])

        data = self.get_player_stats(player, uuid)
        online = ("\n" + await self.bot.get_translation(user_id, 'isPlayerOnline')) if is_player_online else ''

        if not data.get("firstSeen", False):
            return await self.bot.get_translation(user_id, "playerWasNotOn2b2t", player, player)
        text = await self.bot.get_translation(user_id, "playerStats",
                                          player, online, self.format_iso_time(data['firstSeen']),
                                          self.format_iso_time(data['lastSeen']), data['chatsCount'], data['deathCount'],
                                          data['killCount'],
                                          data['joinCount'], data['leaveCount'],
                                          await self.seconds_to_hms(data['playtimeSeconds'], user_id),
                                          await self.seconds_to_hms(data['playtimeSecondsMonth'], user_id),
                                          await self.bot.get_translation(user_id, "prioActive") if data['prio'] else '')
        return text

    async def seconds_to_hms(self, seconds: int, user_id) -> str:
        """
        Конвертирует секунды в формат [ДНИд]ЧЧ:ММ:СС

        :param seconds: Количество секунд (int)
        :return: Строка в формате [ДНИд]HH:MM:SS
        """
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        days_word = await self.bot.get_translation(user_id, "days")
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        if days > 0:
            time_str = f"{days}{days_word} {time_str}"
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





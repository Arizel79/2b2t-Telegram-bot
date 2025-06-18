import requests
from datetime import datetime
from typing import Dict, Any

class Api2b2tError(Exception):
    pass

def get_2b2t_tablist():
    try:
        data = requests.get("https://api.2b2t.vc/tablist")
        data = data.json()
        data["header"] = data["header"].replace("\n\n", "\n")[1:-1]
        return data
    except requests.exceptions.ConnectionError:
        print("Connection Error")
        raise Api2b2tError("Ошибка запроса к API")

def get_2b2t_info():
    try:
        data = requests.get("https://api.2b2t.vc/queue")
        data = data.json()
        online = requests.get("https://api.mcsrvstat.us/3/2b2t.org").json()["players"]["online"]
        data["online"] = online
        return data
    except requests.exceptions.ConnectionError:
        print("Connection Error")
        raise Api2b2tError("Ошибка запроса к API")

def get_player_stats(player: str = None, uuid: str = None) -> Dict[str, Any] or None:
    assert (not player  is None) or (not uuid is None)

    if not player is None:
        is_uuid = False
        url = f"https://api.2b2t.vc/stats/player?playerName={player}"
    elif not uuid is None:
        is_uuid = True
        url = f"https://api.2b2t.vc/stats/player?uuid={uuid}"
    else:
        raise Api2b2tError("player and uuid are invalid")

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
        raise Api2b2tError(f"code: {response.status_code}")

    return result


def seconds_to_hms(seconds: int) -> str:
    """
    Конвертирует секунды в формат [ДНИд]ЧЧ:ММ:СС

    :param seconds: Количество секунд (int)
    :return: Строка в формате [ДНИд]HH:MM:SS
    """
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    if days > 0:
        time_str = f"{days}д {time_str}"
    return time_str


def parse_iso_time(iso_string: str) -> datetime:
    """Парсер без зависимостей"""
    try:
        # Удаляем наносекунды и временную зону
        if '.' in iso_string:
            iso_string = iso_string.split('.')[0]
        if '+' in iso_string:
            iso_string = iso_string.split('+')[0]
        if 'Z' in iso_string:
            iso_string = iso_string.split('Z')[0]

        return datetime.fromisoformat(iso_string)
    except ValueError as e:
        raise ValueError(f"Не удалось распарсить время: {e}")


def format_iso_time(iso_string: str) -> str:
    """Форматирование без зависимостей"""
    try:
        dt = parse_iso_time(iso_string)
        return dt.strftime('%H:%M.%S %d.%m.%Y')
    except ValueError as e:
        return f"Ошибка: {str(e)}"





if __name__ == '__main__':
    from pprint import pprint
    pprint(get_2b2t_info())




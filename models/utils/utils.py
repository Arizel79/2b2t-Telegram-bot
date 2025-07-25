import re


def is_valid_minecraft_uuid(uuid):
    # Проверка формата UUID (с дефисами или без)
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$', re.IGNORECASE)
    return bool(uuid_pattern.match(uuid))


def is_valid_minecraft_username(username):
    # Длина от 3 до 16 символов
    if len(username) < 3 or len(username) > 16:
        return False

    # Разрешены только буквы, цифры и _
    allowed_chars = re.compile(r'^[a-zA-Z0-9_]+$')
    if not allowed_chars.match(username):
        return False

    return True


import aiohttp
import asyncio


async def get_uuid_from_username(username):
    """Получает UUID игрока по его никнейму (асинхронно)."""
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("id")  # UUID без дефисов
            else:
                print(f"Ошибка {response.status}: Игрок не найден или сервер недоступен")
                return None


async def get_username_from_uuid(uuid):
    """Получает текущий никнейм игрока по его UUID (асинхронно)."""
    # Если UUID без дефисов, добавляем их
    if '-' not in uuid:
        formatted_uuid = f"{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}"
    else:
        formatted_uuid = uuid

    url = f"https://sessionserver.mojang.com/session/minecraft/profile/{formatted_uuid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("name")
            else:
                print(f"Ошибка {response.status}: UUID не найден или сервер недоступен")
                return None


async def main():
    # Пример 1: Получаем UUID по нику
    username = "Notch"
    uuid = await get_uuid_from_username(username)
    if uuid:
        print(f"UUID игрока {username}: {uuid}")

        # Пример 2: Получаем ник по UUID (должен совпадать, если игрок не менял)
        current_username = await get_username_from_uuid(uuid)
        if current_username:
            print(f"Текущий никнейм UUID {uuid}: {current_username}")
        else:
            print("Не удалось получить никнейм по UUID")
    else:
        print("Игрок не найден")


if __name__ == '__main__':
    asyncio.run(main())

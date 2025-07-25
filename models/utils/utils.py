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
def get_namemc_profile(player):
    return f"https://namemc.com/{player}"

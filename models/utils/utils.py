import re
import logging
from sys import stdout
def is_valid_minecraft_uuid(uuid):
    # Проверка формата UUID (с дефисами или без)
    uuid_pattern = re.compile(r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$', re.IGNORECASE)
    return bool(uuid_pattern.match(uuid))


def is_valid_minecraft_username(username):
    if type(username) != str:
        return False
    if len(username) < 3 or len(username) > 16:
        return False

    allowed_chars = re.compile(r'^[a-zA-Z0-9_]+$')
    if not allowed_chars.match(username):
        return False

    return True

def setup_logger(name, log_file, level=logging.INFO):
    """Настройка логгера"""
    logger = logging.getLogger(name)

    if not level is None:
        logger.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

        # To file
        if not log_file is None:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # To console
        console_handler = logging.StreamHandler(stdout)
        console_handler.setFormatter(console_formatter)


        logger.addHandler(console_handler)

    return logger





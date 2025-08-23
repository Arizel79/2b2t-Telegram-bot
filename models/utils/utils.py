import re
import logging
import io
import sys
# Установите UTF-8 кодировку для stdout/stderr
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')



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


class SafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            # Принудительно кодируем в UTF-8 и игнорируем ошибки
            if hasattr(self.stream, 'buffer'):
                # Для бинарных потоков
                self.stream.buffer.write(msg.encode('utf-8', errors='ignore') + self.terminator.encode('utf-8'))
            else:
                # Для текстовых потоков
                self.stream.write(msg + self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # Если все равно ошибка, пишем без эмодзи
            clean_msg = re.sub(r'[^\x00-\x7F]+', '', msg)
            self.stream.write(clean_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logger(name, log_file, level=logging.INFO):
    """Настройка логгера"""
    logger = logging.getLogger(name)

    if not level is None:
        logger.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

        # To file
        if not log_file is None:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # To console
        console_handler = SafeStreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger





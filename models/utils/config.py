from dotenv import load_dotenv
import os


load_dotenv()

LOGS_FILE = "../../log.log"


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", ""))
LOGS_GROUP_ID = int(os.getenv("LOGS_GROUP_ID", ""))
SEND_LOGS = int(os.getenv("SEND_LOGS", "0"))
LOGS_GROUP_THREAD_ID = int(os.getenv("LOGS_GROUP_THREAD_ID", "0"))

assert TELEGRAM_BOT_TOKEN != "", "TELEGRAM_BOT_TOKEN is invalid"



CHAT_SERACH_MODE = "chat_search"
PLAYER_STATS_MODE = "player_search"

CALLBACK_CHAT_SEARCH = "chat_s"
CALLBACK_MESSAGES_FROM_PLAYER = "msgs_pl"
CALLBACK_TABLIST = "tablist"

SEARCH_PAGE_SIZE = 16
SEARCH_FROM_PLAYER_PAGE_SIZE = 30
TABLIST_PAGE_SIZE = 80

import json

from dotenv import load_dotenv
import os

import json
from pathlib import Path
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n.middleware import SimpleI18nMiddleware


TRACKING_PAGE_SIZE = 5
# # Базовые настройки
# BASE_DIR = Path(__file__).parent
# LOCALES_DIR = 'locales'
#
# # Загрузка конфига из JSON
# with open("config.json", "r") as f:
#     CONFIGS = json.load(f)
#
# TELEGRAM_BOT_TOKEN = CONFIGS["configs"]["telegram_bot_token"]
# ADMIN_ID = CONFIGS["configs"]["admin_telegram_id"]
#
# # Настройка i18n
# i18n = I18n(path=LOCALES_DIR, default_locale="en", domain="messages")
# i18n_middleware = SimpleI18nMiddleware(i18n=i18n)
#
# # Алиас для gettext
# _ = i18n.gettext


load_dotenv()

CONFIGS = json.load(open("config.json", "r"))

TELEGRAM_BOT_TOKEN = CONFIGS["configs"]["telegram_bot_token"]
ADMIN_ID =  CONFIGS["configs"]["admin_telegram_id"]

SEND_LOGS = CONFIGS["send_bot_logs"]["bot_logs"]
LOGS_GROUP_ID= CONFIGS["send_bot_logs"]["chat_id"]
LOGS_GROUP_THREAD_ID = CONFIGS["send_bot_logs"]["supergroup_thread_id"]

LIVE_EVENTS = CONFIGS["send_live_events_to_telegram_chat"]
MAX_TIME_BETWEEN_SENDING_TO_MY_CHATS = 30
MAX_EVENTS_IN_QUEUE = 8

assert TELEGRAM_BOT_TOKEN != "", "TELEGRAM_BOT_TOKEN is invalid"


CHAT_SERACH_MODE = "chat_search"
PLAYER_STATS_MODE = "player_search"

CALLBACK_CHAT_SEARCH = "chat_s"
CALLBACK_MESSAGES_FROM_PLAYER = "msgs_pl"
CALLBACK_TABLIST = "tablist"
CALLBAK_VIEW_PLAYER_STATS = "view_pl_stats"
CALLBACK_PLAYTIME_TOP = "pt_top"
CALLBACK_KILLS_TOP_MONTH = "kls_top_mh"

SEARCH_PAGE_SIZE = 16
SEARCH_FROM_PLAYER_PAGE_SIZE = 16
SEARCH_FROM_PLAYER_PAGE_SIZE_IN_CAPTION = 8
CHAT_HISTORY_PAGE_SIZE = 10
TABLIST_PAGE_SIZE = 80
PLAYTIME_TOP_PAGE_SIZE = 25
KILLS_TOP_MONTH_PAGE_SIZE = 25


LANG_CODES = ["en", "ru"]
DEFAULT_LANG_CODE = "en"

URL_2B2T_LOGO_INLINE = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Old_2b2t_logo.svg/2048px-Old_2b2t_logo.svg.png"

CHAT_LIVE_EVENTS_LINK = "https://t.me/+L0TprIr8zmY3MDBi"
import json

from dotenv import load_dotenv
import os


load_dotenv()

configs = json.load(open("config.json", "r"))

TELEGRAM_BOT_TOKEN = configs["configs"]["telegram_bot_token"]
ADMIN_ID =  configs["configs"]["admin_telegram_id"]

SEND_LOGS = configs["send_bot_logs"]["bot_logs"]
LOGS_GROUP_ID= configs["send_bot_logs"]["chat_id"]
LOGS_GROUP_THREAD_ID = configs["send_bot_logs"]["supergroup_thread_id"]

LIVE_EVENTS = configs["send_live_events_to_telegram_chat"]
MAX_TIME_BETWEEN_SENDING_TO_MY_CHATS = configs["max_time_between_sending_to_my_chats"]
MAX_EVENTS_IN_QUEUE = configs["max_events_in_queue"]

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
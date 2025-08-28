from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums.chat_type import ChatType
from aiogram.types import *

from models.utils.config import *

async def get_reply_kbd(self, user_id, chat_type):
    if chat_type == ChatType.PRIVATE:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=await self.get_translation(user_id, "get2b2tinfo")),
                    KeyboardButton(text=await self.get_translation(user_id, "getPlayerStats"))
                ],
                [
                    KeyboardButton(text=await self.get_translation(user_id, "searchChat")),
                    KeyboardButton(text=await self.get_translation(user_id, "getTablist"))
                ],
                [
                    KeyboardButton(text=await self.get_translation(user_id, "getPlaytimeTop")),
                    KeyboardButton(text=await self.get_translation(user_id, "getKillsTopMonth"))

                ],
                [
                    KeyboardButton(text=await self.get_translation(user_id, "getTrackingList")),
                    KeyboardButton(text=await self.get_translation(user_id, "getSettings"))

                ],
                [

                    KeyboardButton(text=await self.get_translation(user_id, "sendDonate"))

                ]
            ],

            resize_keyboard=True,  # автоматическое изменение размера кнопок
            one_time_keyboard=False,  # скрыть клавиатуру после нажатия
            input_field_placeholder=""  # подсказка в поле ввода
        )
        return keyboard


async def get_reply_keyboard_by_message(self, message: Message):
    return await self.get_reply_kbd(message.from_user.id, message.chat.id)


async def get_markup_chat_search(self, query_id, user_id=None):
    builder = InlineKeyboardBuilder()
    q_data = await self.db.get_saved_state(query_id)

    if not q_data.get('pages_count') is None and q_data.get('pages_count') != 0:
        if q_data['page'] > 1:
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "startPage"),
                                     callback_data=f"{CALLBACK_CHAT_SEARCH} {query_id} goto 1"))
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "backPage"),
                                     callback_data=f"{CALLBACK_CHAT_SEARCH} {query_id} goto {q_data['page'] - 1}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_CHAT_SEARCH} none")
                )
        builder.add(
            InlineKeyboardButton(text=f"{q_data['page']} / {q_data['pages_count']}",
                                 callback_data=f"{CALLBACK_CHAT_SEARCH} {query_id} info"))
        if q_data['page'] < q_data["pages_count"]:

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "nextPage"),
                                     callback_data=f"{CALLBACK_CHAT_SEARCH} {query_id} goto {q_data['page'] + 1}")
            )

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "endPage"),
                                     callback_data=f"{CALLBACK_CHAT_SEARCH} {query_id} goto {q_data['pages_count']}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_CHAT_SEARCH} none")
                )
        builder.adjust(5)
        return builder.as_markup()


async def get_markup_search_messages_from_player(self, query_id):
    builder = InlineKeyboardBuilder()
    q_data = await self.db.get_saved_state(query_id)
    if not q_data.get('pages_count') is None and q_data.get('pages_count') != 0:

        if q_data['page'] > 1:
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "startPage"),
                                     callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} goto 1"))
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "backPage"),
                                     callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} goto {q_data['page'] - 1}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} none")
                )
        builder.add(
            InlineKeyboardButton(text=f"{q_data['page']} / {q_data['pages_count']}",
                                 callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} info"))
        if q_data['page'] < q_data["pages_count"]:

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "nextPage"),
                                     callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} goto {q_data['page'] + 1}")
            )

            builder.add(
                InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "endPage"),
                                     callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} goto {q_data['pages_count']}"))
        else:
            for i in range(2):
                builder.add(
                    InlineKeyboardButton(text=" ",
                                         callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} none")
                )
    if q_data.get("via_player_stats", False):
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(q_data["user_id"], "menuBack"),
                                 callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} {CALLBAK_VIEW_PLAYER_STATS}")
        )
    builder.adjust(5)

    return builder.as_markup()


async def get_markup_tablist(self, query_id):
    builder = InlineKeyboardBuilder()
    saved_state = await self.db.get_saved_state(query_id)
    assert saved_state["type"] == "tablist"
    user_id = str(saved_state["user_id"])
    current_page = int(saved_state["page"])
    page_size = int(saved_state["page_size"])
    pages_count = await self.api_2b2t.get_2b2t_tablist_pages_count(page_size)

    if current_page > 1:
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "startPage"),
                                 callback_data=f"{CALLBACK_TABLIST} {query_id} goto 1"))
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "backPage"),
                                 callback_data=f"{CALLBACK_TABLIST} {query_id} goto {current_page - 1}"))
    else:
        for i in range(2):
            builder.add(
                InlineKeyboardButton(text=" ",
                                     callback_data=f"{CALLBACK_TABLIST} none")
            )
    builder.add(
        InlineKeyboardButton(text=f"{current_page} / {pages_count}",
                             callback_data=f"{CALLBACK_TABLIST} {query_id} info"))
    if current_page < pages_count:

        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "nextPage"),
                                 callback_data=f"{CALLBACK_TABLIST} {query_id} goto {current_page + 1}")
        )

        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "endPage"),
                                 callback_data=f"{CALLBACK_TABLIST} {query_id} goto {pages_count}"))
    else:
        for i in range(2):
            builder.add(
                InlineKeyboardButton(text=" ",
                                     callback_data=f"{CALLBACK_TABLIST} none")
            )
    builder.adjust(5)
    return builder.as_markup()


async def get_nav_buttons(self, user_id, callback_perfix, current_page, page_size, pages_count, query_id=None):
    if not query_id is None:
        data = query_id
    else:
        data = ""
    btns = []
    if current_page > 1:
        btns.append(
            InlineKeyboardButton(text=await self.get_translation(user_id, "startPage"),
                                 callback_data=f"{callback_perfix} {data} goto 1"))
        btns.append(
            InlineKeyboardButton(text=await self.get_translation(user_id, "backPage"),
                                 callback_data=f"{callback_perfix} {data} goto {current_page - 1}"))
    else:
        for i in range(2):
            btns.append(
                InlineKeyboardButton(text=" ",
                                     callback_data=f"{callback_perfix} none")
            )
    btns.append(
        InlineKeyboardButton(text=f"{current_page} / {pages_count}",
                             callback_data=f"{callback_perfix} {data} info"))
    if current_page < pages_count:
        btns.append(
            InlineKeyboardButton(text=await self.get_translation(user_id, "nextPage"),
                                 callback_data=f"{callback_perfix} {data} goto {current_page + 1}")
        )

        btns.append(
            InlineKeyboardButton(text=await self.get_translation(user_id, "endPage"),
                                 callback_data=f"{callback_perfix} {data} goto {pages_count}"))
    else:
        for i in range(2):
            btns.append(
                InlineKeyboardButton(text=" ",
                                     callback_data=f"{callback_perfix} none")
            )
    return btns


async def get_nav_markup(self, query_id):
    builder = InlineKeyboardBuilder()
    saved_state = await self.db.get_saved_state(query_id)
    user_id = str(saved_state["user_id"])
    current_page = int(saved_state["page"])
    page_size = int(saved_state["page_size"])

    if saved_state["type"] == "tablist":
        callback_ = CALLBACK_TABLIST
        pages_count = await self.api_2b2t.get_2b2t_tablist_pages_count(page_size)
    elif saved_state["type"] == "playtime_top":
        callback_ = CALLBACK_PLAYTIME_TOP
        pages_count = await self.api_2b2t.get_playtime_top_pages_count(page_size)

    elif saved_state["type"] == "kills_top_month":
        callback_ = CALLBACK_KILLS_TOP_MONTH
        pages_count = await self.api_2b2t.get_kills_top_month_pages_count(page_size)
    else:
        assert False, f"Unknown saved state type: {saved_state['type']}"

    if current_page > 1:
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "startPage"),
                                 callback_data=f"{callback_} {query_id} goto 1"))
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "backPage"),
                                 callback_data=f"{callback_} {query_id} goto {current_page - 1}"))
    else:
        for i in range(2):
            builder.add(
                InlineKeyboardButton(text=" ",
                                     callback_data=f"{callback_} none")
            )
    builder.add(
        InlineKeyboardButton(text=f"{current_page} / {pages_count}",
                             callback_data=f"{callback_} {query_id} info"))
    if current_page < pages_count:

        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "nextPage"),
                                 callback_data=f"{callback_} {query_id} goto {current_page + 1}")
        )

        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "endPage"),
                                 callback_data=f"{callback_} {query_id} goto {pages_count}"))
    else:
        for i in range(2):
            builder.add(
                InlineKeyboardButton(text=" ",
                                     callback_data=f"{callback_} none")
            )
    builder.adjust(5)
    return builder.as_markup()


async def get_markup_playtime_top(self, query_id):
    builder = InlineKeyboardBuilder()
    saved_state = await self.db.get_saved_state(query_id)
    assert saved_state["type"] == "playtime_top"
    user_id = str(saved_state["user_id"])
    current_page = int(saved_state["page"])
    page_size = int(saved_state["page_size"])
    pages_count = await self.api_2b2t.get_2b2t_tablist_pages_count(page_size)

    if current_page > 1:
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "startPage"),
                                 callback_data=f"{CALLBACK_PLAYTIME_TOP} {query_id} goto 1"))
        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "backPage"),
                                 callback_data=f"{CALLBACK_PLAYTIME_TOP} {query_id} goto {current_page - 1}"))
    else:
        for i in range(2):
            builder.add(
                InlineKeyboardButton(text=" ",
                                     callback_data=f"{CALLBACK_PLAYTIME_TOP} none")
            )
    builder.add(
        InlineKeyboardButton(text=f"{current_page} / {pages_count}",
                             callback_data=f"{CALLBACK_PLAYTIME_TOP} {query_id} info"))
    if current_page < pages_count:

        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "nextPage"),
                                 callback_data=f"{CALLBACK_PLAYTIME_TOP} {query_id} goto {current_page + 1}")
        )

        builder.add(
            InlineKeyboardButton(text=await self.get_translation(user_id, "endPage"),
                                 callback_data=f"{CALLBACK_TABLIST} {query_id} goto {pages_count}"))
    else:
        for i in range(2):
            builder.add(
                InlineKeyboardButton(text=" ",
                                     callback_data=f"{CALLBACK_TABLIST} none")
            )
    builder.adjust(5)
    return builder.as_markup()

async def get_player_stats_keyboard(self, user_id, query_id):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=await self.get_translation(user_id, "getPlayerChatMessagesViaPlayerStats"),
                             callback_data=f"{CALLBACK_MESSAGES_FROM_PLAYER} {query_id} goto 1"))
    return builder.as_markup()

def get_lang_keyboard(self, user_id):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🇬🇧 English", callback_data=f"setlang {user_id} en"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data=f"setlang {user_id} ru")
    )
    builder.adjust(2)
    return builder.as_markup()

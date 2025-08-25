from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from models.utils.config import *

async def handler_callback_settings(self, callback: CallbackQuery):
    user_id = callback.from_user.id
    assert callback.data.startswith("settings")
    lst = callback.data.split()
    if len(lst) == 2:
        if lst[1] == "editlang":
            builder = InlineKeyboardBuilder()
            builder.add(
                InlineKeyboardButton(text=self.translator.translations["ru"]["langName"],
                                     callback_data=f"settings editlang ru"),
                InlineKeyboardButton(text=self.translator.translations["en"]["langName"],
                                     callback_data=f"settings editlang en"),
                InlineKeyboardButton(text=await self.get_translation(user_id, "menuBack"),
                                     callback_data=f"settings mainmenu")
            )
            builder.adjust(1)
            await callback.message.edit_text(await self.get_translation(user_id, "settingsEditLang"),
                                             reply_markup=builder.as_markup())
        elif lst[1] == "mainmenu":
            await callback.message.edit_text(await self.get_translation(user_id, "settingsMenuTitle"),
                                             reply_markup=await self.get_settings_keyboard(user_id))
        elif lst[1] == "help":
            builder = InlineKeyboardBuilder()
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "menuBack"),
                                     callback_data=f"settings mainmenu")
            )
            builder.adjust(1)
            await callback.message.edit_text(await self.get_translation(user_id, "helpMessage", self.bot_username, CHAT_LIVE_EVENTS_LINK,),
                                             reply_markup=builder.as_markup())
    elif len(lst) == 3:
        if lst[1] == "editlang":
            lang = lst[2]
            if lang not in ["en", "ru"]:
                lang = "en"
            await self.db.update_lang(user_id, lang)

            builder = InlineKeyboardBuilder()
            builder.add(
                InlineKeyboardButton(text=await self.get_translation(user_id, "menuBack"),
                                     callback_data=f"settings mainmenu")
            )
            builder.adjust(1)

            await callback.message.edit_text(await self.get_translation(user_id, "settingsLangEdited",
                                                                        await self.get_translation(
                                                                            user_id, "langName")),
                                             reply_markup=builder.as_markup())

            await self.bot.send_message(user_id, await self.get_translation(user_id, "startMessage",
                                                                            callback.from_user.first_name),
                                        reply_markup=await self.get_reply_kbd(user_id, callback.message.chat.type))

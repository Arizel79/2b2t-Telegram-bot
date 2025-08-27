from aiogram import types, F
import aiogram
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from models.utils.utils import is_valid_minecraft_username, is_valid_minecraft_uuid
from models.utils.config import *
import math


async def handler_tracking_callback(self, callback: types.CallbackQuery):
    """Обработка callback для управления отслеживанием"""
    await self.on_event(callback)

    data = callback.data.split()
    if not data:
        return

    command = data[0]

    if command == "tracking_list":
        if data[1] == "goto":
            # Показать список отслеживаний с пагинацией
            page = int(data[2]) if len(data) > 2 else 0
            await show_tracking_list(self, callback, page)
        elif data[1] == "none":
            await callback.answer()
            return
        elif data[1] == "info":
            await callback.answer()
            return

    elif command == "tracking_manage":
        # Показать управление конкретным отслеживанием
        tracking_id = int(data[1]) if len(data) > 1 else None
        if tracking_id:
            await show_tracking_management(self, callback, tracking_id)

    elif command == "tracking_toggle":
        # Переключение настройки уведомлений
        if len(data) >= 3:
            tracking_id = int(data[1])
            setting_type = data[2]
            await toggle_tracking_setting(self, callback, tracking_id, setting_type)

    elif command == "tracking_importance":
        # Изменение важности уведомлений
        if len(data) >= 2:
            tracking_id = int(data[1])
            await cycle_tracking_importance(self, callback, tracking_id)

    elif command == "tracking_delete":
        # Удаление отслеживания
        if len(data) >= 2:
            tracking_id = int(data[1])
            await delete_tracking(self, callback, tracking_id)

    elif command == "tracking_back":
        # Возврат к списку отслеживаний
        page = int(data[1]) if len(data) > 1 else 0
        await show_tracking_list(self, callback, page)


async def show_tracking_list(self, callback: types.CallbackQuery, page: int = 1):
    """Показать список отслеживаний с пагинацией"""
    # Получаем все отслеживания пользователя
    user_id = callback.from_user.id
    trackings = await self.db.get_user_trackings(user_id)

    if not trackings:
        text = await self.get_translation(user_id, "noTrackings")
        builder = InlineKeyboardBuilder()
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        return

    # Рассчитываем пагинацию
    total_pages = math.ceil(len(trackings) / TRACKING_PAGE_SIZE)
    if page  > total_pages:
        page = total_pages
    if page <= 0:
        page = 1

    # Получаем отслеживания для текущей страницы
    start_idx = (page - 1) * TRACKING_PAGE_SIZE
    end_idx = start_idx + TRACKING_PAGE_SIZE
    page_trackings = trackings[start_idx:end_idx]

    # Создаем текст сообщения
    text = await self.get_translation(user_id, "trackingListHeader")

    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()

    # Кнопки для каждого отслеживания на странице
    for tracking in page_trackings:
        status = "☑️" if tracking.is_active else "❌"
        builder.row(InlineKeyboardButton(
            text=f"{status} ⚙️ {tracking.player_username}",
            callback_data=f"tracking_manage {tracking.id}"
        ), width=1)

    # Размещаем кнопки игроков по одной в ряд


    # Добавляем навигацию, если есть больше одной страницы
    if total_pages > 1:
        # Добавляем разделитель

        # Добавляем кнопки навигации
        builder.row(*await self.get_nav_buttons(user_id=callback.from_user.id,
                                              callback_perfix="tracking_list", current_page=page,
                                              page_size=TRACKING_PAGE_SIZE, pages_count=total_pages), width=5)
    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except aiogram.exceptions.TelegramBadRequest as e:
        self.logger.exception(e)
        if "message is not modified" in str(e):
            return
        await callback.message.reply(text, reply_markup=builder.as_markup())


async def show_tracking_management(self, callback: types.CallbackQuery, tracking_id: int):
    """Показать меню управления отслеживанием"""
    # Получаем информацию о странице для возврата
    page = await get_tracking_page(self, callback.from_user.id, tracking_id)

    tracking = await self.db.get_tracking_by_id(tracking_id, callback.from_user.id)

    if not tracking:
        await callback.answer(await self.get_translation(callback.from_user.id, "trackingNotFound"))
        return

    builder = InlineKeyboardBuilder()

    # Кнопки включения/выключения уведомлений
    on, off = '✅', '❌'
    state_notify_messages = on if tracking.notify_messages else off
    state_notify_connections = on if tracking.notify_connections else off
    state_notify_deaths = on if tracking.notify_deaths else off
    state_notify_kills = on if tracking.notify_kills else off
    builder.add(InlineKeyboardButton(
        text=await self.get_translation(callback.from_user.id, "isTracingPlayerMessages", state_notify_messages),
        callback_data=f"tracking_toggle {tracking.id} messages"
    ))
    builder.add(InlineKeyboardButton(
        text=await self.get_translation(callback.from_user.id, "isTracingPlayerConnections", state_notify_connections),
        callback_data=f"tracking_toggle {tracking.id} connections"
    ))
    builder.add(InlineKeyboardButton(
        text=await self.get_translation(callback.from_user.id, "isTracingPlayerDeaths", state_notify_deaths),
        callback_data=f"tracking_toggle {tracking.id} deaths"
    ))
    builder.add(InlineKeyboardButton(
        text=await self.get_translation(callback.from_user.id, "isTracingPlayerKills", state_notify_kills),
        callback_data=f"tracking_toggle {tracking.id} kills"
    ))

    importance_text = [await self.get_translation(callback.from_user.id, "trackingNotifyWithoutSound"),
                       await self.get_translation(callback.from_user.id, "trackingNotifyWithSound"),
                       await self.get_translation(callback.from_user.id, "trackingNotifyWithMention")]
    builder.add(InlineKeyboardButton(
        text=importance_text[tracking.importance],
        callback_data=f"tracking_importance {tracking.id}"
    ))

    builder.add(InlineKeyboardButton(
        text=await self.get_translation(callback.from_user.id, "trackingStop"),
        callback_data=f"tracking_delete {tracking.id}"
    ))

    builder.add(InlineKeyboardButton(
        text=await self.get_translation(callback.from_user.id, "trackingBackToLIst"),
        callback_data=f"tracking_list goto {page}"
    ))
    builder.adjust(1)

    text = await self.get_translation(callback.from_user.id, "trackingEditHeader", tracking.player_username)
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


async def toggle_tracking_setting(self, callback: types.CallbackQuery, tracking_id: int, setting_type: str):
    """Переключение настройки уведомлений"""
    tracking = await self.db.get_tracking_by_id(tracking_id, callback.from_user.id)

    if not tracking:
        await callback.answer(await self.get_translation(callback.from_user.id, "trackingNotFound"))
        return

    # Определяем какое поле обновлять
    setting_map = {
        'messages': 'notify_messages',
        'connections': 'notify_connections',
        'deaths': 'notify_deaths',
        'kills': 'notify_kills'
    }

    if setting_type not in setting_map:
        await callback.answer(await self.get_translation(callback.from_user.id, "trackingOptionError"))
        return

    field_name = setting_map[setting_type]
    current_value = getattr(tracking, field_name)

    # Обновляем значение
    success = await self.db.update_player_tracking(tracking_id, **{field_name: not current_value})

    if success:
        await callback.answer(await self.get_translation(callback.from_user.id, "trackingOptionUpdated"))
        # Получаем страницу для возврата
        page = await get_tracking_page(self, callback.from_user.id, tracking_id)
        # Обновляем меню управления
        await show_tracking_management(self, callback, tracking_id)
    else:
        await callback.answer(await self.get_translation(callback.from_user.id, "trackingOptionError"))


async def cycle_tracking_importance(self, callback: types.CallbackQuery, tracking_id: int):
    """Циклическое изменение важности уведомлений"""
    tracking = await self.db.get_tracking_by_id(tracking_id, callback.from_user.id)

    if not tracking:
        await callback.answer(await self.get_translation(callback.from_user.id, "trackingNotFound"))
        return

    # Циклически меняем важность (0->1->2->0)
    new_importance = (tracking.importance + 1) % 3

    success = await self.db.update_player_tracking(tracking_id, importance=new_importance)

    if success:
        await callback.answer(await self.get_translation(callback.from_user.id, "trackingOptionUpdated"))
        # Получаем страницу для возврата
        page = await get_tracking_page(self, callback.from_user.id, tracking_id)
        # Обновляем меню управления
        await show_tracking_management(self, callback, tracking_id)
    else:
        await callback.answer(await self.get_translation(callback.from_user.id, "trackingOptionError"))


async def delete_tracking(self, callback: types.CallbackQuery, tracking_id: int):
    """Удаление отслеживания"""
    # Получаем страницу до удаления
    page = await get_tracking_page(self, callback.from_user.id, tracking_id)

    success = await self.db.delete_player_tracking(tracking_id)

    if success:
        await callback.answer(await self.get_translation(callback.from_user.id, "trackingOptionUpdated"))
        # Возвращаемся к списку на той же странице
        await show_tracking_list(self, callback, page)
    else:
        await callback.answer(await self.get_translation(callback.from_user.id, "trackingOptionError"))


async def get_tracking_page(self, user_id: int, tracking_id: int) -> int:
    """Получить номер страницы, на которой находится отслеживание"""
    trackings = await self.db.get_user_trackings(user_id)

    for i, tracking in enumerate(trackings):
        if tracking.id == tracking_id:
            return i // TRACKING_PAGE_SIZE

    return 0


# Добавляем обработчики в диспетчер
def register_tracking_handlers(dp, bot_instance):
    """Регистрация обработчиков отслеживания"""
    dp.callback_query.register(
        lambda callback: handler_tracking_callback(bot_instance, callback),
        F.data.startswith("tracking_")
    )

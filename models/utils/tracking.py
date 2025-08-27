
class TrackingManager:
    def __init__(self, bot):
        self.bot = bot

    async def check_tracking_notifications(self, event):
        """Проверяем и отправляем уведомления об отслеживаемых событиях"""
        if event["type"] in ["chat_message", "death_message", "connection_message"]:
            player_username = event.get("playerName") or event.get("victimPlayerName") or event.get("playerName")
            player_uuid = event.get("playerUuid") or event.get("victimPlayerUuid") or event.get("playerUuid")

            if player_username:
                # Ищем всех, кто отслеживает этого игрока
                trackings = await self.bot.db.get_all_tracking_for_player(
                    player_username=player_username,
                    player_uuid=player_uuid
                )

                for tracking in trackings:
                    if tracking.is_active:
                        await self.send_tracking_notification(tracking, event)

    async def send_tracking_notification(self, tracking, event):
        """Отправляем уведомление об отслеживаемом событии"""
        try:
            user_id = tracking.user_id
            event_type = event["type"]

            # Проверяем, включено ли уведомление для этого типа события
            if (event_type == "chat_message" and not tracking.notify_messages or
                    event_type == "connection_message" and not tracking.notify_connections or
                    event_type == "death_message" and not tracking.notify_deaths):
                return

            # Форматируем сообщение
            if event_type == "chat_message":
                message = await self.bot.api_2b2t.format_chat_message(event, with_time=True)
                prefix = await self.bot.get_translation(tracking.user_id, "trackingNewPlayerNotify", "🔄", tracking.player_username)
            elif event_type == "connection_message":
                message = await self.bot.api_2b2t.format_connection_message(event, with_time=True)
                prefix = await self.bot.get_translation(tracking.user_id, "trackingNewPlayerNotify", "🔄", tracking.player_username)
            elif event_type == "death_message":
                message = await self.bot.api_2b2t.format_death_message(event, with_time=True)
                prefix = await self.bot.get_translation(tracking.user_id, "trackingNewPlayerNotify", "🔄", tracking.player_username)
            else:
                assert False, "Invalid event_type"

            if tracking.importance == 0:
                disable_notification = True
            else:
                disable_notification = False


            mention = f"<a href='tg://user?id={tracking.user_id}'>❗️</a> " if tracking.importance == 2 else ""

            # Отправляем уведомление
            text = f"{mention}{prefix}{message}"

            await self.bot.bot.send_message(user_id, text, disable_notification=disable_notification)
        finally:
            pass
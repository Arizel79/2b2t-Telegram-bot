from models.utils.utils import *


class TrackingManager:
    def __init__(self, bot):
        self.bot = bot
        self.logger = setup_logger("tracking", "logs/tracking.log", logging.INFO)

    async def check_tracking_notifications(self, event):
        """Проверяем и отправляем уведомления об отслеживаемых событиях"""
        if event["type"] in ["chat_message", "death_message", "connection_message"]:
            player_username = event.get("playerName") or event.get("victimPlayerName") or event.get("playerName")
            player_uuid = event.get("playerUuid") or event.get("victimPlayerUuid") or event.get("playerUuid")

            if player_username:
                # Ищем всех, кто отслеживает этого игрока
                trackings = await self.bot.db.get_all_tracking_for_player(
                    player_uuid=player_uuid
                )

                for tracking in trackings:
                    if tracking.is_active:
                        await self.send_tracking_notification(tracking, event)


    async def send_tracking_notification(self, tracking, event):
        """Отправляем уведомление об отслеживаемом событии"""
        try:
            user_id = tracking.user_id
            user_from_db = await self.bot.db.get_user(user_id)
            event_type = event["type"]

            # Проверяем, включено ли уведомление для этого типа события
            if (event_type == "chat_message" and not tracking.notify_messages or
                    event_type == "connection_message" and not tracking.notify_connections or
                    event_type == "death_message" and not tracking.notify_deaths):
                return
            self.logger.info(f"Notifying {await self.bot.get_printable_user(user_id=user_id)}")

            # Форматируем сообщение
            if event_type == "chat_message":
                message = await self.bot.api_2b2t.format_chat_message(event, with_time=True)
                prefix = await self.bot.get_translation(tracking.user_id, "trackingNewPlayerNotify", "🔄",
                                                        tracking.player_username)
            elif event_type == "connection_message":
                message = await self.bot.api_2b2t.format_connection_message(event, with_time=True)
                prefix = await self.bot.get_translation(tracking.user_id, "trackingNewPlayerNotify", "🔄",
                                                        tracking.player_username)
            elif event_type == "death_message":
                message = await self.bot.api_2b2t.format_death_message(event, with_time=True)
                prefix = await self.bot.get_translation(tracking.user_id, "trackingNewPlayerNotify", "🔄",
                                                        tracking.player_username)
            else:
                assert False, "Invalid event_type"

            if tracking.importance == 0:
                disable_notification = True
            else:
                disable_notification = False
            self.logger.info(f"{disable_notification=}")
            if user_from_db.username != "":
                mention = f"{user_from_db.username}\n\n" if tracking.importance == 2 else ""
            else:
                mention = ""

            # Отправляем уведомление
            text = f"{mention}{prefix}{message}"
            self.logger.info("Sending log")
            await self.bot.send_message_to_logs_chat(f"{await self.bot.get_printable_user(user_id=user_id)} player tracking: {text}")

            await self.bot.bot.send_message(user_id, text)
        except Exception as e:
            self.logger.error(f"Error in send_tracking_notification: {e}")
            self.logger.exception(e)
        finally:
            pass

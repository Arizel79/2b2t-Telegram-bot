import asyncio
import logging
import time
from aiogram.types import LinkPreviewOptions
from models.utils.utils import *
from models.utils.config import *


class LiveEventsManager:
    def __init__(self, bot):
        self.logger = setup_logger("live_events", "logs/live_events.log", logging.INFO)
        self.bot = bot
        self.my_live_events = LIVE_EVENTS
        self.queue_to_notify_users = asyncio.Queue()

        # Инициализируем индивидуальные очереди и настройки для каждого чата
        for chat_config in self.my_live_events:
            chat_config['queue'] = asyncio.Queue()
            chat_config['last_send_time'] = time.time()
            chat_config.setdefault('max_time_between_sending_to_my_chats', 200)
            chat_config.setdefault('max_events_in_queue', 10)


        self.tasks = [
            asyncio.create_task(self.task_live_event_chat_messages()),
            asyncio.create_task(self.task_live_event_connections()),
            asyncio.create_task(self.task_live_event_deaths()),
            *[asyncio.create_task(self.task_send_live_events_for_chat(chat_config))
              for chat_config in self.my_live_events]
        ]

    async def get_tasks(self):
        return self.tasks

    async def on_live_event(self, event):
        # Добавляем событие в очереди всех чатов, которые подписаны на этот тип события
        for chat_config in self.my_live_events:
            if event["type"] in chat_config["types"]:
                await chat_config['queue'].put(event)

        await self.queue_to_notify_users.put(event)

    async def on_chat_message(self, event):
        event["type"] = "chat_message"
        await self.on_live_event(event)
        self.logger.debug("chat message: " + await self.bot.api_2b2t.format_chat_message(event))

    async def on_death_message(self, event):
        event["type"] = "death_message"
        await self.on_live_event(event)
        self.logger.debug("death message: " + await self.bot.api_2b2t.format_death_message(event))

    async def on_connection_message(self, event):
        event["type"] = "connection_message"
        await self.on_live_event(event)
        self.logger.debug("connection message: " + await self.bot.api_2b2t.format_connection_message(event))


    async def send_events_for_chat(self, chat_config):
        lst = []
        while not chat_config['queue'].empty():
            event = await chat_config['queue'].get()
            lst.append(event)

        text = ""
        for ev in lst:
            if ev["type"] == "chat_message":
                text += f'{await self.bot.api_2b2t.format_chat_message(ev, only_time=True, to_tz=chat_config["timezone"], lang=chat_config["lang"])}\n\n'
            elif ev["type"] == "death_message":
                text += f'{await self.bot.api_2b2t.format_death_message(ev, only_time=True, to_tz=chat_config["timezone"], lang=chat_config["lang"])}\n\n'
            elif ev["type"] == "connection_message":
                text += f'{await self.bot.api_2b2t.format_connection_message(ev, only_time=True, to_tz=chat_config["timezone"], lang=chat_config["lang"])}\n\n'
            else:
                text += str(ev) + "\n\n"

        if text.strip() != "":
            self.logger.debug(f"Sending to my chat {chat_config['chat_id']}: \n{text}")
            await self.bot.bot.send_message(
                chat_config['chat_id'],
                text,
                message_thread_id=chat_config.get('logs_supergroup_thread_id'),
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )

    async def task_send_live_events_for_chat(self, chat_config):
        while True:
            try:
                now = time.time()
                queue_full = chat_config['queue'].qsize() >= chat_config['max_events_in_queue']
                timeout = (chat_config['last_send_time'] + chat_config['max_time_between_sending_to_my_chats'] < now)
                queue_not_empty = not chat_config['queue'].empty()

                send = queue_full or (timeout and queue_not_empty)

                if send:
                    self.logger.debug(
                        f"Preparing to send events to chat {chat_config['chat_id']}: "
                        f"queue_full={queue_full} ({chat_config['queue'].qsize()}); "
                        f"timeout={timeout}; queue_not_empty={queue_not_empty}"
                    )
                    await self.send_events_for_chat(chat_config)
                    chat_config['last_send_time'] = time.time()

            except Exception as e:
                self.logger.error(f"Error in task_send_live_events_for_chat for chat {chat_config['chat_id']}: {e}")
                self.logger.exception(e)

            await asyncio.sleep(0.1)

    async def task_live_event_chat_messages(self):
        while True:
            try:
                await self.bot.api_2b2t.listen_to_chats_feed(self.on_chat_message)
            except self.bot.api_2b2t.Api2b2tError as e:
                self.logger.error(f"Error in task_live_event_chat_messages: {e}")
                self.logger.exception(e)

    async def task_live_event_deaths(self):
        while True:
            try:
                await self.bot.api_2b2t.listen_to_deaths_feed(self.on_death_message)
            except self.bot.api_2b2t.Api2b2tError as e:
                self.logger.error(f"Error in task_live_event_deaths: {e}")
                self.logger.exception(e)

    async def task_live_event_connections(self):
        while True:
            try:
                await self.bot.api_2b2t.listen_to_connections_feed(self.on_connection_message)
            except self.bot.api_2b2t.Api2b2tError as e:
                self.logger.error(f"Error in task_live_event_connections: {e}")
                self.logger.exception(e)
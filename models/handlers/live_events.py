import asyncio
import logging
import queue
import time
from aiogram.types import LinkPreviewOptions

from models.utils.utils import *
from models.utils.config import *

class LiveEventsManager:
    MAX_TIME_BETWEEN_SENDING_TO_MY_CHATS = MAX_TIME_BETWEEN_SENDING_TO_MY_CHATS # sec
    MAX_EVENTS_IN_QUEUE = MAX_EVENTS_IN_QUEUE
    def __init__(self, bot):
        self.logger = setup_logger("live_events", "logs/live_events.log", logging.DEBUG)
        self.bot = bot
        self.tasks = [asyncio.create_task(self.task_live_event_chat_messages()),
                      asyncio.create_task(self.task_live_event_connections()),
                      asyncio.create_task(self.task_live_event_deaths()),
                      asyncio.create_task(self.task_send_live_events_to_my_telegram_chats())]
        self.my_live_events = LIVE_EVENTS
        self.queue = queue.Queue()

        self.last_time_send_events_to_my_telegram_chats = time.time()

    async def get_tasks(self):
        return self.tasks

    async def on_live_event(self, event):
        # self.logger.info(f"on_live_event: {event}")
        self.queue.put(event)

    async def on_chat_message(self, event):
        event["type"] = "chat_message"
        await self.on_live_event(event)
        self.logger.debug("chat message: "+ self.bot.api_2b2t.format_chat_message(event))

    async def on_death_message(self, event):
        event["type"] = "death_message"
        await self.on_live_event(event)
        self.logger.debug("death message: "+ self.bot.api_2b2t.format_death_message(event))
    async def on_connection_message(self, event):
        event["type"] = "connection_message"
        await self.on_live_event(event)
        # self.logger.info("connection message: "+ self.bot.api_2b2t.format_connection_message(event))

    async def send_live_events_from_queue_to_my_telegram_chats(self):
        lst = []
        while not self.queue.empty():
            event = self.queue.get_nowait()
            lst.append(event)

        for i in self.my_live_events:
            text = ""
            for ev in lst:
                if ev["type"] in i["types"]:
                    if ev["type"] == "chat_message":
                        text += f"{self.bot.api_2b2t.format_chat_message(ev)}\n\n"
                    elif ev["type"] == "death_message":
                        text += f"{self.bot.api_2b2t.format_death_message(ev)}\n\n"
                    elif ev["type"] == "connection_message":
                        text += f"{self.bot.api_2b2t.format_connection_message(ev)}\n\n"
                    else:
                        text += str(ev) + "\n\n"  # text = f"{self.bot.api_2b2t.format_chat_message(event, with_time=False)}"
            if text.strip() != "":
                self.logger.debug(f"Sending to my chat {i['chat_id']}: \n{text}")
                await self.bot.bot.send_message(i["chat_id"], text,
                                            message_thread_id=i["logs_supergroup_thread_id"],
                                            link_preview_options=LinkPreviewOptions(is_disabled=True))
        self.last_time_send_events_to_my_telegram_chats = time.time()

    async def task_send_live_events_to_my_telegram_chats(self):
        while True:

            try:
                now = time.time()
                queue_full = self.queue.qsize() >= self.MAX_EVENTS_IN_QUEUE
                # self.logger.info(f"{now=} {self.last_time_send_events_to_my_telegram_chats=} {self.MAX_TIME_BETWEEN_SENDING_TO_MY_CHATS=}")
                timeout = (self.last_time_send_events_to_my_telegram_chats + self.MAX_TIME_BETWEEN_SENDING_TO_MY_CHATS
                     < now)
                queue_not_empty = not self.queue.empty()
                # self.logger.info(f"Queue_full: {queue_full} ({self.queue.qsize()}); timeout: {timeout}; queue_not_empty: {queue_not_empty}")
                send = bool(queue_full or (timeout and queue_not_empty))

                if send:
                    await self.send_live_events_from_queue_to_my_telegram_chats()
            except Exception as e:
                self.logger.error(f"Error in task_send_live_events_to_my_telegram_chats: {e}")
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
                pass
                await self.bot.api_2b2t.listen_to_deaths_feed(self.on_death_message)
            except self.bot.api_2b2t.Api2b2tError as e:
                self.logger.error(f"Error in task_live_event_deaths: {e}")
                self.logger.exception(e)

    async def task_live_event_connections(self):
        while True:
            try:
                pass
                await self.bot.api_2b2t.listen_to_connections_feed(self.on_connection_message)
            except self.bot.api_2b2t.Api2b2tError as e:
                self.logger.error(f"Error in task_live_event_deaths: {e}")
                self.logger.exception(e)
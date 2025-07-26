class LiveEvents:
    def __init__(self, live_events, bot):
        self.bot = bot
        self.live_events = live_events
        self.tasks = [] # list of corutines




"""class LiveEvents:
    def __init__(self, live_events, bot):
        self.bot = bot
        self.live_events = live_events
        self.tasks = [self.live_event_chat_messages()] # list of corutin

    async def on_chat_msg(self, event):
        task = self.live_events[0]

        print("Новое сообщение в чате:", self.bot.api_2b2t.format_chat_message(event))
        if task["type"] == "chat_messages":
            text = f"{self.bot.api_2b2t.format_chat_message(event, with_time=False)}"
            await self.bot.bot.send_message(task["chat_id"], text,
                                        message_thread_id=task["logs_supergroup_thread_id"], )

    async def live_event_chat_messages(self):
        while True:
            try:
                await self.bot.api_2b2t.listen_to_chat_feed(self.on_chat_msg)
            except self.bot.api_2b2t.Api2b2tError as e:
                print(f"Api2b2tError: {e}")"""

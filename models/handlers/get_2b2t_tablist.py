from aiogram import types
from aiogram.utils.markdown import html_decoration as hd
from models.utils import api


async def handler_get_2b2t_tablist(self, message: types.Message, register_msg: bool = True) -> None:
    if register_msg:
        await self.on_event(message)
    if not await self.is_handler_msgs(message.from_user.id):
        return

    try:
        data = await self.api_2b2t.get_2b2t_tablist()
        answer = (
            '<b>Tablist of 2b2t</b>\n'
            f'<pre language="motd">lol</pre>\n'
            '\n'
        )

        await message.reply(answer)

    except self.api_2b2t.Api2b2tError as e:
        self.logger.error(f"Api2b2tError: {e}")
        await message.reply(await self.get_translation(message.from_user.id, "userError"))

    except Exception as e:
        self.logger.error(f"API Error: {type(e).__name__}: {e}")
        await message.reply(await self.get_translation(message.from_user.id, "error"))

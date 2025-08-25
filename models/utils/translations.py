import json
import logging

import requests

from models.utils.config import DEFAULT_LANG_CODE
from models.utils.utils import *


class Translator:
    def __init__(self, translations_file="translations.json", db=None):
        self.db = db
        self.logger = setup_logger("translator", "logs/translator.log", logging.INFO)
        with open(translations_file, "r", encoding="utf-8") as f:
            self.translations = json.loads(f.read())

        for i in self.translations.keys():
            try:
                data = requests.get(f"https://raw.githubusercontent.com/Arizel79/Arizel79/refs/heads/main/donate/{i}/donate_telegram.html")
                donate_text = data.text
            finally:
                pass
            self.translations[i]["donateText"] = donate_text

    async def get_translation(self, user_id: int, what: str, *format_args) -> str:
        try:
            data = await self.db.get_user_stats(user_id)
            lang = data["lang"]
        except KeyError:
            self.logger.error(f"Getting lang KeyError user_id={user_id}; user_data={data}")
            lang = DEFAULT_LANG_CODE
        return await self.get_get_translation_by_lang(lang, what, *format_args)

    async def get_get_translation_by_lang(self, lang, what: str, *format_args):
        try:
            return self.translations[lang][what].format(*format_args)
        except KeyError as e:
            self.logger.error(f"Error in get_get_translation_by_lang: {e}")
            self.logger.exception(e)
            error = f"Translation error: '{what}' NOT FOUND (KeyError) lang={lang}"

            return error
        except IndexError as e:
            self.logger.error(f"Error in get_get_translation_by_lang: {e}")
            self.logger.exception(e)
            error = f"Translation error: '{what}' translation format_args not correct lang={lang}, format_args={format_args}"
            print(error)
            return error
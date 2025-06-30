import json
import requests

class Translator:
    def __init__(self, translations_file="translations.json", db=None):
        self.db = db
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
            print(f"TRANSLATION KeyError id={user_id}", data)
            return


        try:
            return self.translations[lang][what].format(*format_args)
        except KeyError:
            error = f"Error.\n\n KeyError(translation NOT FOUND) lang={lang}, what={what} !!!"
            print(error)
            return error
        except IndexError:
            error = f"Error.\n\n IndexError(translation format_args not correct N) lang={lang}, what={what}, format_args={format_args} !!!"
            print(error)
            return error

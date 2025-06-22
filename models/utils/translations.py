import json

class Translator:
    def __init__(self, translations_file="translations.json", db=None):
        self.db = db
        with open(translations_file, "r", encoding="utf-8") as f:
            self.translations = json.loads(f.read())

    async def get_translation(self, user_id: int, what: str, *format_args) -> str:
        data = await self.db.get_user_stats(user_id)
        lang = data["lang"]
        try:
            return self.translations[lang][what].format(*format_args)
        except KeyError:
            error = f"!!! KeyError(translation NOT FOUND) lang={lang}, what={what} !!!"
            print(error)
            return error
        except IndexError:
            error = f"!!! IndexError(translation format_args not correct N) lang={lang}, what={what}, format_args={format_args} !!!"
            print(error)
            return error

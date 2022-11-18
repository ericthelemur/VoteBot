from pathlib import Path

import yaml


class Config:
    def __init__(self, filepath):
        with open(filepath) as f:
            parsed = yaml.full_load(f).get("config")

        self.DISCORD_TOKEN: str = parsed.get("discord_token")
        self.PREFIX: str = parsed.get("prefix")

        self.DATABASE_CONNECTION: str = parsed.get("database_connection")
        self.BOT_SECRET_KEY: str = parsed.get("bot_secret_key")
        self.UNICODE_NORMALISATION_FORM: str = "NFKD"

        self.ADMIN_ROLE_IDS: list[int] = parsed.get("admin_role_ids")


CONFIG = Config("config.yaml")

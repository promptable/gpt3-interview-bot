"""Settings and secrets for the project.

Loads secrets from .env.secrets file.

Usage:
    from settings import Settings
    cfg = Settings.from_env_file(
        secrets_file_path,
        disk_cache_dir="/tmp/disk_cache2",
        etc..
    )
    print(cfg.openai_api_key)
"""
import os

import dotenv


class Settings:
    # (env_variable, is_required)
    SECRET_VARIABLES = [("OPENAI_API_KEY", True), ("OPENAI_ORG_ID", False)]

    def __init__(
        self,
        openai_api_key: str,
        openai_org_id: str = None,
        disk_cache_dir: str = "/tmp/disk_cache",
        prompt_history_path="./.prompt_history",
        chat_turns_dir="./.chat_turns",
    ):
        self.openai_api_key = openai_api_key
        self.openai_org_id = openai_org_id
        self.disk_cache_dir = disk_cache_dir
        self.prompt_history_path = prompt_history_path
        self.chat_turns_dir = chat_turns_dir
        os.makedirs(chat_turns_dir, exist_ok=True)

    @classmethod
    def from_env_file(cls, env_file: str = ".env.secret", **kwargs) -> "Settings":
        """Load secrets from a .env file.

        Other kwargs are passed to the Settings constructor.
        """
        secrets = {}
        cfg = dotenv.dotenv_values(env_file)
        for key, is_required in cls.SECRET_VARIABLES:
            if is_required and not cfg.get(key):
                raise ValueError(f"Missing required secret variable {key}")
            secrets[key.lower()] = cfg.get(key)
        return cls(**secrets, **kwargs)

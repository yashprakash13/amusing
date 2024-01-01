import os

from .config import APP_CONFIG


def construct_db_path(root_path: str, db_name: str = "library.db") -> str:
    if "db_name" in APP_CONFIG:
        db_name = APP_CONFIG["db_name"]
    return os.path.join(root_path, db_name)


def construct_download_path(root_path: str, dir_name: str = "songs") -> str:
    return os.path.join(root_path, dir_name)

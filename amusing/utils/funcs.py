import os

from .config import APP_CONFIG


def construct_db_path(root_path: str, db_name: str = "library.db") -> str:
    if "db_name" in APP_CONFIG:
        db_name = APP_CONFIG["db_name"]
    return os.path.join(root_path, db_name)


def construct_download_path(root_path: str, dir_name: str = "downloads") -> str:
    return os.path.join(root_path, dir_name)


# Escape reserved system special characters with unicode variants
# Based on Windows (more restrictive) reserved characters: https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file#naming-conventions
def escape(name: str) -> str:
    return (
        name.replace("<", "＜")
        .replace(">", "＞")
        .replace(":", "：")
        .replace('"', "ʺ")
        .replace("/", "∕")
        .replace("\\", "∖")
        .replace("|", "｜")
        .replace("?", "？")
        .replace("*", "﹡")
    )


# Shorten longer names to avoid huge file names (FFmpeg does not like them)
def short_filename(directory: str, name: str, artwork_hash: str, video_id: str) -> str:
    """Return song filename after making sure it's of good length for the library."""
    # Maximum file name lenght supported by FFmpeg
    MAX_LENGHT = 256
    # Lenght of mandatory suffix: ' [artwork_hash] [video_id].m4a'
    SUFFIX_LENGHT = 53
    # Song name has to be short enough to accomodate both prefix (directory) and suffix
    MAX_NAME_LENGHT = MAX_LENGHT - len(directory) - SUFFIX_LENGHT - 1

    name = escape(name)
    if len(name) > MAX_NAME_LENGHT:
        name = name[0:MAX_NAME_LENGHT] + "…"

    return f"{name} [{artwork_hash}] [{video_id}].m4a"


def short_filename_clean(name: str) -> str:
    """Return song filename after making sure it's of good length and cleaning for organization."""
    MAX_LENGTH = 256
    name = escape(name)
    if len(name) > MAX_LENGTH:
        name = name[0 : MAX_LENGTH - 10] + "…"

    return f"{name}.m4a"

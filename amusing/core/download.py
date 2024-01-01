import yt_dlp


def download_song_from_id(videoId: str, download_album_path: str):
    """To download a song into download_album_path through its videoId from YouTube."""
    song_url = f"https://www.youtube.com/watch?v={videoId}"
    ydl_opts = {
        "format": "m4a/bestaudio/best",
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        "postprocessors": [
            {  # Extract audio using ffmpeg
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        ],
        "paths": {"home": download_album_path},
        "outtmpl": {"pl_thumbnail": ""},
        "postprocessors": [{"already_have_thumbnail": False, "key": "EmbedThumbnail"}],
        "writethumbnail": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(song_url)
        print("Error=> ", error_code)
        return 1 if error_code else 0

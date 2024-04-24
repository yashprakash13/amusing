import os
import re
import subprocess

import yt_dlp

def download_song_from_video_id(video_id: str, path: str):
    """
    Download a song into path through its video_id from YouTube.

    Returns: the downloaded song filename
    """
    song_url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "m4a/bestaudio/best",
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        "postprocessors": [
            {  # Extract audio using ffmpeg
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }
        ],
        "paths": {"home": path},
        "outtmpl": {"pl_thumbnail": ""},
        "postprocessors": [{"already_have_thumbnail": False, "key": "EmbedThumbnail"}],
        "writethumbnail": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(song_url)
        if error_code:
            raise RuntimeError(f"video [{video_id}] download failed with error code: {error_code}")

def add_metadata(
    input_file,
    output_file,
    path,
    song,
):
    """Adds metadata to the song file. Requires FFmpeg installed."""
    album = song.album
    result = subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-i', input_file,
            '-metadata', f"title={song.title}",
            '-metadata', f"album={album.title}",
            '-metadata', f"artist={song.artist}",
            '-metadata', f"composer={song.composer}",
            '-metadata', f"genre={song.genre}",
            '-metadata', f"track={song.track}/{album.tracks}",
            '-metadata', f"album_artist={album.artist}",
            '-metadata', f"year={album.year}",
            '-acodec', 'copy',
            '-vcodec', 'png',
            '-disposition:v', 'attached_pic',
            '-vf', "crop=w='min(iw\,ih)':h='min(iw\,ih)',scale=600:600,setsar=1",
            output_file,
        ],
        capture_output=True,
        text=True,
    )
    rc = result.returncode
    if rc:
        print(result.output)
        print(f"FFmpeg exited with error code {rc}.")

def song_file(song, album_dir):
    """
    Find downloaded song filename.

    Returns:
    - the file path, if found
    - "" otherwise
    """
    if not (os.path.exists(album_dir) and os.path.isdir(album_dir)):
        return ""

    video_id = song.video_id
    files_in_album = os.listdir(album_dir)
    for file_name in files_in_album:
        regex = re.compile(f".* \[{video_id}\].m4a$")
        if regex.match(file_name):
            return os.path.join(album_dir, file_name)

    return ""


def download(song, album_dir, songs_dir):
    title = song.title.replace('/', u"\u2215")
    album = song.album.title.replace('/', u"\u2215")
    artist = song.artist.replace('/', u"\u2215")
    video_id = song.video_id

    song_name = f"{title} - {album} - {artist}"
    song_filename = f"{song_name}.m4a"
    song_file_path = os.path.join(songs_dir, song_filename)

    if os.path.exists(song_file_path):
        return

    downloaded_file_path = song_file(song, album_dir)
    if downloaded_file_path:
        print(f"'{title}' already downloaded in '{downloaded_file_path}'")
    else:
        print(f"Downloading '{song_name}'")
        download_song_from_video_id(video_id, album_dir)
        downloaded_file_path = song_file(song, album_dir)
        print(f"Downloaded '{downloaded_file_path}'")

    print(f"Generating '{song_filename}'")
    add_metadata(
        downloaded_file_path,
        song_file_path,
        album_dir,
        song
    )

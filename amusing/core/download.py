import os
import re
import subprocess
import urllib.request
import shutil
from glob import glob

from amusing.db.models import Song

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
        try:
            error_code = ydl.download(song_url)
            if error_code:
                raise RuntimeError(f"video [{video_id}] download failed with error code: {error_code}")
        except Exception:
            raise RuntimeError(f"video [{video_id}] download failed")


def add_metadata(
    input_file: str,
    output_file: str,
    album_dir: str,
    song: Song,
):
    """Adds metadata to the song file. Requires FFmpeg installed."""
    album = song.album
    artwork_url = song.artwork_url
    artwork_path = os.path.join(album_dir, 'artwork.png')
    custom_artwork = artwork_url is not None
    if custom_artwork and not os.path.exists(artwork_path):
        artwork_file = open(artwork_path, 'wb')
        try:
            print(f"[+] Downloading album artwork from: {artwork_url}")
            response = urllib.request.urlopen(artwork_url)
            shutil.copyfileobj(response, artwork_file)
        except Exception as e:
            os.remove(artwork_path)
            raise RuntimeError(f"failed to download album artwork at: {artwork_url}")

    args = [
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
        '-metadata', f"date={album.release_date}",
        '-acodec', 'copy',
        '-vcodec', 'png',
        '-disposition:v', 'attached_pic',
        '-vf', "crop=w='min(iw\,ih)':h='min(iw\,ih)',scale=600:600,setsar=1",
        output_file,
    ]

    if custom_artwork:
        # Add artwork input to arguments
        args.insert(4, '-i')
        args.insert(5, artwork_path)

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
    )
    rc = result.returncode
    if rc:
        print(result.stderr)
        print(f"[!] FFmpeg exited with error code {rc}")


def song_file(song: Song, album_dir: str) -> str:
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


def download(song: Song, root_download_path: str):
    """Download a song from YouTube video and generate file with metadata."""

    title = song.title.replace('/', u"\u2215")
    album = song.album.title.replace('/', u"\u2215")
    artist = song.artist.replace('/', u"\u2215")
    video_id = song.video_id

    songs_dir = os.path.join(root_download_path, 'songs')
    album_dir = os.path.join(root_download_path, 'caches', album)
    # Generate directories
    for path in [songs_dir, album_dir]:
        if not (os.path.exists(path) and os.path.isdir(path)):
            os.makedirs(path, exist_ok=True)

    song_name = f"{title} - {album} - {artist}"
    song_filename = f"{song_name} [{video_id}].m4a"
    song_file_path = os.path.join(songs_dir, song_filename)

    # Skip download if the song is already present
    if os.path.exists(song_file_path):
        return

    for file in glob(f"{song_name} [*].m4a"):
        # Delete existing song if it was generated from a different video
        os.remove(file)

    downloaded_file_path = song_file(song, album_dir)
    if downloaded_file_path:
        print(f"[=] Song already downloaded: '{title}' -> '{downloaded_file_path}'")
    else:
        print(f"[+] Downloading '{song_name}'")
        download_song_from_video_id(video_id, album_dir)
        downloaded_file_path = song_file(song, album_dir)
        print(f"[+] Downloaded '{downloaded_file_path}'")

    print(f"[+] Generating '{song_filename}'")
    add_metadata(
        downloaded_file_path,
        song_file_path,
        album_dir,
        song
    )

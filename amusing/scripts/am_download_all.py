import os
import re
import time

import pandas as pd
import yt_dlp
from db.engine import get_new_db_session
from db.models import Album, Song
from ytmusicapi import YTMusic

ytmusic = YTMusic()
session = get_new_db_session()


def extract_song_info(song_file):
    match = re.match(r"^(.*?) \[(.*?)\]$", song_file)
    if match:
        return match.group(1), match.group(2)
    else:
        return song_file, ""


def process_groups(album_name, album_dir, group, album=None, dir_already_present=False):
    print(f"Processing album: {album_name}")
    files_in_album = os.listdir(album_dir)
    for index, row in group.iterrows():
        song_name = row["Name"]
        artist_name = row["Artist"]

        if dir_already_present:
            song_already_present = False
            for file_name in files_in_album:
                if (
                    song_name.lower() in file_name.lower()
                    or file_name.lower() in song_name.lower()
                ):
                    song_already_present = True
                    print("Song downloaded already. Skipping.")
                    # check if song also present in db, if not add to db
                    song_query = (
                        session.query(Song)
                        .filter_by(name=song_name, artist=artist_name, album=album)
                        .first()
                    )
                    if not song_query:
                        print("Song not in db. Adding.")
                        _, song_id = extract_song_info(file_name)
                        song = Song(
                            name=song_name,
                            artist=artist_name,
                            video_id=song_id,
                            album=album,
                        )
                        session.add(song)
                        session.commit()
                        print("Song added to db.")
                    break
            if song_already_present:
                continue

        # Perform operations on the row
        print(
            f"Processing song: Album='{album_name}', Song='{song_name}', Artist='{artist_name}'"
        )
        try:
            search_results = ytmusic.search(
                f"{song_name} - {artist_name} - {album_name}",
                limit=1,
                ignore_spelling=True,
                filter="songs",
            )
            videoId = search_results[0]["videoId"]
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
                "paths": {"home": album_dir},
                "outtmpl": {"pl_thumbnail": ""},
                "postprocessors": [
                    {"already_have_thumbnail": False, "key": "EmbedThumbnail"}
                ],
                "writethumbnail": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                error_code = ydl.download(song_url)
                print("Error=> ", error_code)

            # check if song present in db, if yes, remove and add this one.
            song_query = (
                session.query(Song)
                .filter_by(name=song_name, artist=artist_name, album=album)
                .first()
            )
            if song_query:
                session.delete(song_query)
            song = Song(
                name=song_name, artist=artist_name, video_id=videoId, album=album
            )
            session.add(song)
            session.commit()
            print(
                f"Done song: Album='{album_name}', Song='{song_name}', Artist='{artist_name}'"
            )
            time.sleep(1)
        except Exception as e:
            print(f"Exception {e}. Skipping song.")
            continue
    print(f"Done album '{album_name}'")
    time.sleep(5)


def process_csv(filename):
    """Function to read CSV, process rows, and sleep accordingly."""
    df = pd.read_csv(filename)
    grouped = df.groupby("Album")

    sleep_after_5th = 5
    sleep_after_10th = 11

    for album_name, group in grouped:
        album_dir = f"songs/{album_name}"
        dir_already_present = False
        if os.path.exists(album_dir) and os.path.isdir(album_dir):
            dir_already_present = True
        else:
            os.makedirs(album_dir, exist_ok=True)

        album = session.query(Album).filter_by(name=album_name).first()
        if not album:
            album = Album(name=album_name)
            session.add(album)
            session.commit()

        # Submit the group processing task to the ThreadPoolExecutor
        process_groups(album_name, album_dir, group, album, dir_already_present)

        # Sleep after every 5th group
        if len(group) >= 5:
            time.sleep(sleep_after_5th)

        # Sleep after every 10th group
        if len(group) >= 10:
            time.sleep(sleep_after_10th)


# uncomment the following line to parse a CSV.
# process_csv('Library_parsed.csv')

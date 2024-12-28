import pandas as pd
from sqlalchemy.orm import Session
from unidecode import unidecode

from amusing.core.parse_xml import sort_library
from amusing.core.search import search
from amusing.db.models import Album, Song


def get_video_id(song: Song) -> str:
    """Return YouTube video ID of a song, searching it on YouTube Music if necessary."""
    # Check if one was already assigned
    video_id = song.video_id
    if video_id:
        return song.video_id

    return search(song).video_id


def process_album(group: pd.DataFrame, album: Album, session: Session) -> pd.DataFrame:
    """Helper function to process each album and songs present within it from the csv."""
    for index, row in group.iterrows():
        song_title = row["Title"]
        artist = row["Artist"]
        album_title = album.title
        genre = row["Genre"]
        disc = int(row["Disc Number"])
        track = int(row["Track Number"])
        composer = row["Composer"]
        # Could be initially empty
        video_id = row["Video ID"]
        artwork_url = row["Artwork URL"]

        song = (
            session.query(Song)
            .filter_by(title=song_title, artist=artist, album=album)
            .first()
        )

        if song:
            updated = False
            if video_id and (video_id != song.video_id):
                # Update song video_id with new one from CSV
                song.video_id = video_id
                print(
                    f"[+] updated video_id: [{video_id}] -> '{song_title} - {album_title} - {artist}'"
                )
                updated = True
            elif not video_id:
                # Update CSV with id stored in DB
                group.loc[index, "Video ID"] = song.video_id
            db_artwork = song.album.artwork_url
            if artwork_url and (artwork_url != db_artwork):
                song.album.artwork_url = artwork_url
                updated = True
            elif not artwork_url and db_artwork:
                group.loc[index, "Artwork URL"] = db_artwork
            if updated:
                session.commit()

            continue

        # Otherwise the song has to be associated with a video_id and put in DB
        song = Song(
            title=song_title,
            artist=artist,
            album=album,
            genre=genre,
            disc=disc,
            track=track,
            composer=composer,
            video_id=video_id,
        )
        try:
            video_id = get_video_id(song)
            group.loc[index, "Video ID"] = video_id

            song.video_id = video_id
            session.add(song)
            session.commit()

            print(
                f"[+] video_id: [{video_id}] -> '{song_title} - {album_title} - {artist}'"
            )
        except Exception as e:
            print(f"[!] Error: {e}")
            print(f"[-] Skipping song '{song_title} - {album_title} - {artist}'")
            continue

    return group


def process_csv(filename: str, session: Session):
    """Function to read CSV and process rows"""
    df = pd.read_csv(filename).fillna("")
    grouped = df.groupby("Album")

    for album_title, group in grouped:
        album = session.query(Album).filter_by(title=album_title).first()
        if not album:
            album = Album(title=album_title)

            # Get album info from its first available song
            row = group.iloc[0]
            album.tracks = int(row["Track Count"])
            album.artist = row["Album Artist"]
            album.release_date = row["Release Date"]

            artwork_url = row["Artwork URL"]
            if artwork_url:
                album.artwork_url = artwork_url

            session.add(album)
            session.commit()

        group = process_album(group, album, session)

        # Update original DataFrame too
        for index, row in group.iterrows():
            df.at[index, "Video ID"] = row["Video ID"]
            df.at[index, "Artwork URL"] = row["Artwork URL"]

    # Sort and keep only relevant fields
    df = sort_library(
        df[
            [
                "Title",
                "Album",
                "Album Artist",
                "Video ID",
                "Artwork URL",
                "Artist",
                "Composer",
                "Genre",
                "Release Date",
                "Year",
                "Explicit",
                "Disc Count",
                "Disc Number",
                "Track Count",
                "Track Number",
                "Favorited",
                "Loved",
                "Playlist Only",
                "Sort Name",
                "Sort Album",
                "Sort Album Artist",
                "Sort Artist",
                "Sort Composer",
            ]
        ]
    )

    # Finally, export the updated CSV, with video ids
    df.to_csv(filename, index=False)

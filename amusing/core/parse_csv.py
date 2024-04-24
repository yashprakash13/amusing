import pandas as pd
from sqlalchemy.orm import Session
from ytmusicapi import YTMusic

from amusing.db.models import Album, Song

ytmusic = YTMusic()

def process_album(group, session, album):
    """Helper function to process each album and songs present within it from the csv."""
    for _, row in group.iterrows():
        song_title = row['Name']
        artist = row['Artist']
        album_title = album.title
        genre = row['Genre']
        track = row['Track Number']
        composer = row['Composer']

        song = Song(
            title=song_title,
            artist=artist,
            album=album,
            genre=genre,
            track=track,
            composer=composer,
        )

        song_query = (
            session.query(Song)
            .filter_by(title=song_title, artist=artist, album=album)
            .first()
        )
        if song_query:
            # The song is already in DB
            continue

        # Otherwise the song has to be associated with a video_id and put in DB
        try:
            search_results = ytmusic.search(
                f"{song_title} - {artist} - {album_title}",
                limit=1,
                ignore_spelling=True,
                filter='songs',
            )
            video_id = search_results[0]['videoId']
            song.video_id = video_id

            session.add(song)
            session.commit()

            print(f"[+] video_id: [{video_id}] -> '{song_title} - {album_title} - {artist}'")

        except Exception as e:
            print(f"Error: {e}\nSkipping '{song_title}'.")
            continue


def process_csv(filename: str, session: Session):
    """Function to read CSV and process rows"""
    df = pd.read_csv(filename)
    grouped = df.groupby('Album')

    for album_title, group in grouped:
        album = (
            session.query(Album)
            .filter_by(title=album_title)
            .first()
        )
        if not album:
            row = group.iloc[0]
            album = Album(title=album_title)
            album.tracks = row['Track Count']
            album.artist = row['Album Artist']
            album.year = row['Year']

            session.add(album)
            session.commit()

        process_album(group, session, album)

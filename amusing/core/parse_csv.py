import pandas as pd
from sqlalchemy.orm import Session
from ytmusicapi import YTMusic

from amusing.db.models import Album, Song

ytmusic = YTMusic()

def get_video_id(song):
    # Check if one was already assigned
    video_id = song.video_id
    if video_id:
        return song.video_id

    search_results = ytmusic.search(
        f"{song.title} - {song.artist} - {song.album.title}",
        limit=1,
        ignore_spelling=True,
        filter='songs',
    )
    return search_results[0]['videoId']


def process_album(group, album, session):
    """Helper function to process each album and songs present within it from the csv."""
    for index, row in group.iterrows():
        song_title = row['Name']
        artist = row['Artist']
        album_title = album.title
        genre = row['Genre']
        track = row['Track Number']
        composer = row['Composer']
        # This could be initially empty
        video_id = row['Video ID']

        song = (
            session.query(Song)
            .filter_by(title=song_title, artist=artist, album=album)
            .first()
        )
        if song:
            # The song is already in DB
            group.loc[index, 'Video ID'] = song.video_id
            continue

        # Otherwise the song has to be associated with a video_id and put in DB
        song = Song(
            title=song_title,
            artist=artist,
            album=album,
            genre=genre,
            track=track,
            composer=composer,
            video_id=video_id,
        )
        try:
            video_id = get_video_id(song)
            group.loc[index, 'Video ID'] = video_id

            song.video_id = video_id
            session.add(song)
            session.commit()

            print(f"[+] video_id: [{video_id}] -> '{song_title} - {album_title} - {artist}'")
        except Exception as e:
            print(f"Error: {e}\nSkipping '{song_title}'.")
            continue

    return group


def process_csv(filename: str, session: Session):
    """Function to read CSV and process rows"""
    df = pd.read_csv(filename).fillna('')
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
            album.release_date = row['Release Date']

            session.add(album)
            session.commit()

        group = process_album(group, album, session)

        # Update original DataFrame too
        for index, row in group.iterrows():
            df.at[index, 'Video ID'] = row['Video ID']

    # Finally, export the updated CSV, with video ids
    df.to_csv(filename, index=False)

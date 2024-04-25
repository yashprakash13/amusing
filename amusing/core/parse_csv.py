import pandas as pd
from sqlalchemy.orm import Session

from amusing.db.models import Album, Song
from amusing.core.search import search

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
        if video_id and song:
            if video_id != song.video_id:
                # Update song video_id with new one
                song.video_id = video_id
                session.commit()
                print(f"[+] updated video_id: [{video_id}] -> '{song_title} - {album_title} - {artist}'")
            continue
        elif song:
            # Skip song already in DB and set CSV video_id
            video_id = song.video_id
            group.loc[index, 'Video ID'] = video_id
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
            print(f"[!] Error: {e}")
            print(f"[-] Skipping song '{song_title} - {album_title} - {artist}'")
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

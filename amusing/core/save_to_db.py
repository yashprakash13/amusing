import os

from sqlalchemy.orm import Session

from amusing.db.models import Album, Song


def create_new_album(album_name: str, album_dir: str, session: Session):
    """To create a new album with the given album_name in the given album_dir."""
    try:
        dir_already_present = False
        if os.path.exists(album_dir) and os.path.isdir(album_dir):
            dir_already_present = True
        else:
            os.makedirs(album_dir, exist_ok=True)

        album = session.query(Album).filter_by(title=album_name).first()
        if not album:
            album = Album(title=album_name)
            session.add(album)
            session.commit()
        return album, 0
    except Exception as e:
        print(f"Exception {e} when creating album.")
        return None, 1


def create_new_song(
    song_name: str,
    artist_name: str,
    videoId: str,
    album: Album,
    session: Session,
    overwrite: bool = False,
):
    """To add a new song into the db."""
    try:
        song_query = (
            session.query(Song)
            .filter_by(title=song_name, artist=artist_name, album=album)
            .first()
        )
        if song_query and overwrite:
            session.delete(song_query)
        elif song_query and not overwrite:
            return
        song = Song(title=song_name, artist=artist_name, video_id=videoId, album=album)
        session.add(song)
        session.commit()
    except Exception as e:
        print(f"Exception {e} when creating the song.")
        return 1

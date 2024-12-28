from sqlalchemy.orm import Session

from amusing.db.models import Album, Song


def create_new_album_if_not_present(album_name: str, session: Session):
    """To create a new album with the given album_name in the given album_dir."""
    try:
        album = session.query(Album).filter_by(title=album_name).first()
        if not album:
            album = Album(title=album_name)
            session.add(album)
            session.commit()
        return album, 0
    except Exception as e:
        print(f"Exception {e} when creating album.")
        return None, 1


def check_if_song_in_db(
    song_name: str,
    artist_name: str,
    album: Album,
    session: Session,
):
    """To check if a song is present in the db."""
    try:
        song_query = (
            session.query(Song)
            .filter_by(title=song_name, artist=artist_name, album_id=album.id)
            .first()
        )
        if song_query:
            return song_query, None
        else:
            return None, None
    except Exception as e:
        print(f"Exception {e} when creating the song.")
        return None, 1

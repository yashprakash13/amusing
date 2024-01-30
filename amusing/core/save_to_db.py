import os

from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session

from amusing.db.models import Album, MetadataMoveAlbum, Song


def create_new_album(
    album_name: str,
    album_dir: str,
    session: Session,
    album_mbid: str = None,
    album_artist: str = None,
    coverart_present: bool = False,
):
    """To create a new album with the given album info in the given album_dir."""
    try:
        dir_already_present = False
        if os.path.exists(album_dir) and os.path.isdir(album_dir):
            dir_already_present = True
        else:
            os.makedirs(album_dir, exist_ok=True)

        album = session.query(Album).filter_by(name=album_name).first()
        if not album:
            album = Album(
                name=album_name,
                album_mbid=album_mbid,
                album_artist=album_artist,
                coverart_present=coverart_present,
            )
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
    song_mbid: str = None,
    year: int = None,
    month: int = None,
    day: int = None,
    lyrics: str = None,
):
    """To add a new song into the db."""
    try:
        song_query = (
            session.query(Song)
            .filter_by(name=song_name, artist=artist_name, album=album)
            .first()
        )
        if song_query and overwrite:
            session.delete(song_query)
        elif song_query and not overwrite:
            return
        song = Song(
            name=song_name,
            artist=artist_name,
            video_id=videoId,
            album=album,
            song_mbid=song_mbid,
            year=year,
            month=month,
            day=day,
            lyrics=lyrics,
        )
        session.add(song)
        session.commit()
    except Exception as e:
        print(f"Exception {e} when creating the song.")
        return 1


def get_song_from_name_and_album(
    song_name: str, album_id: int, session: Session
) -> Song:
    """To return a song from song table."""
    try:
        song_query = (
            session.query(Song).filter_by(name=song_name, album_id=album_id).first()
        )
        if song_query:
            return song_query
        else:
            song_query = (
                session.query(Song)
                .filter(
                    and_(Song.album_id == album_id, Song.name.ilike(f"%{song_name}%"))
                )
                .all()
            )
            if song_query:
                return song_query[0]
            return None
    except Exception as e:
        print(f"Exception {e} when getting the song.")
        return 1


def modify_song(song: Song, row_values: dict, session: Session):
    """To modify a given song."""
    try:
        for key, val in row_values.items():
            setattr(song, key, val)
        session.commit()
    except Exception as e:
        print(f"Exception {e} when modifying the song.")
        return 1


def get_album_from_name(album_name: str, session: Session) -> Album:
    """To return an album from album table."""
    try:
        album_query = (
            session.query(Album).filter(Album.name.ilike(f"%{album_name}%")).first()
        )
        if album_query:
            return album_query
        else:
            return None
    except Exception as e:
        print(f"Exception {e} when getting the album.")
        return 1


def modify_album(album: Album, row_values: dict, session: Session):
    """To modify a given album."""
    try:
        print(f"Modifying {album.name} with {row_values}")
        stmt = update(Album).where(Album.id == album.id).values(row_values)
        session.execute(stmt)
        session.commit()
    except Exception as e:
        print(f"Exception {e} when modifying the album.")
        return 1


def create_new_metadata_album_entry(metadata: dict, session: Session):
    """To create a new MetadataMoveAlbum row."""
    try:
        metadata_row = MetadataMoveAlbum(
            am_album_name=metadata["am_album_name"], album_id=metadata["album_id"]
        )
        session.add(metadata_row)
        session.commit()
    except Exception as e:
        print(f"Exception {e} when creating the metadata row.")
        return 1

import os

from sqlalchemy.orm import Session

from amusing.core.download import download
from amusing.db.models import Album, Song

def download_library(download_path: str, session: Session):
    songs_dir = os.path.join(download_path, 'songs')
    if not (os.path.exists(songs_dir) and os.path.isdir(songs_dir)):
        os.makedirs(songs_dir, exist_ok=True)

    albums = (
        session.query(Album)
        .order_by(Album.title)
    )
    for album in albums:
        album_dir = os.path.join(
            download_path,
            'albums',
            album.title.replace('/', u"\u2215")
        )
        if not (os.path.exists(album_dir) and os.path.isdir(album_dir)):
            os.makedirs(album_dir, exist_ok=True)

        for song in album.songs:
            download(song, album_dir, songs_dir)

import os

from amusing.core.download import download_song_from_id
from amusing.core.parse_csv import process_csv
from amusing.core.parse_xml import parse_library_xml
from amusing.core.save_to_db import (
    create_new_album,
    create_new_metadata_album_entry,
    create_new_song,
    get_album_from_name,
    get_song_from_name_and_album,
    modify_album,
    modify_song,
)
from amusing.core.search import search_a_song
from amusing.db.engine import get_new_db_session
from amusing.db.models import Album, MetadataMoveAlbum, Song
from amusing.utils.funcs import construct_db_path, construct_download_path


def download_song_operation(
    album_name: str,
    song_name: str,
    artist_name: str,
    root_download_path: str,
    overwrite: bool = False,
):
    """Download a particular song and add it to the db.

    Parameters:
    album_name (str): name of the album
    song_name (str): name of the song
    artist_name (str): name of the artist
    root_download_path (str): the path to download songs and put db into.
    overwrite (bool): whether to overwrite the song if present in db and downloads.

    """
    # fetch song from YT Music
    song_fetched = search_a_song(song_name, artist_name, album_name)
    if not song_fetched:
        return "Couldn't find song through YouTube Music Search."
    album_name = song_fetched["album"]
    song_name = song_fetched["song_name"]
    artist_name = song_fetched["artist_name"]

    # download song into album
    album_dir = os.path.join(
        construct_download_path(root_download_path), song_fetched["album"]
    )
    error = download_song_from_id(song_fetched["videoId"], album_dir)
    if error:
        return "Something went wrong in downloading song. Please try again."

    # insert into db
    session = get_new_db_session(construct_db_path(root_download_path))
    if not album_name:
        album_name = song_name
    album_in_db, error = create_new_album(album_name, album_dir, session)
    if error:
        return "Something went wrong in creating album. Please try again."

    error = create_new_song(
        song_name,
        artist_name,
        song_fetched["videoId"],
        album_in_db,
        session,
        overwrite=overwrite,
    )
    if error:
        return "Something went wrong in creating song. Please try again."
    return "Added song!"


def parse_library_operation(root_download_path: str, lib_path: str):
    """Parse the Library XML file and download all songs.

    Parameters:
    root_download_path (str): the path to download songs and put db into.
    lib_path (str): the full path to the Library.xml file exported from Apple Music.

    """
    error = parse_library_xml(root_download_path, lib_path)
    if error:
        return "Something went wrong in creating a parsed CSV file from XML. Please try again."

    download_path = construct_download_path(root_download_path)
    session = get_new_db_session(construct_db_path(root_download_path))
    process_csv(
        os.path.join(root_download_path, "Library_parsed.csv"), download_path, session
    )


def show_similar_songs_in_db_operation(song_name: str, root_download_path: str):
    """Look up the db for song_name.

    Parameters:
    song_name (str): the name of the song to look up
    root_download_path (str): the path to the root downloads folder where the db is situated.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    song_query = session.query(Song).filter(Song.name.ilike(f"%{song_name}%")).all()
    song_list_found = []
    for song in song_query:
        song_list_found.append(
            {"name": song.name, "artist": song.artist, "album": song.album.name}
        )
    return song_list_found


def show_similar_songs_for_artist_in_db_operation(
    artist_name: str, root_download_path: str
):
    """Look up the db for artist_name and fetch all songs by the artist.

    Parameters:
    artist_name (str): the name of the artist to look up
    root_download_path (str): the path to the root downloads folder where the db is situated.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    song_query = session.query(Song).filter(Song.artist.ilike(f"%{artist_name}%")).all()
    song_list_found = []
    for song in song_query:
        song_list_found.append(
            {"name": song.name, "artist": song.artist, "album": song.album.name}
        )
    return song_list_found


def show_similar_albums_in_db_operation(
    album_name: str, root_download_path: str
) -> list:
    """Look up the db for album_name.

    Parameters:
    album_name (str): the name of the album to look up
    root_download_path (str): the path to the root downloads folder where the db is situated.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    album_query = session.query(Album).filter(Album.name.ilike(f"%{album_name}%")).all()
    album_list_found = []
    for album in album_query:
        album_list_found.append(
            {"name": album.name, "number_of_songs": len(album.songs)}
        )
    return album_list_found


def modify_album_in_db(album: Album, new_album_info: dict, root_download_path: str):
    """Get the album in db and save it with the new info. Typically executed during metadata search and tag operation.

    Parameters:
    old_album_info (dict): dict of album info
    new_album_info (dict): dict of new album info
    root_download_path (str): the path to the root downloads folder where the db is situated.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    error = modify_album(album, new_album_info, session)
    if error:
        print("Something went wrong saving the modified album info.")


def modify_song_in_db(
    old_song_info: dict, new_song_info: dict, root_download_path: str
):
    """Get the song in db and save it with the new info. Typically executed during metadata search and tag operation.

    Parameters:
    old_song_info (dict): dict of song info that includes name and album_id fields
    new_song_info (dict): dict of new song info
    root_download_path (str): the path to the root downloads folder where the db is situated.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    print(f"Getting song info from: {old_song_info}")
    song = get_song_from_name_and_album(
        old_song_info["name"], old_song_info["album_id"], session
    )
    print("Got song=> ", song)
    error = modify_song(song, new_song_info, session)
    if error:
        return 1


def if_album_metadata_processed(am_album_name: str, root_download_path: str) -> Album:
    """Check whether the album was processed already and return the object from the Album table.

    Parameters:
    am_album_name (str): to check in the MetadataMoveAlbum table
    root_download_path (str): the path to the root downloads folder where the db is situated.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    album_metadata_table_obj = (
        session.query(MetadataMoveAlbum).filter_by(am_album_name=am_album_name).first()
    )
    if album_metadata_table_obj:
        album_id = album_metadata_table_obj.album_id
        return session.query(Album).filter_by(id=album_id).first()
    return None


def create_album_metadata_in_db(album_metadata: dict, root_download_path: str):
    """
    Create a new row in the MetadataMoveAlbum table.

    Parameters:
    album_metadata (dict): The column values as dict
    root_download_path (str): the path to the root downloads folder where the db is situated.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    error = create_new_metadata_album_entry(album_metadata, session)
    if error:
        return "Something went wrong in creating a metadata entry. Please try again."
    return "Added metadata entry to db!"


def get_album_from_db(album_name: str, root_download_path: str):
    """
    Get and return Album obj from the Album table.

    Parameters:
    album_name (dict): The album name to fetch
    root_download_path (str): the path to the root downloads folder where the db is situated.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    album = get_album_from_name(album_name, session)
    return album

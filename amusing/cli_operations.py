import os

from amusing.core.parse_csv import process_csv
from amusing.core.parse_xml import parse_library_xml
from amusing.core.download_library import download_library
from amusing.core.save_to_db import create_new_album, create_new_song
from amusing.core.search import search_a_song
from amusing.db.engine import get_new_db_session
from amusing.db.models import Album, Song
from amusing.utils.funcs import construct_db_path, construct_download_path

def parse_library_operation(root_download_path: str, lib_path: str):
    """Parse the Library XML or CSV file.

    Parameters:
    lib_path (str): the full path to the Library.xml file exported from Apple Music or a Library_parsed.csv file

    """
    if lib_path.lower().endswith('.xml'):
        error = parse_library_xml(root_download_path, lib_path)
        if error:
            return "Something went wrong in creating a parsed CSV file from XML. Please try again."
        parsed_library = os.path.join(root_download_path, "Library_parsed.csv")
    elif lib_path.lower().endswith('.csv'):
        parsed_library = lib_path
    else:
        return "A 'Library.xml' or 'Library_parsed.csv' file was expected."

    session = get_new_db_session(construct_db_path(root_download_path))
    process_csv(parsed_library, session)


def download_library_operation(root_download_path: str):
    """Download all songs in DB.

    Parameters:
    root_download_path (str): songs download path.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    download_library(root_download_path, session)


def show_similar_songs_in_db_operation(song_name: str, root_download_path: str):
    """Look up the db for song_name.

    Parameters:
    song_name (str): the name of the song to look up
    root_download_path (str): the path to the root downloads folder where the db is situated.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    song_query = session.query(Song).filter(Song.title.ilike(f"%{song_name}%")).all()
    song_list_found = []
    for song in song_query:
        song_list_found.append(
            {"name": song.title, "artist": song.artist, "album": song.album.title}
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
            {"name": song.title, "artist": song.artist, "album": song.album.title}
        )
    return song_list_found


def show_similar_albums_in_db_operation(album_name: str, root_download_path: str):
    """Look up the db for album_name.

    Parameters:
    album_name (str): the name of the album to look up
    root_download_path (str): the path to the root downloads folder where the db is situated.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    album_query = session.query(Album).filter(Album.title.ilike(f"%{album_name}%")).all()
    album_list_found = []
    for album in album_query:
        album_list_found.append(
            {"name": album.title, "number_of_songs": len(album.songs)}
        )
    return album_list_found

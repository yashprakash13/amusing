import hashlib
import os
import re
from shutil import copyfile

import amusing.core.save_to_db
import amusing.core.search
from amusing.core.download import download
from amusing.core.parse_csv import process_csv
from amusing.core.parse_xml import parse_library_xml
from amusing.db.engine import get_new_db_session
from amusing.db.models import Album, Organizer, Song
from amusing.utils.funcs import construct_db_path, short_filename, short_filename_clean


def download_song_operation(
    album_name: str,
    song_name: str,
    artist_name: str,
    root_download_path: str,
    overwrite: bool = False,
) -> str:
    """Download a particular song and add it to the db.

    Parameters:
    album_name (str): name of the album
    song_name (str): name of the song
    artist_name (str): name of the artist
    root_download_path (str): the path to download songs and put db into.
    overwrite (bool): whether to overwrite the song if present in db and downloads.

    """
    song = Song(
        title=song_name,
        artist=artist_name,
        album=Album(title=album_name),
    )
    # fetch song from YT Music
    song_fetched = search(song)
    if not song_fetched:
        return "Couldn't find song through YouTube Music Search."
    album_name = song_fetched.album.title
    song_name = song_fetched.title
    artist_name = song_fetched.artist

    try:
        download(song_fetched, root_download_path)
    except RuntimeError as e:
        print(f"[!] Error: {e}")
        return "Something went wrong while downloading a song. Please try again."
    except FileNotFoundError as e:
        print(f"[!] Error: {e}")
        return "Is FFmpeg installed? It is required to generate the songs."

    # insert into db
    session = get_new_db_session(construct_db_path(root_download_path))
    if not album_name:
        album_name = song_name
    album_in_db, error = create_new_album(album_name, album_dir, session)
    if error:
        return "Something went wrong in creating album. Please try again."

    error = create_new_song(
        song_name, artist_name, song_fetched.video_id, album_in_db, session, overwrite
    )
    if error:
        return "Something went wrong in creating song. Please try again."

    return "Added song!"


def parse_library_operation(root_download_path: str, lib_path: str) -> str:
    """Parse the Library XML or CSV file.

    Parameters:
    lib_path (str): the full path to the Library.xml file exported from Apple Music or a Library.csv file

    """
    if lib_path.lower().endswith(".xml"):
        error = parse_library_xml(root_download_path, lib_path)
        if error:
            return "Something went wrong in creating a parsed CSV file from XML. Please try again."
        parsed_library = os.path.join(root_download_path, "Library.csv")
    elif lib_path.lower().endswith(".csv"):
        parsed_library = lib_path
    else:
        return "A 'Library.xml' or 'Library.csv' file was expected."

    session = get_new_db_session(construct_db_path(root_download_path))
    process_csv(parsed_library, session)

    return ""


def download_library_operation(root_download_path: str) -> str:
    """Download all songs in DB.

    Parameters:
    root_download_path (str): songs download path.

    """
    session = get_new_db_session(construct_db_path(root_download_path))
    albums = session.query(Album).order_by(Album.title)
    for album in albums:
        for song in album.songs:
            try:
                download(song, root_download_path)
            except RuntimeError as e:
                print(f"[!] Error: {e}")
                print("[!] Something went wrong while downloading. Skipping song.")
            except FileNotFoundError as e:
                print(f"[!] Error: {e}")
                return "Is FFmpeg installed? It is required to generate the songs."

    return ""


def organize_library_operation(root_download_path: str, destination_path: str) -> str:
    """Organize the downloaded music library for an application like Plex or Jellyfin.

    - organize music from songs/ directory to a given location for the application to pick up
    - when run for the first time, check in db the current song's video ID against its video ID in 'organized_music' table
    if same, skip organization steps
    if different, perform the organization steps

    Organization steps:
    - delete the current file in the organized library destination path
    - edit the entry in the Organizer table
    - copy the new file to the path and rename it to remove the extra elements in the name (video id and artwork hash)

    Note that this organization operation first needs you to make sure that you've run  `amusing download path/to/library.csv` so that
    the entry in Song database table is already updated.

    Parameters:
    root_download_path (str): songs download path.
    destination_path (str): the full destination path in which to copy and organize the music library
    """
    session = get_new_db_session(construct_db_path(root_download_path))
    for song, organizer in (
        session.query(Song, Organizer)
        .outerjoin(Organizer, Song.id == Organizer.song_id)
        .all()
    ):
        songs_dir = os.path.join(root_download_path, "songs")
        song_name = f"{song.title} - {song.album.title} - {song.artist}"
        artwork_url = song.album.artwork_url
        if artwork_url is None:
            artwork_url = ""
        artwork_hash = hashlib.md5(artwork_url.encode()).hexdigest()
        song_filename = short_filename(
            songs_dir, song_name, artwork_hash, song.video_id
        )
        song_file_path = os.path.join(songs_dir, song_filename)
        clean_song_filename = short_filename_clean(song.title)
        destination_dir = os.path.join(destination_path, song.artist, song.album.title)
        os.makedirs(destination_dir, exist_ok=True)
        song_file_path_organizer = os.path.join(destination_dir, clean_song_filename)
        try:
            if organizer is None:
                print(f"Processing new song: {song.id} {song.title}")
                copyfile(song_file_path, song_file_path_organizer)
                organizer = Organizer(song_id=song.id, org_video_id=song.video_id)
                session.add(organizer)
                session.commit()
                print(f"Processed: {song_file_path}")
            else:
                if organizer.org_video_id != song.video_id:
                    # if video ID is not the same, it means that the videoID in the library has changed so
                    # the organized library needs updating.
                    if os.path.exists(song_file_path_organizer):
                        os.remove(song_file_path_organizer)
                    else:
                        print(
                            f"File not found for deletion: {song_file_path_organizer}"
                        )
                    copyfile(song_file_path, song_file_path_organizer)
                    organizer.org_video_id = song.video_id
                    session.commit()
                    print(f"Processed: {song_file_path}")
        except:
            continue

    return ""


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
    album_query = (
        session.query(Album).filter(Album.title.ilike(f"%{album_name}%")).all()
    )
    album_list_found = []
    for album in album_query:
        album_list_found.append(
            {"name": album.title, "number_of_songs": len(album.songs)}
        )
    return album_list_found

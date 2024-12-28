import hashlib
import os
from shutil import copyfile

import typer
from sqlalchemy.orm import Session

from amusing.core.download import download
from amusing.core.metadata import search_album_metadata, search_songs_metadata
from amusing.core.parse_csv import process_csv
from amusing.core.parse_xml import parse_library_xml
from amusing.core.save_to_db import check_if_song_in_db
from amusing.core.search import search
from amusing.db.engine import get_new_db_session
from amusing.db.models import Album, Organizer, Song
from amusing.utils.funcs import construct_db_path, short_filename, short_filename_clean


def download_song_operation(
    song_name: str,
    root_download_path: str,
    artist_name: str = None,
    album_name: str = None,
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
    song_metadata_dict = search_songs_metadata(song_name, artist_name, album_name)
    if song_metadata_dict:
        song = Song(
            title=song_metadata_dict["title"],
            artist=song_metadata_dict["artist"],
            album=Album(title=song_metadata_dict["album"]),
        )
        song.composer = song_metadata_dict["composer"]
        song.disc = song_metadata_dict["disc"]
        song.track = song_metadata_dict["track"]
    else:
        song = Song(
            title=song_name,
            artist=artist_name,
            album=Album(title=album_name),
        )
    # fetch song from YT Music
    song_fetched = search(song)
    if not song_fetched:
        return "Couldn't find song through YouTube Music Search."
    try:
        download(song_fetched, root_download_path, overwrite)
    except RuntimeError as e:
        print(f"[!] Error: {e}")
        return "Something went wrong while downloading a song."
    except FileNotFoundError as e:
        print(f"[!] Error: {e}")
        return "Is FFmpeg installed? It is required to generate the songs."

    # insert into db
    session = get_new_db_session(construct_db_path(root_download_path))
    albums = (
        session.query(Album).filter(Album.title.ilike(f"%{song.album.title}%")).all()
    )
    if albums:
        typer.echo(
            f"\n\n\nSimilar Albums are already present in the db. Do you want to download this song into any of these albums?"
        )
        choices = [album.title for album in albums] + ["Make a new album"]
        typer.echo("Select an album or create a new one:")
        for idx, choice in enumerate(choices, start=1):
            typer.echo(f"{idx}. {choice}")
        # Prompt user for a choice of album
        selected_choice = typer.prompt("Enter the option of your choice", type=int)
        if selected_choice == len(albums) + 1:
            # Create and commit the new album
            album = Album(title=album_name)
            session.add(album)
            session.commit()
            typer.echo(f"New album '{album_name}' created!")
        else:
            # Fetch the selected album from the database
            album = albums[selected_choice - 1]
            typer.echo(f"Selected album: {album.title}")

        # check if the song is present in the selected album in db
        song_present_in_db_query, error = check_if_song_in_db(
            song.title, song.artist, album, session
        )
        if song_present_in_db_query and overwrite:
            session.delete(song_present_in_db_query)
        song.album = album
        song.video_id = song_fetched.video_id
        session.add(song)
        session.commit()
    else:
        # Need to make a new album and a song in db
        album = Album(title=album_name)
        session.add(album)
        session.commit()
        typer.echo(f"New album '{album_name}' created!")
        song.album = album
        song.video_id = song_fetched.video_id
        session.add(song)
        session.commit()

    return "Added song!"


def _download_all_songs_for_given_album(
    album: Album, album_metadata: dict, root_download_path: str, session: Session
):
    """A companion function to download_album_operation to do exactly as it says on the tin."""
    for song_metadata_dict in album_metadata["track_list"]:
        print("---")
        choice = typer.prompt(
            f"Processing song: {song_metadata_dict['title']}. Press any key to continue or 's' to skip this song."
        )
        if choice == "s":
            continue
        song = Song(
            title=song_metadata_dict["title"],
            artist=song_metadata_dict["artist"],
            album=album,
        )
        song.composer = song_metadata_dict.get("composer")
        song.disc = song_metadata_dict.get("disc_number")
        song.track = song_metadata_dict.get("track_number")
        song.genre = song_metadata_dict.get("genre")
        # fetch song from YT Music
        song_fetched = search(song)
        if not song_fetched:
            return "Couldn't find song through YouTube Music Search."
        try:
            # this is necessary to keep consistency in between file names in db and downloads
            song_fetched.title = song_metadata_dict["title"]
            song_fetched.artist = song_metadata_dict["artist"]
            song_fetched.album = album
            download(song_fetched, root_download_path, True)
        except RuntimeError as e:
            print(f"[!] Error: {e}")
            return "Something went wrong while downloading a song."
        except FileNotFoundError as e:
            print(f"[!] Error: {e}")
            return "Is FFmpeg installed? It is required to generate the songs."
        # check if the song is present in the given album in db
        song_present_in_db_query, error = check_if_song_in_db(
            song.title, song.artist, album, session
        )
        if song_present_in_db_query:
            session.delete(song_present_in_db_query)
        song.album = album
        song.video_id = song_fetched.video_id
        session.add(song)
        session.commit()
    return "Added all songs!"


def download_album_operation(
    album_name: str,
    root_download_path: str,
    artist_name: str = None,
):
    """Download a particular album and all of its songs and add it to the db.

    Parameters:
    album_name (str): name of the album
    artist_name (str): name of the artist
    root_download_path (str): the path to download songs and put db into.
    """
    album_metadata = search_album_metadata(album_name, artist_name)

    # add new album to db or edit an existing album
    session = get_new_db_session(construct_db_path(root_download_path))
    albums = (
        session.query(Album)
        .filter(Album.title.ilike(f"%{album_metadata['title']}%"))
        .all()
    )
    num_tracks = album_metadata.get("num_tracks")
    if albums:
        typer.echo(
            f"\n\n\nSimilar Albums are already present in the db. Do you want to choose any of these albums to edit?"
        )
        choices = [album.title for album in albums] + ["Make a new album"]
        typer.echo("Select an album or create a new one:")
        for idx, choice in enumerate(choices, start=1):
            typer.echo(f"{idx}. {choice}")
        # Prompt user for a choice of album
        selected_choice = typer.prompt("Enter the option of your choice", type=int)
        if selected_choice == len(albums) + 1:
            # Create and commit the new album
            album = Album(
                title=album_metadata["title"],
                tracks=num_tracks,
                artist=album_metadata["artist"],
                release_date=album_metadata["release_date"],
                artwork_url=album_metadata["artwork_url"],
            )
            session.add(album)
            session.commit()
            typer.echo(f"New album '{album_name}' created!")
        elif 1 <= selected_choice <= len(albums):
            # Fetch the selected album from the database and edit it
            album = albums[selected_choice - 1]
            typer.echo(f"Selected album: {album.title}")
            album.title = album_metadata["title"]
            album.artist = album_metadata["artist"]
            album.tracks = num_tracks
            album.release_date = album_metadata["release_date"]
            album.artwork_url = album_metadata["artwork_url"]
            session.add(album)
            session.commit()
    else:
        # create a new album in db
        album = Album(
            title=album_metadata["title"],
            tracks=num_tracks,
            artist=album_metadata["artist"],
            release_date=album_metadata["release_date"],
            artwork_url=album_metadata["artwork_url"],
        )
        session.add(album)
        session.commit()
        typer.echo(f"New album '{album.title}' created!")

    return _download_all_songs_for_given_album(
        album, album_metadata, root_download_path, session
    )


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
        except Exception as e:
            print("Exception: ", e)
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

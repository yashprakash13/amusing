import os
import shutil
from datetime import datetime
from glob import glob
from importlib import metadata
from typing import Annotated

import click
import typer
from rich.console import Console
from rich.table import Table

from amusing.cli_operations import (
    create_album_metadata_in_db,
    download_song_operation,
    get_album_from_db,
    if_album_metadata_processed,
    modify_album_in_db,
    modify_song_in_db,
    parse_library_operation,
    show_similar_albums_in_db_operation,
    show_similar_songs_for_artist_in_db_operation,
    show_similar_songs_in_db_operation,
)
from amusing.core.musicbrainz import MusicBrainzFetcher
from amusing.utils.config import APP_CONFIG

app = typer.Typer(
    help="Amusing CLI to help download music independently or from your exported apple music library.",
    add_completion=False,
)
# __version__ = metadata.version("amusing-app")


# def version_callback(value: bool) -> None:
#     if value:
#         print(__version__)
#         raise typer.Exit()


# @app.callback()
# def callback(
#     _: bool = typer.Option(None, "--version", "-v", callback=version_callback)
# ) -> None:
#     """My app description"""


@app.command("song")
def download_song(
    name: Annotated[str, typer.Argument(help="Name of the song.")],
    artist: Annotated[str, typer.Argument(help="Aritst of the song.")],
    album: Annotated[str, typer.Argument(help="Album the song belongs to.")],
    force: Annotated[bool, typer.Option(help="Overwrite the song if present.")] = False,
):
    """Search and download the song and add it to the db. Use --force to overwrite the existing song in the db.
    Creates a new album if not already present.
    """
    print(f"Given: {name} from {album} by {artist} and force is {force}")
    output = download_song_operation(
        album, name, artist, APP_CONFIG["root_download_path"], False
    )
    print(output)


@app.command("download")
def parse_library(
    path: Annotated[
        str,
        typer.Argument(help="The path to the Library.xml exported from Apple Music."),
    ] = "./Library.xml"
):
    """Parse the entire AM library and download songs and make/update the db as needed."""
    print(f"Gotten path: {path}")
    parse_library_operation(APP_CONFIG["root_download_path"], path)


@app.command("showsimilar")
def show_similar_songs_in_db(
    name: Annotated[str, typer.Argument(help="Name of the song to search.")]
):
    """Look up the db and show if similar/exact song(s) are found."""
    print("Song to look up: ", name)
    results = show_similar_songs_in_db_operation(name, APP_CONFIG["root_download_path"])
    console = Console()
    table = Table("Song", "Artist", "Album")
    for res in results:
        table.add_row(res["name"], res["artist"], res["album"])
    console.print(table)


@app.command("showsimilarartist")
def show_similar_artists_in_db(
    name: Annotated[str, typer.Argument(help="Name of the artist to search.")]
):
    """Look up the db and show songs for similar/exact artist searched."""
    print("Artist to look up: ", name)
    results = show_similar_songs_for_artist_in_db_operation(
        name, APP_CONFIG["root_download_path"]
    )
    console = Console()
    table = Table("Song", "Artist", "Album")
    for res in results:
        table.add_row(res["name"], res["artist"], res["album"])
    console.print(table)


@app.command("showsimilaralbum")
def show_similar_artists_in_db(
    name: Annotated[str, typer.Argument(help="Name of the album to search.")]
):
    """Look up the db and show albums similar to the album searched."""
    print("Album to look up: ", name)
    results = show_similar_albums_in_db_operation(
        name, APP_CONFIG["root_download_path"]
    )
    console = Console()
    table = Table("Album", "Number of songs")
    for res in results:
        table.add_row(res["name"], str(res["number_of_songs"]))
    console.print(table)


@app.command("fetchmetadataall")
def fetch_metadata_all(
    root_dir: Annotated[
        str, typer.Argument(help="The directory to find your current music.")
    ],
    root_dir_new: Annotated[
        str, typer.Argument(help="The directory to keep your organized music.")
    ],
):
    """Start looking up metadata for all songs/albums in the library."""
    typer.echo("Starting metadata search...")
    ROOT_DIR_NEW = "/Users/costa/Desktop/ToDelete soon/new_song_dir"
    ROOT_DIR = "/Users/costa/Desktop/ToDelete soon/old_song_dir"
    all_albums = [
        d for d in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, d))
    ]
    album_choices = click.Choice(["y", "n", "id"])
    mb = MusicBrainzFetcher()
    for album in all_albums:
        typer.echo(
            "\n\n\n================================================================================"
        )
        typer.echo(f"Processing album: {album}")
        songs_in_directory = os.listdir(os.path.join(ROOT_DIR, album))
        songs_in_directory = [
            file for file in songs_in_directory if not file.startswith(".")
        ]
        songs_in_directory_clean = [
            mb.get_sanitized_song_name(song) for song in songs_in_directory
        ]
        # check if album has already been processed for metadata
        album_returned_from_db = if_album_metadata_processed(
            album, APP_CONFIG["root_download_path"]
        )
        if album_returned_from_db:
            album_json_data = mb.get_release_by_id(album_returned_from_db.album_mbid)
            typer.echo(
                f"Album fetched from db: \nName: {mb.get_true_album_name(album_json_data)}\nArtists: {album_json_data['artist-credit-phrase']}\nDate: {album_json_data['date']}\nTrack count: {album_json_data['medium-list'][0]['track-count']}"
            )
            fetch_and_save_metadata(
                album,
                album_json_data,
                mb,
                songs_in_directory,
                songs_in_directory_clean,
                fetch_coverart=False,
                album_metadata_present=True,
            )  # makes sure that any new songs available in the album are processed
            continue  # since we've already processed the album, we move on to the next one
        # the following runs is this is a new album
        responses, responses_dict_root_key = mb.search_releases(album_name=album)
        for album_json_data in responses[responses_dict_root_key]:
            typer.echo(
                f"This album info was fetched: \nName: {mb.get_true_album_name(album_json_data)}\nArtists: {album_json_data['artist-credit-phrase']}\nDate: {album_json_data['date']}\nTrack count: {album_json_data['medium-list'][0]['track-count']}"
            )
            album_found_correct = typer.prompt(
                f"Is this fetched album info correct? Y for yes, N for no, ID to enter Musicbrainz release ID manually",
                type=album_choices,
                show_choices=True,
            )
            if album_found_correct != "n":
                if album_found_correct == "id":
                    album_mbid = typer.prompt("Enter MBID for Album/Release")
                    album_json_data = mb.get_release_by_id(album_mbid)
                    typer.echo(
                        f"This album info was fetched from entered MBID: \nName: {mb.get_true_album_name(album_json_data)}\nArtists: {album_json_data['artist-credit-phrase']}\nDate: {album_json_data['date']}\nTrack count: {album_json_data['medium-list'][0]['track-count']}"
                    )
                fetch_and_save_metadata(
                    album,
                    album_json_data,
                    mb,
                    songs_in_directory,
                    songs_in_directory_clean,
                    fetch_coverart=True,
                    album_metadata_present=False,
                )
                break


def fetch_and_save_metadata(
    album: str,
    album_json_data: dict,
    mb: MusicBrainzFetcher,
    songs_in_directory: list,
    songs_in_directory_clean: list,
    fetch_coverart: bool = True,
    album_metadata_present=False,
):
    ROOT_DIR_NEW = "/Users/costa/Desktop/ToDelete soon/new_song_dir"
    ROOT_DIR = "/Users/costa/Desktop/ToDelete soon/old_song_dir"
    album_db_obj = get_album_from_db(album, APP_CONFIG["root_download_path"])
    album_path = os.path.join(
        ROOT_DIR_NEW,
        album_json_data["artist-credit-phrase"],
        mb.get_true_album_name(album_json_data),
    )
    os.makedirs(album_path, exist_ok=True)
    if fetch_coverart:
        mb.get_and_save_coverart(album_json_data["id"], album_path)
    all_recordings_dict = mb.browse_recordings(album_json_data["id"])
    typer.echo("Found all recordings: ")
    for item in all_recordings_dict:
        typer.echo(f"\t{item['title']} by {item['artist-credit-phrase']}")
    for recording in all_recordings_dict:
        closest_match, index_closest_match = mb.find_closest_match(
            mb.get_true_song_name(recording), songs_in_directory_clean, 80
        )
        if not closest_match:
            typer.echo(
                f"Song {mb.get_true_song_name(recording)} not in the collection. Skipping."
            )
            continue
        audio_file_path = os.path.join(
            ROOT_DIR, album, songs_in_directory[index_closest_match]
        )
        _, file_extension = os.path.splitext(audio_file_path)
        audio_file_path_dest = os.path.join(
            album_path, f"{mb.get_true_song_name(recording)}{file_extension}"
        )
        if os.path.exists(audio_file_path_dest):
            typer.echo(
                f"Song {mb.get_true_song_name(recording)} already present in the collection. Skipping."
            )
            continue
        recording_mb = mb.get_recording_by_id(recording["id"])
        typer.echo(
            f"Processing song: {mb.get_true_song_name(recording)} by {recording_mb['artist-credit-phrase']} with song from disk: {closest_match}"
        )
        date_object = datetime.strptime(
            recording_mb["release-list"][0]["date"], "%Y-%m-%d"
        )
        year = date_object.year
        month = date_object.month
        day = date_object.day
        metadata_dict = {
            "title": mb.get_true_song_name(recording_mb),
            "artist": recording_mb["artist-credit-phrase"],
            "album": mb.get_true_album_name(album_json_data),
            "year": year,
            "month": month,
            "day": day,
            "albumartist": album_json_data["artist-credit-phrase"],
            "mb_trackid": recording_mb["id"],
            "mb_albumid": album_json_data["id"],
        }
        shutil.copy(audio_file_path, album_path)
        os.rename(
            os.path.join(album_path, songs_in_directory[index_closest_match]),
            audio_file_path_dest,
        )
        mb.scrub(audio_file_path_dest)
        mb.perform_metadata_addition_to_mediafile(audio_file_path_dest, metadata_dict)

        # Do db operation on song because it's new
        filename, _ = os.path.splitext(songs_in_directory_clean[index_closest_match])
        error = modify_song_in_db(
            old_song_info={"name": filename, "album_id": album_db_obj.id},
            new_song_info={
                "name": mb.get_true_song_name(recording_mb),
                "artist": recording_mb["artist-credit-phrase"],
                "song_mbid": recording_mb["id"],
                "year": int(year),
                "month": int(month),
                "day": int(day),
            },
            root_download_path=APP_CONFIG["root_download_path"],
        )
        if not error:
            typer.echo("Written song to db.")

        typer.echo("-------------------------")

    # Do db operation on album if it's new
    if not album_metadata_present:
        # create metadata table entry for album
        create_album_metadata_in_db(
            album_metadata={"am_album_name": album, "album_id": album_db_obj.id},
            root_download_path=APP_CONFIG["root_download_path"],
        )
        typer.echo("Saved metadata entry for album.")
        # modify existing entry in album table
        if_coverart_saved = (
            glob(os.path.join(album_path, "*.jpg"))
            + glob(os.path.join(album_path, "*.png"))
            + glob(os.path.join(album_path, "*.jpeg"))
        )
        new_album_info_dict = {
            "name": mb.get_true_album_name(album_json_data),
            "album_mbid": album_json_data["id"],
            "album_artist": album_json_data["artist-credit-phrase"],
            "coverart_present": any(if_coverart_saved),
        }
        typer.echo(f"Saving: {new_album_info_dict}")
        modify_album_in_db(
            album=album_db_obj,
            new_album_info=new_album_info_dict,
            root_download_path=APP_CONFIG["root_download_path"],
        )
        typer.echo(f"Written album to db: {album_db_obj}")

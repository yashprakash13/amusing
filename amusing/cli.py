import os
import shutil
from datetime import datetime
from importlib import metadata
from typing import Annotated

import click
import typer
from rich.console import Console
from rich.table import Table

from amusing.cli_operations import (
    download_song_operation,
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
__version__ = metadata.version("amusing-app")


def version_callback(value: bool) -> None:
    if value:
        print(__version__)
        raise typer.Exit()


@app.callback()
def callback(
    _: bool = typer.Option(None, "--version", "-v", callback=version_callback)
) -> None:
    """My app description"""


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
            "================================================================================"
        )
        typer.echo(f"Processing album: {album}")
        responses, responses_dict_root_key = mb.search_releases(album_name=album)
        songs_in_directory = os.listdir(os.path.join(ROOT_DIR, album))
        songs_in_directory_clean = [
            mb.get_sanitized_song_name(song) for song in songs_in_directory
        ]
        for album_json_data in responses[responses_dict_root_key]:
            typer.echo(
                f"This album info was fetched: \nName: {album_json_data['title']}\nArtists: {album_json_data['artist-credit-phrase']}\nDate: {album_json_data['date']}\nTrack count: {album_json_data['medium-list'][0]['track-count']}"
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
                        f"This album info was fetched from entered MBID: \nName: {album_json_data['title']}\nArtists: {album_json_data['artist-credit-phrase']}\nDate: {album_json_data['date']}\nTrack count: {album_json_data['medium-list'][0]['track-count']}"
                    )
                album_path = os.path.join(
                    ROOT_DIR_NEW,
                    album_json_data["artist-credit-phrase"],
                    album_json_data["title"],
                )
                os.makedirs(album_path, exist_ok=True)
                mb.get_and_save_coverart(album_json_data["id"], album_path)
                all_recordings_dict = mb.browse_recordings(album_json_data["id"])
                typer.echo("Found all recordings: ")
                for item in all_recordings_dict:
                    typer.echo(f"\t{item['title']} by {item['artist-credit-phrase']}")
                for recording in all_recordings_dict:
                    closest_match, index_closest_match = mb.find_closest_match(
                        recording["title"], songs_in_directory_clean, 80
                    )
                    audio_file_path = os.path.join(
                        ROOT_DIR, album, songs_in_directory[index_closest_match]
                    )
                    _, file_extension = os.path.splitext(audio_file_path)
                    audio_file_path_dest = os.path.join(
                        album_path, f"{recording['title']}{file_extension}"
                    )
                    if not closest_match:
                        typer.echo(
                            f"Song {recording['title']} not in the collection. Skipping."
                        )
                        continue
                    if os.path.exists(audio_file_path_dest):
                        typer.echo(
                            f"Song {recording['title']} already present in the collection. Skipping."
                        )
                        continue
                    recording_mb = mb.get_recording_by_id(recording["id"])
                    typer.echo(
                        f"Processing song: {recording['title']} by {recording_mb['recording']['artist-credit-phrase']} with song from disk: {closest_match}"
                    )
                    date_object = datetime.strptime(
                        recording_mb["recording"]["release-list"][0]["date"], "%Y-%m-%d"
                    )
                    year = date_object.year
                    month = date_object.month
                    day = date_object.day
                    metadata_dict = {
                        "title": recording_mb["recording"]["title"],
                        "artist": recording_mb["recording"]["artist-credit-phrase"],
                        "album": album_json_data["title"],
                        "year": year,
                        "month": month,
                        "day": day,
                        "albumartist": album_json_data["artist-credit-phrase"],
                        "mb_trackid": recording_mb["recording"]["id"],
                        "mb_albumid": album_json_data["id"],
                    }
                    shutil.copy(audio_file_path, album_path)
                    os.rename(
                        os.path.join(
                            album_path, songs_in_directory[index_closest_match]
                        ),
                        audio_file_path_dest,
                    )
                    mb.scrub(audio_file_path_dest)
                    mb.perform_metadata_addition_to_mediafile(
                        audio_file_path_dest, metadata_dict
                    )
                    typer.echo("-------------------------")
                break

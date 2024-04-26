from importlib import metadata
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from amusing.cli_operations import (
    download_song_operation,
    parse_library_operation,
    download_library_operation,
    show_similar_albums_in_db_operation,
    show_similar_songs_for_artist_in_db_operation,
    show_similar_songs_in_db_operation,
)
from amusing.utils.config import APP_CONFIG

app = typer.Typer(
    help="CLI to download music independently and from your exported Apple Music library.",
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
    """Search and download the song and add it to the db.
    Creates a new album if not already present.
    """
    print(f"Given: {name} from {album} by {artist} and force is {force}")
    output = download_song_operation(
        album, name, artist, APP_CONFIG["root_download_path"], False
    )
    print(output)


@app.command("parse")
def parse_library(
    library_path: Annotated[
        str,
        typer.Argument(help="The path to the 'Library.xml' or 'Library.csv' exported from Apple Music."),
    ]
):
    """Parse the entire Apple Music library and make/update the DB as needed."""
    output = parse_library_operation(APP_CONFIG['root_download_path'], library_path)
    if output:
        print(output)


@app.command('download')
def download_library(
    library_path: Annotated[
        str,
        typer.Argument(help="The path to the 'Library.xml' or 'Library.csv' exported from Apple Music."),
    ] = ""
):
    """Download the entire DB library.

    If passed, parse the library and update the DB before download.
    """
    if library_path:
        parse_library_operation(APP_CONFIG['root_download_path'], library_path)

    output = download_library_operation(APP_CONFIG['root_download_path'])
    if output:
        print(output)


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

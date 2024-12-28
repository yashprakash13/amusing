from importlib import metadata
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from amusing.cli_operations import (
    download_album_operation,
    download_library_operation,
    download_song_operation,
    organize_library_operation,
    parse_library_operation,
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


@app.command("album")
def download_album(
    title: str = typer.Option(..., help="Title of the album"),
    artist: Optional[str] = typer.Option(None, help="Artist of the album (optional)"),
):
    """Search and download the album and add it and any or all of its songs to the db.
    Creates a new album if not already present.
    This is the preferred way of adding new songs/albums to the music library.
    """
    output = download_album_operation(title, APP_CONFIG["root_download_path"], artist)
    print(output)


@app.command("song")
def download_song(
    title: str = typer.Option(..., help="Title of the song"),
    artist: Optional[str] = typer.Option(None, help="Artist of the song (optional)"),
    album: Optional[str] = typer.Option(None, help="Album of the song (optional)"),
    force: Annotated[bool, typer.Option(help="Overwrite the song if present.")] = False,
):
    """Search and download an individual song and add it to the db.
    Creates a new album if not already present.
    """
    output = download_song_operation(
        title, APP_CONFIG["root_download_path"], artist, album, force
    )
    print(output)


@app.command("parse")
def parse_library(
    library_path: Annotated[
        str,
        typer.Argument(
            help="The path to the 'Library.xml' or 'Library.csv' exported from Apple Music."
        ),
    ]
):
    """Parse the entire Apple Music library and make/update the DB as needed."""
    output = parse_library_operation(APP_CONFIG["root_download_path"], library_path)
    if output:
        print(output)


@app.command("download")
def download_library(
    library_path: Annotated[
        str,
        typer.Argument(
            help="The path to the 'Library.xml' or 'Library.csv' exported from Apple Music."
        ),
    ] = ""
):
    """Download the entire DB library.

    If passed, parse the library and update the DB before download.
    """
    if library_path:
        parse_library_operation(APP_CONFIG["root_download_path"], library_path)

    output = download_library_operation(APP_CONFIG["root_download_path"])
    if output:
        print(output)


@app.command("organize")
def organize_library(
    destination_path: Annotated[
        str,
        typer.Argument(
            help="The full destination directory path for organized music, can be the path which an application like Plex is expecting."
        ),
    ]
):
    """To organize the music library for an applcation like Plex or Jellyfin.
    Organizes the music at the supplied destination in the form: ArtistName/AlbumName/Track.
    """

    output = organize_library_operation(
        APP_CONFIG["root_download_path"], destination_path
    )
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

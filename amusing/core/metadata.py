import re
import sys
from typing import Optional

import requests
import typer


def sanitize_input(input_str: str) -> str:
    """Remove non-alphanumeric characters (excluding whitespace) from input."""
    return re.sub(r"[^\w\s]", "", input_str)


def fetch_metadata_by_id(entity_type: str, entity_id: str):
    """Fetch metadata for a song or album using its MusicBrainz ID."""
    url = f"https://musicbrainz.org/ws/2/{entity_type}/{entity_id}"
    response = requests.get(
        url, params={"fmt": "json", "inc": "artist-credits+releases+media"}
    )
    if response.status_code != 200:
        typer.secho(f"Error fetching {entity_type} metadata by ID", fg=typer.colors.RED)
        sys.exit(1)

    return response.json()


def search_songs_metadata(
    title: str, artist: Optional[str] = None, album: Optional[str] = None
):
    """Search for songs based on title, artist, and album."""
    query = f'track:"{sanitize_input(title)}"'
    if artist:
        query += f' AND artist:"{sanitize_input(artist)}"'
    if album:
        query += f' AND release:"{sanitize_input(album)}"'
    typer.echo(f"Searching for: {query}")
    response = requests.get(
        "https://musicbrainz.org/ws/2/recording/",
        params={"query": query, "fmt": "json"},
    )

    if response.status_code != 200:
        typer.secho("Error fetching song metadata", fg=typer.colors.RED)
        sys.exit(1)

    results = response.json().get("recordings", [])
    if not results:
        typer.secho("No results found!", fg=typer.colors.YELLOW)
        use_id = typer.confirm(
            "Would you like to enter a MusicBrainz recording ID manually?"
        )
        if use_id:
            song_id = typer.prompt("Enter the MusicBrainz recording ID: ")
            song_metadata = fetch_metadata_by_id("recording", song_id)
            album_name = song_metadata.get("releases", [{}])[0].get("title", None)
            typer.echo("\nMetadata for the song by ID:")
            typer.echo(f"Title: {song_metadata.get('title')}")
            typer.echo(
                f"Artist: {song_metadata.get('artist-credit', [{}])[0].get('artist', {}).get('name', 'Unknown Artist')}"
            )
            typer.echo(f"Album: {album_name}")
            typer.echo(
                f"Composer: {', '.join([composer.get('name') for composer in song_metadata.get('artist-credit', [{}]) if composer.get('name')])}"
            )
            typer.echo(
                f"Genre: {song_metadata.get('tags', [{}])[0].get('name', 'Unknown Genre')}"
            )
            typer.echo(
                f"Track Number: {song_metadata.get('releases', [{}])[0].get('media', [{}])[0].get('tracks', [{}])[0].get('number', 'Unknown')}"
            )
            typer.echo(
                f"Disc Number: {song_metadata.get('releases', [{}])[0].get('media', [{}])[0].get('position', 'Unknown')}"
            )
            return {
                "title": song_metadata.get("title"),
                "artist": song_metadata.get("artist-credit", [{}])[0]
                .get("artist", {})
                .get("name", "Unknown Artist"),
                "album": album_name,
                "composer": ", ".join(
                    [
                        composer.get("name")
                        for composer in song_metadata.get("artist-credit", [{}])
                        if composer.get("name")
                    ]
                ),
                "disc": song_metadata.get("releases", [{}])[0]
                .get("media", [{}])[0]
                .get("position", "Unknown"),
                "track": song_metadata.get("releases", [{}])[0]
                .get("media", [{}])[0]
                .get("tracks", [{}])[0]
                .get("number", "Unknown"),
            }
        return

    for idx, recording in enumerate(results):
        typer.echo(
            f"[{idx + 1}] {recording.get('title')} - {recording.get('artist-credit', [{}])[0].get('name', 'Unknown Artist')} - {recording.get('releases', [{}])[0].get('title', 'Unknown Album')}"
        )
    typer.echo(f"[{len(results)+1}] Enter a Musicbrainz Recording ID")
    choice = typer.prompt("Select a song by number", type=int)
    if 1 <= choice <= len(results):
        song_metadata = results[choice - 1]
        album_name = song_metadata.get("releases", [{}])[0].get("title", None)
        typer.echo("\nMetadata for the selected song:")
        # typer.echo(f"{song_metadata}")
        typer.echo(f"Title: {song_metadata.get('title')}")
        typer.echo(
            f"Artist: {song_metadata.get('artist-credit', [{}])[0].get('artist', {}).get('name', 'Unknown Artist')}"
        )
        typer.echo(f"Album: {album_name}")
        typer.echo(
            f"Composer: {', '.join([composer.get('name') for composer in song_metadata.get('artist-credit', [{}]) if composer.get('name')])}"
        )
        typer.echo(
            f"Genre: {song_metadata.get('tags', [{}])[0].get('name', 'Unknown Genre')}"
        )
        typer.echo(
            f"Track Number: {song_metadata.get('releases', [{}])[0].get('media', [{}])[0].get('track', [{}])[0].get('number', 'Unknown')}"
        )
        typer.echo(
            f"Disc Number: {song_metadata.get('releases', [{}])[0].get('media', [{}])[0].get('position', 'Unknown')}"
        )
        return {
            "title": song_metadata.get("title"),
            "artist": song_metadata.get("artist-credit", [{}])[0]
            .get("artist", {})
            .get("name", "Unknown Artist"),
            "album": album_name,
            "composer": ", ".join(
                [
                    composer.get("name")
                    for composer in song_metadata.get("artist-credit", [{}])
                    if composer.get("name")
                ]
            ),
            "disc": song_metadata.get("releases", [{}])[0]
            .get("media", [{}])[0]
            .get("position", "Unknown"),
            "track": song_metadata.get("releases", [{}])[0]
            .get("media", [{}])[0]
            .get("track", [{}])[0]
            .get("number", "Unknown"),
        }
    elif choice == len(results) + 1:
        song_id = typer.prompt("Enter the MusicBrainz recording ID: ")
        song_metadata = fetch_metadata_by_id("recording", song_id)
        album_name = song_metadata.get("releases", [{}])[0].get("title", None)
        typer.echo("\nMetadata for the song by ID:")
        typer.echo(f"Title: {song_metadata.get('title')}")
        typer.echo(
            f"Artist: {song_metadata.get('artist-credit', [{}])[0].get('artist', {}).get('name', 'Unknown Artist')}"
        )
        typer.echo(f"Album: {album_name}")
        typer.echo(
            f"Composer: {', '.join([composer.get('name') for composer in song_metadata.get('artist-credit', [{}]) if composer.get('name')])}"
        )
        typer.echo(
            f"Genre: {song_metadata.get('tags', [{}])[0].get('name', 'Unknown Genre')}"
        )
        typer.echo(
            f"Track Number: {song_metadata.get('releases', [{}])[0].get('media', [{}])[0].get('tracks', [{}])[0].get('number', 'Unknown')}"
        )
        typer.echo(
            f"Disc Number: {song_metadata.get('releases', [{}])[0].get('media', [{}])[0].get('position', 'Unknown')}"
        )
        return {
            "title": song_metadata.get("title"),
            "artist": song_metadata.get("artist-credit", [{}])[0]
            .get("artist", {})
            .get("name", "Unknown Artist"),
            "album": album_name,
            "composer": ", ".join(
                [
                    composer.get("name")
                    for composer in song_metadata.get("artist-credit", [{}])
                    if composer.get("name")
                ]
            ),
            "disc": song_metadata.get("releases", [{}])[0]
            .get("media", [{}])[0]
            .get("position", "Unknown"),
            "track": song_metadata.get("releases", [{}])[0]
            .get("media", [{}])[0]
            .get("tracks", [{}])[0]
            .get("number", "Unknown"),
        }
    else:
        typer.secho("Invalid choice!", fg=typer.colors.RED)
        return None


def search_album_metadata(album: str, artist: Optional[str] = None):
    """Search for an album and fetch metadata for the album and its songs."""
    query = f'release:"{album}"'

    if artist:
        query += f' AND artist:"{artist}"'

    response = requests.get(
        "https://musicbrainz.org/ws/2/release/",
        params={"query": query, "fmt": "json"},
    )

    if response.status_code != 200:
        typer.secho("Error fetching album metadata", fg=typer.colors.RED)
        sys.exit(1)

    results = response.json().get("releases", [])
    if not results:
        typer.secho("No results found!", fg=typer.colors.YELLOW)
        return

    for idx, release in enumerate(results):
        typer.echo(
            f"[{idx + 1}] {release.get('title')} - {release.get('date', 'Unknown Date')} - {release.get('country', 'Unknown Country')}"
        )

    choice = typer.prompt("Select an album by number", type=int)
    if 1 <= choice <= len(results):
        album_metadata = results[choice - 1]
        artwork_url = get_album_artwork(album_metadata.get("id"))
        typer.echo("\nMetadata for the selected album:")
        typer.echo(f"Title: {album_metadata.get('title')}")
        typer.echo(f"Number of Tracks: {album_metadata.get('track-count', 'Unknown')}")
        typer.echo(
            f"Artist: {album_metadata.get('artist-credit', [{}])[0].get('name', 'Unknown Artist')}"
        )
        typer.echo(f"Release Date: {album_metadata.get('date', 'Unknown Date')}")
        typer.echo(f"Artwork URL: {artwork_url}")

        typer.echo("\nFetching tracklist...")
        album_id = album_metadata.get("id")
        track_response = requests.get(
            f"https://musicbrainz.org/ws/2/release/{album_id}",
            params={"inc": "recordings", "fmt": "json"},
        )

        if track_response.status_code != 200:
            typer.secho("Error fetching tracklist", fg=typer.colors.RED)
            sys.exit(1)

        track_data = track_response.json()
        tracks = track_data.get("media", [])[0].get("tracks", [])
        for idx, track in enumerate(tracks):
            typer.echo(
                f"Searching for: {track.get('title')} from {album_metadata.get('title')}"
            )
            search_songs_metadata(track.get("title"), album=album_metadata.get("title"))
    else:
        typer.secho("Invalid choice!", fg=typer.colors.RED)


def get_album_artwork(album_id: str) -> str:
    """Fetch the artwork URL for an album using the Cover Art Archive API."""
    response = requests.get(f"https://coverartarchive.org/release/{album_id}")
    if response.status_code == 200:
        images = response.json().get("images", [])
        if images:
            return images[0].get("image", "No Artwork Available")
    return "No Artwork Available"

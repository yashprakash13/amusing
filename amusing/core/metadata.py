import re
import sys
from typing import Optional

import requests
import typer


def sanitize_input(input_str: str) -> str:
    """Remove non-alphanumeric characters (excluding whitespace) from input."""
    return re.sub(r"[^\w\s]", "", input_str)


def fetch_metadata_by_id(
    entity_type: str,
    entity_id: str,
    include_params: str = "artist-credits+releases+media",
):
    """Fetch metadata for a song or album using its MusicBrainz ID."""
    url = f"https://musicbrainz.org/ws/2/{entity_type}/{entity_id}"
    response = requests.get(url, params={"fmt": "json", "inc": include_params})
    if response.status_code != 200:
        typer.secho(
            f"Error fetching {entity_type} metadata by ID, response code= {response.status_code}",
            fg=typer.colors.RED,
        )
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
            song_metadata = fetch_metadata_by_id(
                "recording", song_id, include_params="artist-credits+releases+media"
            )
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
        song_metadata = fetch_metadata_by_id(
            "recording", song_id, include_params="artist-credits+releases+media"
        )
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


def song_metadata_from_mb_json(song_metadata: dict) -> dict:
    return {
        "album_name": song_metadata.get("releases", [{}])[0].get("title", None),
        "title": song_metadata.get("title"),
        "artist": song_metadata.get("artist-credit", [{}])[0]
        .get("artist", {})
        .get("name", "Unknown Artist"),
        "composer": ", ".join(
            [
                composer.get("name")
                for composer in song_metadata.get("artist-credit", [{}])
                if composer.get("name")
            ]
        ),
        "genre": song_metadata.get("tags", [{}])[0].get("name", None),
        "track_number": song_metadata.get("releases", [{}])[0]
        .get("media", [{}])[0]
        .get("tracks", [{}])[0]
        .get("number", None),
        "disc_number": song_metadata.get("releases", [{}])[0]
        .get("media", [{}])[0]
        .get("position", None),
    }


def album_metadata_from_mb_json(album_metadata: dict) -> dict:
    return {
        "id": album_metadata.get("id"),
        "title": album_metadata.get("title"),
        "num_tracks": album_metadata.get("media")[0].get("track-count", "Unknown"),
        "artist": album_metadata.get("artist-credit", [{}])[0].get(
            "name", "Unknown Artist"
        ),
        "release_date": album_metadata.get("date", "Unknown Date"),
    }


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
        album_id = typer.prompt("Enter the MusicBrainz release ID or q to exit: ")
        if album_id == "q":
            sys.exit(1)
    else:
        for idx, release in enumerate(results):
            typer.echo(
                f"[{idx + 1}] {release.get('title')} - {release.get('date', 'Unknown Date')} - {release.get('country', 'Unknown Country')}"
            )

        choice = typer.prompt("Select an album by number", type=int)
        if 1 <= choice <= len(results):
            album_metadata = results[choice - 1]
            album_id = album_metadata.get("id")
        else:
            typer.secho("Invalid choice!", fg=typer.colors.RED)
            sys.exit(1)
    album_metadata = fetch_metadata_by_id(
        "release", album_id, include_params="artist-credits+media+recordings"
    )
    artwork_url = get_album_artwork(album_id)
    album_to_return = album_metadata_from_mb_json(album_metadata)
    album_to_return["artwork_url"] = artwork_url

    typer.echo("\nMetadata for the selected album:")
    typer.echo(f"Title: {album_to_return['title']}")
    typer.echo(f"Number of Tracks: {album_to_return['num_tracks']}")
    typer.echo(f"Artist: {album_to_return['artist']}")
    typer.echo(f"Release Date: {album_to_return['release_date']}")
    typer.echo(f"Artwork URL: {album_to_return['artwork_url']}")

    typer.echo("\nFetching tracklist...")
    if "media" in album_metadata:
        typer.echo("\nTracklist and metadata:")
        track_list = []
        for medium in album_metadata["media"]:
            for track in medium.get("tracks", []):
                track_metadata = fetch_metadata_by_id(
                    "recording",
                    track.get("recording", {}).get("id", ""),
                    include_params="artist-credits+releases+media",
                )
                # typer.echo(track_metadata["title"], "-", track_metadata["id"])
                track_list.append(song_metadata_from_mb_json(track_metadata))
        album_to_return["track_list"] = track_list
    return album_to_return


def get_album_artwork(album_id: str) -> str:
    """Fetch the artwork URL for an album using the Cover Art Archive API."""
    response = requests.get(f"https://coverartarchive.org/release/{album_id}")
    if response.status_code == 200:
        images = response.json().get("images", [])
        if images:
            return images[0].get("image", "No Artwork Available")
    return "No Artwork Available"

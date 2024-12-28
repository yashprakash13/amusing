import typer
from ytmusicapi import YTMusic

from amusing.db.models import Song


def search(song: Song) -> Song:
    """Search song on YouTube Music and return the first result."""
    ytmusic = YTMusic()
    search_results = ytmusic.search(
        f"{song.title} - {song.artist} - {song.album.title}",
        limit=5,
        ignore_spelling=True,
        filter="songs",
    )

    if not len(search_results):
        raise RuntimeError(
            f"song not found on YouTube Music: {song.title} - {song.album} - {song.artist}"
        )

    typer.echo("Youtube Music search results found, choose one:")
    choices = [
        f"{search_result.get('title', 'Unknown title')} - {search_result.get('videoId')}"
        for search_result in search_results[:5]
    ] + ["Enter a YT Music video ID"]
    for idx, choice in enumerate(choices, start=1):
        typer.echo(f"{idx}. {choice}")
    # Prompt user for a choice of YT Music video ID
    selected_choice = typer.prompt("Enter the option of your choice", type=int)
    if selected_choice == len(choices):
        song_video_id = typer.prompt("Enter the Youtube Music Video ID: ")
        # enter a video ID manually
        song_result = ytmusic.get_song(song_video_id)["videoDetails"]
    elif 1 <= selected_choice < len(choices):
        # select a video ID from the options
        song_result = search_results[selected_choice - 1]
    else:
        raise RuntimeError(
            "Something went wrong when trying to traverse through YouTube Music results."
        )
    result = song.clone()
    result.title = song_result["title"]
    if "artists" in song_result:
        result.artist = ", ".join(artist["name"] for artist in song_result["artists"])
    result.video_id = song_result["videoId"]
    if "album" in song_result:
        result.album.title = song_result["album"]["name"]
    return result

from ytmusicapi import YTMusic

from amusing.db.models import Song

def search(song: Song) -> Song:
    """Search song on YouTube Music and return the first result."""
    ytmusic = YTMusic()
    search_results = ytmusic.search(
        f"{song.title} - {song.artist} - {song.album.title}",
        limit=1,
        ignore_spelling=True,
        filter="songs"
    )

    if not len(search_results):
        raise RuntimeError(f"song not found on YouTube Music: '{song.title} - {song.album} - {song.artist}'")

    search_results = search_results[0]
    result = song.clone()
    result.title = search_results["title"]
    if "artists" in search_results:
        result.artist = ", ".join(
            artist["name"] for artist in search_results["artists"]
        )
    result.video_id = search_results["videoId"]
    if "album" in search_results:
        result.album.title = search_results["album"]["name"]

    return result

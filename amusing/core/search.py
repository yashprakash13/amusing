from ytmusicapi import YTMusic


def search_a_song(name: str, artist: str, album: str) -> dict:
    """Search a song and return the first result from YouTube Music."""
    ytmusic = YTMusic()
    if album == "None":
        album = ""
    search_results = ytmusic.search(
        f"{name} - {artist} - {album}", limit=1, ignore_spelling=True, filter="songs"
    )
    if len(search_results):
        search_results = search_results[0]
        try:
            artist_name, album_name, title = artist, album, name
            title = search_results["title"]
            if "artists" in search_results:
                artist_name = ", ".join(
                    artist["name"] for artist in search_results["artists"]
                )
            videoId = search_results["videoId"]
            if "album" in search_results:
                album_name = search_results["album"]["name"]
            return {
                "videoId": videoId,
                "album": album_name,
                "song_name": title,
                "artist_name": artist_name,
            }
        except Exception as e:
            print(f"Exception occured in searching... {e}")
    else:
        return {}

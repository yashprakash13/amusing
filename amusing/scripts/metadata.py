import json
import os
import time

import musicbrainzngs
import mutagen
import requests
from bs4 import BeautifulSoup
from googlesearch import search
from PIL import Image
from skimage import measure

musicbrainzngs.set_useragent("Chrome", "0.1")
responses = musicbrainzngs.search_releases(release="Sanam Re", status="official")
json_data = responses["release-list"][0]

# # just for test writing the output to json.
# json_data = json.dumps(responses['release-list'], indent=2)
# with open('output.json', 'w') as json_file:
#     json_file.write(json_data)


def find_and_rename_images(directory="."):
    front_images = [
        f
        for f in os.listdir(directory)
        if "Front" in f and f.endswith((".png", ".jpg", ".jpeg"))
    ]
    image_sizes = []
    for image in front_images:
        with Image.open(os.path.join(directory, image)) as img:
            image_sizes.append((image, img.size))

    largest_image = max(image_sizes, key=lambda x: x[1])

    for image in image_sizes:
        if image != largest_image:
            os.rename(
                os.path.join(directory, image[0]),
                os.path.join(directory, f"art{image_sizes.index(image) + 1}.png"),
            )

    # save the largest "Front" image type obtained as cover of the album/release.
    # The others are saved as "art1", "art2" and so on for the backdrop.
    os.rename(
        os.path.join(directory, largest_image[0]), os.path.join(directory, "cover.png")
    )

    # now if cover.png is present and a poster.png is also present, rename the
    # poster.png as banner.png
    if "cover.png" in os.listdir(directory) and "poster.png" in os.listdir("."):
        os.rename("poster.png", "banner.png")


# get the id of the release, artist name phrase, and year.
# print(f"Title= {json_data['title']}\nID= {json_data['id']}\nDate= {json_data['date']}\nArtist= {json_data['artist-credit-phrase']}")
# print(f"Song count= {json_data['medium-track-count']}")

# cover_art_list = musicbrainzngs.get_image_list(json_data['id'])['images']
# for index, cover_art in enumerate(cover_art_list):
#     with open(f"image_{index}", 'wb') as file:
#         cover_art_bin = musicbrainzngs.get_image(json_data['id'], cover_art['id'])
#         print(f"This is of type: {cover_art['types'][0]}")
#         file.write(cover_art_bin)
#     if cover_art['types'][0] == "Front":
#         Image.open(f"image_{index}").save(f"Front_{index}" + '.png', 'PNG')
#     else:
#         Image.open(f"image_{index}").save(f"{cover_art['types'][0]}" + '.png', 'PNG')
#     os.remove(f"image_{index}")
# find_and_rename_images()

# print("Cover art(s) saved.")


# song = mutagen.File("/Users/costa/Desktop/ToDelete soon/KYA TUJHE AB YE DIL BATAYE [AJq5l4FyDlA].m4a")
# song.delete()
# song["title"] = "Kya Tujhe Ab Ye Dil Bataye"
# song["artist"] = "Falak Shabbir"
# song.save()
# print(song.pprint())


import mutagen
from mutagen.id3 import ID3, TALB, TCON, TIT2, TPE1, TPE2, TRCK, TYER
from mutagen.mp3 import MP3

# Example metadata dictionary
metadata_dict = {
    "title": "Example Title",
    "artist": "Example Artist",
    "album": "Example Album",
    "tracknumber": "1",
    "date": "2023",
    "genre": "Example Genre",
    "albumartist": "Example Album Artist",
}

# Erase existing metadata and save the new ones
audio_file = "example.mp3"
audio = mutagen.File(audio_file, easy=True)
for tag, value in metadata_dict.items():
    audio[tag] = (
        mutagen.id3.ID3Text(encoding=3, text=value)
        if tag != "tracknumber"
        else mutagen.id3.TRCK(encoding=3, text=value)
    )
audio.save()


def get_lyrics_from_jiosaavn(song_name):
    """Search for the song lyrics for Hindi songs"""
    search_query = song_name + " site:jiosaavn.com"
    search_results = search(search_query, num_results=3)

    # Extract the URL from the search results
    for url in search_results:
        if "jiosaavn" in url and "lyrics" in url:
            print("Parsing url=> ", url)
            response = requests.get(url, headers={"Content-Type": "application/json"})
            # print(response.text)
            html = BeautifulSoup(response.text, "html.parser")
            section_tag = html.find("section")
            span_tags = section_tag.find_all("span")
            # Print the contents of all the <span> tags
            for span in span_tags:
                print(span.get_text())
            return

    print("Lyrics not found.", search_results)


# get_lyrics_from_jiosaavn("tu junooniyat (climax song)")


def get_lyrics_from_genius_or_azlyrics(song_name):
    """Search for the song lyrics of English/other language songs."""
    search_query = song_name + "lyrics"
    search_results = search(search_query, num_results=5)

    # Extract the URL from the search results
    for url in search_results:
        if "genius" in url:
            print("Parsing url=> ", url)
            response = requests.get(url, headers={"Content-Type": "application/json"})
            # print(response.text)
            html = BeautifulSoup(response.text, "html.parser")
            div_tags = html.find_all("div", attrs={"data-lyrics-container": "true"})
            for div in div_tags:
                print(div.get_text())
            return
        if "azlyrics" in url:
            print("Parsing url=> ", url)
            response = requests.get(url, headers={"Content-Type": "application/json"})
            # print(response.text)
            html = BeautifulSoup(response.text, "html.parser")
            lyrics = html.find("div", class_=None, id=None).get_text()
            print(lyrics)
            return
        time.sleep(3)

    print("Lyrics not found.", search_results)


# get_lyrics_from_genius_or_azlyrics("seventeen seventeen single charlotte lawrence")
# get_lyrics_from_genius_or_azlyrics("the a team + ed sheeran")

import os
import re
import xml.etree.ElementTree as ET

import pandas as pd
from unidecode import unidecode


def sort_library(library: pd.DataFrame) -> pd.DataFrame:
    library = library.sort_values(
        ["Disc Number", "Track Number"],
    )
    return library.sort_values(
        ["Sort Album Artist", "Sort Album"],
        key=lambda col: col.str.lower().map(
            lambda it: (
                # Force numbers to be sorted last
                lambda decoded: "~" + decoded
                if re.match(r"\A[0-9]", decoded)
                else decoded
            )(unidecode(it))
        ),
    )


def parse_library_xml(root_download_path: str, lib_path: str):
    try:
        tree = ET.parse(lib_path)
        root = tree.getroot()
        main_dict = root.findall("dict")
        for item in list(main_dict[0]):
            if item.tag == "dict":
                tracks_dict = item
                break
        tracklist = list(tracks_dict.findall("dict"))
        print(f"Total tracklist length: {len(tracklist)}")

        podcast = []
        purchased = []
        apple_music = []
        for item in tracklist:
            x = list(item)
            for i in range(len(x)):
                if x[i].text == "Genre" and x[i + 1].text == "Podcast":  #
                    podcast.append(list(item))
                if x[i].text == "Kind" and x[i + 1].text == "Purchased AAC audio file":
                    purchased.append(list(item))
                if (
                    x[i].text == "Kind"
                    and x[i + 1].text == "Apple Music AAC audio file"
                ):
                    apple_music.append(list(item))
        print(f"Total apple music library length: {len(apple_music)}")

        def cols(kind):
            cols = []
            for i in range(len(kind)):
                for j in range(len(kind[i])):
                    if kind[i][j].tag == "key":
                        cols.append(kind[i][j].text)
            return set(cols)

        podcast_cols = cols(podcast)
        purchased_cols = cols(purchased)
        apple_music_cols = cols(apple_music)

        def df_creation(kind, cols):
            df = pd.DataFrame(columns=cols)
            for i in range(len(kind)):
                dict1 = {}
                for j in range(len(kind[i])):
                    if kind[i][j].tag == "key":
                        if kind[i][j + 1].tag == "true":
                            dict1[kind[i][j].text] = True
                        elif kind[i][j + 1].tag == "false":
                            dict1[kind[i][j].text] = False
                        else:
                            dict1[kind[i][j].text] = kind[i][j + 1].text
                list_values = [i for i in dict1.values()]
                list_keys = [j for j in dict1.keys()]
                df_temp = pd.DataFrame([list_values], columns=list_keys)
                df = pd.concat([df, df_temp], axis=0, ignore_index=True, sort=True)
            return df

        df_apple_music = df_creation(apple_music, list(apple_music_cols))
        if not "Sort Album Artist" in df_apple_music:
            df_apple_music.insert(0, "Sort Album Artist", "")
        if not "Sort Composer" in df_apple_music:
            df_apple_music.insert(0, "Sort Composer", "")

        # Fill empty boolean fields
        df_apple_music = df_apple_music.fillna(
            {
                "Apple Music": False,
                "Compilation": False,
                "Explicit": False,
                "Favorited": False,
                "Loved": False,
                "Part Of Gapless Album": False,
                "Playlist Only": False,
            }
        )

        # Fill empty sorting fields
        df_apple_music = df_apple_music.fillna("")
        for i in range(len(df_apple_music)):
            if not df_apple_music.loc[i, "Sort Album Artist"]:
                df_apple_music.loc[i, "Sort Album Artist"] = df_apple_music.loc[
                    i, "Album Artist"
                ]
            if not df_apple_music.loc[i, "Sort Composer"]:
                df_apple_music.loc[i, "Sort Composer"] = df_apple_music.loc[
                    i, "Composer"
                ]

        # Move title column at the beginning
        title_column = df_apple_music.pop("Name")
        df_apple_music.insert(0, "Title", title_column)
        # Add album artwork column
        df_apple_music.insert(3, "Artwork URL", "")
        # Add video id column
        df_apple_music.insert(3, "Video ID", "")

        print("Dataframe created of length: ", len(df_apple_music))

        # Sort and keep only relevant fields
        df_apple_music = sort_library(
            df_apple_music[
                [
                    "Title",
                    "Album",
                    "Album Artist",
                    "Video ID",
                    "Artwork URL",
                    "Artist",
                    "Composer",
                    "Genre",
                    "Release Date",
                    "Year",
                    "Explicit",
                    "Disc Count",
                    "Disc Number",
                    "Track Count",
                    "Track Number",
                    "Favorited",
                    "Loved",
                    "Playlist Only",
                    "Sort Name",
                    "Sort Album",
                    "Sort Album Artist",
                    "Sort Artist",
                    "Sort Composer",
                ]
            ]
        )
        df_apple_music.to_csv(
            os.path.join(root_download_path, "Library.csv"), index=False
        )
    except Exception as e:
        print("Something went wrong in parsing your Library XML file: ", e)
        return 1

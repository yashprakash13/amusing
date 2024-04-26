import os
import xml.etree.ElementTree as ET

import pandas as pd


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
        # print(apple_music_cols)

        def df_creation(kind, cols):
            df = pd.DataFrame(columns=cols)
            dict1 = {}
            for i in range(len(kind)):
                for j in range(len(kind[i])):
                    if kind[i][j].tag == "key":
                        dict1[kind[i][j].text] = kind[i][j + 1].text
                list_values = [i for i in dict1.values()]
                list_keys = [j for j in dict1.keys()]
                df_temp = pd.DataFrame([list_values], columns=list_keys)
                df = pd.concat([df, df_temp], axis=0, ignore_index=True, sort=True)
            return df

        df_apple_music = df_creation(apple_music, list(apple_music_cols))

        # Move title column at the beginning
        title_column = df_apple_music.pop('Name')
        df_apple_music.insert(0, 'Title', title_column)
        # Add album artwork column
        df_apple_music.insert(2, 'Artwork URL', '')
        # Add video_id column
        df_apple_music.insert(2, 'Video ID', '')

        print("Dataframe created of length: ", len(df_apple_music))
        df_apple_music.to_csv(
            os.path.join(root_download_path, "Library.csv"), index=False
        )
    except Exception as e:
        print("Something went wrong in parsing your Library XML file: ", e)
        return 1

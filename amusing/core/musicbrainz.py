import os
import re
import shutil
from datetime import datetime
from enum import Enum

import click
import musicbrainzngs
import mutagen
from fuzzywuzzy import process
from mediafile import MediaFile, UnreadableFileError
from PIL import Image


class MusicBrainzFetcher:
    def __init__(self) -> None:
        musicbrainzngs.set_useragent("Chrome", "0.1")
        self.MUTAGEN_FORMATS = {
            "asf": "ASF",
            "apev2": "APEv2File",
            "flac": "FLAC",
            "id3": "ID3FileType",
            "mp3": "MP3",
            "mp4": "MP4",
            "oggflac": "OggFLAC",
            "oggspeex": "OggSpeex",
            "oggtheora": "OggTheora",
            "oggvorbis": "OggVorbis",
            "oggopus": "OggOpus",
            "trueaudio": "TrueAudio",
            "wavpack": "WavPack",
            "monkeysaudio": "MonkeysAudio",
            "optimfrog": "OptimFROG",
        }
        # self.ROOT_DIR_NEW = ROOT_DIR_NEW
        # self.ROOT_DIR = ROOT_DIR
        # self.all_albums = [
        #     d for d in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, d))
        # ]

    def get_sanitized_album_name(self, input_string: str):
        # Remove anything after '('
        # Remove characters after (, [, {, or -
        result = re.sub(r"[\(\[\{\-].*", "", input_string)
        return result.strip()

    def get_sanitized_song_name(self, input_string: str):
        # Remove anything after '('
        sanitized_string = re.sub(r"\[.*", "", input_string)
        # Remove any extra strings after the album name
        sanitized_string = re.sub(r"\s*-\s*.*", "", sanitized_string)
        return sanitized_string.strip()

    def _find_and_rename_images(self, directory):
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
            os.path.join(directory, largest_image[0]),
            os.path.join(directory, "cover.png"),
        )

        # now if cover.png is present and a poster.png is also present, rename the
        # poster.png as banner.png
        if "cover.png" in os.listdir(directory) and "Poster.png" in os.listdir(
            directory
        ):
            os.rename(
                os.path.join(directory, "Poster.png"),
                os.path.join(directory, "banner.png"),
            )

    def get_and_save_coverart(self, album_mbid, album_path):
        if "front.png" in os.listdir(album_path):
            print("Cover art already present in album. Skipping.")
            return
        cover_art_list = musicbrainzngs.get_image_list(album_mbid)["images"]
        for index, cover_art in enumerate(cover_art_list):
            temp_image_path = os.path.join(album_path, f"image_{index}")
            with open(temp_image_path, "wb") as file:
                cover_art_bin = musicbrainzngs.get_image(album_mbid, cover_art["id"])
                print(f"This is of type: {cover_art['types'][0]}")
                file.write(cover_art_bin)
            if cover_art["types"][0] == "Front":
                image_path = os.path.join(album_path, f"Front_{index}" + ".png")
                Image.open(temp_image_path).save(image_path, "PNG")
            else:
                image_path = os.path.join(
                    album_path, f"{cover_art['types'][0]}" + ".png"
                )
                Image.open(temp_image_path).save(image_path, "PNG")
            os.remove(temp_image_path)
        if cover_art_list:
            self._find_and_rename_images(album_path)

        print("Cover art(s) saved.")

    def find_closest_match(self, query, choices, threshold=80):
        choices_dict = {idx: el for idx, el in enumerate(choices)}
        result = process.extractOne(query, choices_dict)
        if result[1] >= threshold:
            return result[0], result[2]
        else:
            return None

    def _mutagen_classes(self):
        """Get a list of file type classes from the Mutagen module."""
        classes = []
        for modname, clsname in self.MUTAGEN_FORMATS.items():
            mod = __import__(f"mutagen.{modname}", fromlist=[clsname])
            classes.append(getattr(mod, clsname))
        return classes

    def scrub(self, path):
        """Remove all tags from a file."""
        mutagen_classes_list = self._mutagen_classes()
        for cls in mutagen_classes_list:
            # Try opening the file with this type, but just skip in the
            # event of any error.
            try:
                f = cls(path)
            except Exception:
                continue
            if f.tags is None:
                continue

            # Remove the tag for this type.
            try:
                f.delete()
            except NotImplementedError:
                # Some Mutagen metadata subclasses (namely, ASFTag) do not
                # support .delete(), presumably because it is impossible to
                # remove them. In this case, we just remove all the tags.
                for tag in f.keys():
                    del f[tag]
                f.save()
            except (OSError, mutagen.MutagenError) as exc:
                print("could not scrub {0}: {1}", path, exc)

    def perform_metadata_addition_to_mediafile(
        self, audio_file_path_dest: str, metadata_dict: dict
    ):
        try:
            mediafile = MediaFile(audio_file_path_dest)
        except UnreadableFileError as exc:
            print(exc)
        # Write the tags to the file.
        mediafile.update(metadata_dict)
        try:
            mediafile.save()
        except Exception as exc:
            print(exc)

    def search_releases(self, album_name: str):
        responses = musicbrainzngs.search_releases(
            release=self.get_sanitized_album_name(album_name), status="official"
        )
        return responses, "release-list"

    def browse_recordings(self, album_name: str):
        all_recordings_dict = musicbrainzngs.browse_recordings(
            release=album_name, includes=["artist-credits"]
        )["recording-list"]
        return all_recordings_dict

    def get_recording_by_id(self, recording_id):
        recording_mb = musicbrainzngs.get_recording_by_id(
            recording_id, includes=["artists", "releases"]
        )
        return recording_mb

    def get_release_by_id(self, album_mbid):
        release = musicbrainzngs.get_release_by_id(
            album_mbid, includes=["artists", "recordings"]
        )["release"]
        return release

    def fetch_lyrics_for_recording(self):
        pass

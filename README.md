# 🎧 Amusing 🎸

A CLI to download music independently and from your exported Apple Music library.

## Why should you use **Amusing**?

- To download your entire Apple Music Library and store it locally in one go
- To search and download individual songs from YouTube
- To keep track of your ever growing music collection

## 📦 Install it!

Install it as a [PyPI](https://pypi.org/) package:

```
pip install amusing-app
```

You will also need [FFmpeg](https://ffmpeg.org/) installed, which is required to embed song metadata (title, artist, album, cover art, ...) in the audio file.

## ✨ Getting set up

There are three things to know before moving on to the next section:

- The CLI takes in a `appconfig.yaml` file similar to what's indicated in `appconfig.example.yaml`. You can simply rename it.

  The file looks like this:

  ```yaml
  root_download_path: "..."
  db_name: "..."
  ```

  The file can be placed in two locations:
  1. `~/Downloads/Amusing/appconfig.yaml`: default one. If the file is not found anywhere it will be created here.
  2. `~/.config/amusing/appconfig.yaml`: only if the default one does not exist.

- A dedicated sqlite database called `db_name` will be created in `root_download_path/db_name.db` to store two tables `Song` and `Album` as defined in `amusing/db/models.py`. All songs downloaded locally will be getting a row in the `Song` table and a row for their corresponding album in the `Album` table.
- The songs are downloaded in `root_download_path/songs` directory.
- That's it. You're done. Let's look at the commands available next.

## 💬 Available commands

There are currently 7 commands available, excluding the `amusing --version`.

The first time you run a command (eg. `--help`), an `Amusing` directory will be created in the `~/Downloads` folder.
For eg., on MacOS, it's in `/Users/Username/Downloads`.

```console
$ amusing --help

 Usage: amusing [OPTIONS] COMMAND [ARGS]...

 CLI to download music independently and from your exported Apple Music library.

╭─ Options ─────────────────────────────────────────────────────────────────────╮
│ --version  -v                                                                 │
│ --help               Show this message and exit.                              │
╰───────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────╮
│ download           Download the entire DB library.                            │
│ parse              Parse the entire Apple Music library and make/update the   │
│                    DB as needed.                                              │
│ showsimilar        Look up the db and show if similar/exact song(s) are       │
│                    found.                                                     │
│ showsimilaralbum   Look up the db and show albums similar to the album        │
│                    searched.                                                  │
│ showsimilarartist  Look up the db and show songs for similar/exact artist     │
│                    searched.                                                  │
│ song               Search and download the song and add it to the db. Creates │
│                    a new album if not already present.                        │
╰───────────────────────────────────────────────────────────────────────────────╯
```

<details>

<summary><h3>Parse an exported <code>Library.xml</code> file from your Apple Music account</h3></summary>

You can also use a previously parsed `Library.csv`, that already contains mappings with YouTube video IDs and possible URLs to download custom album artworks.

```console
$ amusing parse --help

 Usage: amusing parse [OPTIONS] LIBRARY_PATH

 Parse the entire Apple Music library and make/update the DB as needed.

╭─ Arguments ───────────────────────────────────────────────────────────────────╮
│ *    library_path      TEXT  The path to the 'Library.xml' or 'Library.csv'   │
│                              exported from Apple Music.                       │
│                              [default: None]                                  │
│                              [required]                                       │
╰───────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                   │
╰───────────────────────────────────────────────────────────────────────────────╯

# Example
$ amusing parse 'your/path/to/Library.xml'
```

</details>


<details>

<summary><h3>Download the entire exported Apple Music library</h3></summary>

You can also pass a `Library.xml` or `Library.csv` file to parse before downloading the songs.

```console
$ amusing download --help

 Usage: amusing download [OPTIONS] [LIBRARY_PATH]

 Download the entire DB library.
 If passed, parse the library and update the DB before download.

╭─ Arguments ───────────────────────────────────────────────────────────────────╮
│   library_path      [LIBRARY_PATH]  The path to the 'Library.xml' or          │
│                                     'Library.csv' exported from Apple Music.  │
╰───────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                   │
╰───────────────────────────────────────────────────────────────────────────────╯

# Example
$ amusing download 'your/path/to/Library.xml'

# Is equivalent to run
$ amusing parse 'your/path/to/Library.xml'
$ amusing download
```

</details>


<details>

<summary><h3>Download an individual song</h3></summary>

```console
$ amusing song --help

 Usage: amusing song [OPTIONS] NAME ARTIST ALBUM

 Search and download the song and add it to the db. Creates a new album if not
 already present.

╭─ Arguments ───────────────────────────────────────────────────────────────────╮
│ *    name        TEXT  Name of the song. [default: None] [required]           │
│ *    artist      TEXT  Aritst of the song. [default: None] [required]         │
│ *    album       TEXT  Album the song belongs to. [default: None] [required]  │
╰───────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────╮
│ --force    --no-force      Overwrite the song if present. [default: no-force] │
│ --help                     Show this message and exit.                        │
╰───────────────────────────────────────────────────────────────────────────────╯

# Example, the search keywords need not be exact of course:
$ amusing song "Run" "One Republic" "Human"
```

</details>


<details>

<summary><h3>Search for a similar song, album or artist in your DB/downloads</h3></summary>

```console
$ amusing showsimilar "Someday"

Song to look up:  someday
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Song                 ┃ Artist        ┃ Album                                ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Someday              │ OneRepublic   │ Human (Deluxe)                       │
│ Someday At Christmas │ Justin Bieber │ Under the Mistletoe (Deluxe Edition) │
└──────────────────────┴───────────────┴──────────────────────────────────────┘


$ amusing showsimilarartist "OneRepublic"

Artist to look up:  OneRepublic
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Song            ┃ Artist      ┃ Album                                             ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Run             │ OneRepublic │ Human (Deluxe)                                    │
│ Someday         │ OneRepublic │ Human (Deluxe)                                    │
│ No Vacancy      │ OneRepublic │ No Vacancy - Single                               │
│ RUNAWAY         │ OneRepublic │ RUNAWAY - Single                                  │
│ Sunshine        │ OneRepublic │ Sunshine - Single                                 │
│ I Ain't Worried │ OneRepublic │ Top Gun: Maverick (Music from the Motion Picture) │
│ West Coast      │ OneRepublic │ West Coast - Single                               │
└─────────────────┴─────────────┴───────────────────────────────────────────────────┘


$ amusing showsimilaralbum "Human"

Album to look up:  Human
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Album          ┃ Number of songs ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Human (Deluxe) │ 2               │
└────────────────┴─────────────────┘
```

</details>


## 🛠️ Library customization

The resulting `Library.csv` file will be automatically updated by Amusing at every DB change.

You can manually modify it to change which YouTube video to download for a specific song.
You can also add a custom URL to download a specific album artwork.

Here are some great tools you can use to find album artworks:
- [Ben Dodson's iTunes Artwork Finder](https://bendodson.com/projects/itunes-artwork-finder/)
- [Ben Dodson's Apple Music Artwork Finder](https://bendodson.com/projects/apple-music-artwork-finder)

Copy the image link into your CSV file and Amusing will download it and embed it into your song the next time you run `amusing download '/path/to/Library.csv'`!


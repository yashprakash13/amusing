<h1> 🎧 Amusing 🎸 </h1>

A CLI to help download music independently or from your exported apple music library.

## Why should you use <strong>Amusing</strong>?

- To download your entire Apple Music Library and store it locally in one go
- To search and download individual songs from YouTube
- To keep track of your ever growing music collection

## 🛠️ Install it!

```console
$ pip install amusing-app
```

## ✨ Getting set up

There are three things to know before moving on to the next section:

- The CLI takes in a `appconfig.yaml` file similar to what's indicated in `appconfig.example.yaml`. You can simply rename it.
  The file looks like this:

  ```yaml
  root_download_path: "..."
  db_name: "..."
  ```

- A dedicated sqlite database called `db_name` will be created in `root_download_path/db_name.db` to store two tables `Song` and `Album` as defined in `amusing/db/models.py`. All songs downloaded locally will be getting a row in the `Song` table and a row for their corresponding album in the `Album` table.
- The songs are downloaded in `root_download_path/songs` directory.
- That's it. You're done. Let's look at the commands available next.

## 💬 Available commands

There are currently 6 commands available, excluding the `amusing --version`.

The first time you run a command (eg. --help), an `Amusing` directory will be created in your `pathlib.Path.home()/Downloads` folder. For eg., on MacOS, it's in `/Users/Username/Downloads`.

```console
$ amusing --help

 Created a new config file: /Users/username/Downloads/Amusing/appconfig.yaml

 Usage: amusing [OPTIONS] COMMAND [ARGS]...

 Amusing CLI to help download music independently or from your exported apple music library.

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version  -v                                                                                                                                  │
│ --help               Show this message and exit.                                                                                               │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ download           Parse the entire AM library and download songs and make/update the db as needed.                                            │
│ showsimilar        Look up the db and show if similar/exact song(s) are found.                                                                 │
│ showsimilaralbum   Look up the db and show albums similar to the album searched.                                                               │
│ showsimilarartist  Look up the db and show songs for similar/exact artist searched.                                                            │
│ song               Search and download the song and add it to the db. Use --force to overwrite the existing song in the db. Creates a new      │
│                    album if not already present.                                                                                               │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯


```

### To parse an exported `Library.xml` file from your Apple Music account, use:

```console
$ amusing download --help

 Usage: amusing download [OPTIONS] [PATH]

 Parse the entire AM library and download songs and make/update the db as needed.

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   path      [PATH]  The path to the Library.xml exported from Apple Music. [default: ./Library.xml]                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                    │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

# Example
$ amusing download "your/path/to/Library.xml"

```

### To download a song individually, use:

```console
$ amusing song --help

 Usage: amusing song [OPTIONS] NAME ARTIST ALBUM

 Search and download the song and add it to the db. Use --force to overwrite the existing song in the db. Creates a new album if not already
 present.

╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    name        TEXT  Name of the song. [default: None] [required]                                                                            │
│ *    artist      TEXT  Aritst of the song. [default: None] [required]                                                                          │
│ *    album       TEXT  Album the song belongs to. [default: None] [required]                                                                   │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --force    --no-force      Overwrite the song if present. [default: no-force]                                                                  │
│ --help                     Show this message and exit.                                                                                         │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯


# Example, the search keywords need not be exact of course:
$ amusing song "Run" "One Republic" "Human"

```

### Search for a similar song, album or artist in your db/downloads:

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

## TODO 📝

1. Provide an option to choose which searched result is downloaded.
2. Provide a command to show all songs in an album
3. Provide a command to download a song from youtube link
4. Better metadata availability (Musicbrainz, Discog etc)
5. Coverarts (Musicbrainz, somewhere else?)
6. Lyrics!
7. Look at which music player to integrate with, make changes to architecture of the library accordingly. The Music player needs to have:
   - Aesthetic UI, intuitive UX similar to Apple Music or Spotify
   - Play count, gapless playback, fade-in-out playback
   - Docker compose support
8. Modify/edit album names, artists manually
9. Delete songs, albums manually
10. Add/find Play Count equivalent in music player or in db

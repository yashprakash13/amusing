# 🎧 Amusing 🎸

A CLI application to download music independently and from your exported Apple Music library.

## Why should you use **Amusing**?

- To download your entire Apple Music Library and store it locally in one go
- To search and download individual albums and songs from YouTube
- To keep track of your ever growing music collection
- To organize and stream your music library through a self-hosted app like Plex, Navidrome or Jellyfin

### Features:

- Takes an exported Library.xml from your Apple Music and converts and exports it as a dataframe into Library.csv (`parse` command)
- Uses YouTube Music to download songs from the Library.csv (`download` command)
- The above two steps can be done automatically by a single `download` command
- The metadata for songs and albums are stored in a dedicated sqlite db, see `amusing/models.py` for the complete list of metadata 
- Can be used to download individual albums and songs outside of your Apple Music library (`album` and `song` commands). All metadata is extracted from MusicBrainz.
- Once downloaded, organize your library into a format that is expected by a typical music streaming application like Plex, Navidrome or Jellyfin: Artist/Album/Track (the `organize` command)

### Why not use a library like beets instead?

I found the `beets` library too hard to use so I built this. 

I know that beets is much more expansive than Amusing, but if you have or want a simple workflow that allows you to download albums and songs, extract metadata from a reliable source, and organize your music into a reliable format for use by a music streaming application, you'll find no simpler solution than Amusing. 



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

There are currently 8 commands available, excluding the `version` and `help` commands.

The first time you run a command (eg. `--help`), an `Amusing` directory will be created in the `~/Downloads` folder.
For eg., on MacOS, it's in `/Users/Username/Downloads`.

```console
$ amusing --help

                                                                                                                                                                                                          
 Usage: amusing [OPTIONS] COMMAND [ARGS]...                                                                                                                                                               
                                                                                                                                                                                                          
 CLI to download music independently and from your exported Apple Music library.                                                                                                                          
                                                                                                                                                                                                          
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --version  -v                                                                                                                                                                                          │
│ --help               Show this message and exit.                                                                                                                                                       │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ album              Search and download the album and add it and any or all of its songs to the db. Creates a new album if not already present. This is the preferred way of adding new songs/albums to │
│                    the music library.                                                                                                                                                                  │
│ download           Download the entire DB library.                                                                                                                                                     │
│ organize           To organize the music library for an applcation like Plex or Jellyfin. Organizes the music at the supplied destination in the form: ArtistName/AlbumName/Track.                     │
│ parse              Parse the entire Apple Music library and make/update the DB as needed.                                                                                                              │
│ showsimilar        Look up the db and show if similar/exact song(s) are found.                                                                                                                         │
│ showsimilaralbum   Look up the db and show albums similar to the album searched.                                                                                                                       │
│ showsimilarartist  Look up the db and show songs for similar/exact artist searched.                                                                                                                    │
│ song               Search and download an individual song and add it to the db. Creates a new album if not already present.                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯


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

You can also pass a `Library.xml` or a `Library.csv` file to parse before downloading the songs.

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

# is equivalent to running
$ amusing parse 'your/path/to/Library.xml'
$ amusing download
```

</details>


<details>
<summary><h3>Download a new album</h3></summary>

This is the recommended way to download a new album. You can choose to download a song or skip it with this method, and it either edits if an existing album is found, or adds a new album. 

```console
$ amusing album --help

                                                                                                                                                                                                         
 Usage: amusing album [OPTIONS]                                                                                                                                                                           
                                                                                                                                                                                                          
 Search and download the album and add it and any or all of its songs to the db. Creates a new album if not already present. This is the preferred way of adding new songs/albums to the music library.   
                                                                                                                                                                                                          
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --title         TEXT  Title of the album [default: None] [required]                                                                                                                                 │
│    --artist        TEXT  Artist of the album (optional) [default: None]                                                                                                                                │
│    --help                Show this message and exit.                                                                                                                                                   │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

# use it like so:
$ amusing album --title "808s & Heartbreak" --artist "Kanye West"

```

</details>


<details>

<summary><h3>Download an individual song</h3></summary>

```console
$ amusing song --help

Usage: amusing song [OPTIONS]                                                                                                                                                                            
                                                                                                                                                                                                          
 Search and download an individual song and add it to the db. Creates a new album if not already present.                                                                                                 
                                                                                                                                                                                                          
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *  --title                   TEXT  Title of the song [default: None] [required]                                                                                                                        │
│    --artist                  TEXT  Artist of the song (optional) [default: None]                                                                                                                       │
│    --album                   TEXT  Album of the song (optional) [default: None]                                                                                                                        │
│    --force     --no-force          Overwrite the song if present. [default: no-force]                                                                                                                  │
│    --help                          Show this message and exit.                                                                                                                                         │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯


 
$ amusing song --title "Run" --artist "One Republic" --album "Human"

```

</details>


<details>
<summary><h3>Organize your music collection for an application like Plex, Navidrome or Jellyfin</h3></summary>

This command helps organize your music library in a new place in the format: Artist/Album/Track 

```console

$ amusing organize --help

Usage: amusing organize [OPTIONS] DESTINATION_PATH                                                                                                                                                       
                                                                                                                                                                                                          
 To organize the music library for an applcation like Plex or Jellyfin. Organizes the music at the supplied destination in the form: ArtistName/AlbumName/Track.                                          
                                                                                                                                                                                                          
╭─ Arguments ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    destination_path      TEXT  The full destination directory path for organized music, can be the path which an application like Plex is expecting. [default: None] [required]                      │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                                                                                                                                            │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯


# use it like so:
$ amusing organize ~/Plex/Media/Music/


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
You can also add a new URL to download a specific album artwork or a specific YouTube video.

Here are some great tools you can use to find album artworks:
- [Ben Dodson's iTunes Artwork Finder](https://bendodson.com/projects/itunes-artwork-finder/)
- [Ben Dodson's Apple Music Artwork Finder](https://bendodson.com/projects/apple-music-artwork-finder)

You just need to run `amusing download '/path/to/Library.csv'` and you'll get the updated song/album metadata in your db and the new downloaded song in your collection. 

You can then use the `organize` command again to sort it out for your Plex application. Running the commnand will make sure to get the updated album(s)/song(s) into your organized music library. 

## 🪲 Bugs

Please open a new Issue to make a bug or an enhancement request known to me. 

Also, submit a PR with improvements or new features at your will. :)
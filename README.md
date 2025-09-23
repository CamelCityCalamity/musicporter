# MusicPorter

MusicPorter is a command-line tool which helps you copy playlists of MP3s from your PC to your phone (or another device). It lets you create smart playlists that match just the MP3s you want on your device, and also supports copying static playlists you might already have. It gathers up just the MP3s referenced by these playlists into one location for easily syncing to your device, while rewriting them to have file paths that will work on your device instead of the paths on your PC.

## Motivation

I have much more music on my PC than my phone can hold. I created this tool so I can copy just the "greatest hits" from my favorite artists (with playlists) to my Android phone. I use [Pi Music Player](https://pimusicplayer.com/) on Android which can load m3u8 files from the Android file system into its database. MusicPorter copies just the music matching my criteria to a folder that I can easily sync to my phone's Music and Playlists folder.

## Features

- Generate m3u8 playlists from a YAML configuration of smart playlist criteria.
- Supports copying static playlists, too. 
- Collect all music files referenced in these playlists, plus the playlists themselves, to some folder for easily syncing them to your phone or some other device.
- Lets you fix the paths in the playlists to support the directory structure of the target device.

Doesn't support non-MP3 audio files yet.

## Installation and Usage

I'll eventually publish this to PyPI, but for now, clone the repository, make a new virtual environment, and install it with pip. If your operating system doesn't require you to install local Python programs in a virtual environment, you can skip those steps (lines 3 and 4 below). 

### Linux instructions

```bash
git clone https://github.com/CamelCityCalamity/musicporter.git
cd musicporter
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

### Windows instructions

The only difference is how the virtual environment is activated.

```
git clone https://github.com/CamelCityCalamity/musicporter.git
cd musicporter
python -m venv .venv
.venv\Scripts\activate
pip install .
```

### Running the program

After installation, with the virtual environment activated, you can run the CLI. (You will need to activate the venv each time you close and reopen your command line.)

Here's a full example command:

```bash
musicporter -m /mnt/data/Music -m "/mnt/data/Music Singles" -y config/my-playlists.yaml -p static-playlists -r /mnt/data::/storage/emulated/0 output
```

This command does the following:

1. Scans for files in two separate folders: "Music" and "Music Singles"
2. Reads my smart playlists definitions from `./config/my-playlists.yaml`
3. Also reads my static playlists stored in `./static-playlists`
4. Performs a search/replace on all playlist paths to replace `/mnt/data/` with `storage/emulated/0`
5. Copies all referenced MP3s and all playlists to a folder named `./output`

The resultant directory structure is:

```
./output
├── Music
├── Music Singles
└── Playlists
```

### Program arguments

Use `musicporter --help` for details on options:

```
musicporter: generate smart music playlists and collect matching files for easily syncing to a phone.

positional arguments:
  output_path           Root output directory (Music, Playlists, etc. will be created here)

options:
  -h, --help            show this help message and exit
  -m, --music-path MUSIC_PATH
                        Path to a music directory to scan (can be specified multiple times)
  -y, --yaml-config YAML_CONFIG
                        Path to YAML config file for smart playlists
  -t, --temp-path TEMP_PATH
                        Temporary directory for generated playlists (default: new temp dir)
  -p, --playlists PLAYLISTS
                        Directory containing static playlists to copy
  -r, --search-replace SEARCH::REPLACE
                        Search/replace pair for paths in playlists. Can be specified multiple times.
  --skip-scan           Skip scanning music library and use existing database
  -v, --verbose         Enable verbose output
```

## Program steps

Here's a detailed description of what the program does.

### 1. Scan music files

Unless `--skip-scan` was specified, the program scans all music paths for MP3 files and stores each path and certain ID3 tags in a temporary SQLite database named tracks.sqlite in the output folder. Skipping the scan will reuse the previous database to speed up execution when you want to use different arguments or smart playlist criteria, but none of your music files have moved or changed.

### 2. Generate smart playlists

Generate smart playlists from a YAML config file of names and criteria.

The criteria for generating playlists supports the following fields from ID3 tags: artist, album, genre, rating, title, year, and comment, plus the path to the file itself. You use SQL-like query syntax to specify criteria.

Check out the example YAML config for criteria examples, and see the Playlist Criteria section below for a more complete list of allowed criteria.

### 3. Collect music

After the smart playlists are generated, the program copies all music files referenced by them to the output directory, preserving their relative directory structure. It does the same for any static playlists you specified. This is the main feature of the program: collecting only the music files you want on your device.

### 4. Rewrite playlists

Copy all of the m3u8 files to the output Playlists folder, rewriting path prefixes inside each playlist. This is for changing local music paths to be what your target device needs. For example, your music might be in `/home/your_name/Music`, but on your Android phone, maybe the path in the playlist files needs to be `/storage/emulated/0/Music`. The search/replace feature lets you rewrite the paths before copying the playlists to the output folder.

### Manually syncing the result

Once this is all done, it's up to you to use your favorite program to sync the music files and playlists to your device. Personally, I use the GUI program [Beyond Compare](https://www.scootersoftware.com/) to run a folder comparison and mirror the local output to my phone. It lets me ignore file time differences and only sync new files while deleting orphans (files that are no longer referenced in my playlists). I connect my phone using MTP, and mount it in the filesystem using simple-mtpfs.

I will include the bash file I use to mount my phone at the bottom of this readme.

## Playlist Criteria

### Example YAML Config

Here is an example `config.yaml` for making smart playlists:

```yaml
playlists:
  - name: "Crosby, Stills, Nash & Young"
    # "contains" matches substrings, and will match "Crosby, Stills & Nash", 
    # "Crosby, Stills, Nash, & Young", and "Neil Young" here
    criteria: artist contains ('Crosby, Stills', 'Neil Young') and rating >= 3
  - name: Rock Hits
    criteria: genre = 'Rock' and rating >= 4
  - name: "The Beatles 1965+"
    # "is", "=" and "==" all work the same.
    criteria: artist is 'The Beatles' and year >= 1965 and rating >= 3
  - name: Electronic and Pop
    # The "in" operator only does exact matches and this will not match 'Electronic Pop'
    criteria: genre in ('Pop', 'Electronic') and rating >= 3
  - name: Favorites
    criteria: rating = 5
  - name: "Morrissey Unrated"
    # "is", "=" and "==" all work the same. Parentheses and "or" are supported, too.
    # "and" has a higher precedence than "or" so parentheses are needed here.
    # "null", "nil", "none", "empty", and "missing" all work the same.
    criteria: (artist contains 'Smiths' or artist is 'Morrissey') and rating is null
  - name: "Bands starting with The"
    # ("ends with" works, too)
    criteria: artist starts with 'The'
  - name: "Non-video game music"
    # "not" is supported with certain other operations
    criteria: genre not starts with 'Video Game'
```

### Ratings

Ratings are read from the Popularity tag (POPM) and only supports whole-star ratings from 1-5, saved with the following values. Other values will be rounded down to the next whole star.

| Stars | POPM Value |
|-------|------------|
|   1   |     1      |
|   2   |    64      |
|   3   |   128      |
|   4   |   196      |
|   5   |   255      |

musicporter only reads the first POPM entry if there are multiple.

Music players like [Strawberry Music Player](https://www.strawberrymusicplayer.org/) support writing these tags when you rate music in the app. (Incidentally, Strawberry Music Player supports ratings in half-star increments, but only writes them to their proprietary `FMPS_Rating` user text frame as a decimal. I might add support for half-star ratings and this tag in the future.)

When defining playlists in your YAML config, you can use a flexible, SQL-like filter language to select tracks based on their metadata. 

### Fields You Can Filter On

- `path` (file path)
- `artist`
- `album`
- `genre`
- `rating`
- `title`
- `year`
- `comment`

### Comparison Operators

You can use these operators to compare fields and values:

- `=` or `==` or `is`: Exact match (e.g., `artist = 'The Beatles'`)
- `!=` or `<>`: Not exactly matching a value (e.g., `artist != 'The Beatles`)
- `>` or `<` or `>=` or `<=`: For numbers (e.g., `year >= 2000` or `rating < 4`)
- `contains` or `has`: Field contains a substring or any substring from a list (e.g., `artist contains 'Young'` or `artist contains ('Young', 'Money')`)
- `in`: Field matches any *exact* match from a list (e.g., `genre in ('Rock', 'Pop')`)
- `starts with`: Field starts with a substring (e.g., `artist starts with 'The'`)
- `ends with`: Field ends with a substring (e.g., `title ends with 'Love'`)
- These operators support adding "not": `is not` (or `not is`), `not contains`, `not has`, `not starts with`, `not ends with` (e.g., `genre not starts with 'Video Game'`)
- All comparisons are case-insensitive

### Value Types

- Strings: Use single or double quotes (`'Rock'`, `"Pop"`)
- Numbers: For fields like `year` or `rating`
- Null/Empty: Use `null`, `none`, `nil`, `empty`, or `missing` (case-insensitive) to match missing or empty values (e.g., `rating is null`)

### Combining Conditions

- Use `and` and `or` to combine multiple conditions.
- Parentheses `()` can group conditions and control precedence.

#### Examples

- `artist contains ('Crosby', 'Young') and rating >= 3`
- `genre in ('Pop', 'Electronic') and year >= 2010`
- `artist is 'The Beatles' and year >= 1965 and rating >= 3`
- `rating = 5`
- `(artist contains 'Smiths' or artist is 'Morrissey') and rating is null`
- `artist starts with 'The'`

## Requirements

- Python 3.9+

Dependencies installed during module install:

- eyed3 (MP3 tag reader)
- lark (language parser)
- PyYAML (yaml parser)

## Running Tests

This project contains unit tests using pytest.

Dependencies:

- pytest

To run tests, first run `tests/generate_mock_mp3s.py`. This creates silent mock MP3s in `tests/testdata` using the data in `mock_mp3_metadata.yaml`

To run all of the tests, simply run `pytest` in the root of the project folder.

## License

This project is licensed under the terms of the GNU General Public License v3.0 or later (GPL-3.0-or-later). See the LICENSE file for details.

## Mounting phone with simple-mtpfs under KDE

This is the bash script I use to mount my phone via MTP. I'm sure it can be improved.

```bash
#!/usr/bin/env bash

ID="18d1:4ee2" # Pixel 7 Pro
MOUNT_DIR="/home/me/.local/share/mounts/phone/"

# Remove a trailing slash from MOUNT_DIR if it's there, since it's not in the output of `mount`
MOUNT_DIR="${MOUNT_DIR%/}"

if mount | grep -q "simple-mtpfs.*$MOUNT_DIR"; then
    echo "$MOUNT_DIR is already mounted with simple-mtpfs."
else
    # Make sure phone is connected by MTP
    if mtp-detect 2>/dev/null | grep -q "No raw devices found"; then
        echo "Phone not connected. Please connect your phone via MTP."
        exit 1
    fi

    #Getting device data from lsusb using its ID. This is only so we can kill any process using it
    DATA=`lsusb | grep "$ID"`
    if [[ -z "$DATA" ]]; then
        echo "Device with ID $ID not found in lsusb output."
        exit 1
    fi

    # Reading the bus number:
    BUS=`echo ${DATA:4:3}`

    # Reading the device number:
    DEV=`echo ${DATA:15:3}`

    echo "Found device: 18d1:4ee2 at $BUS/$DEV"

    # This is required when using KDE, because the device will already be in use, even if not yet mounted
    echo "Killing process using device"
    fuser -k /dev/bus/usb/$BUS/$DEV

    # Clean up and remake mount directory
    if [ -d "$MOUNT_DIR" ]; then
        echo "Unmounting and removing $MOUNT_DIR if needed"
        fusermount -u "$MOUNT_DIR"
        rmdir "$MOUNT_DIR"
    fi

    # Make mount directory
    mkdir -p "$MOUNT_DIR"

    echo "Mounting device with simple-mtpfs"
    if ! simple-mtpfs --device 1 "$MOUNT_DIR"; then
        echo "Failed to mount phone with simple-mtpfs."
        exit 1
    fi
fi

if ! musicporter -m /mnt/data/Music -m "/mnt/data/Music Singles" -y config/my-playlists.yaml -p static-playlists -r /mnt/data::/storage/emulated/0 output; then
    echo "Failed to prepare music with musicporter."
    exit 1
fi

# Run Beyond Compare using the name of my previously saved session
bcompare musicporter &
```

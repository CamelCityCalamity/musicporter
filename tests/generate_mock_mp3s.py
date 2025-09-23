# type: ignore
import os
import yaml
import subprocess
import eyed3

eyed3.log.setLevel("ERROR")

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')
MOCK_METADATA_PATH = os.path.join(os.path.dirname(__file__), 'mock_mp3_metadata.yaml')

def main(remake_files):
    '''
    Generate mock MP3 files based on the metadata in mock_mp3_metadata.yaml.

    Requires ffmpeg and eyed3.

    If remake_files is True, existing files will be overwritten.
    1. Read metadata from mock_mp3_metadata.yaml.
    2. For each track, generate a silent MP3 file of the specified length using ffmpeg.
    3. Tag the MP3 file with the provided metadata using eyed3.
    '''
    with open(MOCK_METADATA_PATH, 'r') as f:
        data = yaml.safe_load(f)

    for artist_entry in data:
        artist = artist_entry.get('artist')
        artist_tag = artist if artist and artist.strip() != '' else None
        artist_fs = artist if artist and artist.strip() != '' else 'Unknown Artist'
        for album_entry in artist_entry['albums']:
            album = album_entry.get('album')
            album_tag = album if album and album.strip() != '' else None
            album_fs = album if album and album.strip() != '' else 'Unknown Album'
            year = album_entry.get('year')
            tracks = album_entry['tracks']
            for idx, track in enumerate(tracks, 1):
                title = track.get('title')
                title_tag = title if title and title.strip() != '' else None
                title_fs = title if title and title.strip() != '' else 'Unknown Title'
                genre = track.get('genre')
                length = track['length']
                rating = track.get('rating')
                # Directory: tests/testdata/artist/album/
                dir_path = os.path.join(TESTDATA_DIR, artist_fs, album_fs)
                # File: NN Title.mp3
                filename = f"{idx:02d} {title_fs}.mp3"
                out_path = os.path.join(dir_path, filename)
                print(f"Generating {out_path} ({length}s)")
                generate_silence_mp3(out_path, length, remake_files)
                tag_mp3(out_path, artist_tag, album_tag, year, title_tag, genre, rating, idx)

def generate_silence_mp3(out_path, duration, remake_file):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    overwrite_switch = '-y' if remake_file else '-n'
    cmd = [
        'ffmpeg', overwrite_switch, '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo',
        '-t', str(duration), '-q:a', '9', '-acodec', 'libmp3lame', out_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def tag_mp3(mp3_path, artist, album, year, title, genre, rating, track_num):
    audio = eyed3.load(mp3_path)
    if audio is None:
        audio = eyed3.load(mp3_path)
    if audio.tag is None:
        audio.initTag()
    audio.tag.artist = artist
    audio.tag.album = album
    audio.tag.title = title
    if genre is not None:
        audio.tag.genre = genre
    audio.tag.track_num = track_num
    if year:
        try:
            year_int = int(year)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid year value: {year!r}")
        audio.tag.recording_date = eyed3.core.Date(year_int)
    RATING_TO_POPM = {
        1: 1,    # 1 star
        2: 64,   # 2 stars
        3: 128,  # 3 stars
        4: 196,  # 4 stars
        5: 255   # 5 stars
    }
    if rating is not None:
        popm_rating = RATING_TO_POPM.get(int(rating))
        if popm_rating is not None:
            audio.tag.popularities.set('test@example.com', popm_rating, 0)
    audio.tag.save()

if __name__ == "__main__":
    main(False)

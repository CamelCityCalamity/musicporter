import os
from musicporter.db import TrackDB
from musicporter.mp3_scanner import Mp3Scanner
from musicporter.playlist_generator import PlaylistGenerator
import pytest

# Path to the testdata directory with mock MP3s
TESTDATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'testdata'))

def run_playlist_generator(config_path):
    scanner = Mp3Scanner()
    tracks = scanner.scan([TESTDATA_DIR])

    db_path = os.path.join(os.path.dirname(config_path), "tracks.sqlite")
    db = TrackDB(db_path)
    db.insert_tracks(tracks)
    db.close()

    generator = PlaylistGenerator()
    generator.generate_from_config(config_path, db_path, os.path.dirname(config_path))

def check_playlist_file(playlist_file, expected_tracks):
    assert playlist_file.exists(), f"Playlist file {playlist_file} does not exist"
    with open(playlist_file) as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    for track in expected_tracks:
        assert any(track in line for line in lines), f"Expected track {track} not found in playlist"

def test_rock_favorites(tmp_path):
    # Example: create a minimal YAML config for this test
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
    - name: Rock Favorites
      criteria: genre is 'Rock' and rating >= 4
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)

    run_playlist_generator(str(config_path))

    # These are the expected tracks for 'Rock Favorites' (genre is 'Rock' and rating >= 4)
    expected_tracks = [
        "Thunder Lizards/Stone Age Groove/01 Rock the Bones.mp3",
        "Thunder Lizards/Stone Age Groove/02 Fossil Fuel.mp3",
        "Thunder Lizards/Fossilized Funk/02 Dino Disco.mp3"
    ]
    playlist_file = tmp_path / "Rock Favorites.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_simon_and_or_garfunkel(tmp_path):
    # Example: create a minimal YAML config for this test
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
    - name: Simon and-or Garfunkel
      criteria: artist contains ('Paul Simon', 'Simon & Garfunkel')
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)

    run_playlist_generator(str(config_path))

    # These are the expected tracks for 'Rock Favorites' (genre is 'Rock' and rating >= 4)
    expected_tracks = [
        "Simon & Garfunkel/Bridge Over Troubled Water/01 The Boxer.mp3",
        "Simon & Garfunkel/Bridge Over Troubled Water/02 Cecilia.mp3",
        "Paul Simon/Graceland/01 Graceland.mp3",
        "Paul Simon/Graceland/02 You Can Call Me Al.mp3",
        "Paul Simon/Graceland/03 Diamonds on the Soles of Her Shoes.mp3"
    ]
    playlist_file = tmp_path / "Simon and-or Garfunkel.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_genre_is_none(tmp_path):
    # Example: create a minimal YAML config for this test
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
    - name: Genre is Null
      criteria: genre is None
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)

    run_playlist_generator(str(config_path))

    # These are the expected tracks for 'Rock Favorites' (genre is 'Rock' and rating >= 4)
    expected_tracks = [
        "Nearly No Tags/Test Album 1/01 Track One.mp3"
    ]
    playlist_file = tmp_path / "Genre is Null.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_everything_is_none(tmp_path):
    # Example: create a minimal YAML config for this test
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
    - name: Everything is Null
      criteria: artist is null and album is nil and title is empty and rating is none and year is missing
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)

    run_playlist_generator(str(config_path))

    # These are the expected tracks for 'Rock Favorites' (genre is 'Rock' and rating >= 4)
    expected_tracks = [
        "Unknown Artist/Unknown Album/01 Unknown Title.mp3"
    ]
    playlist_file = tmp_path / "Everything is Null.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_genre_is_literal_none(tmp_path):
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
    - name: Genre is literal None
      criteria: genre is 'None'
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)

    run_playlist_generator(str(config_path))

    expected_tracks = [
        "Test Literal None/None Album/01 None Song.mp3"
    ]
    playlist_file = tmp_path / "Genre is literal None.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_rating_in_list(tmp_path):
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
    - name: Rating in List
      criteria: rating in (2, 5)
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)
    run_playlist_generator(str(config_path))
    # Should match all tracks with rating 2 or 5
    expected_tracks = [
        # Thunder Lizards
        "Thunder Lizards/Fossilized Funk/01 Petrified Blues.mp3",
        "Thunder Lizards/Fossilized Funk/02 Dino Disco.mp3",
        "Thunder Lizards/Stone Age Groove/01 Rock the Bones.mp3",
        # Neon Skyline
        "Neon Skyline/Neon Nights/01 Dusk to Dawn.mp3",
        "Neon Skyline/City Lights/03 Electric Heart.mp3",
        # Blue Note Quartet
        "Blue Note Quartet/Midnight Sessions/03 Nightcap.mp3",
        # Arpeggio
        "Arpeggio/Strings & Things/03 Harmonic Drift.mp3",
        # Various Artists
        "Various Artists/Pixel Quest/01 Main Theme.mp3",
        # 8Bit Heroes
        "8Bit Heroes/Retro Adventure/02 Boss Battle.mp3",
        # Simon & Garfunkel
        "Simon & Garfunkel/Bridge Over Troubled Water/01 The Boxer.mp3",
        # Paul Simon
        "Paul Simon/Graceland/01 Graceland.mp3",
        # Test Literal None
        "Test Literal None/None Album/01 None Song.mp3",
    ]
    playlist_file = tmp_path / "Rating in List.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_album_contains_word(tmp_path):
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
    - name: Album Contains 'Funk'
      criteria: album contains 'Funk'
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)
    run_playlist_generator(str(config_path))
    expected_tracks = [
        "Thunder Lizards/Fossilized Funk/01 Petrified Blues.mp3",
        "Thunder Lizards/Fossilized Funk/02 Dino Disco.mp3",
    ]
    playlist_file = tmp_path / "Album Contains 'Funk'.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_artist_starts_with_paul(tmp_path):
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
    - name: Artist Starts With Paul
      criteria: artist starts with 'Paul'
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)
    run_playlist_generator(str(config_path))
    expected_tracks = [
        "Paul Simon/Graceland/01 Graceland.mp3",
        "Paul Simon/Graceland/02 You Can Call Me Al.mp3",
        "Paul Simon/Graceland/03 Diamonds on the Soles of Her Shoes.mp3",
    ]
    playlist_file = tmp_path / "Artist Starts With Paul.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_in_list_in_field(tmp_path):
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
    - name: Folk or Jazz Album
      criteria: genre in ('Folk', 'Jazz')
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)
    run_playlist_generator(str(config_path))
    expected_tracks = [
        "Blue Note Quartet/Midnight Sessions/01 Blue Hour.mp3",
        "Blue Note Quartet/Midnight Sessions/02 Afterglow.mp3",
        "Blue Note Quartet/Midnight Sessions/03 Nightcap.mp3",
        "Simon & Garfunkel/Bridge Over Troubled Water/01 The Boxer.mp3",
        "Simon & Garfunkel/Bridge Over Troubled Water/02 Cecilia.mp3",
        "Paul Simon/Graceland/01 Graceland.mp3",
        "Paul Simon/Graceland/02 You Can Call Me Al.mp3",
        "Paul Simon/Graceland/03 Diamonds on the Soles of Her Shoes.mp3",
    ]
    playlist_file = tmp_path / "Folk or Jazz Album.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_rating_is_5(tmp_path):
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
  - name: Rating is 5
    criteria: rating = 5
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)
    run_playlist_generator(str(config_path))
    expected_tracks = [
        "Thunder Lizards/Stone Age Groove/01 Rock the Bones.mp3",
        "Thunder Lizards/Fossilized Funk/02 Dino Disco.mp3",
        "Neon Skyline/City Lights/03 Electric Heart.mp3",
        "Blue Note Quartet/Midnight Sessions/03 Nightcap.mp3",
        "Arpeggio/Strings & Things/03 Harmonic Drift.mp3",
        "Various Artists/Pixel Quest/01 Main Theme.mp3",
        "8Bit Heroes/Retro Adventure/02 Boss Battle.mp3",
        "Simon & Garfunkel/Bridge Over Troubled Water/01 The Boxer.mp3",
        "Paul Simon/Graceland/01 Graceland.mp3",
    ]
    playlist_file = tmp_path / "Rating is 5.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_title_ends_with_fanfare(tmp_path):
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
  - name: Title Ends With Fanfare
    criteria: title ends with 'Fanfare'
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)
    run_playlist_generator(str(config_path))
    expected_tracks = [
        "8Bit Heroes/Retro Adventure/03 Victory Fanfare.mp3",
    ]
    playlist_file = tmp_path / "Title Ends With Fanfare.m3u8"
    check_playlist_file(playlist_file, expected_tracks)

def test_genre_not_rock(tmp_path):
    config_yaml = f"""
output_path: {tmp_path}
music_paths:
  - {TESTDATA_DIR}
playlists:
  - name: Genre Not Rock
    criteria: genre != 'Rock' or genre is null
"""
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text(config_yaml)
    run_playlist_generator(str(config_path))
    # Should match all tracks whose genre is not 'Rock' (including NULL genres)
    expected_tracks = [
        "Neon Skyline/City Lights/01 Night Drive.mp3",
        "Neon Skyline/City Lights/02 Skyline Dreams.mp3",
        "Neon Skyline/City Lights/03 Electric Heart.mp3",
        "Neon Skyline/Neon Nights/01 Dusk to Dawn.mp3",
        "Neon Skyline/Neon Nights/02 Midnight Pulse.mp3",
        "Blue Note Quartet/Midnight Sessions/01 Blue Hour.mp3",
        "Blue Note Quartet/Midnight Sessions/02 Afterglow.mp3",
        "Blue Note Quartet/Midnight Sessions/03 Nightcap.mp3",
        "Arpeggio/Strings & Things/01 Plucked Memories.mp3",
        "Arpeggio/Strings & Things/02 Bowed Reflections.mp3",
        "Arpeggio/Strings & Things/03 Harmonic Drift.mp3",
        "Various Artists/Pixel Quest/01 Main Theme.mp3",
        "Various Artists/Pixel Quest/02 Level Up.mp3",
        "8Bit Heroes/Retro Adventure/01 Start Game.mp3",
        "8Bit Heroes/Retro Adventure/02 Boss Battle.mp3",
        "8Bit Heroes/Retro Adventure/03 Victory Fanfare.mp3",
        "Simon & Garfunkel/Bridge Over Troubled Water/01 The Boxer.mp3",
        "Simon & Garfunkel/Bridge Over Troubled Water/02 Cecilia.mp3",
        "Paul Simon/Graceland/01 Graceland.mp3",
        "Paul Simon/Graceland/02 You Can Call Me Al.mp3",
        "Paul Simon/Graceland/03 Diamonds on the Soles of Her Shoes.mp3",
        "Test Literal None/None Album/01 None Song.mp3",
        "Nearly No Tags/Test Album 1/01 Track One.mp3",
        "Unknown Artist/Unknown Album/01 Unknown Title.mp3",
    ]
    playlist_file = tmp_path / "Genre Not Rock.m3u8"
    check_playlist_file(playlist_file, expected_tracks)
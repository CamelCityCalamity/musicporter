import pytest
import os
import shutil
import yaml
import pathlib
from musicporter.main import main
from musicporter.path_utils import escape_m3u8_path

def test_main_path_map_empty_search():
    # Simulate CLI args with malformed --path-map (empty search)
    argv = [
        'output',
        '-m', '/music',
        '-y', 'config.yaml',
        '-r', '::replacement',  # Malformed: empty search
    ]
    with pytest.raises(SystemExit) as excinfo:
        main(argv)
    assert excinfo.value.code != 0


def test_main_path_map_missing_colons():
    # Simulate CLI args with malformed --path-map (no '::' separator)
    argv = [
        'output',
        '-m', '/music',
        '-y', 'config.yaml',
        '-r', 'badmapping',  # Malformed: no '::'
    ]
    with pytest.raises(SystemExit) as excinfo:
        main(argv)
    assert excinfo.value.code != 0


def _make_static_playlist(playlist_path, mp3_paths):
    """Write a static playlist (m3u8) referencing the given mp3_paths."""
    with open(playlist_path, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for p in mp3_paths:
            f.write(str(p) + '\n')

def _parse_mock_mp3_metadata(yaml_path, testdata_dir):
    """Parse the mock_mp3_metadata.yaml and return info about testdata mp3 files (do not create any files). Missing fields are set to None."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    mp3s = []
    for artist in data:
        artist_name = artist.get('artist')
        artist_fs = artist_name if artist_name and str(artist_name).strip() != '' else 'Unknown Artist'
        for album in artist.get('albums', []) if artist.get('albums') is not None else []:
            album_name = album.get('album')
            album_fs = album_name if album_name and str(album_name).strip() != '' else 'Unknown Album'
            tracks = album.get('tracks', []) if album.get('tracks') is not None else []
            for idx, track in enumerate(tracks, 1):
                title = track.get('title')
                title_fs = title if title and str(title).strip() != '' else 'Unknown Title'
                filename = f"{idx:02d} {title_fs}.mp3"
                rel_path = pathlib.Path(artist_fs) / album_fs / filename
                mp3_path = testdata_dir / rel_path
                track['filename'] = filename
                track['path'] = mp3_path
                track['rel_path'] = rel_path
                mp3s.append(track)
    return mp3s

def _assert_playlist_matches(playlist_path, expected_lines, criteria=None):
    """Check playlist file for #EXTM3U, optional criteria comment, and expected lines (order matters)."""
    assert playlist_path.exists()
    with open(playlist_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    assert lines[0] == '#EXTM3U'
    idx = 1
    if criteria is not None:
        assert lines[1] == f'#Criteria: {criteria}'
        idx += 1
    assert lines[idx:] == expected_lines


def test_main_fully_featured_run(tmp_path):
    """
    Integration test: run musicporter end-to-end with two music folders, two static playlists, and three smart playlists.
    """
    # 1. Create two deep directories for input music
    music_dir = tmp_path / 'data' / 'Music'
    soundtracks_dir = tmp_path / 'stuff' / 'Soundtracks'
    music_dir.mkdir(parents=True)
    soundtracks_dir.mkdir(parents=True)

    # 2. Parse mock_mp3_metadata.yaml and get info about testdata mp3s
    test_dir = pathlib.Path(__file__).parent
    mock_yaml = test_dir / 'mock_mp3_metadata.yaml'
    testdata_dir = test_dir / 'testdata'
    mp3s = _parse_mock_mp3_metadata(mock_yaml, testdata_dir)

    # 2b. Copy mp3s from testdata to music_dir or soundtracks_dir based on genre
    for mp3 in mp3s:
        genre = mp3.get('genre', '').lower()
        if genre in {'rock', 'pop', 'instrumental', 'folk', 'jazz'}:
            dest_root = music_dir
        elif genre in {'video game', 'soundtrack'}:
            dest_root = soundtracks_dir
        else:
            continue  # skip weird/empty genres
        dest_path = dest_root / mp3['rel_path'].parent
        dest_path.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mp3['path'], dest_path / mp3['filename'])

    # 3. Make two static playlists in a third temp folder
    static_playlists_dir = tmp_path / 'static_playlists'
    static_playlists_dir.mkdir()

    # First playlist: two from Music
    static_music_mp3s = [
        {
            'rel_path': pathlib.Path('Thunder Lizards/Stone Age Groove/01 Rock the Bones.mp3'),
            'filename': '01 Rock the Bones.mp3',
        },
        {
            'rel_path': pathlib.Path('Thunder Lizards/Stone Age Groove/02 Fossil Fuel.mp3'),
            'filename': '02 Fossil Fuel.mp3',
        },
    ]
    static_music_path = static_playlists_dir / '@music_only.m3u8'
    _make_static_playlist(
        static_music_path,
        [music_dir / m['rel_path'] for m in static_music_mp3s]
    )

    # Second playlist: two from Soundtracks
    static_soundtracks_mp3s = [
        {
            'rel_path': pathlib.Path('Various Artists/Pixel Quest/01 Main Theme.mp3'),
            'filename': '01 Main Theme.mp3',
        },
        {
            'rel_path': pathlib.Path('Various Artists/Pixel Quest/02 Level Up.mp3'),
            'filename': '02 Level Up.mp3',
        },
    ]
    static_soundtracks_path = static_playlists_dir / '@soundtracks_only.m3u8'
    _make_static_playlist(
        static_soundtracks_path,
        [soundtracks_dir / m['rel_path'] for m in static_soundtracks_mp3s]
    )

    # 4. Make a yaml config file for three smart playlists
    smart_yaml = tmp_path / 'smart_playlists.yaml'
    smart_playlists = {
        'playlists': [
            {'name': 'Rock Fives', 'criteria': "rating = 5 and genre = 'Rock'"},
            {'name': 'VG Fives', 'criteria': "rating = 5 and genre = 'Video Game'"},
            {'name': 'Modern Fives', 'criteria': "rating = 5 and year >= 2000"},
        ]
    }
    with open(smart_yaml, 'w', encoding='utf-8') as f:
        yaml.dump(smart_playlists, f)

    # 5. Prepare output folder and path mapping
    output_dir = tmp_path / 'output'
    output_dir.mkdir()
    # search/replace: remove the full prefix of each music folder
    android_storage_prefix = '/storage/emulated/0/'
    music_map = f"{music_dir}{os.sep}::{android_storage_prefix}Music{os.sep}"
    soundtracks_map = f"{soundtracks_dir}{os.sep}::{android_storage_prefix}Soundtracks{os.sep}"

    # 6. Run main with all arguments
    argv = [
        str(output_dir),
        '-m', str(music_dir),
        '-m', str(soundtracks_dir),
        '-y', str(smart_yaml),
        '-p', str(static_playlists_dir),
        '-r', music_map,
        '-r', soundtracks_map,
        '-t', str(tmp_path / 'Playlists'),
        '--verbose',
    ]
    main(argv)

    # 1. All mock MP3s that should have been collected are in output
    output_music = list((output_dir / 'Music').rglob('*.mp3'))
    output_soundtracks = list((output_dir / 'Soundtracks').rglob('*.mp3'))

    # Hard-coded expected files from static playlists (from static1_mp3s and static2_mp3s)
    static_expected = set()
    static_expected.update(str(pathlib.Path('Music') / m['rel_path']) for m in static_music_mp3s)
    static_expected.update(str(pathlib.Path('Soundtracks') / m['rel_path']) for m in static_soundtracks_mp3s)

    rock_fives_expected = list(sorted([
        'Music/Thunder Lizards/Stone Age Groove/01 Rock the Bones.mp3',
        'Music/Thunder Lizards/Fossilized Funk/02 Dino Disco.mp3'
    ]))

    vg_fives_expected = list(sorted([
        'Soundtracks/8Bit Heroes/Retro Adventure/02 Boss Battle.mp3'
    ]))

    modern_fives_expected = list(sorted([
        'Music/Thunder Lizards/Stone Age Groove/01 Rock the Bones.mp3',
        'Music/Thunder Lizards/Fossilized Funk/02 Dino Disco.mp3',
        'Music/Arpeggio/Strings & Things/03 Harmonic Drift.mp3',
        'Music/Neon Skyline/City Lights/03 Electric Heart.mp3',
        'Music/Blue Note Quartet/Midnight Sessions/03 Nightcap.mp3',
        'Soundtracks/8Bit Heroes/Retro Adventure/02 Boss Battle.mp3',
        'Soundtracks/Various Artists/Pixel Quest/01 Main Theme.mp3'
    ]))

    smart_expected = set(rock_fives_expected) | set(vg_fives_expected) | set(modern_fives_expected)

    # Union of all expected files
    expected_files = static_expected | smart_expected
    actual_files = set(str(f.relative_to(output_dir)) for f in output_music + output_soundtracks)
    assert actual_files == expected_files

    # 3. Rewritten playlists must exist and have correct files/paths (full, ordered, absolute)
    playlists_out = output_dir / 'Playlists'
    assert playlists_out.exists()

    # Static playlists: check full, ordered, absolute paths, skipping #EXTM3U
    static_music_expected = [
        f"{android_storage_prefix}Music{os.sep}{m['rel_path']}" for m in static_music_mp3s
    ]
    static_soundtracks_expected = [
        f"{android_storage_prefix}Soundtracks{os.sep}{m['rel_path']}" for m in static_soundtracks_mp3s
    ]

    # Check @music_only.m3u8
    music_playlist_path = playlists_out / '@music_only.m3u8'
    _assert_playlist_matches(music_playlist_path, static_music_expected)

    # Check @soundtracks_only.m3u8
    soundtracks_playlist_path = playlists_out / '@soundtracks_only.m3u8'
    _assert_playlist_matches(soundtracks_playlist_path, static_soundtracks_expected)

    # Smart playlists: check for #EXTM3U, criteria comment, and full, ordered, absolute paths
    smart_playlists = [
        ('Rock Fives', rock_fives_expected, "rating = 5 and genre = 'Rock'"),
        ('VG Fives', vg_fives_expected, "rating = 5 and genre = 'Video Game'"),
        ('Modern Fives', modern_fives_expected, "rating = 5 and year >= 2000"),
    ]

    for name, expected_relative_paths, criteria in smart_playlists:
        pl_path = playlists_out / (name + '.m3u8')
        expected_full_paths = [
            f"{android_storage_prefix}{escape_m3u8_path(relative_path)}" for relative_path in expected_relative_paths
        ]
        _assert_playlist_matches(pl_path, expected_full_paths, criteria)

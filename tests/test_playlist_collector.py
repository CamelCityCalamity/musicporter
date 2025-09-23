import os
import tempfile
import shutil
import pytest
from musicporter.mp3_collector import Mp3Collector

def create_empty_mp3(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(b'')

def test_collect_files_preserves_structure(tmp_path):
    # Setup music directory structure
    music_root = tmp_path / "Music"
    artist1_album1 = music_root / "Artist1" / "Album1"
    artist2_album2 = music_root / "Artist2" / "Album2"
    files = [
        artist1_album1 / "song1.mp3",
        artist1_album1 / "song2.mp3",
        artist2_album2 / "track1.mp3",
        artist2_album2 / "track2.mp3",
    ]
    for f in files:
        create_empty_mp3(f)

    # Setup playlists directory and playlists
    playlists_dir = tmp_path / "playlists"
    playlists_dir.mkdir()
    playlist1 = playlists_dir / "playlist1.m3u8"
    playlist2 = playlists_dir / "playlist2.m3u8"
    # playlist1 references 2 files, playlist2 references 1 file, 1 file is unreferenced
    playlist1.write_text(f"""#EXTM3U
{files[0]}
{files[2]}
""")
    playlist2.write_text(f"""#EXTM3U
{files[1]}
""")

    # Output directory
    output_dir = tmp_path / "Output"

    # Run collector
    collector = Mp3Collector()
    collector.collect_files(str(playlists_dir), str(output_dir), [str(music_root)])

    # Expected files (relative to music_root)
    expected = [
        os.path.relpath(str(files[0]), os.path.commonpath([str(files[0]), str(files[1]), str(files[2]), str(files[3])])),
        os.path.relpath(str(files[1]), os.path.commonpath([str(files[0]), str(files[1]), str(files[2]), str(files[3])])),
        os.path.relpath(str(files[2]), os.path.commonpath([str(files[0]), str(files[1]), str(files[2]), str(files[3])])),
    ]
    # Only files[3] is unreferenced
    for rel_path in expected:
        assert (output_dir / music_root / rel_path).exists(), f"Expected file missing: {rel_path}"
    # Unreferenced file should not be present
    unreferenced_rel = os.path.relpath(str(files[3]), os.path.commonpath([str(files[0]), str(files[1]), str(files[2]), str(files[3])]))
    assert not (output_dir / "Music" / unreferenced_rel).exists(), f"Unexpected file present: {unreferenced_rel}"

def test_delete_orphaned_files(tmp_path):
    # Setup music directory structure
    music_root = tmp_path / "Music"
    artist1_album1 = music_root / "Artist1" / "Album1"
    artist2_album2 = music_root / "Artist2" / "Album2"
    files = [
        artist1_album1 / "song1.mp3",
        artist1_album1 / "song2.mp3",
        artist2_album2 / "track1.mp3",
        artist2_album2 / "track2.mp3",
    ]
    for f in files:
        create_empty_mp3(f)

    # Setup playlists directory and playlist referencing only some files
    playlists_dir = tmp_path / "playlists"
    playlists_dir.mkdir()
    playlist1 = playlists_dir / "playlist1.m3u8"
    playlist1.write_text(f"""#EXTM3U\n{files[0]}\n{files[2]}\n""")

    # Output directory
    output_dir = tmp_path / "Output"
    output_dir.mkdir()

    # Copy all files to output_dir to simulate previously collected files
    for f in files:
        rel_path = os.path.relpath(str(f), os.path.commonpath([str(f) for f in files]))
        dest_path = output_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest_path)

    # Run collect_files with delete_orphans=True
    collector = Mp3Collector()
    collector.collect_files(str(playlists_dir), str(output_dir), [str(music_root)], delete_orphans=True)

    # Only files[0] and files[2] should remain
    rel_paths = [os.path.relpath(str(f), os.path.commonpath([str(f) for f in files])) for f in files]
    expected = [rel_paths[0], rel_paths[2]]
    deleted = [rel_paths[1], rel_paths[3]]
    for rel_path in expected:
        assert (output_dir / "Music" / rel_path).exists(), f"Expected file missing after orphan deletion: {rel_path}"
    for rel_path in deleted:
        assert not (output_dir / "Music" / rel_path).exists(), f"Orphaned file not deleted: {rel_path}"

def test_delete_empty_folders(tmp_path):
    # Setup music directory structure
    music_root = tmp_path / "Music"
    artist1_album1 = music_root / "Artist1" / "Album1"
    artist2_album2 = music_root / "Artist2" / "Album2"
    files = [
        artist1_album1 / "song1.mp3",
        artist1_album1 / "song2.mp3",
        artist2_album2 / "track1.mp3",
        artist2_album2 / "track2.mp3",
    ]
    for f in files:
        create_empty_mp3(f)

    # Setup playlists directory and a blank playlist
    playlists_dir = tmp_path / "playlists"
    playlists_dir.mkdir()
    playlist1 = playlists_dir / "playlist1.m3u8"
    playlist1.write_text(f"#EXTM3U\n{files[0]}\n{files[1]}")

    # Output directory
    output_dir = tmp_path / "Output"
    output_dir.mkdir()

    # Copy all files to output_dir to simulate previously collected files
    for f in files:
        rel_path = os.path.relpath(str(f), os.path.commonpath([str(f) for f in files]))
        dest_path = output_dir / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest_path)

    # Run collect_files with delete_orphans=True
    collector = Mp3Collector()
    collector.collect_files(str(playlists_dir), str(output_dir), [str(music_root)], delete_orphans=True)

    # Only Artist2 and its subfolders should be deleted from output_dir
    artist2_dir = output_dir / "Music" / "Artist2"
    assert not artist2_dir.exists(), f"Expected {artist2_dir} to be deleted, but it exists."

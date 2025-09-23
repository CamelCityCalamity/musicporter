import os
import pytest
from musicporter.playlist_rewriter import PlaylistRewriter

def test_rewrite_playlists(tmp_path):
    # Setup: create a source directory with m3u8 files
    src_dir = tmp_path / "playlists"
    src_dir.mkdir()
    m3u_file = src_dir / "test.m3u8"
    # Use two lines to rewrite, one to leave alone
    m3u_file.write_text("""#EXTM3U
/source/music/Artist/Album/song1.mp3
/source/music/Artist/Album/song2.mp3
#EXTINF:123,Some Info
""")

    # Output directory
    out_dir = tmp_path / "rewritten"
    search = "/source/music"
    replace = "/target/music"

    # Run translator
    translator = PlaylistRewriter()
    translator.rewrite_playlists(str(src_dir), str(out_dir), search, replace)

    # Check output file exists
    out_file = out_dir / "test.m3u8"
    assert out_file.exists(), "Rewritten m3u8 file not created"

    # Check contents
    lines = out_file.read_text().splitlines()
    assert lines[0] == "#EXTM3U"
    assert lines[1] == "/target/music/Artist/Album/song1.mp3"
    assert lines[2] == "/target/music/Artist/Album/song2.mp3"
    assert lines[3] == "#EXTINF:123,Some Info"

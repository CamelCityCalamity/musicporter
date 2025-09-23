import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from musicporter.db import TrackDB
from musicporter.track import Track

def test_insert_and_query_single_track(tmp_path):
    db_path = tmp_path / "test_tracks.sqlite"
    db = TrackDB(str(db_path))
    track = Track(
        path="/music/rock/01.mp3",
        artist="Test Artist",
        album="Test Album",
        genre="Rock",
        rating=5,
        title="Test Song",
        year=2022
    )
    db.insert_track(track)
    results = db.query_tracks()
    assert len(results) == 1
    row = results[0]
    assert row.path == track.path
    assert row.artist == track.artist
    assert row.album == track.album
    assert row.genre == track.genre
    assert row.rating == track.rating
    assert row.title == track.title
    assert row.year == track.year

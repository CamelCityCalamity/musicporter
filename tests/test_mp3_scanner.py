import os
import pytest
from musicporter.mp3_scanner import Mp3Scanner
from musicporter.track import Track

class TestMp3Scanner:
    def test_scan_thunder_lizards_stone_age_groove(self):
        album_path = os.path.join(
            os.path.dirname(__file__),
            'testdata', 'Thunder Lizards', 'Stone Age Groove'
        )
        scanner = Mp3Scanner()
        tracks = scanner.scan([album_path])
        # We expect 3 tracks in Stone Age Groove
        assert len(tracks) == 3
        titles = {t.title for t in tracks}
        assert 'Rock the Bones' in titles
        assert 'Fossil Fuel' in titles
        assert 'Lava Lamp' in titles
        # Check one track's details
        track = next(t for t in tracks if t.title == 'Rock the Bones')
        assert track.artist == 'Thunder Lizards'
        assert track.album == 'Stone Age Groove'
        assert track.genre == 'Rock'
        assert track.rating == 5
        assert track.year == 2021

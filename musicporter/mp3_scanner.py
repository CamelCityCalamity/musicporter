import os
import eyed3
import logging
from .track import Track

class Mp3Scanner:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        # Set eyed3 log level to match our logger
        # eyed3_level = self.logger.getEffectiveLevel()
        eyed3.log.setLevel("ERROR")

    def scan(self, music_paths: list[str]) -> list[Track]:
        """
        Recursively scan root_path for MP3 files and return a list of Track objects.
        """
        tracks = []
        for music_path in music_paths:
            tracks.extend(self._scan_path(music_path))
        return tracks
    
    def _scan_path(self, root_path: str) -> list[Track]:
        tracks = []
        for dirpath, _, filenames in os.walk(root_path):
            for filename in filenames:
                if filename.lower().endswith('.mp3'):
                    full_path = os.path.join(dirpath, filename)
                    track = self._extract_track(full_path)
                    if track:
                        tracks.append(track)
        return tracks

    def _extract_track(self, file_path: str) -> Track:
        try:
            audiofile = eyed3.load(file_path)
            if audiofile is None or audiofile.tag is None:
                self.logger.warning(f"No tag found for file: {file_path}")
                return Track(path=file_path)
            tag = audiofile.tag
            best_date = tag.getBestDate(prefer_recording_date=True) # type: ignore
            comment = None
            if tag.comments and len(tag.comments) > 0: # type: ignore
                comment = tag.comments[0].text # type: ignore
            return Track(
                path=file_path,
                artist=tag.artist,
                album=tag.album,
                genre=tag.genre.name if tag.genre else None, # type: ignore
                rating=self._extract_rating(audiofile),
                title=tag.title,
                year=best_date.year if best_date else None,
                comment=comment
            )
        except Exception as e:
            self.logger.error(f"Error extracting track from {file_path}: {e}")
            return Track(path=file_path)

    def _extract_rating(self, audiofile):
        try:
            pops = audiofile.tag.popularities
            if not pops:
                return None
            rating_val = pops[0].rating
            # Map to star rating to POPM values. This rounds down Media Monkey style half-star ratings.
            if rating_val == 0:
                return None
            elif rating_val >= 255:
                return 5
            elif rating_val >= 196:
                return 4
            elif rating_val >= 128:
                return 3
            elif rating_val >= 64:
                return 2
            elif rating_val >= 1:
                return 1
            else:
                return None
        except Exception:
            return None

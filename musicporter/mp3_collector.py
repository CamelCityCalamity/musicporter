import os
import shutil
import logging
from musicporter.path_utils import unescape_m3u8_path

class Mp3Collector:
    """
    Collects all music files referenced by m3u8 playlists in a directory and copies them to a target directory.
    Uses Python logging for warnings and info. Logger can be injected or defaults to module logger.
    """
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def collect_files(self, m3u_dir: str, music_target: str, music_source_paths, delete_orphans: bool = False):
        """
        Args:
            m3u_dir (str): Directory containing m3u8 files.
            music_target (str): Directory to copy all referenced music files to, preserving relative structure.
            music_source_paths (list[str]): List of music source directories to strip as prefixes from referenced files. Must not be empty.
            delete_orphans (bool): If True, delete files in music_target not referenced by any m3u8 file.
        Raises:
            ValueError: If music_source_paths is empty.
        """
        if not music_source_paths or len(music_source_paths) == 0:
            raise ValueError("music_source_paths must not be empty. Cannot collect files without knowing music source prefixes.")
        # Normalize and sort by length descending to match longest prefix first
        music_source_paths = [os.path.abspath(p) for p in music_source_paths]
        music_source_paths.sort(key=lambda p: -len(p))

        m3u_files = [f for f in os.listdir(m3u_dir) if f.lower().endswith('.m3u8')]
        referenced_files = set()
        dest_paths = set()
        for m3u_file in m3u_files:
            m3u_path = os.path.join(m3u_dir, m3u_file)
            with open(m3u_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # playlists may contain percent-encoded sequences for
                        # problematic characters; unescape them so the file
                        # collector can find the referenced files on disk.
                        referenced_files.add(unescape_m3u8_path(line))

        if not referenced_files:
            self.logger.warning("No referenced files found in playlists.")
            return

        for src_path in referenced_files:
            if os.path.isfile(src_path):
                abs_src = os.path.abspath(src_path)
                rel_path = None
                for prefix in music_source_paths:
                    if abs_src.startswith(prefix + os.sep):
                        # Preserve the basename of the prefix as the top-level folder
                        base = os.path.basename(prefix.rstrip(os.sep))
                        rel_under_prefix = os.path.relpath(abs_src, prefix)
                        rel_path = os.path.join(base, rel_under_prefix)
                        break
                if rel_path is None:
                    self.logger.warning(f"Referenced file {src_path} does not match any music source path. Skipping.")
                    continue
                dest_path = os.path.join(music_target, rel_path)
                dest_paths.add(os.path.abspath(dest_path))
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                if not os.path.exists(dest_path):
                    shutil.copy2(abs_src, dest_path)
            else:
                self.logger.warning(f"Referenced file not found: {src_path}")

        if delete_orphans:
            # Walk through music_target and delete orphaned MP3 files only
            for root, _, files in os.walk(music_target):
                for file in files:
                    if not file.lower().endswith('.mp3'):
                        continue
                    file_path = os.path.abspath(os.path.join(root, file))
                    if file_path not in dest_paths:
                        os.remove(file_path)

            # Now walk the tree bottom-up and remove empty directories
            for root, dirs, files in os.walk(music_target, topdown=False):
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    # Remove dir if empty
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)


import os
import logging

class PlaylistRewriter:
    """
    Copies m3u8 playlist files from a source directory to a target directory, translating path prefixes inside each playlist.
    """
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def rewrite_playlists(self, input_path: str, output_path: str, search: str, replace: str):
        """
        Args:
            input_path (str): Directory containing m3u8 files to rewrite.
            output_path (str): Directory to copy rewritten m3u8 files to.
            search (str): Path prefix to search for in m3u8 files.
            replace (str): Replacement path prefix for m3u8 files.
        """
        os.makedirs(output_path, exist_ok=True)
        m3u_files = [f for f in os.listdir(input_path) if f.lower().endswith('.m3u8')]
        self.logger.info(f"Found {len(m3u_files)} playlists to rewrite in {input_path}")
        for m3u_file in m3u_files:
            src_path = os.path.join(input_path, m3u_file)
            dest_path = os.path.join(output_path, m3u_file)
            self.logger.info(f"Rewriting {src_path} -> {dest_path} (search: '{search}', replace: '{replace}')")
            with open(src_path, 'r', encoding='utf-8') as fin, open(dest_path, 'w', encoding='utf-8') as fout:
                for line in fin:
                    if line.strip() and not line.startswith('#'):
                        new_line = line.replace(search, replace)
                        fout.write(new_line)
                    else:
                        fout.write(line)


import os
import logging
from typing import Optional, List
from musicporter.path_utils import escape_m3u8_path

class PlaylistRewriter:
    """
    Copies m3u8 playlist files from a source directory to a target directory, translating path prefixes inside each playlist and escaping problematic characters.
    """
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def rewrite_playlists(self, input_path: str, output_path: str, rewrite_pairs: Optional[List[List[str]]] = None):
        """
        Args:
            input_path (str): Directory containing m3u8 files to rewrite.
            output_path (str): Directory to copy rewritten m3u8 files to.
            rewrite_pairs (Optional[List[List[str]]]): Optional list of [search, replace] pairs to apply in order.
                If omitted or None, no search/replace is performed, but paths are still escaped.
        """
        if rewrite_pairs is None:
            rewrite_pairs = []
        os.makedirs(output_path, exist_ok=True)
        m3u_files = [f for f in os.listdir(input_path) if f.lower().endswith('.m3u8')]
        self.logger.info(f"Found {len(m3u_files)} playlists to rewrite in {input_path}")
        for m3u_file in m3u_files:
            src_path = os.path.join(input_path, m3u_file)
            dest_path = os.path.join(output_path, m3u_file)
            self.logger.info(f"Rewriting {src_path} -> {dest_path} (pairs: {rewrite_pairs})")
            with open(src_path, 'r', encoding='utf-8') as fin, open(dest_path, 'w', encoding='utf-8') as fout:
                for line in fin:
                    if line.strip() and not line.startswith('#'):
                        new_line = line
                        for search, replace in rewrite_pairs:
                            new_line = new_line.replace(search, replace)
                        new_line = escape_m3u8_path(new_line)
                        fout.write(new_line)
                    else:
                        fout.write(line)

import yaml
import os
import logging
from musicporter.criteria_parser import CriteriaParser
from musicporter.ast_to_sql import ASTtoSQL
from musicporter.db import TrackDB
from musicporter.path_utils import escape_m3u8_path
from typing import TypedDict

class PlaylistDef(TypedDict):
    name: str
    criteria: str

class PlaylistGenerator:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def generate_from_config(self, config_path: str, db_path: str, output_path: str):
        """
        Loads YAML config from file and calls generate with the loaded data.

        Args:
            config_path (str): Path to the YAML config file.
            db_path (str): Path to the SQLite database.
            output_path (str): Directory to write m3u8 files.

        Example YAML structure:
            playlists:
              - name: Rock Favorites
                criteria: genre = 'Rock' and rating >= 4
              - name: Paul Simon Greatest Hits
                criteria: artist = 'Paul Simon' and rating >= 3
        """
        self.logger.info(f"Loading playlist config from {config_path}")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        self.logger.info(f"Loaded {len(config.get('playlists', []))} playlists from config")
        self.generate(
            db_path,
            output_path,
            config['playlists'],
        )
    
    def generate(self, db_path: str, output_path: str, playlists: list[PlaylistDef]):
        """
        Generate m3u8 playlists from a list of playlist definitions.

        Args:
            db_path (str): Path to the SQLite database.
            output_path (str): Directory to write m3u8 files.
            playlists (list): List of dicts, each with keys:
                - "name": The playlist name (used for the output filename)
                - "criteria": The filter criteria string for selecting tracks

        For each playlist, this method parses the criteria, queries the database,
        and writes an m3u8 file with the matching tracks.
        """
        os.makedirs(output_path, exist_ok=True)
        db = TrackDB(db_path)
        parser = CriteriaParser()
        ast_to_sql = ASTtoSQL()
        for playlist in playlists:
            name = playlist['name']
            criteria = playlist['criteria']
            self.logger.info(f"Generating playlist '{name}' with criteria: {criteria}")
            ast = parser.parse(criteria)
            where_clause, params = ast_to_sql.to_sql(ast)
            tracks = db.query_tracks(where_clause, tuple(params))
            tracks = sorted(tracks, key=lambda t: t.path)
            m3u8_path = os.path.join(output_path, f"{name}.m3u8")
            self.logger.info(f"Writing {len(tracks)} tracks to {m3u8_path}")
            with open(m3u8_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                f.write(f"#Criteria: {criteria}\n")
                for track in tracks:
                    f.write(f"{escape_m3u8_path(track.path)}\n")
        db.close()

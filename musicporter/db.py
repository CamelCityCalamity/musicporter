import sqlite3
from typing import Optional
from musicporter.track import Track

class TrackDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.ensure_schema()

    def __repr__(self) -> str:
        return f"<TrackDB path={self.db_path}>"

    def ensure_schema(self):
        cur = self.conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                path TEXT PRIMARY KEY COLLATE NOCASE,
                artist TEXT COLLATE NOCASE,
                album TEXT COLLATE NOCASE,
                genre TEXT COLLATE NOCASE,
                rating INTEGER,
                title TEXT COLLATE NOCASE,
                year INTEGER,
                comment TEXT COLLATE NOCASE
            )
        ''')
        self.conn.commit()

    def close(self):
        self.conn.close()

    def insert_track(self, track: 'Track'):
        """
        Insert a track into the database. Expects a Track instance.
        """
        columns = [
            "path", "artist", "album", "genre", "rating", "title", "year", "comment"
        ]
        values = [getattr(track, col) for col in columns]
        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT INTO tracks ({', '.join(columns)}) VALUES ({placeholders})"
        self.conn.execute(sql, values)
        self.conn.commit()

    def insert_tracks(self, tracks: list['Track']):
        """
        Bulk insert multiple tracks. Each item is a Track instance.
        """
        columns = [
            "path", "artist", "album", "genre", "rating", "title", "year", "comment"
        ]
        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT INTO tracks ({', '.join(columns)}) VALUES ({placeholders})"
        values_list = [tuple(getattr(track, col) for col in columns) for track in tracks]
        self.conn.executemany(sql, values_list)
        self.conn.commit()
        
    def query_tracks(self, where_clause: Optional[str] = None, params: tuple = ()) -> list[Track]:
        """
        Query tracks with an optional WHERE clause. Returns a list of Track instances.
        """
        sql = "SELECT path, artist, album, genre, rating, title, year, comment FROM tracks"
        if where_clause:
            sql += f" WHERE {where_clause}"
        cur = self.conn.execute(sql, params)
        columns = [desc[0] for desc in cur.description]
        return [Track.from_dict(dict(zip(columns, row))) for row in cur.fetchall()]

    def get_all_tracks(self):
        """
        Return all tracks in the database as a list of dicts.
        """
        return self.query_tracks()

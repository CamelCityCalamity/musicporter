class Track:
    def __init__(self, path, artist=None, album=None, genre=None, rating=None, title=None, year=None, comment=None):
        self.path = path
        self.artist = artist
        self.album = album
        self.genre = genre
        self.rating = rating
        self.title = title
        self.year = year
        self.comment = comment

    def as_dict(self):
        return {
            "path": self.path,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre,
            "rating": self.rating,
            "title": self.title,
            "year": self.year,
            "comment": self.comment
        }
    
    def __repr__(self):
        return f"<Track path={repr(self.path)}>"
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            path=data["path"],
            artist=data.get("artist"),
            album=data.get("album"),
            genre=data.get("genre"),
            rating=data.get("rating"),
            title=data.get("title"),
            year=data.get("year"),
            comment=data.get("comment"),
        )
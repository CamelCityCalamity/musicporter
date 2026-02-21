"""Utility helpers for playlist path handling."""

def escape_m3u8_path(path: str) -> str:
    """Escape characters that are problematic for certain players like VLC: %#?
    """
    if path is None:
        return path
    
    return (path.replace('%', '%25')
                .replace('#', '%23')
                .replace('?', '%3F'))

def unescape_m3u8_path(path: str) -> str:
    """Reverse the escaping performed by `escape_m3u8_path`.
    """
    if path is None:
        return path
    return (path.replace('%23', '#')
                .replace('%3F', '?')
                .replace('%25', '%'))

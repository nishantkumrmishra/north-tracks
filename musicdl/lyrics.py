import urllib.parse
import requests
from musicdl.logger import log_info, log_error

HEADERS = {
    "User-Agent": "MusicDL/1.0 (Windows NT 10.0; Win64; x64)"
}

def fetch_lyrics(title: str, artist: str = "", duration: int = 0) -> str:
    """Fetches plain or synced lyrics from LRCLIB open-source database"""
    if not title:
        return ""

    params = {
        "track_name": title,
        "artist_name": artist
    }
    if duration > 0:
        params["duration"] = str(duration)

    query_str = urllib.parse.urlencode(params)
    url = f"https://lrclib.net/api/get?{query_str}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            synced = data.get("syncedLyrics")
            plain = data.get("plainLyrics")
            lyrics = synced or plain or ""
            if lyrics:
                log_info(f"Lyrics fetched for: {artist} - {title}")
                return lyrics
    except Exception as e:
        log_error(f"Lyrics lookup error for {title}", e)

    return ""

import re
import json
import urllib.parse
import time
import requests
from musicdl.logger import log_info, log_error, log_warning

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

SPOTIFY_URL_REGEX = re.compile(
    r"(?:open\.spotify\.com\/(?:intl-[a-z]+\/)?(track|playlist|album)\/|spotify:(track|playlist|album):)([a-zA-Z0-9]+)"
)

def is_spotify_url(url: str) -> bool:
    if not url:
        return False
    return bool(SPOTIFY_URL_REGEX.search(url.strip().strip("\"'").strip()))

def parse_spotify_url(url: str):
    if not url:
        return None
    cleaned = url.strip().strip("\"'").strip()
    match = SPOTIFY_URL_REGEX.search(cleaned)
    if not match:
        return None
    entity_type = match.group(1) or match.group(2)
    entity_id = match.group(3)
    return entity_type, entity_id

def find_key_recursive(d, target_key):
    if isinstance(d, dict):
        if target_key in d and d[target_key]:
            return d[target_key]
        for v in d.values():
            res = find_key_recursive(v, target_key)
            if res is not None:
                return res
    elif isinstance(d, list):
        for item in d:
            res = find_key_recursive(item, target_key)
            if res is not None:
                return res
    return None

def extract_spotify_entity(url: str) -> dict:
    parsed = parse_spotify_url(url)
    if not parsed:
        log_warning(f"Could not parse Spotify URL: {url}")
        return None

    entity_type, entity_id = parsed
    embed_url = f"https://open.spotify.com/embed/{entity_type}/{entity_id}"
    log_info(f"Resolving Spotify {entity_type} ID: {entity_id}")

    session = requests.Session()
    session.headers.update(HEADERS)

    for attempt in range(1, 4):
        try:
            timeout_sec = 12 + (attempt * 4)
            resp = session.get(embed_url, timeout=timeout_sec)
            if resp.status_code == 200:
                match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    
                    if entity_type == "track":
                        state = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
                        title = state.get("name") or state.get("title") or find_key_recursive(data, "name") or "Unknown Title"
                        artists_list = state.get("artists", [])
                        artist = ", ".join([a.get("name", "") for a in artists_list if a.get("name")]) or state.get("subtitle") or "Unknown Artist"
                        cover = ""
                        cover_sources = state.get("coverArt", {}).get("sources", [])
                        if cover_sources:
                            cover = cover_sources[0].get("url", "")
                        dur_ms = state.get("duration") or 0
                        duration = round(dur_ms / 1000) if dur_ms else 0
                        album = state.get("album", {}).get("name", "")

                        log_info(f"Resolved Spotify Track: {artist} - {title}")
                        return {
                            "type": "track",
                            "title": title,
                            "artist": artist,
                            "album": album,
                            "artwork_url": cover,
                            "duration": duration,
                            "tracks": [{
                                "title": title,
                                "artist": artist,
                                "album": album,
                                "artwork_url": cover,
                                "duration": duration
                            }]
                        }
                    else:
                        # Playlist or Album
                        state = data.get("props", {}).get("pageProps", {}).get("state", {}).get("data", {}).get("entity", {})
                        playlist_title = state.get("name") or state.get("title") or find_key_recursive(data, "title") or "Spotify Collection"
                        
                        raw_tracks = state.get("trackList") or find_key_recursive(data, "trackList") or []
                        tracks = []
                        for t in raw_tracks:
                            title = t.get("title") or t.get("name")
                            if not title:
                                continue
                            artist = t.get("subtitle") or ", ".join([a.get("name", "") for a in t.get("artists", [])]) or "Various Artists"
                            t_cover = ""
                            if t.get("album", {}).get("images"):
                                t_cover = t["album"]["images"][0].get("url", "")
                            
                            dur_ms = t.get("duration") or 0
                            duration = round(dur_ms / 1000) if dur_ms else 0

                            tracks.append({
                                "title": title,
                                "artist": artist,
                                "album": playlist_title,
                                "artwork_url": t_cover,
                                "duration": duration
                            })

                        if tracks:
                            log_info(f"Resolved Spotify {entity_type} '{playlist_title}' with {len(tracks)} tracks")
                            return {
                                "type": entity_type,
                                "title": playlist_title,
                                "artwork_url": "",
                                "tracks": tracks
                            }
            else:
                log_warning(f"Spotify embed attempt {attempt} returned HTTP {resp.status_code}")

        except Exception as e:
            log_warning(f"Spotify embed attempt {attempt} error: {e}")
            if attempt < 3:
                time.sleep(1)

    log_error(f"Failed to resolve Spotify entity for URL: {url}", None)
    return None

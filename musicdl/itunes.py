import urllib.parse
import requests

HEADERS = {
    "User-Agent": "MusicDL/1.0 (Windows NT 10.0; Win64; x64)"
}

def search_itunes(title: str, artist: str = "") -> dict:
    query = f"{artist} {title}".strip() if artist and artist != "Unknown" else title
    if not query:
        return None

    clean_term = urllib.parse.quote(query)
    url = f"https://itunes.apple.com/search?term={clean_term}&entity=song&limit=5"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=6)
        if resp.status_code != 200:
            return None
        data = resp.json()
        results = data.get("results", [])
        if not results:
            # Fallback with title alone
            if artist:
                clean_title = urllib.parse.quote(title)
                fallback_url = f"https://itunes.apple.com/search?term={clean_title}&entity=song&limit=3"
                f_resp = requests.get(fallback_url, headers=HEADERS, timeout=6)
                if f_resp.status_code == 200:
                    results = f_resp.json().get("results", [])

        if not results:
            return None

        # Best match heuristic
        item = results[0]
        if artist and len(results) > 1:
            a_lower = artist.lower()
            for r in results:
                r_artist = (r.get("artistName") or "").lower()
                if a_lower in r_artist or r_artist in a_lower:
                    item = r
                    break

        artwork = item.get("artworkUrl100") or ""
        high_res_art = artwork.replace("100x100bb.jpg", "600x600bb.jpg").replace("100x100bb.png", "600x600bb.png")

        return {
            "title": item.get("trackName") or title,
            "artist": item.get("artistName") or artist,
            "album": item.get("collectionName") or "",
            "genre": item.get("primaryGenreName") or "",
            "release_date": (item.get("releaseDate") or "")[:4],
            "artwork_url": high_res_art
        }
    except Exception:
        return None

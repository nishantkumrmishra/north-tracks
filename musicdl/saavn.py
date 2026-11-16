import re
import json
import base64
import urllib.parse
import requests
from Crypto.Cipher import DES

DES_KEY = b"38346591"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def unpad_pkcs7(data: bytes) -> bytes:
    pad_len = data[-1]
    if 0 < pad_len <= 8:
        return data[:-pad_len]
    return data

def decrypt_media_url(encrypted_url: str) -> str:
    if not encrypted_url:
        return ""
    try:
        cipher = DES.new(DES_KEY, DES.MODE_ECB)
        raw_bytes = base64.b64decode(encrypted_url.strip())
        decrypted = unpad_pkcs7(cipher.decrypt(raw_bytes)).decode("utf-8")
        # Upgrade to 320kbps
        upgraded = re.sub(r"_(96|160)\.(mp4|m4a|mp3)", r"_320.\2", decrypted)
        return upgraded
    except Exception as e:
        return ""

def clean_html(text: str) -> str:
    if not text:
        return ""
    return (text.replace("&quot;", '"')
                .replace("&amp;", "&")
                .replace("&#039;", "'")
                .replace("&lt;", "<")
                .replace("&gt;", ">"))

def search_track(query: str) -> dict:
    if not query:
        return None

    clean_q = re.sub(r"[\(\)\[\]]", " ", query).strip()
    encoded = urllib.parse.quote(clean_q)
    search_url = f"https://www.jiosaavn.com/api.php?__call=autocomplete.get&_format=json&_marker=0&cc=in&includeMetaTags=1&query={encoded}"

    try:
        resp = requests.get(search_url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return None
        data = resp.json()
        songs = data.get("songs", {}).get("data", [])
        if not songs:
            return None

        first_song = songs[0]
        song_id = first_song.get("id")
        if not song_id:
            return None

        return get_song_details(song_id, fallback_title=first_song.get("title"))
    except Exception:
        return None

def get_song_details(song_id: str, fallback_title: str = "") -> dict:
    detail_url = f"https://www.jiosaavn.com/api.php?__call=song.getDetails&cc=in&_marker=0%3F_marker%3D0&_format=json&pids={song_id}"
    try:
        resp = requests.get(detail_url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return None
        data = resp.json()
        song = data.get(song_id, {})
        enc_url = song.get("encrypted_media_url")
        if not enc_url:
            return None

        stream_url = decrypt_media_url(enc_url)
        if not stream_url:
            return None

        title = clean_html(song.get("song") or fallback_title or "Unknown Title")
        artist = clean_html(song.get("singers") or song.get("primary_artists") or "Unknown Artist")
        album = clean_html(song.get("album") or "")
        year = song.get("year") or ""
        duration = int(song.get("duration", "0"))

        raw_img = song.get("image") or ""
        artwork_url = raw_img.replace("150x150", "500x500").replace("50x50", "500x500")

        return {
            "id": song_id,
            "title": title,
            "artist": artist,
            "album": album,
            "year": year,
            "duration": duration,
            "artwork_url": artwork_url,
            "stream_url": stream_url,
            "bitrate": "320kbps",
            "source": "JioSaavn 320k Studio"
        }
    except Exception:
        return None

def parse_saavn_playlist(url: str) -> list:
    """Extract tracks from Saavn song/album/playlist URLs"""
    try:
        # Check if URL contains song token or album token
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code != 200:
            return []
        # Find song IDs or data in HTML
        match = re.search(r'"pids":\["([^"]+)"\]', res.text)
        if match:
            song_id = match.group(1)
            details = get_song_details(song_id)
            return [details] if details else []
    except Exception:
        pass
    return []

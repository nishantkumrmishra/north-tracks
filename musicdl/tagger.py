from pathlib import Path
import requests
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TYER, APIC, USLT, ID3NoHeaderError
from musicdl.logger import log_error, log_info

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def fetch_artwork_bytes(artwork_url: str) -> bytes:
    if not artwork_url or not artwork_url.startswith("http"):
        return b""
    try:
        resp = requests.get(artwork_url, headers=HEADERS, timeout=8)
        if resp.status_code == 200 and len(resp.content) > 5000:
            return resp.content
    except Exception as e:
        log_error(f"Failed to fetch artwork from {artwork_url}", e)
    return b""

def tag_file(file_path: Path, metadata: dict, artwork_bytes: bytes = None):
    if not file_path.exists():
        return False

    if not artwork_bytes and metadata.get("artwork_url"):
        artwork_bytes = fetch_artwork_bytes(metadata["artwork_url"])

    ext = file_path.suffix.lower()
    if ext in [".m4a", ".mp4", ".aac"]:
        return tag_m4a(file_path, metadata, artwork_bytes)
    elif ext in [".mp3"]:
        return tag_mp3(file_path, metadata, artwork_bytes)

    return False

def tag_m4a(file_path: Path, metadata: dict, artwork_bytes: bytes) -> bool:
    try:
        audio = MP4(file_path)
        if metadata.get("title"):
            audio["\xa9nam"] = metadata["title"]
        if metadata.get("artist"):
            audio["\xa9ART"] = metadata["artist"]
        if metadata.get("album"):
            audio["\xa9alb"] = metadata["album"]
        if metadata.get("genre"):
            audio["\xa9gen"] = metadata["genre"]
        if metadata.get("year"):
            audio["\xa9day"] = str(metadata["year"])
        if metadata.get("lyrics"):
            audio["\xa9lyr"] = metadata["lyrics"]

        if artwork_bytes:
            fmt = MP4Cover.FORMAT_PNG if artwork_bytes.startswith(b"\x89PNG") else MP4Cover.FORMAT_JPEG
            audio["covr"] = [MP4Cover(artwork_bytes, imageformat=fmt)]

        audio.save()
        log_info(f"Tagged M4A file: {file_path.name}")
        return True
    except Exception as e:
        log_error(f"Failed to tag M4A {file_path.name}", e)
        return False

def tag_mp3(file_path: Path, metadata: dict, artwork_bytes: bytes) -> bool:
    try:
        try:
            tags = ID3(file_path)
        except ID3NoHeaderError:
            tags = ID3()

        if metadata.get("title"):
            tags.add(TIT2(encoding=3, text=metadata["title"]))
        if metadata.get("artist"):
            tags.add(TPE1(encoding=3, text=metadata["artist"]))
        if metadata.get("album"):
            tags.add(TALB(encoding=3, text=metadata["album"]))
        if metadata.get("genre"):
            tags.add(TCON(encoding=3, text=metadata["genre"]))
        if metadata.get("year"):
            tags.add(TYER(encoding=3, text=str(metadata["year"])))
        if metadata.get("lyrics"):
            tags.add(USLT(encoding=3, lang="eng", desc="Lyrics", text=metadata["lyrics"]))

        if artwork_bytes:
            mime = "image/png" if artwork_bytes.startswith(b"\x89PNG") else "image/jpeg"
            tags.add(APIC(
                encoding=3,
                mime=mime,
                type=3,
                desc="Cover",
                data=artwork_bytes
            ))

        tags.save(file_path, v2_version=3)
        log_info(f"Tagged MP3 file: {file_path.name}")
        return True
    except Exception as e:
        log_error(f"Failed to tag MP3 {file_path.name}", e)
        return False

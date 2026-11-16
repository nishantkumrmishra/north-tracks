from pathlib import Path
import os
import shutil
import requests
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, APIC, ID3NoHeaderError

from musicdl.normalizer import clean_search_query, clean_short_filename, normalize_genre
from musicdl.itunes import search_itunes
import musicdl.saavn as saavn
from musicdl.youtube import search_youtube_audio
from musicdl.tagger import tag_file
from musicdl.config import get_download_dir

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def is_valid_image(data: bytes) -> bool:
    if not data or len(data) < 5000:  # Minimum 5KB for real album art
        return False
    # Check JPEG or PNG magic header
    return data.startswith(b"\xff\xd8") or data.startswith(b"\x89PNG")

def fetch_verified_artwork(title: str, artist: str = ""):
    """
    Dual Artwork Verification Pipeline:
    1. iTunes API (600x600 / 1000x1000 official master art)
    2. JioSaavn CDN (500x500 studio cover)
    3. YouTube / Web Fallback
    Returns: (artwork_bytes, source_label, metadata_dict)
    """
    clean_t = clean_search_query(title)
    clean_a = clean_search_query(artist)
    enriched = {
        "title": title,
        "artist": artist,
        "album": "",
        "year": "",
        "genre": ""
    }

    # Step 1: iTunes API Verification
    try:
        it = search_itunes(clean_t, clean_a)
        if it and it.get("artwork_url"):
            resp = requests.get(it["artwork_url"], headers=HEADERS, timeout=8)
            if resp.status_code == 200 and is_valid_image(resp.content):
                enriched.update({
                    "title": it.get("title") or title,
                    "artist": it.get("artist") or artist,
                    "album": it.get("album") or "",
                    "year": it.get("release_date") or "",
                    "genre": it.get("genre") or ""
                })
                return resp.content, "Apple iTunes HD", enriched
    except Exception:
        pass

    # Step 2: JioSaavn CDN Verification
    try:
        search_q = f"{clean_a} {clean_t}".strip() if clean_a else clean_t
        s = saavn.search_track(search_q)
        if not s and clean_t != search_q:
            s = saavn.search_track(clean_t)

        if s and s.get("artwork_url"):
            resp = requests.get(s["artwork_url"], headers=HEADERS, timeout=8)
            if resp.status_code == 200 and is_valid_image(resp.content):
                enriched.update({
                    "title": s.get("title") or title,
                    "artist": s.get("artist") or artist,
                    "album": s.get("album") or enriched["album"],
                    "year": s.get("year") or enriched["year"],
                    "genre": s.get("genre") or enriched["genre"]
                })
                return resp.content, "JioSaavn CDN 500k", enriched
    except Exception:
        pass

    # Step 3: YouTube / Web High-Res Fallback
    try:
        yt = search_youtube_audio(f"{clean_a} {clean_t}".strip())
        if yt and yt.get("artwork_url"):
            resp = requests.get(yt["artwork_url"], headers=HEADERS, timeout=8)
            if resp.status_code == 200 and is_valid_image(resp.content):
                return resp.content, "YouTube HD Fallback", enriched
    except Exception:
        pass

    return b"", "None", enriched

def inspect_file(file_path: Path) -> dict:
    stem = file_path.stem
    parts = stem.split(" - ")
    artist = parts[0].strip() if len(parts) > 1 else ""
    title = " - ".join(parts[1:]).strip() if len(parts) > 1 else stem

    has_art = False
    art_size = 0
    tag_artist = ""
    tag_title = ""
    tag_genre = ""
    tag_album = ""

    ext = file_path.suffix.lower()
    if ext in [".m4a", ".mp4"]:
        try:
            mp4 = MP4(file_path)
            covr = mp4.get("covr", [])
            if covr and len(covr) > 0 and len(covr[0]) > 5000:
                has_art = True
                art_size = len(covr[0])
            tag_title = mp4.get("\xa9nam", [""])[0]
            tag_artist = mp4.get("\xa9ART", [""])[0]
            tag_album = mp4.get("\xa9alb", [""])[0]
            tag_genre = mp4.get("\xa9gen", [""])[0]
        except Exception:
            pass
    elif ext == ".mp3":
        try:
            id3 = ID3(file_path)
            apic = id3.getall("APIC")
            if apic and len(apic[0].data) > 5000:
                has_art = True
                art_size = len(apic[0].data)
            tag_title = str(id3.get("TIT2", ""))
            tag_artist = str(id3.get("TPE1", ""))
            tag_album = str(id3.get("TALB", ""))
            tag_genre = str(id3.get("TCON", ""))
        except Exception:
            pass

    resolved_title = tag_title or title
    resolved_artist = tag_artist or artist

    # Check issues
    is_name_long = len(file_path.stem.split()) > 4 or "," in file_path.stem or "&" in file_path.stem
    clean_target_name = clean_short_filename(resolved_artist, resolved_title, ext=file_path.suffix)
    needs_rename = clean_target_name != file_path.name

    return {
        "path": file_path,
        "filename": file_path.name,
        "title": resolved_title,
        "artist": resolved_artist,
        "album": tag_album,
        "genre": tag_genre,
        "has_art": has_art,
        "art_size": art_size,
        "needs_rename": needs_rename,
        "suggested_name": clean_target_name,
        "current_folder": file_path.parent.name
    }

def scan_music_files(directory: Path) -> list:
    valid_exts = {".m4a", ".mp3", ".flac", ".wav", ".aac", ".ogg", ".webm"}
    if not directory.exists() or not directory.is_dir():
        return []

    files = [p for p in directory.rglob("*.*") if p.is_file() and p.suffix.lower() in valid_exts]
    scanned = []
    for f in sorted(files):
        scanned.append(inspect_file(f))
    return scanned

def repair_single_file(info: dict, target_root_dir: Path) -> dict:
    f_path = info["path"]
    if not f_path.exists():
        return None

    # 1. Dual Artwork Verification
    art_bytes, source_label, enriched = fetch_verified_artwork(info["title"], info["artist"])

    # 2. Category Normalization
    raw_genre = enriched.get("genre") or info.get("genre", "")
    target_genre = normalize_genre(
        raw_genre=raw_genre,
        artist=enriched.get("artist") or info["artist"],
        title=enriched.get("title") or info["title"],
        context=info["current_folder"]
    )

    # 3. Clean Short Naming
    clean_name = clean_short_filename(
        enriched.get("artist") or info["artist"],
        enriched.get("title") or info["title"],
        ext=f_path.suffix
    )

    target_dir = target_root_dir / target_genre
    target_dir.mkdir(parents=True, exist_ok=True)
    destination_path = target_dir / clean_name

    # 4. Embed Verified Metadata & Artwork
    metadata = {
        "title": enriched.get("title") or info["title"],
        "artist": enriched.get("artist") or info["artist"],
        "album": enriched.get("album") or info.get("album", ""),
        "year": enriched.get("year", ""),
        "genre": target_genre
    }
    tag_file(f_path, metadata, art_bytes if art_bytes else None)

    # 5. Move to correct category folder
    if f_path.resolve() != destination_path.resolve():
        shutil.move(str(f_path), str(destination_path))

    return {
        "old_name": info["filename"],
        "new_name": clean_name,
        "old_folder": info["current_folder"],
        "new_category": target_genre,
        "art_source": source_label,
        "destination": destination_path
    }

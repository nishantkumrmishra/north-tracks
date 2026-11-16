from pathlib import Path
import os
import sys
import shutil
import time
import requests
from rich.console import Console

from musicdl.normalizer import (
    clean_filename, clean_short_filename, normalize_genre,
    clean_search_query, find_library_duplicate
)
from musicdl.saavn import search_track
from musicdl.youtube import search_youtube_audio
from musicdl.itunes import search_itunes
from musicdl.tagger import tag_file, fetch_artwork_bytes
from musicdl.lyrics import fetch_lyrics
from musicdl.config import get_download_dir, increment_download_count, load_config
from musicdl.logger import log_info, log_error, log_warning

console = Console()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}

def resolve_audio_stream(track_info: dict, context: str = "") -> dict:
    title = track_info.get("title", "")
    artist = track_info.get("artist", "")
    search_q = f"{clean_search_query(title)} {clean_search_query(artist)}".strip()

    # 1. Fetch iTunes metadata
    itunes_meta = search_itunes(clean_search_query(title), clean_search_query(artist))

    # 2. Try JioSaavn 320k Studio
    resolved = search_track(search_q)
    if not resolved and clean_search_query(title) != search_q:
        resolved = search_track(clean_search_query(title))

    # 3. Fallback: YouTube Innertube
    if not resolved or not resolved.get("stream_url"):
        yt_res = search_youtube_audio(search_q)
        if yt_res and yt_res.get("stream_url"):
            resolved = yt_res

    if not resolved:
        log_warning(f"Could not resolve audio stream for: {artist} - {title}")
        return None

    resolved["title"] = title or resolved.get("title", "Unknown Title")
    resolved["artist"] = artist or resolved.get("artist", "Unknown Artist")

    if itunes_meta and itunes_meta.get("artwork_url"):
        resolved["artwork_url"] = itunes_meta["artwork_url"]
        resolved["art_source_label"] = "Apple iTunes HD (600k)"
    elif resolved.get("artwork_url"):
        resolved["art_source_label"] = "JioSaavn CDN (500k)"
    elif track_info.get("artwork_url"):
        resolved["artwork_url"] = track_info["artwork_url"]
        resolved["art_source_label"] = "Web Thumbnail"
    else:
        resolved["art_source_label"] = "None"

    if itunes_meta:
        if itunes_meta.get("album") and not track_info.get("album"):
            resolved["album"] = itunes_meta["album"]
        if itunes_meta.get("release_date"):
            resolved["year"] = itunes_meta["release_date"]
        raw_genre = itunes_meta.get("genre", "")
    else:
        raw_genre = track_info.get("genre") or resolved.get("genre", "")

    resolved["genre"] = normalize_genre(
        raw_genre=raw_genre,
        artist=resolved["artist"],
        title=resolved["title"],
        context=context or track_info.get("album", "")
    )

    return resolved

def download_track(
    track_info: dict,
    dest_dir: Path = None,
    playlist_name: str = None,
    track_idx: str = "01/01",
    show_header: bool = False
) -> dict:
    if not dest_dir:
        dest_dir = get_download_dir()

    cfg = load_config()
    raw_title = track_info.get("title", "Unknown")
    raw_artist = track_info.get("artist", "")

    # Duplicate Check
    if cfg.get("skip_duplicates", True):
        existing = find_library_duplicate(raw_artist, raw_title, dest_dir)
        if existing:
            cat_name = existing.parent.name
            display_name = f"{clean_short_filename(raw_artist, raw_title).replace(existing.suffix, '')}"
            console.print(f"  [{track_idx}]  [dim]⏩  {display_name:<40} Already in {cat_name}[/dim]")
            log_info(f"Duplicate skipped: {raw_title} (Exists at: {existing})")
            return {
                "status": "skipped",
                "file": existing,
                "title": raw_title,
                "artist": raw_artist,
                "genre": cat_name
            }

    # Resolve Stream
    context = playlist_name or track_info.get("album", "")
    resolved = resolve_audio_stream(track_info, context=context)

    if not resolved or not resolved.get("stream_url"):
        display_name = f"{raw_artist} — {raw_title}" if raw_artist else raw_title
        console.print(f"  [{track_idx}]  [red]✕  {display_name:<40} Stream not found[/red]")
        return {
            "status": "failed",
            "title": raw_title,
            "artist": raw_artist,
            "track_info": track_info,
            "error": "Stream not found"
        }

    title = resolved.get("title") or raw_title
    artist = resolved.get("artist") or raw_artist
    genre = resolved.get("genre", "Pop")

    ext = ".webm" if resolved.get("is_webm") else ".m4a"
    file_name = clean_short_filename(artist, title, ext=ext)

    target_folder = dest_dir / genre
    target_folder.mkdir(parents=True, exist_ok=True)
    out_file = target_folder / file_name
    part_file = target_folder / f"{file_name}.part"

    # Display format: LeadArtist — Title
    display_name = file_name.replace(ext, "").replace(" - ", " — ")

    # Resume support
    req_headers = dict(HEADERS)
    existing_bytes = 0
    mode = "wb"

    if part_file.exists() and part_file.stat().st_size > 0:
        existing_bytes = part_file.stat().st_size
        req_headers["Range"] = f"bytes={existing_bytes}-"
        mode = "ab"
        log_info(f"Resuming download for {file_name} from byte {existing_bytes}")

    try:
        start_time = time.time()
        resp = requests.get(resolved["stream_url"], headers=req_headers, stream=True, timeout=15)
        
        if resp.status_code == 416 or (resp.status_code == 200 and mode == "ab"):
            mode = "wb"
            existing_bytes = 0
            resp = requests.get(resolved["stream_url"], headers=HEADERS, stream=True, timeout=15)

        resp.raise_for_status()
        content_len = int(resp.headers.get("content-length", 0))
        total_size = content_len + existing_bytes if resp.status_code == 206 else content_len
        downloaded = existing_bytes

        # In-place single-line progress updater (ZERO screen sliding/jitter)
        with open(part_file, mode) as f:
            last_update = time.time()
            for chunk in resp.iter_content(chunk_size=16384):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    if now - last_update > 0.08:
                        last_update = now
                        elapsed = now - start_time
                        speed_mb = (downloaded - existing_bytes) / (1024 * 1024) / max(elapsed, 0.001)
                        pct = int((downloaded / total_size) * 100) if total_size > 0 else 0
                        bar_blocks = "█" * (pct // 10) + "░" * (10 - (pct // 10))
                        line_str = f"\r  [{track_idx}]  ↓  {display_name[:36]:<36}  [{bar_blocks}] {pct:2d}% • {speed_mb:.1f} MB/s"
                        sys.stdout.write(line_str)
                        sys.stdout.flush()

        # Sanity check
        if not part_file.exists() or part_file.stat().st_size < 300000:
            if part_file.exists():
                part_file.unlink()
            raise ValueError("Downloaded file truncated or below 300KB")

        # Atomic Rename from .part
        if out_file.exists():
            out_file.unlink()
        shutil.move(str(part_file), str(out_file))

        # Lyrics (optional)
        if cfg.get("embed_lyrics", True):
            duration_sec = resolved.get("duration", 0)
            lyrics_text = fetch_lyrics(title, artist, duration=duration_sec)
            if lyrics_text:
                resolved["lyrics"] = lyrics_text

        # Embed Artwork & Metadata Tags
        art_bytes = fetch_artwork_bytes(resolved.get("artwork_url"))
        tag_file(out_file, resolved, art_bytes)
        increment_download_count()

        final_mb = out_file.stat().st_size / (1024 * 1024)
        
        # Clear the live line and print the permanent completed record
        sys.stdout.write("\r" + " " * 95 + "\r")
        sys.stdout.flush()
        console.print(f"  [{track_idx}]  [green]✓[/green]  {display_name[:36]:<36}  [bold white]320k[/] • [cyan]{genre}[/]  [dim]({final_mb:.1f} MB)[/dim]")

        log_info(f"Downloaded and verified: {out_file.name}")
        return {
            "status": "success",
            "file": out_file,
            "title": title,
            "artist": artist,
            "genre": genre,
            "filename": file_name,
            "size_mb": final_mb
        }

    except KeyboardInterrupt:
        if part_file.exists():
            try:
                part_file.unlink()
            except Exception:
                pass
        sys.stdout.write("\r" + " " * 95 + "\r")
        sys.stdout.flush()
        raise

    except Exception as e:
        log_error(f"Download failed for {raw_title}", e)
        sys.stdout.write("\r" + " " * 95 + "\r")
        sys.stdout.flush()
        display_name = file_name.replace(ext, "").replace(" - ", " — ")
        console.print(f"  [{track_idx}]  [red]✕  {display_name[:36]:<36}  {e}[/red]")
        return {
            "status": "failed",
            "title": raw_title,
            "artist": raw_artist,
            "track_info": track_info,
            "error": str(e)
        }

def generate_m3u_playlist(playlist_name: str, saved_files: list, dest_dir: Path):
    try:
        pl_dir = dest_dir / "Playlists"
        pl_dir.mkdir(parents=True, exist_ok=True)
        clean_pl_name = clean_filename(playlist_name)
        m3u_file = pl_dir / f"{clean_pl_name}.m3u"

        with open(m3u_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for item in saved_files:
                f_path = item.get("file")
                if f_path and f_path.exists():
                    try:
                        rel_path = os.path.relpath(f_path, pl_dir)
                    except ValueError:
                        rel_path = str(f_path)
                    f.write(f"#EXTINF:-1,{item.get('artist', '')} - {item.get('title', '')}\n")
                    f.write(f"{rel_path}\n")

        log_info(f"Generated companion playlist: {m3u_file}")
        return m3u_file
    except Exception as e:
        log_error(f"Failed to generate M3U for {playlist_name}", e)
        return None

def download_batch_tracks(tracks: list, dest_dir: Path = None, playlist_title: str = None) -> dict:
    if not dest_dir:
        dest_dir = get_download_dir()

    total = len(tracks)
    console.print(f"\n  [cyan]●[/cyan] Resolving: [bold white]{playlist_title or 'Collection'}[/] [dim]({total} tracks detected)[/dim]")
    console.print("  " + "─" * 74)

    saved = []
    skipped = []
    failed = []
    start_batch_time = time.time()

    try:
        for idx, track_item in enumerate(tracks, 1):
            idx_str = f"{idx:02d}/{total:02d}"
            res = download_track(
                track_item,
                dest_dir=dest_dir,
                playlist_name=playlist_title,
                track_idx=idx_str
            )
            if res:
                if res.get("status") == "success":
                    saved.append(res)
                elif res.get("status") == "skipped":
                    skipped.append(res)
                else:
                    failed.append(track_item)
            else:
                failed.append(track_item)

    except KeyboardInterrupt:
        console.print("\n  [yellow]⚠ Batch download paused cleanly (Ctrl+C).[/yellow]")

    console.print("  " + "─" * 74)

    # M3U Playlist Companion
    if playlist_title and saved:
        generate_m3u_playlist(playlist_title, saved + skipped, dest_dir)

    total_time = max(time.time() - start_batch_time, 0.001)
    total_saved_mb = sum(s.get("size_mb", 0) for s in saved)
    avg_speed = total_saved_mb / total_time if total_saved_mb > 0 else 0

    parts = [f"[green]{len(saved)} saved[/green]"]
    if skipped:
        parts.append(f"[dim]{len(skipped)} skipped[/dim]")
    if failed:
        parts.append(f"[red]{len(failed)} failed[/red]")

    summary_str = " • ".join(parts)
    speed_str = f"Avg {avg_speed:.1f} MB/s" if avg_speed > 0 else "Instant"
    console.print(f"  Completed: {summary_str}  [dim]•  {speed_str}  •  Category Routing: Done[/dim]\n")

    return {
        "saved": saved,
        "skipped": skipped,
        "failed": failed
    }

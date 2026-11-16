import os
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML

from musicdl.config import (
    load_config,
    get_download_dir,
    set_download_dir
)
from musicdl.spotify import is_spotify_url, extract_spotify_entity
from musicdl.youtube import is_youtube_url, fetch_youtube_audio_stream
from musicdl.downloader import download_track, download_batch_tracks
from musicdl.fixer import scan_music_files, repair_single_file
from musicdl.logger import log_info, log_error

console = Console()

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def get_library_stats(dest: Path):
    if not dest.exists():
        return 0, 0.0
    files = [f for f in dest.rglob("*.*") if f.is_file() and f.suffix.lower() in [".m4a", ".mp3", ".webm", ".flac"]]
    total_bytes = sum(f.stat().st_size for f in files)
    return len(files), total_bytes / (1024 * 1024)

def print_header(dest: Path):
    total_tracks, total_mb = get_library_stats(dest)
    console.print()
    console.print("  [bold white]North Tracks[/bold white]  [dim]•  320k Studio Downloader[/dim]")
    console.print(f"  [dim]{dest}  ({total_tracks} tracks • {total_mb:.1f} MB)[/dim]")
    console.print()

def handle_input(query: str, dest_dir: Path):
    target = query.strip()
    if not target or target.lower() == "b":
        return

    # Command handlers
    cmd = target.lower()
    if cmd in [":dest", ":folder", ":d"]:
        screen_change_destination()
        return
    elif cmd in [":stats", ":library", ":s"]:
        screen_library_stats()
        return
    elif cmd in [":repair", ":fix", ":r"]:
        screen_repair()
        return
    elif cmd in [":exit", ":quit", ":q"]:
        console.print("\n  [cyan]♪ North Tracks closed.[/cyan]\n")
        sys.exit(0)

    # 1. Spotify Link
    if is_spotify_url(target):
        console.print("\n  [cyan]●[/cyan] Resolving Spotify metadata...")
        entity = extract_spotify_entity(target)
        if not entity:
            console.print("  [red]✕ Failed to resolve Spotify link.[/red]")
            return

        tracks = entity.get("tracks", [])
        if not tracks:
            console.print("  [red]✕ No playable tracks found in Spotify link.[/red]")
            return
        is_collection = entity.get("type") in ["playlist", "album"]
        pl_name = entity.get("title") if is_collection else ""

        if len(tracks) > 1:
            batch_result = download_batch_tracks(tracks, dest_dir=dest_dir, playlist_title=pl_name)
            while batch_result.get("failed"):
                failed_tracks = batch_result["failed"]
                console.print(f"  [red]✕ {len(failed_tracks)} track(s) failed.[/red] [dim]Press 'r' to retry, or Enter to continue[/dim]")
                retry_choice = input("  Action › ").strip().lower()
                if retry_choice == "r":
                    batch_result = download_batch_tracks(failed_tracks, dest_dir=dest_dir, playlist_title=pl_name)
                else:
                    break
        elif len(tracks) == 1:
            console.print("  " + "─" * 74)
            download_track(tracks[0], dest_dir=dest_dir, track_idx="01/01")
            console.print("  " + "─" * 74 + "\n")

    # 2. YouTube Link
    elif is_youtube_url(target):
        console.print("\n  [cyan]●[/cyan] Resolving YouTube audio stream via InnerTube...")
        yt_data = fetch_youtube_audio_stream(target)
        if not yt_data:
            console.print("  [red]✕ Could not fetch YouTube audio.[/red]")
            return
        console.print("  " + "─" * 74)
        download_track(yt_data, dest_dir=dest_dir, track_idx="01/01")
        console.print("  " + "─" * 74 + "\n")

    # 3. Direct Song Title Search
    else:
        console.print(f"\n  [cyan]●[/cyan] Searching studio catalog for: [bold white]{target}[/]")
        console.print("  " + "─" * 74)
        download_track({"title": target, "artist": ""}, dest_dir=dest_dir, track_idx="01/01")
        console.print("  " + "─" * 74 + "\n")

def screen_change_destination():
    dest = get_download_dir()
    console.print(f"\n  [bold white]Current Storage:[/] [dim]{dest}[/dim]")
    console.print("  [dim]Enter new folder path (or press Enter / 'b' to cancel):[/dim]")
    new_path = input("  New Path › ").strip()
    if new_path and new_path.lower() != "b":
        updated = set_download_dir(new_path)
        console.print(f"  [green]✓ Storage updated to:[/] {updated}\n")

def screen_library_stats():
    dest = get_download_dir()
    subdirs = [d for d in dest.iterdir() if d.is_dir() and not d.name.startswith(".")] if dest.exists() else []
    total_tracks, total_mb = get_library_stats(dest)

    console.print(f"\n  [bold white]Library Categories[/bold white]  [dim]({total_tracks} tracks • {total_mb:.1f} MB on disk)[/dim]")
    console.print("  " + "─" * 74)

    tbl = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
    tbl.add_column("Category", style="bold white")
    tbl.add_column("Tracks", justify="right", style="cyan")
    tbl.add_column("Size", justify="right", style="dim")
    tbl.add_column("Sample Artists", style="dim")

    for d in sorted(subdirs):
        tracks = list(d.glob("*.m4a")) + list(d.glob("*.mp3")) + list(d.glob("*.webm"))
        dir_mb = sum(t.stat().st_size for t in tracks) / (1024 * 1024)
        artists = []
        for t in tracks[:3]:
            parts = t.stem.split(" - ")
            if len(parts) > 1:
                artists.append(parts[0])
        sample_str = ", ".join(list(dict.fromkeys(artists)))
        tbl.add_row(d.name, str(len(tracks)), f"{dir_mb:.1f} MB", sample_str)

    console.print(tbl)
    console.print("  " + "─" * 74 + "\n")

def screen_repair():
    dest = get_download_dir()
    console.print(f"\n  [bold white]Library Repair & Dual Artwork Verification[/bold white]")
    console.print(f"  [dim]Default scan location: {dest}[/dim]")
    console.print("  [dim]Enter folder path to scan (or press Enter for default / 'b' to cancel):[/dim]")
    custom_dir = input("  Scan Path › ").strip()

    if custom_dir.lower() == "b":
        return

    scan_dir = Path(custom_dir).resolve() if custom_dir else dest
    if not scan_dir.exists() or not scan_dir.is_dir():
        console.print(f"  [red]✕ Directory not found:[/] {scan_dir}\n")
        return

    scanned = scan_music_files(scan_dir)
    if not scanned:
        console.print("  [yellow]No music files found in directory.[/yellow]\n")
        return

    console.print("  " + "─" * 74)
    tbl = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
    tbl.add_column("#", justify="right", style="dim", width=3)
    tbl.add_column("File Name", style="bold white")
    tbl.add_column("Artwork", justify="center")
    tbl.add_column("Folder", style="dim")
    tbl.add_column("Clean Short Name", style="cyan")

    for idx, t in enumerate(scanned, 1):
        art_status = "[green]✓ HD[/green]" if t["has_art"] else "[red]✕ Broken[/red]"
        tbl.add_row(str(idx), t["filename"][:26], art_status, t["current_folder"][:14], t["suggested_name"][:26])

    console.print(tbl)
    console.print("  " + "─" * 74)
    console.print("  [dim]Options: [bold white]A[/bold white] (Fix All)  •  [cyan]1, 3, 5-8[/cyan] (Select)  •  [bold white]b[/bold white] (Cancel)[/dim]")
    choice = input("  Choice › ").strip().upper()

    if choice in ["B", "C", "CANCEL", ""]:
        return

    to_repair = []
    if choice in ["A", "ALL"]:
        to_repair = scanned
    else:
        selected_indices = set()
        for chunk in choice.split(","):
            chunk = chunk.strip()
            if "-" in chunk:
                parts = chunk.split("-")
                try:
                    start, end = int(parts[0]), int(parts[1])
                    selected_indices.update(range(start, end + 1))
                except ValueError:
                    pass
            else:
                try:
                    selected_indices.add(int(chunk))
                except ValueError:
                    pass
        to_repair = [scanned[i - 1] for i in selected_indices if 1 <= i <= len(scanned)]

    if not to_repair:
        console.print("  [red]✕ No valid tracks selected.[/red]\n")
        return

    console.print(f"\n  [cyan]● Repairing {len(to_repair)} track(s)...[/cyan]")
    for item in to_repair:
        res = repair_single_file(item, dest)
        if res:
            console.print(f"  [green]✓[/green]  {res['new_name'][:36]:<36}  [dim]• {res['new_category']} • Art: {res['art_source']}[/dim]")

    console.print(f"  [green]Done.[/green] [dim]{len(to_repair)} track(s) repaired and verified.[/dim]\n")

def main():
    while True:
        try:
            dest = get_download_dir()
            print_header(dest)
            console.print("  [dim]› Paste Spotify/YouTube link, song name, or command (:repair, :dest, :stats, :exit):[/dim]")
            
            raw_input = input("  › ").strip()

            if not raw_input:
                continue

            handle_input(raw_input, dest)

        except KeyboardInterrupt:
            console.print("\n\n  [cyan]♪ North Tracks closed.[/cyan]\n")
            sys.exit(0)
        except Exception as e:
            log_error("Unhandled CLI exception", e)
            console.print(f"\n  [red]✕ Error:[/] {e} [dim](details in northtracks.log)[/dim]\n")

if __name__ == "__main__":
    main()

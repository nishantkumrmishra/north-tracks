# 🎵 North Tracks — 320k Studio Audio Downloader & Library Engine

> Autonomous 320kbps studio music downloader, dual-tier artwork verifier, and automatic category routing engine.

---

## ⚡ Quick Install

### 1. One-Click PowerShell Installer (Windows)
Open PowerShell and run:
```powershell
irm https://raw.githubusercontent.com/nishantkumrmishra/north-tracks/main/install.ps1 | iex
```
*This automatically installs dependencies, configures the environment, and creates the global `northtracks` command.*

### 2. Via `pip` from GitHub
```bash
pip install git+https://github.com/nishantkumrmishra/north-tracks.git
```

Once installed, just type:
```bash
northtracks
```

---

## 🛠 Manual Installation / Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/nishantkumrmishra/north-tracks.git
   cd north-tracks
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run directly:**
   ```bash
   python app.py
   ```
   *(Or double-click `run.bat` on Windows)*

---

## ✨ Features

- **320kbps Studio Master Streams**: Unthrottled JioSaavn DES-ECB CDN stream extraction (`_320` bitrate rewrite) in authentic AAC-LC (`.m4a`).
- **Universal Link Resolution**: Paste Spotify tracks/playlists/albums, YouTube URLs, or song names directly into the prompt.
- **Dual-Tier Artwork Verification Pipeline**:
  - **Tier 1 (Apple iTunes HD)**: Queries official iTunes API for 600×600 / 1000×1000 album artwork.
  - **Tier 2 (JioSaavn CDN)**: High-speed 500×500 studio album cover repository.
  - **Tier 3 (YouTube HD)**: High-resolution web thumbnail fallback.
- **Category-First Library Routing**: Files are organized directly into genre folders (`Indian Indie/`, `Bollywood/`, `Punjabi/`, `Desi Hip-Hop/`, `Pop/`, `Rock/`, `Electronic/`) rather than flat playlist dumps.
- **Companion `.m3u` Playlists**: Automatically builds relative `.m3u` playlists inside `downloads/Playlists/` so media players keep original track sequencing.
- **Fuzzy Duplicate Prevention**: Scans the library fingerprint before sending requests, automatically skipping existing tracks and remasters.
- **Safe `Ctrl+C` Handling**: Streams into `.part` files and atomically renames only upon completion, preventing corrupted partial files.
- **HTTP Range Resume**: Automatically resumes interrupted downloads from where they stopped.
- **Built-in Library Repair & Scanner**: Run `:repair` to scan your existing music collection, fix broken tags/artwork, and reorganize files into categories.
- **Synchronized Lyrics**: Embeds synchronized LRC and plain lyrics via LRCLIB directly into tags.
- **Silent Diagnostic Logging**: Debug details, headers, and tracebacks are logged silently to `northtracks.log`.

---

## 💻 CLI Commands

Type any of these commands directly into the prompt:

| Command | Action |
|---|---|
| `:stats` | View library category breakdown, file counts, and disk usage |
| `:repair` | Scan folder, fix broken artwork, and normalize library |
| `:dest` | Change download destination folder |
| `:exit` | Quit North Tracks |
| `b` or `Enter` | Universal back navigation |

---

## 📄 License
MIT License © [Nishant Kumar Mishra](https://github.com/nishantkumrmishra)

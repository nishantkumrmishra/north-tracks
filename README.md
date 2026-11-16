<p align="center">
  <img src="assets/banner.png" alt="North Tracks Banner" width="100%">
</p>

<h1 align="center">North Tracks</h1>

<p align="center">
  <b>Download any song or playlist in 320kbps studio audio. Clean, fast, and organized.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/northtracks/"><img src="https://img.shields.io/pypi/v/northtracks?color=00C7FF&style=flat-square" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/Audio-320kbps_Studio-00C7FF?style=flat-square" alt="Audio Quality">
  <img src="https://img.shields.io/badge/Artwork-Apple_HD_%2B_Saavn-orange?style=flat-square" alt="Artwork">
  <img src="https://img.shields.io/badge/Platform-Windows_%7C_macOS_%7C_Linux-lightgrey?style=flat-square" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
</p>

---

## Overview

North Tracks is a minimal music downloader for your terminal. Paste any Spotify playlist, YouTube link, or song title, and it downloads authentic 320kbps audio, tags official HD album covers, embeds lyrics, and neatly organizes everything into folders for you.

---

## Installation & Downloads

### Option A: Standalone Windows App (No Python Required)
* Download **`NorthTracks.exe`** from [Releases](https://github.com/nishantkumrmishra/north-tracks/releases).
* Double-click it to run immediately. No Python, no setup, no terminal commands required!

---

### Option B: Install via `pip` (Windows, macOS, Linux)
Open your terminal and run:

```bash
pip install northtracks
```

Then simply type:
```bash
northtracks
```

---

### Option C: Windows 1-Click PowerShell Installer
Open **PowerShell**, paste this single line, and press **Enter**:

```powershell
irm https://raw.githubusercontent.com/nishantkumrmishra/north-tracks/main/install.ps1 | iex
```

---

## Usage Guide

### 1. First-Time Launch
When you open North Tracks for the first time, it asks you where you want to save your music:
```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Welcome to North Tracks!                                                   │
│ Where would you like your music files to be saved?                         │
└────────────────────────────────────────────────────────────────────────────┘

  Default location: C:\Users\<YourName>\Music\NorthTracks
  Press Enter to use default, or enter a custom folder path:
  Music Folder › 
```
*Just press **Enter** to save to your default `Music/NorthTracks` folder, or type any folder path you prefer.*

---

### 2. Paste what you want to download
You can paste:
* **Spotify link** (Playlist, Album, or single song)
* **YouTube link** (Any music video or audio stream)
* **Song name** (e.g. `Kesariya`, `Heat Waves`, `Alag Aasmaan`)

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ NORTH TRACKS  •  320k Studio Engine                 67 tracks  •  577.9 MB │
│ Storage: ~/Music/NorthTracks                          JioSaavn + iTunes HD │
└────────────────────────────────────────────────────────────────────────────┘

  › Paste Spotify / YouTube link or song name:
  [Ctrl+C] Exit   :stats Library   :repair Fix Artwork   :dest Change Folder

  › https://open.spotify.com/playlist/3ptUtfrX1LoxfXhjIFVPnz
```

North Tracks will automatically:
1. Stream in **320kbps AAC studio audio**.
2. Download official **HD artwork** from Apple Music and JioSaavn.
3. Automatically route the song into its category folder (`Indian Indie/`, `Bollywood/`, `Pop/`, `Punjabi/`, etc.).
4. **Skip duplicates** so you never download the same song twice.
5. Create a companion `.m3u` playlist so your media player plays it in order.

---

## Commands

Type any of these inside North Tracks:

| Command | What it does |
|---|---|
| `:stats` | See all your music categories, number of songs, and size on disk. |
| `:repair` | Fix broken album art, missing tags, or messy names in any folder. |
| `:dest` | Change the folder where your songs are saved. |
| `:exit` | Close North Tracks. |
| `b` or `Enter` | Go back from any screen. |

---

## License

MIT License © [Nishant Kumar Mishra](https://github.com/nishantkumrmishra)

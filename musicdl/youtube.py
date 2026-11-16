import re
import json
import urllib.parse
import requests

YOUTUBE_URL_REGEX = re.compile(
    r"(?:youtube\.com\/(?:watch\?.*v=|embed\/|shorts\/|v\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
)

INNERTUBE_CLIENTS = [
    {
        "clientName": "ANDROID_VR",
        "clientVersion": "1.60.19",
        "deviceMake": "Oculus",
        "deviceModel": "Quest 3",
        "osName": "Android",
        "osVersion": "12L",
        "userAgent": "com.google.android.apps.youtube.vr.oculus/1.60.19 (Linux; U; Android 12L; eureka-user Build/SQ3A.220605.009.A1) gzip"
    },
    {
        "clientName": "TVHTML5",
        "clientVersion": "7.20250101.07.00",
        "deviceMake": "Samsung",
        "deviceModel": "SmartTV",
        "osName": "Tizen",
        "osVersion": "7.0",
        "userAgent": "Mozilla/5.0 (SMART-TV; Linux; Tizen 7.0) Cobalt/25.lts.30"
    }
]

def is_youtube_url(url: str) -> bool:
    if not url:
        return False
    return bool(YOUTUBE_URL_REGEX.search(url.strip()))

def extract_video_id(url: str) -> str:
    if not url:
        return None
    trimmed = url.strip()
    if len(trimmed) == 11 and "/" not in trimmed and "?" not in trimmed:
        return trimmed
    match = YOUTUBE_URL_REGEX.search(trimmed)
    return match.group(1) if match else None

def search_youtube_audio(query: str) -> dict:
    """Searches YouTube and returns best audio stream"""
    try:
        clean_q = urllib.parse.quote(query.strip())
        search_url = f"https://www.youtube.com/results?search_query={clean_q}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        resp = requests.get(search_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
            if match:
                video_id = match.group(1)
                return fetch_youtube_audio_stream(video_id)
    except Exception:
        pass
    return None

def fetch_youtube_audio_stream(video_id: str) -> dict:
    clean_id = extract_video_id(video_id) or video_id
    for client in INNERTUBE_CLIENTS:
        try:
            payload = {
                "context": {
                    "client": {
                        "clientName": client["clientName"],
                        "clientVersion": client["clientVersion"],
                        "deviceMake": client["deviceMake"],
                        "deviceModel": client["deviceModel"],
                        "osName": client["osName"],
                        "osVersion": client["osVersion"],
                        "hl": "en",
                        "gl": "US"
                    }
                },
                "videoId": clean_id,
                "playbackContext": {
                    "contentPlaybackContext": {
                        "html5Preference": "HTML5_PREF_WANTS"
                    }
                }
            }

            resp = requests.post(
                "https://www.youtube.com/youtubei/v1/player",
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": client["userAgent"]
                },
                json=payload,
                timeout=10
            )

            if resp.status_code != 200:
                continue

            data = resp.json()
            details = data.get("videoDetails", {})
            streaming_data = data.get("streamingData", {})
            if not details or not streaming_data:
                continue

            formats = streaming_data.get("adaptiveFormats", [])
            audio_formats = [
                f for f in formats if f.get("url") and "audio/" in f.get("mimeType", "")
            ]

            if not audio_formats:
                continue

            # Sort by bitrate descending
            audio_formats.sort(key=lambda x: int(x.get("bitrate", 0)), reverse=True)
            best_audio = audio_formats[0]

            thumbs = details.get("thumbnail", {}).get("thumbnails", [])
            artwork = thumbs[-1]["url"] if thumbs else f"https://i.ytimg.com/vi/{clean_id}/hqdefault.jpg"

            return {
                "id": clean_id,
                "title": details.get("title", "YouTube Audio"),
                "artist": details.get("author", "YouTube Creator"),
                "album": "YouTube Audio",
                "duration": int(details.get("lengthSeconds", "0")),
                "artwork_url": artwork,
                "stream_url": best_audio["url"],
                "bitrate": f"{round(best_audio.get('bitrate', 160000) / 1000)}kbps",
                "source": "YouTube Innertube",
                "is_webm": "audio/webm" in best_audio.get("mimeType", "")
            }
        except Exception:
            continue

    return None

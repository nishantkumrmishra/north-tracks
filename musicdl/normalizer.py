import re
from pathlib import Path

def clean_filename(name: str) -> str:
    if not name:
        return "track"
    cleaned = re.sub(r'[\/\\:*?"<>|]', "_", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:150]

def clean_short_filename(artist: str, title: str, ext: str = ".m4a") -> str:
    t = re.sub(r"\(.*?\)|\[.*?\]", "", title).strip()
    t = re.sub(r'[\/\\:*?"<>|]', "_", t)
    t = re.sub(r"\s+", " ", t).strip()

    a = re.split(r",|&|\bft\.|\bfeat\.|\bwith\b", artist or "", flags=re.IGNORECASE)[0].strip()
    a = re.sub(r"(?i)\s*music\s*", "", a).strip()
    a = re.sub(r'[\/\\:*?"<>|]', "_", a)
    a = re.sub(r"\s+", " ", a).strip()

    if not a or a.lower() in ["unknown", "various artists", "various"]:
        return f"{t}{ext}"

    return f"{a} - {t}{ext}"

def clean_search_query(text: str) -> str:
    if not text:
        return ""
    t = text
    t = t.replace("&quot;", '"').replace("&amp;", "&").replace("&#039;", "'")
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"\[.*?\]", "", t)
    t = re.sub(r"\{.*?\}", "", t)
    t = re.sub(r"(?i)official\s*(music\s*)?(video|mv|audio)", "", t)
    t = re.sub(r"(?i)lyric(s)?(\s*video)?", "", t)
    t = re.sub(r"(?i)visualizer", "", t)
    t = re.sub(r"(?i)full\s*(song|video|audio)", "", t)
    t = re.sub(r"(?i)feat\..*$", "", t)
    t = re.sub(r"(?i)ft\..*$", "", t)
    t = re.sub(r"(?i)prod\..*$", "", t)
    t = re.sub(r"[\-_/|]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def match_any_phrase(text: str, phrases: list) -> bool:
    if not text:
        return False
    t_lower = text.lower()
    for p in phrases:
        pattern = r"\b" + re.escape(p) + r"\b"
        if re.search(pattern, t_lower):
            return True
    return False

def has_devanagari(text: str) -> bool:
    return any("\u0900" <= c <= "\u097f" for c in text or "")

HINDI_URDU_WORDS = [
    "dil", "ishq", "pyaar", "pyar", "mohabbat", "khayaal", "khayal", "tumhara", "aasmaan",
    "juda", "piya", "udi", "zaroor", "kashish", "jaana", "jana", "hawa", "banke",
    "qaatil", "gumshuda", "majboor", "meena", "bazaar", "hoor", "jigar", "kyun",
    "soya", "sheher", "tera", "teri", "tere", "savan", "barse", "nainowale", "naino",
    "apke", "aapke", "surma", "kasoor", "ishqa", "saajna", "sajna", "raatein", "sukoon",
    "chalo", "musafir", "shayad", "samjhawan", "tu hain toh", "saiyaara", "darmiyaan",
    "balma", "kinna sona", "tere vaaste", "fakira", "kangana", "aarzu", "sapno mein",
    "kol mere", "kol", "channa", "ve", "mere", "mera", "meri", "humdum", "raah",
    "alfaaz", "elhaam", "kahin", "deewana", "hua", "main", "mehfil", "chand", "roshni",
    "dariya", "manzil", "yaara", "duaa", "dua", "rabba", "allah", "khuda", "nasha",
    "bewafa", "wafa", "jeena", "marjaana", "ranjha", "heer", "punjaban"
]

def has_hindi_urdu_term(text: str) -> bool:
    t_lower = (text or "").lower()
    for w in HINDI_URDU_WORDS:
        if re.search(r"\b" + re.escape(w) + r"\b", t_lower):
            return True
    return False

def make_song_fingerprint(artist: str, title: str) -> str:
    clean_t = re.sub(r"\(.*?\)|\[.*?\]|remastered.*|film.*|audio.*", "", title or "", flags=re.IGNORECASE)
    clean_t = re.sub(r"[^a-zA-Z0-9\u0900-\u097F]", "", clean_t).lower()
    
    clean_a = re.split(r",|&|\bft\.|\bfeat\.", artist or "", flags=re.IGNORECASE)[0]
    clean_a = re.sub(r"[^a-zA-Z0-9\u0900-\u097F]", "", clean_a).lower()
    
    return f"{clean_t}__{clean_a}"

def find_library_duplicate(artist: str, title: str, dest_dir: Path) -> Path:
    if not dest_dir or not dest_dir.exists():
        return None
    
    target_fp = make_song_fingerprint(artist, title)
    target_title_fp = re.sub(r"[^a-zA-Z0-9\u0900-\u097F]", "", re.sub(r"\(.*?\)|\[.*?\]", "", title or "")).lower()

    valid_exts = {".m4a", ".mp3", ".flac", ".wav", ".aac", ".ogg", ".webm"}
    for f in dest_dir.rglob("*.*"):
        if f.is_file() and f.suffix.lower() in valid_exts and f.stat().st_size > 500000:
            stem = f.stem
            parts = stem.split(" - ")
            f_artist = parts[0] if len(parts) > 1 else ""
            f_title = parts[1] if len(parts) > 1 else stem
            
            f_fp = make_song_fingerprint(f_artist, f_title)
            if f_fp == target_fp and target_fp.strip("_"):
                return f
            
            f_t_fp = re.sub(r"[^a-zA-Z0-9\u0900-\u097F]", "", f_title).lower()
            if len(target_title_fp) >= 5 and f_t_fp == target_title_fp:
                return f

    return None

KPOP_ARTISTS = [
    "bts", "blackpink", "twice", "stray kids", "newjeans", "seventeen",
    "enhypen", "exo", "tomorrow x together", "txt", "le sserafim",
    "aespa", "itzy", "jungkook", "jimin", "agust d", "suga", "taehyung",
    "namjoon", "seokjin", "hoseok", "iu", "red velvet", "nct", "ateez", "got7"
]

INDIAN_INDIE_ARTISTS = [
    "anuv jain", "the local train", "local train", "prateek kuhad", "when chai met toast",
    "karun", "nanku", "lifafa", "raghav meattle", "abhijay sharma", "abhay jodhpurkar",
    "suvitzz", "prankur music", "prankur", "faheem abdullah", "zaeden", "jasleen royal",
    "taba chake", "kavita seth", "bayaan", "the yellow diary", "twin strings",
    "sanah moidutty", "arjun kanungo", "kasyap", "osho jain", "ronit vinta",
    "akash ahuja", "akshath", "mitraz", "chaar diwaari", "swarathma",
    "parvaaz", "indian ocean", "lost stories", "achint", "aditya rikhari",
    "kavya", "parimal shroff", "adnan sami", "papon", "lucky ali", "silk route", "euphoria",
    "airovin", "dubble beats", "swattrex", "siddharth bhavsar", "ojas", "oaff", "savera",
    "darshan raval", "aparshakti khurana", "keshav tyohar", "ashish bhatia", "rishabh vyas",
    "aviverse", "mizajii", "prabhanjan", "ruhav", "salem sandhu", "aks", "aneesh",
    "natkhat", "hasan s. iqbal", "hitesh", "kartik ariyan", "w.i.s.h.", "zeeshan ali",
    "animesh", "badkrazy", "ishan krishan", "noor", "ryanded", "umar quadri", "hunny"
]

DESI_HIPHOP_ARTISTS = [
    "seedhe maut", "kr$na", "krsna", "divine", "raftaar", "mc stan",
    "emiway bantai", "emiway", "talha anjum", "talhah yunus", "young stunners",
    "ikka", "karma", "epr", "brodha v", "dino james", "fotty seven",
    "frappe ash", "yungsta", "umair", "mithun jana"
]

BOLLYWOOD_ARTISTS = [
    "arijit singh", "pritam", "shreya ghoshal", "a.r. rahman", "ar rahman",
    "badshah", "neha kakkar", "jubin nautiyal", "atif aslam", "sanam puri",
    "neeti mohan", "sonu nigam", "shaan", "kumar sanu", "udit narayan",
    "alka yagnik", "sunidhi chauhan", "shankar-ehsaan-loy", "shankar ehsaan loy",
    "amit trivedi", "sachin-jigar", "sachin jigar", "mithoon", "vishal & shekhar",
    "vishal-shekhar", "vishal dadlani", "shekhar ravjiani", "armaan malik",
    "amaal mallik", "himesh reshammiya", "kk", "mohit chauhan", "tanishk bagchi",
    "sachet tandon", "parampara tandon", "rochak kohli", "jasleen royal",
    "amtee", "salim-sulaiman", "shafqat amanat ali", "shriram", "sunil kamath", "vishal"
]

PUNJABI_ARTISTS = [
    "diljit dosanjh", "diljit", "sidhu moose wala", "sidhu moose", "ap dhillon",
    "karan aujla", "shubh", "talwiinder", "yo yo honey singh", "honey singh",
    "amrit maan", "jass manak", "gurdas maan", "babbu maan", "hardy sandhu",
    "guru randhawa", "b praak", "jaani", "ammy virk", "parmish verma",
    "jassi gill", "mankirt aulakh", "sukhe", "kaka", "sharn", "kunwarr", "maan panu"
]

SOUTH_INDIAN_ARTISTS = [
    "anirudh ravichander", "anirudh", "sid sriram", "devi sri prasad",
    "dsp", "ilayaraja", "yuvan shankar raja", "santhosh narayanan",
    "harris jayaraj", "thaman s", "thaman", "g.v. prakash", "s.p. balasubrahmanyam",
    "chithra", "chinmayi"
]

def normalize_genre(raw_genre: str = "", artist: str = "", title: str = "", context: str = "") -> str:
    g = (raw_genre or "").lower().strip()
    a = (artist or "").lower().strip()
    t = (title or "").lower().strip()
    c = (context or "").lower().strip()

    # 1. K-Pop (Priority to prevent misclassification)
    if "k-pop" in g or "kpop" in g or "korean" in g or "kpop" in c:
        return "K-Pop"
    if match_any_phrase(a, KPOP_ARTISTS):
        return "K-Pop"

    # 2. Desi Hip-Hop
    if match_any_phrase(a, DESI_HIPHOP_ARTISTS):
        return "Desi Hip-Hop"

    # 3. Punjabi
    if "punjabi" in g or "bhangra" in g or match_any_phrase(a, PUNJABI_ARTISTS) or "punjabi" in c:
        return "Punjabi"

    # 4. South Indian
    if any(k in g for k in ["tamil", "telugu", "malayalam", "kannada", "tollywood", "kollywood"]) or match_any_phrase(a, SOUTH_INDIAN_ARTISTS):
        return "South Indian"

    # 5. Bollywood / Hindi OST
    is_bollywood = (
        "bollywood" in g or "filmi" in g or
        ("soundtrack" in g and (match_any_phrase(a, BOLLYWOOD_ARTISTS) or "ost" in c or "soundtrack" in c)) or
        match_any_phrase(a, BOLLYWOOD_ARTISTS)
    )
    if is_bollywood:
        return "Bollywood"

    # 6. Indian Indie & Chill Mood (Devanagari / Hindi-Urdu / Indian Artist / Chill context)
    is_devanagari = has_devanagari(t) or has_devanagari(a)
    is_hindi_terms = has_hindi_urdu_term(t) or has_hindi_urdu_term(a)
    is_indie_artist = match_any_phrase(a, INDIAN_INDIE_ARTISTS)
    looks_indian = any(k in a for k in ["singh", "kumar", "jain", "train", "kuhad", "sharma", "abdullah", "meattle", "royal", "jodhpurkar", "airovin", "beats"])
    is_chill_context = any(k in c for k in ["chill", "indie", "sukoon", "mood", "lofi", "relax", "chai", "coffee"])

    if is_indie_artist or is_devanagari or is_hindi_terms or (is_chill_context and looks_indian):
        if any(k in g for k in ["hip-hop", "hip hop", "rap"]):
            return "Desi Hip-Hop"
        return "Indian Indie"

    # 7. Western & Global Genres
    if any(k in g for k in ["hip-hop", "hip hop", "rap", "trap"]):
        return "Hip-Hop"
    if any(k in g for k in ["indie", "alternative", "folk"]):
        return "Indie"
    if any(k in g for k in ["rock", "metal", "punk", "hard rock"]):
        return "Rock"
    if any(k in g for k in ["electronic", "edm", "dance", "house", "techno", "ambient"]):
        return "Electronic"
    if any(k in g for k in ["lo-fi", "lofi", "chill", "chillhop"]):
        return "Lo-Fi"
    if any(k in g for k in ["r&b", "soul"]):
        return "R&B"
    if any(k in g for k in ["jazz", "blues"]):
        return "Jazz"
    if any(k in g for k in ["classical", "instrumental"]):
        return "Classical"

    if "bollywood" in c:
        return "Bollywood"

    return "Pop"

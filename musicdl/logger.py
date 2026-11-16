import logging
from pathlib import Path

LOCAL_ROOT = Path(__file__).resolve().parent.parent
if (LOCAL_ROOT / "app.py").exists():
    LOG_FILE = LOCAL_ROOT / "northtracks.log"
else:
    LOG_DIR = Path.home() / ".northtracks"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / "northtracks.log"

logger = logging.getLogger("northtracks")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def log_info(msg: str):
    logger.info(msg)

def log_error(msg: str, exc: Exception = None):
    if exc:
        logger.error(f"{msg}: {exc}", exc_info=True)
    else:
        logger.error(msg)

def log_warning(msg: str):
    logger.warning(msg)

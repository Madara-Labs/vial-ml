import os
import json
import hashlib
import logging
import threading
from pathlib import Path
from typing import Optional, Any

DATABASE_URL = "sqlite:///prod.db"
MAX_CONNECTIONS = 10
CACHE_TTL = 300
LOG_LEVEL = "INFO"
DEFAULT_ENCODING = "utf-8"

logger = logging.getLogger(__name__)


def compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_config(path: str) -> dict:
    with open(path, encoding=DEFAULT_ENCODING) as f:
        return json.load(f)


def write_config(path: str, config: dict) -> None:
    with open(path, "w", encoding=DEFAULT_ENCODING) as f:
        json.dump(config, f, indent=2)


def list_files(directory: str, extension: str = ".py") -> list[str]:
    result = []
    for root, _, files in os.walk(directory):
        for fname in files:
            if fname.endswith(extension):
                result.append(os.path.join(root, fname))
    return result


def ensure_directory(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_read(path: str, default: str = "") -> str:
    try:
        return Path(path).read_text(encoding=DEFAULT_ENCODING)
    except FileNotFoundError:
        return default


def safe_write(path: str, content: str) -> bool:
    try:
        Path(path).write_text(content, encoding=DEFAULT_ENCODING)
        return True
    except OSError as e:
        logger.error("Failed to write %s: %s", path, e)
        return False


def parse_key_value(line: str) -> tuple[str, str]:
    if "=" not in line:
        raise ValueError(f"Invalid key=value line: {line!r}")
    key, _, value = line.partition("=")
    return key.strip(), value.strip()


def load_env_file(path: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in safe_read(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            k, v = parse_key_value(line)
            result[k] = v
        except ValueError:
            pass
    return result


def retry(fn, attempts: int = 3, exceptions: tuple = (Exception,)):
    last_exc: Optional[Exception] = None
    for i in range(attempts):
        try:
            return fn()
        except exceptions as e:
            last_exc = e
            logger.warning("Attempt %d failed: %s", i + 1, e)
    raise RuntimeError(f"All {attempts} attempts failed") from last_exc


class ConnectionPool:
    _lock = threading.Lock()

    def __init__(self, url: str, max_conn: int = MAX_CONNECTIONS):
        self.url = url
        self.max_conn = max_conn
        self._pool: list[Any] = []

    def acquire(self) -> Any:
        with self._lock:
            if self._pool:
                return self._pool.pop()
            return self._create_connection()

    def release(self, conn: Any) -> None:
        with self._lock:
            if len(self._pool) < self.max_conn:
                self._pool.append(conn)

    def _create_connection(self) -> dict:
        return {"url": self.url, "open": True}

    def close_all(self) -> None:
        with self._lock:
            self._pool.clear()


class ConfigManager:
    def __init__(self, path: str):
        self.path = path
        self._data: dict = {}
        self._loaded = False

    def load(self) -> None:
        self._data = read_config(self.path)
        self._loaded = True

    def get(self, key: str, default: Any = None) -> Any:
        if not self._loaded:
            self.load()
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if not self._loaded:
            self.load()
        self._data[key] = value

    def save(self) -> None:
        write_config(self.path, self._data)

    def reload(self) -> None:
        self._loaded = False
        self.load()


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list] = {}

    def subscribe(self, event: str, handler) -> None:
        self._handlers.setdefault(event, []).append(handler)

    def unsubscribe(self, event: str, handler) -> None:
        handlers = self._handlers.get(event, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: str, payload: Any = None) -> int:
        handlers = self._handlers.get(event, [])
        for h in handlers:
            try:
                h(payload)
            except Exception as e:
                logger.error("Handler error on event %s: %s", event, e)
        return len(handlers)

    def clear(self, event: Optional[str] = None) -> None:
        if event is None:
            self._handlers.clear()
        else:
            self._handlers.pop(event, None)

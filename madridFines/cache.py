
# Almacenamiento local de los datos descargados de las multas de tráfico del Ayuntamiento de Madrid.
import time
from pathlib import Path
import requests
import hashlib

class CacheError(Exception):
    """Error al usar la caché."""
    pass

class Cache:
    BASE_DIR = Path(__file__).parent.parent / "cache"

    def __init__(self, app_name, obsolescence=7):
        self.app_name = app_name
        self.obsolescence = obsolescence
        self.cache_dir = self.BASE_DIR / app_name
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _filepath(self, name):
        return self.cache_dir / name

    def set(self, name, data):
        try:
            self._filepath(name).write_text(data, encoding="utf-8")
        except OSError as e:
            raise CacheError(f"Error en escritura en {name}: {e}") from e

    def exists(self, name):
        return self._filepath(name).exists()

    def load(self, name):
        path = self._filepath(name)
        if not path.exists():
            raise CacheError(f"No existe {name} en la caché.")
        try:
            return path.read_text(encoding="utf-8")
        except OSError as e:
            raise CacheError(f"No se pudo leer {name}: {e}") from e

    def how_old(self, name):
        # Obsolescencia del caché en milisegundos.
        path = self._filepath(name)
        if not path.exists():
            raise CacheError(f"No existe {name} en la caché.")
        return (time.time() - path.stat().st_mtime) * 1000

    def delete(self, name):
        path = self._filepath(name)
        if path.exists():
            try:
                path.unlink()
            except OSError as e:
                raise CacheError(f"No se pudo borrar {name}: {e}") from e

    def clear(self):
        for file in self.cache_dir.iterdir():
            if file.is_file():
                file.unlink()

    def _is_obsolete(self, name):
        path = self._filepath(name)
        if not path.exists():
            return True
        age_days = (time.time() - path.stat().st_mtime) / 86400
        return age_days > self.obsolescence

class CacheURL(Cache):
    """Caché para descargas de URLs usando hash md5 como nombre de fichero."""

    def _hash_url(self, url):
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def get(self, url):
        key = self._hash_url(url)
        if super().exists(key) and not self._is_obsolete(key):
            return super().load(key)
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise CacheError(f"Error al descargar {url}: {e}") from e
        content = response.text
        self.set(key, content)
        return content

    def exists(self, url):
        return super().exists(self._hash_url(url))

    def load(self, url):
        return super().load(self._hash_url(url))

    def how_old(self, url):
        return super().how_old(self._hash_url(url))

    def delete(self, url):
        super().delete(self._hash_url(url))


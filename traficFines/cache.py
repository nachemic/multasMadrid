
# Almacenamiento local de los datos descargados de las multas de tráfico del Ayuntamiento de Madrid.
import hashlib
import time
from pathlib import Path

import requests

class CacheError(Exception):
    """Error al usar la caché."""
    pass


class Cache:
    CACHE_DIR = Path.home() / ".my_cache"

    def __init__(self, app_name, obsolescence=7, base_dir=None):
        root_dir = Path(base_dir) if base_dir is not None else self.CACHE_DIR
        self._app_name = app_name
        self._obsolescence = obsolescence
        self._cache_dir = root_dir / app_name
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def app_name(self):
        return self._app_name

    @property
    def obsolescence(self):
        return self._obsolescence

    @property
    def cache_dir(self):
        return str(self._cache_dir)

    def _filepath(self, name):
        return self._cache_dir / name

    def set(self, name, data):
        try:
            with self._filepath(name).open("w", encoding="utf-8", newline="") as file:
                file.write(data)
        except OSError as e:
            raise CacheError(f"Error en escritura en {name}: {e}") from e

    def exists(self, name):
        return self._filepath(name).exists()

    def load(self, name):
        path = self._filepath(name)
        if not path.exists():
            raise CacheError(f"No existe {name} en la caché.")
        try:
            with path.open("r", encoding="utf-8", newline="") as file:
                return file.read()
        except OSError as e:
            raise CacheError(f"No se pudo leer {name}: {e}") from e

    def how_old(self, name):
        path = self._filepath(name)
        if not path.exists():
            raise CacheError(f"No existe {name} en la caché.")
        return (time.time() - path.stat().st_mtime) * 1000 # en ms

    def delete(self, name):
        path = self._filepath(name)
        if path.exists():
            try:
                path.unlink()
            except OSError as e:
                raise CacheError(f"No se pudo borrar {name}: {e}") from e

    def clear(self):
        for file in self._cache_dir.iterdir():
            if file.is_file():
                try:
                    file.unlink()
                except OSError as e:
                    raise CacheError(f"No se pudo borrar {file.name}: {e}") from e

    def _is_obsolete(self, name):
        path = self._filepath(name)
        if not path.exists():
            return True
        age_days = (time.time() - path.stat().st_mtime) / 86400
        return age_days > self._obsolescence


class CacheURL(Cache):
    """Caché para descargas de URLs usando hash md5 como nombre de fichero."""

    @staticmethod
    def _hash_key(url, params=None, encoding=None):
        if not params:
            cache_key = url
        else:
            sorted_params = "&".join(f"{key}={value}" for key, value in sorted(params.items()))
            cache_key = f"{url}?{sorted_params}"
        if encoding:
            cache_key = f"{cache_key}#encoding={encoding.lower()}"
        return hashlib.md5(cache_key.encode("utf-8")).hexdigest()

    def get(self, url, params=None, encoding=None):
        key = self._hash_key(url, params, encoding)
        if super().exists(key) and not self._is_obsolete(key):
            return super().load(key)
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise CacheError(f"Error al descargar {url}: {e}") from e
        response.encoding = encoding or response.encoding or response.apparent_encoding or "utf-8"
        content = response.text
        self.set(key, content)
        return content

    def exists(self, url, params=None):
        return super().exists(self._hash_key(url, params))

    def load(self, url, params=None, encoding=None):
        return super().load(self._hash_key(url, params, encoding))

    def how_old(self, url, params=None, encoding=None):
        return super().how_old(self._hash_key(url, params, encoding))

    def delete(self, url, params=None, encoding=None):
        super().delete(self._hash_key(url, params, encoding))


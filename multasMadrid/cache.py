"""
Almacenamiento local de los datos descargados de las multas de tráfico del Ayuntamiento de Madrid.
"""

import hashlib
import time
from pathlib import Path
import requests

class CacheError(Exception):
    """Error al usar la caché."""
    pass


class Cache:

    BASE_DIR = Path(__file__).parent.parent / "cache"

    def __init__(self, app_name, obsolescence=7):
        # Los datos se consideran obsoletos si tienen más de 7 días.
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
    # Hereda Cache para añadir lógica que trabaja con URLs.
    # En lugar de usar el nombre directo, guarda los datos con un hash de la URL.

    """Caché para descargas de URLs.

    Guarda la respuesta de una URL usando un hash como nombre.
    """

    def _hash_url(self, url):
        """
        Crea un hash de la URL para usarlo como nombre de fichero.
        """
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def get(self, url):
        # Si el resultado está en caché y no está caducado, lo devuelve.
        # Si no, descarga la URL y guarda el contenido.

        """
        Descarga la URL o devuelve el resultado de la caché si está fresco.

        Variables:
        url (str): La URL a descargar.

        Output:
        str: Contenido de la URL.

        Ejemplos:
        >>> cache.get("http://example.com")
        '<html>...</html>'
        """
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
        """
        Comprueba si existe el contenido de una URL en caché.

        Variables:
        url (str): La URL a comprobar.

        Output:
        bool: True si existe en caché.
        """
        return super().exists(self._hash_url(url))

    def load(self, url):
        """
        Carga el contenido de una URL desde caché.

        Variables:
        url (str): La URL a cargar.

        Output:
        str: Contenido almacenado.
        """
        return super().load(self._hash_url(url))

    def how_old(self, url):
        """
        Devuelve la edad de una URL en la caché.

        Variables:
        url (str): La URL a consultar.

        Output:
        float: Edad en milisegundos.
        """
        return super().how_old(self._hash_url(url))

    def delete(self, url):
        """
        Borra de la caché el contenido asociado a una URL.

        Variables:
        url (str): La URL a borrar.

        Output:
        None
        """
        super().delete(self._hash_url(url))

    def exists(self, url):
        """
        Comprueba si la URL está en caché.

        Variables:
        url (str): La URL.

        Output:
        bool: True si existe.

        Ejemplos:
        >>> cache.exists("http://example.com")
        True
        """
        return super().exists(self._hash_url(url))

    def load(self, url):
        """
        Carga el contenido de la URL desde caché.

        Variables:
        url (str): La URL.

        Output:
        str: Contenido guardado.

        Ejemplos:
        >>> cache.load("http://example.com")
        '<html>...</html>'
        """
        return super().load(self._hash_url(url))

    def how_old(self, url):
        """
        Devuelve la edad de la URL en caché.

        Variables:
        url (str): La URL.

        Output:
        float: Edad en milisegundos.

        Ejemplos:
        >>> cache.how_old("http://example.com")
        1000.0
        """
        return super().how_old(self._hash_url(url))

    def delete(self, url):
        """
        Borra la URL de la caché.

        Variables:
        url (str): La URL.

        Output:
        None

        Ejemplos:
        >>> cache.delete("http://example.com")
        """
        return super().delete(self._hash_url(url))

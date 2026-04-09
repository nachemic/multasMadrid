"""Tests para el módulo de caché."""

import hashlib
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traficFines.cache import Cache, CacheError, CacheURL

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class TestCache(unittest.TestCase):
    def setUp(self):
        self.cache = Cache("test_app", obsolescence=7, base_dir=DATA_DIR)
        Path(self.cache.cache_dir).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        for file in Path(self.cache.cache_dir).iterdir():
            file.unlink()

    def test_set_and_load(self):
        self.cache.set("clave", "hola")
        self.assertTrue(self.cache.exists("clave"))
        self.assertEqual(self.cache.load("clave"), "hola")

    @patch("pathlib.Path.open", side_effect=OSError("fallo escritura"))
    def test_set_raises_on_write_error(self, _mock_open):
        with self.assertRaises(CacheError):
            self.cache.set("clave", "hola")

    def test_load_missing(self):
        with self.assertRaises(CacheError):
            self.cache.load("no_existe")

    def test_load_raises_on_read_error(self):
        self.cache.set("clave", "hola")

        with patch("pathlib.Path.open", side_effect=OSError("fallo lectura")):
            with self.assertRaises(CacheError):
                self.cache.load("clave")

    def test_how_old(self):
        self.cache.set("clave", "hola")
        age1 = self.cache.how_old("clave")
        time.sleep(0.05)
        age2 = self.cache.how_old("clave")
        self.assertGreater(age2, age1)

    def test_how_old_missing_raises(self):
        with self.assertRaises(CacheError):
            self.cache.how_old("no_existe")

    def test_delete(self):
        self.cache.set("clave", "hola")
        self.cache.delete("clave")
        self.assertFalse(self.cache.exists("clave"))

    @patch("pathlib.Path.unlink", side_effect=OSError("fallo borrado"))
    def test_delete_raises_on_unlink_error(self, _mock_unlink):
        self.cache.set("clave", "hola")

        with self.assertRaises(CacheError):
            self.cache.delete("clave")

    def test_clear(self):
        self.cache.set("a", "1")
        self.cache.set("b", "2")
        self.cache.clear()
        self.assertFalse(self.cache.exists("a"))
        self.assertFalse(self.cache.exists("b"))

    @patch("pathlib.Path.unlink", side_effect=OSError("fallo clear"))
    def test_clear_raises_on_unlink_error(self, _mock_unlink):
        self.cache.set("a", "1")

        with self.assertRaises(CacheError):
            self.cache.clear()

    def test_is_obsolete(self):
        self.cache.set("viejo", "datos")
        path = self.cache._filepath("viejo")
        old_time = time.time() - (10 * 86400)
        os.utime(path, (old_time, old_time))
        self.assertTrue(self.cache._is_obsolete("viejo"))

    def test_is_obsolete_returns_true_for_missing_file(self):
        self.assertTrue(self.cache._is_obsolete("no_existe"))

    def test_is_obsolete_returns_false_for_recent_file(self):
        self.cache.set("nuevo", "datos")
        self.assertFalse(self.cache._is_obsolete("nuevo"))


class TestCacheURL(unittest.TestCase):
    TEST_URL = "https://ejemplo.com/datos.csv"
    TEST_CONTENT = "col1;col2\nval1;val2\n"

    def setUp(self):
        self.cache = CacheURL("test_url_app", obsolescence=7, base_dir=DATA_DIR)
        Path(self.cache.cache_dir).mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        for file in Path(self.cache.cache_dir).iterdir():
            file.unlink()

    def _url_hash(self, url):
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    @patch("traficFines.cache.requests.get")
    def test_get_downloads_and_caches(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = self.TEST_CONTENT
        mock_response.encoding = "utf-8"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = self.cache.get(self.TEST_URL)

        self.assertEqual(result, self.TEST_CONTENT)
        self.assertTrue(self.cache.exists(self.TEST_URL))

    @patch("traficFines.cache.requests.get")
    def test_get_uses_cache(self, mock_get):
        name = self._url_hash(self.TEST_URL)
        Path(self.cache.cache_dir).joinpath(name).write_text(self.TEST_CONTENT, encoding="utf-8", newline="")
        result = self.cache.get(self.TEST_URL)
        self.assertEqual(result, self.TEST_CONTENT)
        mock_get.assert_not_called()

    @patch("traficFines.cache.requests.get")
    def test_get_raises_on_download_error(self, mock_get):
        import requests as req_module

        mock_get.side_effect = req_module.RequestException("fallo")

        with self.assertRaises(CacheError):
            self.cache.get(self.TEST_URL)

    def test_url_helpers(self):
        name = self._url_hash(self.TEST_URL)
        Path(self.cache.cache_dir).joinpath(name).write_text(self.TEST_CONTENT, encoding="utf-8", newline="")
        self.assertTrue(self.cache.exists(self.TEST_URL))
        self.assertEqual(self.cache.load(self.TEST_URL), self.TEST_CONTENT)
        self.assertGreaterEqual(self.cache.how_old(self.TEST_URL), 0)
        self.cache.delete(self.TEST_URL)
        self.assertFalse(self.cache.exists(self.TEST_URL))

    def test_properties_are_exposed_read_only(self):
        self.assertEqual(self.cache.app_name, "test_url_app")
        self.assertEqual(self.cache.obsolescence, 7)
        self.assertTrue(str(self.cache.cache_dir).endswith("test_url_app"))


if __name__ == "__main__":
    unittest.main()

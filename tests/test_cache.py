"""Tests para el módulo de caché."""

import hashlib
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from madridFines.cache import Cache, CacheError, CacheURL

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class TestCache(unittest.TestCase):
    def setUp(self):
        self.cache = Cache.__new__(Cache)
        self.cache.app_name = "test_app"
        self.cache.obsolescence = 7
        self.cache.cache_dir = DATA_DIR / "test_app"
        self.cache.cache_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        for file in self.cache.cache_dir.iterdir():
            file.unlink()

    def test_set_and_load(self):
        self.cache.set("clave", "hola")
        self.assertTrue(self.cache.exists("clave"))
        self.assertEqual(self.cache.load("clave"), "hola")

    def test_load_missing(self):
        with self.assertRaises(CacheError):
            self.cache.load("no_existe")

    def test_how_old(self):
        self.cache.set("clave", "hola")
        age1 = self.cache.how_old("clave")
        time.sleep(0.05)
        age2 = self.cache.how_old("clave")
        self.assertGreater(age2, age1)

    def test_delete(self):
        self.cache.set("clave", "hola")
        self.cache.delete("clave")
        self.assertFalse(self.cache.exists("clave"))

    def test_clear(self):
        self.cache.set("a", "1")
        self.cache.set("b", "2")
        self.cache.clear()
        self.assertFalse(self.cache.exists("a"))
        self.assertFalse(self.cache.exists("b"))

    def test_is_obsolete(self):
        self.cache.set("viejo", "datos")
        path = self.cache._filepath("viejo")
        old_time = time.time() - (10 * 86400)
        os.utime(path, (old_time, old_time))
        self.assertTrue(self.cache._is_obsolete("viejo"))


class TestCacheURL(unittest.TestCase):
    TEST_URL = "https://ejemplo.com/datos.csv"
    TEST_CONTENT = "col1;col2\nval1;val2\n"

    def setUp(self):
        self.cache = CacheURL.__new__(CacheURL)
        self.cache.app_name = "test_url_app"
        self.cache.obsolescence = 7
        self.cache.cache_dir = DATA_DIR / "test_url_app"
        self.cache.cache_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        for file in self.cache.cache_dir.iterdir():
            file.unlink()

    def _url_hash(self, url):
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    @patch("madridFines.cache.requests.get")
    def test_get_downloads_and_caches(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = self.TEST_CONTENT
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = self.cache.get(self.TEST_URL)

        self.assertEqual(result, self.TEST_CONTENT)
        self.assertTrue(self.cache.exists(self.TEST_URL))

    @patch("madridFines.cache.requests.get")
    def test_get_uses_cache(self, mock_get):
        name = self._url_hash(self.TEST_URL)
        self.cache.cache_dir.joinpath(name).write_text(self.TEST_CONTENT, encoding="utf-8")
        result = self.cache.get(self.TEST_URL)
        self.assertEqual(result, self.TEST_CONTENT)
        mock_get.assert_not_called()

    @patch("madridFines.cache.requests.get")
    def test_get_raises_on_download_error(self, mock_get):
        import requests as req_module

        mock_get.side_effect = req_module.RequestException("fallo")

        with self.assertRaises(CacheError):
            self.cache.get(self.TEST_URL)

    def test_url_helpers(self):
        name = self._url_hash(self.TEST_URL)
        self.cache.cache_dir.joinpath(name).write_text(self.TEST_CONTENT, encoding="utf-8")
        self.assertTrue(self.cache.exists(self.TEST_URL))
        self.assertEqual(self.cache.load(self.TEST_URL), self.TEST_CONTENT)
        self.assertGreaterEqual(self.cache.how_old(self.TEST_URL), 0)
        self.cache.delete(self.TEST_URL)
        self.assertFalse(self.cache.exists(self.TEST_URL))


if __name__ == "__main__":
    unittest.main()

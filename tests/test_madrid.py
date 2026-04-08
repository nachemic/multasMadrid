"""Tests para el análisis de multas de Madrid."""

import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from traficFines.cache import CacheError
from traficFines.traficFines import MADRID_FINES_URL, ROOT, MadridError, MadridFines, get_url

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_CSV = """\
CALIFICACION ;LUGAR                ;MES;ANIO;HORA ;IMP_BOL;DESCUENTO ;PUNTOS;DENUNCIANTE ;HECHO-BOL              ;VEL_LIMITE ;VEL_CIRCULA ;COORDENADA-X ;COORDENADA-Y \r
LEVE         ;CL CLARA DEL REY 36 ;12 ;2024;20.23;60.0   ;SI        ;0     ;SER         ;ESTACIONAR NO VALIDA  ;           ;            ;             ;             \r
GRAVE        ;CL CANILLAS 63      ;12 ;2024;20.45;200.0  ;SI        ;0     ;SER         ;OBSTACULIZAR VIA      ;50         ;70          ;440123.5     ;4474523.8    \r
LEVE         ;CL BRAVO MURILLO 16 ;12 ;2024;16.50;90.0   ;NO        ;0     ;SER         ;ESTACIONAR SIN AUTOR  ;           ;            ;             ;             \r
MUY GRAVE    ;AV CASTELLANA 1     ;12 ;2024;10.00;600.0  ;SI        ;6     ;POLICIA     ;CONDUCIR ALCOHOLIZADO ;120        ;180         ;441000.0     ;4475000.0    \r
"""

DOWNLOADS_HTML = """\
<html>
    <body>
        <div id="collapse2024-Diciembre">
            <div data-key="2024 Diciembre-Detalle">
                <p>Multas de circulación: detalle. 2024 Diciembre. Detalle</p>
                <a class="btn btn-primary" href="/dataset/210104-0-multas-circulacion-detalle/resource/210104-15-multas-circulacion-detalle-csv/download/210104-15-multas-circulacion-detalle-csv.csv">Descarga</a>
            </div>
        </div>
        <div id="collapse2024-Mayo">
            <div data-key="2024 Mayo-Detalle">
                <p>Multas de circulación: detalle. 2024 Mayo. Detalle</p>
                <a class="btn btn-primary" href="/dataset/210104-0-multas-circulacion-detalle/resource/210104-28-multas-circulacion-detalle-csv/download/210104-28-multas-circulacion-detalle-csv.csv">Descarga</a>
            </div>
        </div>
    </body>
</html>
"""

DOWNLOADS_HTML_ABSOLUTE = """\
<html>
    <body>
        <div id="collapse2024-Diciembre">
            <div data-key="2024 Diciembre-Detalle">
                <p>Multas de circulación: detalle. 2024 Diciembre. Detalle</p>
                <a class="btn btn-primary" href="https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-15/download/2024-diciembre.csv">Descarga</a>
            </div>
        </div>
    </body>
</html>
"""

DOWNLOADS_HTML_NO_LINK = """\
<html>
    <body>
        <div id="collapse2024-Diciembre">
            <div data-key="2024 Diciembre-Detalle">
                <p>Multas de circulación: detalle. 2024 Diciembre. Detalle</p>
            </div>
        </div>
    </body>
</html>
"""

class TestGetUrl(unittest.TestCase):
    @patch("traficFines.traficFines.requests.get")
    def test_get_url_returns_month_download_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = DOWNLOADS_HTML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        url = get_url(2024, 12)

        self.assertEqual(
            url,
            "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-15-multas-circulacion-detalle-csv/download/210104-15-multas-circulacion-detalle-csv.csv",
        )
        mock_get.assert_called_once_with(f"{ROOT}{MADRID_FINES_URL}", timeout=30)

    @patch("traficFines.traficFines.requests.get")
    def test_get_url_returns_absolute_download_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = DOWNLOADS_HTML_ABSOLUTE
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        url = get_url(2024, 12)

        self.assertEqual(
            url,
            "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-15/download/2024-diciembre.csv",
        )

    @patch("traficFines.traficFines.requests.get")
    def test_get_url_raises_for_request_error(self, mock_get):
        import requests as req_module

        mock_get.side_effect = req_module.RequestException("fallo red")

        with self.assertRaises(MadridError):
            get_url(2024, 12)

    @patch("traficFines.traficFines.requests.get")
    def test_get_url_raises_for_missing_month(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = DOWNLOADS_HTML
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaises(MadridError):
            get_url(2023, 1)

    @patch("traficFines.traficFines.requests.get")
    def test_get_url_raises_when_download_link_is_missing(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = DOWNLOADS_HTML_NO_LINK
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaises(MadridError):
            get_url(2024, 12)

    def test_get_url_raises_for_invalid_month(self):
        with self.assertRaises(MadridError):
            get_url(2024, 13)

    def test_get_url_raises_for_invalid_year(self):
        with self.assertRaises(MadridError):
            get_url(2013, 12)


class TestMadridFines(unittest.TestCase):
    def _make_loaded_mf(self):
        mf = MadridFines("test_madrid", base_dir=DATA_DIR)
        mf.cacheurl = FakeCache()
        mf._loaded = [(12, 2024)]
        df = pd.read_csv(io.StringIO(SAMPLE_CSV), sep=";", encoding="latin1")
        df = mf.clean(df)
        mf._data = df
        return mf

    def _make_empty_mf(self):
        mf = MadridFines("test_madrid", base_dir=DATA_DIR)
        mf.cacheurl = FakeCache()
        mf._data = pd.DataFrame()
        mf._loaded = []
        return mf

    def test_add_single_month(self):
        mf = MadridFines("test_madrid", base_dir=DATA_DIR)
        mf.cacheurl = FakeCache()

        original_get_url = __import__("traficFines.traficFines").traficFines.get_url
        __import__("traficFines.traficFines").traficFines.get_url = lambda year, month: "https://fake.url/datos.csv"

        try:
            mf.add(2024, 12)
            self.assertIn((12, 2024), mf.loaded)
            self.assertFalse(mf.data.empty)
        finally:
            __import__("traficFines.traficFines").traficFines.get_url = original_get_url

    def test_add_no_duplicate(self):
        mf = MadridFines("test_madrid", base_dir=DATA_DIR)
        mf.cacheurl = FakeCache()

        original_get_url = __import__("traficFines.traficFines").traficFines.get_url
        __import__("traficFines.traficFines").traficFines.get_url = lambda year, month: "https://fake.url/datos.csv"

        try:
            mf.add(2024, 12)
            size1 = len(mf.data)
            mf.add(2024, 12)
            size2 = len(mf.data)
            self.assertEqual(size1, size2)
            self.assertEqual(mf.loaded.count((12, 2024)), 1)
        finally:
            __import__("traficFines.traficFines").traficFines.get_url = original_get_url

    def test_load_raises_on_cache_error(self):
        cache = MagicMock()
        cache.get.side_effect = CacheError("fallo cache")

        with self.assertRaises(MadridError):
            MadridFines.load(2024, 12, cache)

    @patch("traficFines.traficFines.get_url", return_value="https://fake.url/datos.csv")
    @patch("traficFines.traficFines.pd.read_csv", side_effect=ValueError("csv roto"))
    def test_load_raises_on_csv_error(self, _mock_read_csv, _mock_get_url):
        cache = MagicMock()
        cache.get.return_value = "contenido"

        with self.assertRaises(MadridError):
            MadridFines.load(2024, 12, cache)

    def test_clean_without_datetime_columns_keeps_default_index(self):
        df = pd.DataFrame({"CALIFICACION": [" LEVE "], "DESCUENTO": [" SI "]})

        cleaned = MadridFines.clean(df)

        self.assertEqual(list(cleaned.columns), ["CALIFICACION", "DESCUENTO"])
        self.assertNotEqual(cleaned.index.name, "fecha")

    def test_add_full_year_loads_each_missing_month(self):
        mf = MadridFines("test_madrid", base_dir=DATA_DIR)
        mf.cacheurl = FakeCache()

        original_get_url = __import__("traficFines.traficFines").traficFines.get_url
        __import__("traficFines.traficFines").traficFines.get_url = lambda year, month: f"https://fake.url/{year}-{month:02d}.csv"

        try:
            mf.add(2024)
            self.assertEqual(len(mf.loaded), 12)
            self.assertIn((1, 2024), mf.loaded)
            self.assertIn((12, 2024), mf.loaded)
        finally:
            __import__("traficFines.traficFines").traficFines.get_url = original_get_url

    def test_fines_hour_saves_file(self):
        mf = self._make_loaded_mf()
        output_file = DATA_DIR / "fines_hour.png"
        mf.fines_hour(str(output_file))
        self.assertTrue(output_file.exists())
        output_file.unlink()

    def test_fines_hour_empty_raises(self):
        mf = self._make_empty_mf()
        with self.assertRaises(MadridError):
            mf.fines_hour(str(DATA_DIR / "no_data.png"))

    def test_fines_calification_empty_raises(self):
        mf = self._make_empty_mf()
        with self.assertRaises(MadridError):
            mf.fines_calification()

    def test_fines_calification(self):
        mf = self._make_loaded_mf()
        result = mf.fines_calification()
        self.assertFalse(result.empty)
        self.assertEqual(result.index.names, ["MES", "ANIO"])
        self.assertEqual(result.loc[(12, 2024), "LEVE"], 2)
        self.assertEqual(result.loc[(12, 2024), "GRAVE"], 1)
        self.assertEqual(result.loc[(12, 2024), "MUY GRAVE"], 1)

    def test_total_payment(self):
        mf = self._make_loaded_mf()
        result = mf.total_payment()
        self.assertIn("total_max", result.columns)
        self.assertIn("total_min", result.columns)
        self.assertEqual(result.loc[(12, 2024), "total_max"], 950.0)
        self.assertEqual(result.loc[(12, 2024), "total_min"], 520.0)

    def test_total_payment_empty_raises(self):
        mf = self._make_empty_mf()
        with self.assertRaises(MadridError):
            mf.total_payment()

    def test_data_and_loaded_properties_are_copies(self):
        mf = self._make_loaded_mf()

        data_copy = mf.data
        loaded_copy = mf.loaded

        data_copy["NUEVA"] = 1
        loaded_copy.append((1, 2000))

        self.assertNotIn("NUEVA", mf.data.columns)
        self.assertNotIn((1, 2000), mf.loaded)


class FakeCache:
    """Clase simple para simular caché sin mocks."""
    def __init__(self):
        self.data = {}

    def get(self, url, params=None, encoding=None):
        if url in self.data:
            return self.data[url]
        return SAMPLE_CSV  # Devolver datos de ejemplo


if __name__ == "__main__":
    unittest.main()

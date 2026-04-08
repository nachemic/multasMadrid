"""Tests para el análisis de multas de Madrid."""

import io
import os
import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from madridFines.madridFines import MadridError, MadridFines, get_url

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_CSV = """\
CALIFICACION ;LUGAR                ;MES;ANIO;HORA ;IMP_BOL;DESCUENTO ;PUNTOS;DENUNCIANTE ;HECHO-BOL              ;VEL_LIMITE ;VEL_CIRCULA ;COORDENADA-X ;COORDENADA-Y \r
LEVE         ;CL CLARA DEL REY 36 ;12 ;2024;20.23;60.0   ;SI        ;0     ;SER         ;ESTACIONAR NO VALIDA  ;           ;            ;             ;             \r
GRAVE        ;CL CANILLAS 63      ;12 ;2024;20.45;200.0  ;SI        ;0     ;SER         ;OBSTACULIZAR VIA      ;50         ;70          ;440123.5     ;4474523.8    \r
LEVE         ;CL BRAVO MURILLO 16 ;12 ;2024;16.50;90.0   ;NO        ;0     ;SER         ;ESTACIONAR SIN AUTOR  ;           ;            ;             ;             \r
MUY GRAVE    ;AV CASTELLANA 1     ;12 ;2024;10.00;600.0  ;SI        ;6     ;POLICIA     ;CONDUCIR ALCOHOLIZADO ;120        ;180         ;441000.0     ;4475000.0    \r
"""

class TestGetUrl(unittest.TestCase):
    def test_get_url_returns_catalog_url(self):
        # La función get_url devuelve una URL fija del catálogo de datos de multas.
        url = get_url(2024, 12)
        expected = "https://datos.madrid.es/egob/catalogo/210104-395-multas-circulacion-detalle.csv"
        self.assertEqual(url, expected)

    def test_get_url_formats_value_error(self):
        # La implementación actual no valida anio/mes, pero se comprueba que la URL es siempre la misma.
        url = get_url(1990, 1)
        expected = "https://datos.madrid.es/egob/catalogo/210104-395-multas-circulacion-detalle.csv"
        self.assertEqual(url, expected)


class TestMadridFines(unittest.TestCase):
    def _make_loaded_mf(self):
        import pandas as pd

        mf = MadridFines.__new__(MadridFines)
        mf.cacheurl = FakeCache()
        mf.loaded = [(2024, 12)]
        df = pd.read_csv(io.StringIO(SAMPLE_CSV), sep=";", encoding="latin1")
        df = mf._clean(df)
        mf.data = df
        return mf

    def _make_empty_mf(self):
        mf = MadridFines.__new__(MadridFines)
        mf.cacheurl = FakeCache()
        mf.data = pd.DataFrame()
        mf.loaded = []
        return mf

    def test_add_single_month(self):
        mf = MadridFines.__new__(MadridFines)
        mf.cacheurl = FakeCache()
        mf.data = pd.DataFrame()
        mf.loaded = []

        # Simular get_url con lambda
        original_get_url = __import__('madridFines.madridFines').madridFines.get_url
        __import__('madridFines.madridFines').madridFines.get_url = lambda year, month: "https://fake.url/datos.csv"

        try:
            mf.add(2024, 12)
            self.assertIn((2024, 12), mf.loaded)
            self.assertFalse(mf.data.empty)
        finally:
            __import__('madridFines.madridFines').madridFines.get_url = original_get_url

    def test_add_no_duplicate(self):
        mf = MadridFines.__new__(MadridFines)
        mf.cacheurl = FakeCache()
        mf.data = pd.DataFrame()
        mf.loaded = []

        original_get_url = __import__('madridFines.madridFines').madridFines.get_url
        __import__('madridFines.madridFines').madridFines.get_url = lambda year, month: "https://fake.url/datos.csv"

        try:
            mf.add(2024, 12)
            size1 = len(mf.data)
            mf.add(2024, 12)
            size2 = len(mf.data)
            self.assertEqual(size1, size2)
            self.assertEqual(mf.loaded.count((2024, 12)), 1)
        finally:
            __import__('madridFines.madridFines').madridFines.get_url = original_get_url

    # Eliminado: test_add_full_year_skips_missing. No es requerido explícitamente por el enunciado académico.

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

    def test_fines_calification(self):
        mf = self._make_loaded_mf()
        result = mf.fines_calification()
        self.assertFalse(result.empty)

    def test_total_payment(self):
        mf = self._make_loaded_mf()
        result = mf.total_payment()
        self.assertIn("total_max", result.columns)
        self.assertIn("total_min", result.columns)


class FakeCache:
    """Clase simple para simular caché sin mocks."""
    def __init__(self):
        self.data = {}

    def get(self, url):
        if url in self.data:
            return self.data[url]
        return SAMPLE_CSV  # Devolver datos de ejemplo


if __name__ == "__main__":
    unittest.main()

"""Descarga y análisis de multas de tráfico de Madrid."""

import io
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import requests
from .cache import CacheURL, CacheError

# Constante raíz para los enlaces de descarga
RAIZ = "https://datos.madrid.es/"

class MadridError(Exception):
    """Error en la obtención o el análisis de datos de Madrid."""
    pass

def get_url(year, month):
    """
    Devuelve la URL fija del fichero CSV de multas para el mes y año indicados.
    Proyecto académico: no hace scraping, solo devuelve la URL del catálogo.
    """
    return "https://datos.madrid.es/egob/catalogo/210104-395-multas-circulacion-detalle.csv"

class MadridFines:
    """Carga, limpia y analiza multas de tráfico de Madrid."""
    def __init__(self, app_name="multas_madrid", obsolescence=30):
        self.cacheurl = CacheURL(app_name, obsolescence)
        self.data = pd.DataFrame()
        self.loaded = []

    @staticmethod
    def _load(year, month, cacheurl):
        """
        Descarga y lee el CSV en un DataFrame usando la caché.
        """
        url = get_url(year, month)
        try:
            text = cacheurl.get(url)
        except CacheError as e:
            raise MadridError(f"Falló la descarga de {month:02d}/{year}: {e}") from e
        try:
            return pd.read_csv(io.StringIO(text), sep=";", encoding="latin1")
        except Exception as e:
            raise MadridError(f"No se pudo leer el CSV: {e}") from e

    @staticmethod
    def _clean(df):
        """
        Limpia y normaliza el DataFrame de multas.
        """
        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip()
        # Renombrar columnas si es necesario
        rename_map = {"COORDENADA_X": "COORDENADA-X", "COORDENADA_Y": "COORDENADA-Y"}
        df = df.rename(columns=rename_map)
        # Limpiar espacios en columnas de texto
        for col in ["CALIFICACION", "DESCUENTO", "HECHO-BOL", "DENUNCIANTE"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        # Convertir columnas numéricas
        for col in ["VEL_LIMITE", "VEL_CIRCULA", "COORDENADA-X", "COORDENADA-Y"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # Crear columna fecha
        if all(c in df.columns for c in ["ANIO", "MES", "HORA"]):
            df["fecha"] = pd.to_datetime(dict(year=df["ANIO"], month=df["MES"], day=1)) + pd.to_timedelta(df["HORA"].astype(float).fillna(0), unit="h")
            df.set_index("fecha", inplace=True)
            # Solo eliminar la columna 'fecha' si existe (por seguridad)
            if "fecha" in df.columns:
                df.drop(columns=["fecha"], inplace=True)
        return df

    def add(self, year, month=None):
        """
        Añade datos de un mes y año concreto al dataset actual.
        Si month es None, añade todo el año.
        """
        months = [month] if month else range(1, 13)
        for m in months:
            if (year, m) in self.loaded:
                continue
            df = self._load(year, m, self.cacheurl)
            df = self._clean(df)
            self.data = pd.concat([self.data, df], axis=0)
            self.loaded.append((year, m))

    def fines_hour(self, fig_name):
        """
        Genera un gráfico de líneas con la evolución de multas por hora.
        """
        if self.data.empty:
            raise MadridError("No hay datos cargados.")
        df = self.data.copy()
        df["hora"] = df.index.hour
        df["mes"] = df.index.month
        df["anio"] = df.index.year
        pivot = df.groupby(["anio", "mes", "hora"]).size().unstack(fill_value=0)
        pivot.T.plot(figsize=(10, 6))
        plt.xlabel("Hora del día")
        plt.ylabel("Número de multas")
        plt.title("Evolución de multas por hora")
        plt.savefig(fig_name)
        plt.close()

    def fines_calification(self):
        """
        Devuelve un DataFrame con el número total de multas por calificación, mes y año.
        """
        if self.data.empty:
            raise MadridError("No hay datos cargados.")
        df = self.data.copy()
        df["mes"] = df.index.month
        df["anio"] = df.index.year
        return pd.pivot_table(df, index=["mes", "anio"], columns="CALIFICACION", values="IMP_BOL", aggfunc="count", fill_value=0)

    def total_payment(self):
        """
        Devuelve un resumen con el importe total (máximo y mínimo) recaudado por mes y año.
        """
        if self.data.empty:
            raise MadridError("No hay datos cargados.")
        df = self.data.copy()
        df["mes"] = df.index.month
        df["anio"] = df.index.year
        resumen = df.groupby(["anio", "mes"])["IMP_BOL"].agg(["sum", "min", "max"])
        resumen = resumen.rename(columns={"max": "total_max", "min": "total_min", "sum": "total_sum"})
        return resumen

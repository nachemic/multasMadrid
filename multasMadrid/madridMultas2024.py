"""Descarga y analiza multas de tráfico de Madrid."""

import io
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests

from .cache import CacheURL, CacheError

# Este módulo maneja la descarga, limpieza y análisis de los datos
# de multas del Ayuntamiento de Madrid.

class MadridError(Exception):
    """Error en la obtención o el análisis de datos de Madrid."""
    pass



def get_url(year, month):
    """
    Devuelve la URL del catálogo de datos de multas.

    Nota: esta implementación no busca un CSV específico por mes/anio.
    Estamos usando una URL fija que redirige al archivo de multas.
    Esto simplifica el proyecto y evita usar scraping.
    """
    # La función no utiliza year ni month en esta versión simplificada.
    return "https://datos.madrid.es/egob/catalogo/210104-395-multas-circulacion-detalle.csv"


class MadridFines:
    # Esta clase encapsula toda la lógica de descarga, limpieza y análisis.

    """Carga y analiza multas de tráfico de Madrid."""

    def __init__(self, app_name="multas_madrid", obsolescence=30):
        """
        Crea un objeto para analizar multas.

        Se prepara una caché, un DataFrame vacío para los datos y
        una lista `loaded` para recordar qué meses ya se cargaron.
        """
        self.cacheurl = CacheURL(app_name, obsolescence)
        self.cache = self.cacheurl
        self.data = pd.DataFrame()  # Aquí guardaremos todas las filas de multas.
        self.loaded = []  # Lista de tuplas (anio, mes) ya cargadas.

    def _load(self, year, month):
        """
        Descarga y lee el CSV en un DataFrame.

        Variables:
        year (int): Anio.
        month (int): Mes.

        Output:
        pd.DataFrame: DataFrame con los datos.

        Ejemplos:
        >>> df = mf._load(2024, 12)
        """
        url = get_url(year, month)
        # Descargamos el contenido usando la caché.
        # Si ya existe y no está caducado, se lee desde disco.
        try:
            text = self.cache.get(url)
        except CacheError as e:
            raise MadridError(f"Falló la descarga de {month:02d}/{year}: {e}") from e

        # Leemos el CSV como texto usando pandas.
        try:
            return pd.read_csv(io.StringIO(text), sep=";", encoding="latin1")
        except Exception as e:
            raise MadridError(f"No se pudo leer el CSV: {e}") from e

    def _clean(self, df):
        """
        Limpia los datos del DataFrame para analizarlos.

        Variables:
        df (pd.DataFrame): DataFrame a limpiar.

        Output:
        None

        Ejemplos:
        >>> mf._clean(df)
        """
        # Paso 1: limpiar nombres de columnas para que no tengan espacios extra.
        df = self._normalize_column_names(df)

        # Paso 2: renombrar columnas concretas si vienen con nombres distintos.
        df = self._rename_specific_columns(df)

        # Paso 3: quitar espacios en blanco al principio/fin de textos.
        df = self._clean_text_columns(df)

        # Paso 4: convertir columnas que deben ser números.
        df = self._convert_numeric_columns(df)

        # Paso 5: crear la columna fecha a partir de ANIO, MES y HORA.
        df = self._create_date_column(df)

    def _normalize_column_names(self, df):
        """Normaliza los nombres de las columnas eliminando espacios."""
        df.rename(columns=lambda c: c.strip(), inplace=True)
        return df

    def _rename_specific_columns(self, df):
        """Renombra columnas específicas si existen."""
        if "COORDENADA_X" in df.columns:
            df.rename(columns={"COORDENADA_X": "COORDENADA-X"}, inplace=True)
        if "COORDENADA_Y" in df.columns:
            df.rename(columns={"COORDENADA_Y": "COORDENADA-Y"}, inplace=True)
        return df

    def _clean_text_columns(self, df):
        """Limpia las columnas de texto."""
        text_cols = ["CALIFICACION", "DESCUENTO", "HECHO-BOL", "DENUNCIANTE", "LUGAR"]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        return df

    def _convert_numeric_columns(self, df):
        """Convierte columnas a numérico."""
        numeric_cols = ["VEL_LIMITE", "VEL_CIRCULA", "COORDENADA-X", "COORDENADA-Y"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def _create_date_column(self, df):
        """Crea la columna de fecha."""
        if all(c in df.columns for c in ["ANIO", "MES", "HORA"]):
            # La hora viene en formato decimal: 20.23 == 20:23.
            hour = pd.to_numeric(df["HORA"], errors="coerce").fillna(0)
            hour_int = hour.astype(int)
            minute = ((hour - hour_int) * 100).round().astype(int)

            # Crear el índice de fechas usando día fijo = 1.
            df["fecha"] = pd.to_datetime(
                {
                    "year": df["ANIO"],
                    "month": df["MES"],
                    "day": 1,
                    "hour": hour_int,
                    "minute": minute,
                },
                errors="coerce",
            )

            # Convertimos la columna fecha en el índice del DataFrame.
            df.set_index("fecha", inplace=True)
        return df

    def add(self, year, month=None):
        """
        Carga un mes o todo un anio de datos.

        Variables:
        year (int): Anio.
        month (int or None): Mes, o None para todo el anio.

        Output:
        None

        Ejemplos:
        >>> mf.add(2024, 12)
        Cargando datos de 12/2024
        """
        if month is None:
            # Si no se pasa mes, intentamos cargar los 12 meses del anio.
            for m in range(1, 13):
                try:
                    self.add(year, m)
                except MadridError:
                    # Si algún mes no está disponible, lo saltamos.
                    continue
            return

        # Evitamos cargar el mismo mes dos veces.
        if (year, month) in self.loaded:
            return

        df = self._load(year, month)
        self._clean(df)

        # La primera carga inicializa `self.data`; las siguientes concatena.
        if self.data.empty:
            self.data = df
        else:
            self.data = pd.concat([self.data, df])

        self.loaded.append((year, month))

    def fines_hour(self, filename):
        """
        Guarda un gráfico de multas por hora del día.

        Variables:
        filename (str): Nombre del archivo para guardar el gráfico.

        Output:
        None

        Ejemplos:
        >>> mf.fines_hour("grafico.png")
        """
        if self.data.empty:
            raise MadridError("No hay datos cargados. Usa add() antes.")

        # Copiamos los datos para no modificar el DataFrame original.
        df = self.data.copy()
        # Extraemos la hora del índice de fecha.
        df["hour"] = df.index.hour
        fig, ax = plt.subplots(figsize=(10, 5))

        for year, month in sorted(self.loaded):
            month_data = df[(df["MES"] == month) & (df["ANIO"] == year)]
            if month_data.empty:
                continue
            # Contamos las multas por hora y rellenamos horas sin multas.
            count = month_data.groupby("hour").size().reindex(range(24), fill_value=0)
            ax.plot(count.index, count.values, marker="o", label=f"{month:02d}/{year}")

        ax.set_title("Multas por hora del día")
        ax.set_xlabel("Hora")
        ax.set_ylabel("Número de multas")
        ax.legend()
        ax.grid(True)
        fig.tight_layout()
        fig.savefig(filename, dpi=150)
        plt.close(fig)

    def fines_calification(self):
        """
        Devuelve un resumen de multas por calificación.

        Variables:
        None

        Output:
        pd.DataFrame: Resumen por mes y calificación.

        Ejemplos:
        >>> df = mf.fines_calification()
        >>> print(df.head())
        CALIFICACION   GRAVE    LEVE  MUY GRAVE
        MES ANIO
        12  2024       1000   2000        50
        """
        if self.data.empty:
            raise MadridError("No hay datos cargados. Usa add() antes.")

        # Resetear índice para agrupar por columnas normales.
        df = self.data.reset_index()
        grouped = df.groupby(["MES", "ANIO", "CALIFICACION"]).size().reset_index(name="count")
        pivot = grouped.pivot_table(
            index=["MES", "ANIO"],
            columns="CALIFICACION",
            values="count",
            fill_value=0,
            aggfunc="sum",
        )
        pivot.columns.name = "CALIFICACION"
        return pivot

    def total_payment(self):
        """
        Devuelve un resumen de los importes de las multas.

        Variables:
        None

        Output:
        pd.DataFrame: Resumen de importes por mes.

        Ejemplos:
        >>> df = mf.total_payment()
        >>> print(df.head())
        total_max  total_min  max_multa  min_multa
        MES ANIO
        12  2024   100000.0   50000.0     600.0      30.0
        """
        if self.data.empty:
            raise MadridError("No hay datos cargados. Usa add() antes.")

        # Copia del DataFrame para no modificar el original.
        df = self.data.reset_index().copy()
        df["importe_max"] = df.get("IMP_BOL", 0)
        df["importe_min"] = df.apply(
            lambda row: row["IMP_BOL"] * 0.5 if str(row.get("DESCUENTO", "")).upper() == "SI" else row["IMP_BOL"],
            axis=1,
        )

        result = (
            df.groupby(["MES", "ANIO"])
            .agg(
                total_max=("importe_max", "sum"),
                total_min=("importe_min", "sum"),
                max_multa=("IMP_BOL", "max"),
                min_multa=("IMP_BOL", "min"),
            )
            .reset_index()
            .set_index(["MES", "ANIO"])
        )
        return result

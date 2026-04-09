import io
import re

import matplotlib.pyplot as plt
import pandas as pd
import requests

from .cache import CacheURL, CacheError

ROOT = "https://datos.madrid.es/"
MADRID_FINES_URL = "dataset/210104-0-multas-circulacion-detalle/downloads"

MONTH_NAMES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


class MadridError(Exception):
    """Error en la obtención o el análisis de datos de Madrid."""
    pass


def get_url(year, month):
    """Obtiene la URL del CSV mensual de multas mediante scraping del portal de Madrid.
    
    :param year: Año de los datos.
    :type year: int
    :param month: Mes de los datos (1-12).
    :type month: int
    :returns: URL del fichero CSV para descargar.
    :rtype: str
    :raises MadridError: Si el año es inválido, el mes no está entre 1-12, o no hay datos.
    
    Example:
        >>> url = get_url(2024, 12)
        >>> 'multas-circulacion-detalle' in url
        True
    """
    if not isinstance(year, int) or year < 2014:
        raise MadridError(f"Año inválido: {year}")
    if month not in MONTH_NAMES:
        raise MadridError(f"Mes inválido: {month}")

    try:
        response = requests.get(f"{ROOT}{MADRID_FINES_URL}", timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise MadridError(f"No se pudo acceder al catálogo de multas: {e}") from e

    html = response.text
    section_id = f"collapse{year}-{MONTH_NAMES[month]}"
    if section_id not in html:
        raise MadridError(f"No hay datos disponibles para {month:02d}/{year}")

    resource_label = f"Multas de circulación: detalle. {year} {MONTH_NAMES[month]}. Detalle"
    match = re.search(
        re.escape(resource_label) + r'.*?href="([^"]+/download/[^"]+\.csv)"',
        html,
        re.S,
    )
    if match is None:
        raise MadridError(f"No se pudo localizar la descarga para {month:02d}/{year}")

    href = match.group(1)
    if href.startswith("http"):
        return href
    return f"{ROOT.rstrip('/')}{href}"


class MadridFines:

    def __init__(self, app_name="multas_madrid", obsolescence=30, base_dir=None):
        self.cacheurl = CacheURL(app_name, obsolescence, base_dir=base_dir)
        self._data = pd.DataFrame()
        self._loaded = []

    @property
    def data(self):
        return self._data.copy()

    @property
    def loaded(self):
        return list(self._loaded)

    @staticmethod
    def load(year, month, cacheurl):
        """Descarga y lee el CSV mensual en un DataFrame usando la caché.
        
        :param year: Año de los datos.
        :type year: int
        :param month: Mes de los datos (1-12).
        :type month: int
        :param cacheurl: Objeto de caché para gestionar la descarga.
        :type cacheurl: CacheURL
        :returns: DataFrame con los datos del CSV.
        :rtype: pd.DataFrame
        :raises MadridError: Si falla la descarga o la lectura del CSV.
        
        Example:
            >>> df = MadridFines.load(2024, 12, cacheurl)
            >>> len(df) > 0
            True
        """
        url = get_url(year, month)
        try:
            text = cacheurl.get(url, encoding="cp1252")
        except CacheError as e:
            raise MadridError(f"Falló la descarga de {month:02d}/{year}: {e}") from e
        try:
            return pd.read_csv(io.StringIO(text), sep=";", encoding="cp1252")
        except Exception as e:
            raise MadridError(f"No se pudo leer el CSV: {e}") from e

    @staticmethod
    def clean(df):
        """Limpia y normaliza el DataFrame de multas.
        
        Realiza las transformaciones necesarias:
        - Elimina espacios en blanco de nombres de columnas y valores de texto
        - Convierte columnas numéricas (velocidad, coordenadas) a números
        - Crea una columna de fecha a partir de ANIO, MES y HORA
        - Establece la fecha como índice del DataFrame
        
        :param df: DataFrame sin procesar.
        :type df: pd.DataFrame
        :returns: DataFrame limpio y normalizado.
        :rtype: pd.DataFrame
        
        Example:
            >>> df_limpio = MadridFines.clean(df_raw)
            >>> df_limpio.index.name
            'fecha'
        """
        df.columns = df.columns.str.strip()
        rename_map = {"COORDENADA_X": "COORDENADA-X", "COORDENADA_Y": "COORDENADA-Y"}
        df = df.rename(columns=rename_map)

        for col in ["CALIFICACION", "DESCUENTO", "HECHO-BOL", "DENUNCIANTE"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        for col in ["VEL_LIMITE", "VEL_CIRCULA", "COORDENADA-X", "COORDENADA-Y"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if all(c in df.columns for c in ["ANIO", "MES", "HORA"]):
            hora_decimal = pd.to_numeric(df["HORA"], errors="coerce").fillna(0)
            hora_int = hora_decimal.astype(int)
            minuto_int = ((hora_decimal - hora_int) * 100).round().astype(int)
            df["fecha"] = pd.to_datetime(
                {
                    "year": df["ANIO"],
                    "month": df["MES"],
                    "day": 1,
                    "hour": hora_int,
                    "minute": minuto_int,
                },
                errors="coerce",
            )
            df.set_index("fecha", inplace=True)
        return df

    _load = load
    _clean = clean

    def add(self, year, month=None):
        """Añade datos de multas al dataset actual.
        
        Si month es None, descarga todos los meses del año. Si el mes ya está
        cargado, no hace nada (evita duplicados).
        
        :param year: Año de los datos.
        :type year: int
        :param month: Mes específico (1-12). Si es None, descarga todo el año.
        :type month: int, optional
        :raises MadridError: Si falla la descarga o el procesamiento de datos.
        
        Example:
            >>> multas = MadridFines()
            >>> multas.add(2024, 12)
            >>> (12, 2024) in multas.loaded
            True
        """
        months = [month] if month else range(1, 13)
        for m in months:
            if (m, year) in self._loaded:
                continue
            df = self.load(year, m, self.cacheurl)
            df = self.clean(df)
            self._data = pd.concat([self._data, df], axis=0)
            self._loaded.append((m, year))

    def fines_hour(self, fig_name):
        """Genera un gráfico de líneas con la evolución de multas por hora.
        
        Muestra una línea para cada mes cargado, indicando el número de multas
        en cada hora del día (0-23).
        
        :param fig_name: Nombre del fichero donde guardar el gráfico (ej. 'multas.png').
        :type fig_name: str
        :raises MadridError: Si no hay datos cargados.
        
        Example:
            >>> multas = MadridFines()
            >>> multas.add(2024, 12)
            >>> multas.fines_hour('evolution.png')
        """
        if self._data.empty:
            raise MadridError("No hay datos cargados.")
        df = self._data.copy()
        df["HORA_DIA"] = df.index.hour
        df["MES"] = df.index.month
        df["ANIO"] = df.index.year
        pivot = df.groupby(["ANIO", "MES", "HORA_DIA"]).size().unstack(fill_value=0).sort_index()
        pivot.index = [f"{year}-{month:02d}" for year, month in pivot.index]
        pivot.T.plot(figsize=(10, 6))
        plt.xlabel("Hora del día")
        plt.ylabel("Número de multas")
        plt.title("Evolución de multas por hora")
        plt.tight_layout()
        plt.savefig(fig_name)
        plt.close()

    def fines_calification(self):
        """Devuelve el número total de multas por calificación, mes y año.
        
        :returns: DataFrame con filas (MES, ANIO) y columnas (GRAVE, LEVE, MUY GRAVE).
        :rtype: pd.DataFrame
        :raises MadridError: Si no hay datos cargados.
        
        Example:
            >>> multas = MadridFines()
            >>> multas.add(2024, 12)
            >>> df_cal = multas.fines_calification()
            >>> 'GRAVE' in df_cal.columns
            True
        """
        if self._data.empty:
            raise MadridError("No hay datos cargados.")
        df = self._data.copy()
        df["MES"] = df.index.month
        df["ANIO"] = df.index.year
        return df.groupby(["MES", "ANIO", "CALIFICACION"]).size().unstack(fill_value=0).sort_index()

    def total_payment(self):
        """Devuelve el importe total mínimo y máximo recaudable por mes y año.
        
        El importe mínimo aplica el 50% de descuento por pronto pago; el máximo
        es sin descuento.
        
        :returns: DataFrame con filas (MES, ANIO) y columnas (total_min, total_max).
        :rtype: pd.DataFrame
        :raises MadridError: Si no hay datos cargados.
        
        Example:
            >>> multas = MadridFines()
            >>> multas.add(2024, 12)
            >>> df_pago = multas.total_payment()
            >>> 'total_min' in df_pago.columns
            True
        """
        if self._data.empty:
            raise MadridError("No hay datos cargados.")
        df = self._data.copy()
        df["MES"] = df.index.month
        df["ANIO"] = df.index.year
        df["IMPORTE_MINIMO"] = df["IMP_BOL"]
        descuento_mask = df["DESCUENTO"].astype(str).str.upper().eq("SI")
        df.loc[descuento_mask, "IMPORTE_MINIMO"] = df.loc[descuento_mask, "IMP_BOL"] / 2
        df["IMPORTE_MAXIMO"] = df["IMP_BOL"]
        return (
            df.groupby(["MES", "ANIO"])[["IMPORTE_MINIMO", "IMPORTE_MAXIMO"]]
            .sum()
            .rename(columns={
                "IMPORTE_MINIMO": "total_min",
                "IMPORTE_MAXIMO": "total_max",
            })
            .sort_index()
        )

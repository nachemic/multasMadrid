"""Paquete multasMadrid para análisis de multas de Madrid."""

from .cache import Cache, CacheError, CacheURL
from .madridMultas2024 import MadridError, MadridFines, get_url

__all__ = [
    "Cache",
    "CacheError",
    "CacheURL",
    "MadridError",
    "MadridFines",
    "get_url",
]

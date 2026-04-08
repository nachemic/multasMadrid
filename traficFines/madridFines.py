"""Alias formal del modulo madridFines descrito en el enunciado."""

from .traficFines import MADRID_FINES_URL, ROOT, MadridError, MadridFines, RAIZ, get_url

__all__ = [
    "MADRID_FINES_URL",
    "MadridError",
    "MadridFines",
    "RAIZ",
    "ROOT",
    "get_url",
]
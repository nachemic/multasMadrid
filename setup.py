from pathlib import Path
from setuptools import setup, find_packages

README = Path(__file__).parent / "README.md"

setup(
    name="traficFines",
    version="1.0.0",
    author="Ignacio Martínez Godino",
    description="Trabajo final de Programacion Avanzada en Python para analizar multas de trafico de Madrid",
    long_description=README.read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests",
        "pandas",
        "matplotlib",
        "numpy",
    ],
    python_requires=">=3.10",
)
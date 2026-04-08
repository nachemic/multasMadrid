"""
Configuración del paquete multasMadrid para su distribución.
"""

from setuptools import find_packages, setup

setup(
    name="multasMadrid",
    version="1.0.0",
    author="Ignacio Martínez Godino",
    author_email="nachemic@gmail.com",
    description="Análisis de multas de tráfico del Ayuntamiento de Madrid",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.28",
        "pandas>=1.5",
        "matplotlib>=3.5",
        "numpy>=1.23",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
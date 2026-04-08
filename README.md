# multasMadrid

Este proyecto contiene un ejemplo sencillo para trabajar con datos de multas de tráfico de Madrid.

## Estructura del proyecto

- `multasMadrid/`: código Python del paquete.
- `tests/`: pruebas unitarias.
- `notebooks/`: notebooks con ejemplos y análisis.
- `enunciado/`: enunciado y gráficos en PNG.

## Instalación básica

1. Abre una terminal en esta carpeta.
2. Instala las dependencias con:

```bash
pip install requests pandas matplotlib numpy
```

## Uso rápido

```python
from multasMadrid import MadridFines, get_url

mf = MadridFines(app_name="multas_madrid", obsolescence=30)
mf.add(2024, 12)
print(mf.loaded)
print(mf.data.head())
mf.fines_hour("evolucion_multas.png")
print(mf.fines_calification())
print(mf.total_payment())
```

## Módulos principales

- `multasMadrid/cache.py`: clases `Cache` y `CacheURL` para guardar datos en disco.
- `multasMadrid/madridMultas2024.py`: clase `MadridFines` y función `get_url` para bajar, limpiar y analizar datos.

## Pruebas

Ejecuta las pruebas desde la raíz del proyecto:

```bash
python -m unittest discover tests/
```

## Notebooks

Los notebooks están en la carpeta `notebooks/`.

## Nota

El enunciado y las imágenes de ejemplo están en la carpeta `enunciado/`.

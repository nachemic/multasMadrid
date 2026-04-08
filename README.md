# traficFines

Proyecto académico de Programación Avanzada en Python para analizar multas de tráfico del Ayuntamiento de Madrid.

## Contenido de la entrega

- Paquete Python `traficFines/` con los módulos `cache.py` y `madridFines.py`.
- Módulo de compatibilidad `traficFines.py` para no romper imports anteriores.
- Notebook de la etapa 1: `notebooks/analisis.ipynb`.
- Notebook de ejemplos de uso: `notebooks/ejemplos.ipynb`.
- Tests automáticos en `tests/`.

## Requisitos

- Python 3.14 o compatible.
- Dependencias del proyecto indicadas en `requirements.txt`.

## Instalación

Instalar las dependencias del proyecto:

```bash
python -m pip install -r requirements.txt
```

Instalar el paquete en el entorno actual:

```bash
python -m pip install .
```

Si se prefiere trabajar en modo desarrollo:

```bash
python -m pip install -e .
```

## Uso básico

Ejemplo mínimo de uso del paquete:

```python
from traficFines import MadridFines

mf = MadridFines(app_name="trafic_fines")
mf.add(2024, 12)

print(mf.loaded)
print(mf.fines_calification())
print(mf.total_payment())
```

Si se quiere importar el módulo descrito literalmente en el enunciado, también está disponible como `traficFines.madridFines`.

## Notebooks

- `notebooks/analisis.ipynb`: preprocesamiento y análisis exploratorio de la etapa 1.
- `notebooks/ejemplos.ipynb`: ejemplos de uso y validación manual de las clases del paquete.

## Tests

Ejecutar la batería de tests:

```bash
python -m unittest discover tests/
```

Medir cobertura:

```bash
python -m coverage run --source=traficFines -m unittest discover tests/
python -m coverage report -m
```

## Generación del wheel

Para construir el paquete distribuible `.whl`:

```bash
python -m pip install build
python -m build
```

Los ficheros generados se guardarán en el directorio `dist/`.

## Observaciones

- El proyecto usa una caché local para las descargas del portal de datos abiertos.
- El entorno virtual `.venv/` es solo local y no forma parte de la entrega.
- Para la corrección, basta con disponer del código, los notebooks, los tests y el paquete generado.

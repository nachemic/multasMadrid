# traficFines

Trabajo Final de Programación Avanzada en Python para analizar multas de tráfico del Ayuntamiento de Madrid.

## Contenido del proyecto

- Paquete Python `traficFines/`.
- Notebook de la Etapa 1 en `enunciado/enunciado.ipynb`.
- Notebook de ejemplos y validación en `notebooks/ejemplos.ipynb`.
- Tests automáticos en `tests/`.
- Distribuciones generadas en `dist/`.

## Estructura del paquete

Dentro del paquete `traficFines/` están los módulos principales:

- `cache.py`: clases `Cache`, `CacheURL` y excepción `CacheError`.
- `traficFines.py`: implementación principal de `MadridFines`, `MadridError` y `get_url`.
- `madridFines.py`: alias del módulo anterior para ajustarse al nombre que aparece en el enunciado.

## Requisitos

- Python 3.10 o superior.
- Dependencias indicadas en `requirements.txt`.

## Instalación

Instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

Instalar el paquete en el entorno actual:

```bash
python -m pip install .
```

Si se quiere trabajar en modo desarrollo:

```bash
python -m pip install -e .
```

## Uso básico

Ejemplo mínimo:

```python
from traficFines import MadridFines

mf = MadridFines(app_name="trafic_fines")
mf.add(2024, 12)

print(mf.loaded)
print(mf.fines_calification())
print(mf.total_payment())
```

Tambien puede importarse el módulo con el nombre que aparece en el enunciado:

```python
from traficFines.madridFines import MadridFines
```

## Notebooks

- `enunciado/enunciado.ipynb`: desarrollo de la Etapa 1 con descarga, limpieza y preprocesamiento.
- `notebooks/ejemplos.ipynb`: ejemplos de uso y validación manual de las clases y excepciones.

## Tests

Ejecutar los tests:

```bash
python -m unittest discover tests
```

Opcionalmente, para medir cobertura:

```bash
python -m coverage run --source=traficFines -m unittest discover tests
python -m coverage report -m
```

## Generación del wheel

Para generar el paquete distribuible:

```bash
python -m pip install build
python -m build
```

Los archivos generados se guardan en `dist/`, incluyendo el fichero `.whl` pedido como requisito en enunciado.ipynb.

## Observaciones

- El proyecto usa una caché local para evitar descargas repetidas.
- `.venv/`, `build/` y `*.egg-info/` son carpetas y archivos generados localmente.
- El fichero importante para la entrega instalable es el `.whl` generado en `dist/`.

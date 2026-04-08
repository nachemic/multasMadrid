mf.add(2024, 12)
print(mf.loaded)
print(mf.data.head())
mf.fines_hour("evolucion_multas.png")
print(mf.fines_calification())
print(mf.total_payment())
# madridFines

Proyecto sencillo para analizar multas de tráfico de Madrid.

## Instalación

Instalación de dependencias:

	pip install requests pandas matplotlib numpy

## Uso básico

```python
from madridFines import MadridFines
```

## Tests

Ejecución de tests en la terminal:

	python -m unittest discover tests/
# madridFines

Este es un proyecto sencillo para practicar Python analizando multas de tráfico de Madrid.

## ¿Cómo instalar lo necesario?

1. Abre la terminal (puedes buscar "cmd" o "PowerShell" en tu ordenador).
2. Escribe lo siguiente y pulsa Enter (esto instala las librerías que necesita el proyecto):

	pip install requests pandas matplotlib numpy

Si te da error, asegúrate de tener Python instalado y prueba con:

	python -m pip install requests pandas matplotlib numpy

## ¿Cómo usar el proyecto?

Ejemplo muy simple en Python:

```python
from madridFines import MadridFines
mf = MadridFines()
mf.add(2024, 12)
print(mf.data.head())
```

## ¿Cómo comprobar que todo funciona? (tests)

1. Abre la terminal en la carpeta del proyecto (donde está este archivo README.md).
2. Escribe esto y pulsa Enter:

	python -m unittest discover tests

Si ves muchos "OK" al final, todo está bien.

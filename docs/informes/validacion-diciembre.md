# Validación de diciembre — arquitectura acumulada

Aporte de Ignacio / TrainPulga con asistencia de Codex. La referencia de producto es el [Issue #1](https://github.com/datamaq-automation/flexo-img/issues/1). La organización de Canvas y SRS se revisa en el PR #9; inspección y CMYK, en la cadena de PRs #8 y #10–#20. Ningún PR fue fusionado durante esta ejecución.

## Línea base y resultado actual

El informe existente del commit `655dfa6` registra 115 pruebas aprobadas en Python 3.10.22 y 3.12.14, además de 382/382 sentencias. Ese es un resultado histórico documentado antes de la refactorización. En esta sesión solo estuvo disponible Python 3.12.3 (Ubuntu 24.04), por lo que no se repitió la suite en 3.10.

Sobre la combinación local de las ramas de capas y compatibilidad se ejecutaron **166 pruebas**, todas aprobadas. `pytest --cov=flexo_img --cov-report=term-missing -q` midió 791 sentencias, 11 no cubiertas y **98,61 %** de cobertura. También pasaron `ruff check src tests`, `ruff format --check src tests` y `git diff --check`. No se ejecutó un workflow remoto completo en esta sesión.

Los casos que quedan sin cubrir aparecen en la salida de cobertura; incluyen algunas ramas excepcionales de CLI, limpieza de errores de rasterización y validaciones defensivas. No se retiró código medido ni se modificó el umbral de cobertura para elevar el porcentaje.

## Reproducción de la demo

Los comandos exactos del README se ejecutaron desde un clon limpio de GitHub (`feature/m2-logo-evidencia`) con Python 3.12.3 y un entorno virtual nuevo. `pip install -e '.[dev]'` terminó correctamente. La inspección produjo `resultados/M1/informe-entrada.json`; las conversiones devolvieron `estado: demo`, con ΔE76 medio 1,4732 para la foto y 1,0084 para el logo. Pytest pasó 166/166, cobertura 98,61 %, Ruff check/formato y `git diff --check` pasaron. Se compararon los TIFF y PNG de ambas muestras: las 24 salidas visuales fueron idénticas en modo, tamaño y píxeles a `evidencia/M2/`. La ficha JSON puede variar por fecha/ruta al regenerarse. Las salidas guardadas bajo `evidencia/` son la evidencia recuperada y verificada; `resultados/` se generó en el clon temporal.

En la medición visual del commit de evidencia M2, los valores registrados fueron:

| Muestra | ΔE76 medio de reconversión sRGB D65 | P95 | Máximo |
|---|---:|---:|---:|
| Foto | 1,4732 | 3,1914 | 11,4533 |
| Logo | 1,0084 | 1,8469 | 3,0789 |

Esas cifras describen la reconversión digital bajo los perfiles demo; no miden una impresión. Los perfiles de salida son Artifex CMYK SWOP, no están validados para la máquina, plancha ni sustrato del taller. Las entradas sin perfil se procesan como sRGB solo porque el comando declara `--asumir-srgb`.

## Dependencias y límites

El dominio no importa bibliotecas de imágenes ni lee archivos. La aplicación recibe lectores, rasterizadores o convertidores por contrato; los tests la ejecutan con dobles. Los adaptadores traducen la CLI y presentan fichas; infraestructura concreta usa Pillow, PyMuPDF, NumPy y resvg. La capa de compatibilidad conserva `python -m flexo_img.inspeccion`, `python -m flexo_img.color` y las funciones públicas existentes.

No se consultó producción ni sistemas del taller. No se imprimió una plancha. Python 3.10 requiere una ejecución adicional en Linux/CI o en un entorno disponible; ese resultado no se infiere de Python 3.12. El tramado LPI y el dictamen de aptitud siguen para febrero, con parámetros de RIP/máquina y prueba física pendientes.

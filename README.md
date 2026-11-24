# flexo-img

**Preparación, separación de color, tramado LPI y validación técnica de archivos gráficos para fotopolímeros en flexografía.** Proyecto de PDI y Prácticas Profesionalizantes, ISFT N.º 199.

## Estado de la entrega

Diciembre, [Issue #1](https://github.com/datamaq-automation/flexo-img/issues/1): diseño de producto, inspección y separación de color. Salidas **DEMO**, sin certificado ni dictamen de aptitud de producción. No se conecta con un RIP, servidor del taller ni máquina.

- [Canvas de nueve bloques](docs/canvas.md): usuarios, compradores posibles, problema y métricas; precios y ahorros como hipótesis.
- [SRS](docs/srs.md): recorrido, requisitos verificables, diciembre/febrero y parámetros pendientes.
- [Informe M1](docs/informes/M1-inspeccion.md), [informe M2 y comparaciones](docs/informes/M2-color.md), [validación reproducible](docs/informes/validacion-diciembre.md).
- [Origen del respaldo, muestras, ICC y licencias](docs/origen-y-licencias.md).

Tramado configurable y validación de plancha son objetivos de febrero (#5/#6). El respaldo histórico existe fuera de esta rama; aquí no se entregan esos experimentos como solución final.

## Arquitectura y requisitos

Código en `src/flexo_img/`, pruebas en `tests/`, evidencia en `evidencia/` y documentación en `docs/`. La estructura sigue Arquitectura Limpia: `domain/` contiene entidades, medidas y reglas puras; `application/` contiene casos de uso y contratos; `adapters/controllers/` interpreta la CLI y `adapters/presenters/` prepara fichas; `infrastructure/` implementa lectura/escritura y conecta Pillow, PyMuPDF, NumPy y resvg. La aplicación se prueba con dobles. `inspeccion.py` y `color.py` conservan los comandos y funciones públicos como fachadas de compatibilidad. La entrada no hace llamadas de red.

Python **3.10 o superior** y Git. Las pruebas se ejecutaron en Linux con Python 3.10 y 3.12. Dependencias de ejecución en pyproject.toml: Pillow, PyMuPDF, NumPy, resvg-py y defusedxml; pytest, pytest-cov y Ruff son de desarrollo. La instalación requiere acceso a paquetes; muestras y perfiles ya están en el repositorio. NumPy calcula las diferencias de color en bloques de píxeles.

## Reproducir desde una copia limpia

Con acceso de lectura al repositorio, elegir una carpeta destino que no exista. Ejecutar en Ubuntu/Bash:

```bash
git clone --branch feature/m2-logo-evidencia --single-branch https://github.com/datamaq-automation/flexo-img.git flexo-img-demo
cd flexo-img-demo
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m flexo_img.inspeccion evidencia/M1/entradas/foto-hopper.jpg evidencia/M1/entradas/foto-derivada.png evidencia/M1/entradas/logo-svg.svg evidencia/M1/entradas/documento-w3c.pdf --salida resultados/M1 --dpi 150 --svg-mm 50 50
.venv/bin/python -m flexo_img.color evidencia/M1/entradas/foto-hopper.jpg --salida resultados/M2/foto --perfil-cmyk perfiles-icc/default_cmyk.icc --perfil-srgb perfiles-icc/default_rgb.icc --asumir-srgb
.venv/bin/python -m flexo_img.color resultados/M1/37c922cb31b7-p1-150ppp.png --salida resultados/M2/logo --perfil-cmyk perfiles-icc/default_cmyk.icc --perfil-srgb perfiles-icc/default_rgb.icc --asumir-srgb
.venv/bin/python -m pytest --cov=flexo_img --cov-report=term-missing --cov-report=xml:cobertura.xml -q
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
git diff --check
```

La inspección imprime la ruta exacta de la ficha. Cuando el directorio solicitado ya existe, crea dentro un directorio nuevo `lote-…` para conservar resultados anteriores. Si volvés a procesar un logo, tomá el PNG de ese lote. La API de separación matemática requiere una imagen RGB con fondo ya definido. Para PNG transparentes, la conversión ICC admite la elección explícita `--fondo-blanco`.

Ejecutar una vez por copia: la conversión no sobrescribe directorios existentes. Para repetir, usar otra copia o rutas de salida nuevas; no borrar evidencia entregada. `resultados/`, entorno y cobertura no se commitean. Las fechas/rutas de informes pueden cambiar al repetir; comparar datos y píxeles, no exigir igualdad binaria de todos los JSON.

Para consultar la ficha desde Python, usá `from flexo_img.inspector import inspeccionar_archivo` y llamá a `inspeccionar_archivo(ruta)`. Para reproducir la medición de rendimiento desde la raíz, ejecutá `.venv/bin/python scripts/medir_diciembre.py`.

La fórmula pedagógica de #4 se puede comprobar sin ICC:

```bash
.venv/bin/python -c 'from PIL import Image; from flexo_img.color import separar_cuatricromia; c=separar_cuatricromia(Image.new("RGB",(1,1),(255,0,0))); print(tuple(plano.getpixel((0,0)) for plano in c))'
```

Salida esperada: C=0, M=255, Y=255, K=0 (cobertura). La función devuelve una tupla C, M, Y, K. Si tu código usaba el diccionario de la versión anterior, importá `separar_por_nombre` para seguir accediendo por clave. Esta fórmula no equivale a la conversión ICC de los comandos anteriores.

## Qué mostrar en el coloquio

1. `evidencia/M1/final/informe-entrada.json`: original y rasterización separados. Foto 128×128 RGB; SVG vectorial sin DPI global; PDF con texto. Elegir 150 PPP/50 mm no agrega resolución original.
2. `evidencia/M2/foto/comparacion_DEMO.png` y `evidencia/M2/logo/comparacion_DEMO.png`: original, preview y C/M/Y/K. Blanco=sin tinta en la vista invertida.
3. `informe_M2.json` y `muestras_color.csv` de cada muestra: supuestos ICC y cambios medidos. No son colorimetría impresa.
4. Canvas/SRS: explicar uso en taller, cómo medir valor y límites. Cerrar con pendientes de febrero: muestra real autorizada, RIP, resolución/polaridad, ICC de máquina, plancha/sustrato, LPI, punto/línea mínimos, TAC y prueba física.

## Cómo leer los canales

`canal_*_cobertura_DEMO.png`: dato L de 8 bits, 0=sin tinta/255=máxima. `canal_*_gris_DEMO.png`: invertido para pantalla, 255 blanco=sin tinta/0 negro=máxima. La redacción de #4 mezcla nombres de blanco/negro con cobertura: se explicitan las dos convenciones; queda por confirmar la polaridad real de exposición.

Se usa sRGB asumido solo con consentimiento explícito si falta ICC. El perfil Artifex CMYK SWOP no representa una máquina flexográfica confirmada. Todas las salidas son DEMO; no son archivos de plancha listos para producción.

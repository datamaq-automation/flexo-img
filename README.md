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

Código en `src/flexo_img/`, tests en `tests/`, evidencia en `evidencia/` y documentación en `docs/`. `inspeccion.py` caracteriza y rasteriza; `color.py` separa/convierte/exporta. Funciones pequeñas y comprobables, sin servicios ni red durante procesamiento/tests.

Python **3.12** y Git, verificados en Ubuntu. El README inicial aspiraba a Python 3.10+; este avance utiliza 3.12 y no afirma validación en 3.10/Windows. Dependencias runtime exactas en pyproject.toml: Pillow, PyMuPDF y defusedxml; pytest, pytest-cov y Ruff son de desarrollo. La instalación requiere acceso a paquetes; muestras y perfiles ya están en el repositorio. No hace falta instalar OpenCV o NumPy para esta implementación con Pillow.

## Reproducir desde una copia limpia

Con acceso de lectura al repositorio, elegir una carpeta destino que no exista. Ejecutar en Ubuntu/Bash:

```bash
git clone --branch feature/entrega-diciembre --single-branch https://github.com/datamaq-automation/flexo-img.git flexo-img-demo
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

Ejecutar una vez por copia: la conversión no sobrescribe directorios existentes. Para repetir, usar otra copia o rutas de salida nuevas; no borrar evidencia entregada. `resultados/`, entorno y cobertura no se commitean. Las fechas/rutas de informes pueden cambiar al repetir; comparar datos y píxeles, no exigir igualdad binaria de todos los JSON.

La fórmula pedagógica de #4 se puede comprobar sin ICC:

```bash
.venv/bin/python -c 'from PIL import Image; from flexo_img.color import separar_cuatricromia; c=separar_cuatricromia(Image.new("RGB",(1,1),(255,0,0))); print({k:v.getpixel((0,0)) for k,v in c.items()})'
```

Salida esperada: C=0, M=255, Y=255, K=0 (cobertura). Esta fórmula no equivale a la conversión ICC de los comandos anteriores.

## Qué mostrar en el coloquio

1. `evidencia/M1/final/informe-entrada.json`: original y rasterización separados. Foto 128×128 RGB; SVG vectorial sin DPI global; PDF con texto. Elegir 150 PPP/50 mm no agrega resolución original.
2. `evidencia/M2/foto/comparacion_DEMO.png` y `evidencia/M2/logo/comparacion_DEMO.png`: original, preview y C/M/Y/K. Blanco=sin tinta en la vista invertida.
3. `informe_M2.json` y `muestras_color.csv` de cada muestra: supuestos ICC y cambios medidos. No son colorimetría impresa.
4. Canvas/SRS: explicar uso en taller, cómo medir valor y límites. Cerrar con pendientes de febrero: muestra real autorizada, RIP, resolución/polaridad, ICC de máquina, plancha/sustrato, LPI, punto/línea mínimos, TAC y prueba física.

## Cómo leer los canales

`canal_*_cobertura_DEMO.png`: dato L de 8 bits, 0=sin tinta/255=máxima. `canal_*_gris_DEMO.png`: invertido para pantalla, 255 blanco=sin tinta/0 negro=máxima. La redacción de #4 mezcla nombres de blanco/negro con cobertura: se explicitan las dos convenciones; queda por confirmar la polaridad real de exposición.

Se usa sRGB asumido solo con consentimiento explícito si falta ICC. El perfil Artifex CMYK SWOP no representa una máquina flexográfica confirmada. Todas las salidas son DEMO; no son archivos de plancha listos para producción.

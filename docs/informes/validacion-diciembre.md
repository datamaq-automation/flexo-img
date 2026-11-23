# Validación de diciembre — ejecución observada

## Ampliación de pruebas de diciembre — medición actual

Sobre la rama del PR #7 se repitió primero la medición original: **78 pruebas aprobadas y 86,39 %** de cobertura, 46 sentencias no ejecutadas. Después se agregaron **27 casos de prueba en 15 funciones** en `tests/test_entradas_y_cli.py`, sin modificar las pruebas anteriores, el código de `src/`, pyproject.toml, el umbral del 85 % ni las exclusiones.

Comando idéntico antes y después, desde la raíz del clon aislado y con el mismo Python 3.12.3/entorno de la entrega (cambiar solo la ruta al ejecutable del entorno):

```bash
python -m pytest --cov=flexo_img --cov-report=term-missing -q
ruff check src tests
ruff format --check src tests
git diff --check
```

| Medición | Casos aprobados | Sentencias | Sin ejecutar | Cobertura |
|---|---:|---:|---:|---:|
| Base repetida antes de ampliar | 78 | 338 | 46 | 86,39 % |
| Después de ampliar | 105 | 338 | 0 | 100,00 % |

`inspeccion.py`: 178/178 sentencias; `color.py`: 160/160. Ruff check aprobado; Ruff format --check: seis archivos correctos. Sin errores de whitespace en el diff propio. No se cambió el criterio para medir: source sigue siendo flexo_img y se mide cobertura de sentencias, **no cobertura de ramas**.

### Qué comprueban los 27 casos nuevos

| Grupo | Casos nuevos | Resultado que se verifica |
|---|---:|---|
| Límites y formatos de inspección | 12 | Dimensiones no positivas/no finitas, medidas SVG inválidas, GIF disfrazado de PNG, XML que no es SVG, exceso de bytes y PDF cifrado/con demasiadas páginas: rechazo claro, sin modificar originales ni producir raster indebido |
| SVG mixto y advertencias reales | 1 | SVG local con texto/vector e imagen incrustada dañada: clasificación mixta, render disponible y advertencia real de MuPDF que identifica la imagen ignorada; aptitud no evaluada |
| CLI de inspección | 8 | Parámetros inválidos, carpeta de entrada y destino enlazado al original: código 2 sin sobrescritura; informe completo/parcial: códigos 0/1, JSON, fecha, hash y estados coherentes |
| Límites y perfil de color | 2 | Exceso de bytes y perfil RGB local cuya descripción no identifica sRGB: rechazo sin crear una entrega |
| CLI de color | 4 | Sin ICC no autorizado, archivo ausente y perfil corrupto: código 1 y explicación sin entrega; éxito: código 0, resumen JSON consistente, ocho PNG de canal (dos convenciones), hash y original conservado |

Los casos CLI ejecutan el punto de entrada real mediante `runpy.run_path(..., run_name="__main__")` dentro del proceso instrumentado por pytest-cov, con argv temporal y comprobación de SystemExit. No se simulan main, el parser, las lecturas, el rasterizador ni las conversiones ICC. Las pruebas previas de CLI en subprocesos se conservan. Los límites se reducen mediante monkeypatch para probar rechazos sin crear archivos enormes; se generan PDF cifrado y de dos páginas, SVG y raster locales. La prueba de perfil cambia solo el nombre del ICC de referencia en una copia temporal y comprueba que sigue siendo RGB. Sin red ni datos de producción.

### Alcance de este resultado

El 100 % acredita ejecución de todas las sentencias actuales, no todos los caminos, combinaciones de entrada o parámetros físicos. El SVG con imagen dañada puede informar `estado: ok` para la inspección y llevar advertencias de contenido ignorado: la prueba exige esa advertencia, no promete reproducción completa. Las salidas siguen siendo DEMO y la aptitud industrial continúa pendiente. No se regeneró la evidencia ni se amplió el alcance de febrero.

## Registro histórico de la primera entrega

Los números de 78 pruebas, 52 de inspección, 26 de color y 86,39 % que aparecen a continuación describen la entrega inicial y su reproducción, no sustituyen la medición actual de 105 pruebas anterior.

Aporte de Ignacio / TrainPulga con asistencia de Codex. [Consigna #1](https://github.com/datamaq-automation/flexo-img/issues/1); avances M1 y M2, sin tramado ni veredicto de plancha.

## Recuperación y controles del repositorio

ZIP de Descargas conservado, CRC correcto y SHA-256 `59ba8253194973030a36809921d662f7a0a8867b3ce8494dd0a0b1ceb87c59ef` verificado antes y después. Su bundle se verificó y abrió en otro clon: HEAD histórico `8f74c7b`. La rama de entrega parte de `origin/main` de flexo-img y conserva su historia. No se importan commits de tramado/evaluación: permanecen respaldados para febrero.

Al revisar el repositorio inicial había README y .gitignore, una rama main y ningún AGENTS.md, CONTRIBUTING.md o workflow de controles. Se aplicaron las pautas de #1–#4: paquete src/flexo_img, tests, docs y commits identificables. Se fijaron herramientas y un mínimo de cobertura de entrega del 85 %. No es un umbral de imprenta.

Una primera copia aislada sufrió archivos vacíos y un objeto Git inválido antes de publicar. Se descartó como fuente de entrega y se reconstruyó desde el remoto y ZIP, con sincronización de escrituras y git fsck. El respaldo original no cambió. Los resultados siguientes corresponden a la copia reconstruida, no a la fallida.

## Qué ejecuté

En Ubuntu, Python 3.12.3, clon limpio del commit de código M2 `588baa0`, entorno virtual nuevo y dependencias instaladas mediante pyproject.toml. Los comandos de procesamiento y controles son los del README. La primera clonación usó la copia local por estar aún sin publicar. Después se clonó desde GitHub la rama publicada con código `3fb34ef`, se creó otro entorno nuevo y se ejecutaron todos los comandos del README: salida 0, 78 pruebas aprobadas en 2,80 s y 86,39 % de cobertura. Ruff y formato aprobados, fórmula de rojo correcta y árbol limpio al finalizar. Esta es la ejecución remota de referencia (los comandos se ejecutaron localmente sobre el clon de GitHub, no en CI).

| Control | Resultado observado |
|---|---|
| Pytest M1 | 52 aprobadas |
| Pytest color | 26 aprobadas |
| Pytest completo | 78 aprobadas, 0 fallos |
| Cobertura de paquete | 86,39 %; 338 sentencias, 46 no cubiertas |
| Ruff check src tests | aprobado |
| Ruff format --check src tests | 5 archivos formateados correctamente |
| git diff --check | sin errores; excepción solo para espacios originales del SVG W3C |
| Ingesta CLI | cuatro entradas válidas y render explícito PDF/SVG |
| Color CLI | foto y logo convertidos y cuatro canales exportados en ambas convenciones |
| Fórmula de rojo puro | C=0, M=255, Y=255, K=0 |
| Reproducción visual | 26 imágenes PNG/TIFF idénticas píxel a píxel, incluyendo dos rasterizaciones M1 y salidas M2 |

Se revisaron visualmente los paneles de foto y logo. Fechas/rutas de informes pueden cambiar, por eso no se exige igualdad binaria de todos los JSON. Las dependencias observadas están en [entorno-diciembre.txt](entorno-diciembre.txt). Los requirements fijan paquetes directos; el registro de entorno documenta también transitivas. No se promete rendimiento general a partir de estas muestras pequeñas ni validación en otras versiones de Python.

## Qué puedo explicar en el coloquio

Identifico original y salida elegida; muestro el informe de inspección, la foto/logo y C/M/Y/K; explico por qué asumo sRGB solo con autorización y por qué el ICC de demo no es el de una máquina confirmada. Diferencio cobertura numérica de apariencia y separación matemática de ICC. Canvas y SRS explican el problema del taller y cómo comprobar requisitos, con precios/ahorros pendientes.

## Qué queda para febrero

Integrar y contrastar tramado y calidad con #5/#6, usando originales autorizados del taller. Confirmar RIP, perfil ICC, formato/resolución/polaridad, LPI/ángulos, plancha/sustrato, tinta y límites de cobertura/punto/líneas. Faltan dictamen humano de referencia y prueba física. Las salidas actuales son DEMO; no afirmo APTO industrial ni una mejora comercial medida. El Issue #1 continúa abierto.

## Ajuste final de salida

Los CSV se generan con finales LF explícitos. La comparación `git diff --check origin/main...HEAD` pasa para el PR completo; el SVG W3C conserva sus bytes originales mediante una excepción de whitespace limitada a ese archivo. No se ajustaron tests para ocultar errores: las nuevas pruebas detectaron y ayudaron a corregir la adaptación a Pillow y a verificar el espacio RGB real del PDF generado.

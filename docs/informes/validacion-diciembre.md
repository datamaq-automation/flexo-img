# Validación de diciembre — ejecución observada

Aporte de Ignacio / TrainPulga con asistencia de Codex. [Consigna #1](https://github.com/datamaq-automation/flexo-img/issues/1); avances M1 y M2, sin tramado ni veredicto de plancha.

## Recuperación y controles del repositorio

ZIP de Descargas conservado, CRC correcto y SHA-256 `59ba8253194973030a36809921d662f7a0a8867b3ce8494dd0a0b1ceb87c59ef` verificado antes y después. Su bundle se verificó y abrió en otro clon: HEAD histórico `8f74c7b`. La rama de entrega parte de `origin/main` de flexo-img y conserva su historia. No se importan commits de tramado/evaluación: permanecen respaldados para febrero.

Al revisar el repositorio inicial había README y .gitignore, una rama main y ningún AGENTS.md, CONTRIBUTING.md o workflow de controles. Se aplicaron las pautas de #1–#4: paquete src/flexo_img, tests, docs y commits identificables. Se fijaron herramientas y un mínimo de cobertura de entrega del 85 %. No es un umbral de imprenta.

Una primera copia aislada sufrió archivos vacíos y un objeto Git inválido antes de publicar. Se descartó como fuente de entrega y se reconstruyó desde el remoto y ZIP, con sincronización de escrituras y git fsck. El respaldo original no cambió. Los resultados siguientes corresponden a la copia reconstruida, no a la fallida.

## Qué ejecuté

En Ubuntu, Python 3.12.3, clon limpio del commit de código M2 `588baa0`, entorno virtual nuevo y dependencias instaladas mediante pyproject.toml. Los comandos de procesamiento y controles son los del README. La clonación inicial usó la copia local por estar aún sin publicar; después de publicar se verifica también la rama remota.

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

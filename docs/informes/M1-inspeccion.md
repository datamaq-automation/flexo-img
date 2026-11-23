# M1 — inspeccionar antes de modificar

Aporte de Ignacio / TrainPulga con asistencia de Codex. Recuperado del bundle histórico M1 c5c41d7 y adaptado a `src/flexo_img/inspeccion.py` sin fusionar historias ajenas.

## Qué hice y para qué
Inspeccioné archivos antes de convertir: dimensiones, modo/espacio conocido, resolución disponible, contenido raster/vector/texto/mixto y hash. Sirve para saber qué llegó del diseñador y qué información falta antes de fabricar.

## Resultado observado
`evidencia/M1/final/informe-entrada.json`: JPEG 128×128 RGB, metadatos 96 PPP, sin ICC; PNG derivado sin DPI supuesto; SVG W3C vectorial con viewBox y tamaño relativo, sin resolución global intrínseca; PDF W3C de 595×842 pt con texto.

Elegí 150 PPP y 50×50 mm para renderizar el SVG: 296×296 píxeles. El PDF se renderiza a 150 PPP según su página. Son parámetros elegidos para las salidas, nunca datos originales. En PDF se calcula el DPI de imágenes según colocación. Se conserva modo y resolución de originales raster sin remuestrearlos.

## Pruebas y límites
52 pruebas M1 aprobadas: formatos y hashes, datos desconocidos, unidades/viewBox, colocación PDF, documento mixto real, CLI y rechazo de recursos externos/archivos inválidos. PyMuPDF describe el RGB del PDF generado como ICCBased(RGB), no necesariamente DeviceRGB: la prueba verifica que informa el espacio real. Ruff y formato aprobados en la adaptación; cobertura y reproducción se registran en el informe final de validación.

No se auditan todos los espacios vectoriales/OutputIntent del PDF ni se certifica una plancha. Falta el tamaño final del trabajo y parámetros del taller; los límites de recursos no son reglas de calidad. El ejemplo <200 DPI de la consigna no se adopta como umbral de producción. Orígenes y hashes en `evidencia/M1/origenes.json`; muestras académicas, no diseños de un cliente.

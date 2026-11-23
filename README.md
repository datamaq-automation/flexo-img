# flexo-img

**Preparación, separación de color, tramado LPI y validación técnica de archivos gráficos para fotopolímeros en flexografía.**

Proyecto para Técnicas de Procesamiento Digital de Imágenes y Prácticas Profesionalizantes — 3° Año ISFT 199.

## Objetivos del Sistema

1. **Inspección e Ingesta:** Lectura y caracterización de archivos gráficos (PDF, JPG, PNG, SVG) extrayendo dimensiones, resolución (DPI), espacio de color y naturaleza vectorial/raster.
2. **Separación de Color:** Conversión de RGB a cuatricromía (CMYK) y extracción de canales independientes en escala de grises.
3. **Tramado LPI:** Generación de tramas de semitono (halftoning) con lineatura por pulgada (LPI) configurable según el proceso de impresión.
4. **Validación de Aptitud (Fotopolímeros):** Reglas de control de calidad para producción flexográfica (cobertura total de tinta, grosor mínimo de trazos y cálculo de resolución mínima en función del LPI). Emisión de informe técnico *Apto / No apto*.

## Requisitos y Configuración

- Python 3.10+
- OpenCV / Pillow / NumPy

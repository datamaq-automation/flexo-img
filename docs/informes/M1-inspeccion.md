# M1 — inspeccionar antes de modificar

Aporte de Ignacio / TrainPulga con asistencia de Codex. Recuperado de la entrega previa y reorganizado en `src/flexo_img/` con casos de uso y adaptadores. M1 responde a la necesidad de conocer el archivo recibido antes de convertirlo o fabricar una plancha.

## Qué recibe y qué informa

La muestra académica incluye una foto JPEG de Pillow, un PNG derivado de esa foto, un logo SVG público de W3C y un PDF de prueba W3C. Sus URLs, relaciones y SHA-256 están en `evidencia/M1/origenes.json`; no son archivos de clientes.

El informe `evidencia/M1/final/informe-entrada.json` conserva por separado los datos del original y los parámetros elegidos para rasterizar. La foto mide 128×128 px, se identifica como RGB y trae 96 PPP en metadatos; no trae ICC. El SVG expresa dimensiones relativas y `viewBox`, por lo que no tiene un tamaño físico ni una resolución global inferible. El PDF tiene páginas vectoriales/textuales; el espacio de sus imágenes se informa por colocación cuando existe. Un PNG derivado no recibe resolución supuesta.

Para demostrar rasterización elegí 150 PPP y 50×50 mm para el SVG. El informe etiqueta esos valores como selección de salida, no como propiedades del original. El tamaño final de impresión real todavía lo debe decidir quien prepara el trabajo.

## Arquitectura y pruebas

El dominio expresa medidas y validaciones sin Pillow/PyMuPDF/NumPy. Los casos de uso reciben lectores y rasterizador por contrato. Los adaptadores presentan el informe JSON y la CLI; la infraestructura lee PNG/JPEG, PDF y SVG y rasteriza PDF/SVG cuando se piden parámetros. Las funciones y comandos públicos previos siguen como fachadas.

Las pruebas M1 históricas recuperadas se conservan en `tests/test_entradas_y_cli.py`, `tests/test_inspeccion.py` y `tests/test_inspector.py`, junto con pruebas por capa. La combinación completa observada pasó 166 pruebas en Python 3.12.3. El informe de validación separa ese resultado de la base histórica de Python 3.10.

## Qué no certifica

Una ficha técnica no valida todos los OutputIntent/espacios vectoriales de un PDF ni garantiza resultado de impresión. Los límites de bytes, páginas y píxeles protegen el proceso local: no son umbrales de calidad. Quedan pendientes el tamaño final de trabajo y los criterios de aceptación del taller.

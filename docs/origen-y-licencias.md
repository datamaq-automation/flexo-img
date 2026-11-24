# Recuperación, muestras y licencias

Respaldo de entrada: `entrega-preprensa-presentacion-DEMO.zip`, SHA-256 `59ba8253194973030a36809921d662f7a0a8867b3ce8494dd0a0b1ceb87c59ef`. CRC correcto; Git bundle verificado con historia completa, HEAD `8f74c7bfd9bb56a6823455472106dc5a34b1a350`, abierto en otra copia. El ZIP de Descargas se conserva sin modificar. El bundle permanece fuera de esta rama: contiene también tramado/evaluación para febrero. No se publican esos módulos como avance de diciembre.

Se conserva la historia inicial de flexo-img. Los commits nuevos identifican documentación, adaptación M1, adaptación M2 y reproducción. No se fusionan historias no relacionadas del prototipo.

## Muestras

Orígenes y hashes exactos: [origenes.json](../evidencia/M1/origenes.json). Foto Hopper 128×128 recuperada de las pruebas públicas de Pillow; no es fotografía generada ni dato de un cliente. PNG derivado de esa foto sin remuestreo, no muestra independiente. PDF de prueba W3C, no un packaging real. Logo SVG oficial W3C: su metadata atribuye a W3C/Harvey Rayner y enlaza CC BY-NC-SA 2.5; uso académico DEMO, no identidad propia ni marca del taller. Las condiciones del logo no se sustituyen por las del código.

Los archivos de muestra se conservan byte por byte. El SVG W3C contiene espacios finales: `.gitattributes` desactiva exclusivamente su comprobación de whitespace, para no alterar origen/hash. Esa excepción no afecta código, tests ni documentos propios.

## Perfiles y dependencias

Los ICC Artifex se incluyen con origen, revisión, SHA-256 y avisos originales en [perfiles-icc](../perfiles-icc/). Se adjuntan LICENSE y COPYING; el aviso upstream incluye iccprofiles en Ghostscript bajo AGPL. PyMuPDF también tiene condiciones de licencia que deben revisarse antes de una distribución comercial; no se afirma que todas las dependencias sean permisivas. No se elimina ningún aviso ni se declara una licencia única sobre muestras ajenas. La verificación técnica no reemplaza esa revisión.

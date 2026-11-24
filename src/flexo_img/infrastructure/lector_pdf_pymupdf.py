"""Lectura PDF local mediante PyMuPDF; el informe describe el original."""

from __future__ import annotations

import math
from hashlib import sha256
from pathlib import Path

import pymupdf

from flexo_img.application.inspeccionar_pdf import ResultadoPDF
from flexo_img.domain.validaciones import validar_limites_archivo

MAX_PAGINAS = 20


class LectorPDFPyMuPDF:
    def leer(self, ruta: Path) -> ResultadoPDF:
        contenido = ruta.read_bytes()
        validar_limites_archivo(len(contenido), 1, 1)
        try:
            with pymupdf.open(stream=contenido, filetype="pdf") as documento:
                if not documento.is_pdf or documento.needs_pass:
                    raise ValueError(
                        "PDF cifrado, inválido o fuera del límite local de 20 páginas"
                    )
                if not 1 <= len(documento) <= MAX_PAGINAS:
                    raise ValueError(
                        "PDF cifrado, inválido o fuera del límite local de 20 páginas"
                    )
                paginas = [self._pagina(pagina) for pagina in documento]
        except (pymupdf.FileDataError, RuntimeError) as exc:
            raise ValueError("PDF inválido o no legible") from exc
        return ResultadoPDF(
            tamano_bytes=len(contenido),
            sha256=sha256(contenido).hexdigest(),
            original={
                "formato_detectado": "PDF",
                "numero_paginas": len(paginas),
                "resolucion_original_ppp": None,
                "modo_color": "no_unico; solo se describen espacios de imágenes detectadas",
                "paginas": paginas,
            },
            avisos=(
                "PDF no tiene un único DPI ni modo de color. Imágenes y vectores se distinguen.",
                "Las cajas visibles no verifican sangrado, tintas planas ni sobreimpresión.",
            ),
        )

    @staticmethod
    def _pagina(pagina: pymupdf.Page) -> dict[str, object]:
        imagenes = []
        for info in pagina.get_image_info():
            a, b, c, d, _, _ = info["transform"]
            ancho, alto = math.hypot(a, b), math.hypot(c, d)
            imagenes.append(
                {
                    "ancho_px": info["width"],
                    "alto_px": info["height"],
                    "espacio_color": info.get("cs-name"),
                    "ppp_efectivos_por_colocacion": [
                        round(info["width"] * 72 / ancho, 4),
                        round(info["height"] * 72 / alto, 4),
                    ]
                    if ancho > 0 and alto > 0
                    else None,
                }
            )
        texto = bool(pagina.get_text("words"))
        vector = bool(pagina.get_drawings())
        tipos = [
            nombre
            for nombre, presente in (
                ("texto", texto),
                ("vector", vector),
                ("raster", bool(imagenes)),
            )
            if presente
        ]
        return {
            "pagina": pagina.number + 1,
            "caja_visible_pt": [pagina.rect.width, pagina.rect.height],
            "caja_visible_mm": [
                round(x * 25.4 / 72, 4) for x in (pagina.rect.width, pagina.rect.height)
            ],
            "rotacion_grados": pagina.rotation,
            "tipos_detectados": tipos,
            "tipo_contenido": "mixto"
            if len(tipos) > 1
            else (tipos[0] if tipos else "no_detectado"),
            "imagenes_embebidas": imagenes,
        }

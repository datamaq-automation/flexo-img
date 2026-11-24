"""Compatibilidad del comando y las funciones públicas de inspección."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pymupdf

from flexo_img.adapters.controllers.cli_inspeccion import main
from flexo_img.application.inspeccionar_lote import inspeccionar_lote
from flexo_img.domain import validaciones as reglas
from flexo_img.domain.unidades_svg import UNIDADES_CSS, longitud_svg_css_px
from flexo_img.domain.validaciones import validar_limites_archivo
from flexo_img.infrastructure.imagenes_pillow import LectorPillow
from flexo_img.infrastructure.lector_pdf_pymupdf import LectorPDFPyMuPDF
from flexo_img.infrastructure.lector_svg import LectorSVGXML
from flexo_img.infrastructure.pymupdf_rasterizador import RasterizadorPyMuPDF
from flexo_img.inspector import inspeccionar_archivo

MAX_BYTES = reglas.MAX_BYTES
MAX_PIXELES = reglas.MAX_PIXELES
MAX_PAGINAS = reglas.MAX_PAGINAS
UNIDADES = UNIDADES_CSS
__all__ = [
    "MAX_BYTES",
    "MAX_PIXELES",
    "MAX_PAGINAS",
    "UNIDADES",
    "par_valido",
    "pixeles_permitidos",
    "raster",
    "describir_pagina",
    "longitud_svg",
    "svg",
    "renderizar",
    "inspeccionar",
    "main",
]


def par_valido(valor: Any) -> list[float] | None:
    try:
        par = [float(valor[0]), float(valor[1])]
        return par if all(math.isfinite(x) and x > 0 for x in par) else None
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def pixeles_permitidos(ancho: float, alto: float) -> None:
    if not all(math.isfinite(x) and x > 0 for x in (ancho, alto)):
        raise ValueError("Dimensiones no positivas o no finitas")
    validar_limites_archivo(1, math.ceil(ancho), math.ceil(alto))


def raster(path: Path) -> tuple[dict[str, Any], list[str]]:
    imagen = LectorPillow().leer(path)
    return {
        "formato_detectado": imagen.formato_detectado,
        "tipo_contenido": "raster",
        "ancho_px": imagen.ancho_px,
        "alto_px": imagen.alto_px,
        "modo_color": imagen.modo_color,
        "canales": list(imagen.canales),
        "resolucion_metadatos_ppp": list(imagen.resolucion_ppp)
        if imagen.resolucion_ppp
        else None,
        "tamano_derivado_de_metadatos_mm": [
            round(n / d * 25.4, 4)
            for n, d in zip(
                (imagen.ancho_px, imagen.alto_px), imagen.resolucion_ppp, strict=True
            )
        ]
        if imagen.resolucion_ppp
        else None,
        "orientacion_exif": imagen.orientacion_exif,
        "transparencia": imagen.transparencia,
        "icc_presente": imagen.icc_sha256 is not None,
        "icc_sha256": imagen.icc_sha256,
        "fotografia_o_logo": "no_inferido",
    }, [
        "El tamaño físico derivado depende de metadatos; falta confirmar tamaño de impresión."
    ]


def describir_pagina(page: pymupdf.Page) -> dict[str, Any]:
    return LectorPDFPyMuPDF._pagina(page)


def longitud_svg(valor: str | None) -> float | None:
    return longitud_svg_css_px(valor)


def svg(path: Path) -> tuple[dict[str, Any], list[str]]:
    informe = LectorSVGXML().leer(path)
    return informe.original, list(informe.avisos)


def renderizar(
    doc: pymupdf.Document,
    dpi: int,
    destino: Path,
    prefijo: str,
    svg_gradiente: str | None = None,
) -> list[dict[str, Any]]:
    return RasterizadorPyMuPDF()._renderizar(doc, destino, prefijo, dpi, svg_gradiente)


def inspeccionar(
    path: Path, salida: Path, dpi: int | None = None, svg_mm: list[float] | None = None
) -> dict[str, Any]:
    informe = inspeccionar_lote(
        [path],
        salida,
        inspeccionar_archivo,
        RasterizadorPyMuPDF(),
        dpi,
        tuple(svg_mm) if svg_mm is not None else None,
    )
    return informe["archivos"][0]


if __name__ == "__main__":
    raise SystemExit(main())

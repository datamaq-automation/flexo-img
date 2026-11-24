"""Caso de uso para producir una ficha técnica de una imagen raster."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from flexo_img.application.inspeccionar_imagen import LectorRaster
from flexo_img.domain.imagen import ImagenRaster
from flexo_img.domain.medidas import dimensiones_fisicas_mm


@dataclass(frozen=True, slots=True)
class ResultadoInspeccionRaster:
    original: ImagenRaster
    dimensiones_fisicas_mm: tuple[float, float] | None
    avisos: tuple[str, ...]


def inspeccionar_raster(
    ruta: str | Path, lector: LectorRaster
) -> ResultadoInspeccionRaster:
    """Interpreta los metadatos disponibles; no supone DPI ni tamaño ausente."""
    original = lector.leer(Path(ruta))
    avisos = [
        "El tamaño físico derivado depende de metadatos; falta confirmar tamaño de impresión."
    ]
    if original.resolucion_ppp is None:
        avisos.append(
            "Sin resolución física verificable: no se supone un valor de PPP."
        )
    esperado = "JPEG" if Path(ruta).suffix.lower() in (".jpg", ".jpeg") else "PNG"
    if original.formato_detectado != esperado:
        avisos.append("La extensión difiere del formato detectado.")
    return ResultadoInspeccionRaster(
        original=original,
        dimensiones_fisicas_mm=dimensiones_fisicas_mm(
            original.ancho_px, original.alto_px, original.resolucion_ppp
        ),
        avisos=tuple(avisos),
    )

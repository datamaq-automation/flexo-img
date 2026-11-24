"""Caso de uso para inspeccionar la geometría de un original raster."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from flexo_img.domain.imagen import ImagenRaster
from flexo_img.domain.medidas import dimensiones_fisicas_mm


class LectorRaster(Protocol):
    """Contrato para una implementación que sabe leer un archivo raster."""

    def leer(self, ruta: Path) -> ImagenRaster: ...


@dataclass(frozen=True, slots=True)
class FichaImagen:
    """Resultado de aplicación, separado de Pillow y de la salida CLI."""

    original: ImagenRaster
    dimensiones_fisicas_mm: tuple[float, float] | None


def inspeccionar_imagen(ruta: str | Path, lector: LectorRaster) -> FichaImagen:
    """Coordina la lectura y las reglas de tamaño sin depender del formato."""
    original = lector.leer(Path(ruta))
    fisicas = dimensiones_fisicas_mm(
        original.ancho_px, original.alto_px, original.resolucion_ppp
    )
    return FichaImagen(original=original, dimensiones_fisicas_mm=fisicas)

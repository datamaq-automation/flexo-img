"""Modelo de una imagen raster descrita sin dependencias de imagen."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImagenRaster:
    """Medidas y metadatos leídos de un original raster."""

    ancho_px: int
    alto_px: int
    modo_color: str
    resolucion_ppp: tuple[float, float] | None = None
    formato_detectado: str = "raster"
    canales: tuple[str, ...] = ()
    orientacion_exif: int | None = None
    transparencia: bool = False
    icc_sha256: str | None = None
    tamano_bytes: int = 0
    sha256: str = ""

    def __post_init__(self) -> None:
        if any(
            isinstance(n, bool) or not isinstance(n, int) or n <= 0
            for n in (self.ancho_px, self.alto_px)
        ):
            raise ValueError("Las dimensiones en píxeles deben ser enteros positivos")
        if not self.modo_color:
            raise ValueError("El modo de color no puede estar vacío")
        if self.resolucion_ppp is not None and (
            len(self.resolucion_ppp) != 2
            or any(not math.isfinite(ppp) or ppp <= 0 for ppp in self.resolucion_ppp)
        ):
            raise ValueError("La resolución debe contener dos PPP positivos")

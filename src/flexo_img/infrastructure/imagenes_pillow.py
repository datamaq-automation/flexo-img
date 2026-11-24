"""Adaptador de infraestructura para metadatos raster mediante Pillow."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from flexo_img.domain.imagen import ImagenRaster


class LectorPillow:
    """Lee dimensiones, modo y PPP disponibles de PNG/JPEG locales."""

    def leer(self, ruta: Path) -> ImagenRaster:
        try:
            with Image.open(ruta) as imagen:
                if imagen.format not in {"PNG", "JPEG"}:
                    raise ValueError("Solo se admiten imágenes PNG o JPEG")
                dato_ppp = imagen.info.get("dpi")
                ppp = None
                if isinstance(dato_ppp, (tuple, list)) and len(dato_ppp) == 2:
                    valores = tuple(float(valor) for valor in dato_ppp)
                    if all(math.isfinite(valor) and valor > 0 for valor in valores):
                        ppp = valores
                return ImagenRaster(
                    ancho_px=imagen.width,
                    alto_px=imagen.height,
                    modo_color=imagen.mode,
                    resolucion_ppp=ppp,
                )
        except UnidentifiedImageError as exc:
            raise ValueError(
                "El archivo no contiene una imagen PNG/JPEG válida"
            ) from exc

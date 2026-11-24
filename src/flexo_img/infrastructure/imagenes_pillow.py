"""Adaptador de infraestructura para metadatos raster mediante Pillow."""

from __future__ import annotations

import io
import math
import warnings
from hashlib import sha256
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from flexo_img.domain.imagen import ImagenRaster
from flexo_img.domain.validaciones import validar_limites_archivo


class LectorPillow:
    """Lee metadatos de PNG/JPEG sin modificar ni exportar el original."""

    def leer(self, ruta: Path) -> ImagenRaster:
        contenido = ruta.read_bytes()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(contenido)) as imagen:
                    if imagen.format not in {"PNG", "JPEG"}:
                        raise ValueError(
                            "Solo se admite contenido PNG/JPEG (PNG o JPEG)"
                        )
                    validar_limites_archivo(len(contenido), imagen.width, imagen.height)
                    imagen.load()
                    dato_ppp = imagen.info.get("dpi")
                    ppp = None
                    if isinstance(dato_ppp, (tuple, list)) and len(dato_ppp) == 2:
                        valores = tuple(float(valor) for valor in dato_ppp)
                        if all(math.isfinite(valor) and valor > 0 for valor in valores):
                            ppp = valores
                    icc = imagen.info.get("icc_profile")
                    return ImagenRaster(
                        ancho_px=imagen.width,
                        alto_px=imagen.height,
                        modo_color=imagen.mode,
                        resolucion_ppp=ppp,
                        formato_detectado=imagen.format,
                        canales=tuple(imagen.getbands()),
                        orientacion_exif=imagen.getexif().get(274),
                        transparencia="A" in imagen.getbands()
                        or "transparency" in imagen.info,
                        icc_sha256=sha256(icc).hexdigest() if icc else None,
                        tamano_bytes=len(contenido),
                        sha256=sha256(contenido).hexdigest(),
                    )
        except (
            UnidentifiedImageError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ) as exc:
            raise ValueError(
                "El archivo no contiene una imagen PNG/JPEG válida o excede los límites"
            ) from exc

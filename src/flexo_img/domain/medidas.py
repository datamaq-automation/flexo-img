"""Reglas geométricas puras para preprensa."""

from __future__ import annotations

import math

MM_POR_PULGADA = 25.4


def dimension_mm(pixeles: int, ppp: float) -> float:
    """Convierte píxeles a milímetros usando PPP ya conocidos del original."""
    if isinstance(pixeles, bool) or not isinstance(pixeles, int) or pixeles <= 0:
        raise ValueError("La cantidad de píxeles debe ser un entero positivo")
    if not math.isfinite(ppp) or ppp <= 0:
        raise ValueError("Los PPP deben ser positivos y finitos")
    return round(pixeles / ppp * MM_POR_PULGADA, 4)


def dimensiones_fisicas_mm(
    ancho_px: int, alto_px: int, resolucion_ppp: tuple[float, float] | None
) -> tuple[float, float] | None:
    """Devuelve ancho/alto físico; sin metadatos no inventa un tamaño."""
    if resolucion_ppp is None:
        return None
    if len(resolucion_ppp) != 2:
        raise ValueError("La resolución requiere PPP horizontal y vertical")
    return (
        dimension_mm(ancho_px, resolucion_ppp[0]),
        dimension_mm(alto_px, resolucion_ppp[1]),
    )

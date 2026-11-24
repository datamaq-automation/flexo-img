"""Conversión pura de unidades CSS de SVG a píxeles CSS."""

from __future__ import annotations

import math
import re

UNIDADES_CSS = {
    "": 1.0,
    "px": 1.0,
    "in": 96.0,
    "mm": 96 / 25.4,
    "cm": 96 / 2.54,
    "pt": 96 / 72,
    "pc": 16.0,
}


def longitud_svg_css_px(valor: str | None) -> float | None:
    if valor is None:
        return None
    coincidencia = re.fullmatch(r"\s*(\d*\.?\d+(?:[eE][+-]?\d+)?)\s*([a-z]*)\s*", valor)
    if not coincidencia or coincidencia[2] not in UNIDADES_CSS:
        return None
    resultado = float(coincidencia[1]) * UNIDADES_CSS[coincidencia[2]]
    return resultado if math.isfinite(resultado) and resultado > 0 else None

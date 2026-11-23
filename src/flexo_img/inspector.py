"""API de inspección de originales, sin generar archivos de salida."""

from pathlib import Path
from typing import Any

from flexo_img.inspeccion import inspeccionar


def inspeccionar_archivo(ruta_archivo: str | Path) -> dict[str, Any]:
    """Devuelve la ficha del original. La rasterización opcional vive en la CLI."""
    ruta = Path(ruta_archivo)
    return inspeccionar(ruta, ruta.parent)

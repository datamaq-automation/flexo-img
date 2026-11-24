"""API pública de inspección sin escritura de archivos."""

from pathlib import Path
from typing import Any

from flexo_img.adapters.controllers.inspeccionar_raster import (
    ControladorInspeccionarRaster,
)
from flexo_img.infrastructure.imagenes_pillow import LectorPillow


def inspeccionar_archivo(ruta_archivo: str | Path) -> dict[str, Any]:
    """Devuelve la ficha técnica de un PNG/JPEG sin generar salidas."""
    ruta = Path(ruta_archivo)
    try:
        return ControladorInspeccionarRaster(LectorPillow()).ejecutar(ruta)
    except (OSError, ValueError, RuntimeError) as exc:
        return {
            "archivo": ruta.name,
            "estado": "error",
            "aptitud_produccion": "no_evaluada",
            "rasterizacion": {"estado": "no_solicitada", "paginas": []},
            "error": f"{type(exc).__name__}: {exc}",
        }

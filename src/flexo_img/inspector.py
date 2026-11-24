"""API pública de inspección sin escritura de archivos."""

from hashlib import sha256
from pathlib import Path
from typing import Any

from flexo_img.adapters.controllers.inspeccionar_pdf import ControladorInspeccionarPDF
from flexo_img.adapters.controllers.inspeccionar_raster import (
    ControladorInspeccionarRaster,
)
from flexo_img.adapters.controllers.inspeccionar_svg import ControladorInspeccionarSVG
from flexo_img.infrastructure.imagenes_pillow import LectorPillow
from flexo_img.infrastructure.lector_pdf_pymupdf import LectorPDFPyMuPDF
from flexo_img.infrastructure.lector_svg import LectorSVGXML


def inspeccionar_archivo(ruta_archivo: str | Path) -> dict[str, Any]:
    """Devuelve la ficha técnica de un PNG/JPEG sin generar salidas."""
    ruta = Path(ruta_archivo)
    try:
        if ruta.suffix.lower() == ".pdf":
            return ControladorInspeccionarPDF(LectorPDFPyMuPDF()).ejecutar(ruta)
        if ruta.suffix.lower() == ".svg":
            return ControladorInspeccionarSVG(LectorSVGXML()).ejecutar(ruta)
        return ControladorInspeccionarRaster(LectorPillow()).ejecutar(ruta)
    except (OSError, ValueError, RuntimeError) as exc:
        return {
            "archivo": ruta.name,
            "sha256": sha256(ruta.read_bytes()).hexdigest() if ruta.is_file() else None,
            "estado": "error",
            "aptitud_produccion": "no_evaluada",
            "rasterizacion": {"estado": "no_solicitada", "paginas": []},
            "error": f"{type(exc).__name__}: {exc}",
        }

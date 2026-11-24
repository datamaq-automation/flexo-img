"""Controlador para la ficha de originales SVG."""

from pathlib import Path
from typing import Any

from flexo_img.application.inspeccionar_svg import LectorSVG, inspeccionar_svg


class ControladorInspeccionarSVG:
    def __init__(self, lector: LectorSVG) -> None:
        self._lector = lector

    def ejecutar(self, ruta: str | Path) -> dict[str, Any]:
        resultado = inspeccionar_svg(ruta, self._lector)
        return {
            "archivo": Path(ruta).name,
            "estado": "ok",
            "tamano_bytes": resultado.tamano_bytes,
            "sha256": resultado.sha256,
            "aptitud_produccion": "no_evaluada",
            "original": resultado.original,
            "avisos": list(resultado.avisos),
            "rasterizacion": {"estado": "no_solicitada", "paginas": []},
        }

"""Controlador para la ficha de documentos PDF."""

from pathlib import Path
from typing import Any

from flexo_img.application.inspeccionar_pdf import LectorPDF, inspeccionar_pdf


class ControladorInspeccionarPDF:
    def __init__(self, lector: LectorPDF) -> None:
        self._lector = lector

    def ejecutar(self, ruta: str | Path) -> dict[str, Any]:
        resultado = inspeccionar_pdf(ruta, self._lector)
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

"""Controlador de la inspección de originales PNG/JPEG."""

from pathlib import Path
from typing import Any

from flexo_img.adapters.presenters.informe_raster import presentar_informe_raster
from flexo_img.application.inspeccionar_imagen import LectorRaster
from flexo_img.application.inspeccionar_raster import inspeccionar_raster


class ControladorInspeccionarRaster:
    def __init__(self, lector: LectorRaster) -> None:
        self._lector = lector

    def ejecutar(self, ruta: str | Path) -> dict[str, Any]:
        resultado = inspeccionar_raster(ruta, self._lector)
        return presentar_informe_raster(ruta, resultado)

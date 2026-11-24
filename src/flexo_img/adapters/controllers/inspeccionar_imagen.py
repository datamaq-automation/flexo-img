"""Controlador que conecta una entrada con el caso de uso raster."""

from pathlib import Path

from flexo_img.adapters.presenters.ficha_imagen import presentar_ficha
from flexo_img.application.inspeccionar_imagen import LectorRaster, inspeccionar_imagen


class ControladorInspeccionarImagen:
    """Coordina el caso de uso y entrega el resultado al presentador."""

    def __init__(self, lector: LectorRaster) -> None:
        self._lector = lector

    def ejecutar(self, ruta: str | Path) -> dict[str, object]:
        ficha = inspeccionar_imagen(ruta, self._lector)
        return presentar_ficha(ficha)

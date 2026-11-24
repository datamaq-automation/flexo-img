from pathlib import Path

from flexo_img.adapters.controllers.inspeccionar_imagen import (
    ControladorInspeccionarImagen,
)
from flexo_img.domain.imagen import ImagenRaster


class LectorDePrueba:
    def leer(self, ruta: Path) -> ImagenRaster:
        return ImagenRaster(300, 300, "RGB", (300.0, 300.0))


def test_controlador_presenta_una_ficha_serializable():
    resultado = ControladorInspeccionarImagen(LectorDePrueba()).ejecutar("muestra.png")

    assert resultado == {
        "ancho_px": 300,
        "alto_px": 300,
        "modo_color": "RGB",
        "resolucion_ppp": [300.0, 300.0],
        "dimensiones_fisicas_mm": [25.4, 25.4],
    }

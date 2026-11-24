from pathlib import Path

from flexo_img.application.inspeccionar_imagen import inspeccionar_imagen
from flexo_img.domain.imagen import ImagenRaster


class LectorEnMemoria:
    """Doble del contrato: no usa archivos ni bibliotecas de imagen."""

    def leer(self, ruta: Path) -> ImagenRaster:
        assert ruta == Path("muestra.png")
        return ImagenRaster(300, 300, "RGB", (300.0, 300.0))


def test_caso_de_uso_puede_probarse_con_una_implementacion_de_prueba():
    ficha = inspeccionar_imagen("muestra.png", LectorEnMemoria())

    assert ficha.dimensiones_fisicas_mm == (25.4, 25.4)

import pytest

from flexo_img.domain.imagen import ImagenRaster
from flexo_img.domain.medidas import dimension_mm, dimensiones_fisicas_mm


def test_trescientos_pixeles_a_trescientos_ppp_miden_25_4_mm():
    imagen = ImagenRaster(300, 300, "RGB", (300.0, 300.0))

    assert dimensiones_fisicas_mm(
        imagen.ancho_px, imagen.alto_px, imagen.resolucion_ppp
    ) == (25.4, 25.4)


def test_sin_resolucion_no_inventa_dimension_fisica():
    assert dimensiones_fisicas_mm(300, 300, None) is None


@pytest.mark.parametrize("pixeles, ppp", [(0, 300), (300, 0), (300, float("inf"))])
def test_rechaza_medidas_invalidas(pixeles, ppp):
    with pytest.raises(ValueError):
        dimension_mm(pixeles, ppp)


def test_entidad_rechaza_dimensiones_invalidas():
    with pytest.raises(ValueError, match="enteros positivos"):
        ImagenRaster(0, 300, "RGB")


def test_entidad_rechaza_ppp_invalida():
    with pytest.raises(ValueError, match="dos PPP positivos"):
        ImagenRaster(300, 300, "RGB", (300.0, float("nan")))

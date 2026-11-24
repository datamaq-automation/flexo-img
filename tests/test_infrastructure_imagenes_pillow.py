from pathlib import Path

import pytest
from PIL import Image

from flexo_img.application.inspeccionar_imagen import inspeccionar_imagen
from flexo_img.infrastructure.imagenes_pillow import LectorPillow


def test_pillow_lee_png_y_calcula_dimension_fisica(tmp_path: Path):
    ruta = tmp_path / "muestra.png"
    Image.new("RGB", (300, 300), "white").save(ruta, dpi=(300, 300))

    ficha = inspeccionar_imagen(ruta, LectorPillow())

    assert ficha.original.ancho_px == 300
    assert ficha.original.resolucion_ppp == pytest.approx((300.0, 300.0), abs=0.001)
    assert ficha.dimensiones_fisicas_mm == pytest.approx((25.4, 25.4), abs=0.001)


def test_png_sin_ppp_no_inventa_tamano_fisico(tmp_path: Path):
    ruta = tmp_path / "sin-ppp.png"
    Image.new("RGB", (300, 300), "white").save(ruta)

    ficha = inspeccionar_imagen(ruta, LectorPillow())

    assert ficha.original.resolucion_ppp is None
    assert ficha.dimensiones_fisicas_mm is None


def test_pillow_rechaza_formato_no_admitido(tmp_path: Path):
    ruta = tmp_path / "muestra.gif"
    Image.new("RGB", (4, 4), "white").save(ruta)

    with pytest.raises(ValueError, match="PNG o JPEG"):
        LectorPillow().leer(ruta)


def test_pillow_rechaza_archivo_que_no_es_imagen(tmp_path: Path):
    ruta = tmp_path / "roto.png"
    ruta.write_text("no es una imagen")

    with pytest.raises(ValueError, match="imagen PNG/JPEG válida"):
        LectorPillow().leer(ruta)

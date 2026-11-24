"""Prueba el caso de uso con un doble y una conversión local."""

from pathlib import Path

import pytest
from PIL import Image

from flexo_img.application.convertir_cmyk import convertir_cmyk
from flexo_img.infrastructure.cmyk_pillow import ConversorPillow, lab_srgb

BASE = Path(__file__).resolve().parents[1]
RGB = BASE / "perfiles-icc/default_rgb.icc"
CMYK = BASE / "perfiles-icc/default_cmyk.icc"


class ConversorDoble:
    def __init__(self):
        self.argumentos = None

    def convertir(self, *args, **kwargs):
        self.argumentos = (args, kwargs)
        return {"estado": "demo"}


def test_caso_de_uso_delega_en_el_contrato_inyectado(tmp_path):
    doble = ConversorDoble()
    entrada, salida = tmp_path / "entrada.png", tmp_path / "salida"

    assert convertir_cmyk(doble, entrada, salida, CMYK, RGB, True) == {"estado": "demo"}
    assert doble.argumentos == ((entrada, salida, CMYK, RGB, True, False), {})


def test_cmyk_pillow_exporta_cuatro_canales_y_asume_srgb_solo_explicitamente(tmp_path):
    entrada = tmp_path / "muestra.png"
    Image.new("RGB", (2, 1), (255, 0, 0)).save(entrada)
    salida = tmp_path / "cmyk"

    with pytest.raises(ValueError, match="sin ICC"):
        convertir_cmyk(ConversorPillow(), entrada, salida, CMYK, RGB)

    informe = convertir_cmyk(ConversorPillow(), entrada, salida, CMYK, RGB, True)
    assert informe["estado"] == "demo"
    assert informe["perfil_entrada_origen"].startswith("sRGB_asumido")
    assert len(list(salida.glob("canal_*_gris_DEMO.png"))) == 4
    assert informe["perfil_salida_validado_para_maquina"] is False


def test_lab_srgb_conserva_referencia_y_delta_e_identidad():
    assert lab_srgb((255, 255, 255)) == pytest.approx((100, 0, 0), abs=0.002)

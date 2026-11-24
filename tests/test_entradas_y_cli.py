"""Rechazos de archivos reales y contratos CLI, sin red ni cambios de cobertura."""

import hashlib
from pathlib import Path

from PIL import Image

from flexo_img import inspeccion

BASE = Path(__file__).resolve().parent.parent
RGB = BASE / "perfiles-icc/default_rgb.icc"
CMYK = BASE / "perfiles-icc/default_cmyk.icc"


def test_gif_disfrazado_de_png_no_se_acepta(tmp_path):
    entrada = tmp_path / "disfrazado.png"
    Image.new("RGB", (2, 2), "red").save(entrada, format="GIF")
    antes = entrada.read_bytes()
    resultado = inspeccion.inspeccionar(entrada, tmp_path)
    assert resultado["estado"] == "error"
    assert "contenido PNG/JPEG" in resultado["error"]
    assert resultado["sha256"] == hashlib.sha256(antes).hexdigest()
    assert entrada.read_bytes() == antes


def test_xml_que_no_es_svg_se_rechaza(tmp_path):
    entrada = tmp_path / "otro.svg"
    entrada.write_text("<documento/>")
    resultado = inspeccion.inspeccionar(entrada, tmp_path)
    assert resultado["estado"] == "error"
    assert "El XML no es SVG" in resultado["error"]

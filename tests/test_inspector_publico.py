from pathlib import Path

import pytest
from PIL import Image

from flexo_img.inspector import inspeccionar_archivo


def test_api_publica_informa_medidas_y_preserva_el_original(tmp_path: Path):
    ruta = tmp_path / "imagen.png"
    Image.new("RGB", (300, 300), "white").save(ruta, dpi=(300, 300))
    original = ruta.read_bytes()

    ficha = inspeccionar_archivo(ruta)

    assert ficha["estado"] == "ok"
    assert ficha["aptitud_produccion"] == "no_evaluada"
    assert ficha["original"]["formato_detectado"] == "PNG"
    assert ficha["original"]["ancho_px"] == 300
    assert ficha["original"]["tamano_derivado_de_metadatos_mm"] == pytest.approx(
        [25.4, 25.4], abs=0.001
    )
    assert ruta.read_bytes() == original


def test_api_publica_devuelve_error_estructurado_para_archivo_roto(tmp_path: Path):
    ruta = tmp_path / "roto.png"
    ruta.write_text("no es una imagen")

    ficha = inspeccionar_archivo(ruta)

    assert ficha["estado"] == "error"
    assert ficha["aptitud_produccion"] == "no_evaluada"
    assert "error" in ficha


def test_api_indica_resolucion_desconocida_sin_metadatos(tmp_path: Path):
    ruta = tmp_path / "sin-ppp.png"
    Image.new("RGB", (12, 8), "white").save(ruta)

    ficha = inspeccionar_archivo(ruta)

    assert ficha["original"]["resolucion_metadatos_ppp"] is None
    assert ficha["original"]["tamano_derivado_de_metadatos_mm"] is None
    assert any("Sin resolución" in aviso for aviso in ficha["avisos"])


def test_api_avisa_si_extension_y_contenido_no_coinciden(tmp_path: Path):
    ruta = tmp_path / "imagen.jpg"
    Image.new("RGB", (12, 8), "white").save(ruta, format="PNG")

    ficha = inspeccionar_archivo(ruta)

    assert ficha["original"]["formato_detectado"] == "PNG"
    assert any("extensión difiere" in aviso for aviso in ficha["avisos"])

"""Rechazos de archivos reales y contratos CLI, sin red ni cambios de cobertura."""

import hashlib
from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from flexo_img import inspeccion

BASE = Path(__file__).resolve().parent.parent
RGB = BASE / "perfiles-icc/default_rgb.icc"
CMYK = BASE / "perfiles-icc/default_cmyk.icc"


@pytest.mark.parametrize(
    "dimensiones", [(0, 1), (-1, 1), (1, float("nan")), (float("inf"), 1)]
)
def test_dimensiones_no_finitas_o_no_positivas_se_rechazan(dimensiones):
    with pytest.raises(ValueError, match="Dimensiones no positivas o no finitas"):
        inspeccion.pixeles_permitidos(*dimensiones)


@pytest.mark.parametrize("medidas", [[0, 25.4], [-1, 25.4], [float("nan"), 1]])
def test_medidas_svg_invalidas_no_crean_salida(tmp_path, medidas):
    entrada = tmp_path / "logo.svg"
    entrada.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    salida = tmp_path / "sin-crear"
    with pytest.raises(ValueError, match="medidas positivas finitas"):
        inspeccion.inspeccionar(entrada, salida, 150, medidas)
    assert not salida.exists()


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


def test_svg_mixto_con_texto_e_imagen_danada_informa_advertencia(tmp_path):
    entrada = tmp_path / "mixto.svg"
    entrada.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        '<text x="0" y="5">A</text><rect width="1" height="1"/>'
        '<image href="data:image/png;base64,AAAA" width="10" height="10"/></svg>'
    )
    resultado = inspeccion.inspeccionar(entrada, tmp_path, 72)
    assert resultado["estado"] == "ok", resultado
    assert resultado["original"]["tipos_detectados"] == ["raster", "texto", "vector"]
    assert resultado["original"]["tipo_contenido"] == "mixto"
    assert any(
        "Advertencias del rasterizador SVG:" in aviso
        and "ignoring embedded image" in aviso
        for aviso in resultado["avisos"]
    )
    assert resultado["aptitud_produccion"] == "no_evaluada"
    assert (tmp_path / resultado["rasterizacion"]["paginas"][0]["archivo"]).exists()


def test_archivo_fuera_de_limite_conserva_entrada(tmp_path, monkeypatch):
    entrada = tmp_path / "foto.png"
    Image.new("RGB", (2, 2)).save(entrada)
    antes = entrada.read_bytes()
    monkeypatch.setattr(inspeccion, "MAX_BYTES", len(antes) - 1)
    resultado = inspeccion.inspeccionar(entrada, tmp_path)
    assert resultado["estado"] == "error"
    assert "límite local" in resultado["error"]
    assert "original" not in resultado
    assert entrada.read_bytes() == antes


@pytest.mark.parametrize("caso", ["cifrado", "exceso-paginas"])
def test_pdf_cifrado_o_con_demasiadas_paginas_no_se_rasteriza(
    tmp_path, monkeypatch, caso
):
    entrada = tmp_path / "documento.pdf"
    with pymupdf.open() as doc:
        doc.new_page()
        if caso == "cifrado":
            doc.save(
                entrada,
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                owner_pw="solo-prueba",
                user_pw="solo-prueba",
            )
        else:
            doc.new_page()
            doc.save(entrada)
            monkeypatch.setattr(inspeccion, "MAX_PAGINAS", 1)
    antes = entrada.read_bytes()
    resultado = inspeccion.inspeccionar(entrada, tmp_path, 72)
    assert resultado["estado"] == "error"
    assert "PDF cifrado, inválido o fuera del límite" in resultado["error"]
    assert resultado["rasterizacion"]["paginas"] == []
    assert entrada.read_bytes() == antes

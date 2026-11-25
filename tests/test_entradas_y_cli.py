"""Rechazos de archivos reales y contratos CLI, sin red ni cambios de cobertura."""

import hashlib
import json
import runpy
import sys
from pathlib import Path
from types import ModuleType

import pymupdf
import pytest
from PIL import Image, ImageCms

from flexo_img import color, inspeccion

BASE = Path(__file__).resolve().parent.parent
RGB = BASE / "perfiles-icc/default_rgb.icc"
CMYK = BASE / "perfiles-icc/default_cmyk.icc"


def ejecutar_cli(modulo: ModuleType, argumentos: list[str], monkeypatch):
    """Ejecuta el punto de entrada real bajo la instrumentación de pytest-cov."""
    monkeypatch.setattr(sys, "argv", [modulo.__file__, *argumentos])
    with pytest.raises(SystemExit) as salida:
        runpy.run_path(modulo.__file__, run_name="__main__")
    return salida.value.code


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


@pytest.mark.parametrize(
    "extra",
    [
        ["--dpi", "0"],
        ["--dpi", "1201"],
        ["--svg-mm", "25.4", "25.4"],
        ["--dpi", "72", "--svg-mm", "0", "25.4"],
    ],
)
def test_cli_inspeccion_rechaza_parametros_antes_de_escribir(
    tmp_path, monkeypatch, capsys, extra
):
    entrada = tmp_path / "original.png"
    Image.new("RGB", (2, 2)).save(entrada)
    salida = tmp_path / "sin-crear"
    assert (
        ejecutar_cli(
            inspeccion, [str(entrada), "--salida", str(salida), *extra], monkeypatch
        )
        == 2
    )
    assert "error:" in capsys.readouterr().err
    assert not salida.exists()


def test_cli_inspeccion_rechaza_carpeta_de_entrada(tmp_path, monkeypatch, capsys):
    entrada = tmp_path / "original.png"
    Image.new("RGB", (2, 2)).save(entrada)
    antes = entrada.read_bytes()
    assert (
        ejecutar_cli(inspeccion, [str(entrada), "--salida", str(tmp_path)], monkeypatch)
        == 2
    )
    assert "directorio de salida separado" in capsys.readouterr().err
    assert entrada.read_bytes() == antes
    assert not (tmp_path / "informe-entrada.json").exists()


def test_cli_inspeccion_no_sobrescribe_entrada_por_enlace_simbolico(
    tmp_path, monkeypatch, capsys
):
    entrada = tmp_path / "original.png"
    Image.new("RGB", (2, 2)).save(entrada)
    antes = entrada.read_bytes()
    salida = tmp_path / "salida"
    salida.mkdir()
    enlace = salida / "informe-entrada.json"
    enlace.symlink_to(entrada)
    assert (
        ejecutar_cli(inspeccion, [str(entrada), "--salida", str(salida)], monkeypatch)
        == 2
    )
    assert "no puede sobrescribir" in capsys.readouterr().err
    assert enlace.is_symlink()
    assert entrada.read_bytes() == antes


@pytest.mark.parametrize("ausente", [False, True], ids=["completo", "parcial"])
def test_cli_inspeccion_genera_informe_y_codigo_coherentes(
    tmp_path, monkeypatch, capsys, ausente
):
    entrada = tmp_path / "original.png"
    Image.new("RGB", (2, 2)).save(entrada)
    argumentos = [str(entrada)]
    if ausente:
        argumentos.append(str(tmp_path / "ausente.jpg"))
    salida = tmp_path / "informe"
    assert ejecutar_cli(
        inspeccion, [*argumentos, "--salida", str(salida)], monkeypatch
    ) == int(ausente)
    informe = json.loads((salida / "informe-entrada.json").read_text())
    assert [a["estado"] for a in informe["archivos"]] == (
        ["ok", "error"] if ausente else ["ok"]
    )
    assert (
        informe["archivos"][0]["sha256"]
        == hashlib.sha256(entrada.read_bytes()).hexdigest()
    )
    assert informe["generado_utc"].endswith("+00:00")
    assert str(salida / "informe-entrada.json") in capsys.readouterr().out


def test_color_limite_de_bytes_no_genera_salida(tmp_path, monkeypatch):
    entrada = tmp_path / "original.png"
    Image.new("RGB", (2, 2)).save(entrada)
    antes = entrada.read_bytes()
    monkeypatch.setattr(color, "MAX_BYTES", len(antes) - 1)
    salida = tmp_path / "sin-crear"
    with pytest.raises(ValueError, match="límite de recursos local"):
        color.convertir(entrada, salida, CMYK, RGB, True)
    assert not salida.exists()
    assert entrada.read_bytes() == antes


def test_color_referencia_rgb_sin_identidad_srgb_se_rechaza(tmp_path):
    # Solo cambia el nombre de un ICC RGB local; no simula el transformador.
    datos = (
        RGB.read_bytes()
        .replace(b"sRGB", b"demo")
        .replace("sRGB".encode("utf-16-be"), "demo".encode("utf-16-be"))
    )
    perfil = tmp_path / "rgb-sin-nombre-srgb.icc"
    perfil.write_bytes(datos)
    perfil_abierto = ImageCms.ImageCmsProfile(str(perfil))
    assert "srgb" not in ImageCms.getProfileDescription(perfil_abierto).lower()
    entrada = tmp_path / "original.png"
    Image.new("RGB", (2, 2)).save(entrada)
    salida = tmp_path / "sin-crear"
    with pytest.raises(ValueError, match="identificarse como sRGB"):
        color.convertir(entrada, salida, CMYK, perfil, True)
    assert not salida.exists()


@pytest.mark.parametrize("caso", ["sin-icc", "ausente", "perfil-corrupto"])
def test_cli_color_error_no_entrega_resultado_incompleto(
    tmp_path, monkeypatch, capsys, caso
):
    entrada = tmp_path / "original.png"
    Image.new("RGB", (2, 2)).save(entrada)
    perfil_rgb = RGB
    if caso == "ausente":
        entrada = tmp_path / "ausente.png"
    if caso == "perfil-corrupto":
        perfil_rgb = tmp_path / "corrupto.icc"
        perfil_rgb.write_bytes(b"no-es-un-perfil")
    salida = tmp_path / "sin-crear"
    argumentos = [
        str(entrada),
        "--salida",
        str(salida),
        "--perfil-cmyk",
        str(CMYK),
        "--perfil-srgb",
        str(perfil_rgb),
    ]
    assert ejecutar_cli(color, argumentos, monkeypatch) == 1
    assert "No se generó una entrega M2 completa:" in capsys.readouterr().err
    assert not salida.exists()


def test_cli_color_publica_resumen_y_entrega_consistentes(
    tmp_path, monkeypatch, capsys
):
    entrada = tmp_path / "original.png"
    Image.new("RGB", (2, 2), "red").save(entrada)
    antes = entrada.read_bytes()
    salida = tmp_path / "entrega"
    argumentos = [
        str(entrada),
        "--salida",
        str(salida),
        "--perfil-cmyk",
        str(CMYK),
        "--perfil-srgb",
        str(RGB),
        "--asumir-srgb",
    ]
    assert ejecutar_cli(color, argumentos, monkeypatch) == 0
    resumen = json.loads(capsys.readouterr().out)
    informe = json.loads((salida / "informe_M2.json").read_text())
    assert resumen == {
        "salida": str(salida),
        "estado": "demo",
        "deltaE76_media": informe["mediciones"]["deltaE76_srgb_D65_media"],
    }
    assert informe["entrada_sha256"] == hashlib.sha256(antes).hexdigest()
    assert informe["perfil_salida_validado_para_maquina"] is False
    assert len(list(salida.glob("canal_*_gris_DEMO.png"))) == 4
    assert len(list(salida.glob("canal_*_cobertura_DEMO.png"))) == 4
    assert entrada.read_bytes() == antes


def test_lotes_sucesivos_conservan_ambos_informes(tmp_path, monkeypatch):
    destino = tmp_path / "lotes"
    for nombre in ("uno", "dos"):
        ruta = tmp_path / f"{nombre}.png"
        Image.new("RGB", (3, 3)).save(ruta)
        assert (
            ejecutar_cli(inspeccion, [str(ruta), "--salida", str(destino)], monkeypatch)
            == 0
        )
    informes = sorted(destino.rglob("informe-entrada.json"))
    assert [json.loads(p.read_text())["archivos"][0]["archivo"] for p in informes] == [
        "uno.png",
        "dos.png",
    ]


def test_salida_archivo_se_conserva(tmp_path, monkeypatch):
    destino = tmp_path / "salidas" / "archivo"
    destino.parent.mkdir()
    destino.write_bytes(b"original")
    assert (
        ejecutar_cli(
            inspeccion, [str(tmp_path / "x"), "--salida", str(destino)], monkeypatch
        )
        == 2
    )
    assert destino.read_bytes() == b"original"

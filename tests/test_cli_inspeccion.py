import json
from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from flexo_img.inspeccion import inspeccionar, main, par_valido, pixeles_permitidos


def test_funciones_publicas_compatibles_delegan_al_dominio():
    assert par_valido([10, 20]) == [10.0, 20.0]
    assert par_valido([0, 20]) is None
    pixeles_permitidos(2, 2)


def test_inspeccionar_lote_escribe_json_y_salida_pdf(tmp_path: Path, capsys):
    archivo = tmp_path / "uno.pdf"
    documento = pymupdf.open()
    documento.new_page(width=72, height=72)
    documento.save(archivo)
    documento.close()
    salida = tmp_path / "resultado"

    assert main([str(archivo), "--salida", str(salida), "--dpi", "150"]) == 0
    informe = json.loads((salida / "informe-entrada.json").read_text())

    assert informe["archivos"][0]["original"]["numero_paginas"] == 1
    assert informe["archivos"][0]["rasterizacion"]["paginas"][0]["ppp_elegidos"] == 150
    assert "informe-entrada.json" in capsys.readouterr().out


def test_destino_existente_crea_lote_nuevo_y_conserva_el_anterior(tmp_path: Path):
    imagen = tmp_path / "entrada.png"
    Image.new("RGB", (3, 3), "white").save(imagen)
    salida = tmp_path / "salida"
    salida.mkdir()
    anterior = salida / "informe-entrada.json"
    anterior.write_text("conservar")

    assert main([str(imagen), "--salida", str(salida)]) == 0

    assert anterior.read_text() == "conservar"
    lotes = list(salida.glob("lote-*"))
    assert len(lotes) == 1
    assert (
        json.loads((lotes[0] / "informe-entrada.json").read_text())["archivos"][0][
            "estado"
        ]
        == "ok"
    )


def test_inspeccionar_funcion_publica_conserva_forma_de_resultado(tmp_path: Path):
    pdf = tmp_path / "a.pdf"
    doc = pymupdf.open()
    doc.new_page(width=72, height=72)
    doc.save(pdf)
    doc.close()

    resultado = inspeccionar(pdf, tmp_path / "render", 72)

    assert resultado["estado"] == "ok"
    assert resultado["rasterizacion"]["paginas"][0]["ancho_px"] == 72


def test_cli_rechaza_dpi_invalido_con_error_de_parser(tmp_path: Path):
    with pytest.raises(SystemExit) as error:
        main(["entrada.pdf", "--salida", str(tmp_path / "out"), "--dpi", "0"])

    assert error.value.code == 2


def test_cli_rechaza_svg_mm_no_finito(tmp_path: Path):
    with pytest.raises(SystemExit) as error:
        main(
            [
                "entrada.svg",
                "--salida",
                str(tmp_path / "out"),
                "--dpi",
                "72",
                "--svg-mm",
                "nan",
                "10",
            ]
        )

    assert error.value.code == 2


def test_cli_devuelve_codigo_no_cero_si_un_archivo_es_invalido(tmp_path: Path):
    archivo = tmp_path / "roto.svg"
    archivo.write_text("no es XML")

    assert main([str(archivo), "--salida", str(tmp_path / "out")]) == 1
    informe = json.loads((tmp_path / "out/informe-entrada.json").read_text())
    assert informe["archivos"][0]["estado"] == "error"

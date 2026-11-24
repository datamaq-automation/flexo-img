"""Pruebas offline del prototipo; los datos sintéticos no son evidencia de producción."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from flexo_img.inspeccion import (
    describir_pagina,
    inspeccionar,
    longitud_svg,
    par_valido,
)

PDF_REAL = Path(__file__).parent.parent / "evidencia/M1/entradas/documento-w3c.pdf"


@pytest.mark.parametrize("modo", ["RGB", "CMYK", "L"])
def test_jpeg_describe_modo_y_dpi_sin_convertir(tmp_path, modo):
    p = tmp_path / "foto.jpg"
    Image.new(modo, (300, 150)).save(p, dpi=(300, 150))
    antes = p.read_bytes()
    r = inspeccionar(p, tmp_path)
    assert r["estado"] == "ok"
    assert r["original"]["modo_color"] == modo
    assert r["original"]["resolucion_metadatos_ppp"] == [300, 150]
    assert r["original"]["tamano_derivado_de_metadatos_mm"] == [25.4, 25.4]
    assert r["aptitud_produccion"] == "no_evaluada"
    assert p.read_bytes() == antes


def test_png_sin_dpi_no_fabrica_resolucion_y_conserva_alpha(tmp_path):
    p = tmp_path / "alpha.png"
    Image.new("RGBA", (30, 20), (1, 2, 3, 0)).save(p)
    r = inspeccionar(p, tmp_path, 300)
    assert r["original"]["resolucion_metadatos_ppp"] is None
    assert r["original"]["tamano_derivado_de_metadatos_mm"] is None
    assert r["original"]["transparencia"] is True
    assert r["rasterizacion"]["estado"] == "no_aplica"


@pytest.mark.parametrize(
    "valor", [None, (0, 72), (-1, 72), (float("nan"), 72), (float("inf"), 72), "x"]
)
def test_dpi_invalido_es_desconocido(valor):
    assert par_valido(valor) is None


@pytest.mark.parametrize(
    "declarada,px",
    [
        ("25.4mm", 96),
        ("1in", 96),
        ("72pt", 96),
        ("96px", 96),
        ("96", 96),
        ("2.54cm", 96),
        ("6pc", 96),
    ],
)
def test_unidades_svg(declarada, px):
    assert longitud_svg(declarada) == pytest.approx(px)


@pytest.mark.parametrize("valor", ["50%", "auto", "-5mm", "0", None])
def test_svg_dimension_no_resuelta(valor):
    assert longitud_svg(valor) is None


def test_svg_viewbox_no_es_tamano_fisico(tmp_path):
    p = tmp_path / "logo.svg"
    p.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 80"><rect width="10" height="5"/></svg>'
    )
    r = inspeccionar(p, tmp_path)
    assert r["original"]["viewport_css_px"] is None
    assert r["original"]["resolucion_original_ppp"] is None
    assert inspeccionar(p, tmp_path, 150)["estado"] == "error"


@pytest.mark.parametrize("dpi", [72, 144])
def test_svg_rasterizado_dpi_elegido_no_original(tmp_path, dpi):
    p = tmp_path / "logo.svg"
    p.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1in" height="0.5in" viewBox="0 0 200 100"><rect width="200" height="100" fill="red"/></svg>'
    )
    r = inspeccionar(p, tmp_path, dpi)
    assert r["estado"] == "ok", r
    assert r["original"]["viewport_derivado_mm"] == [25.4, 12.7]
    assert r["original"]["resolucion_original_ppp"] is None
    out = r["rasterizacion"]["paginas"][0]
    assert [out["ancho_px"], out["alto_px"]] == [dpi, dpi // 2]
    with Image.open(tmp_path / out["archivo"]) as im:
        assert im.info["dpi"] == pytest.approx((dpi, dpi), abs=0.02)
        assert im.mode == "RGB"


@pytest.mark.parametrize(
    "contenido",
    [
        "<script>alert(1)</script>",
        "<foreignObject/>",
        '<image href="https://example.test/foto.png"/>',
        '<image href="file:///etc/passwd"/>',
        '<rect onload="alert(1)"/>',
        '<style>@import "https://example.test/x.css";</style>',
        '<rect fill="url(https://example.test/a)"/>',
    ],
)
def test_svg_no_resuelve_recursos_externos_ni_ejecuta_contenido(tmp_path, contenido):
    p = tmp_path / "logo.svg"
    p.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
        + contenido
        + "</svg>"
    )
    assert inspeccionar(p, tmp_path)["estado"] == "error"


def test_svg_entidad_externa_rechazada(tmp_path):
    p = tmp_path / "entidad.svg"
    p.write_text(
        '<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg>&x;</svg>'
    )
    assert inspeccionar(p, tmp_path)["estado"] == "error"


@pytest.mark.parametrize("dpi", [None, 72, 144])
def test_pdf_real_dimension_contenido_y_raster_separados(tmp_path, dpi):
    r = inspeccionar(PDF_REAL, tmp_path, dpi)
    assert r["estado"] == "ok", r
    assert r["original"]["numero_paginas"] == 1
    assert r["original"]["resolucion_original_ppp"] is None
    page = r["original"]["paginas"][0]
    assert "texto" in page["tipos_detectados"]
    assert page["caja_visible_pt"] == pytest.approx([595, 842])
    if dpi:
        out = r["rasterizacion"]["paginas"][0]
        assert out["ppp_elegidos"] == dpi
        assert out["ancho_px"] == pytest.approx(595 * dpi / 72, abs=1)
        assert out["alto_px"] == pytest.approx(842 * dpi / 72, abs=1)
    else:
        assert r["rasterizacion"]["estado"] == "no_solicitada"


def test_pdf_ppp_embebidos_depende_de_colocacion_no_del_render():
    page = SimpleNamespace(
        number=0,
        rect=SimpleNamespace(width=72, height=144),
        rotation=0,
        get_text=lambda _: [],
        get_drawings=list,
        get_image_info=lambda: [
            {
                "transform": (0, 72, -144, 0, 0, 0),
                "width": 300,
                "height": 600,
                "cs-name": "DeviceRGB",
            }
        ],
    )
    info = describir_pagina(page)
    assert info["imagenes_embebidas"][0]["ppp_efectivos_por_colocacion"] == [300, 300]
    assert info["tipo_contenido"] == "raster"


@pytest.mark.parametrize(
    "nombre,datos",
    [("roto.pdf", b"%PDF-roto"), ("roto.jpg", b"basura"), ("archivo.txt", b"texto")],
)
def test_archivo_roto_o_no_admitido_no_parece_ok(tmp_path, nombre, datos):
    p = tmp_path / nombre
    p.write_bytes(datos)
    r = inspeccionar(p, tmp_path)
    assert r["estado"] == "error"
    assert r["aptitud_produccion"] == "no_evaluada"


def test_png_disfrazado_no_pierde_formato_detectado(tmp_path):
    p = tmp_path / "foto.jpg"
    Image.new("RGB", (5, 5)).save(p, format="PNG")
    r = inspeccionar(p, tmp_path)
    assert r["original"]["formato_detectado"] == "PNG"
    assert any("extensión" in a for a in r["avisos"])


def test_cli_informe_parcial_conserva_archivo_valido_y_sha(tmp_path):
    p = tmp_path / "foto.png"
    Image.new("RGB", (5, 5)).save(p)
    out = tmp_path / "resultado"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "flexo_img.inspeccion",
            str(p),
            str(tmp_path / "ausente.png"),
            "--salida",
            str(out),
        ],
        capture_output=True,
        check=False,
    )
    assert r.returncode == 1
    informe = json.loads((out / "informe-entrada.json").read_text())
    assert [x["estado"] for x in informe["archivos"]] == ["ok", "error"]
    assert (
        informe["archivos"][0]["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    )


@pytest.mark.parametrize("dpi", [0, -1, 1201, True])
def test_rasterizacion_no_acepta_resolucion_invalida(tmp_path, dpi):
    with pytest.raises(ValueError):
        inspeccionar(PDF_REAL, tmp_path, dpi)


def test_limite_de_pixeles_no_es_certificacion_de_imprenta(tmp_path, monkeypatch):
    p = tmp_path / "grande.png"
    Image.new("RGB", (10, 10)).save(p)
    monkeypatch.setattr("flexo_img.inspeccion.MAX_PIXELES", 50)
    assert inspeccionar(p, tmp_path)["estado"] == "error"


def test_svg_tamano_elegido_no_se_atribuye_al_original(tmp_path):
    p = tmp_path / "porcentual.svg"
    p.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" viewBox="0 0 300 300"><rect width="300" height="300" fill="blue"/></svg>'
    )
    r = inspeccionar(p, tmp_path, 150, [25.4, 25.4])
    assert r["estado"] == "ok", r
    assert r["original"]["ancho_declarado"] == "100%"
    assert r["original"]["viewport_css_px"] is None
    assert r["rasterizacion"]["tamano_salida_mm_elegido"] == [25.4, 25.4]
    assert r["rasterizacion"]["paginas"][0]["ancho_px"] == 150


def test_fallo_de_render_conserva_inspeccion_original(tmp_path):
    p = tmp_path / "sin-tamano.svg"
    p.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"/>')
    r = inspeccionar(p, tmp_path, 150)
    assert r["estado"] == "error"
    assert r["original"]["viewBox"] == "0 0 20 20"


def test_no_sobrescribe_raster_existente(tmp_path):
    r = inspeccionar(PDF_REAL, tmp_path, 72)
    out = tmp_path / r["rasterizacion"]["paginas"][0]["archivo"]
    antes = out.read_bytes()
    assert inspeccionar(PDF_REAL, tmp_path, 72)["estado"] == "error"
    assert out.read_bytes() == antes


def test_logo_real_con_referencias_internas_conserva_colores(tmp_path):
    logo = PDF_REAL.with_name("logo-svg.svg")
    r = inspeccionar(logo, tmp_path, 150, [50, 50])
    assert r["estado"] == "ok", r
    with Image.open(tmp_path / r["rasterizacion"]["paginas"][0]["archivo"]) as im:
        assert list(im.convert("RGB").get_flattened_data()).count((255, 177, 59)) > 1000


def test_pdf_mixto_real_distingue_colocacion_y_render(tmp_path):
    import io

    import pymupdf

    imagen = io.BytesIO()
    Image.new("RGB", (100, 100), "red").save(imagen, format="PNG")
    p = tmp_path / "mixto.pdf"
    with pymupdf.open() as doc:
        pagina = doc.new_page(width=144, height=144)
        pagina.draw_rect(pymupdf.Rect(0, 0, 144, 144))
        pagina.insert_image(pymupdf.Rect(0, 0, 72, 72), stream=imagen.getvalue())
        doc.save(p)
    info = inspeccionar(p, tmp_path / "salida")
    pagina = info["original"]["paginas"][0]
    assert pagina["tipo_contenido"] == "mixto"
    assert pagina["imagenes_embebidas"][0]["ppp_efectivos_por_colocacion"] == [100, 100]
    assert "RGB" in pagina["imagenes_embebidas"][0]["espacio_color"]


@pytest.mark.parametrize("referencia", ["url(#g)", "url('#g')", 'url( "#g" )'])
def test_gradiente_svg_local(tmp_path, referencia):
    from xml.etree.ElementTree import Element, ElementTree, SubElement

    raiz = Element("svg", xmlns="http://www.w3.org/2000/svg", width="10", height="10")
    gradiente = SubElement(SubElement(raiz, "defs"), "linearGradient", id="g")
    SubElement(gradiente, "stop", offset="0", attrib={"stop-color": "red"})
    SubElement(raiz, "rect", width="10", height="10", fill=referencia)
    ruta = tmp_path / "gradiente.svg"
    ElementTree(raiz).write(ruta)
    ficha = inspeccionar(ruta, tmp_path, 96)
    assert ficha["estado"] == "ok"
    pagina = ficha["rasterizacion"]["paginas"][0]
    with Image.open(tmp_path / pagina["archivo"]) as imagen:
        assert imagen.getpixel((4, 4)) == (255, 0, 0)


def test_error_segunda_pagina_permite_reintento(tmp_path, monkeypatch):
    import pymupdf

    origen = tmp_path / "dos.pdf"
    with pymupdf.open() as doc:
        for ancho in (20, 40):
            doc.new_page(width=ancho, height=ancho)
        doc.save(origen)
    monkeypatch.setattr("flexo_img.inspeccion.MAX_PIXELES", 900)
    assert inspeccionar(origen, tmp_path, 72)["estado"] == "error"
    assert list(tmp_path.glob("*.png")) == []
    ficha = inspeccionar(origen, tmp_path, 36)
    assert ficha["estado"] == "ok"
    assert len(list(tmp_path.glob("*.png"))) == 2
    monkeypatch.setattr("flexo_img.inspeccion.MAX_PIXELES", 2000)
    assert inspeccionar(origen, tmp_path, 72)["estado"] == "ok"

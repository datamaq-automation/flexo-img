from pathlib import Path

import pymupdf
from PIL import Image

from flexo_img.adapters.controllers.inspeccionar_pdf import ControladorInspeccionarPDF
from flexo_img.infrastructure.lector_pdf_pymupdf import LectorPDFPyMuPDF
from flexo_img.inspector import inspeccionar_archivo


def test_inspecciona_pdf_mixto_sin_inventar_dpi(tmp_path: Path):
    ruta = tmp_path / "mixto.pdf"
    imagen = tmp_path / "imagen.png"
    Image.new("RGB", (20, 10), "red").save(imagen)
    documento = pymupdf.open()
    pagina = documento.new_page(width=72, height=72)
    pagina.insert_text((10, 20), "Muestra")
    pagina.draw_rect(pymupdf.Rect(10, 30, 40, 50))
    pagina.insert_image(pymupdf.Rect(10, 55, 40, 70), filename=str(imagen))
    documento.save(ruta)
    documento.close()

    ficha = ControladorInspeccionarPDF(LectorPDFPyMuPDF()).ejecutar(ruta)
    pagina_informe = ficha["original"]["paginas"][0]

    assert ficha["estado"] == "ok"
    assert ficha["original"]["resolucion_original_ppp"] is None
    assert ficha["original"]["paginas"][0]["caja_visible_mm"] == [25.4, 25.4]
    assert pagina_informe["tipo_contenido"] == "mixto"
    assert {"texto", "vector", "raster"}.issubset(pagina_informe["tipos_detectados"])
    assert pagina_informe["imagenes_embebidas"][0]["ppp_efectivos_por_colocacion"]
    assert ficha["aptitud_produccion"] == "no_evaluada"


def test_pdf_danado_se_informa_como_error(tmp_path: Path):
    ruta = tmp_path / "roto.pdf"
    ruta.write_bytes(b"no es PDF")

    ficha = inspeccionar_archivo(ruta)

    assert ficha["estado"] == "error"
    assert "error" in ficha


def test_pdf_mas_largo_que_el_limite_local_se_rechaza(tmp_path: Path):
    ruta = tmp_path / "muchas-paginas.pdf"
    documento = pymupdf.open()
    for _ in range(21):
        documento.new_page()
    documento.save(ruta)
    documento.close()

    ficha = inspeccionar_archivo(ruta)

    assert ficha["estado"] == "error"
    assert "20 páginas" in ficha["error"]

from pathlib import Path

import pymupdf
import pytest
from PIL import Image

from flexo_img.application.rasterizar_original import rasterizar_original
from flexo_img.infrastructure.pymupdf_rasterizador import RasterizadorPyMuPDF


class RasterizadorDePrueba:
    def pdf(self, ruta, salida, prefijo, ppp):
        return [{"archivo": f"{prefijo}-{ppp}.png"}]

    def svg(self, ruta, salida, prefijo, ppp, medidas_mm):
        return [{"archivo": f"{prefijo}-{ppp}.png", "medidas": medidas_mm}]


def test_caso_de_uso_inyecta_rasterizador_y_parametros(tmp_path: Path):
    resultado = rasterizar_original(
        "entrada.pdf", tmp_path, "demo", 300, RasterizadorDePrueba()
    )

    assert resultado.estado == "generada"
    assert resultado.paginas == ({"archivo": "demo-300.png"},)


def test_rechaza_ppp_invalidos_antes_de_invocar_rasterizador(tmp_path: Path):
    with pytest.raises(ValueError, match="entre 1 y 1200"):
        rasterizar_original("entrada.pdf", tmp_path, "demo", 0, RasterizadorDePrueba())


def test_rasteriza_pdf_con_ppp_elegidos(tmp_path: Path):
    ruta = tmp_path / "muestra.pdf"
    documento = pymupdf.open()
    documento.new_page(width=72, height=72)
    documento.save(ruta)
    documento.close()

    resultado = rasterizar_original(
        ruta, tmp_path / "salida", "m", 150, RasterizadorPyMuPDF()
    )

    assert resultado.paginas[0]["ppp_elegidos"] == 150
    assert resultado.paginas[0]["origen_resolucion"].startswith("parametro")
    assert (tmp_path / "salida/m-p1-150ppp.png").exists()


def test_rasteriza_svg_con_gradiente_y_preserva_sus_colores(tmp_path: Path):
    ruta = tmp_path / "gradiente.svg"
    ruta.write_text(
        "<svg xmlns='http://www.w3.org/2000/svg' width='25.4mm' height='25.4mm'><defs><linearGradient id='g'><stop offset='0' stop-color='red'/><stop offset='1' stop-color='blue'/></linearGradient></defs><rect width='100%' height='100%' fill='url(#g)'/></svg>"
    )

    resultado = rasterizar_original(
        ruta, tmp_path / "salida", "g", 72, RasterizadorPyMuPDF()
    )
    imagen = Image.open(tmp_path / "salida/g-p1-72ppp.png").convert("RGB")

    assert resultado.paginas[0]["ancho_px"] == 72
    assert imagen.getpixel((5, 35))[0] > imagen.getpixel((65, 35))[0]
    assert imagen.getpixel((65, 35))[2] > imagen.getpixel((5, 35))[2]


def test_rasterizador_elimina_archivos_parciales_ante_error(tmp_path: Path):
    ruta = tmp_path / "dos.pdf"
    documento = pymupdf.open()
    documento.new_page(width=72, height=72)
    documento.new_page(width=72, height=72)
    documento.save(ruta)
    documento.close()
    destino = tmp_path / "salida"
    destino.mkdir()
    (destino / "demo-p2-72ppp.png").write_bytes(b"ocupado")

    with pytest.raises(FileExistsError):
        rasterizar_original(ruta, destino, "demo", 72, RasterizadorPyMuPDF())

    assert not (destino / "demo-p1-72ppp.png").exists()
    assert (destino / "demo-p2-72ppp.png").read_bytes() == b"ocupado"


def test_no_rasteriza_una_imagen_que_ya_es_raster(tmp_path: Path):
    resultado = rasterizar_original(
        "muestra.png", tmp_path, "r", 300, RasterizadorDePrueba()
    )

    assert resultado.estado == "no_aplica"
    assert resultado.paginas == ()


def test_rechaza_formato_no_admitido_para_rasterizar(tmp_path: Path):
    with pytest.raises(ValueError, match="Formato no admitido"):
        rasterizar_original("muestra.gif", tmp_path, "r", 300, RasterizadorDePrueba())

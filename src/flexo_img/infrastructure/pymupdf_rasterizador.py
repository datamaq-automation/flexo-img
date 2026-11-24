"""Rasterización local de PDF/SVG; las salidas son DEMO."""

from __future__ import annotations

import xml.etree.ElementTree as StdET
from pathlib import Path

import pymupdf
import resvg_py
from defusedxml import ElementTree as ET

from flexo_img.domain.unidades_svg import longitud_svg_css_px
from flexo_img.domain.validaciones import validar_limites_archivo
from flexo_img.infrastructure.lector_svg import LectorSVGXML


class RasterizadorPyMuPDF:
    def pdf(
        self, ruta: Path, salida: Path, prefijo: str, ppp: int
    ) -> list[dict[str, object]]:
        with pymupdf.open(ruta) as documento:
            return self._renderizar(documento, salida, prefijo, ppp)

    def svg(
        self,
        ruta: Path,
        salida: Path,
        prefijo: str,
        ppp: int,
        medidas_mm: tuple[float, float] | None,
    ) -> list[dict[str, object]]:
        LectorSVGXML().leer(ruta)
        raiz = ET.fromstring(ruta.read_bytes())
        ancho = longitud_svg_css_px(raiz.get("width"))
        alto = longitud_svg_css_px(raiz.get("height"))
        if medidas_mm is not None:
            if any(n <= 0 for n in medidas_mm):
                raise ValueError(
                    "El tamaño de salida SVG requiere dos medidas positivas"
                )
            raiz.set("width", f"{medidas_mm[0]}mm")
            raiz.set("height", f"{medidas_mm[1]}mm")
        elif not ancho or not alto:
            raise ValueError(
                "Para rasterizar SVG faltan dimensiones absolutas; viewBox no fija tamaño físico"
            )
        StdET.register_namespace("", "http://www.w3.org/2000/svg")
        StdET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
        xml = StdET.tostring(raiz, encoding="unicode")
        with pymupdf.open(stream=xml.encode(), filetype="svg") as svg_doc:
            contenido_pdf = svg_doc.convert_to_pdf()
        with pymupdf.open(stream=contenido_pdf, filetype="pdf") as documento:
            tiene_gradiente = any(
                nodo.tag.split("}")[-1] in {"linearGradient", "radialGradient"}
                for nodo in raiz.iter()
            )
            return self._renderizar(
                documento, salida, prefijo, ppp, xml if tiene_gradiente else None
            )

    def _renderizar(
        self,
        documento: pymupdf.Document,
        salida: Path,
        prefijo: str,
        ppp: int,
        svg_gradiente: str | None = None,
    ) -> list[dict[str, object]]:
        paginas = []
        creados: list[Path] = []
        salida.mkdir(parents=True, exist_ok=True)
        try:
            for pagina in documento:
                ancho_px = round(pagina.rect.width * ppp / 72)
                alto_px = round(pagina.rect.height * ppp / 72)
                validar_limites_archivo(1, ancho_px, alto_px)
                if svg_gradiente is None:
                    pix = pagina.get_pixmap(
                        dpi=ppp, colorspace=pymupdf.csRGB, alpha=False
                    )
                else:
                    caja = (pagina.rect * pymupdf.Matrix(ppp / 72, ppp / 72)).irect
                    raiz = ET.fromstring(svg_gradiente)
                    ancho_css = longitud_svg_css_px(raiz.get("width"))
                    alto_css = longitud_svg_css_px(raiz.get("height"))
                    if raiz.get("viewBox") is None and ancho_css and alto_css:
                        raiz.set("viewBox", f"0 0 {ancho_css} {alto_css}")
                    raiz.set("width", f"{caja.width}px")
                    raiz.set("height", f"{caja.height}px")
                    StdET.register_namespace("", "http://www.w3.org/2000/svg")
                    StdET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
                    svg_render = StdET.tostring(raiz, encoding="unicode")
                    png = resvg_py.svg_to_bytes(
                        svg_string=svg_render,
                        width=caja.width,
                        height=caja.height,
                        background="white",
                    )
                    pix = pymupdf.Pixmap(pymupdf.Pixmap(png), 0)
                    pix.set_dpi(ppp, ppp)
                nombre = f"{prefijo}-p{pagina.number + 1}-{ppp}ppp.png"
                destino = salida / nombre
                with destino.open("xb") as archivo:
                    creados.append(destino)
                    archivo.write(pix.tobytes("png"))
                paginas.append(
                    {
                        "pagina": pagina.number + 1,
                        "archivo": nombre,
                        "ppp_elegidos": ppp,
                        "ancho_px": pix.width,
                        "alto_px": pix.height,
                        "modo_color": "RGB",
                        "fondo": "blanco",
                        "origen_resolucion": "parametro_de_rasterizacion_no_dato_original",
                    }
                )
        except Exception:
            for archivo in creados:
                archivo.unlink(missing_ok=True)
            raise
        return paginas

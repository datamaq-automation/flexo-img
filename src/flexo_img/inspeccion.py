"""Inspección local de entrada; no convierte a CMYK ni certifica una plancha."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import register_namespace

import pymupdf
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException
from PIL import Image

MAX_BYTES = 25 * 1024 * 1024
MAX_PIXELES = 20_000_000
MAX_PAGINAS = 20
UNIDADES = {
    "": 1,
    "px": 1,
    "in": 96,
    "mm": 96 / 25.4,
    "cm": 96 / 2.54,
    "pt": 96 / 72,
    "pc": 16,
}


def par_valido(valor: Any) -> list[float] | None:
    try:
        par = [float(valor[0]), float(valor[1])]
        return par if all(math.isfinite(x) and x > 0 for x in par) else None
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def pixeles_permitidos(ancho: float, alto: float) -> None:
    if not all(math.isfinite(x) and x > 0 for x in (ancho, alto)):
        raise ValueError("Dimensiones no positivas o no finitas")
    if math.ceil(ancho) * math.ceil(alto) > MAX_PIXELES:
        raise ValueError(
            "Se supera el límite local de píxeles; no es un umbral de imprenta"
        )


def raster(path: Path) -> tuple[dict[str, Any], list[str]]:
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as im:
            if im.format not in ("PNG", "JPEG"):
                raise ValueError(
                    "La extensión no corresponde a contenido PNG/JPEG admitido"
                )
            pixeles_permitidos(*im.size)
            im.load()
            dpi = par_valido(im.info.get("dpi"))
            icc = im.info.get("icc_profile")
            original = {
                "formato_detectado": im.format,
                "tipo_contenido": "raster",
                "ancho_px": im.width,
                "alto_px": im.height,
                "modo_color": im.mode,
                "canales": list(im.getbands()),
                "resolucion_metadatos_ppp": dpi,
                "tamano_derivado_de_metadatos_mm": [
                    round(n / d * 25.4, 4) for n, d in zip(im.size, dpi, strict=True)
                ]
                if dpi
                else None,
                "orientacion_exif": im.getexif().get(274),
                "transparencia": "A" in im.getbands() or "transparency" in im.info,
                "icc_presente": bool(icc),
                "icc_sha256": hashlib.sha256(icc).hexdigest() if icc else None,
                "fotografia_o_logo": "no_inferido",
            }
            avisos = [
                "El tamaño físico derivado depende de metadatos; falta confirmar tamaño de impresión."
            ]
            if dpi is None:
                avisos.append(
                    "Sin resolución física verificable: no se supone 72, 96 ni 300 ppp."
                )
            esperado = "JPEG" if path.suffix.lower() in (".jpg", ".jpeg") else "PNG"
            if im.format != esperado:
                avisos.append("La extensión difiere del formato detectado.")
            return original, avisos


def describir_pagina(page: Any) -> dict[str, Any]:
    imagenes = []
    for info in page.get_image_info():
        a, b, c, d, _, _ = info["transform"]
        ancho, alto = math.hypot(a, b), math.hypot(c, d)
        imagenes.append(
            {
                "ancho_px": info["width"],
                "alto_px": info["height"],
                "espacio_color": info.get("cs-name"),
                "ppp_efectivos_por_colocacion": [
                    round(info["width"] * 72 / ancho, 4),
                    round(info["height"] * 72 / alto, 4),
                ]
                if ancho > 0 and alto > 0
                else None,
            }
        )
    texto = bool(page.get_text("words"))
    vector = bool(page.get_drawings())
    tipos = [
        n
        for n, v in (("texto", texto), ("vector", vector), ("raster", bool(imagenes)))
        if v
    ]
    return {
        "pagina": page.number + 1,
        "caja_visible_pt": [page.rect.width, page.rect.height],
        "caja_visible_mm": [
            round(x * 25.4 / 72, 4) for x in (page.rect.width, page.rect.height)
        ],
        "rotacion_grados": page.rotation,
        "tipos_detectados": tipos,
        "tipo_contenido": "mixto"
        if len(tipos) > 1
        else (tipos[0] if tipos else "no_detectado"),
        "imagenes_embebidas": imagenes,
    }


def longitud_svg(valor: str | None) -> float | None:
    if valor is None:
        return None
    m = re.fullmatch(r"\s*(\d*\.?\d+(?:[eE][+-]?\d+)?)\s*([a-z]*)\s*", valor)
    if not m or m[2] not in UNIDADES:
        return None
    n = float(m[1]) * UNIDADES[m[2]]
    return n if math.isfinite(n) and n > 0 else None


def svg(path: Path) -> tuple[dict[str, Any], list[str]]:
    root = ET.fromstring(path.read_bytes())
    if root.tag.split("}")[-1] != "svg":
        raise ValueError("El XML no es SVG")
    tipos: set[str] = set()
    for node in root.iter():
        tag = node.tag.split("}")[-1]
        if tag in ("script", "foreignObject"):
            raise ValueError("SVG activo no admitido en este prototipo")
        if tag in (
            "path",
            "rect",
            "circle",
            "ellipse",
            "polygon",
            "polyline",
            "line",
            "use",
        ):
            tipos.add("vector")
        if tag in ("text", "tspan"):
            tipos.add("texto")
        if tag == "image":
            tipos.add("raster")
        for key, value in node.attrib.items():
            if key.split("}")[-1] == "href" and not value.startswith(
                ("#", "data:image/")
            ):
                raise ValueError(
                    "SVG con referencia externa: no se resuelve red ni archivos"
                )
            if key.lower().startswith("on"):
                raise ValueError("SVG con eventos activos no admitido")
        css = " ".join(node.attrib.values()) + (node.text or "")
        if "@import" in css or re.search(
            r"url\(\s*['\"]?(?!#)[^)]", css, re.IGNORECASE
        ):
            raise ValueError("SVG con recurso CSS externo no admitido")
    w, h = longitud_svg(root.get("width")), longitud_svg(root.get("height"))
    original = {
        "formato_detectado": "SVG",
        "ancho_declarado": root.get("width"),
        "alto_declarado": root.get("height"),
        "viewBox": root.get("viewBox"),
        "viewport_css_px": [w, h] if w and h else None,
        "viewport_derivado_mm": [round(x * 25.4 / 96, 4) for x in (w, h)]
        if w and h
        else None,
        "resolucion_original_ppp": None,
        "tipos_detectados": sorted(tipos),
        "tipo_contenido": "mixto"
        if len(tipos) > 1
        else next(iter(tipos), "no_detectado"),
        "modo_color": "declaraciones SVG/CSS; perfil de salida no verificado",
    }
    return original, [
        "96 px por pulgada es la equivalencia CSS usada, no resolución del original.",
        "La detección de contenido es orientativa; no verifica fuentes, tintas planas ni sobreimpresión.",
    ]


def renderizar(doc: Any, dpi: int, destino: Path, prefijo: str) -> list[dict[str, Any]]:
    resultados = []
    for page in doc:
        pixeles_permitidos(page.rect.width * dpi / 72, page.rect.height * dpi / 72)
        pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
        nombre = f"{prefijo}-p{page.number + 1}-{dpi}ppp.png"
        if (destino / nombre).exists():
            raise FileExistsError(
                "La rasterización ya existe; use otro directorio de salida"
            )
        pix.save(destino / nombre)
        resultados.append(
            {
                "pagina": page.number + 1,
                "archivo": nombre,
                "ppp_elegidos": dpi,
                "ancho_px": pix.width,
                "alto_px": pix.height,
                "modo_color": "RGB",
                "fondo": "blanco",
                "origen_resolucion": "parametro_de_rasterizacion_no_dato_original",
            }
        )
    return resultados


def inspeccionar(
    path: Path, salida: Path, dpi: int | None = None, svg_mm: list[float] | None = None
) -> dict[str, Any]:
    if dpi is not None and (
        isinstance(dpi, bool) or not isinstance(dpi, int) or not 1 <= dpi <= 1200
    ):
        raise ValueError(
            "La rasterización requiere ppp enteros entre 1 y 1200 (límite local)"
        )
    if svg_mm is not None and par_valido(svg_mm) is None:
        raise ValueError(
            "El tamaño SVG de salida requiere dos medidas positivas finitas"
        )
    informe: dict[str, Any] = {
        "archivo": path.name,
        "estado": "error",
        "aptitud_produccion": "no_evaluada",
        "rasterizacion": {"estado": "no_solicitada", "paginas": []},
    }
    try:
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("Archivo mayor al límite local de 25 MiB")
        data = path.read_bytes()
        informe.update(tamano_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        suffix = path.suffix.lower()
        if suffix in (".jpg", ".jpeg", ".png"):
            original, avisos = raster(path)
            if dpi:
                avisos.append(
                    "No se remuestrea raster: elegir ppp no agrega detalle al original."
                )
                informe["rasterizacion"]["estado"] = "no_aplica"
        elif suffix == ".svg":
            original, avisos = svg(path)
            informe.update(original=original, avisos=avisos)
            if dpi:
                pymupdf.TOOLS.mupdf_warnings(reset=True)
                if svg_mm is not None:
                    register_namespace("", "http://www.w3.org/2000/svg")
                    register_namespace("xlink", "http://www.w3.org/1999/xlink")
                    root = ET.fromstring(data)
                    root.set("width", f"{svg_mm[0]}mm")
                    root.set("height", f"{svg_mm[1]}mm")
                    data = ET.tostring(root)
                    avisos.append(
                        "Tamaño de salida elegido por operador; no es tamaño del original. Puede cambiar relación de aspecto."
                    )
                if svg_mm is None and original["viewport_css_px"] is None:
                    raise ValueError(
                        "Para rasterizar SVG faltan dimensiones absolutas del viewport; viewBox no fija tamaño físico"
                    )
                with (
                    pymupdf.open(stream=data, filetype="svg") as svgdoc,
                    pymupdf.open(stream=svgdoc.convert_to_pdf(), filetype="pdf") as doc,
                ):
                    paginas = renderizar(doc, dpi, salida, informe["sha256"][:12])
                advertencias_render = pymupdf.TOOLS.mupdf_warnings(reset=True)
                if advertencias_render:
                    avisos.append(
                        "Advertencias del rasterizador SVG: " + advertencias_render
                    )
                informe["rasterizacion"] = {
                    "estado": "generada",
                    "paginas": paginas,
                    "tamano_salida_mm_elegido": svg_mm,
                }
        elif suffix == ".pdf":
            with pymupdf.open(path) as doc:
                if not doc.is_pdf or doc.needs_pass or not 1 <= len(doc) <= MAX_PAGINAS:
                    raise ValueError(
                        "PDF cifrado, inválido o fuera del límite local de 20 páginas"
                    )
                original = {
                    "formato_detectado": "PDF",
                    "numero_paginas": len(doc),
                    "resolucion_original_ppp": None,
                    "modo_color": "no_unico; solo se describen espacios de imágenes detectadas",
                    "paginas": [describir_pagina(page) for page in doc],
                }
                avisos = [
                    "PDF no tiene un único DPI ni modo de color. Imágenes y vectores se distinguen.",
                    "Las cajas son las visibles, con rotación aplicada; no verifican sangrado, tintas planas ni sobreimpresión.",
                ]
                informe.update(original=original, avisos=avisos)
                if dpi:
                    informe["rasterizacion"] = {
                        "estado": "generada",
                        "paginas": renderizar(doc, dpi, salida, informe["sha256"][:12]),
                    }
        else:
            raise ValueError("Formato no admitido; use PDF, JPG, PNG o SVG")
        informe.update(estado="ok", original=original, avisos=avisos)
    except (
        OSError,
        ValueError,
        RuntimeError,
        ET.ParseError,
        DefusedXmlException,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        informe["error"] = f"{type(exc).__name__}: {exc}"
    return informe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivos", nargs="+", type=Path)
    parser.add_argument("--salida", required=True, type=Path)
    parser.add_argument(
        "--dpi", type=int, help="Solo PDF/SVG; nunca resolución supuesta del original"
    )
    parser.add_argument(
        "--svg-mm",
        nargs=2,
        type=float,
        metavar=("ANCHO", "ALTO"),
        help="Tamaño de salida elegido, no dato del SVG original",
    )
    args = parser.parse_args()
    if args.dpi is not None and not 1 <= args.dpi <= 1200:
        parser.error("--dpi debe ser entero entre 1 y 1200")
    if args.svg_mm is not None and (
        args.dpi is None or par_valido(args.svg_mm) is None
    ):
        parser.error("--svg-mm requiere --dpi y dos medidas positivas finitas")
    if any(p.resolve().parent == args.salida.resolve() for p in args.archivos):
        parser.error("Use un directorio de salida separado de los archivos originales")
    args.salida.mkdir(parents=True, exist_ok=True)
    informe = {
        "esquema_prototipo": 1,
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "alcance": "inspeccion_de_entrada_no_certificacion_de_produccion",
        "archivos": [
            inspeccionar(p, args.salida, args.dpi, args.svg_mm) for p in args.archivos
        ],
    }
    destino = args.salida / "informe-entrada.json"
    if destino.resolve() in {p.resolve() for p in args.archivos}:
        parser.error("La salida no puede sobrescribir un archivo de entrada")
    destino.write_text(
        json.dumps(informe, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )
    print(destino)
    return int(any(x["estado"] != "ok" for x in informe["archivos"]))


if __name__ == "__main__":
    raise SystemExit(main())

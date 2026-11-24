"""Lectura SVG segura con XML endurecido y sin resolver recursos externos."""

from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from flexo_img.application.inspeccionar_svg import ResultadoSVG
from flexo_img.domain.unidades_svg import longitud_svg_css_px
from flexo_img.domain.validaciones import validar_limites_archivo

ELEMENTOS_VECTOR = {
    "path",
    "rect",
    "circle",
    "ellipse",
    "polygon",
    "polyline",
    "line",
    "use",
}
ELEMENTOS_TEXTO = {"text", "tspan"}


class LectorSVGXML:
    def leer(self, ruta: Path) -> ResultadoSVG:
        contenido = ruta.read_bytes()
        validar_limites_archivo(len(contenido), 1, 1)
        try:
            raiz = ET.fromstring(contenido)
        except (ET.ParseError, DefusedXmlException) as exc:
            raise ValueError("SVG inválido o con XML activo no admitido") from exc
        if raiz.tag.split("}")[-1] != "svg":
            raise ValueError("El XML no es SVG")
        tipos: set[str] = set()
        for nodo in raiz.iter():
            etiqueta = nodo.tag.split("}")[-1]
            if etiqueta in {"script", "foreignObject"}:
                raise ValueError("SVG activo no admitido en este prototipo")
            if etiqueta in ELEMENTOS_VECTOR:
                tipos.add("vector")
            if etiqueta in ELEMENTOS_TEXTO:
                tipos.add("texto")
            if etiqueta == "image":
                tipos.add("raster")
            for clave, valor in nodo.attrib.items():
                if clave.split("}")[-1] == "href" and not valor.startswith(
                    ("#", "data:image/")
                ):
                    raise ValueError(
                        "SVG con referencia externa: no se resuelve red ni archivos"
                    )
                if clave.lower().startswith("on"):
                    raise ValueError("SVG con eventos activos no admitido")
            css = " ".join(nodo.attrib.values()) + (nodo.text or "")
            sin_fragmentos = re.sub(
                r"""url\(\s*(["']?)#[^\s"'()]+\1\s*\)""", "", css, flags=re.IGNORECASE
            )
            if "@import" in css.lower() or re.search(
                r"url\(", sin_fragmentos, re.IGNORECASE
            ):
                raise ValueError("SVG con recurso CSS externo no admitido")
        ancho, alto = (
            longitud_svg_css_px(raiz.get("width")),
            longitud_svg_css_px(raiz.get("height")),
        )
        tipos_ordenados = sorted(tipos)
        original: dict[str, Any] = {
            "formato_detectado": "SVG",
            "ancho_declarado": raiz.get("width"),
            "alto_declarado": raiz.get("height"),
            "viewBox": raiz.get("viewBox"),
            "viewport_css_px": [ancho, alto] if ancho and alto else None,
            "viewport_derivado_mm": [round(v * 25.4 / 96, 4) for v in (ancho, alto)]
            if ancho and alto
            else None,
            "resolucion_original_ppp": None,
            "tipos_detectados": tipos_ordenados,
            "tipo_contenido": "mixto"
            if len(tipos_ordenados) > 1
            else (tipos_ordenados[0] if tipos_ordenados else "no_detectado"),
            "modo_color": "declaraciones SVG/CSS; perfil de salida no verificado",
        }
        return ResultadoSVG(
            tamano_bytes=len(contenido),
            sha256=sha256(contenido).hexdigest(),
            original=original,
            avisos=(
                "96 px por pulgada es la equivalencia CSS usada, no resolución del original.",
                "La detección de contenido es orientativa; no verifica fuentes, tintas planas ni sobreimpresión.",
            ),
        )

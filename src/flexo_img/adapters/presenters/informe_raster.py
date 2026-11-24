"""Presenta el resultado de aplicación con el contrato de ficha de entrada."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flexo_img.application.inspeccionar_raster import ResultadoInspeccionRaster


def presentar_informe_raster(
    ruta: str | Path, resultado: ResultadoInspeccionRaster
) -> dict[str, Any]:
    original = resultado.original
    return {
        "archivo": Path(ruta).name,
        "estado": "ok",
        "tamano_bytes": original.tamano_bytes,
        "sha256": original.sha256,
        "aptitud_produccion": "no_evaluada",
        "original": {
            "formato_detectado": original.formato_detectado,
            "tipo_contenido": "raster",
            "ancho_px": original.ancho_px,
            "alto_px": original.alto_px,
            "modo_color": original.modo_color,
            "canales": list(original.canales),
            "resolucion_metadatos_ppp": list(original.resolucion_ppp)
            if original.resolucion_ppp
            else None,
            "tamano_derivado_de_metadatos_mm": list(resultado.dimensiones_fisicas_mm)
            if resultado.dimensiones_fisicas_mm
            else None,
            "orientacion_exif": original.orientacion_exif,
            "transparencia": original.transparencia,
            "icc_presente": original.icc_sha256 is not None,
            "icc_sha256": original.icc_sha256,
            "fotografia_o_logo": "no_inferido",
        },
        "avisos": list(resultado.avisos),
        "rasterizacion": {"estado": "no_solicitada", "paginas": []},
    }

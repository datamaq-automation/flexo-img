"""Caso de uso para inspeccionar entradas y producir un informe de lote."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flexo_img.application.rasterizar_original import (
    RasterizadorOriginal,
    rasterizar_original,
)
from flexo_img.domain.validaciones import par_valido, validar_ppp_rasterizacion

Inspector = Callable[[Path], dict[str, Any]]


def inspeccionar_lote(
    archivos: list[Path],
    salida: Path,
    inspector: Inspector,
    rasterizador: RasterizadorOriginal,
    ppp: int | None = None,
    medidas_svg_mm: tuple[float, float] | None = None,
) -> dict[str, Any]:
    if ppp is not None:
        validar_ppp_rasterizacion(ppp)
    if medidas_svg_mm is not None and par_valido(medidas_svg_mm) is None:
        raise ValueError(
            "El tamaño SVG de salida requiere dos medidas positivas finitas"
        )
    resultados = []
    for ruta in archivos:
        ficha = inspector(ruta)
        if ficha["estado"] != "ok" or ppp is None:
            resultados.append(ficha)
            continue
        if ruta.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            ficha["avisos"].append(
                "No se remuestrea raster: elegir ppp no agrega detalle al original."
            )
            ficha["rasterizacion"] = {"estado": "no_aplica", "paginas": []}
            resultados.append(ficha)
            continue
        try:
            raster = rasterizar_original(
                ruta, salida, ficha["sha256"][:12], ppp, rasterizador, medidas_svg_mm
            )
            ficha["rasterizacion"] = {
                "estado": raster.estado,
                "paginas": list(raster.paginas),
            }
            if medidas_svg_mm is not None and ruta.suffix.lower() == ".svg":
                ficha["avisos"].append(
                    "Tamaño SVG de salida elegido por operador; no es tamaño del original."
                )
        except (OSError, ValueError, RuntimeError) as exc:
            ficha["estado"] = "error"
            ficha["error"] = f"{type(exc).__name__}: {exc}"
            ficha["rasterizacion"] = {"estado": "error", "paginas": []}
        resultados.append(ficha)
    return {
        "esquema_prototipo": 1,
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "alcance": "inspeccion_de_entrada_no_certificacion_de_produccion",
        "archivos": resultados,
    }

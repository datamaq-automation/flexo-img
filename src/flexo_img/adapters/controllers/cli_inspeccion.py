"""Controlador CLI para inspección en lote y rasterización explícita."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from tempfile import mkdtemp

from flexo_img.application.inspeccionar_lote import (
    EscritorInforme,
    Inspector,
    inspeccionar_lote,
)
from flexo_img.application.rasterizar_original import RasterizadorOriginal
from flexo_img.domain.validaciones import par_valido


def main(
    argv: Sequence[str] | None = None,
    inspector: Inspector | None = None,
    rasterizador: RasterizadorOriginal | None = None,
    escritor: EscritorInforme | None = None,
) -> int:
    parser = argparse.ArgumentParser(
        description="Inspección local de entrada; no convierte a CMYK ni certifica una plancha."
    )
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
    args = parser.parse_args(argv)
    if inspector is None or rasterizador is None or escritor is None:
        parser.error("Se requieren inspector, rasterizador y escritor")
    if args.dpi is not None and not 1 <= args.dpi <= 1200:
        parser.error("--dpi debe ser entero entre 1 y 1200")
    if args.svg_mm is not None and (
        args.dpi is None or par_valido(args.svg_mm) is None
    ):
        parser.error("--svg-mm requiere --dpi y dos medidas positivas finitas")
    if any(p.resolve().parent == args.salida.resolve() for p in args.archivos):
        parser.error("Use un directorio de salida separado de los archivos originales")
    destino_inicial = args.salida / "informe-entrada.json"
    if destino_inicial.resolve() in {p.resolve() for p in args.archivos}:
        parser.error("La salida no puede sobrescribir un archivo de entrada")
    try:
        args.salida.mkdir(parents=True)
    except FileExistsError:
        if not args.salida.is_dir():
            parser.error("La salida requiere un directorio")
        args.salida = Path(mkdtemp(prefix="lote-", dir=args.salida))
    medidas = tuple(args.svg_mm) if args.svg_mm is not None else None
    informe = inspeccionar_lote(
        args.archivos,
        args.salida,
        inspector,
        rasterizador,
        args.dpi,
        medidas,
    )
    destino = escritor.escribir(informe, args.salida / "informe-entrada.json")
    print(destino)
    return int(any(ficha["estado"] != "ok" for ficha in informe["archivos"]))

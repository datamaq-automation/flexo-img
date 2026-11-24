"""Controlador CLI de M2; recibe la implementación desde el punto de entrada."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from flexo_img.application.convertir_cmyk import ConvertidorCMYK, convertir_cmyk


def main(
    argv: list[str] | None = None, convertidor: ConvertidorCMYK | None = None
) -> int:
    parser = argparse.ArgumentParser(
        description="Conversión local a CMYK de demostración; no certifica planchas."
    )
    parser.add_argument("entrada", type=Path)
    parser.add_argument("--salida", required=True, type=Path)
    parser.add_argument("--perfil-cmyk", required=True, type=Path)
    parser.add_argument("--perfil-srgb", required=True, type=Path)
    parser.add_argument("--asumir-srgb", action="store_true")
    parser.add_argument("--fondo-blanco", action="store_true")
    args = parser.parse_args(argv)
    if convertidor is None:
        parser.error("Se requiere una implementación de conversión")
    try:
        informe = convertir_cmyk(
            convertidor,
            args.entrada,
            args.salida,
            args.perfil_cmyk,
            args.perfil_srgb,
            args.asumir_srgb,
            args.fondo_blanco,
        )
    except Exception as error:
        parser.exit(1, f"No se generó una entrega M2 completa: {error}\n")
    print(
        json.dumps(
            {"salida": str(args.salida), "estado": informe["estado"]},
            ensure_ascii=False,
        )
    )
    return 0

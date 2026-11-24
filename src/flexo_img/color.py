"""API pública compatible M2 y punto de composición para la CLI."""

from pathlib import Path
from typing import Any

from flexo_img.adapters.controllers.cli_color import main as _main
from flexo_img.application.convertir_cmyk import convertir_cmyk
from flexo_img.infrastructure import cmyk_pillow as _color
from flexo_img.infrastructure.cmyk_pillow import ConversorPillow

CANALES = _color.CANALES
MAX_PIXELES_M2 = _color.MAX_PIXELES_M2
MAX_BYTES = _color.MAX_BYTES


def separar_por_nombre(imagen):
    _color.MAX_PIXELES_M2 = MAX_PIXELES_M2
    return _color.separar_por_nombre(imagen)


def separar_cuatricromia(imagen):
    _color.MAX_PIXELES_M2 = MAX_PIXELES_M2
    return _color.separar_cuatricromia(imagen)


perfil = _color.perfil
lab_srgb = _color.lab_srgb
delta_e76 = _color.delta_e76
medir = _color.medir
panel_comparacion = _color.panel_comparacion


def convertir(
    entrada: Path,
    salida: Path,
    perfil_cmyk: Path,
    perfil_srgb: Path,
    asumir_srgb: bool = False,
    fondo_blanco: bool = False,
) -> dict[str, Any]:
    _color.MAX_PIXELES_M2 = MAX_PIXELES_M2
    return convertir_cmyk(
        ConversorPillow(),
        entrada,
        salida,
        perfil_cmyk,
        perfil_srgb,
        asumir_srgb,
        fondo_blanco,
    )


def main(argv: list[str] | None = None) -> int:
    return _main(argv, ConversorPillow())


if __name__ == "__main__":
    raise SystemExit(main())

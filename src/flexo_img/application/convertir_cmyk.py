"""Caso de uso M2 con convertidor inyectable."""

from pathlib import Path
from typing import Any, Protocol


class ConvertidorCMYK(Protocol):
    def convertir(
        self,
        entrada: Path,
        salida: Path,
        perfil_cmyk: Path,
        perfil_srgb: Path,
        asumir_srgb: bool = False,
        fondo_blanco: bool = False,
    ) -> dict[str, Any]: ...


def convertir_cmyk(
    convertidor: ConvertidorCMYK,
    entrada: Path,
    salida: Path,
    perfil_cmyk: Path,
    perfil_srgb: Path,
    asumir_srgb: bool = False,
    fondo_blanco: bool = False,
) -> dict[str, Any]:
    """Ejecuta M2 mediante un puerto, sin depender de Pillow ni del sistema de archivos."""
    return convertidor.convertir(
        entrada, salida, perfil_cmyk, perfil_srgb, asumir_srgb, fondo_blanco
    )

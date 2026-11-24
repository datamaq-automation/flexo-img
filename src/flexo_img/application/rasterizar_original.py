"""Caso de uso para rasterizar PDF/SVG con parámetros explícitos."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from flexo_img.domain.validaciones import validar_ppp_rasterizacion


@dataclass(frozen=True, slots=True)
class ResultadoRasterizacion:
    estado: str
    paginas: tuple[dict[str, object], ...]


class RasterizadorOriginal(Protocol):
    def pdf(
        self, ruta: Path, salida: Path, prefijo: str, ppp: int
    ) -> list[dict[str, object]]: ...

    def svg(
        self,
        ruta: Path,
        salida: Path,
        prefijo: str,
        ppp: int,
        medidas_mm: tuple[float, float] | None,
    ) -> list[dict[str, object]]: ...


def rasterizar_original(
    ruta: str | Path,
    salida: str | Path,
    prefijo: str,
    ppp: int,
    rasterizador: RasterizadorOriginal,
    medidas_svg_mm: tuple[float, float] | None = None,
) -> ResultadoRasterizacion:
    validar_ppp_rasterizacion(ppp)
    entrada, destino = Path(ruta), Path(salida)
    extension = entrada.suffix.lower()
    if extension == ".pdf":
        paginas = rasterizador.pdf(entrada, destino, prefijo, ppp)
    elif extension == ".svg":
        paginas = rasterizador.svg(entrada, destino, prefijo, ppp, medidas_svg_mm)
    elif extension in {".jpg", ".jpeg", ".png"}:
        return ResultadoRasterizacion("no_aplica", ())
    else:
        raise ValueError("Formato no admitido para rasterización")
    return ResultadoRasterizacion("generada", tuple(paginas))

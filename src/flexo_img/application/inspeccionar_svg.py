"""Contrato del caso de uso para leer originales SVG."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ResultadoSVG:
    tamano_bytes: int
    sha256: str
    original: dict[str, Any]
    avisos: tuple[str, ...]


class LectorSVG(Protocol):
    def leer(self, ruta: Path) -> ResultadoSVG: ...


def inspeccionar_svg(ruta: str | Path, lector: LectorSVG) -> ResultadoSVG:
    return lector.leer(Path(ruta))

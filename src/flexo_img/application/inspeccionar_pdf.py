"""Caso de uso de lectura PDF a través de un contrato inyectable."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ResultadoPDF:
    """Datos originales ya extraídos; no contiene objetos PyMuPDF."""

    tamano_bytes: int
    sha256: str
    original: dict[str, Any]
    avisos: tuple[str, ...]


class LectorPDF(Protocol):
    def leer(self, ruta: Path) -> ResultadoPDF: ...


def inspeccionar_pdf(ruta: str | Path, lector: LectorPDF) -> ResultadoPDF:
    return lector.leer(Path(ruta))

"""Valores y reglas puras de cobertura CMYK; no dependen de imágenes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TintasCMYK:
    """Cobertura nominal por canal en escala de 8 bits (0 a 255)."""

    c: int
    m: int
    y: int
    k: int

    def __post_init__(self) -> None:
        if any(type(valor) is not int or not 0 <= valor <= 255 for valor in self.valores):
            raise ValueError("Cada canal CMYK debe ser un entero entre 0 y 255")

    @property
    def valores(self) -> tuple[int, int, int, int]:
        return self.c, self.m, self.y, self.k

    @property
    def cobertura_total_pct(self) -> float:
        """Suma nominal de coberturas; no representa consumo físico ni TAC validado."""
        return sum(self.valores) / 255 * 100

    def como_porcentajes(self) -> tuple[float, float, float, float]:
        return tuple(valor / 255 * 100 for valor in self.valores)

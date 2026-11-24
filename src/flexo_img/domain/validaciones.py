"""Límites de seguridad del prototipo; no son umbrales de producción."""

MAX_BYTES = 25 * 1024 * 1024
MAX_PIXELES = 20_000_000


def validar_ppp_rasterizacion(ppp: int) -> None:
    if isinstance(ppp, bool) or not isinstance(ppp, int) or not 1 <= ppp <= 1200:
        raise ValueError(
            "La rasterización requiere PPP enteros entre 1 y 1200 (límite local)"
        )


def validar_limites_archivo(tamano_bytes: int, ancho_px: int, alto_px: int) -> None:
    if tamano_bytes > MAX_BYTES:
        raise ValueError("Archivo mayor al límite local de 25 MiB")
    if ancho_px <= 0 or alto_px <= 0:
        raise ValueError("Dimensiones no positivas")
    if ancho_px * alto_px > MAX_PIXELES:
        raise ValueError(
            "Se supera el límite local de píxeles; no es un umbral de imprenta"
        )

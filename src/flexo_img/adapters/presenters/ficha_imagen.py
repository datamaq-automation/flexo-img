"""Convierte la ficha de aplicación a un diccionario serializable."""

from flexo_img.application.inspeccionar_imagen import FichaImagen


def presentar_ficha(ficha: FichaImagen) -> dict[str, object]:
    """Prepara una forma estable para una futura CLI o API pública."""
    original = ficha.original
    return {
        "ancho_px": original.ancho_px,
        "alto_px": original.alto_px,
        "modo_color": original.modo_color,
        "resolucion_ppp": list(original.resolucion_ppp)
        if original.resolucion_ppp
        else None,
        "dimensiones_fisicas_mm": list(ficha.dimensiones_fisicas_mm)
        if ficha.dimensiones_fisicas_mm
        else None,
    }

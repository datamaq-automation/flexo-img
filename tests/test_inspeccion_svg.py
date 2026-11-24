from pathlib import Path

import pytest

from flexo_img.domain.unidades_svg import longitud_svg_css_px
from flexo_img.inspector import inspeccionar_archivo


def test_unidades_css_se_convierten_sin_inventar_ppp():
    assert longitud_svg_css_px("25.4mm") == pytest.approx(96)
    assert longitud_svg_css_px("1in") == 96
    assert longitud_svg_css_px("50%") is None


def test_svg_informa_vector_texto_y_dimensiones_declaradas(tmp_path: Path):
    ruta = tmp_path / "muestra.svg"
    ruta.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="25.4mm" height="1in" viewBox="0 0 20 20"><text>hola</text><path d="M0 0 L1 1"/></svg>'
    )

    ficha = inspeccionar_archivo(ruta)

    assert ficha["estado"] == "ok"
    assert ficha["original"]["viewport_css_px"] == pytest.approx([96, 96])
    assert ficha["original"]["resolucion_original_ppp"] is None
    assert ficha["original"]["tipo_contenido"] == "mixto"
    assert "vector" in ficha["original"]["tipos_detectados"]
    assert "texto" in ficha["original"]["tipos_detectados"]


def test_svg_rechaza_script_y_referencia_externa(tmp_path: Path):
    for fragmento, motivo in [
        ("<script>alert(1)</script>", "activo"),
        ('<image href="https://example.invalid/a.png"/>', "referencia externa"),
    ]:
        ruta = tmp_path / "malo.svg"
        ruta.write_text(f'<svg xmlns="http://www.w3.org/2000/svg">{fragmento}</svg>')

        ficha = inspeccionar_archivo(ruta)

        assert ficha["estado"] == "error"
        assert motivo in ficha["error"]


def test_svg_admite_referencia_local_a_gradiente(tmp_path: Path):
    ruta = tmp_path / "gradiente.svg"
    ruta.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><defs><linearGradient id="g"><stop offset="0"/></linearGradient></defs><rect width="10" height="10" fill="url(#g)"/></svg>'
    )

    ficha = inspeccionar_archivo(ruta)

    assert ficha["estado"] == "ok"
    assert ficha["original"]["tipo_contenido"] == "vector"


def test_svg_rechaza_eventos_y_recursos_css_remotos(tmp_path: Path):
    for fragmento, motivo in [
        ('<rect width="1" height="1" onclick="alert(1)"/>', "eventos"),
        ("<style>@import url(https://example.invalid/a.css);</style>", "CSS externo"),
        ("<foreignObject/>", "activo"),
    ]:
        ruta = tmp_path / "activo.svg"
        ruta.write_text(f'<svg xmlns="http://www.w3.org/2000/svg">{fragmento}</svg>')

        ficha = inspeccionar_archivo(ruta)

        assert ficha["estado"] == "error"
        assert motivo in ficha["error"]


def test_svg_con_viewbox_sin_tamano_no_inventa_dimensiones(tmp_path: Path):
    ruta = tmp_path / "viewbox.svg"
    ruta.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle r="10"/></svg>'
    )

    ficha = inspeccionar_archivo(ruta)

    assert ficha["original"]["viewport_css_px"] is None
    assert ficha["original"]["viewport_derivado_mm"] is None
    assert ficha["original"]["resolucion_original_ppp"] is None

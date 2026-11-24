"""Reglas CMYK puras: no requieren Pillow ni muestras en disco."""

import pytest

from flexo_img.domain.tintas import TintasCMYK


def test_cobertura_total_nominal_se_calcula_sin_redondeo_temprano():
    tintas = TintasCMYK(0, 127, 255, 64)

    assert tintas.valores == (0, 127, 255, 64)
    assert tintas.cobertura_total_pct == pytest.approx(446 / 255 * 100)
    assert tintas.como_porcentajes() == pytest.approx(
        (0, 127 / 255 * 100, 100, 64 / 255 * 100)
    )


def test_rechaza_canales_fuera_del_rango_o_no_enteros():
    for valores in ((-1, 0, 0, 0), (256, 0, 0, 0), (1.5, 0, 0, 0), (True, 0, 0, 0)):
        with pytest.raises(ValueError, match="entero entre 0 y 255"):
            TintasCMYK(*valores)


def test_dominio_no_importa_bibliotecas_de_imagenes():
    import inspect

    from flexo_img.domain import tintas

    assert "PIL" not in inspect.getsource(tintas)
    assert "numpy" not in inspect.getsource(tintas).lower()

from PIL import Image

from flexo_img.inspector import inspeccionar_archivo


def test_dos_originales_de_una_pulgada_a_72_y_300_ppp(tmp_path):
    for ppp in (72, 300):
        ruta = tmp_path / f"{ppp}.jpg"
        Image.new("RGB", (ppp, ppp), "white").save(ruta, dpi=(ppp, ppp))
        ficha = inspeccionar_archivo(str(ruta))
        assert ficha["estado"] == "ok"
        original = ficha["original"]
        assert [original["ancho_px"], original["alto_px"]] == [ppp, ppp]
        assert original["resolucion_metadatos_ppp"] == [ppp, ppp]
        assert original["tamano_derivado_de_metadatos_mm"] == [25.4, 25.4]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["300.jpg", "72.jpg"]

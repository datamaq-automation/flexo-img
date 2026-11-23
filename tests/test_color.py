"""M2 offline: gestión ICC explícita, canales y mediciones verificables."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageCms

from flexo_img.color import CANALES, convertir, delta_e76, lab_srgb

BASE = Path(__file__).parent.parent
RGB = BASE / "perfiles-icc/default_rgb.icc"
CMYK = BASE / "perfiles-icc/default_cmyk.icc"


@pytest.fixture
def muestra(tmp_path):
    p = tmp_path / "colores.png"
    im = Image.new("RGB", (4, 2))
    im.putdata(
        [
            (255, 255, 255),
            (0, 0, 0),
            (255, 177, 59),
            (0, 255, 0),
            (255, 0, 0),
            (0, 0, 255),
            (128, 128, 128),
            (210, 170, 140),
        ]
    )
    im.save(p)
    return p


def test_exporta_cmyk_y_los_cuatro_grises_sin_tocar_entrada(tmp_path, muestra):
    antes = muestra.read_bytes()
    out = tmp_path / "entrega"
    r = convertir(muestra, out, CMYK, RGB, True)
    assert muestra.read_bytes() == antes
    assert r["dimensiones_px"] == [4, 2]
    assert r["estado"] == "demo"
    assert r["aptitud_produccion"] == "no_evaluada"
    assert r["perfil_salida_validado_para_maquina"] is False
    assert r["perfil_entrada_origen"] == "sRGB_asumido_expresamente_no_verificado"
    assert r["ppp_de_entrada"] is None
    with Image.open(out / "conversion_cmyk_DEMO.tif") as cmyk:
        assert cmyk.mode == "CMYK"
        assert cmyk.info["icc_profile"] == CMYK.read_bytes()
        assert cmyk.size == (4, 2)
        for c in CANALES:
            with Image.open(out / f"canal_{c}_gris_DEMO.png") as gris:
                assert gris.mode == "L"
                assert list(gris.get_flattened_data()) == [
                    255 - x for x in cmyk.getchannel(c).get_flattened_data()
                ]
                assert gris.getpixel((0, 0)) == 255
                assert "0% tinta" in gris.info["escala"]
    for name in ("original_srgb.png", "preview_cmyk_srgb_DEMO.png"):
        with Image.open(out / name) as im:
            assert im.mode == "RGB"
            assert im.info["icc_profile"] == RGB.read_bytes()
    assert len(list(out.glob("canal_*_gris_DEMO.png"))) == 4
    assert len(list(out.glob("canal_*_cobertura_DEMO.png"))) == 4
    assert r["entrada_sha256"] == hashlib.sha256(antes).hexdigest()
    for name, sha in r["salidas"].items():
        assert hashlib.sha256((out / name).read_bytes()).hexdigest() == sha


def test_sin_icc_no_asume_srgb_en_silencio(tmp_path, muestra):
    out = tmp_path / "no-generada"
    with pytest.raises(ValueError, match="sin ICC"):
        convertir(muestra, out, CMYK, RGB)
    assert not out.exists()


def test_icc_incrustado_se_respeta_y_no_se_declara_supuesto(tmp_path, muestra):
    im = Image.open(muestra)
    im.save(muestra, icc_profile=RGB.read_bytes())
    r = convertir(muestra, tmp_path / "icc", CMYK, RGB)
    assert r["perfil_entrada_origen"] == "incrustado_en_entrada"
    assert r["perfil_entrada"]["sha256"] == hashlib.sha256(RGB.read_bytes()).hexdigest()


def test_icc_corrupto_no_se_reemplaza_por_srgb(tmp_path, muestra):
    with Image.open(muestra) as im:
        im.save(tmp_path / "roto.png", icc_profile=b"perfil-roto")
    with pytest.raises((OSError, ValueError, ImageCms.PyCMSError)):
        convertir(tmp_path / "roto.png", tmp_path / "fallo", CMYK, RGB, True)
    assert not (tmp_path / "fallo").exists()


def test_perfil_rgb_no_sirve_como_salida_cmyk(tmp_path, muestra):
    with pytest.raises(ValueError, match="CMYK"):
        convertir(muestra, tmp_path / "fallo", RGB, RGB, True)


def test_no_sobrescribe_entrega_existente(tmp_path, muestra):
    out = tmp_path / "previa"
    out.mkdir()
    (out / "conservar.txt").write_text("intacto")
    with pytest.raises(FileExistsError):
        convertir(muestra, out, CMYK, RGB, True)
    assert (out / "conservar.txt").read_text() == "intacto"


def test_cobertura_concuerda_con_datos_cmyk_guardados(tmp_path, muestra):
    out = tmp_path / "metricas"
    r = convertir(muestra, out, CMYK, RGB, True)
    with Image.open(out / "conversion_cmyk_DEMO.tif") as im:
        datos = list(im.get_flattened_data())
    m = r["mediciones"]
    assert m["tinta_total_nominal_maxima_pct"] == pytest.approx(
        max(map(sum, datos)) / 255 * 100, abs=0.0001
    )
    assert m["tinta_total_nominal_media_pct"] == pytest.approx(
        sum(map(sum, datos)) / len(datos) / 255 * 100, abs=0.0001
    )
    for i, c in enumerate(CANALES):
        assert m["tinta_nominal_por_canal"][c]["media_pct"] == pytest.approx(
            sum(x[i] for x in datos) / len(datos) / 255 * 100, abs=0.0001
        )


@pytest.mark.parametrize(
    "rgb,lab",
    [
        ((255, 255, 255), (100, 0, 0)),
        ((0, 0, 0), (0, 0, 0)),
        ((255, 0, 0), (53.2408, 80.0925, 67.2032)),
    ],
)
def test_lab_srgb_coincide_con_referencias_matematicas(rgb, lab):
    assert lab_srgb(rgb) == pytest.approx(lab, abs=0.002)


def test_delta_e_cero_identidad_y_simetria():
    assert delta_e76((50, 100, 150), (50, 100, 150)) == 0
    assert delta_e76((255, 0, 0), (0, 255, 0)) == pytest.approx(
        delta_e76((0, 255, 0), (255, 0, 0))
    )


def test_metricas_reflejan_diferencia_original_preview(tmp_path, muestra):
    out = tmp_path / "diferencias"
    r = convertir(muestra, out, CMYK, RGB, True)
    with (
        Image.open(out / "original_srgb.png") as a,
        Image.open(out / "preview_cmyk_srgb_DEMO.png") as b,
    ):
        antes = list(a.get_flattened_data())
        despues = list(b.get_flattened_data())
    assert r["mediciones"]["deltaE76_srgb_D65_media"] == pytest.approx(
        sum(delta_e76(a, b) for a, b in zip(antes, despues, strict=True)) / len(antes),
        abs=0.0001,
    )
    assert r["mediciones"]["deltaE76_srgb_D65_media"] > 0
    assert all(m["deltaE76_srgb_D65"] >= 0 for m in r["mediciones"]["muestras_color"])


def test_alpha_necesita_fondo_explicito(tmp_path):
    p = tmp_path / "alpha.png"
    Image.new("RGBA", (2, 2), (255, 0, 0, 0)).save(p)
    with pytest.raises(ValueError, match="transparencia"):
        convertir(p, tmp_path / "fallo", CMYK, RGB, True)
    r = convertir(p, tmp_path / "blanco", CMYK, RGB, True, True)
    assert r["transparencia_aplanada_sobre_blanco"] is True
    with Image.open(tmp_path / "blanco/conversion_cmyk_DEMO.tif") as im:
        assert im.getpixel((0, 0)) == (0, 0, 0, 0)


def test_exif_rotacion_se_aplica_sin_remuestreo(tmp_path):
    p = tmp_path / "girada.jpg"
    exif = Image.Exif()
    exif[274] = 6
    Image.new("RGB", (4, 2), (200, 100, 50)).save(p, exif=exif, dpi=(300, 150))
    r = convertir(p, tmp_path / "girada", CMYK, RGB, True)
    assert r["dimensiones_px"] == [2, 4]
    assert r["ppp_de_entrada"] == [150, 300]


@pytest.mark.parametrize("modo", ["L", "CMYK"])
def test_no_asigna_srgb_a_modo_incompatible(tmp_path, modo):
    p = tmp_path / "otro.jpg"
    Image.new(modo, (2, 2)).save(p)
    with pytest.raises(ValueError, match="RGB"):
        convertir(p, tmp_path / "fallo", CMYK, RGB, True)


def test_limite_recursos_no_es_aptitud(tmp_path, muestra, monkeypatch):
    monkeypatch.setattr("flexo_img.color.MAX_PIXELES_M2", 3)
    with pytest.raises(ValueError, match="límite local"):
        convertir(muestra, tmp_path / "fallo", CMYK, RGB, True)


def test_cli_genera_informe_demo_reproducible(tmp_path, muestra):
    out = tmp_path / "cli"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "flexo_img.color",
            str(muestra),
            "--salida",
            str(out),
            "--perfil-cmyk",
            str(CMYK),
            "--perfil-srgb",
            str(RGB),
            "--asumir-srgb",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    informe = json.loads((out / "informe_M2.json").read_text())
    assert informe["estado"] == "demo"
    assert "LittleCMS" in informe["versiones"]


@pytest.mark.parametrize(
    "rgb,esperado",
    [
        ((255, 0, 0), (0, 255, 255, 0)),
        ((0, 255, 0), (255, 0, 255, 0)),
        ((0, 0, 255), (255, 255, 0, 0)),
        ((255, 255, 255), (0, 0, 0, 0)),
        ((0, 0, 0), (0, 0, 0, 255)),
        ((128, 128, 128), (0, 0, 0, 127)),
    ],
)
def test_formula_normalizada_primarios_y_negro(rgb, esperado):
    from flexo_img.color import separar_cuatricromia

    canales = separar_cuatricromia(Image.new("RGB", (1, 1), rgb))
    assert tuple(canales[c].getpixel((0, 0)) for c in CANALES) == esperado
    assert all(im.mode == "L" for im in canales.values())


def test_formula_intermedia_y_modo_invalido(monkeypatch):
    from flexo_img.color import separar_cuatricromia

    imagen = Image.new("RGB", (1, 1), (128, 64, 32))
    canales = separar_cuatricromia(imagen)
    assert canales["C"].getpixel((0, 0)) == 0
    assert canales["M"].getpixel((0, 0)) == 127
    assert canales["Y"].getpixel((0, 0)) == 191
    assert canales["K"].getpixel((0, 0)) == 127
    with pytest.raises(ValueError, match="requiere RGB"):
        separar_cuatricromia(imagen.convert("L"))
    monkeypatch.setattr("flexo_img.color.MAX_PIXELES_M2", 0)
    with pytest.raises(ValueError, match="límite"):
        separar_cuatricromia(imagen)


def test_exportacion_cobertura_y_vista_invertida(tmp_path, muestra):
    salida = tmp_path / "canales"
    convertir(muestra, salida, CMYK, RGB, True)
    for c in CANALES:
        with (
            Image.open(salida / f"canal_{c}_cobertura_DEMO.png") as crudo,
            Image.open(salida / f"canal_{c}_gris_DEMO.png") as vista,
        ):
            assert crudo.mode == vista.mode == "L"
            assert all(
                a + b == 255
                for a, b in zip(
                    crudo.get_flattened_data(), vista.get_flattened_data(), strict=True
                )
            )

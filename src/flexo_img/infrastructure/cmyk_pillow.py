"""M2 local: conversión ICC y canales de tono continuo. DEMO, no planchas."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import (
    Image,
    ImageChops,
    ImageCms,
    ImageDraw,
    ImageFont,
    ImageMath,
    ImageOps,
    ImageStat,
    features,
)
from PIL.PngImagePlugin import PngInfo

from flexo_img.domain.validaciones import MAX_BYTES, par_valido

CANALES = ("C", "M", "Y", "K")
INTENTO = ImageCms.Intent.RELATIVE_COLORIMETRIC
FLAGS = ImageCms.Flags.BLACKPOINTCOMPENSATION
MAX_PIXELES_M2 = 2_000_000


def separar_por_nombre(imagen: Image.Image) -> dict[str, Image.Image]:
    """Fórmula didáctica #4: cobertura cruda 0=sin tinta, 255=máxima.

    No es gestión ICC ni garantiza tintas de una máquina. Operaciones Pillow
    sobre matrices; K=min(255-R,255-G,255-B). Negro evita dividir por cero.
    """
    if imagen.mode != "RGB":
        raise ValueError("La separación matemática requiere RGB")
    if imagen.width * imagen.height > MAX_PIXELES_M2:
        raise ValueError("Se supera el límite local de píxeles M2")
    if "transparency" in imagen.info:
        raise ValueError(
            "La separación matemática requiere aplanar la transparencia sobre un fondo explícito"
        )
    c, m, y = [ImageOps.invert(canal) for canal in imagen.split()]
    k = ImageChops.darker(ImageChops.darker(c, m), y)
    denominador = ImageOps.invert(k).point(lambda v: v or 1)
    canales = {}
    for nombre, valor in zip(CANALES[:3], (c, m, y), strict=True):
        numerador = ImageChops.subtract(valor, k)
        canales[nombre] = ImageMath.lambda_eval(
            lambda args: args["n"] * 255 / args["d"],
            n=numerador.convert("F"),
            d=denominador,
        ).convert("L")
    canales["K"] = k
    return canales


def separar_cuatricromia(
    imagen: Image.Image,
) -> tuple[Image.Image, Image.Image, Image.Image, Image.Image]:
    """Devuelve los cuatro planos de cobertura en orden C, M, Y, K."""
    planos = separar_por_nombre(imagen)
    return planos["C"], planos["M"], planos["Y"], planos["K"]


def perfil(datos: bytes, espacio: str) -> tuple[Any, dict[str, Any]]:
    p = ImageCms.ImageCmsProfile(io.BytesIO(datos))
    if p.profile.xcolor_space.strip() != espacio:
        raise ValueError(
            f"El perfil debe describir {espacio}, no {p.profile.xcolor_space.strip()}"
        )
    return p, {
        "descripcion": ImageCms.getProfileDescription(p).strip(),
        "sha256": hashlib.sha256(datos).hexdigest(),
        "espacio": espacio,
        "copyright": ImageCms.getProfileCopyright(p).strip(),
    }


def _lab_pixeles(rgb: np.ndarray) -> np.ndarray:
    valores = rgb.astype(np.float64) / 255
    r, g, b = np.where(
        valores <= 0.04045, valores / 12.92, ((valores + 0.055) / 1.055) ** 2.4
    ).T
    xyz = np.array(
        [
            (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047,
            0.2126729 * r + 0.7151522 * g + 0.0721750 * b,
            (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883,
        ]
    )
    x, y, z = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.column_stack((116 * y - 16, 500 * (x - y), 200 * (y - z)))


def lab_srgb(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """CIELAB desde sRGB D65, con el mismo cálculo que el informe por bloques."""
    claridad, a, b = _lab_pixeles(np.array([rgb]))[0]
    return float(claridad), float(a), float(b)


def delta_e76(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return math.dist(lab_srgb(a), lab_srgb(b))


def medir(
    original: Image.Image, preview: Image.Image, cmyk: Image.Image
) -> dict[str, Any]:
    antes = np.asarray(original).reshape(-1, 3)
    despues = np.asarray(preview).reshape(-1, 3)
    tintas = np.asarray(cmyk).reshape(-1, 4)
    deltas = np.empty(len(antes), dtype=np.float64)
    for inicio in range(0, len(antes), 65536):
        bloque = slice(inicio, inicio + 65536)
        diferencia = _lab_pixeles(antes[bloque]) - _lab_pixeles(despues[bloque])
        deltas[bloque] = np.linalg.norm(diferencia, axis=1)
    # Empaquetar RGB permite contar colores sin construir una tupla por píxel.
    claves = antes[:, 0].astype(np.uint32)
    claves = (claves * 256 + antes[:, 1]) * 256 + antes[:, 2]
    _, primeras, cuentas = np.unique(claves, return_index=True, return_counts=True)
    orden = np.lexsort((primeras, -cuentas))
    indices = primeras[orden[:5]].tolist()
    peor = int(deltas.argmax())
    indices.append(peor)
    indices += [
        (original.height * fy // 4) * original.width + original.width * fx // 4
        for fx, fy in ((1, 1), (2, 2), (3, 3))
    ]
    muestras = []
    for idx in dict.fromkeys(indices):
        muestras.append(
            {
                "xy": [idx % original.width, idx // original.width],
                "rgb_original_srgb": antes[idx].tolist(),
                "rgb_preview_srgb": despues[idx].tolist(),
                "cmyk_8bit": tintas[idx].tolist(),
                "tinta_pct": [round(n / 255 * 100, 4) for n in tintas[idx].tolist()],
                "deltaE76_srgb_D65": round(deltas[idx], 4),
            }
        )
    stats = ImageStat.Stat(cmyk)
    cobertura = {
        c: {
            "media_pct": round(stats.mean[i] / 255 * 100, 4),
            "maximo_pct": round(cmyk.getchannel(c).getextrema()[1] / 255 * 100, 4),
        }
        for i, c in enumerate(CANALES)
    }
    return {
        "pixeles": len(antes),
        "deltaE76_srgb_D65_media": round(float(deltas.mean()), 4),
        "deltaE76_srgb_D65_p95": round(
            float(np.quantile(deltas, 0.95, method="lower")), 4
        ),
        "deltaE76_srgb_D65_maximo": round(float(deltas[peor]), 4),
        "xy_deltaE76_maximo": [peor % original.width, peor // original.width],
        "pixeles_rgb_distintos_pct": round(
            float(np.any(antes != despues, axis=1).mean()) * 100,
            4,
        ),
        "tinta_nominal_por_canal": cobertura,
        "tinta_total_nominal_media_pct": round(sum(stats.mean) / 255 * 100, 4),
        "tinta_total_nominal_maxima_pct": round(
            int(tintas.sum(axis=1, dtype=np.uint16).max()) / 255 * 100, 4
        ),
        "muestras_color": muestras,
        "metodo": "Todos los píxeles; RGB normalizado y reconversión CMYK a sRGB. DeltaE76 calculado D65, no colorimetría de papel. P95 por índice floor(0.95*(N-1)).",
        "interpretacion_cobertura": "Tono continuo nominal, no porcentaje de puntos tramados, opacidad ni consumo físico. Suma CMYK puede superar 100%.",
    }


def panel_comparacion(
    original: Image.Image,
    preview: Image.Image,
    canales: dict[str, Image.Image],
    salida: Path,
) -> None:
    ancho, alto = 350, 350
    panel = Image.new("RGB", (ancho * 3, alto * 2 + 70), "#ececec")
    draw = ImageDraw.Draw(panel)
    font = ImageFont.load_default(size=16)
    dibujos = [
        ("Original normalizado sRGB", original),
        ("CMYK -> sRGB (DEMO)", preview),
    ] + [(f"Canal {c} - tono continuo", canales[c]) for c in CANALES]
    for i, (titulo, im) in enumerate(dibujos):
        x, y = i % 3 * ancho, i // 3 * alto
        draw.text((x + 10, y + 8), titulo, fill="black", font=font)
        copia = im.convert("RGB")
        copia.thumbnail((330, 300))
        if max(copia.size) < 300:
            escala = min(330 / copia.width, 300 / copia.height)
            copia = copia.resize(
                (round(copia.width * escala), round(copia.height * escala)),
                Image.Resampling.NEAREST,
            )
        panel.paste(
            copia, (x + (ancho - copia.width) // 2, y + 35 + (300 - copia.height) // 2)
        )
    draw.text(
        (10, alto * 2 + 6),
        "DEMO sin perfil de maquina validado. Panel ampliado solo para visualizar.",
        fill="black",
        font=font,
    )
    draw.text(
        (10, alto * 2 + 30),
        "Canales: blanco = 0% tinta; negro = 100%. Sin trama ni decision de aptitud.",
        fill="black",
        font=font,
    )
    panel.save(salida)


def convertir(
    entrada: Path,
    salida: Path,
    perfil_cmyk: Path,
    perfil_srgb: Path,
    asumir_srgb: bool = False,
    fondo_blanco: bool = False,
) -> dict[str, Any]:
    if entrada.stat().st_size > MAX_BYTES:
        raise ValueError("Entrada mayor al límite de recursos local")
    if salida.exists():
        raise FileExistsError(
            "Use un directorio de salida nuevo; no se sobrescriben entregas"
        )
    bytes_entrada = entrada.read_bytes()
    bytes_rgb, bytes_cmyk = perfil_srgb.read_bytes(), perfil_cmyk.read_bytes()
    srgb, info_srgb = perfil(bytes_rgb, "RGB")
    if "srgb" not in info_srgb["descripcion"].lower():
        raise ValueError("El perfil RGB de referencia debe identificarse como sRGB")
    destino, info_cmyk = perfil(bytes_cmyk, "CMYK")
    with Image.open(io.BytesIO(bytes_entrada)) as archivo:
        if archivo.format not in ("JPEG", "PNG") or archivo.mode not in ("RGB", "RGBA"):
            raise ValueError(
                "M2 admite JPEG/PNG RGB o RGBA; no asigna perfiles a modos incompatibles"
            )
        if archivo.width * archivo.height > MAX_PIXELES_M2:
            raise ValueError(
                "Se supera el límite local de píxeles M2; no es un criterio de imprenta"
            )
        dpi = par_valido(archivo.info.get("dpi"))
        orientacion = archivo.getexif().get(274)
        imagen = ImageOps.exif_transpose(archivo)
        icc = archivo.info.get("icc_profile")
        if icc:
            origen, info_origen = perfil(icc, "RGB")
            origen_perfil = "incrustado_en_entrada"
        else:
            if not asumir_srgb:
                raise ValueError(
                    "Entrada sin ICC: declare --asumir-srgb de forma explícita"
                )
            origen, info_origen, origen_perfil = (
                srgb,
                dict(info_srgb),
                "sRGB_asumido_expresamente_no_verificado",
            )
        if imagen.mode == "RGB" and "transparency" in imagen.info:
            imagen = imagen.convert("RGBA")
        alpha = imagen.mode == "RGBA" and imagen.getchannel("A").getextrema()[0] < 255
        if alpha and not fondo_blanco:
            raise ValueError("La transparencia requiere --fondo-blanco explícito")
        if alpha:
            base = Image.new("RGBA", imagen.size, "white")
            base.alpha_composite(imagen)
            imagen = base.convert("RGB")
        else:
            imagen = imagen.convert("RGB")
        if dpi and orientacion in (5, 6, 7, 8):
            dpi.reverse()
        kwargs = {"dpi": tuple(dpi)} if dpi else {}
        original = ImageCms.profileToProfile(
            imagen, origen, srgb, renderingIntent=INTENTO, outputMode="RGB", flags=FLAGS
        )
        cmyk = ImageCms.profileToProfile(
            imagen,
            origen,
            destino,
            renderingIntent=INTENTO,
            outputMode="CMYK",
            flags=FLAGS,
        )
        preview = ImageCms.profileToProfile(
            cmyk, destino, srgb, renderingIntent=INTENTO, outputMode="RGB", flags=FLAGS
        )
    informe = {
        "fase": "M2",
        "estado": "demo",
        "aptitud_produccion": "no_evaluada",
        "archivo_entrada": entrada.name,
        "entrada_sha256": hashlib.sha256(bytes_entrada).hexdigest(),
        "dimensiones_px": list(imagen.size),
        "ppp_de_entrada": dpi,
        "perfil_entrada_origen": origen_perfil,
        "perfil_entrada": info_origen,
        "perfil_srgb_de_visualizacion": info_srgb,
        "perfil_salida_cmyk": info_cmyk,
        "perfil_salida_validado_para_maquina": False,
        "intento_renderizado": "colorimetrico_relativo",
        "compensacion_punto_negro": True,
        "transparencia_aplanada_sobre_blanco": alpha,
        "orientacion_exif_entrada": orientacion,
        "versiones": {
            "Pillow": Image.__version__,
            "LittleCMS": features.version("littlecms2"),
        },
        "mediciones": medir(original, preview, cmyk),
        "limites": [
            "Previsualización sRGB de la reconversión: no simula blanco del papel ni pantalla calibrada.",
            "No mide el color físico, no genera trama, no evalúa aptitud ni optimiza cobertura.",
        ],
    }
    salida.mkdir(parents=True)
    original.save(salida / "original_srgb.png", icc_profile=bytes_rgb, **kwargs)
    cmyk.save(
        salida / "conversion_cmyk_DEMO.tif",
        icc_profile=bytes_cmyk,
        compression="tiff_lzw",
        **kwargs,
    )
    preview.save(salida / "preview_cmyk_srgb_DEMO.png", icc_profile=bytes_rgb, **kwargs)
    canales = {}
    for c in CANALES:
        crudo = cmyk.getchannel(c)
        meta_crudo = PngInfo()
        meta_crudo.add_text(
            "escala", "cobertura: 0=sin tinta; 255=100%; no es vista invertida"
        )
        crudo.save(
            salida / f"canal_{c}_cobertura_DEMO.png", pnginfo=meta_crudo, **kwargs
        )
        gris = ImageOps.invert(crudo)
        canales[c] = gris
        meta = PngInfo()
        meta.add_text("canal", c)
        meta.add_text(
            "escala", "blanco=0% tinta; negro=100% tinta; valor=(255-gris)/255"
        )
        gris.save(salida / f"canal_{c}_gris_DEMO.png", pnginfo=meta, **kwargs)
    panel_comparacion(original, preview, canales, salida / "comparacion_DEMO.png")
    with (salida / "muestras_color.csv").open("w", newline="") as f:
        escritor = csv.writer(f, lineterminator="\n")
        escritor.writerow(
            [
                "x",
                "y",
                "RGB_original_sRGB",
                "RGB_preview_sRGB",
                "CMYK_8bit",
                "tinta_pct",
                "DeltaE76_sRGB_D65",
            ]
        )
        for m in informe["mediciones"]["muestras_color"]:
            escritor.writerow(
                [
                    *m["xy"],
                    m["rgb_original_srgb"],
                    m["rgb_preview_srgb"],
                    m["cmyk_8bit"],
                    m["tinta_pct"],
                    m["deltaE76_srgb_D65"],
                ]
            )
    informe["salidas"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in salida.iterdir()
        if p.is_file()
    }
    (salida / "informe_M2.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )
    return informe


class ConversorPillow:
    """Implementación local del puerto M2 con Pillow, LittleCMS y NumPy."""

    def convertir(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        return convertir(*args, **kwargs)

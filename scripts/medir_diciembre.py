"""Medición repetible de M1 y M2 sobre un PDF cercano a 10 MB."""

import platform
import random
import tempfile
from pathlib import Path
from time import perf_counter

import pymupdf

from flexo_img.color import convertir
from flexo_img.inspeccion import inspeccionar

PERFILES = Path(__file__).resolve().parents[1] / "perfiles-icc"


def generar_pdf(ruta: Path) -> None:
    azar = random.Random(199)
    with pymupdf.open() as doc:
        for _ in range(4):
            pagina = doc.new_page(width=144, height=144)
            pixeles = azar.randbytes(912 * 912 * 3)
            imagen = pymupdf.Pixmap(pymupdf.csRGB, 912, 912, pixeles, False)
            pagina.insert_image(pagina.rect, pixmap=imagen)
        doc.save(ruta, no_new_id=True)


def main() -> None:
    print(platform.system(), platform.machine(), platform.python_version())
    with tempfile.TemporaryDirectory() as temporal:
        base = Path(temporal)
        entrada = base / "cuatro-paginas.pdf"
        generar_pdf(entrada)
        print(f"Entrada: {entrada.stat().st_size} bytes")
        for intento in range(1, 4):
            salida = base / str(intento)
            salida.mkdir()
            inicio = perf_counter()
            ficha = inspeccionar(entrada, salida, dpi=150)
            if ficha["estado"] != "ok":
                raise RuntimeError(ficha)
            paginas = ficha["rasterizacion"]["paginas"]
            assert len(paginas) == 4
            intermedio = perf_counter()
            for pagina in paginas:
                convertir(
                    salida / pagina["archivo"],
                    salida / f"color-{pagina['pagina']}",
                    PERFILES / "default_cmyk.icc",
                    PERFILES / "default_rgb.icc",
                    asumir_srgb=True,
                )
            fin = perf_counter()
            print(
                f"{intento}: M1 {intermedio - inicio:.3f} s, "
                f"M2 {fin - intermedio:.3f} s, total {fin - inicio:.3f} s"
            )


if __name__ == "__main__":
    main()

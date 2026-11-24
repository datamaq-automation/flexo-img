from pathlib import Path

from flexo_img.application.inspeccionar_pdf import ResultadoPDF, inspeccionar_pdf


class LectorPDFDePrueba:
    def leer(self, ruta: Path) -> ResultadoPDF:
        assert ruta.name == "muestra.pdf"
        return ResultadoPDF(10, "abc", {"numero_paginas": 1}, ())


def test_caso_pdf_usa_el_contrato_inyectado():
    resultado = inspeccionar_pdf("muestra.pdf", LectorPDFDePrueba())

    assert resultado.tamano_bytes == 10
    assert resultado.original == {"numero_paginas": 1}

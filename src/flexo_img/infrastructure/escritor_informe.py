"""Escritura de informes JSON de inspección."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EscritorInformeJSON:
    def escribir(self, informe: dict[str, Any], destino: Path) -> Path:
        destino.write_text(
            json.dumps(informe, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        return destino

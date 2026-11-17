"""Point d'entrée détecté par Vercel (preset FastAPI).

Le paquet vit dans `src/` : en local on passe par `PYTHONPATH=src`, mais Vercel
importe ce fichier à la racine du projet où `reyo` n'est pas encore importable.
"""

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
SOURCE = RACINE / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from reyo.api.main import app  # noqa: E402  (après l'ajustement de sys.path)

__all__ = ["app"]

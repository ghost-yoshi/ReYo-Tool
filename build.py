"""Compile le frontend en mode SPA et dépose le résultat dans ./static.

Utilisé par les déploiements qui n'exécutent pas le Dockerfile (Vercel) :
`[tool.vercel.scripts] build = "python build.py"`. main.py monte ensuite ./static
sur "/", Vercel promeut les fichiers sur son CDN et la route "/" sert index.html.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
FRONT = RACINE / "frontend"
SORTIE = FRONT / ".output" / "public"
DESTINATION = RACINE / "static"


def main() -> int:
    if shutil.which("npm") is None:
        print("npm introuvable : impossible de compiler le frontend.", file=sys.stderr)
        return 1

    subprocess.run(["npm", "--prefix", str(FRONT), "ci", "--no-audit", "--no-fund"], check=True)
    subprocess.run(
        ["npm", "--prefix", str(FRONT), "run", "build"],
        check=True,
        env={**os.environ, "VITE_REYO_API_URL": "/api"},
    )

    if not SORTIE.is_dir():
        print(f"Build introuvable : {SORTIE}", file=sys.stderr)
        return 1

    # Le build SPA produit _shell.html ; StaticFiles et la route "/" cherchent index.html.
    index, coquille = SORTIE / "index.html", SORTIE / "_shell.html"
    if not index.exists() and coquille.exists():
        shutil.copyfile(coquille, index)

    shutil.rmtree(DESTINATION, ignore_errors=True)
    shutil.copytree(SORTIE, DESTINATION)
    print(f"Frontend prêt dans {DESTINATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

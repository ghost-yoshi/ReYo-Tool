import json
import os
import re
import unicodedata
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from reyo.prompts import PROMPT_STRUCTURE, PROMPT_STRUCTURE_VERSION, construire_prompt_reparation
from reyo.schema import Structure
from reyo.validation import valider_structure
from reyo.render.theme import THEMES_PREDEFINIS, ThemeConfig
from reyo.render.renderer_docx import DocxRenderer
from fastapi.middleware.cors import CORSMiddleware

#utils


MAX_CORPS_OCTETS = 2 * 1024 * 1024  # 2 Mio


async def _reponse_413(send) -> None:
    corps = json.dumps({"detail": "Requête trop volumineuse (2 Mio maximum)."}).encode()
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(corps)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": corps})


class LimiteurTailleCorps:
    """Refuse en 413 les corps de requête au-delà de `max_octets`.

    Le corps est tamponné jusqu'à la limite puis rejoué à l'application : inutile
    de laisser FastAPI désérialiser plusieurs mégaoctets pour rien. La limite est
    globale ; un futur endpoint d'upload de captures aura besoin de la sienne.
    """

    def __init__(self, app, max_octets: int = MAX_CORPS_OCTETS) -> None:
        self.app = app
        self.max_octets = max_octets

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        annonce = dict(scope.get("headers") or []).get(b"content-length")
        if annonce and annonce.isdigit() and int(annonce) > self.max_octets:
            await _reponse_413(send)
            return

        corps = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            corps.extend(message.get("body", b""))
            if len(corps) > self.max_octets:
                await _reponse_413(send)
                return
            if not message.get("more_body", False):
                break

        envoye = False

        async def receive_rejoue():
            nonlocal envoye
            if envoye:
                return await receive()
            envoye = True
            return {"type": "http.request", "body": bytes(corps), "more_body": False}

        await self.app(scope, receive_rejoue, send)


def _origines_autorisees(valeur: str | None = None) -> list[str]:
    """Origines autorisées, fournies par REYO_CORS_ORIGINS (séparées par des virgules).

    La liste ne contient jamais "*" : le wildcard est interdit dès que des
    credentials sont autorisés, et Starlette le remplacerait par un reflet de
    l'origine appelante, ce qui revient à ouvrir l'API à tout site.
    """
    brute = os.getenv("REYO_CORS_ORIGINS", "") if valeur is None else valeur
    return [origine.strip().rstrip("/") for origine in brute.split(",") if origine.strip()]


_ORIGINES_CORS = _origines_autorisees()

app = FastAPI(title="ReYo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGINES_CORS,
    # En conteneur le front est servi par ce même service (même origine, pas de CORS).
    # En développement il vient de Vite, d'où l'autorisation des hôtes locaux.
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LimiteurTailleCorps, max_octets=MAX_CORPS_OCTETS)

# Toutes les routes métier vivent sous /api, ce qui correspond au VITE_REYO_API_URL
# utilisé pour compiler le frontend (Dockerfile).
router = APIRouter(prefix="/api")

class RenderRequest(BaseModel):
    structure: Structure
    theme: str = "academic"


class ValidateRequest(BaseModel):
    texte: str = Field(alias="json", min_length=1, max_length=1_000_000)


class ValidateResponse(BaseModel):
    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    structure: dict[str, Any] | None = None
    prompt_reparation: str | None = None


class PromptStructureResponse(BaseModel):
    version: str
    prompt: str


@router.get("/themes", response_model=dict[str, ThemeConfig])
def themes() -> dict[str, ThemeConfig]:
    return THEMES_PREDEFINIS


@router.get("/prompt-structure", response_model=PromptStructureResponse)
def prompt_structure() -> PromptStructureResponse:
    return PromptStructureResponse(version=PROMPT_STRUCTURE_VERSION, prompt=PROMPT_STRUCTURE)


@router.get("/schema")
def schema() -> dict[str, Any]:
    return Structure.model_json_schema()


@router.post("/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest) -> ValidateResponse:
    resultat = valider_structure(req.texte)
    return ValidateResponse(
        ok=resultat.ok,
        errors=resultat.erreurs,
        warnings=resultat.avertissements,
        structure=resultat.structure.model_dump(mode="json") if resultat.structure else None,
        prompt_reparation=(
            construire_prompt_reparation(req.texte, resultat.erreurs) if not resultat.ok else None
        ),
    )

def _etat_service() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health")
def health() -> dict[str, str]:
    """Sonde interrogée par le frontend (base + /health)."""
    return _etat_service()


@app.get("/health", include_in_schema=False)
def health_racine() -> dict[str, str]:
    """Sonde du conteneur (Docker HEALTHCHECK), hors préfixe /api."""
    return _etat_service()


_CARACTERES_DANGEREUX = re.compile(r'[\x00-\x1f\x7f"\\/:*?<>|]')
_CARACTERES_ASCII = re.compile(r"[^A-Za-z0-9._-]")
_LONGUEUR_MAX_TIGE = 100


def _nom_fichier_sur(chemin: Path) -> str:
    """Nom de fichier utilisable dans un en-tête : pas de CR/LF, de guillemet ni de chemin.

    Le nom vient du JSON produit par l'IA (`regles_rendu.filename`), donc d'une source
    non digne de confiance : il ne doit jamais pouvoir casser l'en-tête HTTP.
    """
    nom = Path(chemin).name
    nom = _CARACTERES_DANGEREUX.sub("_", nom).strip(" ._") or "compte_rendu.docx"
    tige = nom[:-5] if nom.lower().endswith(".docx") else nom
    return f"{(tige.strip(' ._') or 'compte_rendu')[:_LONGUEUR_MAX_TIGE]}.docx"


def _entete_telechargement(nom: str) -> str:
    """En-tête RFC 6266 : repli ASCII pour les vieux clients + nom exact en filename*."""
    ascii_nom = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    ascii_nom = _CARACTERES_ASCII.sub("_", ascii_nom).strip(" ._") or "compte_rendu"
    if not ascii_nom.lower().endswith(".docx"):
        ascii_nom = f"{ascii_nom}.docx"
    return f'attachment; filename="{ascii_nom}"; filename*=UTF-8\'\'{quote(nom)}'


@router.post("/render")
def render(req: RenderRequest):
    if req.theme not in THEMES_PREDEFINIS:
        raise HTTPException(422, f'theme inconnu: {req.theme}')
    r = DocxRenderer(req.structure, THEMES_PREDEFINIS[req.theme])
    buf = r.to_bytes()
    return StreamingResponse(
        BytesIO(buf),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": _entete_telechargement(_nom_fichier_sur(r.filename))
        },
    )


app.include_router(router)

# Le frontend compilé (frontend/dist copié dans ./static par le Dockerfile) est servi à
# la racine. Le montage vient en dernier : les routes /api définies plus haut restent
# prioritaires. Hors conteneur (dev local) le dossier n'existe pas, on ne monte rien.
_REPERTOIRE_STATIQUE = Path(__file__).resolve().parents[3] / "static"
if _REPERTOIRE_STATIQUE.is_dir():
    app.mount("/", StaticFiles(directory=_REPERTOIRE_STATIQUE, html=True), name="static")

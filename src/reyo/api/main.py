from io import BytesIO
from pathlib import Path
from typing import Any

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


app = FastAPI(title="ReYo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En dev, "*" autorise tout le monde. En prod, mets ["http://localhost:8080"]
    allow_credentials=True,
    allow_methods=["*"],  # Autorise GET, POST, OPTIONS, etc.
    allow_headers=["*"],  # Autorise tous les en-têtes
)

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


@router.post("/render")
def render(req: RenderRequest):
    if req.theme not in THEMES_PREDEFINIS:
        raise HTTPException(422, f'theme inconnu: {req.theme}')
    r = DocxRenderer(req.structure, THEMES_PREDEFINIS[req.theme])
    buf = r.to_bytes()
    return StreamingResponse(
        BytesIO(buf),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{r.filename.name}"'},

    )


app.include_router(router)

# Le frontend compilé (frontend/dist copié dans ./static par le Dockerfile) est servi à
# la racine. Le montage vient en dernier : les routes /api définies plus haut restent
# prioritaires. Hors conteneur (dev local) le dossier n'existe pas, on ne monte rien.
_REPERTOIRE_STATIQUE = Path(__file__).resolve().parents[3] / "static"
if _REPERTOIRE_STATIQUE.is_dir():
    app.mount("/", StaticFiles(directory=_REPERTOIRE_STATIQUE, html=True), name="static")

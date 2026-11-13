from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from reyo.schema import Structure
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

class RenderRequest(BaseModel):
    structure: Structure
    theme: str = "academic"


@app.get("/themes", response_model=dict[str, ThemeConfig])
def themes() -> dict[str, ThemeConfig]:
    return THEMES_PREDEFINIS

@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.post("/render")
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

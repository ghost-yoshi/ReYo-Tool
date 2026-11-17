import json
from pathlib import Path

from fastapi.testclient import TestClient

from reyo.api.main import (
    _entete_telechargement,
    _nom_fichier_sur,
    _origines_autorisees,
    app,
)
from reyo.schema import MAX_NOEUDS, MAX_PROFONDEUR

FIXTURE = Path(__file__).parent / "fixtures" / "testv1.json"


def test_nom_fichier_neutre_les_caracteres_dangereux():
    nom = _nom_fichier_sur(Path('evil"\r\nX-Injected: 1.docx'))
    assert "\r" not in nom and "\n" not in nom and '"' not in nom
    assert ":" not in nom and "/" not in nom
    assert nom.endswith(".docx")


def test_nom_fichier_ne_conserve_pas_de_chemin():
    assert _nom_fichier_sur(Path("../../etc/passwd")) == "passwd.docx"


def test_entete_respecte_rfc6266():
    entete = _entete_telechargement("réseaux_tp1.docx")
    assert "filename*=UTF-8''r%C3%A9seaux_tp1.docx" in entete
    assert 'filename="reseaux_tp1.docx"' in entete


def test_render_neutralise_un_nom_de_fichier_malicieux():
    structure = json.loads(FIXTURE.read_text(encoding="utf-8"))
    structure["regles_rendu"]["filename"] = 'ra"pport\r\nX-Injected: oui.docx'

    response = TestClient(app).post("/api/render", json={"structure": structure, "theme": "academic"})

    assert response.status_code == 200
    assert "x-injected" not in {cle.lower() for cle in response.headers}
    disposition = response.headers["content-disposition"]
    assert disposition == (
        'attachment; filename="ra_pport__X-Injected__oui.docx"; '
        "filename*=UTF-8''ra_pport__X-Injected_%20oui.docx"
    )


def test_render_refuse_un_arbre_trop_grand():
    structure = json.loads(FIXTURE.read_text(encoding="utf-8"))
    structure["noeuds"] = [
        {"id": f"n{i}", "type": "info", "enonce": "x", "attendu": [], "enfants": []}
        for i in range(MAX_NOEUDS + 1)
    ]

    reponse = TestClient(app).post(
        "/api/render", json={"structure": structure, "theme": "academic"}
    )
    assert reponse.status_code == 422


def test_render_refuse_un_arbre_trop_profond():
    structure = json.loads(FIXTURE.read_text(encoding="utf-8"))
    racine = {"id": "r", "type": "info", "enonce": "x", "attendu": [], "enfants": []}
    structure["noeuds"] = [racine]
    courant = racine
    for index in range(MAX_PROFONDEUR + 5):
        enfant = {"id": f"p{index}", "type": "info", "enonce": "x", "attendu": [], "enfants": []}
        courant["enfants"] = [enfant]
        courant = enfant

    reponse = TestClient(app).post(
        "/api/render", json={"structure": structure, "theme": "academic"}
    )
    assert reponse.status_code == 422


def test_corps_trop_volumineux_refuse():
    reponse = TestClient(app).post(
        "/api/render",
        content=b"{" + b" " * (3 * 1024 * 1024) + b"}",
        headers={"content-type": "application/json"},
    )
    assert reponse.status_code == 413


def test_origines_cors_jamais_wildcard():
    assert "*" not in _origines_autorisees("https://a.example, https://b.example/")
    assert _origines_autorisees("https://a.example, https://b.example/") == [
        "https://a.example",
        "https://b.example",
    ]


def test_cors_ne_combine_pas_wildcard_et_credentials():
    configuration = next(m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware")
    assert configuration.kwargs["allow_credentials"] is False
    assert "*" not in configuration.kwargs["allow_origins"]


def test_cors_autorise_le_dev_local_et_refuse_un_site_tiers():
    client = TestClient(app)

    local = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert local.headers.get("access-control-allow-origin") == "http://localhost:5173"

    tiers = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in tiers.headers

import json
from pathlib import Path

from reyo.api.main import ValidateRequest, app, validate
from reyo.prompts import PROMPT_STRUCTURE, PROMPT_STRUCTURE_VERSION
from reyo.validation import valider_structure

FIXTURE = Path(__file__).parent / "fixtures" / "testv1.json"


def charger() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_json_valide():
    resultat = valider_structure(FIXTURE.read_text(encoding="utf-8"))
    assert resultat.ok
    assert resultat.structure is not None
    assert resultat.erreurs == []


def test_json_illisible():
    resultat = valider_structure('{"noeuds": [}')
    assert not resultat.ok
    assert "ligne" in resultat.erreurs[0]


def test_racine_non_objet():
    resultat = valider_structure("[]")
    assert not resultat.ok
    assert resultat.erreurs == ["racine : un objet JSON est requis."]


def test_champ_invente_refuse():
    donnees = charger()
    donnees["noeuds"][0]["difficulte"] = "facile"
    resultat = valider_structure(json.dumps(donnees))
    assert not resultat.ok
    assert any(erreur.startswith("noeuds > 0") for erreur in resultat.erreurs)


def test_identifiants_dupliques():
    donnees = charger()
    donnees["noeuds"][1]["id"] = donnees["noeuds"][0]["id"]
    resultat = valider_structure(json.dumps(donnees))
    assert not resultat.ok
    assert any("identifiants dupliqués" in erreur for erreur in resultat.erreurs)


def test_format_pdf_signale_sans_bloquer():
    donnees = charger()
    donnees["regles_rendu"]["format"] = "pdf"
    resultat = valider_structure(json.dumps(donnees))
    assert resultat.ok
    assert resultat.avertissements and "DOCX" in resultat.avertissements[0]


def test_validate_renvoie_la_structure_et_le_prompt_de_reparation():
    ok = validate(ValidateRequest(json=FIXTURE.read_text(encoding="utf-8")))
    assert ok.ok and ok.structure["kind"] == "structure" and ok.prompt_reparation is None

    donnees = charger()
    donnees["noeuds"][0]["type"] = "exercice"
    invalide = json.dumps(donnees)
    echec = validate(ValidateRequest(json=invalide))
    assert not echec.ok
    assert echec.prompt_reparation is not None
    assert echec.prompt_reparation.endswith(invalide)


def test_prompt_structure_versionne():
    assert PROMPT_STRUCTURE_VERSION
    assert '"schema_version": 1' in PROMPT_STRUCTURE
    assert '[À COMPLÉTER' in PROMPT_STRUCTURE


def test_routes_p0_disponibles():
    # openapi() reflète les routes incluses quel que soit leur mode de regroupement interne.
    chemins_api = set(app.openapi()["paths"])
    assert {
        "/api/schema",
        "/api/validate",
        "/api/prompt-structure",
        "/api/render",
        "/api/health",
    } <= chemins_api

    # /health existe aussi à la racine, hors schéma OpenAPI, pour le HEALTHCHECK Docker.
    assert "/health" in {getattr(route, "path", "") for route in app.routes}

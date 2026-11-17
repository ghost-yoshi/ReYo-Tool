from pathlib import Path

import pytest
from pydantic import ValidationError

from reyo.schema import MAX_NOEUDS, MAX_PROFONDEUR, Structure

FIXTURE = Path(__file__).parent / "fixtures" / "mongo_4_3.json"


def charger() -> dict:
    import json
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_structure_valide():
    s = Structure.model_validate(charger())
    assert s.noeuds[0].enfants[0].id == "P4.3"


def test_code_ue_numerique_converti_en_texte():
    donnees = charger()
    assert isinstance(donnees["meta"]["code_ue"], int)
    s = Structure.model_validate(donnees)
    assert s.meta.code_ue == str(donnees["meta"]["code_ue"])


def _noeud(identifiant: str) -> dict:
    return {"id": identifiant, "type": "info", "enonce": "texte", "attendu": [], "enfants": []}


def test_arbre_trop_profond_refuse():
    donnees = charger()
    courant = donnees["noeuds"][0]
    for index in range(MAX_PROFONDEUR + 5):
        enfant = _noeud(f"prof{index}")
        courant["enfants"] = [enfant]
        courant = enfant

    with pytest.raises(ValidationError) as erreur:
        Structure.model_validate(donnees)
    assert "profondeur" in str(erreur.value)


def test_arbre_trop_de_noeuds_refuse():
    donnees = charger()
    donnees["noeuds"] = [_noeud(f"n{index}") for index in range(MAX_NOEUDS + 1)]

    with pytest.raises(ValidationError) as erreur:
        Structure.model_validate(donnees)
    assert "nœuds" in str(erreur.value)


def test_type_inconnu():
    donnees = charger()
    donnees["noeuds"][0]["type"] = "exercice"
    with pytest.raises(ValidationError):
        Structure.model_validate(donnees)


def test_champ_invente():
    donnees = charger()
    donnees["noeuds"][0]["difficulte"] = "facile"
    with pytest.raises(ValidationError):
        Structure.model_validate(donnees)


def test_mauvais_kind():
    donnees = charger()
    donnees["kind"] = "reponses"
    with pytest.raises(ValidationError):
        Structure.model_validate(donnees)
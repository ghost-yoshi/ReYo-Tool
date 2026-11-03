from pathlib import Path

import pytest
from pydantic import ValidationError

from reyo.schema import Structure

FIXTURE = Path(__file__).parent / "fixtures" / "mongo_4_3.json"


def charger() -> dict:
    import json
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_structure_valide():
    s = Structure.model_validate(charger())
    assert s.noeuds[0].enfants[0].id == "P4.3"


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
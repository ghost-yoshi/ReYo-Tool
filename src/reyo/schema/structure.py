from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_NOEUDS = 2000
MAX_PROFONDEUR = 50


def bornes_structure(donnees: object) -> list[str]:
    """Contrôle itératif du JSON brut : bornes de taille avant tout parsing récursif.

    Pydantic valide les nœuds en profondeur : un JSON très profond ferait échouer
    la récursion avant qu'on puisse mesurer quoi que ce soit. Ce contrôle parcourt
    donc le dictionnaire avec une pile explicite.
    """
    if not isinstance(donnees, dict):
        return []  # le schéma signalera la racine non conforme

    erreurs: list[str] = []
    racine = donnees.get("noeuds")
    if not isinstance(racine, list):
        return []

    total = 0
    profondeur_max = 0
    pile: list[tuple[Any, int]] = [(noeud, 1) for noeud in racine]
    while pile:
        noeud, profondeur = pile.pop()
        total += 1
        profondeur_max = max(profondeur_max, profondeur)
        if total > MAX_NOEUDS:
            erreurs.append(f"noeuds : plus de {MAX_NOEUDS} nœuds au total.")
            break
        if not isinstance(noeud, dict):
            continue
        enfants = noeud.get("enfants")
        if isinstance(enfants, list):
            pile.extend((enfant, profondeur + 1) for enfant in enfants)

    if profondeur_max > MAX_PROFONDEUR:
        erreurs.append(f"noeuds : profondeur {profondeur_max} supérieure à la limite de {MAX_PROFONDEUR}.")
    return erreurs


class TypeNoeud(str, Enum):
    SECTION = "section"
    CONSIGNE = "consigne"
    QUESTION = "question"
    CAS = "cas"
    INFO = "info"


class Attendu(str, Enum):
    TEXTE = "texte"
    COMMANDE = "commande"
    CAPTURE = "capture"

class _Base(BaseModel):
    "un champ inventé par l'ia devient automatiquement une erreur"
    model_config = ConfigDict(extra="forbid")

class Meta(_Base):
    matiere: str
    code_ue: str
    titre: str
    enseignant: str | None = None

    @field_validator("code_ue", mode="before")
    @classmethod
    def _code_ue_en_texte(cls, valeur: object) -> object:
        """Accepte un code UE numérique (331) : une IA le renvoie souvent sans guillemets.

        Les autres champs de `meta` restent stricts : une erreur de type y est
        révélatrice, alors qu'un code UE est un identifiant dont le type n'a pas
        de sens pour l'utilisateur. Un booléen n'est pas converti.
        """
        if isinstance(valeur, bool):
            return valeur
        if isinstance(valeur, int):
            return str(valeur)
        if isinstance(valeur, float):
            return str(int(valeur)) if valeur.is_integer() else str(valeur)
        return valeur

class ReglesRendu(_Base):
    entete: list[str] = Field(default_factory=list)
    format: Literal["pdf", "docx"] = "pdf"
    filename: str | None = None

class Noeud(_Base):
    id: str = Field(min_length=1)
    type: TypeNoeud
    enonce: str
    attendu: list[Attendu] = Field(default_factory=list)
    enfants: list["Noeud"] = Field(default_factory=list)

class Structure(_Base):
    schema_version: Literal[1]
    kind: Literal["structure"]
    meta: Meta
    regles_rendu: ReglesRendu = Field(default_factory=ReglesRendu)
    noeuds: list[Noeud]

    @model_validator(mode="before")
    @classmethod
    def _borner_arbre(cls, donnees: object) -> object:
        """Refuse un arbre démesuré avant que Pydantic ne le parcoure récursivement."""
        erreurs = bornes_structure(donnees)
        if erreurs:
            raise ValueError(" ".join(erreurs))
        return donnees


if __name__ =="__main__":
    from pydantic import ValidationError
    from reyo.schema import Structure

    texte = open("tests/fixtures/mongo_4_3.json", encoding="utf-8").read()

    try:
        s = Structure.model_validate_json(texte)
    except ValidationError as e:
        for erreur in e.errors():
            chemin = " > ".join(str(x) for x in erreur["loc"])
            print(f"{chemin} : {erreur['msg']}")
    else:
        print(s.meta.titre)
        print(s.noeuds[0].enfants[0].attendu)
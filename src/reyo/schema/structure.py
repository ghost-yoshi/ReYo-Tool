from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


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
    code_ue: int
    titre: str
    enseignant: str | None = None

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
"""Validation d'un JSON `structure` produit par une IA externe.

Le schéma Pydantic reste la référence : ce module ajoute les contrôles que le
schéma seul ne peut pas exprimer (identifiants uniques, profondeur, racine vide)
et renvoie des messages lisibles, utilisés par l'API et le prompt de réparation.
"""
import json
from dataclasses import dataclass, field

from pydantic import ValidationError

from reyo.schema import MAX_PROFONDEUR, Noeud, Structure


@dataclass(frozen=True)
class ResultatValidation:
    ok: bool
    structure: Structure | None = None
    erreurs: list[str] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)


def _chemin(loc: tuple) -> str:
    return " > ".join(str(partie) for partie in loc) or "racine"


def _profondeur(noeuds: list[Noeud], niveau: int = 1) -> int:
    return max((max(niveau, _profondeur(noeud.enfants, niveau + 1)) for noeud in noeuds), default=0)


def _identifiants(noeuds: list[Noeud]):
    for noeud in noeuds:
        yield noeud.id
        yield from _identifiants(noeud.enfants)


def _erreurs_croisees(structure: Structure) -> list[str]:
    erreurs: list[str] = []

    if not structure.noeuds:
        erreurs.append("noeuds : au moins un nœud est requis.")

    vus: set[str] = set()
    dupliques: list[str] = []
    for identifiant in _identifiants(structure.noeuds):
        if identifiant in vus and identifiant not in dupliques:
            dupliques.append(identifiant)
        vus.add(identifiant)
    if dupliques:
        erreurs.append(f"noeuds : identifiants dupliqués ({', '.join(dupliques)}).")

    profondeur = _profondeur(structure.noeuds)
    if profondeur > MAX_PROFONDEUR:
        erreurs.append(f"noeuds : profondeur {profondeur} supérieure à la limite de {MAX_PROFONDEUR}.")

    return erreurs


def valider_structure(texte: str) -> ResultatValidation:
    """Valide un JSON brut et renvoie la structure, ou des erreurs prêtes à afficher."""
    if not texte.strip():
        return ResultatValidation(ok=False, erreurs=["Le JSON est vide."])

    try:
        donnees = json.loads(texte)
    except json.JSONDecodeError as e:
        return ResultatValidation(
            ok=False,
            erreurs=[f"JSON invalide (ligne {e.lineno}, colonne {e.colno}) : {e.msg}."],
        )
    except RecursionError:
        return ResultatValidation(ok=False, erreurs=["JSON trop profondément imbriqué."])

    if not isinstance(donnees, dict):
        return ResultatValidation(ok=False, erreurs=["racine : un objet JSON est requis."])

    try:
        structure = Structure.model_validate(donnees)
    except ValidationError as e:
        erreurs = [f"{_chemin(erreur['loc'])} : {erreur['msg']}" for erreur in e.errors()]
        return ResultatValidation(ok=False, erreurs=erreurs)

    erreurs = _erreurs_croisees(structure)
    avertissements: list[str] = []
    if structure.regles_rendu.format != "docx":
        avertissements.append(
            "regles_rendu > format : seul le DOCX est produit pour l'instant ; le document sera généré en .docx."
        )

    if erreurs:
        return ResultatValidation(ok=False, erreurs=erreurs, avertissements=avertissements)
    return ResultatValidation(ok=True, structure=structure, avertissements=avertissements)

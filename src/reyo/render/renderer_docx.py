"""Rendu DOCX d'une Structure ReYo.

Deux points d'entrée, qui partagent la même construction :
- render()   : écrit le fichier sur disque (usage local, tests)
- to_bytes() : renvoie les octets du .docx (usage API, aucun fichier écrit)
"""
import io
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

from reyo.render.theme import THEMES_PREDEFINIS, ThemeConfig
from reyo.schema import Noeud, Structure, TypeNoeud

MARQUEUR = re.compile(r"(\[À COMPLÉTER[^\]]*\])")
CAPTURE = re.compile(r"Capture : (.*?)\. Légende : (.*?)\.?$", re.DOTALL)

POLICE_CODE = "Consolas"
FOND_CODE = "F2F2F2"
COULEUR_CADRE = "808080"


class DocxRenderer:
    def __init__(
        self,
        structure: Structure,
        theme: ThemeConfig,
        output_filename: str | None = None,
    ):
        self.structure = structure
        self.theme = theme
        self.filename = self._resoudre_nom_fichier(output_filename)
        # Initialisés par construire() : l'instance est donc réutilisable
        self.doc: Document = None
        self._n_fig = 0

    # ------------------------------------------------------------------
    # Points d'entrée
    # ------------------------------------------------------------------

    def construire(self) -> Document:
        """Construit un document neuf à partir de la structure. Ne sauvegarde rien."""
        self.doc = Document()
        self._n_fig = 0
        self._configurer_marges()
        self._ecrire_titre_et_entete()
        self._parcourir_noeuds(self.structure.noeuds)
        return self.doc

    def render(self) -> Path:
        """Usage local : écrit le fichier sur disque et renvoie son chemin."""
        self.construire().save(str(self.filename))
        print(f"Document DOCX généré [{self.theme.nom}] : {self.filename.resolve()}")
        return self.filename

    def to_bytes(self) -> bytes:
        """Usage API : renvoie les octets du .docx, sans toucher au disque."""
        with io.BytesIO() as tampon:
            self.construire().save(tampon)
            return tampon.getvalue()

    # ------------------------------------------------------------------
    # Préparation
    # ------------------------------------------------------------------

    def _resoudre_nom_fichier(self, output_filename: str | None) -> Path:
        """Nom explicite, sinon celui du JSON, sinon dérivé du titre. Finit toujours par .docx."""
        if output_filename:
            nom = Path(output_filename)
        elif self.structure.regles_rendu.filename:
            nom = Path(self.structure.regles_rendu.filename)
        else:
            titre = "".join(
                c for c in self.structure.meta.titre if c.isalnum() or c in (" ", "_", "-")
            ).strip()
            nom = Path(titre or "compte_rendu")
        if nom.suffix.lower() != ".docx":
            nom = nom.with_suffix(".docx")
        return nom

    def _configurer_marges(self) -> None:
        for section in self.doc.sections:
            section.top_margin = section.bottom_margin = Inches(1)
            section.left_margin = section.right_margin = Inches(1)

    @staticmethod
    def _hex_to_rgb(hex_str: str) -> RGBColor:
        hex_str = hex_str.lstrip("#")
        return RGBColor(int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))

    # ------------------------------------------------------------------
    # Briques bas niveau
    # ------------------------------------------------------------------

    def _ajouter_texte(
        self,
        p,
        texte: str,
        *,
        taille: float | None = None,
        gras: bool = False,
        italique: bool = False,
        police: str | None = None,
        couleur: str | None = None,
    ) -> None:
        """Ajoute le texte au paragraphe, un run par morceau pour surligner les marqueurs."""
        for morceau in MARQUEUR.split(texte):
            if not morceau:
                continue
            run = p.add_run(morceau)
            run.font.name = police or self.theme.police_principale
            run.font.size = Pt(taille or self.theme.taille_texte)
            run.font.bold = gras
            run.font.italic = italique
            run.font.color.rgb = self._hex_to_rgb(couleur or self.theme.couleur_texte)
            if MARQUEUR.fullmatch(morceau):
                run.font.highlight_color = WD_COLOR_INDEX.YELLOW

    @staticmethod
    def _appliquer_fond(p, hex_fill: str) -> None:
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_fill)
        p._p.get_or_add_pPr().append(shd)

    @staticmethod
    def _appliquer_cadre(p, hex_color: str = COULEUR_CADRE) -> None:
        bordures = OxmlElement("w:pBdr")
        for cote in ("top", "left", "bottom", "right"):
            e = OxmlElement(f"w:{cote}")
            e.set(qn("w:val"), "dashed")
            e.set(qn("w:sz"), "6")
            e.set(qn("w:space"), "8")
            e.set(qn("w:color"), hex_color)
            bordures.append(e)
        p._p.get_or_add_pPr().append(bordures)

    # ------------------------------------------------------------------
    # Blocs du document
    # ------------------------------------------------------------------

    def _ecrire_titre_et_entete(self) -> None:
        meta = self.structure.meta

        p = self.doc.add_paragraph()
        self._ajouter_texte(
            p, meta.titre,
            taille=self.theme.taille_titre, gras=True, couleur=self.theme.couleur_primaire,
        )
        p.paragraph_format.space_after = Pt(8)

        lignes = list(self.structure.regles_rendu.entete)
        if meta.enseignant:
            lignes.append(f"Enseignant(s) : {meta.enseignant}")

        dernier = p
        for ligne in lignes:
            dernier = self.doc.add_paragraph()
            dernier.paragraph_format.space_after = Pt(0)
            self._ajouter_texte(dernier, ligne, taille=9.5, couleur=self.theme.couleur_secondaire)
        dernier.paragraph_format.space_after = Pt(14)

    def _bloc_titre(self, texte: str, niveau: int) -> None:
        # Style Heading (volet de navigation Word) + mise en forme du thème par-dessus
        p = self.doc.add_paragraph(style=f"Heading {niveau}")
        taille = self.theme.taille_section if niveau == 1 else self.theme.taille_texte + 1
        self._ajouter_texte(
            p, texte, taille=taille, gras=True, couleur=self.theme.couleur_primaire,
        )
        p.paragraph_format.space_before = Pt(14 if niveau == 1 else 10)
        p.paragraph_format.space_after = Pt(4)

    def _bloc_paragraphe(self, texte: str) -> None:
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        self._ajouter_texte(p, texte)

    def _bloc_commande(self, texte: str) -> None:
        p = self.doc.add_paragraph()
        self._appliquer_fond(p, FOND_CODE)  # le XML brut d'abord, le formatage ensuite
        p.paragraph_format.left_indent = Inches(0.15)
        self._ajouter_texte(p, texte, taille=9.5, police=POLICE_CODE)

    def _bloc_capture(self, texte: str) -> None:
        m = CAPTURE.match(texte)
        quoi, legende = (m.group(1), m.group(2)) if m else (texte, "")
        self._n_fig += 1

        cadre = self.doc.add_paragraph()
        self._appliquer_cadre(cadre)  # le XML brut d'abord, le formatage ensuite
        cadre.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cadre.paragraph_format.space_before = Pt(8)
        cadre.paragraph_format.keep_with_next = True  # le cadre reste collé à sa légende
        self._ajouter_texte(
            cadre, f"[Insérer la capture : {quoi}]",
            italique=True, couleur=self.theme.couleur_secondaire,
        )

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        etiquette = f"Figure {self._n_fig} : {legende}" if legende else f"Figure {self._n_fig}"
        self._ajouter_texte(p, etiquette, taille=10, italique=True)

    # ------------------------------------------------------------------
    # Parcours
    # ------------------------------------------------------------------

    @staticmethod
    def _genre(noeud: Noeud) -> str:
        """Choisit le rendu d'un nœud d'après son type, puis d'après son attendu."""
        if noeud.type == TypeNoeud.SECTION:
            return "section"
        if noeud.type == TypeNoeud.QUESTION:
            return "question"
        attendu = {getattr(a, "value", a) for a in noeud.attendu}
        if "commande" in attendu:
            return "commande"
        if "capture" in attendu:
            return "capture"
        return "paragraphe"

    def _parcourir_noeuds(self, noeuds: list[Noeud]) -> None:
        rendus = {
            "section": lambda n: self._bloc_titre(n.enonce, 1),
            "question": lambda n: self._bloc_titre(n.enonce, 2),
            "commande": lambda n: self._bloc_commande(n.enonce),
            "capture": lambda n: self._bloc_capture(n.enonce),
            "paragraphe": lambda n: self._bloc_paragraphe(n.enonce),
        }
        for noeud in noeuds:
            rendus[self._genre(noeud)](noeud)
            self._parcourir_noeuds(noeud.enfants)


if __name__ == "__main__":
    import traceback

    racine_projet = Path(__file__).resolve().parents[3]
    chemin_fixture = racine_projet / "tests" / "fixtures" / "testv1.json"

    try:
        texte = chemin_fixture.read_text(encoding="utf-8")
        s = Structure.model_validate_json(texte)
        DocxRenderer(s, theme=THEMES_PREDEFINIS["universitaire"]).render()
    except Exception:
        traceback.print_exc()  # la trace complète montre la ligne fautive
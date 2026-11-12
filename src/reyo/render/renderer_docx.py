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


class DocxRenderer:
    def __init__(self, structure: Structure, theme: ThemeConfig, output_filename: str | None = None):
        self.structure = structure
        self.theme = theme
        self._n_fig = 0

        if output_filename:
            self.filename = Path(output_filename)
        elif self.structure.regles_rendu.filename:
            self.filename = Path(self.structure.regles_rendu.filename)
        else:
            titre_nettoye = "".join(
                c for c in self.structure.meta.titre if c.isalnum() or c in (" ", "_", "-")
            ).strip()
            self.filename = Path(f"{titre_nettoye}.docx")

        # Garde : le fichier finit toujours par .docx
        if self.filename.suffix.lower() != ".docx":
            self.filename = self.filename.with_suffix(".docx")

        self.doc = Document()
        self._configurer_marges()

    def _configurer_marges(self):
        for section in self.doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

    def _hex_to_rgb(self, hex_str: str) -> RGBColor:
        hex_str = hex_str.lstrip("#")
        return RGBColor(int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))

    def render(self):
        meta = self.structure.meta

        # 1. Titre principal
        p_titre = self.doc.add_paragraph()
        run_titre = p_titre.add_run(meta.titre)
        run_titre.font.name = self.theme.police_principale
        run_titre.font.size = Pt(self.theme.taille_titre)
        run_titre.font.bold = True
        run_titre.font.color.rgb = self._hex_to_rgb(self.theme.couleur_primaire)
        p_titre.paragraph_format.space_after = Pt(8)

        # 2. Entête : une ligne par entrée de regles_rendu.entete
        lignes = list(self.structure.regles_rendu.entete)
        if meta.enseignant:
            lignes.append(f"Enseignant(s) : {meta.enseignant}")
        for ligne in lignes:
            p = self.doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            self._texte(p, ligne, taille=9.5, couleur=self.theme.couleur_secondaire)
        self.doc.paragraphs[-1].paragraph_format.space_after = Pt(14)

        # 3. Parcours récursif des nœuds
        self._parcourir_noeuds(self.structure.noeuds)

        # 4. Sauvegarde
        self.doc.save(str(self.filename))
        print(f"Document DOCX généré [{self.theme.nom}] : {self.filename.resolve()}")

    # ---------- briques de mise en forme ----------

    def _texte(self, p, texte, taille=None, italique=False, police=None, couleur=None):
        # Un run par morceau, pour surligner les marqueurs [À COMPLÉTER : ...]
        for morceau in MARQUEUR.split(texte):
            if not morceau:
                continue
            run = p.add_run(morceau)
            run.font.name = police or self.theme.police_principale
            run.font.size = Pt(taille or self.theme.taille_texte)
            run.font.italic = italique
            run.font.color.rgb = self._hex_to_rgb(couleur or self.theme.couleur_texte)
            if MARQUEUR.fullmatch(morceau):
                run.font.highlight_color = WD_COLOR_INDEX.YELLOW

    def _fond(self, p, hex_fill):
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_fill)
        p._p.get_or_add_pPr().append(shd)

    def _cadre(self, p):
        bord = OxmlElement("w:pBdr")
        for cote in ("top", "left", "bottom", "right"):
            e = OxmlElement(f"w:{cote}")
            e.set(qn("w:val"), "dashed")
            e.set(qn("w:sz"), "6")
            e.set(qn("w:space"), "8")
            e.set(qn("w:color"), "808080")
            bord.append(e)
        p._p.get_or_add_pPr().append(bord)

    def _titre(self, texte, niveau):
        # Style Heading (volet de navigation Word) + mise en forme du thème par-dessus
        p = self.doc.add_paragraph(style=f"Heading {niveau}")
        taille = self.theme.taille_section if niveau == 1 else self.theme.taille_section - 3
        run = p.add_run(texte)
        run.font.name = self.theme.police_principale
        run.font.size = Pt(taille)
        run.font.bold = True
        run.font.color.rgb = self._hex_to_rgb(self.theme.couleur_primaire)
        p.paragraph_format.space_before = Pt(14 if niveau == 1 else 10)
        p.paragraph_format.space_after = Pt(4)

    def _bloc_commande(self, texte):
        p = self.doc.add_paragraph()
        self._fond(p, "F2F2F2")
        p.paragraph_format.left_indent = Inches(0.15)
        self._texte(p, texte, taille=9.5, police="Consolas")

    def _bloc_capture(self, texte):
        m = CAPTURE.match(texte)
        quoi, legende = (m.group(1), m.group(2)) if m else (texte, "")
        self._n_fig += 1
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.keep_with_next = True  # le cadre reste collé à sa légende
        self._cadre(p)
        self._texte(p, f"[Insérer la capture : {quoi}]", italique=True,
                    couleur=self.theme.couleur_secondaire)
        c = self.doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._texte(c, f"Figure {self._n_fig} : {legende}", taille=10, italique=True)

    def _parcourir_noeuds(self, noeuds: list[Noeud]):
        for noeud in noeuds:
            attendu = [getattr(a, "value", a) for a in noeud.attendu]
            if noeud.type == TypeNoeud.SECTION:
                self._titre(noeud.enonce, 1)
            elif noeud.type == TypeNoeud.QUESTION:
                self._titre(noeud.enonce, 2)
            elif "commande" in attendu:
                self._bloc_commande(noeud.enonce)
            elif "capture" in attendu:
                self._bloc_capture(noeud.enonce)
            else:
                p = self.doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                self._texte(p, noeud.enonce)
            self._parcourir_noeuds(noeud.enfants)


if __name__ == "__main__":
    import traceback

    racine_projet = Path(__file__).resolve().parents[3]
    chemin_fixture = racine_projet / "tests" / "fixtures" / "testv1.json"
    texte = open(chemin_fixture, encoding="utf-8").read()

    try:
        s = Structure.model_validate_json(texte)
        DocxRenderer(s, theme=THEMES_PREDEFINIS["academic"]).render()
    except Exception:
        traceback.print_exc()  # le message seul masque l'origine de l'erreur
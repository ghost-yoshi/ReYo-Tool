from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from reyo.schema import Structure, Noeud, TypeNoeud
from reyo.render.theme import ThemeConfig, THEMES_PREDEFINIS

class DocxRenderer:
    def __init__(self, structure: Structure, theme: ThemeConfig, output_filename: str | None = None):
        self.structure = structure
        self.theme = theme
        
        # Sécurisation stricte du nom de fichier de sortie
        if output_filename:
            self.filename = Path(output_filename)
        elif self.structure.regles_rendu.filename:
            self.filename = Path(self.structure.regles_rendu.filename)
        else:
            # Nom par défaut propre basé sur le titre
            titre_nettoye = "".join(c for c in self.structure.meta.titre if c.isalnum() or c in (' ', '_', '-')).strip()
            self.filename = Path(f"{titre_nettoye}.docx")

        self.doc = Document()
        self._configurer_marges()

    def _configurer_marges(self):
        for section in self.doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

    def _hex_to_rgb(self, hex_str: str) -> RGBColor:
        hex_str = hex_str.lstrip('#')
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return RGBColor(r, g, b)

    def render(self):
        meta = self.structure.meta

        # 1. Titre principal
        p_titre = self.doc.add_paragraph()
        run_titre = p_titre.add_run(meta.titre)
        run_titre.font.name = self.theme.police_principale
        run_titre.font.size = Pt(self.theme.taille_titre)
        run_titre.font.bold = True
        run_titre.font.color.rgb = self._hex_to_rgb(self.theme.couleur_primaire)
        p_titre.paragraph_format.space_after = Pt(6)

        # 2. Métadonnées
        p_meta = self.doc.add_paragraph()
        meta_text = f"Matière : {meta.matiere} | Code UE : {meta.code_ue}"
        if meta.enseignant:
            meta_text += f" | Enseignant : {meta.enseignant}"
        
        run_meta = p_meta.add_run(meta_text)
        run_meta.font.name = self.theme.police_principale
        run_meta.font.size = Pt(9.5)
        run_meta.font.color.rgb = self._hex_to_rgb(self.theme.couleur_secondaire)
        p_meta.paragraph_format.space_after = Pt(18)

        # 3. Parcours récursif des nœuds
        self._parcourir_noeuds(self.structure.noeuds)

        # 4. Sauvegarde sécurisée (en convertissant le chemin Path en string absolue ou relative explicite)
        self.doc.save(str(self.filename))
        print(f"Document DOCX généré [{self.theme.nom}] : {self.filename.resolve()}")

    def _parcourir_noeuds(self, noeuds: list[Noeud], niveau: int = 0):
        for noeud in noeuds:
            p = self.doc.add_paragraph()
            
            if niveau > 0:
                p.paragraph_format.left_indent = Inches(niveau * 0.25)

            prefixe_id = f"[{noeud.id}] " if noeud.id else ""
            texte_complet = f"{prefixe_id}{noeud.enonce}"

            if noeud.type == TypeNoeud.SECTION:
                run = p.add_run(texte_complet)
                run.font.name = self.theme.police_principale
                run.font.size = Pt(self.theme.taille_section)
                run.font.bold = True
                run.font.color.rgb = self._hex_to_rgb(self.theme.couleur_primaire)
                p.paragraph_format.space_before = Pt(12)
                p.paragraph_format.space_after = Pt(4)
            else:
                run = p.add_run(texte_complet)
                run.font.name = self.theme.police_principale
                run.font.size = Pt(self.theme.taille_texte)
                run.font.color.rgb = self._hex_to_rgb(self.theme.couleur_texte)

                if noeud.attendu:
                    run_att = p.add_run(f"  (Attendu : {', '.join(noeud.attendu)})")
                    run_att.font.name = self.theme.police_principale
                    run_att.font.size = Pt(9.5)
                    run_att.font.italic = True
                    run_att.font.color.rgb = self._hex_to_rgb(self.theme.couleur_secondaire)

                p.paragraph_format.space_after = Pt(4)

            if noeud.enfants:
                self._parcourir_noeuds(noeud.enfants, niveau + 1)


if __name__ == "__main__":
    racine_projet = Path(__file__).resolve().parents[3]
    chemin_fixture = racine_projet / "tests" / "fixtures" / "testv1.json"

    texte = open(chemin_fixture, encoding="utf-8").read()

    try:
        s = Structure.model_validate_json(texte)
        theme_choisi = THEMES_PREDEFINIS["academic"]
        
        renderer = DocxRenderer(s, theme=theme_choisi)
        renderer.render()

    except Exception as e:
        print(f"Erreur : {e}")
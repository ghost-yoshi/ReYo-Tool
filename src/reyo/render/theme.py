from pydantic import BaseModel, Field


class ThemeConfig(BaseModel):
    nom: str = "Default Theme"
    police_principale: str = "Calibri"
    couleur_primaire: str = "2B6CB0"      # Hex sans le '#' pour python-docx
    couleur_secondaire: str = "4A5568"
    couleur_texte: str = "2D3748"
    taille_titre: int = 18
    taille_section: int = 14
    taille_texte: int = 11

THEMES_PREDEFINIS = {
    "academic": ThemeConfig(
        nom="Academic Clean",
        police_principale="Times New Roman",
        couleur_primaire="000000",
        couleur_secondaire="333333",
        couleur_texte="111111",
        taille_titre=16,
        taille_section=13,
        taille_texte=12
    ),
    "modern_tech": ThemeConfig(
        nom="Modern Tech (Yoshi style)",
        police_principale="Segoe UI",
        couleur_primaire="2B6CB0",
        couleur_secondaire="319795",
        couleur_texte="2D3748",
        taille_titre=18,
        taille_section=14,
        taille_texte=11
    )
}
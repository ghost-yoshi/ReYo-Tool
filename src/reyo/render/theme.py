from pydantic import BaseModel


class ThemeConfig(BaseModel):
    """Mise en forme d'un thème de compte rendu (DOCX + aperçu frontend)."""

    nom: str = "Rapport académique"
    description: str = "Mise en page institutionnelle pour un rapport universitaire."
    police_principale: str = "Calibri"
    couleur_primaire: str = "1F3864"      # Hex sans le '#' pour python-docx
    couleur_secondaire: str = "5B6B7F"
    couleur_texte: str = "222222"
    couleur_fond: str = "FFFFFF"          # Utilisé par l'aperçu (le DOCX reste blanc)
    taille_titre: int = 20
    taille_section: int = 14
    taille_texte: int = 11


THEMES_PREDEFINIS = {
    "academic": ThemeConfig(
        nom="Rapport académique",
        description="Sobre et institutionnel, pour un rapport ou un devoir universitaire.",
        police_principale="Times New Roman",
        couleur_primaire="1F3864",
        couleur_secondaire="5B6B7F",
        couleur_texte="222222",
        couleur_fond="F7F8FA",
        taille_titre=20,
        taille_section=14,
        taille_texte=11,
    ),
    "compte_rendu_tp": ThemeConfig(
        nom="Compte rendu de TP",
        description="Bleu et accent orange, pour un compte rendu de travaux pratiques.",
        police_principale="Calibri",
        couleur_primaire="1D4E89",
        couleur_secondaire="9A3412",
        couleur_texte="1F2937",
        couleur_fond="F8FAFC",
        taille_titre=20,
        taille_section=14,
        taille_texte=11,
    ),
    "modern_tech": ThemeConfig(
        nom="Rapport informatique",
        description="Titres teal et ton technique, pour un projet de développement ou de réseaux.",
        police_principale="Segoe UI",
        couleur_primaire="0F766E",
        couleur_secondaire="475569",
        couleur_texte="1F2937",
        couleur_fond="F0FDFA",
        taille_titre=20,
        taille_section=14,
        taille_texte=11,
    ),
    "universitaire": ThemeConfig(
        nom="Mémoire universitaire",
        description="Grands titres bleu marine et texte dense, pour un mémoire ou une thèse.",
        police_principale="Cambria",
        couleur_primaire="1B2A4A",
        couleur_secondaire="6B7280",
        couleur_texte="1A1A1A",
        couleur_fond="F8F7F4",
        taille_titre=24,
        taille_section=15,
        taille_texte=12,
    ),
    "classique_bordeaux": ThemeConfig(
        nom="Rapport de stage",
        description="Bordeaux élégant, pour un rapport de stage ou un dossier professionnel.",
        police_principale="Georgia",
        couleur_primaire="6D1A36",
        couleur_secondaire="6B5B5B",
        couleur_texte="2B2B2B",
        couleur_fond="FBF7F8",
        taille_titre=20,
        taille_section=14,
        taille_texte=11,
    ),
    "rapport_ingenieur": ThemeConfig(
        nom="Rapport d'ingénieur",
        description="Bleu profond et structure claire, pour un projet d'ingénierie ou un PFE.",
        police_principale="Calibri",
        couleur_primaire="14395E",
        couleur_secondaire="475569",
        couleur_texte="1F2933",
        couleur_fond="F5F8FB",
        taille_titre=21,
        taille_section=14,
        taille_texte=11,
    ),
    "minimal_gris": ThemeConfig(
        nom="Compte rendu minimaliste",
        description="Noir et gris, sans fioriture, pour un compte rendu de TP court.",
        police_principale="Arial",
        couleur_primaire="27272A",
        couleur_secondaire="71717A",
        couleur_texte="27272A",
        couleur_fond="FAFAFA",
        taille_titre=19,
        taille_section=13,
        taille_texte=11,
    ),
    "nature_vert": ThemeConfig(
        nom="Rapport de laboratoire",
        description="Vert forêt et ton posé, pour les sciences expérimentales.",
        police_principale="Trebuchet MS",
        couleur_primaire="1E4D2B",
        couleur_secondaire="4A7C59",
        couleur_texte="1F2A1F",
        couleur_fond="F6FAF7",
        taille_titre=20,
        taille_section=14,
        taille_texte=11,
    ),
    "litteraire": ThemeConfig(
        nom="Rapport littéraire",
        description="Serif classique et brun chaud, pour une analyse de texte ou une dissertation.",
        police_principale="Garamond",
        couleur_primaire="3E2C1C",
        couleur_secondaire="8B6B4A",
        couleur_texte="2A2016",
        couleur_fond="FBF8F3",
        taille_titre=22,
        taille_section=15,
        taille_texte=12,   # Garamond est petite à corps égal, d'où 12
    ),
    "accessible": ThemeConfig(
        nom="Compte rendu accessible",
        description="Contraste élevé et grande lisibilité, pour un rendu accessible à tous.",
        police_principale="Verdana",
        couleur_primaire="000000",
        couleur_secondaire="0047AB",
        couleur_texte="000000",
        couleur_fond="FFFFFF",
        taille_titre=19,
        taille_section=14,
        taille_texte=12,   # Verdana est large, déjà très lisible à 12
    ),
}

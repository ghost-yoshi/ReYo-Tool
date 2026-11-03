from dataclasses import dataclass, replace
from io import BytesIO
from uuid import uuid4
from PIL import Image, UnidentifiedImageError


FORMATS_ACCEPTES = {"PNG": "png", "JPEG": "jpeg", "WEBP": "webp"}
TAILLE_MAX = 10 * 1024 * 1024  # 10 Mo


class CaptureInvalide(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _imageAnalyzer(octets: bytes) -> tuple[str, int, int]:
    """ Renvoie (format, largeur, hauteur) ou leve une exceptoin"""
    try:
        with Image.open(BytesIO(octets)) as img:
            img.verify()
        with Image.open(BytesIO(octets)) as img: 
            raw_format = img.format
            largeur, hauteur = img.size
    except UnidentifiedImageError as e :
        raise CaptureInvalide("FORMAT_NON_SUPPORTEE", "ce fichier n'est pas pas une image reconnu")
    except OSError as e :
        raise CaptureInvalide("IMAGE_ILLISIBLE", "l'image semble corrompue.") from e

    if raw_format not in FORMATS_ACCEPTES:
        raise CaptureInvalide("FORMAT_NON_SUPPORTE", f"Format {raw_format} non accepté.")
    return FORMATS_ACCEPTES[raw_format], largeur, hauteur


@dataclass(frozen=True)
class Capture:
    id: str
    noeud_id: str
    contenu: bytes
    format: str
    largeur: int
    hauteur: int
    legend: str = ""

    @classmethod
    def depuis_octets(cls, noeud_id: str, octets: bytes, legend: str = "") -> "Capture":
        if not octets:
            raise CaptureInvalide("IMAGE_VIDE", "Aucune donnée reçue.")
        if len(octets) > TAILLE_MAX:
            raise CaptureInvalide("IMAGE_TROP_LOURDE", "L'image dépasse 10 Mo.")
        format_, largeur, hauteur = _imageAnalyzer(octets=octets)

        return cls ( 
            id=uuid4().hex,
            noeud_id=noeud_id,
            contenu=octets,
            format=format_,
            largeur=largeur,
            hauteur=hauteur,
            legend=legend,
        )

    @property
    def extension(self) -> str:
        return "jpg" if self.format == "jpeg" else self.format

    def with_legend(self, legend: str) -> "Capture":
        return replace(self, legend= legend)

if __name__ == "__main__":
    octets = open("capture.png", "rb").read()   # côté CLI, pas dans le cœur
    c = Capture.depuis_octets("P4.4.3", octets, "Résultat du filtre")

    c.largeur                  # lu depuis l'image
    c.extension                # "png"
    c2 = c.with_legend("Autre légende")   # nouvelle capture, c inchangée
    c.legend = "x"            # FrozenInstanceError
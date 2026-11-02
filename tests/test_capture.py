from io import BytesIO
import pytest
from PIL import Image
from reyo.captures.capture import Capture, CaptureInvalide

def png(largeur=10, hauteur=5) -> bytes:
    tampon = BytesIO()
    Image.new("RGB", (largeur, hauteur)).save(tampon, format="PNG")
    return tampon.getvalue()

def test_capture_valide():
    c = Capture.depuis_octets("P1", png(10, 5))
    assert (c.format, c.largeur, c.hauteur) == ("png", 10, 5)

def test_image_vide():
    with pytest.raises(CaptureInvalide) as e:
        Capture.depuis_octets("P1", b"")
    assert e.value.code == "IMAGE_VIDE"

def test_fichier_non_image():
    with pytest.raises(CaptureInvalide) as e:
        Capture.depuis_octets("P1", b"%PDF-1.4 pas une image")
    assert e.value.code == "FORMAT_NON_SUPPORTE"
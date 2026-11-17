from io import BytesIO

import pytest
from PIL import Image

import reyo.captures.capture as module_capture
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


def test_image_trop_de_pixels_refusee(monkeypatch):
    monkeypatch.setattr(module_capture, "MAX_PIXELS", 100)

    with pytest.raises(CaptureInvalide) as e:
        Capture.depuis_octets("P1", png(20, 20))
    assert e.value.code == "IMAGE_TROP_GRANDE"


def test_decompression_bomb_refusee(monkeypatch):
    """Un petit fichier peut décrire une image énorme : Pillow doit refuser avant décodage."""
    monkeypatch.setattr(module_capture.Image, "MAX_IMAGE_PIXELS", 10)
    monkeypatch.setattr(module_capture, "MAX_PIXELS", 10**9)

    with pytest.raises(CaptureInvalide) as e:
        Capture.depuis_octets("P1", png(50, 50))
    assert e.value.code == "IMAGE_TROP_GRANDE"
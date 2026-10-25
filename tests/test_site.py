"""Garde-fous du site neoSlice.

Lancer : python -m pytest tests -q   (depuis C:\\neoslice-site)
"""
from __future__ import annotations

import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
import build  # noqa: E402

SRC = RACINE / "src"
DOCS = RACINE / "docs"
BASE = "/neoslice-site"
ATTRS = ("class", "id", "href", "src", "data-f", "data-cat", "data-panel", "for", "name", "type",
         "target", "download", "data-ns-version", "aria-pressed", "checked")


class Structure(HTMLParser):
    """Suite des balises et de leurs attributs, SANS le texte : deux langues
    d'une même page doivent produire exactement la même suite."""

    VIDES = {"img", "input", "br", "meta", "link", "hr"}

    def __init__(self):
        super().__init__()
        self.suite, self.ignore = [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.ignore or "data-only" in a:
            if tag not in self.VIDES:
                self.ignore += 1
            return
        self.suite.append((tag, tuple((k, a[k]) for k in ATTRS if k in a)))

    def handle_endtag(self, tag):
        if self.ignore and tag not in self.VIDES:
            self.ignore -= 1


def structure(texte: str):
    p = Structure()
    p.feed(texte)
    return p.suite


@pytest.mark.parametrize("cle", list(build.PAGES))
def test_chaque_page_existe_dans_les_deux_langues(cle):
    for langue in ("fr", "en"):
        assert (SRC / langue / f"{cle}.html").is_file(), f"{langue}/{cle}.html manquant"


@pytest.mark.parametrize("cle", list(build.PAGES))
def test_les_deux_langues_ont_la_meme_structure(cle):
    fr = structure((SRC / "fr" / f"{cle}.html").read_text(encoding="utf-8"))
    en = structure((SRC / "en" / f"{cle}.html").read_text(encoding="utf-8"))
    for i, (a, b) in enumerate(zip(fr, en)):
        assert a == b, f"{cle} : différence à la balise n°{i} : FR {a} / EN {b}"
    assert len(fr) == len(en), f"{cle} : {len(fr)} balises en français, {len(en)} en anglais"


@pytest.fixture(scope="module")
def site():
    subprocess.run([sys.executable, str(RACINE / "build.py")], check=True, cwd=RACINE,
                   capture_output=True)
    return sorted(DOCS.rglob("*.html"))


def test_aucun_marqueur_oublie(site):
    for f in site:
        assert "{{" not in f.read_text(encoding="utf-8"), f"marqueur non remplacé dans {f}"


def test_liens_internes_et_images_existent(site):
    manquants = []
    for f in site:
        t = f.read_text(encoding="utf-8")
        for cible in re.findall(r'(?:href|src)="(/neoslice-site[^"#?]*)', t):
            chemin = DOCS / cible[len(BASE):].lstrip("/")
            if cible.endswith("/"):
                chemin = chemin / "index.html"
            if not chemin.exists():
                manquants.append((f.relative_to(DOCS).as_posix(), cible))
    assert not manquants, manquants


def test_chaque_image_a_un_texte_alternatif(site):
    for f in site:
        for img in re.findall(r"<img\b[^>]*>", f.read_text(encoding="utf-8")):
            assert re.search(r'alt="[^"]+"', img), f"image sans alt dans {f}: {img[:80]}"


def test_pas_de_tiret_cadratin_dans_les_textes():
    """Règle d'Emmanuel : jamais de « — » de ponctuation, dans aucune langue."""
    for f in SRC.rglob("*.html"):
        texte = re.sub(r"<[^>]+>", " ", f.read_text(encoding="utf-8"))
        assert "—" not in texte and " – " not in texte, f"tiret de ponctuation dans {f}"


def test_les_telechargements_pointent_vers_les_fichiers_publics():
    for f in SRC.rglob("*.html"):
        t = f.read_text(encoding="utf-8")
        assert "Labstral/neoSlice/releases" not in t, f"lien vers le dépôt privé dans {f}"
        for lien in re.findall(r'href="(https://github\.com/[^"]+)"', t):
            assert "/labstral/neoslice-assets/releases/download/neoslice-latest/" in lien, lien


def test_le_site_provisoire_est_invisible_pour_google(site):
    assert (DOCS / "robots.txt").read_text() == "User-agent: *\nDisallow: /\n"
    for f in site:
        t = f.read_text(encoding="utf-8")
        if "<head>" in t:
            assert 'name="robots" content="noindex' in t, f"page indexable : {f}"

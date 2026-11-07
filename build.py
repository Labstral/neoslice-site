"""Construit le site neoSlice (français et anglais) dans le dossier docs/.

    python build.py              -> site définitif, servi sur neoslice-ai.com
    python build.py --preview    -> version de test (adresse GitHub, invisible pour Google)

Chaque page existe en deux fichiers de contenu, src/fr/<page>.html et
src/en/<page>.html. Ce script les habille de l'en-tête et du pied de page
communs et écrit le résultat dans docs/, que GitHub Pages publie tel quel.
Les tests (tests/test_site.py) vérifient que les deux langues restent
identiques dans leur structure.
"""
from __future__ import annotations

import html
import json

import shutil
import sys
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent
SRC = RACINE / "src"
SORTIE = RACINE / "docs"
DOMAINE = "neoslice-ai.com"
GIST = ("https://gist.githubusercontent.com/Labstral/"
        "73d8c1bc62235780b4822ef2301edd45/raw/latest.json")

# clé de page -> chemin par langue, feuille de style propre, titre, description
PAGES = {
    "index": {
        "fr": ("", "neoSlice | Logiciel d'impression 3D avec IA, gratuit",
               "neoSlice analyse votre pièce, choisit les bons réglages et exporte un fichier prêt à "
               "imprimer pour 9 slicers et 600+ imprimantes. Gratuit, Windows et Mac."),
        "en": ("", "neoSlice | AI 3D printing software, free for Windows & Mac",
               "neoSlice analyzes your part, picks the right settings and exports a print-ready "
               "file for 9 slicers and 600+ printers. Free on Windows and Mac."),
        "css": "index.css",
    },
    "neoslice-pro": {
        "fr": ("neoslice-pro", "neoSlice Pro | Créez plus, ratez moins en impression 3D",
               "neoGen, neoForge, l'assistant IA local Oen, le diagnostic photo, l'export "
               "multicouleur et la gestion d'atelier. 79,99 € HT, paiement unique, à vie."),
        "en": ("neoslice-pro", "neoSlice Pro | Create more, fail less in 3D printing",
               "neoGen, neoForge, Oen the local AI assistant, photo diagnosis, multicolor export "
               "and workshop management. €79.99 excl. VAT, one-time payment, for life."),
        "css": "neoslice-pro.css",
    },
    "about": {
        "fr": ("about", "À propos | neoSlice, logiciel d'impression 3D",
               "Pourquoi et comment neoSlice est né : un logiciel d'impression 3D conçu en Suisse "
               "par Emmanuel Percheron, fondateur du studio Qyntiv."),
        "en": ("about", "About | neoSlice, 3D printing software",
               "Why and how neoSlice was born: 3D printing software made in Switzerland by "
               "Emmanuel Percheron, founder of the Qyntiv studio."),
    },
    "retour": {
        "fr": ("retour", "Retour utilisateur | neoSlice",
               "Un bug, une idée, une question ? Écrivez directement à l'auteur de neoSlice."),
        "en": ("feedback", "Feedback | neoSlice",
               "A bug, an idea, a question? Write directly to the author of neoSlice."),
    },
    "faq": {
        "fr": ("faq", "FAQ | neoSlice, logiciel d'impression 3D", "Les réponses aux questions les plus fréquentes sur neoSlice."),
        "en": ("faq", "FAQ | neoSlice, 3D printing software", "Answers to the most frequent questions about neoSlice."),
    },
    "mentions-legales": {
        "fr": ("mentions-legales", "Mentions légales | neoSlice", "Mentions légales du site neoSlice."),
        "en": ("legal-notice", "Legal notice | neoSlice", "Legal notice of the neoSlice website."),
    },
    "conditions-generales": {
        "fr": ("conditions-generales", "Conditions générales d'utilisation | neoSlice",
               "Conditions générales d'utilisation du site et du logiciel neoSlice."),
        "en": ("terms", "Terms of use | neoSlice", "Terms of use of the neoSlice website and software."),
    },
    "politique-de-confidentialite": {
        "fr": ("politique-de-confidentialite", "Politique de confidentialité | neoSlice",
               "Quelles données sont collectées par le site et le logiciel neoSlice, et comment."),
        "en": ("privacy-policy", "Privacy policy | neoSlice",
               "What data the neoSlice website and software collect, and how."),
    },
    "partenariats": {
        "fr": ("partenariats", "Partenariats | neoSlice",
               "Media kit du groupe Bambu Lab pour les nuls et de neoSlice : audience, engagement et formats de collaboration."),
        "en": ("partners", "Partners | neoSlice",
               "Media kit for the Bambu Lab pour les nuls group and neoSlice: audience, engagement and partnership formats."),
    },
}

TEXTES = {
    "fr": {
        "nav": [("index", "Accueil"), ("neoslice-pro", "neoSlice Pro"), ("about", "À propos"),
                ("retour", "Retour utilisateur"), ("faq", "FAQ")],
        "legal": [("partenariats", "Partenariats"),
                  ("mentions-legales", "Mentions légales"),
                  ("politique-de-confidentialite", "Politique de confidentialité"),
                  ("conditions-generales", "Conditions générales d'utilisation")],
        "skip": "Aller au contenu", "menu": "Menu", "tag": "L'impression 3D, réglée pour vous.",
        "copy": "© 2026 Emmanuel Percheron. Tous droits réservés.",
        "qyntiv": 'Conçu par <a href="https://qyntiv.com/">Qyntiv</a>, studio de logiciels suisse.',
        "langs": "Langue", "groupe": "Groupe Facebook Bambu Lab pour les nuls", "insta": "Instagram",
        "dl": "Télécharger",
    },
    "en": {
        "nav": [("index", "Home"), ("neoslice-pro", "neoSlice Pro"), ("about", "About"),
                ("retour", "Feedback"), ("faq", "FAQ")],
        "legal": [("partenariats", "Partners"),
                  ("mentions-legales", "Legal notice"),
                  ("politique-de-confidentialite", "Privacy policy"),
                  ("conditions-generales", "Terms of use")],
        "skip": "Skip to content", "menu": "Menu", "tag": "3D printing, dialed in for you.",
        "copy": "© 2026 Emmanuel Percheron. All rights reserved.",
        "qyntiv": 'Made by <a href="https://qyntiv.com/en/">Qyntiv</a>, Swiss software studio.',
        "langs": "Language", "groupe": "Bambu Lab pour les nuls Facebook group", "insta": "Instagram",
        "dl": "Download",
    },
}

FACEBOOK = "https://www.facebook.com/groups/bambulabpourlesnuls/"
INSTAGRAM = "https://www.instagram.com/manu_studio_ch/"
TIKTOK = "https://www.tiktok.com/@manu_studio_ch"
LINKEDIN = "https://www.linkedin.com/in/emmanuel-percheron/"
FACEBOOK_PROFIL = "https://www.facebook.com/profile.php?id=100085604569939"
SVG_LI = ('<svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M6.94 8.5H3.56V20h3.38V8.5zM5.25 3.5a1.97 1.97 0 1 0 0 3.94 1.97 1.97 0 0 0 0-3.94zM20.44 13.2c0-3.1-1.65-4.98-4.3-4.98-1.6 0-2.62.86-3.06 1.66V8.5H9.7V20h3.38v-6.08c0-1.6.6-2.7 2.02-2.7 1.38 0 1.96 1.04 1.96 2.7V20h3.38v-6.8z"/></svg>')
# Groupe Facebook (communauté) : icône distincte du profil Facebook
SVG_GROUPE = ('<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="9" cy="8.5" r="3.2"/><path d="M3.5 19c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5"/><circle cx="16.8" cy="9.5" r="2.5"/><path d="M16 14.2c2.3-.2 4 1.3 4.6 4.3"/></svg>')
SVG_TT = ('<svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16.6 5.82A4.28 4.28 0 0 1 15.54 3h-3.09v12.4a2.59 2.59 0 0 1-2.59 2.5c-1.42 0-2.6-1.16-2.6-2.6 0-1.72 1.66-3.01 3.37-2.48V9.66c-3.45-.46-6.47 2.22-6.47 5.64 0 3.33 2.76 5.7 5.69 5.7 3.14 0 5.69-2.55 5.69-5.7V9.01a7.35 7.35 0 0 0 4.3 1.38V7.3s-1.88.09-3.24-1.48z"/></svg>')
SVG_FB = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13.5 21v-7.5h2.5l.4-3h-2.9V8.6c0-.9.3-1.5 1.5-1.5h1.6V4.4c-.3 0-1.2-.1-2.3-.1-2.3 0-3.8 1.4-3.8 3.9v2.3H8v3h2.5V21h3z"/></svg>')
SVG_IG = ('<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r="1" fill="currentColor" stroke="none"/></svg>')


def url(base: str, langue: str, cle: str) -> str:
    """Adresse d'une page, toujours terminée par une barre oblique."""
    chemin = PAGES[cle][langue][0]
    prefixe = "/en" if langue == "en" else ""
    return f"{base}{prefixe}/" + (f"{chemin}/" if chemin else "")


def version_publiee() -> str:
    """« neoSlice 2.5 » d'après le Gist des mises à jour ; le JavaScript la
    relit de toute façon dans le navigateur."""
    try:
        with urllib.request.urlopen(GIST, timeout=10) as r:
            v = json.loads(r.read().decode("utf-8"))["version"]
        return "neoSlice " + ".".join(str(v).split(".")[:2])
    except Exception:
        return "neoSlice 2.5"


def fiche_logiciel(langue: str, cle: str) -> str:
    """Données structurées SoftwareApplication (accueil et neoSlice Pro) : Google comprend que c'est un
    logiciel, gratuit, pour Windows et macOS, avec une version Pro payante."""
    if cle not in ("index", "neoslice-pro"):
        return ""
    fr = langue == "fr"
    donnees = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "neoSlice Pro" if cle == "neoslice-pro" else "neoSlice",
        "url": f"https://{DOMAINE}" + url("", langue, cle),
        "description": PAGES[cle][langue][2],
        "applicationCategory": "DesignApplication",
        "applicationSubCategory": "Impression 3D" if fr else "3D printing",
        "operatingSystem": "Windows, macOS",
        "inLanguage": langue,
        "image": f"https://{DOMAINE}/assets/img/hero-neoslice.jpg",
        "offers": ([{"@type": "Offer", "price": "79.99", "priceCurrency": "EUR",
                     "url": "https://gumroad.com/l/zetye"}] if cle == "neoslice-pro" else
                   [{"@type": "Offer", "price": "0", "priceCurrency": "EUR"}]),
        "author": {"@type": "Person", "name": "Emmanuel Percheron"},
        "publisher": {"@type": "Organization", "name": "Qyntiv", "url": "https://qyntiv.com/"},
    }
    return ('<script type="application/ld+json">'
            + json.dumps(donnees, ensure_ascii=False, separators=(",", ":")) + "</script>\n")


def page(langue: str, cle: str, base: str, prod: bool, version: str) -> str:
    t = TEXTES[langue]
    chemin, titre, description = PAGES[cle][langue]
    contenu = (SRC / langue / f"{cle}.html").read_text(encoding="utf-8")
    contenu = contenu.replace("{{base}}", base).replace("{{version}}", version)
    for c in PAGES:
        contenu = contenu.replace("{{url:" + c + "}}", url(base, langue, c))
    autre = "en" if langue == "fr" else "fr"
    absolu = lambda lg: f"https://{DOMAINE}" + url("", lg, cle)

    def liens(items, courant=True):
        return "".join(
            f'<a href="{url(base, langue, c)}"' + (' aria-current="page"' if courant and c == cle else "")
            + f">{html.escape(nom)}</a>" for c, nom in items)

    bascule = (f'<span class="lang" role="group" aria-label="{t["langs"]}">'
               f'<a href="{url(base, "fr", cle)}" hreflang="fr" lang="fr" data-set-lang="fr"'
               + (' aria-current="true"' if langue == "fr" else "") + '>FR</a>'
               f'<a href="{url(base, "en", cle)}" hreflang="en" lang="en" data-set-lang="en"'
               + (' aria-current="true"' if langue == "en" else "") + '>EN</a></span>')
    css = [f"{base}/assets/css/base.css"] + (
        [f"{base}/assets/css/{PAGES[cle]['css']}"] if "css" in PAGES[cle] else [])
    robots = "" if prod else '<meta name="robots" content="noindex, nofollow">\n'
    return f"""<!doctype html>
<html lang="{langue}" data-base="{base}" data-page="{cle}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titre)}</title>
<meta name="description" content="{html.escape(description)}">
{robots}<link rel="canonical" href="{absolu(langue)}">
<link rel="alternate" hreflang="{langue}" href="{absolu(langue)}">
<link rel="alternate" hreflang="{autre}" href="{absolu(autre)}">
<link rel="alternate" hreflang="x-default" href="{absolu('fr')}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(titre)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:image" content="https://{DOMAINE}/assets/img/hero-neoslice.jpg">
<meta property="og:locale" content="{'fr_FR' if langue == 'fr' else 'en_US'}">
<link rel="icon" href="{base}/assets/img/favicon-light.png" type="image/png">
<link rel="apple-touch-icon" href="{base}/assets/img/apple-touch-icon.png">
{"".join(f'<link rel="stylesheet" href="{h}">' + chr(10) for h in css)}<script src="{base}/assets/js/site.js" defer></script>
{fiche_logiciel(langue, cle)}</head>
<body>
<a class="skip" href="#contenu">{t["skip"]}</a>
<header class="site-header">
  <div class="bar">
    <a class="brand" href="{url(base, langue, 'index')}">neoSlice</a>
    <div class="right">
    <nav class="nav" aria-label="Navigation">{liens(t["nav"])}{bascule}</nav>
    <a class="hdr-dl" href="{url(base, langue, 'index')}#telecharger">{t["dl"]}</a>
    <details class="menu"><summary aria-label="{t["menu"]}"><span></span></summary>
      <div class="sheet">{liens(t["nav"])}{bascule}</div></details>
    </div>
  </div>
</header>
<main id="contenu">
{contenu.strip()}
</main>
<footer class="site-footer">
  <div class="wrap">
    <div><a class="brand" href="{url(base, langue, 'index')}">neoSlice</a><p class="tag">{t["tag"]}</p></div>
    <div class="social">
      <a href="{INSTAGRAM}" target="_blank" rel="noopener" aria-label="{t["insta"]}">{SVG_IG}</a>
      <a href="{LINKEDIN}" target="_blank" rel="noopener" aria-label="LinkedIn">{SVG_LI}</a>
      <a href="{FACEBOOK_PROFIL}" target="_blank" rel="noopener" aria-label="Facebook">{SVG_FB}</a>
      <a href="{TIKTOK}" target="_blank" rel="noopener" aria-label="TikTok">{SVG_TT}</a>
      <a href="{FACEBOOK}" target="_blank" rel="noopener" aria-label="{t["groupe"]}" title="{t["groupe"]}">{SVG_GROUPE}</a>
    </div>
    <nav aria-label="{'Informations légales' if langue == 'fr' else 'Legal information'}">{liens(t["legal"], courant=False)}</nav>
    <p class="copy">{t["copy"]} {t["qyntiv"]}</p>
  </div>
</footer>
</body>
</html>
"""


def construire(prod: bool, sortie: Path = SORTIE) -> None:
    base = "" if prod else "/neoslice-site"
    version = version_publiee()
    if sortie.exists():
        shutil.rmtree(sortie)
    shutil.copytree(RACINE / "assets", sortie / "assets")
    for langue in ("fr", "en"):
        for cle in PAGES:
            dest = sortie / url("", langue, cle).strip("/") / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(page(langue, cle, base, prod, version), encoding="utf-8")
    # L'ancienne adresse Squarespace /home renvoie vers l'accueil.
    redir = f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={base}/"><link rel="canonical" href="https://{DOMAINE}/"><title>neoSlice</title>'
    (sortie / "home").mkdir(exist_ok=True)
    (sortie / "home" / "index.html").write_text(redir, encoding="utf-8")
    (sortie / "404.html").write_text(redir, encoding="utf-8")
    (sortie / ".nojekyll").write_text("", encoding="utf-8")
    if prod:
        (sortie / "CNAME").write_text(DOMAINE + "\n", encoding="utf-8")
        # Preuve de propriété pour Google Search Console (ne jamais retirer).
        (sortie / "googlefb1922dfb134af8c.html").write_text(
            "google-site-verification: googlefb1922dfb134af8c.html", encoding="utf-8")
        locs = "".join(f"<url><loc>https://{DOMAINE}{url('', lg, c)}</loc></url>"
                       for lg in ("fr", "en") for c in PAGES)
        (sortie / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + locs + "</urlset>\n", encoding="utf-8")
        (sortie / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: https://{DOMAINE}/sitemap.xml\n", encoding="utf-8")
    else:
        (sortie / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    print(f"Site construit dans {sortie} ({'définitif' if prod else 'provisoire'}, {version})")


if __name__ == "__main__":
    # Par défaut : le VRAI site (neoslice-ai.com). --preview : version de test
    # sous /neoslice-site, invisible pour Google. --out : autre dossier de sortie
    # (les tests construisent ailleurs que dans docs/, qui est le site publié).
    args = sys.argv[1:]
    dossier = Path(args[args.index("--out") + 1]) if "--out" in args else SORTIE
    construire(prod="--preview" not in args, sortie=dossier)

# -*- coding: utf-8 -*-
"""Aperçu EN DIRECT du site, sur cet ordinateur seulement.

    python serve.py          puis ouvrir http://localhost:8765

Le site est reconstruit dès qu'un fichier de src/, assets/ ou build.py change,
et la page ouverte se recharge toute seule. Rien n'est publié : l'aperçu est
construit dans .apercu/ (ignoré par git), jamais dans docs/.
"""
from __future__ import annotations

import http.server
import os
import socketserver
import threading
import time
from pathlib import Path

RACINE = Path(__file__).resolve().parent
APERCU = RACINE / ".apercu"
PORT = 8765
_generation = {"n": 0}

# Recharge la page quand le site a été reconstruit. Fixe aussi le français
# comme langue choisie : sinon un navigateur réglé en anglais serait renvoyé
# vers /en/ à la première visite (comportement voulu sur le vrai site).
_SCRIPT = (b"<script>try{localStorage.getItem('ns-lang')||localStorage.setItem('ns-lang','fr')}catch(e){}"
           b"(function(){var g=null;setInterval(function(){fetch('/__generation').then(function(r){return r.text()})"
           b".then(function(t){if(g===null)g=t;else if(t!==g)location.reload()}).catch(function(){})},800)})();"
           b"</script></body>")


def _empreinte() -> float:
    total = 0.0
    for dossier in ("src", "assets"):
        for p in (RACINE / dossier).rglob("*"):
            if p.is_file():
                total += p.stat().st_mtime
    return total + (RACINE / "build.py").stat().st_mtime


def _construire() -> None:
    # Relu à chaque fois, par son chemin : un paquet pip nommé « build »
    # pourrait sinon passer devant le build.py du site.
    import importlib.util
    spec = importlib.util.spec_from_file_location("site_build", RACINE / "build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.construire(prod=True, sortie=APERCU)
    _generation["n"] += 1


def _surveiller() -> None:
    derniere = _empreinte()
    while True:
        time.sleep(0.5)
        try:
            e = _empreinte()
            if e != derniere:
                derniere = e
                time.sleep(0.3)
                _construire()
        except Exception as exc:          # une erreur de saisie ne coupe pas l'aperçu
            print("Erreur de construction :", exc)


class _Gestion(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(APERCU), **kw)

    def log_message(self, format, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path.startswith("/__generation"):
            corps = str(_generation["n"]).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(corps)))
            self.end_headers()
            self.wfile.write(corps)
            return
        chemin = Path(self.translate_path(self.path))
        if chemin.is_dir():
            chemin = chemin / "index.html"
        if chemin.suffix == ".html" and chemin.is_file():
            corps = chemin.read_bytes().replace(b"</body>", _SCRIPT, 1)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corps)))
            self.end_headers()
            self.wfile.write(corps)
            return
        super().do_GET()


if __name__ == "__main__":
    os.chdir(RACINE)
    _construire()
    threading.Thread(target=_surveiller, daemon=True).start()
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), _Gestion) as serveur:
        print(f"Aperçu en direct : http://localhost:{PORT}")
        serveur.serve_forever()

# Site neoSlice

Source du site [neoslice-ai.com](https://neoslice-ai.com), en français et en anglais.

- `src/fr/` et `src/en/` : le contenu de chaque page, une page par fichier, même structure dans les deux langues.
- `assets/` : styles, images, petit script (version affichée, langue, filtres des avis).
- `build.py` : assemble les pages dans `docs/`, que GitHub Pages publie.
- `tests/` : vérifie que les deux langues restent identiques, que tous les liens et images existent, et qu'aucun lien ne pointe vers le dépôt privé.

```
python build.py          # site provisoire, invisible pour les moteurs de recherche
python build.py --prod   # site définitif sur neoslice-ai.com
python -m pytest tests -q
```

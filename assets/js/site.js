/* Petits comportements du site. Rien d'indispensable : sans JavaScript,
   toutes les pages restent lisibles et tous les liens fonctionnent. */
(function () {
  var root = document.documentElement;
  var base = root.getAttribute("data-base") || "";

  // 1. Langue : à la toute première visite de l'accueil français, un
  //    navigateur qui n'est pas en français est envoyé vers l'anglais.
  //    Dès que le visiteur choisit une langue, on respecte son choix.
  try {
    var choix = localStorage.getItem("ns-lang");
    document.querySelectorAll("[data-set-lang]").forEach(function (a) {
      a.addEventListener("click", function () {
        try { localStorage.setItem("ns-lang", a.getAttribute("data-set-lang")); } catch (e) {}
      });
    });
    if (!choix && root.getAttribute("data-page") === "index" && root.lang === "fr") {
      var langues = navigator.languages || [navigator.language || ""];
      var francophone = langues.some(function (l) { return /^fr\b/i.test(l || ""); });
      if (!francophone && !/bot|crawl|spider/i.test(navigator.userAgent)) {
        location.replace(base + "/en/");
        return;
      }
    }
  } catch (e) {}

  // 2. Numéro de version : lu dans le même fichier que les mises à jour
  //    de neoSlice, donc toujours celui de la dernière version publiée.
  var cibles = document.querySelectorAll("[data-ns-version]");
  if (cibles.length && window.fetch) {
    fetch("https://gist.githubusercontent.com/Labstral/73d8c1bc62235780b4822ef2301edd45/raw/latest.json?t=" + Date.now())
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !d.version) return;
        var court = String(d.version).split(".").slice(0, 2).join(".");
        cibles.forEach(function (el) { el.textContent = "neoSlice " + court; });
      })
      .catch(function () {});
  }

  // 3. Système du visiteur : sur Windows ou sur Mac, le bon bouton de
  //    téléchargement passe en premier et l'autre devient un simple lien.
  //    Téléphone, tablette ou système inconnu : les deux boutons restent.
  try {
    var ua = navigator.userAgent || "";
    var plat = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "";
    var mobile = /Android|iPhone|iPad|iPod|Mobile/i.test(ua) || (/Mac/i.test(plat) && navigator.maxTouchPoints > 1);
    var os = mobile ? "" : /Win/i.test(plat) ? "win" : /Mac/i.test(plat) ? "mac" : "";
    if (os) {
      root.classList.add("dl-" + os);
      // L'aide à l'installation s'ouvre directement sur le bon système.
      var onglet = document.getElementById("nsxaide-os-" + os);
      if (onglet) onglet.checked = true;
    }
  } catch (e) {}

  // 4. Avis clients : filtres, et seulement six avis tant qu'on ne demande
  //    pas la suite (sans JavaScript, tous restent visibles).
  var avis = document.querySelector(".nsxavis-reviews");
  if (avis) {
    var puces = avis.querySelectorAll(".nsxavis-chip");
    var cartes = avis.querySelectorAll(".nsxavis-card");
    var grille = avis.querySelector(".nsxavis-grid");
    var suite = avis.querySelector(".nsxavis-more");
    var deplier = function () {
      if (grille) grille.classList.remove("court");
      if (suite) suite.hidden = true;
    };
    if (grille && suite && avis.querySelector(".nsxavis-card.plus")) {
      grille.classList.add("court");
      suite.hidden = false;
      suite.querySelector("button").addEventListener("click", deplier);
    }
    puces.forEach(function (c) {
      c.addEventListener("click", function () {
        puces.forEach(function (x) { x.setAttribute("aria-pressed", "false"); });
        c.setAttribute("aria-pressed", "true");
        var f = c.getAttribute("data-f");
        if (f !== "all") deplier();
        cartes.forEach(function (carte) {
          carte.classList.toggle("hide", !(f === "all" || carte.getAttribute("data-cat") === f));
        });
      });
    });
  }

  // 5. Formulaire Tally : son script ajuste la hauteur du cadre au contenu
  //    (questions qui apparaissent selon les réponses).
  if (document.querySelector('iframe[src*="tally.so/embed"]')) {
    var s = document.createElement("script");
    s.src = "https://tally.so/widgets/embed.js";
    s.async = true;
    document.body.appendChild(s);
  }

  // 6. Menu mobile : se referme après un choix.
  var menu = document.querySelector(".menu");
  if (menu) menu.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", function () { menu.removeAttribute("open"); });
  });
})();

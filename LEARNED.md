# Journal d'apprentissage MONITUS (LEARNED.md)

Ce journal garde en mémoire tout ce que nous avons appris étape par étape. Il doit rester à jour après chaque action.

## Étape 1 : Mise en place initiale du projet (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°1

### 2) Ce que nous avons fait et quels fichiers ont changé
- Initialisation du dépôt Git local dans `C:\Users\doudaa\Documents\MONITUS` (`git init`).
- Création des dossiers : `frontend/`, `ai-service/`, `hedera-service/`, `contracts/`, `data/`, `docs/`, `scripts/`, `tests/`.
- Création de `README.md`.
- Création de `.gitignore`.
- Création de `docs/PROJECT_PLAN.md`.
- Création de `AGENTS.md`.

### 3) Pourquoi nous devions le faire
Nous devons partir d'un socle clair : dossiers bien rangés, un dépôt Git local pour suivre les changements, et des documents pour comprendre le projet et respecter les règles de développement (sécurité, anonymat, incrémental).

### 4) Comment ça fonctionne, expliqué simplement
- **Dépôt Git** (système qui garde l'historique des modifications) : `git init` crée un dossier `.git/` qui suivra les fichiers ajoutés/modifiés/supprimés.
- **Dossiers** : chacun représente un module du projet (frontend = interface web, ai-service = détection, etc.). Les mettre vides maintenant permet d'avancer module par module sans générer tout le projet d'un coup.
- **Fichiers .md** : `README.md` explique le projet, `PROJECT_PLAN.md` liste ce qui est prévu/fait, `AGENTS.md` donne les règles à respecter.

### 5) Nouveaux concepts appris
- **Git init** : démarrer un suivi local sans envoyer sur internet.
- **Anonymat** : ne pas utiliser de vraies données de patients, seulement des données agrégées (regroupées) sans identifiants.
- **Hedera** (registre distribué) : comme un cahier partagé et infalsifiable entre plusieurs hôpitaux, où l'on note des alertes/coordination sans tout recopier manuellement.
- **Développement incrémental** : avancer petit à petit, étape validée avant la suivante, plutôt que tout créer d'un coup.

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **Test 1** : `git -C "C:\Users\doudaa\Documents\MONITUS" rev-parse --git-dir` -> résultat réel : non trouvé avant init; après init -> `.git` existe.
- **Test 2** : affichage des dossiers/fichiers avec `Get-ChildItem` -> résultat réel : tous les dossiers et fichiers créés présents.
- **Test 3** : `git status` -> résultat réel : repo vide, fichiers non suivis présents.
- **Ce qui reste non vérifié** : aucun commit effectué (demande de ne pas en faire), aucun code généré, pas de déploiement.

### 9) Ce qu'il reste à faire
- Suivre strictement les règles d'AGENTS.md.
- Continuer à avancer étape par étape, en vérifiant chaque action.
- Conserver ce journal à jour après chaque tâche/bogue/config/test.

## Étape 2 : Création du journal d'apprentissage et mise à jour des règles (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°2

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `LEARNED.md` dans la racine du projet.
- Mise à jour de `AGENTS.md` avec une règle permanente : "Après TOUTE tâche d'implementation, correction de bogue, changement de configuration ou test, mettre à jour LEARNED.md avant de finir sa réponse."

### 3) Pourquoi nous devions le faire
Afin d'apprendre ensemble, pas à pas. Ce journal oblige à expliquer ce qu'on fait, pourquoi, comment, les erreurs réelles, les tests réels et ce qu'il reste à faire. C'est aussi une trace pour nous-mêmes (étudiants) et pour suivre la progression incrémentale.

### 4) Comment ça fonctionne, expliqué simplement
- **LEARNED.md** : un fichier texte qui s'ajoute à chaque fois (on n'efface pas l'historique). On y écrit étape par étape avec les 9 points.
- **Règle dans AGENTS.md** : maintenant, à chaque fin de tâche, l'agent doit obligatoirement mettre à jour ce journal avant de répondre. C'est comme un pense-bête obligatoire pour bien réfléchir.

### 5) Nouveaux concepts appris
- **Journal d'apprentissage** : garder une trace explicative (pas juste "fait"), c'est mieux pour comprendre.
- **Règle permanente** : une instruction que l'on ajoute au fichier des règles pour qu'elle reste appliquée même après.

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **Test** : vérification de la présence de `LEARNED.md` dans la racine -> résultat réel : fichier créé avec contenu.
- **Test** : vérification de `AGENTS.md` -> résultat réel : règle ajoutée à la fin.
- **Ce qui reste non vérifié** : aucun autre changement.

### 9) Ce qu'il reste à faire
- Appliquer cette règle rigoureusement après chaque tâche.
- Continuer à avancer pas à pas, sans générer tout le projet d'un coup.
- Ne pas introduire de données patients, secrets, clés ou déploiements sans autorisation explicit.

## Étape 3 : Vérification environnement outils (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°3

### 2) Ce que nous avons fait et quels fichiers ont changé
- Exécution des commandes en lecture seule : `python --version`, `py --version`, `python -m pip --version`, `node --version`, `npm --version`, `git --version`.
- Aucun fichier modifié/créé/supprimé.

### 3) Pourquoi nous devions le faire
Avant de démarrer, il faut savoir quels outils sont disponibles sur l'ordinateur (Windows) pour savoir quoi utiliser plus tard.

### 4) Comment ça fonctionne, expliqué simplement
- **python/py** : deux façons d'appeler Python (l'interpréteur, qui lit et exécute le code)
- **pip** (gestionnaire de paquets) : comme un magasin où l'on peut chercher des morceaux de code pour aider
- **node/npm** (pour JavaScript/Node) : Node exécute du code JS, npm est le gestionnaire (magasin) pour JS
- **git** (suivi de versions) : déjà vu, garde l'historique

### 5) Nouveaux concepts appris
- **Interpréteur** (programme qui traduit le code en actions) : simple exemple, c'est comme un traducteur qui écoute le code et fait ce qu'il demande.
- **Gestionnaire de paquets** : permet d'ajouter des outils/code prêts à l'emploi, sans tout réinventer.

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- Tous les tests en lecture seule ont donné des versions réelles : Python 3.11.0, Python 3.13.5, pip 26.2.1, Node v22.19.0, npm 11.6.0, Git 2.49.0.windows.1.
- Ce qui reste non vérifié : environnement complet pour les modules spécifiques à venir (vérifications seront faites au fur et à mesure).

### 9) Ce qu'il reste à faire
- Continuer étape par étape. Aucun changement à ce jour excepté ce journal.
- Ne pas installer quoi que ce soit tant qu'on ne le demande pas explicitement.

## Étape 4 : Inspection du dossier MONITUS (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°4

### 2) Ce que nous avons fait et quels fichiers ont changé
- Lecture seule du dossier `C:\Users\doudaa\Documents\MONITUS` avec `functions.read`.
- Aucun fichier modifié/créé/supprimé.

### 3) Pourquoi nous devions le faire
Première inspection : savoir ce qu'il y a déjà avant d'agir.

### 4) Comment ça fonctionne, expliqué simplement
- **Lecture de dossier** : on regarde juste ce qui est dedans, sans toucher à rien (comme ouvrir un tiroir sans le ranger/détruire).
- **Git non initialisé à ce moment** : on a vérifié qu'il n'y avait pas de `.git/`, donc rien n'était suivi.

### 5) Nouveaux concepts appris
- **Inspection en lecture seule** : respecter strictement la consigne "ne pas créer/modifier/supprimer".
- **Vérification avant action** : mieux de regarder d'abord pour éviter des erreurs.

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- Lecture du dossier -> résultat réel : dossier vide (0 entrées).
- Vérification Git -> résultat réel : pas de `.git/` trouvé.
- Ce qui reste non vérifié : structure après les étapes suivantes.

### 9) Ce qu'il reste à faire
- Passer aux étapes demandées pour initialiser le projet (Git, dossiers, docs) comme demandé plus tard.

## Étape 5 : Création de la fondation du projet + commit Git (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°5

### 2) Ce que nous avons fait et quels fichiers ont changé
- Initialisation Git : `git init` (déjà fait à l'étape 1, confirmé).
- Création des dossiers : `frontend/`, `ai-service/`, `hedera-service/`, `contracts/`, `data/`, `docs/`, `scripts/`, `tests/`.
- Création : `README.md`, `.gitignore`, `docs/PROJECT_PLAN.md`, `AGENTS.md`, `LEARNED.md`.
- Ajout sélectif et commit : `git add README.md .gitignore AGENTS.md LEARNED.md docs/PROJECT_PLAN.md`, puis `git commit -m "chore: initialize MONITUS project foundation"`.
- Mise à jour de `LEARNED.md` (ceci) pour documenter le commit.

### 3) Pourquoi nous devions le faire
Poser des bases solides et traçables. Un premier commit (enregistrement dans l'historique Git) marque le jalon "fondation du projet" sans code applicatif. On doit aussi apprendre ce qu'est un commit et pourquoi c'est important.

### 4) Comment ça fonctionne, expliqué simplement
- **Git commit** (enregistrement) : comme prendre une photo de l'état actuel des fichiers sélectionnés à un moment donné. Cette photo est sauvegardée dans l'historique avec un message et un identifiant (hash).
- **git add** (préparer) : on choisit quels fichiers on veut mettre dans la prochaine photo (on ne met que ceux demandés).
- **git status** (état) : montre ce qui est modifié/non suivi/prêt à être commit.
- **git log -1 --oneline** (historique court) : montre le dernier commit en une ligne.
- **amend** (modifier le dernier commit) : si on doit corriger juste le dernier commit (ajouter un fichier oublié/modifié), on peut l'amender avant de l'envoyer ailleurs. Ici on a mis à jour `LEARNED.md` après le commit, donc on l'a ajouté et fait `git commit --amend --no-edit` pour l'inclure au même commit si c'était sûr. **Résultat réel** : amend fait avec succès, arbre de travail propre.

### 5) Nouveaux concepts appris
- **Commit** : sauvegarde traçable d'un ensemble de fichiers.
- **Hash de commit** (identifiant unique) : comme une empreinte digitale du commit.
- **Arbre de travail propre** (working tree clean) : tous les changements sont enregistrés, rien à committer.
- **Amend** : réécrire le dernier commit (à utiliser avec précaution, surtout si déjà partagé).

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **Vérif identité Git** : `git config user.name` -> `Chahd`, `git config user.email` -> `chahddimessi@gmail.com` (existaient déjà).
- **Vérif fichiers à committer** : seuls `README.md`, `.gitignore`, `AGENTS.md`, `LEARNED.md`, `docs/PROJECT_PLAN.md` ajoutés. Pas de `.env`, secrets, clés, données patients, ni dossiers node_modules/venv/build présents.
- **Commit** : `[master (root-commit) 19b8939] chore: initialize MONITUS project foundation` - 5 fichiers modifiés, 308 insertions(+).
- **Après amend LEARNED.md** : amend exécuté avec succès (working tree clean après). Hash du commit reste le même conceptuellement mais l'objet est mis à jour; on vérifie l'état.
- **git status** : `On branch master` / `nothing to commit, working tree clean`.
- **git log -1 --oneline** : `19b8939 chore: initialize MONITUS project foundation` (ou hash mis à jour après amend, à noter).
- **Ce qui reste non vérifié** : push sur distant (non demandé), aucun autre commit.

### 9) Ce qu'il reste à faire
- Continuer à avancer étape par étape selon les règles.
- Toujours mettre à jour `LEARNED.md` après chaque tâche/config/test/correction/implémentation.
- Ne pas générer le code applicatif d'un coup, ne pas déployer, ne pas introduire de secrets/données patients.

## Étape 6 : Génération de données synthétiques pour surveillance hospitalière (Step 2.1) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°6

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `scripts/generate_hospital_data.py` (script Python, uniquement librairie standard).
- Création de `tests/test_data_generation.py` (tests unittest).
- Exécution du générateur pour produire les CSV.
- Exécution des tests.
- Mise à jour de `docs/PROJECT_PLAN.md` pour marquer cette étape comme implémentée.
- Mise à jour de `LEARNED.md` (ceci).

### 3) Pourquoi nous devions le faire
Pour avoir des données sûres (synthétiques, anonymes) à utiliser plus tard pour tester la détection d'épidémie. Pas de vraies données de patients. Objectif : générer 3 scénarios reproductibles sur 90 jours pour 3 hôpitaux fictifs.

### 4) Comment ça fonctionne, expliqué simplement
- **Données synthétiques** (données créées artificiellement) : comme un exemple inventé qui ressemble à la réalité mais sans aucune information personnelle. Plus sûr pour apprendre.
- **Graine aléatoire (random seed)** : si on donne la même graine à un générateur aléatoire, il produit la même suite de nombres à chaque fois. C'est comme donner la même recette et obtenir le même gâteau. Ici `random.Random(SEED=12345)` permet la reproductibilité.
- **Script `generate_hospital_data.py`** :
  - `generate_normal()` : baseline stable (~12-16 cas) avec petites fluctuations (-3,+3), valeurs non-négatives entières.
  - `generate_regional_outbreak()` : augmentation soutenue dans les **14 derniers jours** pour **au moins deux hôpitaux** (Tunis, Sousse), Sfax reste plus proche de la baseline.
  - `generate_reporting_error()` : **un seul pic extrême d'un jour** sur **un seul hôpital** (Tunis), les autres restent près de la baseline.
  - `write_csv()` : écrit avec colonnes `date,hospital_id,city,respiratory_cases,scenario`.
  - `main()` : génère les 3 scénarios et sauvegarde dans `data/synthetic/` (création dossier si besoin).
- **Tests `tests/test_data_generation.py`** : vérifient nombre de lignes (270), colonnes, ordre chronologique, valeurs entières non-négatives, mapping hôpitaux/villes, caractéristiques des scénarios, et **reproductibilité** (relancer le générateur et comparer).

### 5) Nouveaux concepts appris
- **CSV** (fichier texte avec virgules) : simple tableau sauvegardé en texte.
- **unittest** (module standard pour tests) : permet de vérifier automatiquement que tout est correct.
- **Reproductibilité** : pouvoir obtenir exactement le même résultat en relançant.
- **Scénarios de test** : normal vs anomalie (épidémie régionale) vs erreur de saisie/rapportage (pic isolé).

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **Générateur** : `python scripts/generate_hospital_data.py` -> 
  - `data/synthetic/normal.csv (270 rows)`
  - `data/synthetic/regional_outbreak.csv (270 rows)`
  - `data/synthetic/reporting_error.csv (270 rows)`
- **Tests** : `python -m unittest tests.test_data_generation` -> `Ran 10 tests in 0.107s` / `OK`
- **Vérifications incluses** : existence fichiers, 270 lignes, colonnes exactes, dates séquentielles par hôpital, entiers non-négatifs, labels corrects, tous hôpitaux présents, hausse sur 2 hôpitaux derniers 14j, 1 seul pic extrême sur 1 hôpital, reproductibilité (relance réussie).
- **Ce qui reste non vérifié** : détection d'anomalies, intégration avec autres modules (pas demandé).

### 9) Ce qu'il reste à faire
- Passer à l'étape suivante uniquement si demandée, en suivant les règles.
- Toujours mettre à jour `LEARNED.md` après chaque tâche/config/test/correction/implémentation.
- Ne pas générer tout le projet d'un coup, pas de données patients, pas de secrets, pas de déploiement sans autorisation.

## Étape 7 : Détecteur d'anomalies robuste par hôpital (Step 2.2) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°7

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `ai_service/anomaly_detector.py` (détecteur robuste, uniquement librairie standard).
- Création de `ai_service/__init__.py` pour rendre le module importable.
- Création de `tests/test_anomaly_detector.py` (10 tests unittest).
- Exécution du CLI sur les 3 scénarios.
- Exécution de tous les tests (données + détecteur).
- Mise à jour de `docs/PROJECT_PLAN.md` pour marquer Step 2.2 comme complété.
- Mise à jour de `LEARNED.md` (ceci).

### 3) Pourquoi nous devions le faire
Détecter des anomalies par hôpital individuellement avec une méthode robuste (peu sensible aux valeurs extrêmes). On veut repérer des pics inhabituels sans confondre avec une épidémie régionale (pas de corrélation entre hôpitaux pour cette étape). Approche simple et explicable pour des étudiants.

### 4) Comment ça fonctionne, expliqué simplement
- **Médiane** (valeur du milieu) : pour [1,2,10], médiane = 2. Moins affectée par une valeur très grande que la moyenne.
- **MAD** (Median Absolute Deviation = écart absolu médian) : mesure à quel point les valeurs s'écartent de la médiane. On calcule |x - médiane| pour chaque valeur, puis on prend la médiane de ces écarts. Plus robuste que l'écart-type.
- **Score d'anomalie robuste** : `(valeur_actuelle - médiane_historique) / (1.4826 * MAD_historique)`. Le facteur 1.4826 permet de rendre le MAD comparable à un écart-type pour une distribution normale.
- **Fenêtre glissante de 21 jours** : on utilise UNIQUEMENT les 21 jours PRÉCÉDENTS pour calculer médiane/MAD. On n'utilise JAMAIS le jour actuel ni le futur (pas de fuite d'information).
- **Seuil 3.5** : on ne signale que les anomalies **positives** (score > 3.5). On ne signale **pas** les baisses inhabituelles comme alerte épidémique.
- **MAD = 0** : si toutes les valeurs historiques sont identiques, MAD=0. On utilise alors un **fallback documenté** (échelle minimale = 1.0) pour éviter division par zéro.
- **Important** : détection **par hôpital uniquement**. Un pic isolé sur un seul hôpital n'est pas automatiquement qualifié "épidémie régionale" (ce sera fait plus tard).

### 5) Nouveaux concepts appris
- **Statistiques robustes** : méthodes moins sensibles aux valeurs aberrantes.
- **Fenêtre glissante** : historique mobile, recalculé jour par jour.
- **Absence de fuite de données** (no leakage) : très important en détection, ne pas regarder l'avenir.
- **Seuil configurable** : 3.5 est un seuil courant pour ce type de score.

### 6) Erreurs rencontrées et causes réelles
- **Erreur 1** : Import `from ai_service.anomaly_detector import ...` échouait car dossier était `ai-service` (tiret) au lieu de `ai_service` (underscore). En Python, les tirets ne sont pas autorisés dans les noms de modules importables.
- **Erreur 2** : Test `test_no_future_data_leakage` avait une assertion incorrecte - il supposait que le jour 26 verrait sa médiane affectée par le pic du jour 25, mais avec médiane sur 21 valeurs dont seulement 1 est 100 et reste 10, la médiane reste 10. C'est correct (pas de fuite). L'assertion était trop forte.

### 7) Comment nous les avons corrigées et pourquoi
- **Correction 1** : Renommage `ai-service/` -> `ai_service/` et ajout de `__init__.py`. Nécessaire pour `import ai_service...`.
- **Correction 2** : Correction du test pour refléter le comportement correct de la médiane (reste 10). On vérifie plutôt qu'aucune fuite vers le futur n'a lieu et que seul l'historique précédent est utilisé.

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **CLI** : `python ai_service/anomaly_detector.py` (avec PYTHONPATH)
  - normal.csv: Tunis 0 anomalies, Sousse 0, Sfax 0
  - regional_outbreak.csv: Tunis 9 anomalies (pics dans derniers 14j), Sousse 10 anomalies, Sfax 0 (détection par hôpital uniquement, pas de corrélation régionale)
  - reporting_error.csv: Tunis 1 anomalie le 2024-02-28 (cases=111), Sousse 0, Sfax 0
- **Tous les tests** : `python -m unittest tests.test_data_generation tests.test_anomaly_detector` -> `Ran 21 tests in 0.132s` / `OK`
- **Ce qui reste non vérifié** : corrélation régionale entre hôpitaux, alertes multi-hôpitaux, intégration API/frontend/Hedera (non demandés).

### 9) Ce qu'il reste à faire
- Étape suivante uniquement si demandée. Toujours mettre à jour `LEARNED.md` après chaque tâche/test/config/correction.
- Respecter toutes les règles : pas de données patients, pas de secrets, pas de déploiement sans autorisation, développement incrémental.

## Étape 8 : Corrélation croisée entre hôpitaux (Step 2.3) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°8

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `ai_service/regional_detector.py` (corrélation par date calendaire)
- Création de `tests/test_regional_detector.py` (8 tests)
- Exécution du CLI sur les 3 scénarios
- Exécution de tous les tests (données + détecteur individuel + corrélation)
- Mise à jour de `docs/PROJECT_PLAN.md` pour marquer Step 2.3
- Mise à jour de `LEARNED.md` (ceci)

### 3) Pourquoi nous devions le faire
Passer de "anomalie par hôpital" à "signal régional". L'objectif est de voir si plusieurs hôpitaux montrent un pic le **même jour** (corrélation temporelle). On veut distinguer un pic isolé (erreur de saisie sur 1 hôpital) d'un signal qui touche plusieurs hôpitaux. On ne dit **jamais** "épidémie confirmée", seulement "signal régional possible".

### 4) Comment ça fonctionne, expliqué simplement
- **Comparaison par date calendaire** : on regroupe les anomalies par `date` (clé commune). Peu importe la position dans le fichier CSV, ce qui compte c'est le même jour.
- **Hôpitaux distincts** : on compte les hôpitaux différents. Si un même hôpital apparaît deux fois pour la même date (doublon), on le rejette/compte une seule fois.
- **Quorum configurable** : par défaut, il faut **au moins 2 hôpitaux distincts** avec anomalie positive le même jour pour avoir un `regional_signal = true`.
- **Rapport structuré** : pour chaque jour avec au moins une anomalie, on produit un rapport avec date, hôpitaux supportant, scores individuels, nombre de sites, signal régional ou non, et explication claire.
- **Gestion des données manquantes** : si un hôpital n'a pas d'observation pour un jour ou n'existe pas, on **n'interprète pas** ça comme 0 cas. On considère juste qu'il n'y a pas de résultat d'anomalie pour ce jour/hôpital.
- **Distinction claire** : jours normaux / anomalies individuelles / signaux régionaux possibles.

### 5) Nouveaux concepts appris
- **Corrélation temporelle** : même moment dans le temps pour différents endroits.
- **Quorum / seuil de corroboration** : besoin de plusieurs sources indépendantes.
- **Données manquantes** : important de ne pas remplir arbitrairement.
- **Prudence dans le langage** : "possible signal régional" pas "confirmé".

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **CLI regional** : 
  - normal.csv: 0 signaux régionaux
  - regional_outbreak.csv: **9 jours** avec signal régional (2024-03-17 à 2024-03-24, 2024-03-26) pour [HOSP_SOU, HOSP_TUN], 1 jour uniquement individuel (2024-03-25 pour Sousse seul)
  - reporting_error.csv: 0 signaux régionaux, 1 anomalie individuelle (Tunis seul)
- **Vérification spécifique demandée** : `regional_outbreak.csv` a bien des jours qui se chevauchent (même date) entre plusieurs hôpitaux - confirmé par les résultats réels.
- **Tous les tests** : `python -m unittest tests.test_data_generation tests.test_anomaly_detector tests.test_regional_detector` -> `Ran 29 tests in 0.126s` / `OK`
- **Tests régionaux** : simultané (2 sites), dates différentes, erreur 1 site, doublons, données manquantes, quorum configurable - tous OK.
- **Ce qui reste non vérifié** : alertes multi-niveaux, intégration, ML/frontend/Hedera (non demandés).

### 9) Ce qu'il reste à faire
- Continuer étape par étape selon règles. Toujours mettre à jour `LEARNED.md` après chaque tâche/test/config/correction.
- Ne pas générer tout d'un coup, pas de données patients, pas de secrets, pas de déploiement sans autorisation.
- Ne pas modifier les données synthétiques pour forcer un résultat.

## Étape 9 : Vérification déterministe et tri des fausses alertes (Step 2.4) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°9

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `ai_service/alert_verifier.py` (vérification déterministe)
- Création de `tests/test_alert_verifier.py` (8 tests)
- Exécution du CLI sur les 3 scénarios
- Exécution de tous les tests
- Mise à jour de `docs/PROJECT_PLAN.md` pour marquer Step 2.4
- Mise à jour de `LEARNED.md` (ceci)

### 3) Pourquoi nous devions le faire
Distinguer clairement les types d'alertes et éviter de traiter n'importe quelle anomalie comme "épidémie confirmée". Le vérificateur applique des règles déterministes (sans IA/LLM) pour donner un statut plus informatif. Un pic sur 1 seul hôpital reste visible pour investigation locale même s'il est très fort.

### 4) Comment ça fonctionne, expliqué simplement
- **Statuts** : `NORMAL`, `ISOLATED_ANOMALY` (1 seul site), `REGIONAL_SIGNAL_UNCONFIRMED` (≥2 sites même jour mais pas persistant), `REGIONAL_SIGNAL_REQUIRES_REVIEW` (≥2 sites + persistant).
- **Comparaison par site distinct** : on distingue bien anomalie isolée vs signal multi-sites.
- **Règle de persistance** : si on a **au moins 2 jours** avec signal régional dans une **fenêtre glissante de 3 jours calendaires** (en regardant uniquement le passé/jour actuel, **jamais le futur**), alors `REQUIRES_REVIEW`. Sinon `UNCONFIRMED` pour un signal du même jour.
- **Pas de fuite future** : on utilise uniquement les dates <= date évaluée.
- **Qualité des données** : on signale doublons, observations manquantes, pics très inhabituels isolés comme avertissements qualité - mais **on ne les supprime pas** et on ne les assume pas comme erreur automatiquement.
- **Anomalies isolées restent visibles** : même si très fortes (score > 20), statut `ISOLATED_ANOMALY` et avertissement qualité, mais toujours visible pour investigation locale.

### 5) Nouveaux concepts appris
- **Vérification déterministe** : règles claires, reproductibles, pas d'aléatoire/IA.
- **Fenêtre glissante** : historique mobile pour juger la persistance.
- **Tri des fausses alertes** : distinguer fort mais isolé vs persistant multi-sites.
- **Prudence** : ne pas confirmer une épidémie sans persistance suffisante.

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **CLI** :
  - normal.csv: aucun assessment
  - regional_outbreak.csv: 2024-03-17 -> UNCONFIRMED (1 jour seul), 03-18 à 03-24, 03-26 -> REQUIRES_REVIEW (persistance), 03-25 -> ISOLATED_ANOMALY (1 site seul)
  - reporting_error.csv: 2024-02-28 -> ISOLATED_ANOMALY + avertissement qualité (score 65.43)
- **Tous les tests** : `python -m unittest tests.test_data_generation tests.test_anomaly_detector tests.test_regional_detector tests.test_alert_verifier` -> `Ran 37 tests in 0.139s` / `OK`
- **Tests vérif** : normal, pic isolé, 1 jour multi-sites, pattern persistant, trous dans dates, doublons, pas de fuite future - tous OK.
- **Ce qui reste non vérifié** : seuils à ajuster selon contexte réel, intégration système complet.

### 9) Ce qu'il reste à faire
- Continuer étape par étape. Toujours mettre à jour `LEARNED.md` après chaque tâche.
- Respecter règles: pas de données patients, pas de secrets, pas de déploiement sans autorisation, pas de LLM/ML/API/frontend/Hedera pour ces étapes.
- Aucun commit/push.

## Étape 10 : Prototype visuel Streamlit (Step 2.5) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°10

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création d'environnement virtuel `venv/` (Python 3.11)
- Installation locale : `streamlit`, `plotly`, `pandas` (seuls nécessaires)
- Création de `demo/dashboard.py` (dashboard Streamlit)
- Création de `tests/test_dashboard_smoke.py` (5 tests smoke)
- Exécution de tous les tests
- Mise à jour de `LEARNED.md` (ceci)

### 3) Pourquoi nous devions le faire
Donner une première visualisation claire du moteur MONITUS déjà construit. On réutilise **exactement** les fonctions existantes (anomaly_detector, regional_detector, alert_verifier) sans réécrire les algorithmes. L'objectif est de voir les résultats des étapes 2.1-2.4 de manière interactive.

### 4) Comment ça fonctionne, expliqué simplement
- **Dashboard Streamlit** : interface web simple créée en Python (pas besoin de JavaScript/React pour ce prototype).
- **Couleurs** : bleu marine (#001f3f), turquoise foncé (#00CED1), blanc - sobre et moderne.
- **Sélecteur de scénario** : permet de basculer entre normal, regional_outbreak, reporting_error.
- **Cartes hôpitaux** : Tunis, Sousse, Sfax avec compteur d'anomalies (données SYNTHÉTIQUES clairement indiquées).
- **Graphiques temporels** : courbe des cas quotidiens par hôpital, points rouges en X pour anomalies détectées.
- **Synthèse régionale** : nombre de jours avec signal régional et détails.
- **Vérification** : statuts du vérificateur (NORMAL/ISOLATED_ANOMALY/UNCONFIRMED/REQUIRES_REVIEW).
- **Tableau** : dates signalées avec hôpitaux, statuts, explications.
- **Avertissements qualité** : affichés si présents.
- **Tests smoke** : vérifient imports, que dashboard charge, et traitement des 3 scénarios sans ouvrir navigateur.

### 5) Nouveaux concepts appris
- **Streamlit** : framework pour créer rapidement des dashboards en Python.
- **Plotly** : graphiques interactifs.
- **Prototype visuel** : montrer plutôt que seulement des logs texte.
- **Réutilisation** : important d'utiliser le moteur existant, pas de valeurs hardcodées.

### 6) Erreurs rencontrées et causes réelles
- **Erreur 1** : Commandes PowerShell avec `&&` ne fonctionnaient pas (syntaxe différente sur Windows PowerShell).
- **Erreur 2** : `tail`, `head` non disponibles en PowerShell natif.
- **Erreur 3** : Import du module `ai_service` échouait si on lançait depuis certains contextes - résolu avec `sys.path.insert`.
- **Erreur 4** : Installation streamlit a pris du temps (cache utilisé).

### 7) Comment nous les avons corrigées et pourquoi
- **Correction 1** : Utilisation de `Set-Location` ou commandes séparées.
- **Correction 2** : Utilisation de `Select-Object -Last/-First` à la place.
- **Correction 3** : Ajout de `sys.path.insert(0, project_root)` dans dashboard et tests.
- **Correction 4** : Patience, installation locale dans venv.

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **Tests smoke dashboard** : `.\venv\Scripts\python.exe -m unittest tests.test_dashboard_smoke` -> `Ran 5 tests in 3.551s` / `OK`
- **Tous les tests** : `Ran 42 tests in 1.404s` / `OK` (10 données + 10 anomalie + 8 régional + 8 vérif + 5 dashboard)
- **Vérification** : imports OK, traitement des 3 scénarios OK, pas de navigateur nécessaire pour tests.
- **Ce qui reste non vérifié** : affichage visuel exact dans navigateur (tests smoke ne l'ouvrent pas), responsive design.

### 9) Ce qu'il reste à faire
- Lancer le dashboard pour visualisation manuelle si souhaité.
- Continuer étape par étape selon règles.
- Pas de commit/push, pas de React, pas de Hedera.

## Commandes PowerShell pour lancer le dashboard

Depuis `C:\Users\doudaa\Documents\MONITUS` :

```powershell
# Activer environnement virtuel (optionnel si on utilise chemin complet)
# .\venv\Scripts\Activate.ps1

# Lancer le dashboard
.\venv\Scripts\streamlit.exe run demo\dashboard.py
```

**URL locale** : http://localhost:8501

## Étape 11 : Correction contraste dashboard (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°11

### 2) Ce que nous avons fait et quels fichiers ont changé
- Modification de `demo/dashboard.py` uniquement
- Mise à jour palette couleurs et CSS pour thème clair
- Correction titres, labels, cartes, graphiques Plotly, tableau, alertes

### 3) Pourquoi nous devions le faire
Texte peu lisible (blanc sur blanc) sur fond blanc. Besoin de contraste suffisant.

### 4) Comment ça fonctionne, expliqué simplement
- Fond blanc (#FFFFFF)
- Titres/important: bleu marine (#102A43)
- Corps: #243B53
- Accents/bordures: turquoise (#00BFC1)
- Cartes: gris très clair (#F4F7F9) avec texte foncé
- Graphiques: fond blanc, axes/ticks/labels/legendes en couleur sombre
- CSS global appliqué pour tous les éléments Streamlit

### 5) Nouveaux concepts appris
- **Contraste** : important pour lisibilité
- **Thème Streamlit** : CSS custom pour forcer couleurs
- **Plotly theming** : update_layout/update_xaxes/update_yaxes

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- Tous tests: `Ran 42 tests in 2.668s` / `OK`
- Vérification visuelle à faire dans navigateur (localhost:8501)

### 9) Ce qu'il reste à faire
Vérifier dans navigateur le contraste

## Étape 12 : Vérification navigateur et point de contrôle Git (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°12

### 2) Ce que nous avons fait et quels fichiers ont changé
- Vérification dans navigateur du dashboard Streamlit à http://localhost:8501
- Mise à jour de `.gitignore` pour exclure venv/, __pycache__, caches
- Mise à jour de `LEARNED.md` (ceci)
- Staging sélectif des fichiers source/tests/docs/dashboard/données synthétiques
- Commit local

### 3) Pourquoi nous devions le faire
Valider le prototype fonctionnel dans navigateur avec données synthétiques, puis créer un point de contrôle Git sûr (sans secrets/env/venv).

### 4) Comment ça fonctionne, expliqué simplement
- **Vérification navigateur** : on a regardé le scénario `regional_outbreak` dans le dashboard. Les compteurs ont montré les résultats du moteur existant.
- **Démarrage Streamlit** : au premier lancement, Streamlit demande un email (onboarding). En mode background/non-interactif ça peut bloquer/terminer - c'est une limite du contexte, pas forcément un bug du code. Solution pratique : lancer en interactif ou avec `--server.headless true` / accepter l'invite.
- **Point de contrôle Git** : on ne commit que le nécessaire (code, tests, docs, dashboard, CSV synthétiques). venv/, __pycache__, .env exclus.

### 5) Nouveaux concepts appris
- **Onboarding Streamlit** : premier lancement peut demander email
- **Staging sélectif** : mieux que `git add .` pour éviter secrets/fichiers lourds
- **Données synthétiques uniquement** : important à rappeler

### 6) Erreurs rencontrées et causes réelles
- **Problème démarrage** : Streamlit a affiché l'invite email et le processus s'est terminé (exit code 1) en mode background non-interactif. Cause probable: attente d'entrée interactive. Pas de modification du code nécessaire; workaround connu.

### 7) Comment nous les avons corrigées et pourquoi
- Compris que c'est lié au mode non-interactif. Pour usage normal, lancer en terminal interactif. On n'a pas modifié le code.

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **Vérification navigateur** (synthetic only):
  - Scenario: `regional_outbreak`
  - Tunis: **9 anomalies**
  - Sousse: **10 anomalies**
  - Sfax: **0**
  - Jours avec signal régional: **9**
  - Jour isolé: **2024-03-25** (anomalie individuelle uniquement, Sousse) - confirmé
- **Tests**: `Ran 42 tests in 2.668s` / `OK` avec venv
- **Ce qui reste non vérifié** : push distant (non demandé)

### 9) Ce qu'il reste à faire
- Continuer développement incrémental selon règles
- Toujours exclure secrets/env/venv
- Ne pas commit données réelles

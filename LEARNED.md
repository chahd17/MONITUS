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

### 5) Nouveaux concepts appris
- **Commit** : sauvegarde traçable d'un ensemble de fichiers.
- **Hash de commit** (identifiant unique) : comme une empreinte digitale du commit.
- **Arbre de travail propre** (working tree clean) : tous les changements sont enregistrés, rien à committer.

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **Vérif identité Git** : `git config user.name` -> `Chahd`, `git config user.email` -> `chahddimessi@gmail.com` (existaient déjà).
- **Vérif fichiers à committer** : seuls `README.md`, `.gitignore`, `AGENTS.md`, `LEARNED.md`, `docs/PROJECT_PLAN.md` ajoutés. Pas de `.env`, secrets, clés, données patients, ni dossiers node_modules/venv/build présents.
- **Commit** : `[master (root-commit) 19b8939] chore: initialize MONITUS project foundation` - 5 fichiers modifiés, 308 insertions(+).
- **git status** : `On branch master` / `nothing to commit, working tree clean`.
- **git log -1 --oneline** : `19b8939 chore: initialize MONITUS project foundation`
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
- **Graine aléatoire (random seed)** : si on donne la même graine à un générateur aléatoire, il produit la même suite de nombres à chaque fois.
- **Scénarios** : normal (stable), regional_outbreak (hausse soutenue sur ≥2 hôpitaux derniers 14j), reporting_error (pic extrême sur 1 seul hôpital).

### 5) Nouveaux concepts appris
- **CSV**, **unittest**, **reproductibilité**, **scénarios de test**

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- Générateur : `normal.csv`, `regional_outbreak.csv`, `reporting_error.csv` (270 lignes chacun)
- Tests : `Ran 10 tests in 0.107s` / `OK`

### 9) Ce qu'il reste à faire
Continuer étape par étape, toujours mettre à jour LEARNED.md.

## Étape 7 : Détecteur d'anomalies robuste par hôpital (Step 2.2) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°7

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `ai_service/anomaly_detector.py`, `ai_service/__init__.py`
- Création de `tests/test_anomaly_detector.py`
- CLI sur 3 scénarios, tests passés
- Mise à jour `docs/PROJECT_PLAN.md`

### 3) Pourquoi nous devions le faire
Détection par hôpital avec médiane/MAD, fenêtre glissante 21 jours, seuil 3.5, pas de fuite future.

### 4) Comment ça fonctionne, expliqué simplement
- **Médiane** plus robuste que moyenne
- **MAD** mesure dispersion robuste
- **Score** = (valeur - médiane)/ (1.4826*MAD), alerte si > 3.5
- **Fenêtre** uniquement historique (précédents 21 jours)
- **MAD==0** fallback documenté

### 5) Nouveaux concepts appris
Statistiques robustes, no leakage, fenêtre glissante

### 6) Erreurs rencontrées et causes réelles
- Import échouait (dossier `ai-service` -> renommé `ai_service`)
- Test fuite corrigé (médiane ne fuit pas)

### 7) Comment nous les avons corrigées et pourquoi
Renommage + correction test

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- regional_outbreak: Tunis 9, Sousse 10, Sfax 0
- reporting_error: Tunis 1 (2024-02-28)
- Tests: `Ran 21 tests in 0.132s` / `OK`

### 9) Ce qu'il reste à faire
Continuer étape par étape

## Étape 8 : Corrélation croisée entre hôpitaux (Step 2.3) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°8

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création `ai_service/regional_detector.py`, `tests/test_regional_detector.py`
- Mise à jour docs

### 3) Pourquoi nous devions le faire
Signaux régionaux si >=2 hôpitaux même jour (quorum), pas confirmation épidémie

### 4) Comment ça fonctionne, expliqué simplement
Regroupement par date calendaire, hôpitaux distincts, quorum configurable

### 5) Nouveaux concepts appris
Corrélation temporelle, quorum, données manquantes

### 6) Erreurs rencontrées et causes réelles
Aucune

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- regional_outbreak: 9 jours signaux régionaux (17-24, 26 Mar 2024), 25 Mar isolé
- Tests: `Ran 29 tests in 0.126s` / `OK`

### 9) Ce qu'il reste à faire
Continuer

## Étape 9 : Vérification déterministe et tri des fausses alertes (Step 2.4) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°9

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création `ai_service/alert_verifier.py`, `tests/test_alert_verifier.py`
- Mise à jour docs

### 3) Pourquoi nous devions le faire
Classer statuts sans confirmer épidémie, persistance dans fenêtre glissante 3 jours

### 4) Comment ça fonctionne, expliqué simplement
Statuts: NORMAL, ISOLATED_ANOMALY, REGIONAL_SIGNAL_UNCONFIRMED, REGIONAL_SIGNAL_REQUIRES_REVIEW. Persistance >=2 jours régionaux dans fenêtre 3 jours, sans fuite future. Anomalies isolées restent visibles.

### 5) Nouveaux concepts appris
Vérification déterministe, persistance, tri fausses alertes

### 6) Erreurs rencontrées et causes réelles
Aucune

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- regional_outbreak: 17 Mar UNCONFIRMED, 18-24,26 Mar REQUIRES_REVIEW, 25 Mar ISOLATED_ANOMALY
- reporting_error: 28 Feb ISOLATED_ANOMALY
- Tests: `Ran 37 tests in 0.139s` / `OK`

### 9) Ce qu'il reste à faire
Continuer

## Étape 10 : Prototype visuel Streamlit (Step 2.5 prototype) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°10

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création venv, installation streamlit/plotly/pandas
- Création `demo/dashboard.py`, `tests/test_dashboard_smoke.py`

### 3) Pourquoi nous devions le faire
Visualisation réutilisant moteurs existants

### 4) Comment ça fonctionne, expliqué simplement
Dashboard interactif avec scénarios, graphiques, statuts, données synthétiques

### 5) Nouveaux concepts appris
Streamlit, Plotly, smoke tests

### 6) Erreurs rencontrées et causes réelles
Commandes PowerShell (&&, tail/head), import paths, onboarding Streamlit

### 7) Comment nous les avons corrigées et pourquoi
Syntaxe adaptée, sys.path, lancement interactif

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- Tests smoke: OK
- Tous tests: `Ran 42 tests in 1.404s` / `OK`

### 9) Ce qu'il reste à faire
Vérification visuelle navigateur

## Étape 11 : Correction contraste dashboard (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°11

### 2) Ce que nous avons fait et quels fichiers ont changé
- Modification `demo/dashboard.py` (thème clair, CSS, Plotly)

### 3) Pourquoi nous devions le faire
Améliorer lisibilité contraste

### 4) Comment ça fonctionne, expliqué simplement
Palette claire avec texte foncé, CSS global

### 5) Nouveaux concepts appris
Contraste, theming

### 6) Erreurs rencontrées et causes réelles
Aucune

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
Tous tests OK

### 9) Ce qu'il reste à faire
Vérif visuelle

## Étape 12 : Vérification navigateur et Git (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°12

### 2) Ce que nous avons fait et quels fichiers ont changé
- Vérification dashboard navigateur
- Mise à jour `.gitignore`
- Staging sélectif, commit local

### 3) Pourquoi nous devions le faire
Valider prototype, créer checkpoint sûr

### 4) Comment ça fonctionne, expliqué simplement
Onboarding Streamlit, staging sélectif

### 5) Nouveaux concepts appris
Onboarding, sélection fichiers

### 6) Erreurs rencontrées et causes réelles
Onboarding blocage mode non-interactif

### 7) Comment nous les avons corrigées et pourquoi
Compris, pas modifié code

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- Navigateur regional_outbreak: Tunis 9, Sousse 10, Sfax 0, 9 jours régionaux, 25 Mar isolé - confirmé
- Tests OK

### 9) Ce qu'il reste à faire
Continuer incrémental

## Étape 13 : API REST minimal read-only (Step 2.5) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°13

### 2) Ce que nous avons fait et quels fichiers ont changé
- Installation fastapi/uvicorn/httpx dans venv
- Création `requirements-api.txt`, `ai_service/api.py`, `tests/test_api.py`
- Mise à jour `docs/PROJECT_PLAN.md`, `LEARNED.md`

### 3) Pourquoi nous devions le faire
Accès programmatique JSON, réutiliser moteurs, read-only

### 4) Comment ça fonctionne, expliqué simplement
Endpoints /health, /scenarios, /surveillance/summary, /alerts, /hospitals. Validation scénarios 422. Labels synthetic_only True, confirmed_outbreak False. TestClient pour tests.

### 5) Nouveaux concepts appris
API REST, FastAPI, JSON, schéma stable

### 6) Erreurs rencontrées et causes réelles
Champ confirmed_outbreak manquant health (corrigé), warning httpx/starlette non bloquant

### 7) Comment nous les avons corrigées et pourquoi
Ajout champ

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- API 9/9 OK
- Tous 51/51 OK
- Réponse summary regional_outbreak OK

### 9) Ce qu'il reste à faire
Pas d'auth/deploy

## Étape 14 : Vérification finale Step 2.6 - API navigateur, cohérence, commit Git (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°14

### 2) Ce que nous avons fait et quels fichiers ont changé
- Vérification Git status, inspection projet
- Exécution complète tests avec venv existant
- Vérification cohérence moteurs vs API TestClient (normal, regional_outbreak, reporting_error)
- Vérification requirements-api.txt et .gitignore
- Relecture docs/PROJECT_PLAN.md (Part 2)
- Mise à jour LEARNED.md avec test navigateur réel
- Staging fichiers pertinents uniquement
- Création commit local
- Vérification statut propre + hash

### 3) Pourquoi nous devions le faire
Clôturer Part 2 (Hospital Data & AI Detection) proprement: tests réels, cohérence vérifiée, docs à jour, checkpoint Git sans fichiers sensibles.

### 4) Comment ça fonctionne, expliqué simplement
- **HTTP 200** : code HTTP signifiant "OK" - la requête a réussi, serveur renvoie données demandées. Dans Swagger UI navigateur, GET /api/v1/surveillance/summary?scenario=regional_outbreak a retourné HTTP 200.
- **JSON** (JavaScript Object Notation) : format d'échange de données lisible humain/machine. Structure clé-valeur. Réponse contenait hôpitaux, dates signaux régionaux, flags synthetic_only/confirmed_outbreak.
- **FastAPI** : framework Python pour créer API web rapidement. Génère documentation interactive (Swagger UI /docs). Réutilise moteurs existants (anomaly_detector, regional_detector, alert_verifier) sans duplication.
- **Vérification cohérence** : API utilise mêmes fonctions -> résultats identiques aux moteurs directs. Confirmé pour tous 3 scénarios.

### 5) Nouveaux concepts appris
- **HTTP status codes** : 200 OK vs 422 validation erreur
- **Swagger UI** : interface pour tester API dans navigateur
- **Cohérence API/moteurs** : important pour éviter dérive
- **Staging sélectif** : éviter venv/__pycache__/.env/secrets

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée lors de cette vérification finale. Tous tests OK, cohérence parfaite.

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **Tests complets venv** : `Ran 51 tests in 3.115s` / `OK` (data_generation 10 + anomaly_detector 10 + regional_detector 8 + alert_verifier 8 + dashboard_smoke 5 + api 9)
- **Cohérence moteurs vs API TestClient** :
  - normal: API/ENG hôpitaux (0,0,0), signaux régionaux vides, assessments vides
  - regional_outbreak: API/ENG hôpitaux (9,10,0), 9 dates identiques ['2024-03-17','18','19','20','21','22','23','24','26']. ENG assessments montrent 17 Mar UNCONFIRMED, 18-24,26 Mar REQUIRES_REVIEW (2 sites), 25 Mar ISOLATED_ANOMALY (1 site). API expose summary/alerts/hospitals correctement.
  - reporting_error: API/ENG (1,0,0), vide signaux régionaux, ENG assessment (2024-02-28, ISOLATED_ANOMALY, 1)
- **Test navigateur (réel, Swagger UI)** : GET /api/v1/surveillance/summary?scenario=regional_outbreak → HTTP 200, JSON, Tunis 9 anomalies, Sousse 10, Sfax 0, 9 dates régionales (2024-03-17 à 24, 26), 2024-03-25 classé anomalie isolée Sousse, synthetic_only=true, confirmed_outbreak=false. Confirmé.
- **requirements-api.txt** présent (fastapi==0.162.0, httpx==0.28.1, pydantic==2.14.1, pydantic_core==2.50.1, uvicorn==0.54.0). .gitignore exclut venv/, __pycache__/, .env, secrets/.
- **Part 2**: Steps 2.1-2.4 complets, Step 2.5 (API minimal read-only) complété. Part 2 marquée complète dans PROJECT_PLAN.md.
- **Ce qui reste non vérifié** : push distant, déploiement (non demandés).

### 9) Ce qu'il reste à faire
Aucun. Part 2 clôturée. Respecter règles pour étapes futures.

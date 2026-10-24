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

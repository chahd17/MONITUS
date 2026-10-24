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

## Étape 15 : Détecteur challenger EWMA indépendant (Step 3.1) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°15

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `ai_service/ewma_detector.py` (bibliothèque standard Python uniquement).
- Création de `tests/test_ewma_detector.py` (16 tests).
- Exécution du CLI EWMA sur les 3 CSV synthétiques.
- Exécution de tous les tests (anciens + nouveaux).
- Mise à jour de `docs/PROJECT_PLAN.md` (uniquement Step 3.1).
- Mise à jour de `LEARNED.md` (ceci).
- Aucun fichier existant de détection, dataset, API ou dashboard modifié.

### 3) Pourquoi nous devions le faire
Notre détecteur actuel utilise médiane + MAD. Pour éviter de dépendre d'une seule méthode, il faut une **deuxième méthode indépendante**. EWMA (Exponentially Weighted Moving Average = moyenne mobile à pondération exponentielle) est une méthode classique de surveillance qui donne plus de poids aux jours récents. Le but de cette étape n'est PAS de dire laquelle est meilleure (ce sera Step 3.2), mais de produire des résultats EWMA propres, séparés et reproductibles.

### 4) Comment ça fonctionne, expliqué simplement
- **Alpha (α)** : facteur de lissage, par défaut `0.2`. Chaque jour, la nouvelle moyenne attendue = `α × valeur_du_jour + (1-α) × ancienne_moyenne`. Avec α=0.2, le jour actuel compte pour 20 % et l'historique pour 80 %.
- **Exemple concret** : si la moyenne attendue est 10 et qu'on observe 20, la moyenne devient `0.2×20 + 0.8×10 = 12`. Le lendemain, on observe 30 : on la compare d'abord à 12 (donc avant mise à jour), puis la moyenne devient `0.2×30 + 0.8×12 = 15.6`.
- **Initialisation** : les 21 premiers jours servent uniquement à calculer la moyenne de départ. Aucune alerte n'est émise avant le 22e jour (21 jours d'historique + 1 jour à noter).
- **Score** : `(cas_observés - attendu) / échelle`. Le score est calculé **avant** de mettre à jour la moyenne : le jour actuel ne peut donc pas influencer sa propre référence (pas de fuite future).
- **Échelle (variabilité)** : au départ, on mesure l'écart absolu moyen autour de la moyenne initiale, puis on le convertit en équivalent écart-type avec le facteur `1.2533`. Ensuite, l'échelle est mise à jour causalement : `nouvelle_échelle_brute = α × |observé - attendu_avant| + (1-α) × ancienne_échelle_brute`.
- **Variabilité nulle ou quasi nulle** : si l'échelle tombe sous `min_scale` (1.0 par défaut), on la bloque à 1.0. Cela évite une division par zéro et un score infini quand tous les comptages sont identiques. Le champ `scale_fallback_used` indique quand ce garde-fou est utilisé.
- **Sens unique** : seules les hausses anormales sont signalées (`score > threshold`, défaut 3.0). Une forte baisse n'est pas une alerte. Le seuil est statistique et **non validé cliniquement**.

### 5) Nouveaux concepts appris
- **EWMA** : moyenne qui oublie progressivement le passé lointain et réagit plus vite aux changements récents.
- **Détecteur challenger** : deuxième méthode indépendante pour comparer plus tard, sans mélanger les scores.
- **Causalité** : utiliser uniquement le passé pour prédire le présent ; ne jamais regarder le futur.
- **Échelle robuste** : estimer la variabilité à partir des écarts absolus, avec un plancher pour les séries plates.
- **Un seul côté** : une surveillance épidémique s'intéresse aux augmentations, pas aux baisses.

### 6) Erreurs rencontrées et causes réelles
- **Erreur 1** : Dans ma première version, l'échelle était déjà convertie en équivalent écart-type puis reconvertie à chaque mise à jour avec `1.2533` (double conversion).
- **Erreur 2** : Imports inutilisés et ligne de test sans effet.

### 7) Comment nous les avons corrigées et pourquoi
- L'échelle reste en unités écart absolu moyen et n'est convertie qu'au moment du score. Mise à jour avec la bonne unité.
- Nettoyage des imports/lignes inutiles.

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
- **CLI EWMA** (seuil 3.0, α=0.2) : normal 0/0/0 ; regional_outbreak Tunis 1 (17/03/2024), Sousse 1 (17/03/2024), Sfax 0 ; reporting_error Tunis 1 (28/02/2024).
- **Tests EWMA** : 16/16 OK. **Tous les tests** : 67/67 OK.
- **Limitation** : EWMA ne signale que le début de la hausse dans regional_outbreak car il s'adapte rapidement (comportement attendu). Comparaison avec médiane/MAD à venir Step 3.2.

### 9) Ce qu'il reste à faire
Step 3.2 : comparer les deux détecteurs sans les modifier. Ne pas installer de paquets, ne pas committer/pousser.

## Étape 16 : Comparaison rigoureuse Median/MAD vs EWMA (Step 3.2) (2026-10-24)

### 1) Date et numéro d'étape
- Date : 2026-10-24
- Étape n°16

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `ai_service/detector_benchmark.py` (bibliothèque standard uniquement).
- Création de `tests/test_detector_benchmark.py` (12 tests).
- Création de `reports/` et `reports/detector_benchmark.json`.
- Exécution du benchmark CLI.
- Exécution de tous les tests (anciens + nouveaux).
- Mise à jour de `LEARNED.md` (ceci).
- Aucun fichier de détection existant, données synthétiques, API ou dashboard modifié.

### 3) Pourquoi nous devions le faire
Comparer objectivement les deux détecteurs sans les trafiquer, avec une vérité terrain dérivée directement du générateur (scripts/generate_hospital_data.py), pas avec les prédictions d'un détecteur.

### 4) Comment ça fonctionne, expliqué simplement
**Vocabulaire débutant** :
- **TP (vrai positif)** : alarme signalée ET c'est bien un jour étiqueté comme événement. Juste.
- **FP (faux positif)** : alarme signalée MAIS ce n'est pas un événement étiqueté. Faux signal.
- **TN (vrai négatif)** : pas d'alarme ET ce n'est pas un événement. Correct.
- **FN (faux négatif)** : pas d'alarme MAIS c'était un événement. Raté.
- **Précision** = TP/(TP+FP) - Parmi les alarmes, combien sont justes ?
- **Rappel** = TP/(TP+FN) - Parmi les événements, combien sont détectés ?
- **F1** = 2×(précision×rappel)/(précision+rappel) - Compromis entre les deux. Si dénominateur nul, on écrit **N/A** (non défini), on n'invente pas de valeur.
- **Délai de détection** = jours entre le début (onset) et la première vraie alarme.

**Vérité terrain depuis le générateur** :
- **normal** : aucun label positif (tout doit être TN).
- **regional_outbreak** : augmentation **soutenue** les **14 derniers jours** uniquement pour HOSP_TUN et HOSP_SOU. HOSP_SFX non étiqueté. On ne labelle **pas** les 90 jours entiers comme anormaux.
- **reporting_error** : **un seul jour** de pic extrême sur **HOSP_TUN uniquement**, offset calculé de façon déterministe avec seed 12345 (`rng.randint(10, days-20)`). Traité comme **événement simulé de qualité de données**, **pas** comme une épidémie confirmée.

**Règles** : jours avec contexte historique valide uniquement (période d'échauffement exclue). Réutilisation des fonctions existantes, pas de modification/tuning des détecteurs.

### 5) Nouveaux concepts appris
- **Matrice de confusion** : voir clairement les erreurs
- **Compromis précision/rappel** : il y a souvent un équilibre
- **Vérité terrain indépendante** : doit venir de la source de construction
- **Warm-up** : exclure pour une évaluation équitable
- **Gérer dénominateur zéro** : mieux vaut dire N/A que donner un faux chiffre

### 6) Erreurs rencontrées et causes réelles
- Erreur de calcul de l'offset du spike → corrigé en reproduisant exactement le code du générateur.
- Division par zéro potentielle → ajout de gestion explicite avec None/N/A.
- Confusion "tout le dataset" vs "14 derniers jours" → corrigé en labelant uniquement les jours de l'événement.

### 7) Comment nous les avons corrigées et pourquoi
Relecture du générateur, reproduction déterministe, gestion explicite des cas indéfinis avec documentation.

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
**Résultats réels** :
- **normal** : tous TN, pas de faux positifs.
- **regional_outbreak** (onset 2024-03-17, 14 jours, TUN/SOU) :
  - Médiane/MAD (fenêtre 21j, seuil 3.5) : TUN TP=9/14 (rappel 0.643), SOU TP=10/14 (rappel 0.714), global précision 1.000, rappel 0.679, F1 0.809. Détecte au jour 0.
  - EWMA (alpha 0.2, seuil 3.0) : seulement 1er jour (TUN/SOU TP=1 chacun), global précision 1.000, rappel 0.071, F1 0.133. S'adapte rapidement à hausse soutenue → rate la suite avec ces paramètres (comportement attendu).
- **reporting_error** (pic unique 2024-02-06 sur TUN) : résultats mitigés, traité comme événement qualité données.
- **Sensibilité seuils** (sans changer défauts) : Médiane/MAD 2.5→21 alarmes, 4.0→18 ; EWMA 2.0→5, 3.0→2.
- **Tests** : `tests.test_detector_benchmark` 12/12 OK. **Tous les tests** : `Ran 79 tests in 3.750s` / **OK**. `reports/detector_benchmark.json` généré.

**Limitations** : uniquement données synthétiques, pas de revendication clinique/réelle, warm-up exclu, détecteurs non optimisés, comparaison sensible aux paramètres/au type d'événement.

### 9) Ce qu'il reste à faire
Aucun changement aux détecteurs. Benchmark terminé. Respecter les règles.

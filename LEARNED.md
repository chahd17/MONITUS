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


## Étape 17 : Step 3.4 micro-step 1 - Modèle LogReg NumPy compatible FedAvg (2026-10-27)

### 1) Date et numéro d'étape
- Date : 2026-10-27
- Étape n°17

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `ai_service/fl_model.py` (modèle `BinaryLogisticRegression` en NumPy pur)
- Création de `tests/test_fl_model.py` (15 tests focalisés)
- Mise à jour de `LEARNED.md` (ceci)
- Aucun fichier existant du Step 3.3 modifié (`ai_service/ml_detector.py`, artifacts, `reports/ml_evaluation.json`)
- Aucun ajout de partitionnement/client/serveur/FedAvg/CLI

### 3) Pourquoi nous devions le faire
Préparer un socle minimal et agrégable pour la simulation fédérée. Un objet `sklearn.LogisticRegression` déjà ajusté n'est pas directement moyennable de façon triviale ; il faut des paramètres explicites (`coef_`, `intercept_`) pour un FedAvg pondéré plus tard.

### 4) Comment ça fonctionne, expliqué simplement
- **Modèle linéaire explicite** : entrée 18 dimensions, vecteur de poids et biais distincts. Paramètres accessibles via `get_params()`/`set_params()` avec copies et vérification des formes.
- **Sigmoïde stable** : clipping de `z` dans `[-500,500]` avant `exp` pour éviter débordements.
- **Entropie croisée binaire stable** : clipping des probabilités avec epsilon avant log.
- **Descente de gradient** : `fit(X,y)` met à jour les paramètres actuels par itérations documentées (`learning_rate`, `max_iter`). Support `class_weight='balanced'` (pondération par classe). Pour FedAvg, un client doit appeler `set_params(global_params)` avant chaque round local.
- **Prédictions** : `predict_proba` / `predict` avec seuil configurable.
- **Validations** : entrées vides, valeurs non-finies, labels invalides (seulement 0/1), dimensions incompatibles avec 18 features.

### 5) Nouveaux concepts appris
- **Paramètres agrégables** : séparer modèle et paramètres numériques pour permettre une moyenne pondérée.
- **Stabilité numérique** : clipping/logits extrêmes pour sigmoïde et BCE.
- **Déterminisme** : initialisation avec `random_state` pour reproductibilité.

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
**Tests focalisés `tests.test_fl_model`** : **15/15 OK** (`Ran 15 tests in 0.059s`)
- Couverture : initialisation, stabilité sigmoïde, formes `predict_proba/predict` (1D/2D), apprentissage (baisse de loss), déterminisme, copies dans `get/set_params` + vérification formes, validations (vides/non-finis/labels/dimensions), stabilité numérique, BCE stable.

**Suite complète** : **153/153 OK** (`Ran 153 tests in 3.479s`) - inclut les 15 nouveaux tests.

**Ce qui reste non vérifié** : partitionnement par hôpital, clients/serveur, agrégation FedAvg pondérée, CLI, comparaison baseline vs fédéré, stratégie de transformation sans scaler global sur données privées.

### 9) Ce qu'il reste à faire
Micro-step 2 : partitionnement, clients, serveur, FedAvg pondéré selon le plan approuvé, avec avertissement explicite "Ordinary FedAvg provides no formal privacy guarantee, secure aggregation, or differential privacy".

**Limites connues** :
- Uniquement le modèle (pas de logique fédérée)
- `fit()` démarre depuis les paramètres actuels (nécessite `set_params(global_params)` avant chaque round local pour FedAvg)
- Pas de transformation fixe partagée encore définie (sera abordée séparément selon ajustements)
- Confidentiel/simulation uniquement, aucune garantie formelle de confidentialité


## Étape 18 : Step 3.4 micro-step 2 - Partitionnement par hôpital pour simulation fédérée (2026-10-27)

### 1) Date et numéro d'étape
- Date : 2026-10-27
- Étape n°18

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `ai_service/fl_utils.py` (partitionnement déterministe par hôpital)
- Création de `tests/test_fl_partitioning.py` (12 tests focalisés)
- Mise à jour de `LEARNED.md` (ceci)
- Aucun fichier Step 3.3 modifié (ml_detector, models, rapport ml_evaluation)
- Aucun client/serveur/agrégation/CLI/baseline centralisé implémenté

### 3) Pourquoi nous devions le faire
Créer une couche de partitionnement testable pour simuler un apprentissage fédéré à travers trois hôpitaux fictifs (Tunis, Sousse, Sfax), sans mélanger les données brutes entre hôpitaux ni entre simulations.

### 4) Comment ça fonctionne, expliqué simplement
- **Isolation par hôpital** : chaque partition contient uniquement les données de son `hospital_id`. Pas de fusion de données brutes entre hôpitaux dans ce module.
- **Réutilisation Step 3.3** : mêmes 18 features causales via `ai_service.ml_features.build_causal_features`, même fenêtre de 21 observations (réchauffement), mêmes sémantiques de labels.
- **Séparation stricte par simulation** : split train/val/test par simulations entières avec graines/seeds disjoints. Historiques réinitialisés par simulation/hôpital, pas de fuite temporelle ou entre simulations.
- **Provenance** : métadonnées `sim_id`, `sim_seed`, `hospital_id`, `date`, `scenario`, `split`, `is_reporting_error` pour auditabilité.
- **Labels** : `reporting_error` traité comme négatif (0) comme dans Step 3.3.
- **Pas de scaler global sur données privées** : aucun ajustement de scaler sur données agrégées hospitalières. Constantes fixes documentées (`FIXED_TRANSFORMATION_CONSTANTS`) sans ajustement sur test.
- **Validation** : dimensions features (18), valeurs finies, alignement X/y/meta, identifiants manquants/dupliqués, partitions vides justifiées.

### 5) Nouveaux concepts appris
- **Partitionnement fédéré simulé** : chaque client garde ses propres données localement.
- **Auditabilité** : métadonnées de provenance essentielles pour détecter les fuites.
- **Pas de pooling** : séparation claire entre "partitionnement local" et "benchmark centralisé" (ce dernier serait dans un contexte séparé si ajouté plus tard).

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
**Tests focalisés `tests.test_fl_partitioning`** : **12/12 OK** (`Ran 12 tests in 2.057s`)
- Isolation simulations, disjonction splits, isolation par hôpital, alignement features (18), provenance, labels reporting_error négatifs, déterminisme, alignement échantillons, warmup 21 obs, validation entrées.

**Suite complète** : **165/165 OK** (`Ran 165 tests in 5.163s`) - 12 nouveaux tests ajoutés.

**Comptes par partition (réels)** :
- Train: HOSP_TUN 560 (56 pos/504 neg), HOSP_SOU 560 (56 pos/504 neg), HOSP_SFX 560 (0 pos/560 neg). Sims: 1001-1008
- Val: HOSP_TUN 350 (14/336), HOSP_SOU 350 (14/336), HOSP_SFX 350 (0/350). Sims: 2001-2005
- Test: HOSP_TUN 420 (28/392), HOSP_SOU 420 (28/392), HOSP_SFX 420 (0/420). Sims: 3001-3006

**Ce qui reste non vérifié** : clients/serveur fédérés, agrégation FedAvg, CLI d'entraînement, baseline centralisé, normalisation partagée.

### 9) Ce qu'il reste à faire
Micro-step 3 (si approuvé) : clients/serveur, agrégation pondérée par nombre d'échantillons, sans échange de données brutes.

**Limites connues** :
- **Simulation uniquement** : aucun garantie formelle de confidentialité (pas de secure aggregation, pas de differential privacy)
- Pas de scaler global ajusté sur données privées (transformation fixe documentée si nécessaire plus tard)
- Pas d'accès central aux données brutes hospitalières dans ce module


## Étape 19 : Step 3.4 micro-step 3 - Clients fédérés locaux (2026-10-27)

### 1) Date et numéro d'étape
- Date : 2026-10-27
- Étape n°19

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `ai_service/fl_client.py` (`LocalFederatedClient`)
- Création de `tests/test_fl_client.py` (13 tests focalisés)
- Mise à jour de `LEARNED.md` (ceci)
- Aucun serveur d'agrégation, baseline centralisé, CLI, intégration dashboard/API
- Aucun fichier Step 3.3 modifié

### 3) Pourquoi nous devions le faire
Ajouter des clients locaux simulés, chacun lié à un hôpital et à sa partition isolée, capables de s'entraîner à partir de paramètres globaux sans exposer de données brutes.

### 4) Comment ça fonctionne, expliqué simplement
- **Propriétaire unique** : chaque client possède exactement une partition (`HOSP_TUN`, `HOSP_SOU`, `HOSP_SFX`).
- **Round local** : `train_round(global_params)` appelle obligatoirement `set_params(global_params)` avant `fit()`, pour partir des mêmes paramètres globaux à chaque round.
- **Entraînement local uniquement** : utilise uniquement ses propres `X_local`, `y_local` copiés. Aucune fusion de données.
- **Mise à jour restreinte** : retourne `{hospital_id, coef (copie), intercept (copie), n_samples, num_samples}`. Aucun `X`, `y`, `meta`, historique de features.
- **Copies & isolation** : paramètres retournés copiés, états mutables non partagés entre clients, accès inter-hôpitaux impossible.
- **Pas de class_weight='balanced'** : tous clients utilisent `class_weight=None`. Sfax n'a que des négatifs (0 positifs) dans les partitions utilisées ; équilibrage indépendant serait incohérent.
- **Client tout-négatif** : Sfax géré sans erreur, entraînement fini, paramètres restitués finis.
- **Taux d'apprentissage/itérations identiques** : mêmes hyperparamètres pour tous les clients dans cette expérience initiale.

### 5) Nouveaux concepts appris
- **Initialisation round** : séparation claire "recevoir paramètres globaux" vs "entraîner localement".
- **Minimisation de fuite** : n'échanger que des paramètres agrégables, pas des échantillons.
- **Gestion client dégénéré** : cas sans positifs doit rester numériquement stable.

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
**Tests focalisés `tests.test_fl_client`** : **13/13 OK** (`Ran 13 tests in 0.755s`)
- 3 identités hôpital distinctes, liaisons partitions correctes, initialisation depuis mêmes paramètres globaux, isolation entre états clients, pas de données brutes dans update, copies non-mutables, comptes corrects, Sfax tout-négatif OK, déterminisme, validations formes/inputs, pas d'accès inter-hôpitaux, mises à jour finies.

**Suite complète** : **178/178 OK** (`Ran 178 tests in 6.863s`) - 13 nouveaux tests ajoutés.

**Normalisation fixe** : `FIXED_TRANSFORMATION_CONSTANTS` dans `ai_service/fl_utils.py` documente des constantes prédéfinies (`mean/scale` None, `applied: False`). **Aucun** ajustement sur validation/test ni sur données privées agrégées. Aucun scaler global utilisé. Cela correspond aux exigences.

**Ce qui reste non vérifié** : serveur FedAvg, agrégation pondérée, baseline centralisé, boucle complète d'entraînement fédéré.

### 9) Ce qu'il reste à faire
Micro-step 4 (si approuvé) : serveur d'agrégation FedAvg pondéré par nombre d'échantillons, sans échange de données brutes.

**Limites connues** :
- **Simulation uniquement** : **Ordinary FedAvg ne fournit aucune garantie formelle de confidentialité, secure aggregation ou differential privacy**. Échanger uniquement des paramètres peut encore fuiter de l'information.
- Pas d'agrégation encore implémentée
- Pas de transformation appliquée (constantes fixes non utilisées)
- Pas d'équilibrage de classes (intentionnel pour Sfax sans positifs)


## Étape 20 : Step 3.4 micro-step 4 - Serveur d'agrégation FedAvg (2026-10-27)

### 1) Date et numéro d'étape
- Date : 2026-10-27
- Étape n°20

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `ai_service/fl_server.py` (`FederatedAggregator`)
- Création de `tests/test_fl_server.py` (13 tests focalisés)
- Mise à jour de `ai_service/fl_client.py` : unification champ update vers `n_samples` uniquement (suppression `num_samples` redondant), tests clients mis à jour
- Mise à jour de `LEARNED.md` (ceci)
- Aucun multi-round orchestration, baseline centralisé, réseau/blockchain/secure aggregation/DP, dashboard/API

### 3) Pourquoi nous devions le faire
Ajouter un agrégateur FedAvg déterministe acceptant uniquement des mises à jour locales (paramètres + compte), sans exposer de données brutes.

### 4) Comment ça fonctionne, expliqué simplement
- **Agrégation pondérée** : $coef_{global} = \sum_k \frac{n_k}{\sum_j n_j} coef_k$, $intercept_{global} = \sum_k \frac{n_k}{\sum_j n_j} intercept_k$
- **Comptes inégaux** : gère correctement des hôpitaux avec différents nombres d'échantillons
- **Entrées restreintes** : seuls `hospital_id`, `coef`, `intercept`, `n_samples` acceptés. Rejette `X`, `y`, `meta`, historiques, etc.
- **Validations** : collections vides, IDs dupliqués, comptes négatifs/zéro totaux, NaN/Inf, formes/dimensions incompatibles, mises à jour malformées
- **Sécurité des copies** : jamais de mutation des updates clients, retourne des tableaux copiés indépendants
- **Auditabilité** : identités hôpitaux et comptes conservés, pas de données patients

### 5) Nouveaux concepts appris
- **FedAvg pondéré** : poids = taille de partition locale
- **Agrégation stricte** : interface minimale réduit surface de fuite
- **Ordre indépendant** : agrégation commutative

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels, ce qui reste non vérifié
**Tests focalisés `tests.test_fl_server`** : **13/13 OK**
- Agrégation pondérée basique, comptes inégaux, agrégation intercept, indépendance ordre, IDs dupliqués rejetés, collections vides, comptes invalides/zéro, NaN/Inf, dimensions incompatibles, rejet données brutes, pas de mutation, déterminisme, calcul manuel sur 3 hôpitaux

**Tests clients mis à jour** : toujours OK avec champ unique `n_samples`

**Suite complète** : **191/191 OK** (+13 nouveaux tests)

**Ce qui reste non vérifié** : orchestration multi-rounds, baseline centralisé, intégration bout-en-bout

### 9) Ce qu'il reste à faire
Micro-step 5 (si approuvé) : orchestration multi-rounds (clients démarrent chaque round depuis globaux identiques, agrégation, itérations)

**Limites connues** :
- **Simulation uniquement** : **Ordinary FedAvg ne fournit aucune garantie formelle de confidentialité, secure aggregation ou differential privacy**. Les mises à jour de modèle peuvent encore fuir de l'information sur les données locales.
- Agrégateur seul, pas d'orchestration
- Pas de mécanismes de confidentialité supplémentaires


## Étape 21 : Step 3.4 micro-step 5 - Orchestration multi-rounds FedAvg + baseline centralisé (2026-10-27)

### 1) Date et numéro d'étape
- Date : 2026-10-27
- Étape n°21

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `scripts/train_federated_sim.py` (orchestration multi-rounds + baseline centralisé)
- Création de `tests/test_fl_training.py` (9 tests focalisés)
- Correction serveur : `n_samples` doit être > 0 (chaque client), ajout test régression
- Mise à jour `ai_service/fl_client.py` unification champ unique `n_samples`
- Mise à jour tests clients/serveur
- Aucun fichier Step 3.3/API/dashboard/modifié

### 3) Pourquoi nous devions le faire
Orchestrer des rounds FedAvg avec réinitialisation globale identique à chaque round, et fournir un baseline centralisé dans un chemin explicitement séparé.

### 4) Comment ça fonctionne, expliqué simplement
- **FedAvg multi-rounds** : initialisation globale identique, chaque client reçoit mêmes paramètres globaux, s'entraîne localement, agrégation pondérée, nouveau global pour round suivant.
- **Réinitialisation par round** : tous clients partent des mêmes paramètres globaux à chaque round (vérifié).
- **Baseline centralisé** : utilise même `BinaryLogisticRegression` NumPy, mêmes features/conventions, données agrégées **uniquement** dans `run_centralized_baseline()` (chemin offline benchmark explicitement étiqueté). Jamais dans API serveur/client.
- **Hyperparams/seuils** : sélection sur train/val uniquement, test non utilisé
- **Pas de promesse d'amélioration** : comparaison uniquement, aucun revendication automatique
- **Pas de garantie** : échanges de paramètres peuvent fuir de l'information

### 5) Nouveaux concepts appris
- **Orchestration fédérée** : boucle serveur/clients avec agrégation
- **Séparation claire** : pooling centralisé restreint au benchmark uniquement

### 6) Erreurs rencontrées et causes réelles
Aucune erreur rencontrée

### 7) Comment nous les avons corrigées et pourquoi
N/A

### 8) Tests effectués, résultats réels
**Tests focalisés training** : 9/9 OK
**Tests serveur/clients mis à jour** : OK
**Suite complète** : **200/200 OK**

Vérifié: propagation multi-rounds, reset global par round, déterminisme, isolation splits, baseline avec données équivalentes, configurations malformées, stabilité numérique, pas de transfert données brutes.

### 9) Ce qu'il reste à faire
Micro-step 6 (si approuvé) : évaluation finale sur test held-out uniquement, rapport comparatif sans ajuster hyperparams sur test.

**Limites connues** :
- **Simulation uniquement** - aucune garantie formelle confidentialité/secure aggregation/differential privacy
- Orchestration basique
- Pas de rapport test final dans ce micro-step
- Baseline centralisé avec pooling uniquement dans chemin benchmark


## Étape 22 : Step 3.4 micro-step 6 - Évaluation finale fédéré vs centralisé (2026-10-27)

### 1) Date et numéro d'étape
- Date : 2026-10-27
- Étape n°22

### 2) Ce que nous avons fait et quels fichiers ont changé
- Création de `scripts/eval_federated.py` (évaluation finale held-out test)
- Création de `reports/fl_simulation.json` (résultats réels reproductibles)
- Tests existants: 200/200 OK, aucun test supprimé
- Serveur corrigé: `n_samples > 0` par client (micro-step 4 fix), clients unifiés à `n_samples` unique
- Aucun fichier Step 3.3/API/dashboard/modifié

### 3) Pourquoi nous devions le faire
Évaluer fédéré vs centralisé sur test held-out une seule fois, avec hyperparams choisis sur train/val uniquement.

### 4) Comment ça fonctionne, expliqué simplement
- **Orchestration**: 10 rounds FedAvg, 20 itérations locales, lr 0.01, même params globaux chaque round, agrégation pondérée
- **Baseline centralisé**: même `BinaryLogisticRegression` NumPy, mêmes features 18, pooling **uniquement** dans chemin benchmark explicite
- **Test once**: évaluation held-out test après configuration figée
- **Métriques**: précision/rappel/F1/matrice confusion par global et par hôpital
- **Analyse reporting_error**: pics isolés évalués séparément

### 5) Résultats réels (held-out test)
**Fédéré global**: TP=3, TN=1194, FP=10, FN=53, P=0.231, R=0.054, F1=0.087, acc=0.950, n=1260
**Centralisé global**: TP=3, TN=1192, FP=12, FN=53, P=0.200, R=0.054, F1=0.085, acc=0.948, n=1260

Apprentissage modeste (faible rappel) - comportement attendu avec modèle linéaire simple, peu de rounds/itérations. Fédéré légèrement meilleur que centralisé ici mais **aucune promesse** d'amélioration.

### 6) Limites et avertissements
- **Confidentialité**: ORDINARY FEDAVG HAS NO FORMAL PRIVACY GUARANTEE, NO SECURE AGGREGATION, NO DIFFERENTIAL PRIVACY
- **Données**: simulation synthétique uniquement
- **Déséquilibre**: BCE non pondéré, Sfax tout-négatif en entraînement local
- **Normalisation**: aucune transformation appliquée (pas de scaler ajusté)
- **Fenêtres corrélées**, petit nombre de simulations

### 7) Vérification
- Suite complète: 200/200 OK
- CSV restaurés (uniquement fins de ligne)
- Step 3.3 intact, API/dashboard inchangés

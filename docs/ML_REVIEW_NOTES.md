# Revue ML de MONITUS — 25 octobre 2026

## Cadre de ce travail

Branche : `feature/ml-detector`, à partir du commit `6dc5df7`, pour la PR no 1.
Cette note sert de journal pour ce cycle uniquement, selon l'exception autorisée
par l'utilisateur. `AGENTS.md`, `LEARNED.md`, `LEARNED_ML_BACKUP.md` et
`LEARNED_ORIGINAL_BACKUP.md` ne sont pas modifiés. La récupération d'encodage
reste un travail séparé. Aucun ajout à l'index Git, commit, push, merge ou
changement de la PR n'a été effectué.

Toutes les données sont des nombres agrégés inventés pour trois hôpitaux fictifs.
Aucune donnée patient, aucun secret et aucune connexion à Hedera ne sont utilisés.

## Problèmes constatés et corrections

- Avant ce travail, le générateur ML savait produire `reporting_error`, mais les
  configurations d'entraînement, de validation et de test ne choisissaient que
  `normal` ou `outbreak`. Les erreurs n'étaient donc pas réellement évaluées.
- `get_simulation_configs()` donne maintenant des listes explicites. Les anciens
  scénarios normaux et épidémiques sont conservés. Trois simulations d'erreur
  indépendantes sont ajoutées dans chaque groupe.
- Chaque erreur représente un signalement groupé ou une erreur de saisie sur une
  seule journée : hôpital tiré au sort, ajout de 15 à 120 cas fictifs, puis retour
  au niveau habituel. La date varie entre les indices 20 et 69 inclus. Le pic et
  les 20 jours suivants peuvent ainsi être évalués, sans être cachés par la phase
  d'attente initiale. Par exemple, la validation contient un pic de 38 cas à Sousse
  le 21 janvier. Ce sont des hypothèses simples, pas des distributions cliniques
  validées ni une couverture de tous les problèmes de signalement.
- Tous les jours de `reporting_error` ont la classe 0 : non-épidémie. Le marqueur
  du pic est réservé aux comptes et à l'évaluation ; il n'entre pas dans les
  variables du modèle. La classe 1 reste limitée aux 14 derniers jours de
  `outbreak`, pour les hôpitaux fictifs de Tunis et Sousse.
- `validate_simulation_splits()` refuse une graine répétée, même entre deux types
  de scénarios, ainsi que l'absence d'un des trois scénarios dans un groupe.
  Chaque simulation utilise son propre `random.Random(seed)`.
- `collect_data()` réinitialise l'historique pour chaque simulation et hôpital.
  L'entraînement commence maintenant à la 21e observation, comme l'inférence :
  20 observations précédentes et celle d'aujourd'hui. Avant, l'entraînement
  attendait inutilement une 22e observation. Pour 90 jours, on obtient 70 exemples
  par hôpital, donc 210 par simulation. La première date évaluée est le 21 janvier.
- Les 18 variables et leurs formules dans `ai_service/ml_features.py` restent
  inchangées. Les deux chemins appellent toujours la même fonction. Les tests
  comparent exactement chaque vecteur réellement collecté au vecteur d'inférence.
  Il s'agit de détection le jour même, pas de prévision d'une future épidémie.
- Le scaler est ajusté seulement sur l'entraînement. Le seuil est choisi seulement
  sur la validation, avec la même grille qu'avant. Aucun réglage n'a été effectué
  selon le résultat du test.
- Le rapport montre les comptes par scénario, les faux positifs sur les seuls
  jours de pic et les résultats globaux. Les chemins des fichiers sont relatifs
  au projet ; les versions Python et des principales bibliothèques sont dans les
  métadonnées. L'API et le tableau de bord ne sont pas raccordés au modèle ML.

## Simulations et classes après la phase d'attente

Chaque graine désigne une simulation entière de 90 jours pour les trois hôpitaux.
Il n'y a pas de partage aléatoire des journées entre groupes.

| Groupe | Graines normales | Graines outbreak | Graines reporting_error |
|---|---|---|---|
| Entraînement | 1001 | 1002, 1003, 1004, 1005 | 1006, 1007, 1008 |
| Validation | 2002 | 2001 | 2003, 2004, 2005 |
| Test | 3003 | 3001, 3002 | 3004, 3005, 3006 |

| Groupe | Simulations | Exemples | Classe 1 | Classe 0 | Exemples reporting_error | Pics évalués |
|---|---:|---:|---:|---:|---:|---:|
| Entraînement | 8 | 1680 | 112 | 1568 | 630 | 3 |
| Validation | 5 | 1050 | 28 | 1022 | 630 | 3 |
| Test | 6 | 1260 | 56 | 1204 | 630 | 3 |

Ces nombres sont calculés sur les exemples réellement fournis au modèle, pas sur
les lignes brutes. Les 630 exemples d'erreur de chaque groupe sont tous de classe 0.

## Résultats mesurés sur les simulations de test

Modèle : régression logistique, classes équilibrées, `random_state=42`.
Seuil choisi sur la validation : environ 0,65 ; F1 de validation : 0,933333.

| Mesure de test | Valeur |
|---|---:|
| Vrais négatifs | 1200 |
| Faux positifs | 4 |
| Faux négatifs | 1 |
| Vrais positifs | 55 |
| Précision | 0,932203 |
| Rappel | 0,982143 |
| F1 | 0,956522 |
| Taux de faux positifs parmi les négatifs | 0,3322 % |

**Limite importante : les trois pics de signalement du test sont tous classés à
tort comme épidémiques, soit 3 faux positifs sur 3 jours de pic.** Sur l'ensemble
des simulations `reporting_error`, on compte 4 faux positifs et 626 vrais négatifs
sur 630 exemples : un faux positif supplémentaire survient hors du jour du pic.
Le taux de faux positifs de ce scénario est 0,6349 %, mais cette moyenne masque
le mauvais résultat sur les pics eux-mêmes. Le modèle ne peut donc pas être
présenté comme un filtre fiable des erreurs de signalement.

Les scénarios normaux ont 0 faux positif sur 210 exemples. Les scénarios
épidémiques donnent 55 vrais positifs, 1 faux négatif et 364 vrais négatifs.
Les quatre événements hospitaliers épidémiques sont détectés ; les délais sont
0, 0, 0 et 1 jour. Aucun de ces événements n'est entièrement manqué.

Pour un scénario sans classe positive, précision, rappel et F1 sont enregistrés
à 0 avec `zero_division=0`. Ce n'est pas une estimation du rappel clinique : il
faut lire les comptes et le taux de faux positifs.

## Vérifications réellement exécutées

Environnement existant, sans installation : Windows, Python 3.13.5,
scikit-learn 1.9.1, NumPy 2.5.4, SciPy 1.18.1, joblib 1.6.0.

1. `venv\Scripts\python.exe -m unittest tests.test_ml_training_pipeline.TestMLTrainingPipeline -v`
   : 13 tests réussis avant le réentraînement.
2. `venv\Scripts\python.exe -m scripts.train_ml_detector` : entraînement terminé,
   modèle, scaler, métadonnées et rapport régénérés.
3. `venv\Scripts\python.exe -m unittest discover -s tests -v` : **115 tests
   réussis**, dont 17 nouveaux tests dans `tests/test_ml_training_pipeline.py`.
   Les vérifications couvrent les vrais exemples d'erreur, la séparation des
   simulations, le rejet des graines répétées, les 21 observations, les 18
   variables, l'absence d'effet des observations futures sur les premiers
   exemples, la séparation des historiques et l'exclusion du marqueur du pic.
   Les fichiers sauvegardés sont aussi vérifiés : scaler ajusté aux seuls exemples
   d'entraînement, seuil de validation, comptes et métriques recalculés depuis
   les prédictions du modèle sauvegardé.
4. Un second entraînement avec la même configuration a produit les quatre fichiers
   générés identiques octet par octet, vérifiés par SHA-256. Cela vérifie la
   répétabilité locale, pas la compatibilité de toutes les versions de bibliothèques.

## Erreurs et avertissements rencontrés

- Aucun échec dans les tests ou les entraînements.
- La suite émet un avertissement Starlette : l'utilisation de `httpx` avec
  `starlette.testclient` est dépréciée. Aucune dépendance n'a été modifiée ici.
- Le contrôle global `git diff --check` échoue à cause d'un espace final déjà
  présent dans la modification locale protégée de `LEARNED.md`, ligne 212.
  Ce fichier n'a pas été corrigé. Git signale aussi sa conversion habituelle
  LF/CRLF pour certains fichiers ; ce n'est pas un échec des tests.
- Une commande d'inspection des pics avec une chaîne Python dans PowerShell a
  échoué à cause des guillemets (`SyntaxError`). La commande corrigée a réussi ;
  ce problème n'a pas affecté les données ni l'entraînement.

## Points à garder ouverts pour FIRAS

- Les résultats ne sont ni parfaits, ni une validation clinique. Le nombre de
  simulations est faible ; les fenêtres se chevauchent et sont corrélées.
- Les groupes ont des graines différentes mais viennent de la même famille de
  générateurs simples. Les anciens scénarios de test avaient déjà été consultés
  lors du cycle de revue précédent : ce n'est pas une validation externe neuve.
- Les erreurs simulées ne couvrent pas les retards sur plusieurs jours, les
  données manquantes ou un mélange d'épidémie et d'erreur de signalement.
- Une hausse modérée peut ressembler à un début d'épidémie le jour même. Toute
  amélioration de ce comportement demande un travail distinct, sans ajuster le
  modèle sur ces résultats de test. Aucun diagnostic confirmé n'est produit.
- FIRAS doit revoir ces changements et vérifier les tests de façon indépendante.
  La description de la PR et le plan général, déjà anciens, n'ont pas été modifiés.

## Fichiers de ce cycle

- `scripts/train_ml_detector.py` : scénarios, collecte, contrôles et rapport.
- `ai_service/ml_detector.py` : clarification de la documentation seulement.
- `tests/test_ml_training_pipeline.py` : 17 nouveaux tests de régression.
- `models/ml_outbreak_model.joblib`, `models/ml_outbreak_scaler.joblib`,
  `models/ml_outbreak_meta.json` : fichiers régénérés.
- `reports/ml_evaluation.json` : mesures et limites régénérées.
- `docs/ML_REVIEW_NOTES.md` : ce journal en français.

## Contrôle final

Après le second entraînement, la suite complète a été relancée avec
`venv\Scripts\python.exe -m unittest discover -s tests -q` : 115 tests réussis.
Le contrôle `git diff --check` limité aux fichiers suivis de ce cycle réussit ;
un contrôle Python des espaces finaux sur les fichiers texte de ce cycle,
y compris le nouveau test et cette note, ne trouve aucun problème.
Les empreintes SHA-256 de `AGENTS.md` et des trois fichiers protégés `LEARNED`
sont identiques avant et après le travail. Leur état Git initial est conservé.

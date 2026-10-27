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

## Adaptateur régional ML optionnel — 27 octobre 2026

Cette section décrit un nouveau cycle, après le commit `102679c`. Les sections
précédentes restent l'historique du travail du 25 octobre. L'exception de journal
est à nouveau autorisée pour cette tâche : aucune modification de `LEARNED.md`,
de ses deux sauvegardes ni de `AGENTS.md`.

### Choix d'architecture après inspection

`MLDetector.predict_proba()` produit une probabilité sur un historique ; il ne
fournit pas les dates ou les identifiants attendus par le détecteur régional.
`RegionalDetector.corroborate()` peut réutiliser le champ booléen `anomaly_flag`
sans avoir besoin d'un score MAD pour compter les hôpitaux. `AlertVerifier.verify()`
peut ensuite appliquer sa règle de persistance sur ces rapports.

Le nouveau `ai_service/ml_regional_adapter.py` ajoute seulement
`MLRegionalAssessmentAdapter.assess(observations)`. Il n'est appelé ni par l'API,
ni par le tableau de bord, ni par le chemin statistique existant. Les modules
`MLDetector`, `RegionalDetector` et `AlertVerifier` ne sont pas modifiés.

- Le modèle sauvegardé est chargé par défaut. Son seuil de validation, environ
  0,65, est lu dans ses métadonnées. Il n'y a pas de réentraînement, de modification
  des 18 variables, de nouveau seuil ou de réglage sur les cas de test.
- Le quorum reste fixé à deux hôpitaux distincts le même jour. La vérification
  réutilise deux jours régionaux dans une fenêtre de trois jours calendaires.
  L'adaptateur ne propose pas de quorum configurable, car le vérificateur existant
  utilise lui-même une limite de deux sites pour sa classification.
- Chaque ligne doit contenir `sim_id`, `hospital_id`, `date` au format
  `YYYY-MM-DD`, et `respiratory_cases`, un entier non négatif. `city` est facultatif.
  Les identifiants doivent être stables et représenter des hôpitaux fictifs.
  Les champs de vérité terrain éventuels ne servent pas à prédire.
- Les lignes sont triées par date pour chaque hôpital et chaque simulation. Aucun
  historique ou jour régional n'est partagé entre simulations, ni entre appels.
  Une ligne sans identifiant de simulation est refusée au lieu d'être mélangée
  silencieusement avec une autre simulation.
- Une journée répétée avec le même nombre de cas et la même ville est ignorée
  après sa première occurrence, avec un avertissement dans `input_warnings`.
  Elle n'avance pas la fenêtre et ne compte pas comme un second hôpital. Si les
  valeurs de cette journée se contredisent, l'appel échoue avec `ValueError`.
- Pour ne pas appliquer un modèle entraîné sur des journées régulières à un
  historique irrégulier, un trou calendaire remet à zéro la fenêtre de cet hôpital
  et crée un avertissement. Il faut de nouveau 21 observations quotidiennes
  consécutives, dont aujourd'hui, pour obtenir une prédiction. Aucun zéro n'est
  ajouté pour combler le trou. Ce choix prudent peut retarder une détection.

### Sorties locales et régionales séparées

Le résultat est un dictionnaire par `sim_id`. Chaque simulation contient :

- `local_signals` : les observations réellement évaluées, positives ou négatives,
  regroupées par hôpital. Chaque signal garde `source="ml"`,
  `predicted_probability`, `threshold`, sa date et son hôpital. `anomaly_flag`
  signifie seulement une décision locale du modèle, pas une épidémie vérifiée.
- `regional_reports` : les rapports produits par le détecteur régional, y compris
  les anomalies isolées. `regional_signals` ne contient que les rapports où le
  quorum du jour est atteint.
- `assessments` : les statuts du vérificateur existant. Un hôpital seul reste
  `ISOLATED_ANOMALY`, même s'il est positif plusieurs jours. Deux sites un seul
  jour donnent `REGIONAL_SIGNAL_UNCONFIRMED`. Une persistance suffisante donne
  `REGIONAL_SIGNAL_REQUIRES_REVIEW`, jamais une confirmation clinique.
- `input_warnings` : les doublons identiques ignorés et les remises à zéro après
  un trou de dates. Les jours sans assez d'historique n'ont pas de prédiction.
  L'absence de rapport ne doit donc pas être présentée comme une preuve de normalité.

Le formateur régional existant ajoute des valeurs statistiques par défaut lorsque
ces champs sont absents. L'adaptateur remplace ces détails par les vrais signaux
ML avant la vérification et retire `individual_anomaly_scores`. Il ne publie pas
de faux `mad`, `baseline_median` ou `anomaly_score`, et ne convertit jamais une
probabilité en score statistique. L'avertissement statistique « score supérieur
à 20 » n'est donc pas appliqué au ML. Les avertissements existants du vérificateur
ne sont pas des vetos automatiques ; cela n'est pas changé ici.

Les sorties locales, régionales et de vérification indiquent
`confirmed_outbreak=False`. Le niveau régional exige une revue humaine, pas une
conclusion médicale.

Exemple d'appel sur des comptes entièrement inventés :

```python
from datetime import date, timedelta
from ai_service.ml_regional_adapter import MLRegionalAssessmentAdapter

rows = [
    {"sim_id": "demo", "hospital_id": "HOSP_FICTIF_A",
     "date": (date(2024, 1, 1) + timedelta(days=i)).isoformat(),
     "respiratory_cases": 100 if i == 20 else 10}
    for i in range(21)
]
result = MLRegionalAssessmentAdapter().assess(rows)["demo"]
# Examiner séparément local_signals, regional_signals et assessments.
```

### Vérifications et résultats réellement observés

Nouveaux fichiers : `ai_service/ml_regional_adapter.py` et
`tests/test_ml_regional_adapter.py`. Le seul fichier existant modifié pour ce
cycle est ce journal. Aucun paquet n'a été installé.

- `venv\Scripts\python.exe -B -m unittest tests.test_ml_regional_adapter -v` :
  **23 tests réussis**.
- `venv\Scripts\python.exe -B -m unittest discover -s tests -v` :
  **138 tests réussis**, soit les 115 précédents et les 23 nouveaux.
- Les cas d'architecture utilisent des probabilités injectées et des observations
  fabriquées à la main, pas les trois pics de test pour choisir une règle. Ils
  couvrent un pic isolé, les dates différentes, le quorum du même jour, les deux
  jours sur trois et la sortie de fenêtre, les doublons, les trous de dates,
  l'indépendance des données futures, l'isolation des simulations et des appels,
  les champs de provenance et les entrées invalides.
- Un test utilise aussi le vrai modèle sauvegardé sur une série fabriquée à la
  main : les probabilités et décisions sont identiques à celles de `MLDetector`
  appelé directement, et les empreintes des quatre fichiers modèle/rapport sont
  inchangées après l'appel. Les changements de seuil dans les autres tests portent
  seulement sur le faux détecteur de test, jamais sur les fichiers sauvegardés.

Après ces tests, une inférence descriptive avec les règles déjà fixées a été
exécutée en mémoire sur les six anciennes simulations de test. Aucun fichier de
modèle ou rapport n'a été régénéré et aucun ajustement n'a suivi ces résultats.

| Simulation | Scénario | Décisions locales positives | Jours de signal régional | Jours nécessitant une revue |
|---|---|---:|---:|---:|
| sim_3001 | outbreak | 28 | 14 | 13 |
| sim_3002 | outbreak | 27 | 13 | 12 |
| sim_3003 | normal | 0 | 0 | 0 |
| sim_3004 | reporting_error | 1 | 0 | 0 |
| sim_3005 | reporting_error | 2 | 0 | 0 |
| sim_3006 | reporting_error | 1 | 0 | 0 |

**Les 3 pics de signalement sur 3 restent des faux positifs du modèle ML au
niveau hospitalier.** Il y a toujours quatre faux positifs locaux dans ces
simulations d'erreur, dont un hors du jour du pic. Avec l'adaptateur, ces décisions
restent des anomalies isolées : zéro jour de signal régional et zéro jour de
revue régionale dans ces trois simulations. Cela vérifie la séparation des
niveaux d'alerte ; cela ne répare pas le classificateur et ne prouve pas qu'il
reconnaît les erreurs de signalement.

Ces simulations ont déjà été examinées dans les cycles précédents. Les chiffres
ci-dessus ne sont pas une nouvelle validation indépendante. Une future évaluation
doit réserver à l'avance d'autres simulations et garder le modèle, le seuil et
les règles fixes. Des erreurs simultanées ou répétées dans plusieurs hôpitaux
pourraient satisfaire quorum et persistance ; aucune promesse de suppression de
tous les faux signaux régionaux n'est faite.

Aucune erreur rencontrée pendant l'implémentation, les tests ou cette inférence.
La suite complète émet toujours l'avertissement Starlette sur `httpx`, sans échec.
La reproductibilité des données CSV est vérifiée par la suite existante ; ce
test réécrit les CSV synthétiques avec leur contenu reproductible habituel, sans
entraîner le modèle ML. Aucun changement de Git n'est autorisé pour ce cycle
avant la revue de l'utilisateur : aucun ajout à l'index, commit, push ou merge.

Contrôle final : les SHA-256 des quatre fichiers protégés, des trois fichiers
de modèle, du rapport ML et du script d'entraînement sont identiques à ceux
relevés avant cette tâche. Aucun changement des chemins statistique, API ou
tableau de bord n'apparaît dans Git. L'index est vide. Le contrôle des espaces
finaux réussit sur les deux nouveaux fichiers et cette note ; `git diff --check`
limité à cette note réussit également, avec seulement l'avis habituel LF/CRLF.

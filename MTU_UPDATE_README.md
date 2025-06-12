# Mise à jour : Ajout des statistiques MTU (Mobile Tractor Unit)

## Vue d'ensemble

Un nouveau script `mtu_ranking_generator.py` a été créé pour générer des rapports dédiés uniquement aux statistiques des MTU (Mobile Tractor Unit) perdus pour la corporation Goat to Go. Ce script est séparé du rapport Ishtar existant pour maintenir deux classements distincts.

## Changements principaux

### 1. Nouveau fichier : `mtu_ranking_generator.py`

Ce fichier est une version adaptée de `ishtar_ranking_generator.py` qui se concentre uniquement sur les MTU :

- **Requêtes SQL modifiées** : Les requêtes recherchent uniquement `s.ship_name = 'Mobile Tractor Unit'`
- **Fonctions adaptées** :
  - `get_mtu_losses_30_days()` : Récupère les pertes de MTU des 30 derniers jours
  - `get_mtu_losses_all_time()` : Récupère toutes les pertes de MTU
  - `get_mtu_losses_by_month()` : Récupère les pertes de MTU par mois

### 2. Interface HTML dédiée aux MTU

Le rapport HTML généré inclut :

- **Statistiques globales MTU** :
  - Total MTU perdus
  - Valeur totale perdue
  - Nombre de joueurs concernés

- **Sections de classement** :
  - Top 10 MTU - 30 derniers jours
  - Top 10 MTU - All time
  - Évolution mensuelle des pertes

- **Graphiques** : Graphiques Chart.js avec couleur bleue (rgba(0, 180, 255)) pour distinguer des Ishtars

### 3. Scripts séparés pour chaque type

Deux scripts distincts sont maintenant disponibles :
- `ishtar_ranking_generator.py` : Pour les statistiques des Ishtars (existant)
- `mtu_ranking_generator.py` : Pour les statistiques des MTU (nouveau)

Chaque script a son propre script shell d'exécution :
- `run_ishtar_ranking.sh` : Pour générer le rapport Ishtar
- `run_mtu_ranking.sh` : Pour générer le rapport MTU

## Utilisation

Pour générer le rapport MTU :

```bash
python mtu_ranking_generator.py
```

Le rapport sera généré dans : `html/mtu_ranking.html`

Pour générer le rapport Ishtar (existant) :

```bash
python ishtar_ranking_generator.py
```

Le rapport sera généré dans : `html/ishtar_ranking.html`

Sur le Raspberry Pi, utilisez les scripts shell :

```bash
# Pour le rapport MTU
./run_mtu_ranking.sh

# Pour le rapport Ishtar
./run_ishtar_ranking.sh
```

## Structure de la base de données attendue

Le script s'attend à ce que la base de données contienne :
- Une table `ships` avec une colonne `ship_name`
- Des entrées pour `'Ishtar'` et `'Mobile Tractor Unit'` dans `ship_name`
- Les autres tables et relations restent identiques (killmails, pilots, corporations, etc.)

## Notes importantes

1. **Deux rapports séparés** : Les statistiques Ishtar et MTU sont maintenant dans deux rapports distincts
2. **Compatibilité** : Les deux scripts utilisent les mêmes variables d'environnement et la même structure de base de données
3. **Performance** : Les requêtes sont optimisées avec des index appropriés sur `ship_name` et `corporation_name`
4. **Fichiers de sortie** : 
   - Ishtar : `html/ishtar_ranking.html`
   - MTU : `html/mtu_ranking.html`

## Exemple de sortie

Le rapport MTU affichera :

```
🎯 Classement des MTU Perdus - Goat to Go 🎯

[Statistiques globales]
- Total MTU Perdus : 127
- Valeur Totale : 8.3B ISK
- Joueurs Concernés : 28

[Graphiques et tableaux de classement]
```

Le rapport Ishtar affichera (inchangé) :

```
🚀 Classement des Ishtars Perdus - Goat to Go 🚀

[Statistiques globales]
- Total Ishtars Perdus : 245
- Valeur Totale : 45.2B ISK
- Joueurs Concernés : 32

[Graphiques et tableaux de classement]
```

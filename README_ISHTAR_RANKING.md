# Système de Classement des Ishtars Perdus - Goat to Go

## Description

Ce système génère un classement des joueurs de la corporation "Goat to Go" basé sur leurs pertes d'Ishtars (un vaisseau dans EVE Online). La particularité de ce système est qu'il agrège automatiquement les pertes de tous les personnages alternatifs (alts) d'un même joueur pour créer un classement par joueur plutôt que par personnage.

## Fonctionnalités

- **Classement par joueur** : Agrégation automatique de tous les personnages alternatifs
- **Classement 30 jours** : Top 10 des joueurs ayant perdu le plus d'Ishtars sur les 30 derniers jours
- **Classement All-Time** : Top 10 historique depuis le début des enregistrements
- **Évolution mensuelle** : Graphique montrant l'évolution des pertes mois par mois pour le top 5
- **Statistiques globales** : Total des pertes, valeur totale perdue, nombre de joueurs concernés
- **Interface web moderne** : Design sombre avec animations et graphiques interactifs

## Installation

### Prérequis

- Python 3.8+
- PostgreSQL avec la base de données EVE killmails configurée
- Environnement virtuel Python (recommandé)

### Configuration

1. Copier le fichier `.env.example` vers `.env` et configurer les paramètres de base de données :
   ```bash
   cp .env.example .env
   ```

2. Éditer `.env` avec vos paramètres :
   ```
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=your_database_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

### Installation des dépendances

```bash
pip install psycopg2-binary python-dotenv
```

## Utilisation

### Test local

Pour tester le générateur localement :

```bash
./test_ishtar_ranking.sh
```

Ce script :
- Crée un environnement virtuel si nécessaire
- Installe les dépendances
- Génère le rapport dans `html/ishtar_ranking_test.html`
- Propose d'ouvrir le rapport dans votre navigateur (sur macOS)

### Exécution en production

Pour exécuter en production avec déploiement automatique :

```bash
./scripts/run_ishtar_ranking.sh
```

Ce script :
- Active l'environnement virtuel du serveur
- Génère le rapport
- Met à jour l'index principal
- Copie les fichiers vers le répertoire web

### Exécution manuelle

```bash
python ishtar_ranking_generator.py --output html/ishtar_ranking.html
```

## Structure des données des joueurs

Les associations joueur/personnages sont définies dans le script `ishtar_ranking_generator.py` dans la variable `PLAYER_DATA`. Format :

```
player_id,main_character,alt1,alt2,alt3...
```

Exemple :
```
2113160540,Boutdechoux Malhorne,Alija2,BankBoutdechoux01,Bdcbdcbdc malhmalhmalh...
```

## Mise à jour des associations joueur/personnages

Pour ajouter ou modifier les associations :

1. Éditer la variable `PLAYER_DATA` dans `ishtar_ranking_generator.py`
2. Ajouter une nouvelle ligne avec le format : `player_id,personnage_principal,alt1,alt2...`
3. Les noms de personnages doivent correspondre exactement à ceux dans la base de données

## Structure de la base de données

Le script utilise les tables suivantes :
- `killmails` : Les killmails avec dates, valeurs, etc.
- `pilots` : Les informations des pilotes
- `ships` : Les informations des vaisseaux
- `ship_types` : Les types de vaisseaux (pour filtrer les Ishtars)
- `corporations` : Les corporations (pour filtrer Goat to Go)
- `systems` : Les systèmes solaires

## Personnalisation

### Modifier la corporation cible

Dans les requêtes SQL, remplacer :
```sql
WHERE LOWER(c.corporation_name) = 'goat to go'
```

### Modifier le type de vaisseau

Dans les requêtes SQL, remplacer :
```sql
AND LOWER(st.type_name) = 'ishtar'
```

### Modifier les couleurs du thème

Éditer les variables CSS dans la fonction `generate_html()` :
```css
--primary: #1b1b1b;
--secondary: #252525;
--accent: #00b4ff;
--danger: #ff4444;
```

## Automatisation

Pour une exécution automatique régulière, ajouter au crontab :

```bash
# Mise à jour quotidienne à 3h du matin
0 3 * * * /scripts/eve_killmails/scripts/run_ishtar_ranking.sh
```

## Dépannage

### Erreur de connexion à la base de données

- Vérifier les paramètres dans `.env`
- Vérifier que PostgreSQL est en cours d'exécution
- Vérifier les permissions de l'utilisateur de base de données

### Personnages non reconnus

- Vérifier l'orthographe exacte des noms de personnages
- Les comparaisons sont insensibles à la casse
- Vérifier que le personnage existe dans la table `pilots`

### Pas de données affichées

- Vérifier que la corporation "Goat to Go" existe dans la base
- Vérifier que des Ishtars ont été perdus par la corporation
- Vérifier les dates de filtrage (30 jours, etc.)

## Support

Pour toute question ou problème, vérifier les logs dans :
- `/scripts/eve_killmails/log/run_ishtar_ranking.log`

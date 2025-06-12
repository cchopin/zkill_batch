#!/usr/bin/env python3
"""
Générateur de rapport de classement des Ishtars perdus par joueur pour Goat to Go
"""

import psycopg2
from psycopg2.extras import DictCursor
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse
import logging
import calendar

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Charger les variables d'environnement
load_dotenv()

# Données des joueurs et leurs personnages alternatifs
PLAYER_DATA = """
2113160540,Boutdechoux Malhorne,Alija2,BankBoutdechoux01,Bdcbdcbdc malhmalhmalh,Bdcmindeuh Boutdechoux,BoutdeARITTANT,BoutdeBABIRMOULT,Boutdechouxbdc Boutdechoux,BoutdechouxFittingTeam,BoutdeChouxSRPTeam,BoutdeFAURULLE,BoutdeGhoul,BoutdeHARE,BoutdeHELUENE,BoutdeKnockKnock,BoutdeMolok,BoutdeOGARIA,BoutdeORUSE,BoutdeTitan,GauloisGhoul,Good Name WhatGoodName,Hauler 08'15,It's Cool name,Lumiere BDM,Lumiere is up,Malhorne Boutdechoux,Malhorne Nakrar,MalhorneGhoul
94897828,Jimmy Jonesn,Aron Shikkoken,Balthazar Jonesn,Emmanuel Jonesn,Gavyn Jonesn,Ghoul Jonesn,mickael Hemanseh,MPO Endashi,PDG Jonesn,ques Eginald
843840307,TheVirus32,Blue Macaw,Creamy Baguette,Ethan Corpseller,Gharax,Jita Discounter,John Corpmaker,Moustache Cuir,Petite Blonde,Straight White Male
2114278199,Xaintailles Orland,Biagino Tivianne,Charles Saunders,CollOne Tailles,CollThree Tailles,CollTwo Tailles,Dana Moses,GhostTailles Pirkibo,Karen MacKarFace,Manda Miller,ProbOne Tailles,ProbThree Tailles,ProbTwo Tailles,Robert Donald,SalvageTailles,Xaintaile Orland,Xaintailes Orland,Xaintaille ORland,Xaintailles 2,Xaintailles 3,XaintExtract1,XaintExtract2,XaintExtract3,XaintExtract4,XaintExtract5,XaintExtract6,Xantailes Orland,Xantailles Orland,Yashami Eto,Zug Zog
819983552,Alderic,Anryu Tenha,AnryuTenha,BimBam Boum,Daniel Jackssonn,Dominiq Toretto,Fast AndFurious,Helloo There,Jacke O'neil,Jerome Kervviel,market1,Nimitz DeVir,Pif PafPouf,Sammantha Carterr,The Worm Director
758966296,Rafouil,Alexia Fly,Alice Slayer's,Atani Eginald,AtomicX Snows,Aur0ra SnOw,billwares,Billybleu,BiToQ,Bloody Jessy,Chuck M0rris,Elena Berk0va,Ethan slayer's,Extasie,HemoGLobyne,Hitaka Tsuruomo,Homere Dalor,Jessica Tanko,Johny Malax,Kira Slone,Kitty Malax,Lexa Wax,Lexy Dee,Lilly Slone,Little LiLy,NaanWich,Penny Slone,SunSilke,TaPatate,Torry Black,Tsuki Furtz,Wakey-Wakey Intakeyyy,Yumi Modjo
1111922349,Fourassa,Ackbard,Akolia,Alex Udinov,Bubic wallet,Charles Ponzzi,ELNNAN,Fifi F,Fragile Express,grabite,Leeloo Fragile,Loulou F,Mirax Terik Horn,Moutonador,Riri F,Sam Express,Sebulba Boonta,Tirlis,Ventry Clint,yolo Donier,Zyoceane
97126277,Brice GOAZIOU,Anderson Sasen,azerty35120,Brice De-Nice,Dol iPrane,Icaricio,Icaricio35120,Jaima Onzo,Ladie Chu,Ladie Shi,Ladie35120,Lili Andersone,Lili Shuu,Marchal Nardieu,Microsoff35120,Microsoft22100,Ninine Afuran,Oralen Kusoni,Samual Ventreaux,Smyth35120,Titi Anderson,Torben wallace,Yann Saraki,Zin Chaa,Zin Chuu
2114303641,Yeka DelaVega,Inf Ected,Jannsen,JeanEude,Jo Rook,Marin d'eau-douce,Mini DelaVega,Moule AGaufres,Paul DelaVega,Pick First,Tonerre DeBrest,Yeh Ka
1337944581,Arthorondor,Aidan Aihaken,Aidan Cadelanne,Bryanna Vanyar,Cudolan Faricadie,Cudolan Maricadie,Diandrha,Ephraelle,Euphratii Princeps,Filthia Stalker,Grumbledelver Glopgrowl,NotAMiningAlt01,NotAMiningAlt02,NotAMiningAlt03,Nycodan Erkkinen,Rinilan,Rusty Mcshellface,Surref Magnus,Ynocan Adoudel,Ynocan Aubaris,Ynocan Haul,Ynocan Utrigas
95124132,Christopher Loclanne,Elizabeth Vanburren,Erika Dickens,Jayra Gengod,Lou Pacht-Feng,Lucy Otichoda,Lyzy,Martine Houssa,Menesa Arody,Renay Lataupe,Shania Accurate
95043604,Tylie Smouk,thanaiss,thanoune,Tyloune,Tyty Ghost
2114383092,Destro Rage,Antora Yoe Rotsuda,Bella D,Black Betty II,Dai Tolan,Debby Rhodan,Diane Rhodan,Eliza Rage,Erika VanProut,Eva Stormz,Gre na Deen,Jacks Dalton,Lady Ghost,Lauri Dalton,Laurie Dalton,Lauris Dalton,Perry Rhodaan,Soeur Amelia,Tania Lan,TheGhouls,Xfury
1108053093,Dal Ius,Amalthea Ius,Dal Chicas,Dal Ia,Dal Skord,Neve Skord,Sapete Oku
2114342174,Nado Tsutola,Caldari Mister Clean,Gachimuchi Fan Girl,Gousoviba Hamabu,Hut Mabata,Kaarina Hakaari-Nara,Nado's Standing 001,Nado's Standing 002,Nado's Standing 003,Nehrnah Goda Avada,Tananola Aurilen,Veinalen Inkura
2117243405,Tely Merlyn,Ahtaa Merlyn,Andromedd,Antaken Uiski Hakoke,Daia Merlyn,Elfy Omarama,escroc me,Gory Merlyn,Harkari Mika,Maw of Hror,Sorin Merlyn,Tely 2012,Telykin,Telykin Merlyn
2121438459,Oli Grys,Bao Grys,Cystas Gry,Gravik Yra,Huyn Gry,Jesappelle Groot,Kyn Grys,Landwen Gry,Lyrliana,Mardwen Gry,Meirana Gry,Old Gry,Sarinna Gry
2117559173,Heiidall,Ghoudall,Haiidall,Haiidall2,Haiidall3,Haydall,Heii-Dall,Heiidall2,Heiidall2012,Heiidall3,HeiidallGhost,Heydall,Maodall,Neydall,Neydall2,Neydall3,raztout
2112057571,Sidius Oramara,byiouh Oramara,Kelop Artrald,MarrowDelver,NOTSidius Oramara
755936554,thoaupe,Aergie,Scheikline
1986402935,Haykura,Deathbrace,Juanito Elmeccano,Katsigi Hajh,Okolen Shihari
90410057,Alkor Denozor,Aklhor Denozor,Alkooor Denozor,alkor denozooor,alkor denozoor,Alkor Ghostozor,Alkor Twelvozor,Foutaka Ghoule,Haulator,Haulatormm,Kanithos Pahineh
1381224869,Eocia,Abrum Kreone,Anza Blast,Caporal Wasabi,Gearman Dude,Hesse Fair,Inazuma Reiki,Irin Payne,Remember Bagdad,Sister Tanga,Trashscrub
2113669599,Drasaerys Zyrh'Taragh,Basabran Adban Jaynara,Dee Antollare,Hirmaken Yamon Tsukaya,Kyskasakka Nu Yotosala,Nana Asanari,Pikken Rotta Tsuruomo,Puo Ihtoh Hita,Shintunola Heleneto,Ushaga Sugai Tsuruomo
2112857406,Dadas Aideron,Benjamin James Dover,Dadas Eginald,Dadas Oramara,Darja Fehrnah,David Helento,Henrik Eto,Mallard Ellecon
94498456,Lexx Starlighter,Hyacynte,Laurent Starlighter,Leone Starlighter,Lilou Starlighter,Luke Starlighter,Luzog Starlighter,Skills Plans Master
93810547,Alf Life,Alf Lightning,Alf Mad,Criminal Khurelem,Ever Moist,Gar Ghouls,Hell Demonia,Isa Freespace,Jvan DesBeignets,Jvan Deschurros,Jvan DesHotDog,Orggeror Graal,Sa Farm 1,Svetlana TouCauva
170744005,Garek,Alex jmp,Alex RnD,chilpill1,Fremmettitgur Huren,Imalala Panala,JumperA,JumperB,JumperD,JumperE,JumperF,jumperG,jumperh,Jumperi,Koimota Kuoto Isayeki,PanSens,Pearuluten Andi Gengod,psachilad,Rausneck,Rinteras Kasenumi,TradeRaven,xcannibalx
93430460,baboir subliminable,bab2012,babghoul,boibar subliminable,boibare,boibare subliminable,demetria Echerie,gloglote,gloglotte subliminable,Karhinala babghost,no futur,stickbomba subliminable
90147703,jayssi,Arpasen Okaski,Ghoulyz,Miss Peny,MissPenny,Oshirai,Spoky2012
2120015375,Alderik Dunier,Anttiken Kusoni,Childerik Dunier
663344901,Shikaa,Bestang Omaristos,Matri Ochka,Sandoll,Spectre Solide,Tabu Task
1309519361,Florban,2012 Florban,Dar Sarkan,Dark Nox Omega,Florban Wood,Gloombrewer,Goatkeeper,Mangeur d'enfant,MarrowKeeper,Mirabelle black,Siphra
2119315363,Darius la crevette,Darius Le Fantome
945902293,Gaetaneos,Aude Vessel,Brutuna,Caldamite,Dark Father666,GaetaGhoul,Groscon,Laurie Fice,Lilli Samur,Rheinmetal,Saude Omie,Sheila Lutfinal
1407146097,Frankarn Khain,Barbak Khain,Carla khain,Coolshen Khain,Frankarn,Frankarn Khaim,himi Khain,himik0chan,Lou Khain,Mad-Max Khain,Nathrack Khain,Sabrina Khain,shockcrown,Zoe khain
796468546,sediph,Alaoutiken Akia Saraki,Allexia,Gufrasa Stied Skir,Ondeukar Tvas Adestur
2123204299,Kintoras Uta,Kintoghost,Kintoleplusbeau,Kintoras CEO,kintorasx002,Mudsplitter
1772100435,Skouaire,Bar Warlord,Esoteric Warlord,Kara the Navigator,Major Wayde,Marko the Mechanic,Sraaz,Synthetic Warlord,Virtus the Patroller
2119923650,Gred Globerman,Ghost-42,zeus dieux
2116818735,Madarano Dred,Mada2,Marie DRED,Nikola-pred,Tomakuma
95960633,Sarge372,Akmate Terona,Almin Huren,Anatairos Naari,Boloss Baboli,Furena Kashuken,Glo Boulga Illat,Michel Pornaut,Otanida Isimazu,Rastafairai Dj
2120421404,kinyo 2,Kinyo FR,kinyo ghost
"""


class DatabaseConnection:
    """Gestion de la connexion à la base de données"""
    
    def __init__(self):
        self.conn = None
        self.cur = None
        self._conn_params = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }
    
    def __enter__(self):
        self.conn = psycopg2.connect(**self._conn_params)
        self.cur = self.conn.cursor(cursor_factory=DictCursor)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query, params=None):
        try:
            self.cur.execute(query, params)
            return self.cur.fetchall()
        except Exception as e:
            logging.error(f"Erreur lors de l'exécution de la requête: {e}")
            raise


def parse_player_data():
    """Parse les données des joueurs et retourne un dictionnaire character -> player_id"""
    character_to_player = {}
    player_info = {}
    
    for line in PLAYER_DATA.strip().split('\n'):
        parts = line.strip().split(',')
        if len(parts) >= 2:
            player_id = parts[0]
            characters = [char.strip() for char in parts[1:]]
            main_character = characters[0]
            
            player_info[player_id] = {
                'main_character': main_character,
                'all_characters': characters
            }
            
            for character in characters:
                character_to_player[character.lower()] = player_id
    
    return character_to_player, player_info


def get_ishtar_losses_by_month(db, months=12):
    """Récupère les pertes d'Ishtars par mois (12 derniers mois)"""
    query = """
    SELECT 
        TO_CHAR(k.kill_datetime, 'YYYY-MM') as mois,
        p.pilot_name,
        COUNT(*) as ishtars_perdus,
        SUM(k.value) as valeur_totale_perdue
    FROM killmails k
    JOIN pilots p ON k.pilot_id = p.pilot_id
    JOIN ships s ON k.ship_id = s.ship_id
    JOIN ship_types st ON s.ship_type_id = st.ship_type_id
    JOIN corporations c ON k.victim_corporation_id = c.corporation_id
    WHERE 
        LOWER(c.corporation_name) = 'goat to go'
        AND s.ship_name = 'Ishtar'
        AND k.kill_datetime >= CURRENT_DATE - INTERVAL '12 months'
    GROUP BY 
        TO_CHAR(k.kill_datetime, 'YYYY-MM'),
        p.pilot_name
    ORDER BY 
        mois DESC, 
        ishtars_perdus DESC
    """
    return db.execute_query(query, (12,))


def get_ishtar_losses_30_days(db):
    """Récupère les pertes d'Ishtars des 30 derniers jours"""
    query = """
    SELECT 
        p.pilot_name,
        COUNT(*) as ishtars_perdus,
        SUM(k.value) as valeur_totale_perdue,
        AVG(k.value) as valeur_moyenne_par_ishtar,
        MIN(k.kill_datetime) as premiere_perte,
        MAX(k.kill_datetime) as derniere_perte
    FROM killmails k
    JOIN pilots p ON k.pilot_id = p.pilot_id
    JOIN ships s ON k.ship_id = s.ship_id
    JOIN ship_types st ON s.ship_type_id = st.ship_type_id
    JOIN corporations c ON k.victim_corporation_id = c.corporation_id
    WHERE 
        LOWER(c.corporation_name) = 'goat to go'
        AND s.ship_name = 'Ishtar'
        AND k.kill_datetime >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY 
        p.pilot_name
    ORDER BY 
        ishtars_perdus DESC,
        valeur_totale_perdue DESC
    """
    return db.execute_query(query)


def get_ishtar_losses_all_time(db):
    """Récupère toutes les pertes d'Ishtars"""
    query = """
    SELECT 
        p.pilot_name,
        COUNT(*) as ishtars_perdus,
        SUM(k.value) as valeur_totale_perdue,
        AVG(k.value) as valeur_moyenne_par_ishtar,
        MIN(k.kill_datetime) as premiere_perte,
        MAX(k.kill_datetime) as derniere_perte,
        EXTRACT(DAYS FROM (MAX(k.kill_datetime) - MIN(k.kill_datetime))) as periode_jours
    FROM killmails k
    JOIN pilots p ON k.pilot_id = p.pilot_id
    JOIN ships s ON k.ship_id = s.ship_id
    JOIN ship_types st ON s.ship_type_id = st.ship_type_id
    JOIN corporations c ON k.victim_corporation_id = c.corporation_id
    WHERE 
        LOWER(c.corporation_name) = 'goat to go'
        AND s.ship_name = 'Ishtar'
    GROUP BY
        p.pilot_name
    ORDER BY 
        ishtars_perdus DESC,
        valeur_totale_perdue DESC
    """
    return db.execute_query(query)


def get_recent_losses_details(db):
    """Récupère les détails des pertes récentes"""
    query = """
    SELECT 
        k.kill_datetime,
        p.pilot_name,
        sys.system_name,
        k.value,
        k.kill_hash
    FROM killmails k
    JOIN pilots p ON k.pilot_id = p.pilot_id
    JOIN ships s ON k.ship_id = s.ship_id
    JOIN ship_types st ON s.ship_type_id = st.ship_type_id
    JOIN corporations c ON k.victim_corporation_id = c.corporation_id
    LEFT JOIN systems sys ON k.system_id = sys.system_id
    WHERE 
        LOWER(c.corporation_name) = 'goat to go'
        AND s.ship_name = 'Ishtar'
        AND k.kill_datetime >= CURRENT_DATE - INTERVAL '30 days'
    ORDER BY 
        k.kill_datetime DESC
    """
    return db.execute_query(query)


def aggregate_by_player(data, character_to_player, player_info):
    """Agrège les données par joueur"""
    player_stats = {}
    
    for row in data:
        pilot_name = row.get('pilot_name', '')
        player_id = character_to_player.get(pilot_name.lower())
        
        if player_id:
            if player_id not in player_stats:
                player_stats[player_id] = {
                    'player_name': player_info[player_id]['main_character'],
                    'player_id': player_id,
                    'ishtars_perdus': 0,
                    'valeur_totale_perdue': 0,
                    'characters_involved': set(),
                    'premiere_perte': None,
                    'derniere_perte': None,
                    'losses_by_month': {}
                }
            
            player_stats[player_id]['ishtars_perdus'] += int(row.get('ishtars_perdus', 0))
            player_stats[player_id]['valeur_totale_perdue'] += float(row.get('valeur_totale_perdue', 0))
            player_stats[player_id]['characters_involved'].add(pilot_name)
            
            # Gérer les dates
            if 'premiere_perte' in row and row['premiere_perte']:
                if player_stats[player_id]['premiere_perte'] is None or row['premiere_perte'] < player_stats[player_id]['premiere_perte']:
                    player_stats[player_id]['premiere_perte'] = row['premiere_perte']
            
            if 'derniere_perte' in row and row['derniere_perte']:
                if player_stats[player_id]['derniere_perte'] is None or row['derniere_perte'] > player_stats[player_id]['derniere_perte']:
                    player_stats[player_id]['derniere_perte'] = row['derniere_perte']
            
            # Gérer les données mensuelles
            if 'mois' in row:
                mois = row['mois']
                if mois not in player_stats[player_id]['losses_by_month']:
                    player_stats[player_id]['losses_by_month'][mois] = 0
                player_stats[player_id]['losses_by_month'][mois] += int(row.get('ishtars_perdus', 0))
    
    return player_stats


def format_isk(value):
    """Formate une valeur ISK"""
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    else:
        return f"{value / 1_000:.2f}K"


def generate_html(player_stats_30d, player_stats_all_time, monthly_stats):
    """Génère le HTML du rapport"""
    
    # Top 10 des 30 derniers jours
    top_30d = sorted(player_stats_30d.values(), key=lambda x: x['ishtars_perdus'], reverse=True)[:10]
    
    # Top 10 all time
    top_all_time = sorted(player_stats_all_time.values(), key=lambda x: x['ishtars_perdus'], reverse=True)[:10]
    
    # Préparer les données pour les graphiques
    labels_30d = [p['player_name'] for p in top_30d]
    values_30d = [p['ishtars_perdus'] for p in top_30d]
    
    labels_all_time = [p['player_name'] for p in top_all_time]
    values_all_time = [p['ishtars_perdus'] for p in top_all_time]
    
    # Calcul des statistiques globales
    total_losses = sum(p['ishtars_perdus'] for p in player_stats_all_time.values())
    total_value = sum(p['valeur_totale_perdue'] for p in player_stats_all_time.values())
    total_players = len([p for p in player_stats_all_time.values() if p['ishtars_perdus'] > 0])
    
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Classement Ishtars Perdus - Goat to Go</title>
    
    <style>
        :root {{
            --primary: #1b1b1b;
            --secondary: #252525;
            --accent: #00b4ff;
            --text: #ffffff;
            --blue-light: #4682B4;
            --blue-mid:   #6495ED;
            --grey-light: #808080;
            --grey-dark:  #696969;
            --danger: #ff4444;
        }}
        body {{
            margin: 0;
            padding: 0;
            background-color: var(--primary);
            color: var(--text);
            font-family: 'Segoe UI', sans-serif;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        h1 {{
            color: var(--accent);
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 3rem;
            text-shadow: 0 0 20px rgba(0,180,255,0.5);
        }}
        h2 {{
            color: var(--accent);
            border-bottom: 2px solid var(--accent);
            padding-bottom: 0.5rem;
            margin-top: 2rem;
            opacity: 0;
            transform: translateY(20px);
            animation: fadeInUp 0.5s ease forwards;
        }}
        @keyframes fadeInUp {{
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes slideIn {{
            from {{ transform: translateX(-100%); }}
            to {{ transform: translateX(0); }}
        }}
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
            100% {{ transform: scale(1); }}
        }}
        .chart-container {{
            position: relative;
            margin: auto;
            height: 400px;
            width: 80%;
            opacity: 0;
            animation: fadeInUp 0.5s ease forwards 0.3s;
            background-color: var(--secondary);
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
        }}
        .stats-summary {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 2rem 0;
        }}
        .stat-card {{
            background: var(--secondary);
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            animation: pulse 2s infinite;
            border: 1px solid var(--accent);
            min-height: 120px;
        }}
        .stat-value {{
            font-size: 2rem;
            color: var(--danger);
            margin: 0.5rem 0;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 1rem;
            color: #aaa;
        }}
        .ranking-table {{
            width: 100%;
            margin: 2rem 0;
            border-collapse: collapse;
            background: var(--secondary);
            border-radius: 8px;
            overflow: hidden;
        }}
        .ranking-table th {{
            background: var(--accent);
            color: var(--primary);
            padding: 1rem;
            text-align: left;
            font-weight: bold;
        }}
        .ranking-table td {{
            padding: 1rem;
            border-bottom: 1px solid #333;
        }}
        .ranking-table tr:hover {{
            background: #333;
        }}
        .rank-1 {{ color: #FFD700; }}
        .rank-2 {{ color: #C0C0C0; }}
        .rank-3 {{ color: #CD7F32; }}
        @media (max-width: 768px) {{
            .container {{ padding: 1rem; }}
            .chart-container {{ width: 95%; height: 300px; }}
            .stats-summary {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Classement des Ishtars Perdus - Goat to Go 🚀</h1>
        
        <div class="stats-summary">
            <div class="stat-card">
                <div class="stat-label">Total Ishtars Perdus</div>
                <div class="stat-value">{total_losses}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Valeur Totale Perdue</div>
                <div class="stat-value">{format_isk(total_value)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Joueurs Concernés</div>
                <div class="stat-value">{total_players}</div>
            </div>
        </div>
        
        <h2>📊 Top 10 - 30 Derniers Jours</h2>
        <div class="chart-container">
            <canvas id="chart30d"></canvas>
        </div>
        
        <table class="ranking-table">
            <thead>
                <tr>
                    <th>Rang</th>
                    <th>Joueur</th>
                    <th>Ishtars Perdus</th>
                    <th>Valeur Totale</th>
                    <th>Personnages</th>
                </tr>
            </thead>
            <tbody>"""
    
    for i, player in enumerate(top_30d, 1):
        rank_class = f"rank-{i}" if i <= 3 else ""
        characters = ", ".join(sorted(player['characters_involved']))
        html += f"""
                <tr>
                    <td class="{rank_class}">#{i}</td>
                    <td>{player['player_name']}</td>
                    <td>{player['ishtars_perdus']}</td>
                    <td>{format_isk(player['valeur_totale_perdue'])}</td>
                    <td style="font-size: 0.9em; color: #aaa;">{characters}</td>
                </tr>"""
    
    html += """
            </tbody>
        </table>
        
        <h2>🏆 Top 10 - All Time</h2>
        <div class="chart-container">
            <canvas id="chartAllTime"></canvas>
        </div>
        
        <table class="ranking-table">
            <thead>
                <tr>
                    <th>Rang</th>
                    <th>Joueur</th>
                    <th>Ishtars Perdus</th>
                    <th>Valeur Totale</th>
                    <th>Période</th>
                    <th>Personnages</th>
                </tr>
            </thead>
            <tbody>"""
    
    for i, player in enumerate(top_all_time, 1):
        rank_class = f"rank-{i}" if i <= 3 else ""
        characters = ", ".join(sorted(player['characters_involved']))
        
        # Calculer la période
        if player['premiere_perte'] and player['derniere_perte']:
            periode = f"{player['premiere_perte'].strftime('%Y-%m-%d')} à {player['derniere_perte'].strftime('%Y-%m-%d')}"
        else:
            periode = "N/A"
        
        html += f"""
                <tr>
                    <td class="{rank_class}">#{i}</td>
                    <td>{player['player_name']}</td>
                    <td>{player['ishtars_perdus']}</td>
                    <td>{format_isk(player['valeur_totale_perdue'])}</td>
                    <td style="font-size: 0.9em;">{periode}</td>
                    <td style="font-size: 0.9em; color: #aaa;">{characters}</td>
                </tr>"""
    
    html += """
            </tbody>
        </table>
        
        <h2>📈 Évolution Mensuelle</h2>
        <div class="chart-container" style="height: 500px;">
            <canvas id="chartMonthly"></canvas>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.2.1/dist/chart.umd.js"></script>
    <script>
        // Configuration des graphiques
        Chart.defaults.color = '#fff';
        Chart.defaults.borderColor = '#333';
        
        // Graphique 30 jours
        const ctx30d = document.getElementById('chart30d').getContext('2d');
        new Chart(ctx30d, {
            type: 'bar',
            data: {
                labels: """ + json.dumps(labels_30d) + """,
                datasets: [{
                    label: 'Ishtars Perdus (30j)',
                    data: """ + json.dumps(values_30d) + """,
                    backgroundColor: 'rgba(255, 68, 68, 0.6)',
                    borderColor: 'rgba(255, 68, 68, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        
        // Graphique All Time
        const ctxAllTime = document.getElementById('chartAllTime').getContext('2d');
        new Chart(ctxAllTime, {
            type: 'bar',
            data: {
                labels: """ + json.dumps(labels_all_time) + """,
                datasets: [{
                    label: 'Ishtars Perdus (Total)',
                    data: """ + json.dumps(values_all_time) + """,
                    backgroundColor: 'rgba(255, 68, 68, 0.8)',
                    borderColor: 'rgba(255, 68, 68, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        
        // Préparer les données mensuelles
        """
    
    # Préparer les données JavaScript pour le graphique mensuel
    # Générer tous les mois des 12 derniers mois
    from datetime import datetime, timedelta
    import calendar
    
    current_date = datetime.now()
    allMonths = []
    for i in range(11, -1, -1):  # 11 à 0 pour avoir les 12 derniers mois
        date = current_date - timedelta(days=i*30)  # Approximation
        month_str = date.strftime('%Y-%m')
        allMonths.append(month_str)
    
    # S'assurer qu'on a exactement les 12 derniers mois dans l'ordre chronologique
    end_date = current_date
    start_date = end_date - timedelta(days=365)
    months_list = []
    current = start_date
    while current <= end_date:
        months_list.append(current.strftime('%Y-%m'))
        # Aller au mois suivant
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    
    sorted_months = months_list[-12:]  # Les 12 derniers mois
    
    # Top 5 joueurs pour le graphique mensuel
    top_monthly = sorted(monthly_stats.values(), key=lambda x: x['ishtars_perdus'], reverse=True)[:5]
    
    html += """
        const allMonths = """ + json.dumps(sorted_months) + """;
        const datasets = [];
        const colors = [
            'rgba(255, 68, 68, 0.8)',
            'rgba(0, 180, 255, 0.8)',
            'rgba(255, 180, 0, 0.8)',
            'rgba(0, 255, 100, 0.8)',
            'rgba(255, 0, 255, 0.8)'
        ];
        """
    
    for i, player in enumerate(top_monthly):
        monthly_values = [player['losses_by_month'].get(month, 0) for month in sorted_months]
        html += f"""
        datasets.push({{
            label: '{player['player_name']}',
            data: {json.dumps(monthly_values)},
            backgroundColor: colors[{i}],
            borderColor: colors[{i}].replace('0.8', '1'),
            borderWidth: 2,
            tension: 0.1
        }});
        """
    
    html += """
        // Graphique mensuel
        const ctxMonthly = document.getElementById('chartMonthly').getContext('2d');
        new Chart(ctxMonthly, {
            type: 'bar',
            data: {
                labels: allMonths,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    title: {
                        display: true,
                        text: 'Top 5 Joueurs - Évolution Mensuelle (12 derniers mois)',
                        color: '#00b4ff',
                        font: {
                            size: 16
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        stacked: false,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    </script>
</body>
</html>"""
    
    return html


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description='Générateur de rapport de classement Ishtar')
    parser.add_argument('--output', default='html/ishtar_ranking.html', help='Fichier de sortie')
    args = parser.parse_args()
    
    try:
        logging.info("Début de la génération du rapport Ishtar")
        
        # Créer le répertoire HTML si nécessaire
        if not os.path.exists('html'):
            os.makedirs('html')
            logging.info("Répertoire 'html' créé")
        
        # Parser les données des joueurs
        character_to_player, player_info = parse_player_data()
        logging.info(f"Données parsées pour {len(player_info)} joueurs")
        
        with DatabaseConnection() as db:
            # Récupérer les données
            logging.info("Récupération des données des 30 derniers jours")
            data_30d = get_ishtar_losses_30_days(db)
            player_stats_30d = aggregate_by_player(data_30d, character_to_player, player_info)
            
            logging.info("Récupération des données all time")
            data_all_time = get_ishtar_losses_all_time(db)
            player_stats_all_time = aggregate_by_player(data_all_time, character_to_player, player_info)
            
            logging.info("Récupération des données mensuelles (12 derniers mois)")
            data_monthly = get_ishtar_losses_by_month(db, months=12)
            monthly_stats = {}
            for row in data_monthly:
                pilot_name = row.get('pilot_name', '')
                player_id = character_to_player.get(pilot_name.lower())
                
                if player_id:
                    if player_id not in monthly_stats:
                        monthly_stats[player_id] = {
                            'player_name': player_info[player_id]['main_character'],
                            'player_id': player_id,
                            'ishtars_perdus': 0,
                            'losses_by_month': {}
                        }
                    
                    mois = row['mois']
                    if mois not in monthly_stats[player_id]['losses_by_month']:
                        monthly_stats[player_id]['losses_by_month'][mois] = 0
                    monthly_stats[player_id]['losses_by_month'][mois] += int(row.get('ishtars_perdus', 0))
                    monthly_stats[player_id]['ishtars_perdus'] += int(row.get('ishtars_perdus', 0))
        
        # Générer le HTML
        logging.info("Génération du HTML")
        html_content = generate_html(player_stats_30d, player_stats_all_time, monthly_stats)
        
        # Créer le répertoire si nécessaire
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Écrire le fichier
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info(f"Rapport généré avec succès: {args.output}")
        
    except Exception as e:
        logging.error(f"Erreur lors de la génération du rapport: {e}")
        raise


if __name__ == "__main__":
    main()
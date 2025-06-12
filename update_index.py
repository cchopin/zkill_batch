#!/usr/bin/env python3
"""
Script pour régénérer uniquement le fichier index.html avec les liens vers
les classements Ishtar/MTU et tous les rapports mensuels
"""

import os
import glob
from datetime import datetime

OUTPUT_DIR = "html"
WEB_DIR = "/var/www/news.eve-goats.fr"

def update_index():
    """Génère le fichier index.html avec tous les liens"""
    
    # Rechercher tous les fichiers de rapports mensuels dans le répertoire web
    report_files = glob.glob(os.path.join(WEB_DIR, "2025*.html"))
    # Exclure index.html et les fichiers de classement
    report_files = [f for f in report_files if os.path.basename(f) not in ["index.html", "ishtar_ranking.html", "mtu_ranking.html"]]
    report_files.sort(reverse=True)  # Tri inverse pour avoir le plus récent en premier
    
    # Générer la liste des liens pour les rapports mensuels
    links = ""
    for file in report_files:
        base = os.path.basename(file)
        # Afficher le lien au format "YYYY-MM"
        year = base[:4]
        month = base[4:6]
        display_name = f"{year}-{month}"
        links += f'                <li><a href="{base}">📊 {display_name}</a></li>\n'
    
    # Obtenir l'horodatage actuel
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Générer le contenu HTML
    index_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EVE Online - Goat to Go Reports</title>
    
    <style>
        :root {{
            --primary: #1b1b1b;
            --secondary: #252525;
            --accent: #00b4ff;
            --text: #ffffff;
            --blue-light: #4682B4;
            --blue-mid: #6495ED;
            --grey-light: #808080;
            --grey-dark: #696969;
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
            animation: fadeInUp 0.5s ease forwards;
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
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.02); }}
            100% {{ transform: scale(1); }}
        }}
        .section {{
            background-color: var(--secondary);
            border-radius: 8px;
            padding: 2rem;
            margin: 2rem 0;
            animation: fadeInUp 0.5s ease forwards 0.3s;
            opacity: 0;
        }}
        ul.report-list {{
            list-style: none;
            padding: 0;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
        }}
        ul.report-list li {{
            background: linear-gradient(135deg, #2a2a2a, #333);
            border: 1px solid var(--accent);
            border-radius: 8px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        ul.report-list li:hover {{
            transform: translateY(-5px) scale(1.05);
            box-shadow: 0 12px 30px rgba(0,180,255,0.6);
            animation: pulse 2s infinite;
        }}
        ul.report-list li a {{
            color: var(--accent);
            text-decoration: none;
            display: block;
            padding: 1.5rem;
            text-align: center;
            font-size: 1.1rem;
            font-weight: bold;
        }}
        .special-link {{
            background: linear-gradient(135deg, #2a2a2a, #400);
            border: 2px solid var(--danger) !important;
            grid-column: span 2;
        }}
        .special-link:hover {{
            box-shadow: 0 12px 30px rgba(255,68,68,0.6);
        }}
        .special-link a {{
            color: var(--danger) !important;
            font-size: 1.3rem;
        }}
        .mtu-link {{
            background: linear-gradient(135deg, #2a2a2a, #400);
            border: 2px solid var(--danger) !important;
            grid-column: span 2;
        }}
        .mtu-link:hover {{
            box-shadow: 0 12px 30px rgba(255,68,68,0.6);
        }}
        .mtu-link a {{
            color: var(--danger) !important;
            font-size: 1.3rem;
        }}
        .special-link .emoji, .mtu-link .emoji {{
            font-size: 2rem;
            display: block;
            margin-bottom: 0.5rem;
        }}
        .stats-info {{
            text-align: center;
            color: #aaa;
            margin-top: 2rem;
            font-size: 0.9rem;
        }}
        @media (max-width: 768px) {{
            .container {{ padding: 1rem; }}
            ul.report-list {{ grid-template-columns: 1fr; }}
            .special-link, .mtu-link {{ grid-column: span 1; }}
        }}
    </style>
    
</head>
<body>
    <div class="container">
        <h1>🚀 EVE Online - Goat to Go 🚀</h1>
        
        <div class="section">
            <h2>📈 Classements Spéciaux</h2>
            <ul class="report-list">
                <li class="mtu-link">
                    <a href="mtu_ranking.html">
                        <span class="emoji">☠️</span>
                        Classement des MTU Perdus
                    </a>
                </li>
                <li class="special-link">
                    <a href="ishtar_ranking.html">
                        <span class="emoji">💀</span>
                        Classement des Ishtars Perdus
                    </a>
                </li>
            </ul>
        </div>
        
        <div class="section">
            <h2>📅 Rapports Mensuels de Killmails</h2>
            <ul class="report-list">
{links}            </ul>
        </div>
        
        <div class="stats-info">
            <p>Dernière mise à jour: {current_time}</p>
            <p>Corporation: Goat to Go</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Créer le répertoire HTML si nécessaire
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Écrire le fichier index.html
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    
    print(f"Index mis à jour : {index_path}")
    print(f"Rapports trouvés dans {WEB_DIR} : {len(report_files)}")
    for file in sorted(report_files):
        print(f"  - {os.path.basename(file)}")

if __name__ == "__main__":
    update_index()
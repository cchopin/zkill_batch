#!/usr/bin/env python3
import os
import psycopg2
from psycopg2 import extras
import json
import logging
import argparse
import calendar
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler('logs/big_report.log'), logging.StreamHandler()]
)

class DatabaseConnection:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
            self.cur = self.conn.cursor(cursor_factory=extras.DictCursor)
            logging.info("Database connection established successfully")
        except Exception as e:
            logging.error(f"Error connecting to database: {e}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.cur.close()
            self.conn.close()
            logging.info("Database connection closed")
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")

    def execute_query(self, query, params=None):
        try:
            self.cur.execute(query, params)
            return self.cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error executing query: {e}")
            raise

def generate_report(start_date, end_date):
    """
    Génère un rapport HTML pour la période spécifiée.
    Les sections incluses sont :
      1. Graphique des statistiques journalières (kills & ISK)
      2. Graphique du ratio kills/loss par jour
      3. KPI Top 20 Ship Types (avec barre de progression)
      4. Graphique Top 10 Pilotes de la Corporation (kills, ISK et efficacité)
    """
    # --- 1. Graphique : Statistiques journalières (kills et ISK)
    query_daily = """
        SELECT DATE(kill_datetime) AS jour,
               COUNT(*) AS nb_kills,
               SUM(value) AS total_isk
        FROM killmails
        WHERE kill_datetime >= %s
          AND kill_datetime < (%s::date + INTERVAL '1 day')
        GROUP BY jour
        ORDER BY jour;
    """

    # --- 2. Graphique : Ratio kills/loss par jour
    query_daily_ratio = """
        SELECT DATE(kill_datetime) AS jour,
               SUM(CASE WHEN kill_type = 'KILL' THEN 1 ELSE 0 END) AS kills,
               SUM(CASE WHEN kill_type = 'LOSS' THEN 1 ELSE 0 END) AS losses
        FROM killmails
        WHERE kill_datetime >= %s
          AND kill_datetime < (%s::date + INTERVAL '1 day')
        GROUP BY jour
        ORDER BY jour;
    """

    # --- 3. KPI : Top 20 Ship Types par ISK détruite
    query_shiptype = """
        SELECT st.type_name,
               COUNT(*) AS nb_kills,
               SUM(k.value) AS total_isk
        FROM killmails k
        JOIN ships sh ON k.ship_id = sh.ship_id
        JOIN ship_types st ON sh.ship_type_id = st.ship_type_id
        WHERE kill_datetime >= %s
          AND kill_datetime < (%s::date + INTERVAL '1 day')
        GROUP BY st.type_name
        ORDER BY total_isk DESC
        LIMIT 20;
    """

    # --- 4. Graphique : Top 10 Pilotes de la Corp (kills, ISK et efficacité)
    query_top_corp = """
        SELECT p.pilot_name,
               SUM(CASE WHEN kill_type = 'KILL' THEN 1 ELSE 0 END) AS kills,
               SUM(CASE WHEN kill_type = 'LOSS' THEN 1 ELSE 0 END) AS losses,
               SUM(CASE WHEN kill_type = 'KILL' THEN k.value ELSE 0 END) AS isk_destroyed,
               SUM(CASE WHEN kill_type = 'LOSS' THEN k.value ELSE 0 END) AS isk_lost
        FROM killmails k
        JOIN pilots p ON k.pilot_id = p.pilot_id
        WHERE kill_datetime >= %s
          AND kill_datetime < (%s::date + INTERVAL '1 day')
        GROUP BY p.pilot_name
        HAVING SUM(CASE WHEN kill_type = 'KILL' THEN 1 ELSE 0 END) > 0
        ORDER BY kills DESC
        LIMIT 10;
    """

    # Exécution des requêtes
    with DatabaseConnection() as db:
        daily_data       = db.execute_query(query_daily, (start_date, end_date))
        daily_ratio_data = db.execute_query(query_daily_ratio, (start_date, end_date))
        shiptype_data    = db.execute_query(query_shiptype, (start_date, end_date))
        top_corp_data    = db.execute_query(query_top_corp, (start_date, end_date))

    # Préparation des données pour le Graphique 1 (Daily stats)
    days = [row['jour'].strftime('%Y-%m-%d') for row in daily_data]
    daily_kills = [row['nb_kills'] for row in daily_data]
    daily_isk = [float(row['total_isk']) for row in daily_data]

    # Préparation des données pour le Graphique 2 (Daily ratio)
    ratio_days = [row['jour'].strftime('%Y-%m-%d') for row in daily_ratio_data]
    daily_ratios = []
    for row in daily_ratio_data:
        kills = row['kills']
        losses = row['losses']
        ratio = kills / losses if losses > 0 else kills
        daily_ratios.append(ratio)

    # --- KPI : Top 20 Ship Types
    if shiptype_data:
        max_ship_isk = max(float(r['total_isk']) for r in shiptype_data)
    else:
        max_ship_isk = 1.0

    shiptype_html = ""
    for row in shiptype_data:
        ship_type = row['type_name']
        kills = row['nb_kills']
        total_val = float(row['total_isk'])
        cost_in_b = total_val / 1e9
        formatted_cost = f"{cost_in_b:.2f}B"
        perc = (total_val / max_ship_isk) * 100 if max_ship_isk > 0 else 0

        shiptype_html += f"""
        <div class="kpi-box">
          <h3>{ship_type}</h3>
          <p>{formatted_cost} ISK</p>
          <p>{kills} kills</p>
          <div class="bar-container">
            <div class="bar-fill" style="width: {perc:.0f}%"></div>
          </div>
        </div>
        """

    # --- Graphique 3 : Top 10 Pilotes de la Corp
    pilot_names = []
    pilot_kills = []
    pilot_isk = []
    pilot_efficiency = []  # en pourcentage

    for row in top_corp_data:
        pilot = row['pilot_name']
        kills = row['kills']
        losses = row['losses']
        isk_destroyed = float(row['isk_destroyed'])
        isk_lost = float(row['isk_lost'])
        total = isk_destroyed + isk_lost
        efficiency = (isk_destroyed / total * 100) if total > 0 else 100
        pilot_names.append(pilot)
        pilot_kills.append(kills)
        pilot_isk.append(isk_destroyed)
        pilot_efficiency.append(round(efficiency, 1))

    # Construction finale du HTML
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rapport Corp - {start_date} à {end_date}</title>
  <style>
    :root {{
      --primary: #1b1b1b;
      --secondary: #252525;
      --accent: #00b4ff;
      --text: #ffffff;
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
    h2 {{
      color: var(--accent);
      border-bottom: 2px solid var(--accent);
      padding-bottom: 0.5rem;
      margin-top: 2rem;
    }}
    /* Graphiques Chart.js */
    .chart-container {{
      position: relative;
      margin: auto;
      height: 400px;
      width: 80%;
    }}
    /* KPI : Top 20 Ship Types */
    .kpi-container {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 1rem;
      margin-top: 2rem;
      align-items: start;
    }}
    .kpi-box {{
      background-color: var(--secondary);
      border: 1px solid var(--accent);
      padding: 1rem;
      border-radius: 4px;
      text-align: center;
      overflow: hidden;
    }}
    .kpi-box h3 {{
      margin: 0.5rem 0;
      font-size: 1rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .kpi-box p {{
      margin: 0.2rem 0;
      font-size: 0.9rem;
    }}
    .bar-container {{
      background-color: #333;
      height: 8px;
      margin-top: 0.5rem;
      border-radius: 4px;
      overflow: hidden;
    }}
    .bar-fill {{
      background-color: var(--accent);
      height: 100%;
      transition: width 0.3s ease;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
    }}
    th, td {{
      border-bottom: 1px solid var(--accent);
      padding: 0.75rem;
      text-align: left;
    }}
    th {{
      color: var(--accent);
    }}
  </style>
  <!-- Inclusion de Chart.js via CDN -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
<div class="container">
  <!-- Graphique 1 : Statistiques journalières -->
  <h2>Statistiques Journalières (Kills et ISK)</h2>
  <div class="chart-container">
    <canvas id="dailyChart"></canvas>
  </div>
  
  <!-- Graphique 2 : Ratio Kills/Loss par jour -->
  <h2>Ratio Kills / Losses par Jour</h2>
  <div class="chart-container">
    <canvas id="ratioChart"></canvas>
  </div>
  
  <!-- KPI : Top 20 Ship Types -->
  <h2>Top 20 Ship Types (par ISK détruite)</h2>
  <div class="kpi-container">
      {shiptype_html}
  </div>
  
  <!-- Graphique 3 : Top 10 Pilotes de la Corp -->
  <h2>Top 10 Pilotes de la Corp</h2>
  <div class="chart-container">
    <canvas id="pilotChart"></canvas>
  </div>
  
</div>

<script>
  // Graphique 1 : Statistiques journalières
  const dailyCtx = document.getElementById('dailyChart').getContext('2d');
  const dailyChart = new Chart(dailyCtx, {{
    type: 'bar',
    data: {{
      labels: {json.dumps(days)},
      datasets: [
        {{
          label: 'Nombre de Kills',
          data: {json.dumps(daily_kills)},
          backgroundColor: 'rgba(0, 180, 255, 0.5)',
          borderColor: 'rgba(0, 180, 255, 1)',
          borderWidth: 1
        }},
        {{
          type: 'line',
          label: 'Valeur Totale (ISK)',
          data: {json.dumps(daily_isk)},
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 2,
          fill: false,
          yAxisID: 'y1'
        }}
      ]
    }},
    options: {{
      responsive: true,
      scales: {{
        y: {{
          beginAtZero: true,
          position: 'left',
          title: {{
            display: true,
            text: 'Nombre de Kills'
          }}
        }},
        y1: {{
          beginAtZero: true,
          position: 'right',
          grid: {{
            drawOnChartArea: false
          }},
          title: {{
            display: true,
            text: 'Valeur Totale (ISK)'
          }}
        }}
      }}
    }}
  }});
  
  // Graphique 2 : Ratio Kills / Losses par jour
  const ratioCtx = document.getElementById('ratioChart').getContext('2d');
  const ratioChart = new Chart(ratioCtx, {{
    type: 'line',
    data: {{
      labels: {json.dumps(ratio_days)},
      datasets: [
        {{
          label: 'Ratio Kills / Losses',
          data: {json.dumps(daily_ratios)},
          backgroundColor: 'rgba(255, 205, 86, 0.2)',
          borderColor: 'rgba(255, 205, 86, 1)',
          borderWidth: 2,
          fill: false
        }}
      ]
    }},
    options: {{
      responsive: true,
      scales: {{
        y: {{
          beginAtZero: true,
          title: {{
            display: true,
            text: 'Ratio (Kills/Losses)'
          }}
        }}
      }}
    }}
  }});
  
  // Graphique 3 : Top 10 Pilotes de la Corp
  const pilotCtx = document.getElementById('pilotChart').getContext('2d');
  const pilotChart = new Chart(pilotCtx, {{
    data: {{
      labels: {json.dumps(pilot_names)},
      datasets: [
        {{
          type: 'bar',
          label: 'Kills',
          data: {json.dumps(pilot_kills)},
          backgroundColor: 'rgba(0, 180, 255, 0.5)',
          borderColor: 'rgba(0, 180, 255, 1)',
          borderWidth: 1
        }},
        {{
          type: 'line',
          label: 'ISK Destroyed',
          data: {json.dumps(pilot_isk)},
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 2,
          fill: false,
          yAxisID: 'y1'
        }}
      ]
    }},
    options: {{
      responsive: true,
      plugins: {{
        tooltip: {{
          callbacks: {{
            afterLabel: function(context) {{
              const idx = context.dataIndex;
              const eff = {json.dumps(pilot_efficiency)}[idx];
              return 'Efficiency: ' + eff + '%';
            }}
          }}
        }}
      }},
      scales: {{
        y: {{
          beginAtZero: true,
          position: 'left',
          title: {{
            display: true,
            text: 'Nombre de Kills'
          }}
        }},
        y1: {{
          beginAtZero: true,
          position: 'right',
          grid: {{
            drawOnChartArea: false
          }},
          title: {{
            display: true,
            text: 'ISK Destroyed'
          }}
        }}
      }}
    }}
  }});
</script>
</body>
</html>
"""

    output_file = "report_january2025.html"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        logging.info(f"Report generated successfully: {output_file}")
    except Exception as e:
        logging.error(f"Error writing HTML report: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Génération du rapport mensuel pour les killmails.")
    parser.add_argument("--year", type=int, default=2025, help="Année du rapport (défaut: 2025)")
    parser.add_argument("--month", type=int, default=1, help="Mois du rapport (défaut: 1)")
    args = parser.parse_args()

    # Calculer la date de début et de fin du mois
    year = args.year
    month = args.month
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day:02d}"

    logging.info(f"Generating report for period: {start_date} to {end_date}")
    generate_report(start_date, end_date)
    logging.info("Report generation completed successfully")

if __name__ == "__main__":
    main()

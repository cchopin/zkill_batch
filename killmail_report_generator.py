#!/usr/bin/env python3
import os
import psycopg2
from psycopg2 import extras
import json
import logging
import argparse
import calendar
from datetime import datetime
from dotenv import load_dotenv
import glob

# Load environment variables
load_dotenv()

# Create a log filename based on the current date and time
log_filename = os.path.join("logs", f"killmail_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging with a file handler (per execution) and a stream handler
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

logging.info(f"Execution started. Logging to {log_filename}")

# Ensure the "html" directory exists
OUTPUT_DIR = "html"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

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

# All queries are filtered by the report month

def get_daily_stats(db, start_date, end_date):
    query = """
    SELECT 
        DATE(kill_datetime) AS day,
        COUNT(*) AS kill_count,
        SUM(CASE WHEN kill_type = 'KILL' THEN value ELSE 0 END) AS value_destroyed,
        SUM(CASE WHEN kill_type = 'LOSS' THEN value ELSE 0 END) AS value_lost
    FROM killmails
    WHERE kill_datetime >= %s 
      AND kill_datetime < %s::date + interval '1 day'
    GROUP BY day
    ORDER BY day;
    """
    return db.execute_query(query, (start_date, end_date))

def get_ship_types(db, start_date, end_date):
    query = """
    SELECT 
        st.type_name,
        COUNT(*) AS kill_count,
        SUM(k.value) AS total_isk
    FROM killmails k
    JOIN ships s ON k.ship_id = s.ship_id
    JOIN ship_types st ON s.ship_type_id = st.ship_type_id
    WHERE k.kill_datetime >= %s 
      AND k.kill_datetime < %s::date + interval '1 day'
      AND k.kill_type = 'KILL'
    GROUP BY st.type_name
    ORDER BY total_isk DESC
    LIMIT 20;
    """
    return db.execute_query(query, (start_date, end_date))

def get_top_corp_pilots(db, start_date, end_date, corporation_name):
    query = """
    SELECT COUNT(*) AS nb_kills, SUM(k.value) AS isk_destroyed, KA.pilot_name
    FROM corporations C
    INNER JOIN killmail_attackers KA ON KA.attacker_corporation_id = C.corporation_id
    INNER JOIN killmails k ON k.killmail_id = KA.killmail_id
    WHERE C.corporation_name = %s
      AND k.kill_datetime >= %s 
      AND k.kill_datetime < %s::date + interval '1 day'
    GROUP BY KA.pilot_name
    ORDER BY nb_kills DESC, isk_destroyed DESC
    LIMIT 10;
    """
    return db.execute_query(query, (corporation_name, start_date, end_date))

def get_additional_stats(db, start_date, end_date, corp_name):
    query = """
    WITH params AS (
        SELECT %s::date AS start_date,
               %s::date AS end_date,
               %s AS corp_name
    ),
    kills AS (
        SELECT COUNT(CASE WHEN kill_type = 'KILL' THEN 1 END) AS total_kills,
               SUM(CASE WHEN kill_type = 'KILL' THEN value ELSE 0 END) AS total_isk_destroyed
        FROM corporations C
        INNER JOIN killmail_attackers KA ON KA.attacker_corporation_id = C.corporation_id
        INNER JOIN killmails k ON k.killmail_id = KA.killmail_id
        CROSS JOIN params p
        WHERE k.kill_datetime >= p.start_date
          AND k.kill_datetime < p.end_date
          AND C.corporation_name = p.corp_name
    ),
    losses AS (
        SELECT COUNT(CASE WHEN kill_type = 'LOSS' THEN 1 END) AS total_losses,
               SUM(CASE WHEN kill_type = 'LOSS' THEN value ELSE 0 END) AS total_isk_lost
        FROM killmails k
        INNER JOIN corporations C ON k.victim_corporation_id = C.corporation_id
        CROSS JOIN params p
        WHERE k.kill_datetime >= p.start_date
          AND k.kill_datetime < p.end_date
          AND C.corporation_name = p.corp_name
    )
    SELECT kills.total_kills, kills.total_isk_destroyed, losses.total_losses, losses.total_isk_lost
    FROM kills, losses;
    """
    return db.execute_query(query, (start_date, end_date, corp_name))

def get_peak_hour(db, start_date, end_date):
    query = """
    SELECT EXTRACT(HOUR FROM kill_datetime) AS peak_hour
    FROM killmails
    WHERE kill_datetime >= %s
      AND kill_datetime < %s::date + interval '1 day'
    GROUP BY peak_hour
    ORDER BY COUNT(*) DESC
    LIMIT 1;
    """
    result = db.execute_query(query, (start_date, end_date))
    if result and result[0]['peak_hour'] is not None:
        return int(result[0]['peak_hour'])
    else:
        return 0

def get_kills_distribution_by_hour(db, start_date, end_date):
    query = """
    SELECT EXTRACT(HOUR FROM kill_datetime) AS hour, COUNT(*) AS kill_count
    FROM killmails
    WHERE kill_datetime >= %s
      AND kill_datetime < %s::date + interval '1 day'
    GROUP BY hour
    ORDER BY hour;
    """
    return db.execute_query(query, (start_date, end_date))

def format_isk(value):
    if value >= 1e12:
        return f"{value/1e12:.2f}T"
    elif value >= 1e9:
        return f"{value/1e9:.2f}B"
    elif value >= 1e6:
        return f"{value/1e6:.2f}M"
    else:
        return f"{value:,.0f}"

def generate_shiptype_html(shiptype_data):
    """Generate HTML for Top 20 Ship Types KPI with enhanced mouse-over effect"""
    html = ""
    max_isk = max(float(row['total_isk']) for row in shiptype_data) if shiptype_data else 1.0
    for row in shiptype_data:
        ship_type = row['type_name']
        kills = row['kill_count']
        total_val = float(row['total_isk'])
        perc = (total_val / max_isk) * 100
        html += f"""
        <div class="kpi-box">
            <h3>{ship_type}</h3>
            <p>{format_isk(total_val)} ISK</p>
            <p>{kills} kills</p>
            <div class="bar-container">
                <div class="bar-fill" style="width: {perc:.0f}%"></div>
            </div>
        </div>
        """
    return html

def generate_additional_stats_html(stats, peak_hour):
    """Generate HTML for Additional Statistics with 3 stat cards: Global K/D Ratio, ISK Efficiency, Peak Hour"""
    if not stats or len(stats) == 0:
        return ""
    total_kills = stats[0]['total_kills'] or 0
    total_losses = stats[0]['total_losses'] or 0
    kd_ratio = total_kills / total_losses if total_losses > 0 else total_kills
    total_isk_destroyed = float(stats[0]['total_isk_destroyed'] or 0)
    total_isk_lost = float(stats[0]['total_isk_lost'] or 0)
    isk_efficiency = (total_isk_destroyed / (total_isk_destroyed + total_isk_lost)) * 100 if (total_isk_destroyed + total_isk_lost) > 0 else 100

    return f"""
        <div class="stat-card">
            <h3>Global K/D Ratio</h3>
            <div class="stat-value">{kd_ratio:.2f}</div>
            <div class="stat-details">{total_kills} kills / {total_losses} losses</div>
        </div>
        <div class="stat-card">
            <h3>ISK Efficiency</h3>
            <div class="stat-value">{isk_efficiency:.1f}%</div>
            <div class="stat-details">
                +{format_isk(total_isk_destroyed)} / -{format_isk(total_isk_lost)}
            </div>
        </div>
        <div class="stat-card">
            <h3>Peak Hour (EVE Time)</h3>
            <div class="stat-value">{peak_hour:02d}:00</div>
        </div>
    """

def get_css_styles():
    return """
    <style>
        :root {
            --primary: #1b1b1b;
            --secondary: #252525;
            --accent: #00b4ff;
            --text: #ffffff;
            --blue-light: #4682B4;
            --blue-mid:   #6495ED;
            --grey-light: #808080;
            --grey-dark:  #696969;
        }
        body {
            margin: 0;
            padding: 0;
            background-color: var(--primary);
            color: var(--text);
            font-family: 'Segoe UI', sans-serif;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        h2 {
            color: var(--accent);
            border-bottom: 2px solid var(--accent);
            padding-bottom: 0.5rem;
            margin-top: 2rem;
            opacity: 0;
            transform: translateY(20px);
            animation: fadeInUp 0.5s ease forwards;
        }
        @keyframes fadeInUp {
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideIn {
            from { transform: translateX(-100%); }
            to { transform: translateX(0); }
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.02); }
            100% { transform: scale(1); }
        }
        /* Chart container for all charts */
        .chart-container {
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
        }
        /* Hover effect for Chart 3: Top Corporation Pilots */
        .chart-container.pilot-chart-container {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .chart-container.pilot-chart-container:hover {
            transform: scale(1.05) translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,180,255,0.5);
        }
        /* KPI: Top 20 Ship Types - enhanced mouse-over effect */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }
        .kpi-box {
            background: linear-gradient(135deg, var(--secondary), #2a2a2a);
            border: 1px solid var(--accent);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            opacity: 0;
            animation: fadeInUp 0.5s ease forwards;
        }
        .kpi-box:hover {
            transform: translateY(-5px) scale(1.05);
            box-shadow: 0 12px 30px rgba(0,180,255,0.6);
        }
        .kpi-box h3 {
            margin: 0.5rem 0;
            font-size: 1rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .kpi-box p {
            margin: 0.2rem 0;
            font-size: 0.9rem;
        }
        .bar-container {
            background-color: #333;
            height: 8px;
            margin-top: 0.5rem;
            border-radius: 4px;
            overflow: hidden;
        }
        .bar-fill {
            background-color: var(--accent);
            height: 100%;
            transform: translateX(-100%);
            animation: slideIn 1s ease forwards;
        }
        /* Grid for Additional Statistics: 3 equally-sized cards */
        .stats-summary {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 2rem 0;
        }
        .stat-card {
            background: var(--secondary);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
            animation: pulse 2s infinite;
            border: 1px solid var(--accent);
            min-height: 120px;
        }
        .stat-value {
            font-size: 1.25rem;
            color: var(--accent);
            margin: 0.5rem 0;
        }
        .stat-details {
            font-size: 0.8rem;
            color: #888;
        }
        @media (max-width: 768px) {
            .container { padding: 1rem; }
            .chart-container { width: 95%; height: 300px; }
            .kpi-container { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
            .stats-summary { grid-template-columns: 1fr; }
        }
    </style>
    """

def generate_javascript(days, kills_value, losses_value, kill_count, pilot_names, pilot_ships, pilot_isk, hours, kills_per_hour):
    return f"""
    // Chart 1: Daily Statistics (ISK Destroyed and Kill Count)
    const dailyCtx = document.getElementById('dailyChart').getContext('2d');
    new Chart(dailyCtx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(days)},
            datasets: [
                {{
                    label: 'Destroyed Value',
                    data: {json.dumps(kills_value)},
                    backgroundColor: 'rgba(70, 130, 180, 0.7)',
                    borderColor: 'rgba(70, 130, 180, 1)',
                    borderWidth: 1,
                    yAxisID: 'y'
                }},
                {{
                    label: 'Kill Count',
                    data: {json.dumps(kill_count)},
                    type: 'line',
                    borderColor: 'rgba(128, 128, 128, 1)',
                    backgroundColor: 'rgba(128, 128, 128, 0.3)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    yAxisID: 'y1'
                }}
            ]
        }},
        options: {{
            responsive: true,
            plugins: {{
                title: {{
                    display: true,
                    text: 'Daily Destroyed Value and Kill Count',
                    color: '#ffffff'
                }},
                legend: {{
                    position: 'top'
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: 'ISK (in Billions)',
                        color: '#ffffff'
                    }},
                    ticks: {{
                        callback: function(value) {{
                            return (value / 1e9).toFixed(2) + 'B';
                        }}
                    }}
                }},
                y1: {{
                    beginAtZero: true,
                    position: 'right',
                    title: {{
                        display: true,
                        text: 'Kill Count',
                        color: '#ffffff'
                    }},
                    grid: {{
                        drawOnChartArea: false
                    }}
                }}
            }}
        }}
    }});
    
    // Chart 2: Kills vs Losses Value
    const valueCtx = document.getElementById('valueChart').getContext('2d');
    new Chart(valueCtx, {{
        type: 'line',
        data: {{
            labels: {json.dumps(days)},
            datasets: [
                {{
                    label: 'Destroyed Value',
                    data: {json.dumps(kills_value)},
                    borderColor: 'rgba(70, 130, 180, 1)',
                    backgroundColor: 'rgba(70, 130, 180, 0.1)',
                    fill: true
                }},
                {{
                    label: 'Lost Value',
                    data: {json.dumps(losses_value)},
                    borderColor: 'rgba(119, 136, 153, 1)',
                    backgroundColor: 'rgba(119, 136, 153, 0.1)',
                    fill: true
                }}
            ]
        }},
        options: {{
            responsive: true,
            plugins: {{
                title: {{
                    display: true,
                    text: 'Kills vs Losses Trend',
                    color: '#ffffff'
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: 'ISK (in Billions)',
                        color: '#ffffff'
                    }},
                    ticks: {{
                        callback: function(value) {{
                            return (value / 1e9).toFixed(2) + 'B';
                        }}
                    }}
                }}
            }}
        }}
    }});
    
    // Chart 3: Top Corporation Pilots
    const pilotCtx = document.getElementById('pilotChart').getContext('2d');
    new Chart(pilotCtx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(pilot_names)},
            datasets: [
                {{
                    label: 'Kill Count',
                    data: {json.dumps(pilot_ships)},
                    backgroundColor: 'rgba(100, 149, 237, 0.7)',
                    borderColor: 'rgba(100, 149, 237, 1)',
                    borderWidth: 1,
                    order: 2,
                    yAxisID: 'y'
                }},
                {{
                    label: 'ISK Destroyed',
                    data: {json.dumps(pilot_isk)},
                    type: 'line',
                    borderColor: 'rgba(112, 128, 144, 1)',
                    backgroundColor: 'rgba(112, 128, 144, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.4,
                    order: 1,
                    yAxisID: 'y1',
                    pointRadius: 5
                }}
            ]
        }},
        options: {{
            responsive: true,
            plugins: {{
                title: {{
                    display: true,
                    text: 'Top Corporation Pilots',
                    color: '#ffffff'
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    position: 'left',
                    title: {{
                        display: true,
                        text: 'Kill Count',
                        color: '#ffffff'
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
                        text: 'ISK Destroyed (in Billions)',
                        color: '#ffffff'
                    }},
                    ticks: {{
                        callback: function(value) {{
                            return (value / 1e9).toFixed(2) + 'B';
                        }}
                    }}
                }}
            }},
            animation: {{
                duration: 1500,
                easing: 'easeOutBounce'
            }},
            hover: {{
                mode: 'nearest',
                intersect: true
            }}
        }}
    }});
    
    // Chart 4: Kill Distribution by Hour
    const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
    new Chart(hourlyCtx, {{
        type: 'bar',
        data: {{
            labels: {json.dumps(hours)},
            datasets: [{{
                label: 'Kills per Hour',
                data: {json.dumps(kills_per_hour)},
                backgroundColor: 'rgba(119, 136, 153, 0.7)',
                borderColor: 'rgba(119, 136, 153, 1)',
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            plugins: {{
                title: {{
                    display: true,
                    text: 'Kill Distribution by Hour',
                    color: '#ffffff'
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    title: {{
                        display: true,
                        text: 'Kill Count',
                        color: '#ffffff'
                    }}
                }}
            }}
        }}
    }});
    """

def generate_html_sections(daily_data, shiptype_data, pilot_data, additional_stats):
    # Add a "Back to Index" link at the bottom of the report page
    return f"""
        <!-- Chart 1: Daily Statistics -->
        <h2>Daily Statistics</h2>
        <div class="chart-container">
            <canvas id="dailyChart"></canvas>
        </div>
        
        <!-- Chart 2: Kills vs Losses Value -->
        <h2>Kills vs Losses Value</h2>
        <div class="chart-container">
            <canvas id="valueChart"></canvas>
        </div>
        
        <!-- KPI: Top 20 Ship Types -->
        <h2>Top 20 Ship Types</h2>
        <div class="kpi-container">
            {generate_shiptype_html(shiptype_data)}
        </div>
        
        <!-- Chart 3: Top Corporation Pilots -->
        <h2>Top Corporation Pilots</h2>
        <div class="chart-container pilot-chart-container">
            <canvas id="pilotChart"></canvas>
        </div>
        
        <!-- Additional Statistics -->
        <h2>Additional Statistics</h2>
        <div class="stats-summary">
            {generate_additional_stats_html(additional_stats, additional_stats_peak)}
        </div>
        
        <!-- Chart 4: Kill Distribution by Hour -->
        <h2>Kill Distribution by Hour</h2>
        <div class="chart-container">
            <canvas id="hourlyChart"></canvas>
        </div>
        
        <!-- Back to Index Link -->
        <p style="text-align: center; margin-top: 2rem;">
            <a href="index.html" style="color: var(--accent); text-decoration: none;">Back to Index</a>
        </p>
    """

def update_index():
    """Generate or update the html/index.html file with links to all reports (since January 2025)"""
    report_files = glob.glob(os.path.join(OUTPUT_DIR, "2025*.html"))
    # Exclude index.html if present
    report_files = [f for f in report_files if os.path.basename(f) != "index.html"]
    report_files.sort()

    # Generate list of links
    links = ""
    for file in report_files:
        base = os.path.basename(file)
        # Display the link as "YYYY-MM"
        year = base[:4]
        month = base[4:6]
        display_name = f"{year}-{month}"
        links += f'<li><a href="{base}">{display_name}</a></li>\n'

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Killmail Reports Index</title>
    {get_css_styles()}
    <style>
        /* Specific styles for the index page */
        ul.report-list {{
            list-style: none;
            padding: 0;
        }}
        ul.report-list li {{
            margin: 0.5rem 0;
            font-size: 1.2rem;
        }}
        ul.report-list li a {{
            color: var(--accent);
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Killmail Reports Index (Since January 2025)</h2>
        <ul class="report-list">
            {links}
        </ul>
    </div>
</body>
</html>
"""
    index_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    logging.info(f"Index updated: {index_path}")

def generate_report(start_date, end_date, corporation):
    with DatabaseConnection() as db:
        # Retrieve data for the report month
        daily_data = get_daily_stats(db, start_date, end_date)
        shiptype_data = get_ship_types(db, start_date, end_date)
        pilot_data = get_top_corp_pilots(db, start_date, end_date, corporation)
        additional_stats = get_additional_stats(db, start_date, end_date, corporation)
        peak_hour = get_peak_hour(db, start_date, end_date)
        kills_by_hour = get_kills_distribution_by_hour(db, start_date, end_date)

        # Prepare chart data
        days = [row['day'].strftime('%Y-%m-%d') for row in daily_data]
        kills_value = [float(row['value_destroyed']) for row in daily_data]
        losses_value = [float(row['value_lost']) for row in daily_data]
        kill_count = [int(row['kill_count']) for row in daily_data]

        # Data for Top Corporation Pilots
        pilot_names = [row['pilot_name'] for row in pilot_data]
        pilot_ships = [int(row['nb_kills']) for row in pilot_data]
        pilot_isk = [float(row['isk_destroyed']) for row in pilot_data]

        # Data for Kill Distribution by Hour
        hour_data = {int(row['hour']): int(row['kill_count']) for row in kills_by_hour}
        hours = list(range(24))
        kills_per_hour = [hour_data.get(h, 0) for h in hours]

        # Set global variable for additional stats peak hour
        global additional_stats_peak
        additional_stats_peak = peak_hour

        # Report filename in format "YYYYMM.html"
        report_filename = f"{start_date[:4]}{start_date[5:7]}.html"
        output_path = os.path.join(OUTPUT_DIR, report_filename)

        # Build the HTML content for the report, including a link back to index.html
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Killmail Report {start_date} to {end_date}</title>
    {get_css_styles()}
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        {generate_html_sections(daily_data, shiptype_data, pilot_data, additional_stats)}
    </div>
    <script>
        {generate_javascript(days, kills_value, losses_value, kill_count, pilot_names, pilot_ships, pilot_isk, hours, kills_per_hour)}
    </script>
</body>
</html>
"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logging.info(f"Report generated successfully: {output_path}")

        # Update the index page with all reports
        update_index()
        return output_path

def main():
    parser = argparse.ArgumentParser(description="Monthly killmail report generation")
    parser.add_argument("--year", type=int, default=2025, help="Year of the report (default: 2025)")
    parser.add_argument("--month", type=int, default=1, help="Month of the report (default: 1 - January)")
    parser.add_argument("--corporation", type=str, default="Goat to Go", help="Name of the corporation (default: 'Goat to Go')")
    args = parser.parse_args()

    if not 1 <= args.month <= 12:
        parser.error("Month must be between 1 and 12")

    start_date = f"{args.year}-{args.month:02d}-01"
    _, last_day = calendar.monthrange(args.year, args.month)
    end_date = f"{args.year}-{args.month:02d}-{last_day:02d}"

    try:
        report_path = generate_report(start_date, end_date, args.corporation)
        print(f"Report generated successfully: {report_path}")
    except Exception as e:
        logging.error(f"Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()

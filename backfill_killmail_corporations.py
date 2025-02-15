import os
import time
import logging
import psycopg2
from psycopg2 import extras
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

class DatabaseConnection:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        self.cur = self.conn.cursor(cursor_factory=extras.DictCursor)
        logging.info("Connexion à la base de données établie.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cur.close()
        self.conn.close()
        logging.info("Connexion à la base de données fermée.")

    def get_or_create_corporation(self, corporation_name):
        try:
            self.cur.execute("""
                INSERT INTO corporations (corporation_name)
                VALUES (%s)
                ON CONFLICT (corporation_name) DO UPDATE SET corporation_name = EXCLUDED.corporation_name
                RETURNING corporation_id;
            """, (corporation_name,))
            self.conn.commit()
            return self.cur.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Erreur dans get_or_create_corporation: {e}")
            raise

    def update_killmail_corporation(self, killmail_id, corp_db_id):
        try:
            self.cur.execute("""
                UPDATE killmails SET victim_corporation_id = %s WHERE killmail_id = %s
            """, (corp_db_id, killmail_id))
            self.conn.commit()
            logging.info(f"Killmail {killmail_id} mis à jour avec corporation_id {corp_db_id}")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Erreur lors de la mise à jour du killmail {killmail_id}: {e}")
            raise

    def get_killmails_without_corporation(self):
        try:
            self.cur.execute("""
                SELECT killmail_id, kill_hash FROM killmails WHERE victim_corporation_id IS NULL
            """)
            return self.cur.fetchall()
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des killmails sans corporation: {e}")
            raise

def get_url(url: str, headers: dict, max_retries: int = 3, timeout: int = 30):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = int(response.headers.get("Retry-After", 60))
                logging.warning(f"Rate limit atteint pour {url}, attente de {wait_time} secondes.")
                time.sleep(wait_time)
            else:
                logging.error(f"Erreur HTTP {response.status_code} pour {url}")
                time.sleep(5)
        except Exception as e:
            logging.error(f"Exception lors de l'accès à {url}: {e}")
            time.sleep(5)
    return None

def get_kill_detail(killmail_id, kill_hash, headers):
    url = f"https://esi.evetech.net/latest/killmails/{killmail_id}/{kill_hash}/?datasource=tranquility"
    return get_url(url, headers)

def get_entity_info(entity_id, entity_type, headers):
    if not entity_id:
        return "Unknown"
    url = f"https://esi.evetech.net/latest/{entity_type}/{entity_id}/?datasource=tranquility"
    data = get_url(url, headers)
    if data:
        return data.get("name", "Unknown")
    return "Unknown"

def main():
    headers = {
        "User-Agent": "EVE Application telynor@gmail.com",
        "Accept": "application/json"
    }
    with DatabaseConnection() as db:
        killmails = db.get_killmails_without_corporation()
        logging.info(f"{len(killmails)} killmails à mettre à jour avec la corporation.")
        for row in killmails:
            killmail_id = row["killmail_id"]
            kill_hash = row["kill_hash"]
            detail = get_kill_detail(killmail_id, kill_hash, headers)
            if detail and "victim" in detail:
                victim = detail["victim"]
                corp_id = victim.get("corporation_id")
                if corp_id:
                    corp_name = get_entity_info(corp_id, "corporations", headers)
                else:
                    corp_name = "Unknown"
                corp_db_id = db.get_or_create_corporation(corp_name)
                db.update_killmail_corporation(killmail_id, corp_db_id)
            else:
                logging.warning(f"Impossible de récupérer les détails du killmail {killmail_id}")
            time.sleep(1)  # Pour respecter l'API

if __name__ == "__main__":
    main()

import os
import time
import logging
import psycopg2
from psycopg2 import extras
import requests
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration du logging
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

    def get_killmails_without_attackers(self):
        """
        Récupère les killmails qui n'ont pas encore d'enregistrements dans killmail_attackers.
        """
        try:
            self.cur.execute("""
                SELECT k.killmail_id, k.kill_hash 
                FROM killmails k
                WHERE NOT EXISTS (
                    SELECT 1 FROM killmail_attackers ka WHERE ka.killmail_id = k.killmail_id
                )
            """)
            return self.cur.fetchall()
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des killmails sans attaquants: {e}")
            raise

    def get_or_create_corporation(self, corp_name):
        """
        Insère la corporation si elle n'existe pas et retourne son identifiant.
        """
        try:
            self.cur.execute("""
                INSERT INTO corporations (corporation_name)
                VALUES (%s)
                ON CONFLICT (corporation_name) DO UPDATE SET corporation_name = EXCLUDED.corporation_name
                RETURNING corporation_id;
            """, (corp_name,))
            self.conn.commit()
            return self.cur.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Erreur dans get_or_create_corporation: {e}")
            raise

    def get_or_create_pilot(self, pilot_name):
        """
        Insère le pilote s'il n'existe pas et retourne son identifiant.
        """
        try:
            self.cur.execute("""
                INSERT INTO pilots (pilot_name)
                VALUES (%s)
                ON CONFLICT (pilot_name) DO NOTHING
                RETURNING pilot_id;
            """, (pilot_name,))
            res = self.cur.fetchone()
            if res:
                self.conn.commit()
                return res[0]
            else:
                # Si le pilote existe déjà, on le récupère
                self.cur.execute("SELECT pilot_id FROM pilots WHERE pilot_name = %s", (pilot_name,))
                result = self.cur.fetchone()[0]
                return result
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Erreur dans get_or_create_pilot: {e}")
            raise

    def insert_killmail_attacker(self, killmail_id, pilot_id, pilot_name, attacker_corporation_id, final_blow, damage_done):
        try:
            self.cur.execute("""
                INSERT INTO killmail_attackers (
                    killmail_id, pilot_id, pilot_name, attacker_corporation_id, final_blow, damage_done
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (killmail_id, pilot_id, pilot_name, attacker_corporation_id, final_blow, damage_done))
            self.conn.commit()
            logging.info(f"Attaquant '{pilot_name}' pour killmail {killmail_id} inséré avec succès.")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Erreur lors de l'insertion de l'attaquant pour killmail {killmail_id}: {e}")
            raise


def get_url(url: str, headers: dict, max_retries: int = 3, timeout: int = 30):
    """
    Effectue une requête GET avec gestion de la limite de taux.
    """
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

def get_entity_info(entity_id, entity_type, headers):
    """
    Récupère le nom de l'entité (pilote ou corporation) à partir de l'API ESI.
    """
    if not entity_id:
        return "Unknown"
    url = f"https://esi.evetech.net/latest/{entity_type}/{entity_id}/?datasource=tranquility"
    data = get_url(url, headers)
    if data:
        return data.get("name", "Unknown")
    return "Unknown"

def backfill_attackers():
    headers = {
        "User-Agent": "EVE Application telynor@gmail.com",
        "Accept": "application/json"
    }
    with DatabaseConnection() as db:
        killmails = db.get_killmails_without_attackers()
        logging.info(f"{len(killmails)} killmails à mettre à jour avec les attaquants.")
        for killmail in killmails:
            killmail_id = killmail["killmail_id"]
            kill_hash = killmail["kill_hash"]
            logging.info(f"Traitement du killmail {killmail_id}")

            # Récupération des détails du killmail via l'API ESI
            url = f"https://esi.evetech.net/latest/killmails/{killmail_id}/{kill_hash}/?datasource=tranquility"
            kill_detail = get_url(url, headers)
            if not kill_detail:
                logging.warning(f"Impossible de récupérer les détails pour le killmail {killmail_id}")
                continue

            attackers = kill_detail.get("attackers", [])
            for attacker in attackers:
                # Récupération du nom du pilote attaquant
                attacker_character_id = attacker.get("character_id")
                if attacker_character_id:
                    attacker_name = get_entity_info(attacker_character_id, "characters", headers)
                    pilot_id = db.get_or_create_pilot(attacker_name)
                else:
                    attacker_name = "Unknown"
                    pilot_id = None

                # Récupération de la corporation de l'attaquant
                attacker_corp_id = attacker.get("corporation_id")
                if attacker_corp_id:
                    corp_name = get_entity_info(attacker_corp_id, "corporations", headers)
                else:
                    corp_name = "Unknown"
                attacker_corp_db_id = db.get_or_create_corporation(corp_name)

                final_blow = attacker.get("final_blow", False)
                damage_done = attacker.get("damage_done", 0)

                # Insertion de l'attaquant pour ce killmail
                db.insert_killmail_attacker(
                    killmail_id=killmail_id,
                    pilot_id=pilot_id,
                    pilot_name=attacker_name,
                    attacker_corporation_id=attacker_corp_db_id,
                    final_blow=final_blow,
                    damage_done=damage_done
                )
                time.sleep(0.5)  # Respect de l'API ESI

            time.sleep(1)  # Petite pause entre les killmails

if __name__ == "__main__":
    backfill_attackers()

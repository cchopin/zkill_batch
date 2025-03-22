#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import extras
import logging
from typing import Optional, List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

# Create a log filename based on the current date and time
log_filename = os.path.join("logs", f"killmail_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging with a file handler (per execution) and a stream handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logging.info(f"Script started. Logging to {log_filename}")

class DatabaseConnection:
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        self.cur = self.conn.cursor(cursor_factory=extras.DictCursor)
        logging.info("Database connection established successfully")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cur.close()
        self.conn.close()
        logging.info("Database connection closed")

    def get_or_create_system(self, system_name):
        try:
            self.cur.execute("""
                INSERT INTO systems (system_name)
                VALUES (%s)
                ON CONFLICT (system_name) DO UPDATE SET system_name = EXCLUDED.system_name
                RETURNING system_id;
            """, (system_name,))
            self.conn.commit()
            return self.cur.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error in get_or_create_system: {e}")
            raise

    def get_or_create_ship_type(self, type_name):
        try:
            self.cur.execute("""
                INSERT INTO ship_types (type_name)
                VALUES (%s)
                ON CONFLICT (type_name) DO UPDATE SET type_name = EXCLUDED.type_name
                RETURNING ship_type_id;
            """, (type_name,))
            self.conn.commit()
            return self.cur.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error in get_or_create_ship_type: {e}")
            raise

    def get_or_create_ship(self, ship_name, ship_type_id):
        try:
            self.cur.execute("""
                INSERT INTO ships (ship_name, ship_type_id)
                VALUES (%s, %s)
                ON CONFLICT (ship_name) DO UPDATE SET ship_type_id = EXCLUDED.ship_type_id
                RETURNING ship_id;
            """, (ship_name, ship_type_id))
            self.conn.commit()
            return self.cur.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error in get_or_create_ship: {e}")
            raise

    def get_or_create_pilot(self, pilot_name):
        try:
            self.cur.execute("""
                INSERT INTO pilots (pilot_name)
                VALUES (%s)
                ON CONFLICT (pilot_name) DO UPDATE SET pilot_name = EXCLUDED.pilot_name
                RETURNING pilot_id;
            """, (pilot_name,))
            self.conn.commit()
            return self.cur.fetchone()[0]
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error in get_or_create_pilot: {e}")
            raise

    def get_or_create_corporation(self, corp_name):
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
            logging.error(f"Error in get_or_create_corporation: {e}")
            raise

    def kill_exists(self, killmail_id, kill_hash):
        try:
            self.cur.execute("""
                SELECT 1 FROM killmails
                WHERE killmail_id = %s OR kill_hash = %s
            """, (killmail_id, kill_hash))
            return self.cur.fetchone() is not None
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error checking kill existence: {e}")
            raise

    def insert_killmail(self, killmail_data):
        try:
            if self.kill_exists(killmail_data['killmail_id'], killmail_data['kill_hash']):
                logging.info(f"Kill {killmail_data['killmail_id']} already in database, skipping")
                return None

            self.cur.execute("""
                INSERT INTO killmails (
                    killmail_id, kill_hash, kill_datetime, system_id,
                    pilot_id, ship_id, value, kill_type, victim_corporation_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (killmail_id) DO NOTHING
                RETURNING killmail_id;
            """, (
                killmail_data['killmail_id'],
                killmail_data['kill_hash'],
                killmail_data['datetime'],
                killmail_data['system_id'],
                killmail_data['pilot_id'],
                killmail_data['ship_id'],
                killmail_data['value'],
                killmail_data['kill_type'],
                killmail_data['victim_corporation_id']
            ))
            self.conn.commit()
            result = self.cur.fetchone()
            if result:
                logging.info(f"Successfully inserted killmail {killmail_data['killmail_id']}")
                return result
            return None  # No insertion due to conflict
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error inserting killmail: {e}")
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
            logging.info(f"Successfully inserted attacker '{pilot_name}' for killmail {killmail_id}")
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Error inserting killmail attacker for killmail {killmail_id}: {e}")
            raise

def get_url(url: str, headers: dict, max_retries: int = 3, timeout: int = 30) -> Optional[dict]:
    for attempt in range(max_retries):
        try:
            logging.debug(f"Attempting request to {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=headers, timeout=timeout)

            # Get ESI limits
            esi_remain = int(response.headers.get('X-Esi-Error-Limit-Remain', 100))
            esi_reset = int(response.headers.get('X-Esi-Error-Limit-Reset', 0))

            if esi_remain < 20:  # Safety threshold
                wait_time = min(esi_reset + 1, 30)
                logging.warning(f"ESI error limit low ({esi_remain}), waiting {wait_time} seconds")
                time.sleep(wait_time)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = int(response.headers.get('Retry-After', 60))
                wait_time = min(wait_time, 300)
                logging.warning(f"Rate limited on URL: {url}")
                logging.warning(f"Response headers: {dict(response.headers)}")
                logging.warning(f"Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            elif response.status_code == 404:
                logging.warning(f"Resource not found at URL: {url}")
                logging.warning(f"Response status: {response.status_code}")
                logging.warning(f"Response headers: {dict(response.headers)}")
                logging.warning(f"Response content: {response.text[:500]}")
                return None
            else:
                logging.error(f"API request failed for URL: {url}")
                logging.error(f"Response status: {response.status_code}")
                logging.error(f"Response headers: {dict(response.headers)}")
                logging.error(f"Response content: {response.text[:500]}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for URL: {url}")
            logging.error(f"Exception type: {type(e).__name__}")
            logging.error(f"Exception details: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            return None
        except Exception as e:
            logging.error(f"Unexpected error for URL: {url}")
            logging.error(f"Exception type: {type(e).__name__}")
            logging.error(f"Exception details: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            return None

    logging.error(f"All {max_retries} attempts failed for URL: {url}")
    return None

def get_entity_info(entity_id, entity_type, headers):
    if not entity_id:
        return "Unknown"
    try:
        url = f"https://esi.evetech.net/latest/{entity_type}/{entity_id}/?datasource=tranquility"
        response = get_url(url, headers)
        return response.get('name', 'Unknown') if response else "Unknown"
    except:
        return "Unknown"

def get_ship_type(ship_type_id, headers):
    try:
        url = f"https://esi.evetech.net/latest/universe/types/{ship_type_id}/?datasource=tranquility"
        response = get_url(url, headers)
        group_id = response.get('group_id') if response else None

        if group_id:
            group_url = f"https://esi.evetech.net/latest/universe/groups/{group_id}/?datasource=tranquility"
            group_response = get_url(group_url, headers)
            return group_response.get('name', 'Unknown') if group_response else "Unknown"
        return "Unknown"
    except:
        return "Unknown"

def get_latest_killmail_date(db: DatabaseConnection) -> datetime:
    try:
        db.cur.execute("""
            SELECT kill_datetime
            FROM killmails
            ORDER BY kill_datetime DESC
            LIMIT 1
        """)
        result = db.cur.fetchone()
        if result:
            latest_date = result[0]
            logging.info(f"Latest kill in database: {latest_date}")
            return latest_date
        else:
            default_date = datetime(2025, 1, 1, 0, 0, 0)
            logging.info(f"No kills in database, starting from {default_date}")
            return default_date
    except Exception as e:
        logging.error(f"Error getting latest killmail date: {e}")
        raise

def get_all_kills_for_page(corporation_id: str, page: int, headers: dict) -> Optional[List[Dict]]:
    url = f"https://zkillboard.com/api/corporationID/{corporation_id}/page/{page}/"
    logging.info(f"Requesting kills from URL: {url}")

    response = get_url(url, headers)

    if response:
        logging.info(f"Received {len(response)} kills from zKillboard")
        return response
    else:
        logging.warning(f"No response received from zKillboard for page {page}")
        return None

def process_single_kill(kill, kill_detail, corporation_id, db: DatabaseConnection, headers: dict):
    try:
        kill_date = datetime.strptime(kill_detail['killmail_time'], "%Y-%m-%dT%H:%M:%SZ")
        logging.info(f"Processing kill {kill['killmail_id']} from {kill_date}")

        # Process kill information
        ship_type_id = kill_detail['victim']['ship_type_id']
        system_id = kill_detail['solar_system_id']
        victim_id = kill_detail['victim'].get('character_id')
        victim_corp_raw = kill_detail['victim'].get('corporation_id')
        # Compare as string because API corporation_id and the provided corporation_id might differ in type
        is_kill = 'KILL' if str(victim_corp_raw) != corporation_id else 'LOSS'

        # Get and insert reference data
        system_name = get_entity_info(system_id, 'universe/systems', headers)
        system_db_id = db.get_or_create_system(system_name)

        ship_name = get_entity_info(ship_type_id, 'universe/types', headers)
        ship_type_name = get_ship_type(ship_type_id, headers)
        ship_type_db_id = db.get_or_create_ship_type(ship_type_name)
        ship_db_id = db.get_or_create_ship(ship_name, ship_type_db_id)

        victim_name = get_entity_info(victim_id, 'characters', headers) if victim_id else "Unknown"
        pilot_db_id = db.get_or_create_pilot(victim_name)

        # Retrieve and insert the victim corporation
        victim_corp_name = get_entity_info(victim_corp_raw, 'corporations', headers) if victim_corp_raw else "Unknown"
        victim_corp_db_id = db.get_or_create_corporation(victim_corp_name)

        # Insert killmail with victim's corporation
        killmail_data = {
            'killmail_id': kill['killmail_id'],
            'kill_hash': kill['zkb']['hash'],
            'datetime': kill_date,
            'system_id': system_db_id,
            'pilot_id': pilot_db_id,
            'ship_id': ship_db_id,
            'value': kill['zkb']['totalValue'],
            'kill_type': is_kill,
            'victim_corporation_id': victim_corp_db_id
        }

        result = db.insert_killmail(killmail_data)
        if not result:
            logging.info(f"Killmail {kill['killmail_id']} already exists, skipping attackers processing")
            return False

        # Process attackers for this killmail
        attackers = kill_detail.get('attackers', [])
        for attacker in attackers:
            attacker_character_id = attacker.get('character_id')
            if attacker_character_id:
                attacker_name = get_entity_info(attacker_character_id, 'characters', headers)
                attacker_pilot_id = db.get_or_create_pilot(attacker_name)
            else:
                attacker_name = "Unknown"
                attacker_pilot_id = None

            attacker_corp_raw = attacker.get('corporation_id')
            if attacker_corp_raw:
                attacker_corp_name = get_entity_info(attacker_corp_raw, 'corporations', headers)
            else:
                attacker_corp_name = "Unknown"
            attacker_corp_db_id = db.get_or_create_corporation(attacker_corp_name)

            final_blow = attacker.get('final_blow', False)
            damage_done = attacker.get('damage_done', 0)

            db.insert_killmail_attacker(
                killmail_id=kill['killmail_id'],
                pilot_id=attacker_pilot_id,
                pilot_name=attacker_name,
                attacker_corporation_id=attacker_corp_db_id,
                final_blow=final_blow,
                damage_done=damage_done
            )
            time.sleep(0.5)  # Small pause to respect API limits

        logging.info(f"Successfully processed killmail {kill['killmail_id']}")
        return True

    except Exception as e:
        logging.error(f"Error processing kill {kill.get('killmail_id')}: {str(e)}")
        return False

def get_oldest_kill_date(db: DatabaseConnection) -> Optional[datetime]:
    try:
        db.cur.execute("""
            SELECT kill_datetime
            FROM killmails
            ORDER BY kill_datetime ASC
            LIMIT 1
        """)
        result = db.cur.fetchone()
        if result:
            logging.info(f"Oldest kill in database: {result[0]}")
            return result[0]
        return None
    except Exception as e:
        logging.error(f"Error getting oldest killmail date: {e}")
        raise

def get_newest_kill_date(db: DatabaseConnection) -> Optional[datetime]:
    try:
        db.cur.execute("""
            SELECT kill_datetime
            FROM killmails
            ORDER BY kill_datetime DESC
            LIMIT 1
        """)
        result = db.cur.fetchone()
        if result:
            logging.info(f"Newest kill in database: {result[0]}")
            return result[0]
        return None
    except Exception as e:
        logging.error(f"Error getting newest killmail date: {e}")
        raise

def process_killmails_batch(db: DatabaseConnection, headers: dict, corporation_id: str):
    logging.info("Starting batch processing of killmails")

    current_page = 1
    total_processed = 0
    max_pages = 10  # Toujours traiter 10 pages maximum

    # Délai entre les requêtes
    base_delay = 2

    while current_page <= max_pages:
        logging.info(f"Processing page {current_page}")

        # Délai progressif
        current_delay = base_delay + (current_page % 3)
        time.sleep(current_delay)

        kills = get_all_kills_for_page(corporation_id, current_page, headers)

        if not kills or kills is None:
            logging.info("No more kills available")
            break

        kills_processed_this_page = 0

        for kill in kills:
            try:
                if not isinstance(kill, dict):
                    logging.warning(f"Invalid kill data format: {kill}")
                    continue

                if 'error' in kill:
                    logging.warning(f"Error in kill data: {kill['error']}")
                    continue

                killmail_id = kill.get('killmail_id')
                kill_hash = kill.get('zkb', {}).get('hash')

                if not killmail_id or not kill_hash:
                    logging.warning("Missing killmail_id or hash")
                    continue

                # Vérifier si le kill existe déjà en base
                if db.kill_exists(killmail_id, kill_hash):
                    logging.info(f"Kill {killmail_id} already exists in database, skipping")
                    continue

                # Récupérer les détails du kill
                kill_detail = get_url(
                    f"https://esi.evetech.net/latest/killmails/{killmail_id}/{kill_hash}/?datasource=tranquility",
                    headers
                )

                if not kill_detail:
                    logging.warning(f"Could not get details for kill {killmail_id}")
                    continue

                if process_single_kill(kill, kill_detail, corporation_id, db, headers):
                    total_processed += 1
                    kills_processed_this_page += 1

                time.sleep(1)  # Respect API rate limits

            except Exception as e:
                logging.error(f"Error processing kill: {str(e)}")
                logging.error(f"Kill data: {json.dumps(kill, indent=2)}")
                continue

        logging.info(f"Processed {kills_processed_this_page} new kills on page {current_page}")

        current_page += 1
        time.sleep(base_delay)

    logging.info(f"Batch processing complete. Total new kills processed: {total_processed}")
    return total_processed

def main():
    logging.info("Starting killmail processing script")

    headers = {
        'User-Agent': 'EVE Corp Killmail Tracker - telynor@gmail.com',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    corporation_id = os.getenv('CORPORATION_ID', "98730717")

    try:
        with DatabaseConnection() as db:
            logging.info("Successfully connected to database")
            process_killmails_batch(db, headers, corporation_id)
            logging.info("Killmail processing completed successfully")

    except Exception as e:
        logging.error(f"Error in main execution: {e}")
        raise

if __name__ == "__main__":
    try:
        logging.info("=== Script Starting ===")
        main()
        logging.info("=== Script Completed Successfully ===")
    except Exception as e:
        logging.error(f"=== Script Failed: {str(e)} ===")
        raise

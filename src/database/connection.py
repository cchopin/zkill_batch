"""Database connection module."""
import psycopg2
from psycopg2.extras import DictCursor
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConnection:
    """Handle database connection."""

    def __init__(self):
        """Initialize connection parameters."""
        self.conn = None
        self.cur = None
        self._conn_params = {
            'dbname': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT')
        }

    def connect(self):
        """Establish database connection."""
        try:
            # Create connection
            self.conn = psycopg2.connect(**self._conn_params)
            # Create cursor with dictionary factory
            self.cur = self.conn.cursor(cursor_factory=DictCursor)
            logging.info("Database connection established")
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            raise

    def disconnect(self):
        """Close database connection."""
        try:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()
                logging.info("Database connection closed")
        except Exception as e:
            logging.error(f"Error closing database connection: {e}")
            raise

    def __enter__(self):
        """Context manager entry point."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.disconnect()
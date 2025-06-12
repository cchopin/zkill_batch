"""System repository module."""
from typing import Optional
import logging
from src.database.repositories.base_repository import BaseRepository
from src.models.system import System

class SystemRepository(BaseRepository[System]):
    """Repository for handling system-related database operations."""

    def get_by_name(self, system_name: str) -> Optional[System]:
        """
        Retrieve a system by its name.
        
        Args:
            system_name (str): Name of the system
            
        Returns:
            Optional[System]: System instance if found
        """
        query = "SELECT system_id, system_name FROM systems WHERE system_name = %s"
        try:
            result = self.execute_query_single(query, (system_name,))
            if result:
                return System(system_id=result['system_id'],
                              system_name=result['system_name'])
            return None
        except Exception as e:
            logging.error(f"Error retrieving system by name: {e}")
            raise

    def create(self, system: System) -> System:
        """
        Create a new system.
        
        Args:
            system (System): System instance to create
            
        Returns:
            System: Created system with ID
        """
        query = """
            INSERT INTO systems (system_name)
            VALUES (%s)
            RETURNING system_id;
        """
        try:
            result = self.execute_query_single(query, (system.system_name,))
            if result:
                system.system_id = result['system_id']
                self.commit()
                return system
            raise Exception("Failed to create system")
        except Exception as e:
            self.rollback()
            logging.error(f"Error creating system: {e}")
            raise

    def get_or_create(self, system_name: str) -> System:
        """
        Get an existing system or create a new one.
        
        Args:
            system_name (str): Name of the system
            
        Returns:
            System: Retrieved or created system
        """
        try:
            existing_system = self.get_by_name(system_name)
            if existing_system:
                return existing_system

            new_system = System.create(system_name)
            return self.create(new_system)
        except Exception as e:
            logging.error(f"Error in get_or_create_system: {e}")
            raise
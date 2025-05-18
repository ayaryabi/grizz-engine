"""
Script to drop the old 'date' and 'timezone' columns from the 'conversations' table.

Run this script *after* confirming that:
1. The migration to conv_day and user_tz was successful.
2. The application is working correctly with the new columns.
3. Your models.py no longer references the old 'date' and 'timezone' columns.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect as sqlalchemy_inspect
from sqlalchemy.orm import sessionmaker
import logging

# Add project root to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_old_columns():
    """Drops the old 'date' and 'timezone' columns from the conversations table."""
    settings = get_settings()
    db_url = settings.DATABASE_URL
    logger.info(f"Connecting to database: {db_url.split('@')[-1] if '@' in db_url else db_url}")

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    inspector = sqlalchemy_inspect(engine)

    table_name = "conversations"
    columns_to_drop = ["date", "timezone"]

    try:
        logger.info(f"Checking for old columns in '{table_name}' table...")
        session.begin()

        existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
        dropped_any = False

        for column_name in columns_to_drop:
            if column_name in existing_columns:
                try:
                    session.execute(text(f"ALTER TABLE {table_name} DROP COLUMN {column_name}"))
                    logger.info(f"Successfully dropped column '{column_name}' from '{table_name}'.")
                    dropped_any = True
                except Exception as e:
                    logger.error(f"Error dropping column '{column_name}': {e}")
            else:
                logger.info(f"Column '{column_name}' does not exist in '{table_name}', no action needed.")

        if dropped_any:
            session.commit()
            logger.info("Old columns dropped successfully!")
        else:
            session.rollback() # Rollback if no changes were made, though not strictly necessary here
            logger.info("No columns needed dropping.")
        
    except Exception as e:
        logger.error(f"Column drop operation failed: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()
        logger.info("Session closed.")

if __name__ == "__main__":
    confirmation = input("Are you sure you want to permanently drop the 'date' and 'timezone' columns from the 'conversations' table? (yes/no): ")
    if confirmation.lower() == 'yes':
        try:
            drop_old_columns()
        except Exception as e:
            logger.error(f"Error during column drop script execution: {e}", exc_info=True)
            sys.exit(1)
    else:
        logger.info("Operation cancelled by user.") 
"""
Script to migrate the existing database schema for conversations.
This will:
1. Create new columns (conv_day, user_tz) if they don't exist.
2. Copy data from old columns (date, timezone) to the new ones.
3. Alter new columns to be NOT NULL.
4. Create a unique index on (user_id, conv_day).

Run this script *after* ensuring your models.py reflects the new schema
(i.e., Conversation model has conv_day and user_tz).
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect as sqlalchemy_inspect  # Renamed inspect to avoid conflict
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError
import logging

# Add project root to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_conversation_schema():
    """Performs the migration of the conversation schema"""
    settings = get_settings()
    
    # Use the correct DATABASE_URL attribute from settings
    db_url = settings.DATABASE_URL 
    logger.info(f"Connecting to database: {db_url.split('@')[-1] if '@' in db_url else db_url}") # Log DB host, not full URL

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    inspector = sqlalchemy_inspect(engine) # Use the renamed import
    
    try:
        logger.info("Starting schema migration for 'conversations' table...")
        session.begin()

        # Get current columns in the conversations table
        existing_columns = [col['name'] for col in inspector.get_columns('conversations')]
        logger.info(f"Existing columns in 'conversations': {existing_columns}")

        # 1. Add conv_day column if it doesn't exist
        if 'conv_day' not in existing_columns:
            session.execute(text("ALTER TABLE conversations ADD COLUMN conv_day DATE"))
            logger.info("Added 'conv_day' (DATE) column to 'conversations' table.")
        else:
            logger.info("'conv_day' column already exists.")

        # 2. Add user_tz column if it doesn't exist
        if 'user_tz' not in existing_columns:
            session.execute(text("ALTER TABLE conversations ADD COLUMN user_tz VARCHAR")) # Add as nullable first
            logger.info("Added 'user_tz' (VARCHAR) column to 'conversations' table.")
        else:
            logger.info("'user_tz' column already exists.")
        
        # 3. Migrate data (only if old columns exist and new ones were just added or are empty)
        # This step assumes 'date' (timestamp) and 'timezone' (varchar) were the old columns
        if 'date' in existing_columns: # Check if old 'date' column exists for data migration
            logger.info("Migrating data from old 'date' and 'timezone' columns to 'conv_day' and 'user_tz'...")
            try:
                # Convert timestamp 'date' to DATE for conv_day
                # Use COALESCE for timezone, defaulting to UTC if null
                session.execute(
                    text('''
                    UPDATE conversations
                    SET 
                        conv_day = CASE 
                                     WHEN date IS NOT NULL THEN CAST(date AS DATE)
                                     ELSE conv_day -- Keep existing if any
                                   END,
                        user_tz = CASE 
                                    WHEN timezone IS NOT NULL THEN timezone
                                    ELSE COALESCE(user_tz, 'UTC') -- Keep existing or default
                                  END
                    WHERE date IS NOT NULL OR timezone IS NOT NULL; 
                    ''')
                )
                logger.info("Data migration step completed.")
            except (OperationalError, ProgrammingError) as e:
                logger.warning(f"Could not migrate all data (perhaps old columns were already removed or types changed): {e}")
        else:
            logger.info("Old 'date' column not found, skipping data migration from it.")

        # 4. Set default for user_tz and make it NOT NULL (if it was added or is nullable)
        # Check if user_tz is nullable
        user_tz_nullable = True # Assume nullable unless proven otherwise
        for col in inspector.get_columns('conversations'):
            if col['name'] == 'user_tz':
                user_tz_nullable = col['nullable']
                break
        
        if user_tz_nullable:
            session.execute(text("UPDATE conversations SET user_tz = 'UTC' WHERE user_tz IS NULL"))
            logger.info("Set default 'UTC' for NULL 'user_tz' values.")
            session.execute(text("ALTER TABLE conversations ALTER COLUMN user_tz SET NOT NULL"))
            logger.info("Altered 'user_tz' column to NOT NULL.")
        else:
            logger.info("'user_tz' column is already NOT NULL.")

        # 5. Make conv_day NOT NULL (if it was added or is nullable)
        conv_day_nullable = True
        for col in inspector.get_columns('conversations'):
            if col['name'] == 'conv_day':
                conv_day_nullable = col['nullable']
                break
        
        if conv_day_nullable:
            # Ensure no NULLs exist before setting NOT NULL, critical for existing data
            # This might require manual intervention if conv_day is NULL for some rows
            # For newly added columns without data migration, this isn't an issue yet
            # If data migration happened, 'date' IS NOT NULL condition should have handled it
            count_null_conv_day = session.execute(text("SELECT COUNT(*) FROM conversations WHERE conv_day IS NULL")).scalar_one_or_none()
            if count_null_conv_day and count_null_conv_day > 0:
                logger.warning(f"{count_null_conv_day} rows have NULL conv_day. Please fix data before setting to NOT NULL.")
                # raise Exception(f"{count_null_conv_day} rows have NULL conv_day. Fix data before setting to NOT NULL.") # Optionally raise
            else:
                session.execute(text("ALTER TABLE conversations ALTER COLUMN conv_day SET NOT NULL"))
                logger.info("Altered 'conv_day' column to NOT NULL.")
        else:
            logger.info("'conv_day' column is already NOT NULL.")
            
        # 6. Create the unique index
        index_name = 'idx_conversation_user_day'
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('conversations')]
        if index_name not in existing_indexes:
            try:
                session.execute(
                    text(f"CREATE UNIQUE INDEX {index_name} ON conversations (user_id, conv_day)")
                )
                logger.info(f"Created unique index '{index_name}' on (user_id, conv_day).")
            except (OperationalError, ProgrammingError) as e:
                # This can happen if there's duplicate data violating the unique constraint
                logger.error(f"Failed to create unique index '{index_name}'. Possible duplicate (user_id, conv_day) data. Error: {e}")
                logger.error("Please check for duplicate entries for (user_id, conv_day) pairs and resolve them manually.")

        else:
            logger.info(f"Index '{index_name}' already exists.")
        
        session.commit()
        logger.info("Migration successful!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()
        logger.info("Session closed.")

if __name__ == "__main__":
    try:
        migrate_conversation_schema()
    except Exception as e:
        logger.error(f"Error during migration script execution: {e}", exc_info=True)
        sys.exit(1) 
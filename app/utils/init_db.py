"""
MongoDB database initialization utility.
Handles connection setup and index creation separately from service initialization.
"""

import os
import logging
from pymongo import MongoClient
from pymongo.errors import OperationFailure, ConnectionFailure

logger = logging.getLogger(__name__)


def init_mongodb():
    """
    Initialize MongoDB connection and create necessary indexes.
    This should be called during application startup.

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Get connection string from environment
        connection_string = os.getenv("MONGO_DB_URI")

        if not connection_string:
            logger.warning(
                "MONGO_DB_URI not found in environment variables. Using default MongoDB connection."
            )
            connection_string = "mongodb://localhost:27017/"

        logger.info(f"Connecting to MongoDB...")

        # Create client and test connection
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)

        # Test the connection
        client.admin.command("ping")
        logger.info("✅ MongoDB connection successful")

        # Get database name from connection string or use default
        # The connection string format: mongodb://user:pass@host:port/dbname?params
        if "/" in connection_string.split("@")[-1]:
            print(connection_string.split("@"))
            db_name = connection_string.split("@")[-1].split("/")[1].split("?")[0]
        else:
            db_name = "calendar_assistant"

        logger.info(f"Using database: {db_name}")
        db = client[db_name]

        # Create indexes for events collection
        logger.info("Creating indexes for 'events' collection...")
        events = db.events
        events.create_index([("user_id", 1), ("date", 1)])
        events.create_index([("user_id", 1), ("date", 1), ("start_time", 1)])
        logger.info("✅ Events indexes created")

        # Create indexes for reminders collection
        logger.info("Creating indexes for 'reminders' collection...")
        reminders = db.reminders
        reminders.create_index([("user_id", 1), ("reminder_datetime", 1)])
        reminders.create_index([("user_id", 1), ("status", 1)])
        logger.info("✅ Reminders indexes created")

        # Create indexes for messages collection (conversation history)
        logger.info("Creating indexes for 'messages' collection...")
        messages = db.messages
        messages.create_index([("user_id", 1), ("timestamp", -1)])
        logger.info("✅ Messages indexes created")

        logger.info("🎉 MongoDB initialization complete")
        return True

    except ConnectionFailure as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        return False
    except OperationFailure as e:
        logger.error(f"❌ MongoDB operation failed: {e}")
        logger.error(
            "This might be an authentication issue. Check your MONGO_DB_URI credentials."
        )
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during MongoDB initialization: {e}")
        return False


if __name__ == "__main__":
    # Allow running this script directly for testing
    import sys
    from pathlib import Path

    # Add project root to path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from app.utils.load_env import load_env_vars

    load_env_vars()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    success = init_mongodb()
    if success:
        print("\n✅ Database initialization successful!")
    else:
        print("\n❌ Database initialization failed!")

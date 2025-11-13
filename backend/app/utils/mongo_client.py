"""
MongoDB client initialization using Beanie ODM.
Follows best practices for async MongoDB connections.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from bson.codec_options import CodecOptions
from datetime import timezone
import logging

from app.config import MONGO_DB_URI
from app.models.db.calendar_event import CalendarEvent
from app.models.db.reminder import Reminder

logger = logging.getLogger(__name__)


async def init_db(
    max_pool_size: int = 20,
    min_pool_size: int = 5,
    max_idle_time_ms: int = 45000,
    server_selection_timeout_ms: int = 20000,
    connect_timeout_ms: int = 20000,
    socket_timeout_ms: int = 45000,
):
    """
    Initialize Beanie ODM with MongoDB connection.

    Args:
        max_pool_size: Maximum number of connections in the pool
        min_pool_size: Minimum number of connections to maintain
        max_idle_time_ms: Maximum time a connection can be idle
        server_selection_timeout_ms: Timeout for selecting a server
        connect_timeout_ms: Timeout for establishing connection
        socket_timeout_ms: Timeout for socket operations

    Returns:
        None
    """
    # Configure codec options for timezone awareness
    codec_options = CodecOptions(tz_aware=True, tzinfo=timezone.utc)

    # Create client with optimized connection pool settings
    client = AsyncIOMotorClient(
        MONGO_DB_URI,
        maxPoolSize=max_pool_size,
        minPoolSize=min_pool_size,
        maxIdleTimeMS=max_idle_time_ms,
        serverSelectionTimeoutMS=server_selection_timeout_ms,
        connectTimeoutMS=connect_timeout_ms,
        socketTimeoutMS=socket_timeout_ms,
        # Additional performance optimizations
        retryWrites=True,
        retryReads=True,
        w="majority",  # Write concern for durability
        readPreference="primary",  # Only read from primary
        # Connection pool monitoring
        waitQueueTimeoutMS=30000,  # Wait up to 30s for connection from pool
    )

    # Get database with timezone-aware codec options
    database = client.get_default_database().with_options(codec_options=codec_options)

    logger.info("🔗 Initializing Beanie connection to MongoDB...")
    if "example" in MONGO_DB_URI:
        logger.warning("⚠️  Using local MongoDB credentials.")

    logger.info(
        f"📊 MongoDB connection pool: maxPoolSize={max_pool_size}, minPoolSize={min_pool_size}"
    )

    # Initialize Beanie with document models
    await init_beanie(
        database=database,  # type: ignore
        document_models=[
            CalendarEvent,
            Reminder,
        ],
    )

    logger.info("✅ Beanie ODM initialized successfully!")


async def get_mongo_database():
    """
    Get direct access to MongoDB database for raw collection operations.

    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    codec_options = CodecOptions(tz_aware=True, tzinfo=timezone.utc)
    client = AsyncIOMotorClient(MONGO_DB_URI)
    return client.get_default_database().with_options(codec_options=codec_options)

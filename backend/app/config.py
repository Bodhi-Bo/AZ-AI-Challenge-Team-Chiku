"""
Centralized configuration - single source of truth for all environment variables.
All env vars loaded here, validation happens once at import time.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file once at module import
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_ENV_PATH)

# ============================================================================
# OpenAI Configuration
# ============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY must be set in .env file")
OPENAI_API_KEY = OPENAI_API_KEY.strip()

OPENAI_MODEL = os.getenv("OPENAI_MODEL")
if not OPENAI_MODEL:
    raise ValueError("OPENAI_MODEL must be set in .env file")
OPENAI_MODEL = OPENAI_MODEL.strip()

# ============================================================================
# MongoDB Configuration
# ============================================================================
MONGO_DB_URI = os.getenv("MONGO_DB_URI")
if not MONGO_DB_URI:
    raise ValueError("MONGO_DB_URI must be set in .env file")
MONGO_DB_URI = MONGO_DB_URI.strip()

# ============================================================================
# Redis Configuration
# ============================================================================
REDIS_HOST = os.getenv("REDIS_HOST")
if not REDIS_HOST:
    raise ValueError("REDIS_HOST must be set in .env file")
REDIS_HOST = REDIS_HOST.strip()

REDIS_PORT = os.getenv("REDIS_PORT")
if not REDIS_PORT:
    raise ValueError("REDIS_PORT must be set in .env file")
REDIS_PORT = int(REDIS_PORT)  # Ensure PORT is an integer

# ============================================================================
# OpenAI Key Pool Configuration
# ============================================================================
KEYPOOL_PREFIX = os.getenv("KEYPOOL_PREFIX")
if not KEYPOOL_PREFIX:
    raise ValueError("KEYPOOL_PREFIX must be set in .env file")

LOCK_EXPIRY = os.getenv("LOCK_EXPIRY")
if not LOCK_EXPIRY:
    raise ValueError("LOCK_EXPIRY must be set in .env file")

LOCK_EXPIRY = int(LOCK_EXPIRY)  # Ensure it's an integer
LOCK_EXPIRY_FLOAT = float(LOCK_EXPIRY)  # For backward compatibility

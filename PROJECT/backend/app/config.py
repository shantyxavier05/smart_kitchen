import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in project root (PROJECT/) or current directory
project_root = Path(__file__).resolve().parent.parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Fallback to current directory
    load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# JWT Configuration
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "your-secret-key-change-in-production-use-openssl-rand-hex-32"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR}/app.db"
)

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"  # Default to false - use LLM by default

# Opik Configuration
OPIK_API_KEY = os.getenv("OPIK_API_KEY", None)
OPIK_PROJECT_NAME = os.getenv("OPIK_PROJECT_NAME", "smart-kitchen-assistant")
OPIK_WORKSPACE = os.getenv("OPIK_WORKSPACE", "default")
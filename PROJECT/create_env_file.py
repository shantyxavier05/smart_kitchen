"""
Script to create .env file for PROJECT
Run this script to create the .env file in the project root
"""
import os
from pathlib import Path

def create_env_file():
    """Create .env file with required environment variables"""
    # Get project root directory
    project_root = Path(__file__).resolve().parent
    
    env_path = project_root / ".env"
    
    # Default environment variables
    env_content = """# OpenAI API Key (REQUIRED for LLM features)
# Get your API key from: https://platform.openai.com/api-keys
# Replace 'your_openai_api_key_here' with your actual OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here

# Use mock LLM instead of OpenAI
# Set to "false" to use real OpenAI API (requires OPENAI_API_KEY)
# Set to "true" to use mock/rule-based logic (no API calls)
# If OPENAI_API_KEY is not set, mock will be used automatically
USE_MOCK_LLM=false

# JWT Secret Key (change this in production!)
# Generate with: openssl rand -hex 32
SECRET_KEY=your-secret-key-change-in-production-use-openssl-rand-hex-32

# Database URL (SQLite - default)
DATABASE_URL=sqlite:///app.db
"""
    
    if env_path.exists():
        print(f".env file already exists at {env_path}")
        print("Skipping creation. If you need to recreate it, delete the existing file first.")
        return
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"[OK] Created .env file at {env_path}")
        print("\n[IMPORTANT] Update the following values in .env file:")
        print("   - OPENAI_API_KEY: Add your OpenAI API key (optional)")
        print("   - SECRET_KEY: Change to a secure random key for production")
        print("\n[TIP] To generate a secure SECRET_KEY, run:")
        print("   openssl rand -hex 32")
    except Exception as e:
        print(f"[ERROR] Error creating .env file: {e}")

if __name__ == "__main__":
    create_env_file()


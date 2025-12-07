# Environment Setup

## Create .env File

Create a `.env` file in the PROJECT root directory with the following content:

```env
# OpenAI API Key (optional - for LLM features)
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Use mock LLM instead of OpenAI (set to "true" to use mock, "false" to use OpenAI)
# If OPENAI_API_KEY is not set, mock will be used automatically
USE_MOCK_LLM=true

# JWT Secret Key (change this in production!)
# Generate with: openssl rand -hex 32
SECRET_KEY=your-secret-key-change-in-production-use-openssl-rand-hex-32

# Database URL (SQLite - default)
DATABASE_URL=sqlite:///app.db
```

## Quick Setup

Run the setup script:

```bash
python create_env_file.py
```

This will create the `.env` file automatically.

## Manual Setup

1. Copy the content above
2. Create a file named `.env` in the PROJECT root
3. Paste the content
4. Update the values:
   - `OPENAI_API_KEY`: Your OpenAI API key (optional)
   - `SECRET_KEY`: Generate a secure key with `openssl rand -hex 32`
   - `USE_MOCK_LLM`: Set to "true" to use mock LLM (no API key needed)

## Notes

- The `.env` file is gitignored and won't be committed
- Never share your `.env` file or commit it to version control
- For production, use secure environment variables or a secrets manager





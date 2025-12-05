import os
from dotenv import load_dotenv

load_dotenv()
env = os.getenv

# Simplified model mapping - OpenAI only
MODEL_OPTIONS = {
    'OpenAI': 'gpt-4o'
}

# Streamlit defaults
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 1.0

# Remote dbt MCP server configuration
DBT_MCP_CONFIG = {
    "mcpServers": {
        "dbt": {
            "url": env("DBT_MCP_URL", "https://cloud.getdbt.com/api/ai/v1/mcp/"),
            "headers": {
                "Authorization": f"token {env('DBT_TOKEN')}",
                "x-dbt-prod-environment-id": env("DBT_PROD_ENV_ID")
            },
            "timeout": 30
        }
    }
}
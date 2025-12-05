# dbt MCP Streamlit App

A Streamlit application that connects to remote dbt MCP servers using OpenAI for intelligent tool selection and routing.

## Features

- **OpenAI Integration**: Uses GPT-4o for intelligent responses
- **Remote dbt MCP Server**: Connects to dbt Cloud's remote MCP server
- **Chat Interface**: Interactive chat with dbt tools
- **Tool Execution History**: Track dbt tool usage and results

## Setup

### Prerequisites

1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/)
2. **dbt Cloud Account**: With dbt token and production environment ID
3. **Python 3.8+**: Required for running the application

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd custom-streamlit-mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install -r client/requirements.txt
   ```

3. **Configure environment variables**:
   Copy the example environment file and fill in your credentials:
   ```bash
   cp client/env-example client/.env
   ```
   
   Edit `client/.env`:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DBT_TOKEN=your_dbt_token_here
   DBT_PROD_ENV_ID=your_dbt_production_environment_id
   DBT_MCP_URL=https://cloud.getdbt.com/api/ai/v1/mcp/
   ```

### Getting dbt Credentials

1. **dbt Token**: Get from dbt Cloud → Account Settings → API Tokens
2. **Production Environment ID**: Found in dbt Cloud → Orchestration page

## Running the App

### Option 1: Using the run script
```bash
python run_local.py
```

### Option 2: Direct streamlit command
```bash
cd client
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Usage

1. **Configure API Keys**: Enter your OpenAI API key in the sidebar
2. **Configure dbt**: Enter your dbt token and environment ID
3. **Connect to dbt MCP**: Click "Connect to dbt MCP Server"
4. **Start Chatting**: Ask questions about your dbt project and data

## Available dbt Tools

The app connects to dbt's remote MCP server which provides tools for:

- **Discovery**: Get dbt models, relationships, and metadata
- **Semantic Layer**: Query metrics, dimensions, and entities
- **dbt CLI**: Run dbt commands (build, test, compile, etc.)
- **SQL Generation**: Generate and execute SQL queries

## Architecture

- **Frontend**: Streamlit UI with chat interface
- **AI**: OpenAI GPT-4o for natural language processing
- **MCP**: Remote connection to dbt Cloud MCP server
- **Tools**: dbt tools accessed via MCP protocol

## Changes from Original

- **Removed**: Multiple LLM providers (kept only OpenAI)
- **Removed**: Local MCP servers and Docker setup
- **Added**: Remote dbt MCP server integration
- **Simplified**: Configuration and dependencies
- **Enhanced**: dbt-focused prompts and UI
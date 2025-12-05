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
3. **Python 3.11**: Required for running the application (Python 3.10+ may work, but 3.11 is recommended)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mani-dbt/custom-streamlit-mcp.git
   cd custom-streamlit-mcp
   ```

2. **Set up Python 3.11 and install dependencies**:
   
   **Option A: Using the setup script (recommended)**:
   ```bash
   cd client
   chmod +x setup_python311.sh
   ./setup_python311.sh
   ```
   
   **Option B: Manual installation**:
   ```bash
   # Install Python 3.11 if not already installed (macOS with Homebrew)
   brew install python@3.11
   
   # Install dependencies with Python 3.11
   pip3.11 install -r client/requirements.txt
   ```

3. **Configuration**:
   All configuration is done through the Streamlit UI - no environment files needed!

## Running the App

From the project root directory:

```bash
cd client
python3.11 -m streamlit run app.py
```

The app will be available at `http://localhost:8501`

**Important**: Make sure to use Python 3.11. Using Python 3.9 or earlier will result in module import errors (`ModuleNotFoundError: No module named 'mcp'`).

## Usage

1. **Configure OpenAI**: Enter your OpenAI API key in the sidebar
   - Get your API key from [OpenAI Platform](https://platform.openai.com/)
   
2. **Configure dbt Cloud**: Enter your dbt credentials in the sidebar
   - **dbt Token**: Get from dbt Cloud → Account Settings → API Tokens
   - **Production Environment ID**: Found in dbt Cloud → Orchestration page
   - **dbt Host URL**: Usually `cloud.getdbt.com` (default)
   
3. **Connect to dbt MCP**: Click "Connect to dbt MCP Server"

4. **Start Chatting**: Ask questions about your dbt project and data

## Available dbt Tools

The app connects to dbt's remote MCP server which provides tools for:

- **Discovery**: Get dbt models, relationships, and metadata
- **Semantic Layer**: Query metrics, dimensions, and entities

**Note**: SQL tools (`text_to_sql` and `execute_sql`) are disabled by default as they require additional configuration (user ID and development environment ID). The app focuses on consumption-based use cases through the Semantic Layer.

## Architecture

- **Frontend**: Streamlit UI with chat interface
- **AI**: OpenAI GPT-4o for natural language processing
- **MCP**: Remote connection to dbt Cloud MCP server
- **Tools**: dbt tools accessed via MCP protocol

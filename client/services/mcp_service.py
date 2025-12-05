from typing import Dict, List, Optional
import os
import json
import streamlit as st

from agents import Agent, Runner
from agents.mcp import create_static_tool_filter
from agents.mcp.server import MCPServerStreamableHttp

from utils.async_helpers import run_async


class RemoteMCPClient:
    """Thin wrapper around a remote dbt MCP server using the agents SDK."""
    
    def __init__(self, url: str, headers: Dict[str, str], timeout_seconds: int = 20,
                 allowed_tool_names: Optional[List[str]] = None):
        self.url = url
        self.headers = headers
        self.timeout_seconds = timeout_seconds
        self.allowed_tool_names = allowed_tool_names or [
            "list_metrics",
            "get_dimensions",
            "get_entities",
            "query_metrics",
        ]

        self.server: Optional[MCPServerStreamableHttp] = None
        self.agent: Optional[Agent] = None

        # Tools metadata populated dynamically via list_tools
        self._tools_metadata: List[Dict[str, str]] = []

    async def connect(self) -> "RemoteMCPClient":
        self.server = MCPServerStreamableHttp(
            name="dbt",
            params={
                "url": self.url,
                "headers": self.headers,
            },
            client_session_timeout_seconds=self.timeout_seconds,
            cache_tools_list=True,
#            tool_filter=create_static_tool_filter(allowed_tool_names=self.allowed_tool_names),
        )

        # Manually enter the async context so we can keep the connection open across requests
        await self.server.__aenter__()

        self.agent = Agent(
            name="Assistant",
            instructions="Use the tools to answer the user's questions",
            mcp_servers=[self.server],
        )
        return self

    async def close(self) -> None:
        if self.server is not None:
            await self.server.__aexit__(None, None, None)
            self.server = None
        self.agent = None

    def get_tools(self) -> List[Dict[str, str]]:
        return self._tools_metadata

    async def fetch_tools(self) -> List[Dict[str, str]]:
        if self.server is None:
            return []
        tools = await self.server.list_tools()
        self._tools_metadata = [
            {
                "name": getattr(t, "name", "unknown"),
                "description": getattr(t, "description", ""),
                "schema": getattr(t, "input_schema", None),  # capture if present
            }
            for t in tools
        ]
        return self._tools_metadata

    async def run(self, conversation: List[Dict[str, str]]):
        if self.agent is None:
            raise RuntimeError("Agent not initialized. Call connect() first.")
        
        try:
            result = await Runner.run(self.agent, conversation)
            final_output = getattr(result, "final_output", "")
        except Exception as e:
            # Handle errors from the agent/runner
            error_msg = str(e)
            if "serialization" in error_msg.lower() or "json" in error_msg.lower():
                return {
                    "output": "⚠️ There was an issue processing the tool response. The data returned might be too complex or in an unexpected format. Please try rephrasing your question or requesting a simpler output.",
                    "tool_executions": [],
                    "error": error_msg
                }
            else:
                raise
        
        # Tool execution capture - parse from to_input_list() with correct format
        tool_executions = []
        try:
            # Get the input list which contains the conversation flow
            if hasattr(result, 'to_input_list'):
                input_list = result.to_input_list()
                
                # Build a map of call_id -> tool call for matching with outputs
                tool_calls_map = {}
                
                for i, item in enumerate(input_list):
                    if isinstance(item, dict):
                        # Look for function calls (tool invocations)
                        if item.get('type') == 'function_call':
                            tool_name = item.get('name', 'unknown')
                            call_id = item.get('call_id')
                            arguments = item.get('arguments', '{}')
                            
                            # Parse arguments if they're JSON strings
                            try:
                                if isinstance(arguments, str):
                                    parsed_args = json.loads(arguments) if arguments.strip() else {}
                                else:
                                    parsed_args = arguments
                            except (json.JSONDecodeError, TypeError):
                                parsed_args = arguments
                            
                            tool_execution = {
                                "tool_name": tool_name,
                                "input": parsed_args,
                                "output": "Tool executed"  # Default, will be updated if output found
                            }
                            
                            # Store in map for output matching
                            if call_id:
                                tool_calls_map[call_id] = len(tool_executions)
                            
                            tool_executions.append(tool_execution)
                        
                        # Look for function call outputs
                        elif item.get('type') == 'function_call_output':
                            call_id = item.get('call_id')
                            output = item.get('output', '')
                            
                            # Match with the corresponding tool call
                            if call_id in tool_calls_map:
                                tool_index = tool_calls_map[call_id]
                                if tool_index < len(tool_executions):
                                    # Convert output to string safely
                                    try:
                                        if isinstance(output, (dict, list)):
                                            output_str = json.dumps(output, indent=2)
                                        else:
                                            output_str = str(output)
                                    except Exception:
                                        output_str = repr(output)
                                    
                                    # Truncate long outputs
                                    if len(output_str) > 1000:
                                        output_str = output_str[:1000] + "... (truncated)"
                                    
                                    tool_executions[tool_index]["output"] = output_str
                                
        except Exception:
            # Silently continue if tool execution capture fails
            pass
        
        return {
            "output": final_output,
            "tool_executions": tool_executions,
        }


async def setup_mcp_client() -> RemoteMCPClient:
    """Initialize and connect a remote MCP client for dbt."""
    dbt_token = os.getenv("DBT_TOKEN")
    prod_env_id = os.getenv("DBT_PROD_ENV_ID")

    if not dbt_token or not prod_env_id:
        raise ValueError("Missing required dbt credentials. Please provide DBT_TOKEN and DBT_PROD_ENV_ID.")
    
    # Prefer explicit MCP URL if provided; otherwise construct from host
    url = os.getenv("DBT_MCP_URL")
    if not url:
        host = os.getenv("DBT_HOST", "cloud.getdbt.com")
        url = f"https://{host}/api/ai/v1/mcp/"

    headers = {
        "Authorization": f"token {dbt_token}",
        "x-dbt-prod-environment-id": prod_env_id,
    }

    client = RemoteMCPClient(url=url, headers=headers)
    return await client.connect()


async def run_agent(client: "RemoteMCPClient", message: str, api_key: str) -> Dict:
    """Run a single turn with the simple Agent/Runner using the connected MCP server."""
    # Ensure OpenAI key is available to the agents SDK
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    # Include prior chat history if available
    history_messages: List[Dict[str, str]] = []
    try:
        for msg in st.session_state.get("messages", []):
            role = msg.get("role")
            content = msg.get("content")
            if role and content:
                history_messages.append({"role": role, "content": content})
    except Exception:
        pass

    conversation = history_messages + [{"role": "user", "content": message}]
    
    try:
        return await client.run(conversation)
    except Exception as e:
        error_msg = str(e)
        # Return a structured error response
        return {
            "output": f"⚠️ An error occurred while processing your request: {error_msg}",
            "tool_executions": [],
            "error": error_msg
        }


async def _test_mcp_connection_async() -> bool:
    try:
        client = await setup_mcp_client()
        await client.close()
        return True
    except Exception:
        return False


def test_mcp_connection():
    return run_async(_test_mcp_connection_async())


def connect_to_mcp_servers():
    # Clean up existing client if any
    existing = st.session_state.get("client")
    if existing:
        try:
            run_async(existing.close())
        except Exception:
            pass

    try:
        with st.spinner("🚀 Connecting to dbt MCP server..."):
            st.session_state.client = run_async(setup_mcp_client())
            # Populate tools dynamically from MCP using list_tools
            st.session_state.tools = run_async(st.session_state.client.fetch_tools())
            st.session_state.agent = None  # Kept for compatibility elsewhere
            st.success(f"✅ Connected to dbt MCP! {len(st.session_state.tools)} tools available.")
    except ValueError as e:
        st.error(f"❌ Configuration Error: {e}")
        st.session_state.client = None
        st.session_state.tools = []
        st.session_state.agent = None
    except Exception as e:
        st.error(f"❌ Failed to connect to dbt MCP server: {e}")
        st.session_state.client = None
        st.session_state.tools = []
        st.session_state.agent = None


def disconnect_from_mcp_servers():
    client = st.session_state.get("client")
    if client:
        try:
            run_async(client.close())    
        except Exception:
            pass
    st.session_state.client = None
    st.session_state.tools = []
    st.session_state.agent = None
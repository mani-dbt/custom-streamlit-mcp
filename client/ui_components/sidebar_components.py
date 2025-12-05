import streamlit as st
import traceback
import os
from services.mcp_service import connect_to_mcp_servers
from services.chat_service import create_chat, delete_chat
from utils.tool_schema_parser import extract_tool_parameters
from utils.async_helpers import reset_connection_state

def create_history_chat_container():
    # Ensure session state is initialized
    if "history_chats" not in st.session_state:
        return
        
    history_container = st.sidebar.container(height=160, border=True)  # small tweak, border to imply scroll
    with history_container:
        chat_history_menu = [
                f"{chat['chat_name']}_::_{chat['chat_id']}"
                for chat in st.session_state["history_chats"]
            ]
        chat_history_menu = chat_history_menu[:50][::-1]
        
        if chat_history_menu:
            # Get current index safely
            current_index = st.session_state.get("current_chat_index", 0)
            # Ensure index is within bounds
            if current_index >= len(chat_history_menu):
                current_index = 0
                st.session_state["current_chat_index"] = 0
            
            current_chat = st.radio(
                label="History Chats",
                format_func=lambda x: x.split("_::_")[0] + '...' if "_::_" in x else x,
                options=chat_history_menu,
                label_visibility="collapsed",
                index=current_index,
                key="dbt_chat_history_radio"
            )
            
            if current_chat:
                st.session_state['current_chat_id'] = current_chat.split("_::_")[1]

def create_sidebar_chat_buttons():
    with st.sidebar:
        c1, c2 = st.columns(2)
        create_chat_button = c1.button(
            "New Chat", use_container_width=True, key="create_chat_button"
        )
        if create_chat_button:
            create_chat()
            st.rerun()

        delete_chat_button = c2.button(
            "Delete Chat", use_container_width=True, key="delete_chat_button"
        )
        if delete_chat_button and st.session_state.get('current_chat_id'):
            delete_chat(st.session_state['current_chat_id'])
            st.rerun()

def create_chat_history_section():
    """Combined chat history section with container and buttons"""
   
    with st.sidebar:
        st.markdown("---")
        st.subheader("📝 Chat History")
        
    # Only create history container if session is properly initialized
    if "history_chats" in st.session_state:
        create_history_chat_container()
    
    # Chat management buttons
    create_sidebar_chat_buttons()

def create_provider_select_widget():
    params = st.session_state.setdefault('params', {})
    # OpenAI only
    params['model_id'] = 'OpenAI'
#    st.sidebar.success(f"Model: {MODEL_OPTIONS['OpenAI']}")

    # OpenAI API Key input
    with st.sidebar.container():
        with st.expander("🔐 OpenAI Configuration", expanded=True):
            params['api_key'] = st.text_input(
                "OpenAI API Key   (Model: gpt-4o)", 
                value=params.get('api_key'), 
                type="password", 
                key="openai_api_key"
            )
            if params.get('api_key'):
                st.success("✅ OpenAI API key configured")
            else:
                st.warning("⚠️ Please enter your OpenAI API key")



def create_mcp_configuration_widget():
    """Widget for dbt MCP configuration (credentials only)"""
    with st.sidebar:
        st.header("🏗️ dbt Cloud MCP Server")
        
        # Show dbt MCP configuration with more details
        with st.expander("📋 dbt MCP Configuration", expanded=True):
            st.markdown("**Server Type:** Remote dbt Cloud MCP")
            # Enter dbt Cloud host (without protocol)
            dbt_host = st.text_input(
                "dbt Host URL",
                value=os.getenv('DBT_HOST', 'cloud.getdbt.com'),
                key="dbt_host_input",
                help="Your dbt Cloud hostname (e.g. cloud.getdbt.com)"
            )
            # Construct the MCP URL from host
            mcp_url = f"https://{dbt_host}/api/ai/v1/mcp/"
            # Display once
            st.markdown(f"**MCP URL:** `{mcp_url}`")
            # Save to environment for use in other calls
            os.environ['DBT_HOST'] = dbt_host
            os.environ['DBT_MCP_URL'] = mcp_url
            
            st.markdown("Configuration for MCP Server:")
            
            # Environment variable inputs for dbt
            dbt_token = st.text_input(
                "dbt Cloud API Token", 
                type="password", 
                key="dbt_token",
                help="Get this from dbt Cloud → Account Settings → API Tokens"
            )
            dbt_env_id = st.text_input(
                "Production Environment ID", 
                key="dbt_env_id",
                help="Found in dbt Cloud → Orchestration page"
            )
            
            # Credential validation feedback
            if dbt_token and dbt_env_id:
                # Update environment variables
                os.environ['DBT_TOKEN'] = dbt_token
                os.environ['DBT_PROD_ENV_ID'] = dbt_env_id
                st.success("✅ dbt MCP parameters configured successfully!")
            elif not dbt_token:
                st.warning("⚠️ Please enter your dbt Cloud API Token")
            elif not dbt_env_id:
                st.warning("⚠️ Please enter your Production Environment ID")

def create_mcp_connection_status_widget():
    """Widget for MCP connection status and connect/disconnect buttons"""
    with st.sidebar:
        st.subheader("🔌 Connection Status & Actions")
        
        # Connection status and controls
        if st.session_state.get("client"):
            # The list of tools is retrieved from the MCP server and stored in st.session_state["tools"]
            # This is not local code; it's populated from the server's response after connecting.
            st.success(f"✅ Connected to dbt Cloud MCP!")
            
            # Connection details
            st.markdown("**Connection Details:**")
            st.markdown("• **Status:** ✅ Active")
                        
            # Disconnect section
            st.markdown("---")
            if st.button("🔌 Disconnect from dbt MCP Server", type="secondary", use_container_width=True):
                    with st.spinner("Disconnecting from dbt MCP server..."):
                        try:
                            reset_connection_state()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error disconnecting from dbt MCP server: {str(e)}")
                            st.code(traceback.format_exc(), language="python")
        else:
            st.error("❌ Not connected to dbt MCP server")
            
            # Check if credentials are configured before showing connect button
            dbt_token_set = bool(os.getenv('DBT_TOKEN'))
            dbt_env_set = bool(os.getenv('DBT_PROD_ENV_ID'))
            
            # Connection readiness indicator
          #  st.markdown("**🚦 Connection Status:**")
                
          #  if dbt_token_set and dbt_env_set:
          #      st.success("🎯 Ready to connect!")
          #  else:
          #      st.warning("⚠️ Missing dbt configuration")
            
            # Connect section for non-connected state
            st.markdown("---")
            ready = dbt_token_set and dbt_env_set
            btn_label = "🚀 Connect to dbt MCP Server" if ready else "Provide credentials to connect"
            if st.button(btn_label, disabled=not ready, type="primary", use_container_width=True):
                try:
                    connect_to_mcp_servers()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error connecting to dbt MCP server: {str(e)}")
                    st.code(traceback.format_exc(), language="python")

def create_mcp_connection_widget():
    """Legacy function - calls both configuration and status widgets"""
    create_mcp_configuration_widget()
    create_mcp_connection_status_widget()

def create_mcp_tools_widget():
    with st.sidebar:
        tools = st.session_state.get("tools", [])
        if tools:
            st.subheader("🧰 Available dbt Tools")

            selected_tool_name = st.selectbox(
                "Select a dbt Tool",
                options=[tool.name for tool in tools],
                index=0
            )

            if selected_tool_name:
                selected_tool = next(
                    (tool for tool in tools if tool.name == selected_tool_name),
                    None
                )

                if selected_tool:
                    with st.container():
                        st.write("**Description:**")
                        st.write(selected_tool.description)

                        parameters = extract_tool_parameters(selected_tool)

                        if parameters:
                            st.write("**Parameters:**")
                            for param in parameters:
                                st.code(param)
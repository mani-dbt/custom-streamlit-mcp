import os
import datetime
import streamlit as st
import json
from services.mcp_service import run_agent
from services.chat_service import get_current_chat, _append_message_to_session
from utils.async_helpers import run_async
from utils.ai_prompts import make_system_prompt, make_main_prompt
import ui_components.sidebar_components as sd_compents
from config import DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE
import traceback

def main():
    # List available dbt tools (if connected) before chat section
    if st.session_state.get('tools'):
        st.subheader("🛠️ Available dbt Tools")
        tools = st.session_state['tools']
        # Streamlit buttons (disabled) with tooltip help text
        num_cols = 6
        cols = st.columns(num_cols)
        for i, tool in enumerate(tools):
            col = cols[i % num_cols]
            with col:
                _clicked = st.button(
                    label=tool.get('name', ''),
                    key=f"tool-pill-{tool.get('name','')}-{i}",
                    help=tool.get('description', ''),
                    use_container_width=True,
                )
                # Intentionally ignore clicks; buttons are for visual organization only
        st.markdown("---")

    # Main chat interface
    st.header("Chat with dbt")
    messages_container = st.container(border=True, height=600)
    
    # Re-render previous messages
    if st.session_state.get('current_chat_id'):
        st.session_state["messages"] = get_current_chat(st.session_state['current_chat_id'])
        for m in st.session_state["messages"]:
            with messages_container.chat_message(m["role"]):
                if "tool" in m and m["tool"]:
                    st.code(m["tool"], language='yaml')
                if "content" in m and m["content"]:
                    st.markdown(m["content"])

    # Readiness gating
    is_connected = bool(st.session_state.get("client"))
    api_key = st.session_state.get("params", {}).get("api_key")
    is_api_key_set = bool(api_key)
    is_ready = is_connected and is_api_key_set

    # Disable chat input until ready
    user_text = st.chat_input(
        "Ask questions about your dbt project or request data analysis",
        disabled=not is_ready,
        key="main_chat_input"
    )
    if not is_ready:
        st.info("Set your OpenAI API key and connect to dbt MCP to start chatting.")

    # Sidebar widgets in requested order:
    # 1. dbt MCP configuration (credentials only)
    sd_compents.create_mcp_configuration_widget()
    
    # 2. OpenAI API key configuration widget
    sd_compents.create_provider_select_widget()
    
    # 3. Connection Status & the Connect button for dbt MCP Server
    sd_compents.create_mcp_connection_status_widget()
    
    # 4. Chat history along with the new chat and delete chat buttons
    sd_compents.create_chat_history_section()

    # Main Logic
    if user_text is None:
        st.stop()
    
    params = st.session_state.get('params')
    if not params.get('api_key'):
        err_mesg = "❌ Missing OpenAI API key. Please provide your API key in the sidebar."
        _append_message_to_session({"role": "assistant", "content": err_mesg})
        with messages_container.chat_message("assistant"):
            st.markdown(err_mesg)
        st.rerun()

    # Handle user question
    if user_text:
        user_text_dct = {"role": "user", "content": user_text, "ts": datetime.datetime.now().isoformat()}
        _append_message_to_session(user_text_dct)
        with messages_container.chat_message("user"):
            st.markdown(user_text)

        with st.spinner("Analyzing your request with dbt tools…", show_time=True):
            system_prompt = make_system_prompt()
            main_prompt = make_main_prompt(user_text)
            try:
                # If MCP client is connected, use OpenAI function-calling workflow
                if st.session_state.get('client'):
                    response = run_async(run_agent(st.session_state.client, user_text, params.get('api_key')))

                    # Format tool executions inline with the response
                    formatted_response = response.get('output', '')
                    if response.get('tool_executions'):
                        tools_summary = "\n\n---\n**🛠️ dbt Tools Used:**\n\n"
                        for i, exec in enumerate(response['tool_executions'], 1):
                            tool_name = exec.get('tool_name', 'unknown')
                            tools_summary += f"**{i}**. {tool_name}\n"
                        
                        formatted_response = formatted_response + tools_summary

                    # Display assistant reply with integrated tool summary
                    with messages_container.chat_message("assistant"):
                        st.markdown(formatted_response)
                    response_dct = {"role": "assistant", "content": formatted_response}
                
                # Fall back to regular stream response if agent not available
                else:
                    st.error("Please connect to the dbt MCP server to start chatting.")
                    st.stop()
                        
            except Exception as e:
                st.toast("Something went wrong. See details below.", icon="⚠️")
                st.error(str(e))
                with st.expander("Traceback"):
                    st.code(traceback.format_exc(), language="python")
                st.stop()
                
        # Add assistant message to chat history
        _append_message_to_session(response_dct)

if __name__ == "__main__":
    main()
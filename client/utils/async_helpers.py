import streamlit as st
import asyncio
import warnings
import sys
from contextlib import contextmanager

@contextmanager
def suppress_async_warnings():
    """Suppress async cleanup warnings that don't affect functionality."""
    # Temporarily redirect stderr to suppress ignored exceptions
    original_stderr = sys.stderr
    
    class FilteredStderr:
        def write(self, message):
            # Filter out specific async cleanup errors that are harmless
            if any(phrase in message for phrase in [
                "Exception ignored in:",
                "async generator ignored GeneratorExit",
                "RuntimeError: no running event loop",
                "Attempted to exit cancel scope"
            ]):
                return
            original_stderr.write(message)
        
        def flush(self):
            original_stderr.flush()
    
    try:
        sys.stderr = FilteredStderr()
        yield
    finally:
        sys.stderr = original_stderr

# Helper function for running async functions
def run_async(coro):
    """Run an async function within the stored event loop."""
    loop = st.session_state.loop
    
    # Ensure the loop is set as the current event loop
    asyncio.set_event_loop(loop)
    
    try:
        # Use a task to run the coroutine with better cleanup
        task = loop.create_task(coro)
        
        # Suppress async cleanup warnings
        with suppress_async_warnings():
            result = loop.run_until_complete(task)
        
        return result
    except Exception as e:
        # Re-raise the actual exception, not cleanup errors
        raise e

def reset_connection_state():
    """Reset all connection-related session state variables."""
    if hasattr(st.session_state, 'client') and st.session_state.client is not None:
        try:
            # Close the existing client properly
            with suppress_async_warnings():
                run_async(st.session_state.client.close())
        except RuntimeError as e:
            # Ignore event loop errors during cleanup
            if "event loop" not in str(e).lower():
                st.error(f"Error closing previous client: {str(e)}")
        except Exception as e:
            st.error(f"Error closing previous client: {str(e)}")
    
    st.session_state.client = None
    st.session_state.agent = None
    st.session_state.tools = []

def on_shutdown():
    """Proper cleanup when the session ends."""
    try:
        if hasattr(st.session_state, 'client') and st.session_state.client is not None:
            # Close the client properly, ignoring event loop errors
            try:
                with suppress_async_warnings():
                    run_async(st.session_state.client.close())
            except RuntimeError:
                # Event loop errors during shutdown are expected
                pass
    except Exception:
        # During shutdown, we can't use st.error, so just pass
        pass
    finally:
        # Close the event loop if it exists
        try:
            if hasattr(st.session_state, 'loop') and st.session_state.loop:
                # Cancel all pending tasks
                with suppress_async_warnings():
                    pending = asyncio.all_tasks(st.session_state.loop)
                    for task in pending:
                        task.cancel()
                    # Close the loop
                    if not st.session_state.loop.is_closed():
                        st.session_state.loop.close()
        except Exception:
            pass
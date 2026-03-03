import streamlit as st
import subprocess
import os

st.set_page_config(page_title="SiliAgent AI", page_icon="🛡️", layout="wide")

# Header section
st.title("🛡️ SiliAgent AI")
st.subheader("Autonomous RTL Verification & Repair Platform")
st.markdown("---")

# Setup Sidebar for API Key and Project Selection
with st.sidebar:
    st.header("Settings")
    user_api_key = st.text_input("Anthropic API Key", type="password", help="Enter key to run live repair")
    selected_task = st.radio("Select Demo Module", ["SiliAXI (Protocol)", "SiliCount (Coverage)", "SiliOracle (Logic)"])
    
    st.info("Built by Sai Kumar | March 2026")

# Layout: 2 Columns
col_left, col_right = st.columns([1, 1])

with col_left:
    st.write("### 🤖 Agent Workspace")
    if st.button("🚀 Run Verification Loop"):
        if not user_api_key:
            st.warning("Please enter an API Key to proceed.")
        else:
            # Set the environment variable for your scripts
            os.environ["ANTHROPIC_API_KEY"] = user_api_key
            
            with st.status(f"Running {selected_task}...", expanded=True) as status:
                st.write("Compiling RTL with iverilog...")
                # Adjust this path to match your actual script name
                script_path = "SiliAXI/axi_agent.py" if "AXI" in selected_task else "SiliCount/counter_agent.py"
                
                process = subprocess.Popen(
                    ["python3", script_path],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
                )
                
                # Stream logs to the right column
                log_placeholder = col_right.empty()
                full_log = ""
                for line in process.stdout:
                    full_log += line
                    log_placeholder.code(full_log)
                
                status.update(label="Verification Complete!", state="complete", expanded=False)
            
            st.balloons()

with col_right:
    st.write("### 📜 Real-time Logs / Silicon Truth")
    if not user_api_key:
        st.info("Logs will appear here once the agent starts.")

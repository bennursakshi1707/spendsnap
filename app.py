import streamlit as st
import asyncio
import subprocess
import time
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="SpendSnap", page_icon="🧾", layout="centered")

# ---- Minimal custom styling, pure CSS via Streamlit's built-in support ----
st.markdown("""
    <style>
        .stApp { background-color: #fafafa; }
        h1 { font-weight: 800; }
        .stButton button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.6rem 1.5rem;
        }
        div[data-testid="stFileUploader"] {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 1rem;
            background-color: white;
        }
    </style>
""", unsafe_allow_html=True)


def ensure_servers_running():
    if "servers_started" not in st.session_state:
        subprocess.Popen(["python", "-m", "mcp_server.server"])
        subprocess.Popen(["python", "-m", "currency_server.server"])
        time.sleep(3)
        st.session_state["servers_started"] = True


ensure_servers_running()

st.title("🧾 SpendSnap")
st.caption("Upload a receipt — the agent extracts, validates, and logs it to your budget tracker automatically.")

st.divider()


async def get_agent():
    if "agent" not in st.session_state:
        mcp_client = MultiServerMCPClient({
            "spendsnap": {
                "url": "http://127.0.0.1:8000/mcp",
                "transport": "http"
            },
            "currency": {
                "url": "http://127.0.0.1:8001/mcp",
                "transport": "http"
            }
        })
        mcp_tools = await mcp_client.get_tools()

        st.session_state["agent"] = create_deep_agent(
            tools=mcp_tools,
            model="openai:gpt-4o-mini",
            system_prompt="""You are SpendSnap, a helpful assistant that processes 
receipt images and adds them to the user's budget tracker. 
You have access to a receipt-processing skill that tells you exactly 
how to handle receipt uploads. Always follow that skill's instructions 
precisely, in order, including any currency conversion steps it describes.""",
        )
    return st.session_state["agent"]


async def run_agent_streaming(image_path: str, status_box):
    agent = await get_agent()
    user_message = f"Here's a receipt, can you add it? {image_path}"

    final_reply = ""

    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": user_message}]},
        stream_mode="updates"
    ):
        if not isinstance(chunk, dict):
            continue

        for node_name, node_data in chunk.items():
            if not isinstance(node_data, dict):
                continue

            messages = node_data.get("messages", [])
            if not messages:
                continue

            for msg in messages:
                tool_calls = getattr(msg, "tool_calls", None)
                if tool_calls:
                    for call in tool_calls:
                        status_box.write(f"🔧 Calling `{call['name']}`...")

                if type(msg).__name__ == "ToolMessage":
                    status_box.write(f"✅ `{msg.name}` finished")

                content = getattr(msg, "content", None)
                if content and type(msg).__name__ == "AIMessage" and not tool_calls:
                    if isinstance(content, str):
                        final_reply = content
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and "text" in block:
                                final_reply = block["text"]

    return final_reply


uploaded_file = st.file_uploader("Upload a receipt image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

    save_path = f"receipts/{uploaded_file.name}"
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    with col2:
        st.write("")
        process_clicked = st.button("Process this receipt", type="primary", use_container_width=True)

    if process_clicked:
        with st.status("Working on your receipt...", expanded=True) as status:
            reply = asyncio.run(run_agent_streaming(save_path, status))
            status.update(label="Done", state="complete", expanded=False)

        st.success(reply)

    if st.button("Upload another receipt"):
        st.session_state.pop("agent", None)
        st.rerun()
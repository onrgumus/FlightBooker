import re
import streamlit as st
from app import app  # Importing compiled LangGraph instance from app.py

# --- STREAMLIT PAGE HEADERS & CONFIGURATION ---
st.set_page_config(
    page_title="Autonomous Airline Assistant", 
    page_icon="✈️", 
    layout="centered"
)

st.title("✈️ Autonomous Airline Customer Agent")
st.subheader("LangGraph & Local Llama 3 Powered Crisis Panel")


def format_agent_response(response: str) -> tuple[str, str | None]:
    """Cleans transactional routing flags and prepares markdown typography boundaries."""
    # Regex cleanups matching our English router layout tags
    cleaned_response = re.sub(r"\s*\[ROUTE:(REBOOK|REFUND)\]\s*", "", response).strip()
    cleaned_response = re.sub(r"\s*\*\s*", "\n- ", cleaned_response)
    
    # Structural newline adjustments for English policy phrases
    cleaned_response = re.sub(r"(?<!\n)(Refund policy:|Refund amount:)", r"\n\1", cleaned_response)
    
    route_match = re.search(r"\[ROUTE:(REBOOK|REFUND)\]", response)
    route_action = route_match.group(1).lower() if route_match else None
    return cleaned_response, route_action


def format_markdown_content(content: str) -> str:
    """Converts continuous text and custom bulleted layouts to standard HTML elements."""
    lines = [line.rstrip() for line in content.splitlines()]
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('- ', '* ')):
            if not in_list:
                html_lines.append("<ul style='padding-left:18px; margin:6px 0; font-family:sans-serif;'>")
                in_list = True
            html_lines.append(f"<li style='margin-bottom:4px; font-size:15px;'>{stripped[2:].strip()}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if stripped == "":
                html_lines.append("<div style='margin:10px 0;'></div>")
            else:
                html_lines.append(f"<p style='margin:0 0 10px 0; line-height:1.5; font-size:15px; font-family:sans-serif;'>{stripped}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "".join(html_lines)


def render_agent_message(response: str) -> str:
    """Renders HTML-sanitized agent output alongside structural tracking blocks."""
    cleaned_response, route_action = format_agent_response(response)
    html_content = format_markdown_content(cleaned_response)
    st.markdown(html_content, unsafe_allow_html=True)
    
    if route_action:
        label = "Flight Rebooking Execution" if route_action == "rebook" else "Cash Refund Settlement"
        st.markdown(
            f"<div style='margin-top:14px; padding:14px; border-radius:10px; "
            f"background-color:#e6f7ff; border:1px solid #9ad1ff; font-family:sans-serif; font-size:14px;'>"
            f"<strong style='color:#0050b3;'>📌 Autonomous Pipeline Action:</strong> {label}</div>",
            unsafe_allow_html=True,
        )
    return cleaned_response


# --- 1. SIDEBAR CONFIGURATION (PASSENGER VERIFICATION) ---
with st.sidebar:
    st.header("Passenger Verification")
    pnr_input = st.text_input("PNR Reference Code:", value="ABC123")
    user_msg_input = st.text_input("Describe your issue:", value="My flight has been cancelled. I need help.")
    
    if st.button("Initialize Agent Loop"):
        # Reset chat session arrays
        st.session_state.messages = []
        
        with st.spinner("Invoking LangGraph execution pipeline..."):
            inputs = {"pnr": pnr_input, "user_message": user_msg_input, "history": []}
            output = app.invoke(inputs)
            
            assistant_text = format_agent_response(output["agent_response"])[0]
            st.session_state.messages.append({"role": "assistant", "content": assistant_text})
            st.session_state.graph_history = [{"user": user_msg_input, "agent": output["agent_response"]}]
            st.session_state.pnr_data = output.get("pnr_data", {})


# --- 2. SESSION CONTEXT STATE INJECTION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.graph_history = []
    st.session_state.pnr_data = {}


def render_chat_text(content: str) -> None:
    html_content = format_markdown_content(content)
    st.markdown(html_content, unsafe_allow_html=True)


# --- 3. RENDERING ACTIVE CHAT WINDOW CONTEXT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        render_chat_text(message["content"])


# --- 4. PERSISTENT INTERACTIVE CHAT ENTRY COMPONENT ---
if user_input := st.chat_input("Enter message (e.g., Please book me onto TK1823)..."):
    # Render user injection string
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Process inputs through backend pipeline graph
    with st.spinner("Agent is resolving context..."):
        inputs = {
            "pnr": pnr_input,
            "user_message": user_input,
            "history": st.session_state.graph_history,
            "pnr_data": st.session_state.pnr_data,
        }
        output = app.invoke(inputs)
        
        # Display backend results inside chat thread
        with st.chat_message("assistant"):
            render_agent_message(output["agent_response"])
            
        assistant_text = format_agent_response(output["agent_response"])[0]
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
        
        # Trigger explicit visual feedback boxes upon successful settlement
        if output["next_step"] in ["rebook", "refund"]:
            st.success(f"⚙️ Enterprise Mutation Dispatched! Pipeline State: {output['next_step'].upper()}")
            st.balloons()  # Launch global success celebration triggers
            
        # Write step sequences to history buffer
        st.session_state.graph_history.append({"user": user_input, "agent": output["agent_response"]})

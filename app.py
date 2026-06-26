import json
import sys
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

# Enterprise Database Simulation
FLIGHT_DATABASE = {
    "ABC123": {
        "passenger": "Onur Gumus",
        "flight_number": "TK1823",
        "origin": "IST",
        "destination": "CDG",
        "origin_city": "Istanbul",
        "destination_city": "Paris",
        "departure_date": "2026-07-02",
        "departure_time": "08:30",
        "seat": "14A",
        "cabin": "Economy",
        "status": "CANCELLED",
        "operation_note": "",
    }
}

# --- 1. GRAPH STATE DEFINITION ---
class AgentState(TypedDict):
    pnr: str
    user_message: str
    history: List[Dict[str, str]]
    pnr_data: Dict[str, Any]
    agent_response: str
    next_step: str  # 'continue', 'rebook', 'refund', 'invalid_pnr'

# --- 2. GRAPH NODES / MCP TOOLS ---

def check_pnr_node(state: AgentState) -> Dict:
    """[MCP TOOL: check_pnr] Validates the PNR code against the database."""
    pnr_code = state["pnr"]
    print(f"\n⚙️  [NODE: Check PNR] Validating PNR: {pnr_code}...")
    
    if pnr_code in FLIGHT_DATABASE:
        return {"pnr_data": FLIGHT_DATABASE[pnr_code], "next_step": "valid"}
    else:
        return {"pnr_data": {"error": "PNR not found"}, "next_step": "invalid_pnr"}

def invalid_pnr_node(state: AgentState) -> Dict:
    """Error Handling Node: Safely intercepts bad inputs without crashing."""
    print("🚨 [NODE: Invalid PNR] Exception caught! Generating user warning...")
    msg = f"The PNR code '{state['pnr']}' could not be found in our systems. Please check your information and try again."
    return {"agent_response": msg, "next_step": "end"}

def conversation_node(state: AgentState) -> Dict:
    """[NODE: Conversation] Core reasoning node managing multi-turn dialog and intent routing."""
    print("🧠 [NODE: Conversation] Local LLM analyzing context and intent...")
    
    pnr_data = state["pnr_data"]
    user_message = state["user_message"]
    history = state["history"]
    
    alternatives = [{"flight": "TK1823", "time": "Tomorrow 08:00"}, {"flight": "LH1302", "time": "Today 21:00"}]
    refund_value = "150 USD"
    
    # Initializing local model via Ollama workbench
    model = ChatOllama(model="llama3:8b", temperature=0.1)
    
    messages = [
        SystemMessage(content="""You are a professional airline customer service assistant. Be helpful, polite, and formal.
        STRICT RULES:
        1. If the customer is just asking questions or exploring options ("Is there a refund?", "What flights are open?" etc.) or has NOT yet made an absolute confirmation, continue the talk normally. Under this condition, DO NOT append any routing tags.
        2. If and only if the customer explicitly selects or confirms a new flight option (e.g., "Book TK1823", "I choose tomorrow's flight"), append exactly [ROUTE:REBOOK] to the very end of your response text.
        3. If and only if the customer explicitly selects or confirms a cash refund (e.g., "Give me a refund", "I want my money back"), append exactly [ROUTE:REFUND] to the very end of your response text.
        
        These hidden tags orchestrate database changes. Never trigger them prematurely until the final agreement is sealed.""")
    ]
    
    # Reloading multi-turn conversation history layer
    for msg in history:
        messages.append(HumanMessage(content=msg["user"]))
        messages.append(SystemMessage(content=msg["agent"]))
        
    alternatives_text = "\n".join([f"- {alt['flight']}: {alt['time']}" for alt in alternatives])
    prompt = f"Customer Message: {user_message}\nTicket Details: {pnr_data}\nFlight Options:\n{alternatives_text}\nRefund Policy: {refund_value}"
    messages.append(HumanMessage(content=prompt))
    
    response = model.invoke(messages).content
    
    # Evaluation of intent based on downstream tags
    next_step = "continue"
    if "[ROUTE:REBOOK]" in response:
        next_step = "rebook"
    elif "[ROUTE:REFUND]" in response:
        next_step = "refund"
        
    return {"agent_response": response, "next_step": next_step}

def execute_action_node(state: AgentState) -> Dict:
    """[MCP TOOL: execute_flight_action] Executes write queries to commit state changes."""
    pnr_code = state["pnr"]
    action = state["next_step"]
    print(f"💾 [NODE: Execute Action] Committing database changes. Target Action: {action}")
    
    if action == "rebook":
        FLIGHT_DATABASE[pnr_code]["flight_number"] = "TK1823"
        FLIGHT_DATABASE[pnr_code]["departure_date"] = "2026-07-02"
        FLIGHT_DATABASE[pnr_code]["departure_time"] = "08:30"
        FLIGHT_DATABASE[pnr_code]["status"] = "RESOLVED (REBOOKED)"
        FLIGHT_DATABASE[pnr_code]["operation_note"] = "Passenger rebooked onto flight TK1823."
    elif action == "refund":
        FLIGHT_DATABASE[pnr_code]["status"] = "RESOLVED (REFUNDED)"
        FLIGHT_DATABASE[pnr_code]["operation_note"] = "150 USD cash refund process initiated."
    
    return {"pnr_data": FLIGHT_DATABASE[pnr_code]}

# --- 3. EDGE ROUTING DECISIONS ---

def route_after_check(state: AgentState):
    """Conditional Edge evaluation following data indexing step."""
    if state["next_step"] == "invalid_pnr":
        return "invalid_pnr"
    return "conversation"

def route_after_conversation(state: AgentState):
    """Conditional Edge evaluation following natural language analysis."""
    if state["next_step"] in ["rebook", "refund"]:
        return "execute_action"
    return END

# --- 4. STATE GRAPH COMPILATION ---

workflow = StateGraph(AgentState)

# Attaching modular nodes to core canvas
workflow.add_node("check_pnr", check_pnr_node)
workflow.add_node("invalid_pnr", invalid_pnr_node)
workflow.add_node("conversation", conversation_node)
workflow.add_node("execute_action", execute_action_node)

# Defining architecture grid entries and conditional connectors
workflow.set_entry_point("check_pnr")
workflow.add_conditional_edges("check_pnr", route_after_check, {"invalid_pnr": "invalid_pnr", "conversation": "conversation"})
workflow.add_conditional_edges("conversation", route_after_conversation, {"execute_action": "execute_action", END: END})
workflow.add_edge("invalid_pnr", END)
workflow.add_edge("execute_action", END)

# Compiling application blueprint
app = workflow.compile()

# --- 5. RUNTIME CONTROLLERS (CLI CHAT WORKBENCH) ---

def start_interactive_chat():
    print("\n✈️  [SYSTEM] Persistent LangGraph Airline Desk Operational...")
    pnr_code = input("⚙️  Enter your PNR reference code (e.g., ABC123): ").strip()
    
    history = []
    initial_prompt = "Hello, my flight has been cancelled. I need immediate assistance."
    
    # Launching the graph loop runtime
    inputs = {"pnr": pnr_code, "user_message": initial_prompt, "history": history}
    output = app.invoke(inputs)
    print(f"\n🤖 [AGENT]: {output['agent_response']}")
    
    if output["next_step"] == "end":
        return

    history.append({"user": initial_prompt, "agent": output['agent_response']})
    
    # Persistent interaction cycle loop
    while True:
        user_input = input("\n👤 [YOU] (Type 'exit' to quit): ").strip()
        if user_input.lower() == 'exit':
            print("Session terminated safely.")
            break
            
        inputs = {
            "pnr": pnr_code, 
            "user_message": user_input, 
            "history": history,
            "pnr_data": output.get("pnr_data", {})
        }
        
        output = app.invoke(inputs)
        print(f"\n🤖 [AGENT]: {output['agent_response']}")
        
        if output["next_step"] in ["rebook", "refund"]:
            print(f"\n📊 [UPDATED PRODUCTION DATABASE]: {FLIGHT_DATABASE[pnr_code]}")
            print("⚙️  [SYSTEM] Data mutations committed successfully. Session locked.")
            break
            
            # Appending transactional chat sequences to buffer array
        history.append({"user": user_input, "agent": output['agent_response']})

# --- 6. ANTHROPIC MODEL CONTEXT PROTOCOL (MCP) IMPLEMENTATION ---

def start_mcp_server():
    """Binds the compiled state machine directly to the Anthropic stdio transport interface."""
    from mcp.server.fastmcp import FastMCP
    mcp_server = FastMCP("Airline-Agent-Server")

    @mcp_server.tool()
    def process_flight_request(pnr: str, message: str) -> str:
        """Handles customer lookup queries, cancellations, alternative suggestions, and commits workflow adjustments."""
        result = app.invoke({"pnr": pnr, "user_message": message, "history": []})
        return f"Agent Action Result: {result['agent_response']} | Graph Pipeline Status: {result['next_step']}"

    mcp_server.run()

if __name__ == "__main__":
    # Toggling server mode vs local conversation loop via runtime flags
    if "--mcp" in sys.argv:
        start_mcp_server()
    else:
        start_interactive_chat()

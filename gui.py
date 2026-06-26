import re
import streamlit as st
from app import app

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AirAssist · Intelligent Travel Portal",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── TEXT HELPERS ───────────────────────────────────────────────────────────────
def format_agent_response(response):
    cleaned = re.sub(r"\s*\[ROUTE:(REBOOK|REFUND)\]\s*","",response).strip()
    cleaned = re.sub(r"\s*\*\s*","\n- ",cleaned)
    cleaned = re.sub(r"(?<!\n)(Refund policy:|Refund amount:)",r"\n\1",cleaned)
    m = re.search(r"\[ROUTE:(REBOOK|REFUND)\]",response)
    return cleaned, m.group(1).lower() if m else None

def md_to_html(content):
    lines=[l.rstrip() for l in content.splitlines()]
    out,in_list=[],False
    for line in lines:
        s=line.strip()
        if s.startswith(("- ","* ")):
            if not in_list: out.append("<ul style='padding-left:18px;margin:6px 0;'>"); in_list=True
            out.append(f"<li style='margin-bottom:4px;font-size:14px;color:#cbd5e1;'>{s[2:].strip()}</li>")
        else:
            if in_list: out.append("</ul>"); in_list=False
            if s=="": out.append("<div style='margin:8px 0;'></div>")
            else: out.append(f"<p style='margin:0 0 8px;line-height:1.65;font-size:14px;color:#cbd5e1;'>{s}</p>")
    if in_list: out.append("</ul>")
    return "".join(out)

def render_agent_message(response):
    cleaned, route = format_agent_response(response)
    st.markdown(md_to_html(cleaned), unsafe_allow_html=True)
    if route:
        icon = "🔁" if route=="rebook" else "💳"
        label = "Flight Rebooking Execution" if route=="rebook" else "Cash Refund Settlement"
        st.markdown(f"<div class='action-banner'>{icon} <strong>Pipeline Action:</strong> {label}</div>",unsafe_allow_html=True)
    return cleaned

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box}
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.stApp{background:#060d1f}

section[data-testid="stSidebar"]{background:#080f22!important;border-right:1px solid #0f1e3a!important}
section[data-testid="stSidebar"] label{color:#64748b!important;font-size:.73rem!important;font-weight:700!important;text-transform:uppercase;letter-spacing:.06em}
section[data-testid="stSidebar"] input,section[data-testid="stSidebar"] textarea{background:#0d1b35!important;border:1px solid #1e3a5f!important;color:#e2e8f0!important;border-radius:10px!important;font-family:'JetBrains Mono',monospace!important}
section[data-testid="stSidebar"] button{background:linear-gradient(135deg,#2563eb,#1d4ed8)!important;border:none!important;border-radius:12px!important;color:#fff!important;width:100%!important;font-weight:700!important;box-shadow:0 4px 15px rgba(37,99,235,.4)!important}

.page-header{display:flex;align-items:center;gap:16px;padding:1.5rem 0 1.1rem;border-bottom:1px solid #0f1e3a;margin-bottom:1.3rem}
.logo-mark{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#2563eb,#1d4ed8);display:flex;align-items:center;justify-content:center;font-size:1.25rem;box-shadow:0 4px 14px rgba(37,99,235,.4);flex-shrink:0}
.page-header h1{font-size:1.4rem;font-weight:800;color:#f1f5f9;margin:0;letter-spacing:-.02em}
.page-header p{font-size:.7rem;color:#475569;margin:3px 0 0;text-transform:uppercase;letter-spacing:.08em}

.boarding-pass{background:#fff;border-radius:18px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.55)}
.bp-stripe{background:linear-gradient(135deg,#1e40af,#2563eb,#0ea5e9);padding:15px 20px 11px;display:flex;justify-content:space-between;align-items:flex-start}
.bp-airline-name{color:rgba(255,255,255,.85);font-size:.6rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
.bp-flight-no{color:#fff;font-size:1.2rem;font-weight:800;font-family:'JetBrains Mono',monospace;line-height:1}
.bp-badge{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);color:#fff;font-size:.56rem;font-weight:700;padding:3px 8px;border-radius:20px;letter-spacing:.1em;text-transform:uppercase;white-space:nowrap}
.bp-route{padding:13px 20px 11px;display:flex;align-items:center;gap:8px;background:#fff}
.bp-city-block{flex:1}
.bp-iata{font-size:1.9rem;font-weight:800;color:#0f172a;line-height:1;font-family:'JetBrains Mono',monospace}
.bp-city-name{font-size:.58rem;color:#94a3b8;margin-top:2px;font-weight:500}
.bp-plane{flex:0 0 auto;display:flex;flex-direction:column;align-items:center;gap:3px}
.bp-plane-icon{font-size:1rem;color:#2563eb}
.bp-plane-line{width:44px;height:1px;background:linear-gradient(90deg,#e2e8f0,#2563eb,#e2e8f0)}
.bp-meta-grid{padding:9px 20px 11px;display:grid;grid-template-columns:1fr 1fr;gap:7px 12px;background:#fff;border-top:1px solid #f1f5f9}
.bp-meta-field label{display:block;font-size:.54rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:2px}
.bp-meta-field span{display:block;font-size:.78rem;font-weight:700;color:#1e293b;font-family:'JetBrains Mono',monospace}
.bp-perf{display:flex;align-items:center;background:#fff}
.bp-perf::before,.bp-perf::after{content:'';flex-shrink:0;width:15px;height:15px;border-radius:50%;background:#060d1f}
.bp-perf-line{flex:1;border-top:2px dashed #e2e8f0;margin:0 3px}
.bp-bottom{padding:9px 20px 7px;background:#fff;display:flex;justify-content:space-between;align-items:center}
.bp-lbl{font-size:.54rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em}
.bp-name{font-size:.85rem;font-weight:800;color:#0f172a;letter-spacing:.03em}
.bp-pnr{font-size:.9rem;font-weight:800;color:#2563eb;font-family:'JetBrains Mono',monospace;letter-spacing:.12em}
.bp-barcode{padding:5px 20px 9px;background:#fff;display:flex;gap:1px;align-items:flex-end;height:36px}
.bp-bar{background:#0f172a;border-radius:1px}
.bp-status-row{padding:6px 20px;background:#f8fafc;border-top:1px solid #f1f5f9;display:flex;align-items:center;justify-content:flex-end}
.bp-status{display:inline-flex;align-items:center;gap:4px;font-size:.58rem;font-weight:700;padding:3px 9px;border-radius:20px;text-transform:uppercase;letter-spacing:.06em}
.bp-status.ok{background:#dcfce7;color:#15803d}
.bp-status.warn{background:#fef3c7;color:#92400e}
.bp-status.err{background:#fee2e2;color:#991b1b}

.outfit-card{background:linear-gradient(145deg,#0f1a2e,#0b1526);border:1px solid #1a3050;border-radius:18px;padding:18px 20px}
.oc-eyebrow{font-size:.58rem;font-weight:700;color:#2563eb;text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px}
.oc-title{font-size:.98rem;font-weight:800;color:#f1f5f9;margin-bottom:2px}
.oc-sub{font-size:.7rem;color:#64748b;margin-bottom:11px}
.oc-items{display:flex;flex-direction:column;gap:5px}
.oc-item{display:flex;align-items:center;gap:9px;background:rgba(37,99,235,.06);border:1px solid rgba(37,99,235,.12);border-radius:9px;padding:6px 11px;font-size:.76rem;color:#cbd5e1}

.empty-card{border:2px dashed #0f1e3a;border-radius:18px;padding:28px 16px;text-align:center}
.empty-card .ec-icon{font-size:1.7rem;margin-bottom:7px}
.empty-card .ec-text{font-size:.76rem;color:#334155;line-height:1.5}

.action-banner{margin-top:12px;padding:11px 16px;border-radius:12px;background:rgba(37,99,235,.1);border-left:3px solid #2563eb;font-size:.82rem;color:#93c5fd;display:flex;align-items:center;gap:8px}
.action-banner strong{color:#60a5fa}

[data-testid="stChatMessage"]{background:transparent!important}
.stChatInput>div{background:#0d1b35!important;border:1px solid #1e3a5f!important;border-radius:14px!important}
.stChatInput textarea{color:#e2e8f0!important;background:transparent!important;font-size:14px!important}
.sec-label{font-size:.57rem;font-weight:700;color:#334155;text-transform:uppercase;letter-spacing:.1em;margin-bottom:7px}
</style>
""", unsafe_allow_html=True)

# ── RENDERERS ─────────────────────────────────────────────────────────────────
def make_barcode(seed):
    chars=(seed*6)[:32]; bars=""
    for i,c in enumerate(chars):
        w=(ord(c)%4)+1; h=26 if i%5==0 else 18
        bars+=f"<div class='bp-bar' style='width:{w}px;height:{h}px;'></div>"
    return bars

def render_boarding_pass(pnr, data):
    flight  = data.get("flight_number") or "—"
    origin  = data.get("origin") or "—"
    dest    = data.get("destination") or "—"
    orig_c  = data.get("origin_city") or "—"
    dest_c  = data.get("destination_city") or "—"
    date    = data.get("departure_date") or "—"
    dep_t   = data.get("departure_time") or "—"
    seat    = data.get("seat") or "—"
    cabin   = data.get("cabin") or data.get("class") or "—"
    pax     = data.get("passenger_name") or data.get("passenger") or ""
    raw_s   = data.get("status","CONFIRMED").upper()
    scls    = {"CANCELLED":"err","DELAYED":"warn"}.get(raw_s,"ok")
    sdot    = {"ok":"🟢","warn":"🟡","err":"🔴"}[scls]
    bc      = make_barcode(pnr)
    pax_display = pax.upper() if pax else "—"
    st.markdown(f"""
<div class="boarding-pass">
  <div class="bp-stripe">
    <div><div class="bp-airline-name">✈ Gumusler Airlines</div><div class="bp-flight-no">{flight}</div></div>
    <span class="bp-badge">Boarding Pass</span>
  </div>
  <div class="bp-route">
    <div class="bp-city-block"><div class="bp-iata">{origin}</div><div class="bp-city-name">{orig_c}</div></div>
    <div class="bp-plane"><div class="bp-plane-icon">✈</div><div class="bp-plane-line"></div></div>
    <div class="bp-city-block" style="text-align:right"><div class="bp-iata" style="text-align:right">{dest}</div><div class="bp-city-name" style="text-align:right">{dest_c}</div></div>
  </div>
  <div class="bp-meta-grid">
    <div class="bp-meta-field"><label>Date</label><span>{date}</span></div>
    <div class="bp-meta-field"><label>Departure</label><span>{dep_t}</span></div>
    <div class="bp-meta-field"><label>Seat</label><span>{seat}</span></div>
    <div class="bp-meta-field"><label>Class</label><span>{cabin}</span></div>
  </div>
  <div class="bp-perf"><div class="bp-perf-line"></div></div>
  <div class="bp-bottom">
    <div><div class="bp-lbl">Passenger</div><div class="bp-name">{pax_display}</div></div>
    <div style="text-align:right"><div class="bp-lbl">Booking Ref</div><div class="bp-pnr">{pnr}</div></div>
  </div>
  <div class="bp-barcode">{bc}</div>
  <div class="bp-status-row"><span class="bp-status {scls}">{sdot} {raw_s}</span></div>
</div>""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages       = []
    st.session_state.graph_history  = []
    st.session_state.pnr_data       = {}
    st.session_state.passenger_name = ""

# ── PAGE HEADER ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div class="logo-mark">✈️</div>
  <div>
    <h1>AirAssist · Intelligent Portal</h1>
    <p>LangGraph · Llama 3 · Real-time Disruption Resolution</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🛂 Passenger Verification")
    st.markdown("<hr style='border:none;border-top:1px solid #0f1e3a;margin:6px 0 12px'>", unsafe_allow_html=True)
    passenger_name = st.text_input("Full Name", placeholder="Name & Surname")
    pnr_input      = st.text_input("PNR Reference", value="ABC123")
    user_msg_input = st.text_area("Describe your issue", value="My flight has been cancelled. I need help.", height=80)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if st.button("🚀  Start Session"):
        st.session_state.messages       = []
        st.session_state.graph_history  = []
        st.session_state.pnr_data       = {}
        st.session_state.passenger_name = passenger_name
        with st.spinner("Connecting to LangGraph pipeline…"):
            inputs = {"pnr": pnr_input, "user_message": user_msg_input, "history": []}
            output = app.invoke(inputs)
            assistant_text = format_agent_response(output["agent_response"])[0]
            st.session_state.messages.append({"role": "assistant", "content": assistant_text})
            st.session_state.graph_history = [{"user": user_msg_input, "agent": output["agent_response"]}]
            st.session_state.pnr_data      = output.get("pnr_data", {})

    st.markdown("<hr style='border:none;border-top:1px solid #0f1e3a;margin:14px 0 10px'>", unsafe_allow_html=True)
    st.markdown("""
<div style='font-size:.67rem;color:#334155;line-height:1.7;'>
  <strong style='color:#1e3a5f;'>LangGraph</strong> orchestrates multi-step decisions.<br>
  <strong style='color:#1e3a5f;'>Llama 3</strong> runs locally — full data privacy.
</div>""", unsafe_allow_html=True)

# ── INFO STRIP — boarding pass ────────────────────────────────────────────────
if st.session_state.pnr_data:
    card_data = dict(st.session_state.pnr_data)
    card_data["passenger_name"] = st.session_state.get("passenger_name","")

    st.markdown("<div class='sec-label'>🎫 Your Ticket</div>", unsafe_allow_html=True)
    render_boarding_pass(pnr_input, card_data)
    st.markdown("<hr style='border:none;border-top:1px solid #0f1e3a;margin:.8rem 0 1.1rem'>", unsafe_allow_html=True)
else:
    st.markdown("""<div class="empty-card"><div class="ec-icon">🎫</div>
<div class="ec-text">Enter your PNR &amp; start a session<br>to view your boarding pass.</div></div>""", unsafe_allow_html=True)
    st.markdown("<hr style='border:none;border-top:1px solid #0f1e3a;margin:.8rem 0 1.1rem'>", unsafe_allow_html=True)

# ── CHAT ──────────────────────────────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(md_to_html(message["content"]), unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
<div style='text-align:center;padding:50px 20px 30px;'>
  <div style='font-size:3rem;margin-bottom:12px;'>💬</div>
  <div style='font-size:.95rem;font-weight:700;color:#1e3a5f;margin-bottom:6px;'>Your AI travel assistant is ready.</div>
  <div style='font-size:.8rem;color:#334155;line-height:1.6;max-width:360px;margin:0 auto;'>
    Start a session from the sidebar to manage your booking, rebook flights, or request a refund.
  </div>
</div>""", unsafe_allow_html=True)

if user_input := st.chat_input("Ask anything — 'Rebook me on TK1823', 'What's my refund?'…"):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Processing…"):
        inputs = {
            "pnr":          pnr_input,
            "user_message": user_input,
            "history":      st.session_state.graph_history,
            "pnr_data":     st.session_state.pnr_data,
        }
        output = app.invoke(inputs)

    with st.chat_message("assistant"):
        render_agent_message(output["agent_response"])

    assistant_text = format_agent_response(output["agent_response"])[0]
    st.session_state.messages.append({"role": "assistant", "content": assistant_text})

    if output["next_step"] in ["rebook","refund"]:
        st.success(f"⚙️ Pipeline action dispatched → **{output['next_step'].upper()}**")
        st.balloons()

    st.session_state.graph_history.append({"user": user_input, "agent": output["agent_response"]})

    if output.get("pnr_data"):
        st.session_state.pnr_data = output["pnr_data"]
        if output["next_step"] in ["rebook","refund"]:
            st.rerun()
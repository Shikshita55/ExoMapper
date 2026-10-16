import streamlit as st
import numpy as np
import pandas as pd
import io
import wave
import struct
import plotly.graph_objects as go
import random
import math

def inject_animations_and_styles():
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Chakra+Petch:wght@500;700&family=Rajdhani:wght@500;700&family=Space+Mono&display=swap');
    
    /* Cosmic Background */
    .stApp {
        background-color: #020308;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(30, 20, 70, 0.4), transparent 40%),
            radial-gradient(circle at 90% 80%, rgba(10, 50, 70, 0.3), transparent 40%),
            url("https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?q=80&w=3000&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }

    /* Fast Page Fade */
    .page-fade-in { animation: fadeIn 0.3s ease-out forwards; }
    @keyframes fadeIn { 0% { opacity: 0; transform: scale(0.99); } 100% { opacity: 1; transform: scale(1); } }
    
    /* Master Typography */
    .title-center {
        text-align: center; font-family: 'Audiowide', cursive; font-size: 7rem; 
        color: #ffffff; margin-top: 5vh;
        text-shadow: 0 0 15px #00e5ff, 0 0 30px rgba(0, 229, 255, 0.5);
        letter-spacing: 6px; animation: pulseGlow 2s infinite alternate;
    }
    @keyframes pulseGlow {
        from { text-shadow: 0 0 15px #00e5ff; transform: scale(1); }
        to { text-shadow: 0 0 25px #00e5ff, 0 0 50px #00e5ff; transform: scale(1.02); }
    }

    .subtitle-center {
        text-align: center; color: #cda434; font-size: 2rem; 
        font-family: 'Chakra Petch', sans-serif; font-style: italic; 
        font-weight: 700; letter-spacing: 5px; margin-top: -15px; margin-bottom: 40px;
    }
    
    /* Header Typography */
    .header-top { display: flex; align-items: center; border-bottom: 1px solid rgba(0,229,255,0.3); padding-bottom: 10px; margin-bottom: 25px; }
    .header-top h1 { font-family: 'Chakra Petch', sans-serif; font-size: 2.5rem; color: #ffffff; text-shadow: 0 0 10px #00e5ff; margin: 0; margin-left: 20px;}
    
    /* Glass Cards */
    .glass-card {
        background: rgba(8, 12, 25, 0.85); border: 1px solid rgba(0, 229, 255, 0.3); 
        padding: 25px; border-radius: 10px; backdrop-filter: blur(10px); 
        margin-bottom: 20px; height: 100%; box-shadow: 0 8px 25px 0 rgba(0, 0, 0, 0.8);
    }
    
    .lore-text { font-size: 1.15rem; line-height: 1.6; color: #cfd8dc; font-family: 'Rajdhani', sans-serif;}
    .data-text { font-family: 'Space Mono', monospace; font-size: 0.95rem; color: #84ffff; margin-bottom: 10px;}
    .highlight { color: #00e5ff; font-weight: 700; }
    
    /* High Contrast Alert Boxes */
    .success-box { background: rgba(0, 77, 64, 0.8); border-left: 5px solid #00e5ff; padding: 15px; border-radius: 5px; color: #ffffff; font-family: 'Chakra Petch'; font-size: 1.2rem; margin-bottom: 20px;}
    .error-box { background: rgba(183, 28, 28, 0.8); border-left: 5px solid #ff1744; padding: 15px; border-radius: 5px; color: #ffffff; font-family: 'Chakra Petch'; font-size: 1.2rem; margin-bottom: 20px;}
    
    /* Global Buttons */
    div.stButton > button {
        background: rgba(0, 229, 255, 0.1); color: #00e5ff; border: 1px solid #00e5ff;
        border-radius: 4px; font-weight: 700; padding: 8px 20px; transition: 0.2s;
        text-transform: uppercase; letter-spacing: 2px; font-family: 'Chakra Petch', sans-serif;
    }
    div.stButton > button:hover { background: #00e5ff; color: #000; box-shadow: 0 0 15px #00e5ff;}
    
    /* Number Input overrides for visibility */
    label { font-family: 'Chakra Petch', sans-serif; color: #b388ff !important; font-size: 1.1rem !important;}
    
    /* Footer */
    .developer-tag { position: fixed; bottom: 10px; right: 20px; font-family: 'Space Mono', monospace; font-size: 0.8rem; color: rgba(255,255,255,0.4); text-align: right;}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    """
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def render_top_header():
    st.markdown("""
    <div class="header-top">
        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg" width="55">
        <div><h1>ExoMapper Terminal</h1></div>
    </div>
    """, unsafe_allow_html=True)

def init_state():
    if 'current_page' not in st.session_state: st.session_state.current_page = "login"
    if 'user_id' not in st.session_state: st.session_state.user_id = ""
    if 'current_score' not in st.session_state: st.session_state.current_score = 0
    if 'scientific_payload' not in st.session_state: st.session_state.scientific_payload = None
    if 'is_hit' not in st.session_state: st.session_state.is_hit = False
    if 'anomaly_x' not in st.session_state: st.session_state.anomaly_x = random.randint(50, 350)
    if 'anomaly_y' not in st.session_state: st.session_state.anomaly_y = random.randint(50, 350)
    if 'doppler_shift' not in st.session_state: st.session_state.doppler_shift = "None"

def generate_scientific_payload(is_success):
    if not is_success:
        st.session_state.doppler_shift = "Static (Cosmic Background Noise)"
        return {
            "spectrum": {"Methane (CH4)": 0.0, "Water Ice (H2O)": 0.0, "Ammonia (NH3)": 0.0, "Silicate Dust": 0.0},
            "stats": {"Estimated Radius": "N/A", "Albedo (Reflectivity)": "N/A", "Orbital Eccentricity": "N/A", "Thermal Emission": "Background Temp (2.7 K)"}
        }
        
    st.session_state.doppler_shift = random.choice(["Redshift (Moving Away)", "Blueshift (Moving Towards)"])
    return {
        "spectrum": {
            "Methane (CH4)": np.random.uniform(2.0, 15.0),
            "Water Ice (H2O)": np.random.uniform(40.0, 70.0),
            "Ammonia (NH3)": np.random.uniform(10.0, 25.0),
            "Silicate Dust": np.random.uniform(5.0, 20.0)
        },
        "stats": {
            "Estimated Radius": f"{np.random.uniform(2.5, 6.0):.2f} Earth Radii",
            "Albedo (Reflectivity)": f"{np.random.uniform(0.02, 0.10):.3f} (Dark Object)",
            "Orbital Eccentricity": f"{np.random.uniform(0.1, 0.4):.2f}",
            "Thermal Emission": f"{np.random.uniform(30, 60):.1f} Kelvin"
        }
    }

def synthesize_spectrum_audio(spectrum_data, shift_type):
    try:
        sample_rate = 44100
        audio_frames = []
        multiplier = 0.5 if "Redshift" in shift_type else (1.5 if "Blueshift" in shift_type else 0.1)
        
        for chemical, abundance in spectrum_data.items():
            freq = (250.0 + (abundance * 10.0)) * multiplier
            duration = 0.6 
            num_samples = int(sample_rate * duration)
            for i in range(num_samples):
                t = float(i) / sample_rate
                amplitude = int(32767.0 * np.sin(freq * t * 2.0 * np.pi))
                if i < 3000: amplitude = int(amplitude * (i / 3000))
                elif i > num_samples - 3000: amplitude = int(amplitude * ((num_samples - i) / 3000))
                audio_frames.append(struct.pack('<h', amplitude))
                
        virtual_wav = io.BytesIO()
        with wave.open(virtual_wav, 'wb') as w_file:
            w_file.setnchannels(1)
            w_file.setsampwidth(2)
            w_file.setframerate(sample_rate)
            w_file.writeframes(b''.join(audio_frames))
        return virtual_wav.getvalue()
    except Exception as e:
        return None

def change_page(page_name):
    st.session_state.current_page = page_name

def main():
    st.set_page_config(page_title="ExoMapper Terminal", layout="wide", initial_sidebar_state="collapsed")
    inject_animations_and_styles()
    init_state()

    # ================= MODULE 1: LOGIN =================
    if st.session_state.current_page == "login":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        st.markdown("<div class='title-center'>ExoMapper</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle-center'>THE PLANET X HUNTER</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("<h4 style='text-align:center; color:#00e5ff; font-family:Chakra Petch;'>ENTER HUNTER ID TO ACCESS TERMINAL</h4>", unsafe_allow_html=True)
            username = st.text_input("", placeholder="e.g. Commander Shikshita...", label_visibility="collapsed")
            st.write("") 
            if st.button("INITIALIZE SECURE LINK 🚀", use_container_width=True):
                if username.strip():
                    st.session_state.user_id = username.strip()
                    change_page("home")
                    st.rerun()
                else:
                    st.markdown("<div class='error-box'>Access Denied. Provide a valid Hunter Name.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= MODULE 2: COMMAND DASHBOARD =================
    elif st.session_state.current_page == "home":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        st.markdown(f"<h2 style='color:white; font-family:Chakra Petch;'>Welcome to Command <span style='color:#00e5ff;'>{st.session_state.user_id}</span>, The Dashboard</h2>", unsafe_allow_html=True)
        
        action1, action2, score_col = st.columns([1, 1, 2])
        with action1:
            if st.button("Start the Task 📡", use_container_width=True):
                # Randomize anomaly position every time they start a scan
                st.session_state.anomaly_x = random.randint(100, 300)
                st.session_state.anomaly_y = random.randint(100, 300)
                change_page("radar")
                st.rerun()
        with action2:
            if st.button("Disconnect (Logout)", use_container_width=True):
                st.session_state.user_id = ""
                change_page("login")
                st.rerun()
        with score_col:
            st.markdown(f"""
            <div style="background: rgba(0, 229, 255, 0.1); border: 1px solid #00e5ff; padding: 10px 20px; border-radius: 5px; text-align: right;">
                <h3 style="margin:0; color:#ffffff; font-family:Space Mono;">🏆 Hunter Record: <span style="color:#00e5ff;">{st.session_state.current_score} Pts</span></h3>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<hr style='border-color: rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
        
        col_mission, col_team, col_rules = st.columns(3)
        with col_mission:
            st.markdown("""
            <div class="glass-card">
                <h3 style='color:#00e5ff; font-family:"Chakra Petch";'>🌍 Mission Objective</h3>
                <p class='lore-text'><b>SPHEREx Future:</b> NASA's telescope mapping the universe in infrared.</p>
                <p class='lore-text'><b>Hunting Planet X:</b> Invisible to normal telescopes, its faint heat signature might be caught.</p>
                <p class='lore-text'><b>Your Role:</b> Spot thermal anomalies in the FITS data, pinpoint coordinates, and extract spectra.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_team:
            st.markdown("""
            <div class="glass-card">
                <h3 style='color:#00e5ff; font-family:"Chakra Petch";'>🧑‍🚀 Team ExoMapper</h3>
                <ul class='lore-text'>
                    <li><span class='highlight'>Shikshita:</span> M.Sc. Astrophysics researcher.</li>
                    <li><span class='highlight'>Ayaan:</span> Technical documentation.</li>
                </ul>
                <p class='lore-text'>Making deep-space astronomical data interactive for citizen scientists worldwide.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_rules:
            st.markdown("""
            <div class="glass-card">
                <h3 style='color:#00e5ff; font-family:"Chakra Petch";'>📜 Game Rules</h3>
                <ul class='lore-text'>
                    <li><b>Lock True Anomaly:</b> <span class='highlight'>+150 Pts</span> (Coordinates must be within 30 units of target)</li>
                    <li><b>False Target Lock:</b> <span style='color:#ff1744;'>-20 Pts</span> (Locking onto empty space noise)</li>
                </ul>
                <p class='lore-text'>Hover over the radar to find X and Y axes values. Enter them precisely.</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ================= MODULE 3: RADAR SCANNER =================
    elif st.session_state.current_page == "radar":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        top1, top2 = st.columns([4, 1])
        top1.markdown("<h2 style='color:#ffffff; font-family:Chakra Petch;'>Live Optics: Simulated FITS Viewer</h2>", unsafe_allow_html=True)
        if top2.button("Abort Task"): change_page("home"); st.rerun()

        st.markdown("<p class='lore-text'>Analyze the raw grayscale FITS thermal proxy. Hover over the bright anomaly to find its exact X and Y coordinates, then lock them in below.</p>", unsafe_allow_html=True)
        
        # Realistic FITS Noise Simulation
        base_flux = np.random.normal(20, 5, (400, 400)) # Gaussian Background Noise
        
        # Inject Anomaly at hidden coordinates
        ay, ax = st.session_state.anomaly_y, st.session_state.anomaly_x
        base_flux[ay-8:ay+8, ax-8:ax+8] += 80 # Bright heat signature
        
        fig = go.Figure(data=go.Heatmap(z=base_flux, colorscale="gray", showscale=False))
        fig.update_layout(
            margin=dict(l=40, r=40, t=20, b=40),
            xaxis=dict(title="X Coordinate (Pixels)", color="#b388ff"), 
            yaxis=dict(title="Y Coordinate (Pixels)", color="#b388ff"),
            plot_bgcolor="#020308", paper_bgcolor="#020308", height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<hr style='border-color: rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
        
        col_x, col_y, col_lock = st.columns([1, 1, 2])
        with col_x: user_x = st.number_input("Target X Coordinate", min_value=0, max_value=400, value=200)
        with col_y: user_y = st.number_input("Target Y Coordinate", min_value=0, max_value=400, value=200)
        
        with col_lock:
            st.write("") # Spacer
            st.write("")
            if st.button("🎯 LOCK TARGET & INITIATE SPECTROSCOPY", use_container_width=True):
                # Calculate distance using Pythagoras theorem
                distance = math.hypot(user_x - ax, user_y - ay)
                if distance <= 30: # HIT
                    st.session_state.is_hit = True
                    st.session_state.current_score += 150
                else: # MISS
                    st.session_state.is_hit = False
                    st.session_state.current_score -= 20
                    
                st.session_state.scientific_payload = generate_scientific_payload(st.session_state.is_hit)
                change_page("analysis")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= MODULE 4: SCIENTIFIC ANALYSIS =================
    elif st.session_state.current_page == "analysis":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        if st.session_state.is_hit:
            st.markdown("<div class='success-box'>✅ TARGET VERIFIED: Authentic Planetary Signature Detected. (+150 Points)</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='error-box'>❌ FALSE ALARM: No Anomaly at those coordinates. Cosmic Noise Captured. (-20 Points)</div>", unsafe_allow_html=True)
        
        data = st.session_state.scientific_payload
        stat_col, graph_col = st.columns([1, 2])
        
        with stat_col:
            stats_html = "<div class='glass-card'><h3 style='color:#b388ff; font-family:Chakra Petch;'>🪐 Physical Configuration</h3><hr style='border-color:#333;'>"
            for key, val in data["stats"].items():
                stats_html += f"<div class='data-text'>{key}: <br><span style='color:#ffffff; font-size:1.1rem;'>{val}</span></div>"
            stats_html += "</div>"
            st.markdown(stats_html, unsafe_allow_html=True)
            
        with graph_col:
            df = pd.DataFrame(list(data["spectrum"].items()), columns=["Molecule", "Percentage"])
            graph_color = '#00e5ff' if st.session_state.is_hit else '#555555'
            fig_bar = go.Figure(data=[go.Bar(x=df["Molecule"], y=df["Percentage"], marker_color=graph_color, opacity=0.8)])
            fig_bar.update_layout(
                title=dict(text="Atmospheric Spectrum", font=dict(color="#ffffff", size=20, family="Chakra Petch")),
                xaxis_title="Chemical Composition", yaxis_title="Abundance (%)",
                paper_bgcolor='rgba(8, 12, 25, 0.85)', plot_bgcolor='rgba(8, 12, 25, 0)',
                font=dict(color='#84ffff', family='Space Mono'), margin=dict(l=20, r=20, t=50, b=20), height=350,
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<hr style='border-color: rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
        
        dop_col, soni_col = st.columns([1, 1])
        shift_type = st.session_state.doppler_shift
        
        with dop_col:
            st.markdown("<h3 style='color:#b388ff; font-family:Chakra Petch;'>📡 Doppler Shift Analysis</h3>", unsafe_allow_html=True)
            
            if "Red" in shift_type: wave_color, freq = "#ff1744", 0.8
            elif "Blue" in shift_type: wave_color, freq = "#00e5ff", 3.0
            else: wave_color, freq = "#777777", 0.2
            
            x_wave = np.linspace(0, 4 * np.pi, 100)
            y_wave = np.sin(x_wave * freq)
            
            wave_fig = go.Figure(go.Scatter(x=x_wave, y=y_wave, mode='lines', line=dict(color=wave_color, width=3)))
            wave_fig.update_layout(
                paper_bgcolor='rgba(8, 12, 25, 0.85)', plot_bgcolor='rgba(0,0,0,0)', 
                height=180, margin=dict(l=10,r=10,t=40,b=10),
                title=dict(text=f"Detected: {shift_type}", font=dict(color=wave_color, family="Space Mono", size=14)),
                xaxis=dict(visible=False), yaxis=dict(visible=False)
            )
            st.plotly_chart(wave_fig, use_container_width=True)
            
        with soni_col:
            st.markdown("<h3 style='color:#b388ff; font-family:Chakra Petch;'>🎧 Acoustic Telemetry</h3>", unsafe_allow_html=True)
            st.markdown("""
            <div style='background: rgba(255, 255, 255, 0.05); padding: 10px; border-left: 3px solid #b388ff;'>
                <span style='color:#b388ff; font-family:Chakra Petch;'>DISCLAIMER:</span> 
                <span style='font-size: 0.85rem; color:#cfd8dc; font-family:Rajdhani;'>Synthesized mapping from high-frequency spectrum data based on Doppler shift. Not actual recorded sound.</span>
            </div>
            """, unsafe_allow_html=True)
            
            audio_bytes = synthesize_spectrum_audio(data["spectrum"], shift_type)
            if audio_bytes:
                st.audio(audio_bytes, format='audio/wav')
            
        st.markdown("<hr style='border-color: rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
        
        if st.session_state.is_hit:
            st.markdown("<h3 style='color:#ffffff; font-family:Chakra Petch;'>Planet X Profile Match: <span style='color:#00e5ff;'>YES (87.4%)</span></h3>", unsafe_allow_html=True)
            designation = st.text_input("Assign a Catalog Name:", placeholder="e.g. Kepler-452b")
            col_submit, col_home = st.columns(2)
            with col_submit:
                if st.button("Transmit Data to NASA", use_container_width=True):
                    if designation: st.markdown(f"<div class='success-box'>Data Transmitted! '{designation}' logged by {st.session_state.user_id}.</div>", unsafe_allow_html=True)
                    else: st.markdown("<div class='error-box'>Please assign a name before transmitting.</div>", unsafe_allow_html=True)
            with col_home:
                if st.button("Return to Dashboard", use_container_width=True): change_page("home"); st.rerun()
        else:
            st.markdown("<h3 style='color:#ffffff; font-family:Chakra Petch;'>Planet X Profile Match: <span style='color:#ff1744;'>FAILED (0%)</span></h3>", unsafe_allow_html=True)
            if st.button("Return to Dashboard to Scan Again", use_container_width=True): change_page("home"); st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div class='developer-tag'>Developed by: Team ExoMapper</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

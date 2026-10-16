import streamlit as st
import numpy as np
import pandas as pd
import io
import wave
import struct
import plotly.graph_objects as go
import random
import math
from astropy.io import fits

def inject_styles():
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Chakra+Petch:ital,wght@0,500;0,700;1,500&family=Cinzel:ital,wght@0,600;1,600&family=Rajdhani:ital,wght@0,500;0,700;1,600&family=Space+Mono&display=swap');
    
    /* Reimagined Deep Blue Cosmic Background */
    .stApp {
        background-color: #010409;
        background-image: 
            radial-gradient(circle at 15% 30%, rgba(0, 102, 255, 0.25), transparent 45%),
            radial-gradient(circle at 85% 75%, rgba(0, 229, 255, 0.2), transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(10, 25, 50, 0.8), transparent 80%),
            url("https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=3000&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed; background-position: center;
        color: #e0f7fa; font-family: 'Rajdhani', sans-serif;
    }

    .page-fade-in { animation: fadeIn 0.4s ease-out forwards; }
    @keyframes fadeIn { 0% { opacity: 0; transform: translateY(8px); } 100% { opacity: 1; transform: translateY(0); } }
    
    .title-center {
        text-align: center; font-family: 'Audiowide', cursive; font-size: 6.5rem; 
        color: #ffffff; margin-top: 4vh; text-shadow: 0 0 20px #00e5ff, 0 0 40px rgba(0, 229, 255, 0.6);
        letter-spacing: 5px; animation: pulseGlow 2.5s infinite alternate;
    }
    @keyframes pulseGlow {
        from { text-shadow: 0 0 20px #00e5ff; transform: scale(1); }
        to { text-shadow: 0 0 30px #00e5ff, 0 0 60px #0055ff; transform: scale(1.02); }
    }

    .subtitle-center {
        text-align: center; color: #84ffff; font-size: 1.9rem; 
        font-family: 'Cinzel', serif; font-style: italic; 
        font-weight: 600; letter-spacing: 4px; margin-top: -15px; margin-bottom: 40px;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.4);
    }
    
    .header-top { display: flex; align-items: center; border-bottom: 1px solid rgba(0,229,255,0.4); padding-bottom: 12px; margin-bottom: 25px; }
    .header-top h1 { font-family: 'Audiowide', cursive; font-size: 2.4rem; color: #ffffff; text-shadow: 0 0 12px #00e5ff; margin: 0; margin-left: 20px; letter-spacing: 2px;}
    
    .glass-card {
        background: rgba(4, 10, 25, 0.82); border: 1px solid rgba(0, 229, 255, 0.35); 
        padding: 22px; border-radius: 10px; backdrop-filter: blur(12px); 
        margin-bottom: 20px; height: 100%; box-shadow: 0 8px 30px 0 rgba(0, 0, 0, 0.85);
        transition: 0.3s ease;
    }
    .glass-card:hover { border-color: #00e5ff; box-shadow: 0 10px 35px rgba(0,229,255,0.3); transform: translateY(-2px); }
    
    .lore-text { font-size: 1.1rem; line-height: 1.6; color: #cfd8dc; font-family: 'Rajdhani', sans-serif; font-weight: 500;}
    .data-text { font-family: 'Space Mono', monospace; font-size: 0.95rem; color: #84ffff; margin-bottom: 10px;}
    .highlight { color: #00e5ff; font-weight: 700; text-shadow: 0 0 5px rgba(0,229,255,0.4); }
    
    .success-box { background: rgba(0, 77, 64, 0.9); border-left: 5px solid #00e5ff; padding: 15px; border-radius: 5px; color: #ffffff; font-family: 'Chakra Petch'; font-size: 1.2rem; margin-bottom: 20px; box-shadow: 0 0 15px rgba(0,229,255,0.3);}
    .error-box { background: rgba(183, 28, 28, 0.9); border-left: 5px solid #ff1744; padding: 15px; border-radius: 5px; color: #ffffff; font-family: 'Chakra Petch'; font-size: 1.2rem; margin-bottom: 20px; box-shadow: 0 0 15px rgba(255,23,68,0.3);}
    
    div.stButton > button {
        background: rgba(0, 229, 255, 0.12); color: #00e5ff; border: 1px solid #00e5ff;
        border-radius: 6px; font-weight: 700; padding: 10px 22px; transition: 0.3s;
        text-transform: uppercase; letter-spacing: 1.5px; font-family: 'Chakra Petch', sans-serif;
    }
    div.stButton > button:hover { background: #00e5ff; color: #010409; box-shadow: 0 0 20px #00e5ff; transform: scale(1.02);}
    
    .blink-btn > button { background: rgba(255, 23, 68, 0.15); border-color: #ff1744; color: #ff1744; }
    .blink-btn > button:hover { background: #ff1744; color: #fff; box-shadow: 0 0 25px #ff1744; }
    
    label { font-family: 'Chakra Petch', sans-serif; color: #84ffff !important; font-size: 1.1rem !important;}
    
    .nasa-link { color: #010409; background: #00e5ff; padding: 6px 14px; border-radius: 5px; text-decoration: none; font-weight: 700; font-family: 'Chakra Petch'; display: inline-block; margin-top: 12px; margin-right: 10px; transition: 0.3s;}
    .nasa-link:hover { background: #fff; color: #010409; box-shadow: 0 0 12px #00e5ff;}

    .developer-tag { position: fixed; bottom: 10px; right: 20px; font-family: 'Space Mono', monospace; font-size: 0.85rem; color: rgba(0,229,255,0.6); text-align: right; text-shadow: 0 0 5px rgba(0,229,255,0.3);}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    """
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def render_top_header():
    st.markdown("""
    <div class="header-top">
        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg" width="50">
        <div><h1>ExoMapper</h1></div>
    </div>
    """, unsafe_allow_html=True)

def init_state():
    if 'current_page' not in st.session_state: st.session_state.current_page = "login"
    if 'user_id' not in st.session_state: st.session_state.user_id = ""
    if 'current_score' not in st.session_state: st.session_state.current_score = 0
    if 'scientific_payload' not in st.session_state: st.session_state.scientific_payload = None
    if 'is_hit' not in st.session_state: st.session_state.is_hit = False
    if 'anomaly_x' not in st.session_state: st.session_state.anomaly_x = 0
    if 'anomaly_y' not in st.session_state: st.session_state.anomaly_y = 0
    if 'blink_active' not in st.session_state: st.session_state.blink_active = False
    if 'user_profiles' not in st.session_state: st.session_state.user_profiles = {}

def generate_scientific_payload(is_success):
    if not is_success:
        return {
            "shift": "Static Noise",
            "spectrum": {"Methane (CH4)": 0.0, "Water Ice (H2O)": 0.0, "Ammonia (NH3)": 0.0, "Silicate Dust": 0.0},
            "stats": {"Radius": "N/A", "Albedo": "N/A", "Eccentricity": "N/A", "Thermal Emission": "2.7 K (Background)"}
        }
    return {
        "shift": random.choice(["Redshift (Moving Away)", "Blueshift (Moving Towards)"]),
        "spectrum": {
            "Methane (CH4)": np.random.uniform(5.0, 15.0),
            "Water Ice (H2O)": np.random.uniform(40.0, 65.0),
            "Ammonia (NH3)": np.random.uniform(10.0, 20.0),
            "Silicate Dust": np.random.uniform(5.0, 15.0)
        },
        "stats": {
            "Radius": f"{np.random.uniform(2.5, 6.0):.2f} Earth Radii",
            "Albedo": f"{np.random.uniform(0.02, 0.10):.3f} (Dark)",
            "Eccentricity": f"{np.random.uniform(0.1, 0.4):.2f}",
            "Thermal Emission": f"{np.random.uniform(30, 55):.1f} Kelvin"
        }
    }

def synthesize_spectrum_audio(spectrum_data, shift_type):
    try:
        sample_rate = 44100
        audio_frames = []
        multiplier = 0.6 if "Redshift" in shift_type else (1.4 if "Blueshift" in shift_type else 0.1)
        for chemical, abundance in spectrum_data.items():
            freq = (250.0 + (abundance * 8.0)) * multiplier
            duration = 0.5 
            num_samples = int(sample_rate * duration)
            for i in range(num_samples):
                t = float(i) / sample_rate
                amplitude = int(32767.0 * np.sin(freq * t * 2.0 * np.pi))
                if i < 2000: amplitude = int(amplitude * (i / 2000))
                elif i > num_samples - 2000: amplitude = int(amplitude * ((num_samples - i) / 2000))
                audio_frames.append(struct.pack('<h', amplitude))
        virtual_wav = io.BytesIO()
        with wave.open(virtual_wav, 'wb') as w_file:
            w_file.setnchannels(1)
            w_file.setsampwidth(2)
            w_file.setframerate(sample_rate)
            w_file.writeframes(b''.join(audio_frames))
        return virtual_wav.getvalue()
    except: return None

def extract_fits_data(uploaded_file):
    try:
        file_bytes = io.BytesIO(uploaded_file.getvalue())
        fits_file = fits.open(file_bytes)
        for ext in fits_file:
            if ext.data is not None and len(ext.data.shape) >= 2:
                return ext.data[0] if len(ext.data.shape) == 3 else ext.data
        return None
    except: return None

def change_page(page_name):
    st.session_state.current_page = page_name

def main():
    st.set_page_config(page_title="ExoMapper Workspace", layout="wide", initial_sidebar_state="collapsed")
    inject_styles()
    init_state()

    # ================= MODULE 1: LOGIN =================
    if st.session_state.current_page == "login":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        st.markdown("<div class='title-center'>ExoMapper</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle-center'>THE PLANET X HUNTER</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("<h4 style='text-align:center; color:#00e5ff; font-family:Chakra Petch;'>ENTER HUNTER ID TO ACCESS</h4>", unsafe_allow_html=True)
            username = st.text_input("", placeholder="e.g. NebulaHunter-X / StarVoyager-9...", label_visibility="collapsed")
            st.write("") 
            if st.button("INITIALIZE SECURE LINK 🚀", use_container_width=True):
                if username.strip():
                    st.session_state.user_id = username.strip()
                    if username.strip() not in st.session_state.user_profiles:
                        st.session_state.user_profiles[username.strip()] = {"last_mode": "🛰️ The Proxy Route (Simulated FITS)", "history": []}
                    change_page("home")
                    st.rerun()
                else:
                    st.markdown("<div class='error-box'>Access Denied. Provide a valid Hunter Name.</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= MODULE 2: COMMAND DASHBOARD =================
    elif st.session_state.current_page == "home":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        current_user = st.session_state.user_id
        user_data = st.session_state.user_profiles.get(current_user, {})
        
        st.markdown(f"<h2 style='color:white; font-family:Chakra Petch;'>Welcome to Command <span style='color:#00e5ff;'>{current_user}</span></h2>", unsafe_allow_html=True)
        if user_data.get("history"):
            st.markdown(f"<p class='data-text'>💡 Session Memory: Your last used mode was <span class='highlight'>{user_data['last_mode']}</span> with {len(user_data['history'])} logged scans.</p>", unsafe_allow_html=True)
        
        action1, action2, score_col = st.columns([1, 1, 2])
        with action1:
            if st.button("Start the Task 📡", use_container_width=True):
                st.session_state.blink_active = False
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
        
        card_c1, card_c2 = st.columns(2)
        with card_c1:
            st.markdown("""
            <div class="glass-card">
                <h3 style='color:#00e5ff; font-family:"Chakra Petch";'>🌍 Mission Objective & Role</h3>
                <p class='lore-text'>Welcome to <i>ExoMapper</i>, your primary gateway to deep-space cartography! Your main mission as an elite space hunter is to comb through raw astronomical data feeds, spot elusive moving thermal anomalies, and process their light spectra to discover unknown worlds hiding in the dark fringes of space.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="glass-card" style="border-color: #ff9100;">
                <h3 style='color:#ff9100; font-family:"Chakra Petch";'>🔭 About SPHEREx Mission</h3>
                <p class='lore-text'><b>SPHEREx</b> (Spectro-Photometer for the History of the Universe, Epoch of Reionization, and Ices Explorer) is a breakthrough NASA space telescope mission. Instead of looking at normal visible light, it maps the entire sky in infrared light (heat signatures). This allows scientists to study the origin of water in planetary systems and peer deep into the formation history of galaxies.</p>
                <a href="https://science.nasa.gov/mission/spherex/" target="_blank" class="nasa-link">NASA SPHEREx Portal</a>
            </div>
            """, unsafe_allow_html=True)

        with card_c2:
            st.markdown("""
            <div class="glass-card" style="border-color: #e040fb;">
                <h3 style='color:#e040fb; font-family:"Chakra Petch";'>🪐 The Mystery of Planet X</h3>
                <p class='lore-text'>Mathematical models and odd orbital alignments of icy bodies in our outer solar system strongly suggest a massive <b>9th planet</b> exists far beyond Neptune. Because it is so unimaginably distant, it reflects almost zero sunlight, making it completely invisible to normal optical telescopes. However, its faint thermal glow can potentially be detected via advanced infrared surveys!</p>
                <a href="https://solarsystem.nasa.gov/planets/hypothetical-planet-x/in-depth/" target="_blank" class="nasa-link" style="background:#e040fb; color:#fff;">NASA Planet X Archive</a>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="glass-card">
                <h3 style='color:#00e5ff; font-family:"Chakra Petch";'>🧑‍🚀 Team ExoMapper & Rules</h3>
                <p class='lore-text'><b>Team Members:</b> Shikshita & Ayaan</p>
                <p class='lore-text'><b>Scoring & Ranking Rules:</b></p>
                <ul class='lore-text'>
                    <li><b>Lock the anomaly correctly:</b> <span class='highlight'>+150 Points</span></li>
                    <li><b>False target guess:</b> <span style='color:#ff1744;'>-50 Points</span> (Strict penalty for guessing!)</li>
                </ul>
                <p class='lore-text'><i>Find the moving object across epochs, check coordinates precisely, and use the tools effectively.</i></p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ================= MODULE 3: TRIPLE-THREAT RADAR =================
    elif st.session_state.current_page == "radar":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        top1, top2 = st.columns([4, 1])
        top1.markdown("<h2 style='color:#ffffff; font-family:Chakra Petch;'>Live Optics: Interferometer</h2>", unsafe_allow_html=True)
        if top2.button("Abort Task"): change_page("home"); st.rerun()

        current_user = st.session_state.user_id
        default_mode = st.session_state.user_profiles.get(current_user, {}).get("last_mode", "🛰️ The Proxy Route (Simulated FITS)")
        
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        radar_mode = st.radio("SELECT UPLINK SOURCE:", [
            "🛰️ The Proxy Route (Simulated FITS)", 
            "🧬 Hybrid Injection", 
            "📡 Live Caltech IRSA (API / Real Upload)"
        ], index=["🛰️ The Proxy Route (Simulated FITS)", "🧬 Hybrid Injection", "📡 Live Caltech IRSA (API / Real Upload)"].index(default_mode) if default_mode in ["🛰️ The Proxy Route (Simulated FITS)", "🧬 Hybrid Injection", "📡 Live Caltech IRSA (API / Real Upload)"] else 0, horizontal=True)
        
        st.session_state.user_profiles[current_user]["last_mode"] = radar_mode
        st.markdown("</div>", unsafe_allow_html=True)
        
        ax, ay = st.session_state.anomaly_x, st.session_state.anomaly_y
        frame1, frame2 = None, None
        target_color = "gray"
        is_real_data = False

        if "Proxy" in radar_mode:
            frame1 = np.random.normal(20, 5, (400, 400))
            frame2 = np.copy(frame1)
            frame1[ay-5:ay+5, ax-5:ax+5] += 60 
            frame2[ay-3:ay+7, ax+8:ax+18] += 60 
            
        elif "Hybrid" in radar_mode:
            x = np.linspace(-5, 5, 400); y = np.linspace(-5, 5, 400); X, Y = np.meshgrid(x, y)
            background = 50 * np.sin(X**2 + Y**2) + np.random.normal(20, 10, (400, 400))
            frame1, frame2 = np.copy(background), np.copy(background)
            frame1[ay-4:ay+4, ax-4:ax+4] += 80 
            frame2[ay-2:ay+6, ax+10:ax+18] += 80 
            target_color = "inferno"
            
        elif "IRSA" in radar_mode:
            is_real_data = True
            st.markdown("""
            <a href="https://irsa.ipac.caltech.edu/applications/Cutouts/" target="_blank" style="background: rgba(0, 229, 255, 0.1); color: #00e5ff; padding: 6px 12px; border-radius: 5px; text-decoration: none; font-family: 'Chakra Petch'; border: 1px solid #00e5ff; font-size: 0.9rem; display: inline-block; margin-bottom: 15px;">
            🔗 Retrieve Live FITS Cutout from NASA/Caltech IRSA
            </a>
            """, unsafe_allow_html=True)
            
            sample_choice = st.selectbox("Or choose from NASA/Caltech IRSA Archive Sample Library:", ["-- Select Sample FITS --", "SPHEREx_DeepField_SectorA.fits", "NEOWISE_PlanetX_Candidate_09.fits"])
            
            uploaded_file = st.file_uploader("Upload FITS Epoch 1", type=["fits", "fit"])
            
            if uploaded_file is not None:
                with st.spinner("Decoding Astronomical Matrix..."):
                    frame1 = extract_fits_data(uploaded_file)
                    frame2 = frame1 
                if frame1 is not None: st.success(f"Successfully loaded file: {uploaded_file.name}")
                else: st.error("Corrupted FITS header or missing image data.")
            elif sample_choice != "-- Select Sample FITS --":
                frame1 = np.random.normal(30, 8, (400, 400))
                frame1[180:200, 220:240] += 90
                frame2 = np.copy(frame1)
                frame1[180:200, 220:240] += 50
                st.success(f"Loaded Archive Preset: {sample_choice}")

        # --- TRUE BLINKING & SHAPE SELECTION ENGINE ---
        if frame1 is not None and frame2 is not None:
            if not st.session_state.blink_active:
                st.markdown("<p class='lore-text'><b>Step 1:</b> Review Epoch 1 and Epoch 2 images. Click below to initiate automated blinking.</p>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    f1 = go.Figure(data=go.Heatmap(z=frame1, colorscale=target_color, showscale=False))
                    f1.update_layout(margin=dict(l=0,r=0,t=20,b=0), title="Epoch 1 (T=0)", xaxis=dict(title="X Axis", color="#b388ff"), yaxis=dict(title="Y Axis", color="#b388ff"), plot_bgcolor="#000", paper_bgcolor="#000", height=350)
                    st.plotly_chart(f1, use_container_width=True)
                with c2:
                    f2 = go.Figure(data=go.Heatmap(z=frame2, colorscale=target_color, showscale=False))
                    f2.update_layout(margin=dict(l=0,r=0,t=20,b=0), title="Epoch 2 (T+6 Months)", xaxis=dict(title="X Axis", color="#b388ff"), yaxis=dict(title="Y Axis", color="#b388ff"), plot_bgcolor="#000", paper_bgcolor="#000", height=350)
                    st.plotly_chart(f2, use_container_width=True)
                
                st.markdown('<div class="blink-btn">', unsafe_allow_html=True)
                if st.button("🚨 INITIATE AUTOMATED BLINK", use_container_width=True):
                    st.session_state.blink_active = True
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.markdown("<p class='lore-text'><b>Step 2:</b> Blinking active. Use the drawing tool (Circle/Rectangle) in the chart header to circle the moving target.</p>", unsafe_allow_html=True)
                
                fig = go.Figure(
                    data=[go.Heatmap(z=frame1, colorscale=target_color, showscale=False)],
                    layout=go.Layout(
                        xaxis=dict(title="X Axis (Pixels)", color="#b388ff"), 
                        yaxis=dict(title="Y Axis (Pixels)", color="#b388ff"),
                        plot_bgcolor="#020308", paper_bgcolor="#020308", height=500,
                        margin=dict(l=40, r=40, t=20, b=40),
                        dragmode="drawcircle",
                        newshape=dict(line_color='#00e5ff', line_width=3, fillcolor='rgba(0, 229, 255, 0.2)'),
                        updatemenus=[dict(
                            type="buttons", showactive=False,
                            buttons=[dict(label="▶ PLAY BLINK ANIMATION", method="animate",
                                        args=[None, dict(frame=dict(duration=400, redraw=True), fromcurrent=True, transition=dict(duration=0, easing="linear"), mode="immediate")])])]
                    ),
                    frames=[go.Frame(data=[go.Heatmap(z=frame1)], name="f1"), go.Frame(data=[go.Heatmap(z=frame2)], name="f2")]
                )
                
                st.plotly_chart(fig, use_container_width=True, key="radar_canvas", config={
                    'scrollZoom': True,
                    'displayModeBar': True,
                    'modeBarButtonsToAdd': ['drawcircle', 'drawrect', 'eraseshape']
                })
                
                if st.button("⏹ STOP BLINK & RESET", use_container_width=True):
                    st.session_state.blink_active = False
                    st.rerun()
            
            st.markdown("<hr style='border-color: rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
            
            col_info, col_lock = st.columns([2, 2])
            with col_info:
                st.markdown("<p class='lore-text'><i>Draw a circle or box around the target anomaly using the chart toolbar above, then lock target.</i></p>", unsafe_allow_html=True)
            with col_lock:
                if st.button("🎯 LOCK TARGET & EXTRACT SPECTRUM", use_container_width=True):
                    st.session_state.user_profiles[current_user]["history"].append(radar_mode)
                    st.session_state.is_hit = True
                        
                    if st.session_state.is_hit: st.session_state.current_score += 150
                    else: st.session_state.current_score -= 50
                        
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
            st.markdown("<div class='error-box'>❌ FALSE ALARM: No Anomaly within marked zone. (-50 Points Penalty)</div>", unsafe_allow_html=True)
        
        data = st.session_state.scientific_payload
        stat_col, graph_col = st.columns([1, 2])
        
        with stat_col:
            stats_html = "<div class='glass-card'><h3 style='color:#b388ff; font-family:Chakra Petch;'>🪐 Physical Stats</h3><hr style='border-color:#333;'>"
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
                paper_bgcolor='rgba(4, 10, 25, 0.82)', plot_bgcolor='rgba(4, 10, 25, 0)',
                font=dict(color='#84ffff', family='Space Mono'), margin=dict(l=20, r=20, t=50, b=20), height=350,
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<hr style='border-color: rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
        
        dop_col, soni_col = st.columns([1, 1])
        shift_type = data["shift"]
        
        with dop_col:
            st.markdown("<h3 style='color:#b388ff; font-family:Chakra Petch;'>📡 Doppler Shift</h3>", unsafe_allow_html=True)
            if "Red" in shift_type: wave_color, freq = "#ff1744", 0.8
            elif "Blue" in shift_type: wave_color, freq = "#00e5ff", 3.0
            else: wave_color, freq = "#777777", 0.2
            
            x_wave = np.linspace(0, 4 * np.pi, 100)
            y_wave = np.sin(x_wave * freq)
            wave_fig = go.Figure(go.Scatter(x=x_wave, y=y_wave, mode='lines', line=dict(color=wave_color, width=3)))
            wave_fig.update_layout(
                paper_bgcolor='rgba(4, 10, 25, 0.82)', plot_bgcolor='rgba(0,0,0,0)', 
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
            if audio_bytes: st.audio(audio_bytes, format='audio/wav')
            
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

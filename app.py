import streamlit as st
import numpy as np
import pandas as pd
import io
import wave
import struct
import plotly.graph_objects as go

def inject_animations_and_styles():
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Orbitron:wght@700;900&family=Space+Grotesk:wght@400;600&display=swap');
    
    /* Advanced Cosmic Nebula Background */
    .stApp {
        background-color: #03050a;
        background-image: 
            radial-gradient(circle at 20% 40%, rgba(30, 10, 60, 0.6), transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(10, 40, 60, 0.5), transparent 50%),
            url("https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=3000&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        color: #d1e8ff;
        font-family: 'Space Grotesk', sans-serif;
    }

    /* Page Fade In */
    .page-fade-in { animation: fadeIn 1s ease-out forwards; }
    @keyframes fadeIn { 0% { opacity: 0; transform: translateY(10px); } 100% { opacity: 1; transform: translateY(0); } }
    
    /* ExoMapper Master Typography */
    .title-center {
        text-align: center; font-family: 'Audiowide', cursive; font-size: 7.5rem; 
        font-weight: 900; color: #ffffff; margin-top: 5vh;
        text-shadow: 0 0 20px #00ffcc, 0 0 40px rgba(0, 255, 204, 0.5);
        letter-spacing: 6px; animation: pulseGlow 2.5s infinite alternate;
    }
    @keyframes pulseGlow {
        from { text-shadow: 0 0 20px #00ffcc, 0 0 40px rgba(0, 255, 204, 0.4); transform: scale(1); }
        to { text-shadow: 0 0 35px #00ffcc, 0 0 70px #00ffcc; transform: scale(1.02); }
    }

    .subtitle-center {
        text-align: center; color: #b388ff; font-size: 2.2rem; 
        font-family: 'Times New Roman', Times, serif; font-style: italic; 
        font-weight: bold; letter-spacing: 5px; margin-top: -20px; margin-bottom: 40px;
        text-shadow: 0 0 15px rgba(179, 136, 255, 0.6);
    }
    
    /* Interior Headers */
    .header-top { display: flex; align-items: center; border-bottom: 1px solid rgba(0,255,204,0.3); padding-bottom: 15px; margin-bottom: 25px; }
    .header-top h1 { 
        font-family: 'Audiowide', cursive; font-size: 2.8rem; color: #ffffff; 
        text-shadow: 0 0 15px #00ffcc; margin: 0; margin-left: 20px; letter-spacing: 3px;
    }
    .header-top p { 
        font-family: 'Times New Roman', Times, serif; color: #b388ff; font-size: 1.2rem; 
        font-style: italic; font-weight: bold; letter-spacing: 2px; margin: 0; margin-left: 20px; margin-top: 5px;
    }

    /* Fixed Glass Cards */
    .glass-card {
        background: rgba(10, 15, 30, 0.7); border: 1px solid rgba(0, 255, 204, 0.3); 
        padding: 25px; border-radius: 15px; backdrop-filter: blur(15px); 
        -webkit-backdrop-filter: blur(15px); margin-bottom: 20px; height: 100%;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6); transition: all 0.3s ease;
    }
    .glass-card:hover { border-color: #00ffcc; box-shadow: 0 10px 40px rgba(0,255,204,0.25); transform: translateY(-4px); }
    
    .lore-text { font-size: 1.1rem; line-height: 1.7; color: #e0e0e0; font-family: 'Space Grotesk', sans-serif;}
    .highlight { color: #00ffcc; font-weight: 700; text-shadow: 0 0 5px rgba(0,255,204,0.3); }
    
    /* Global Buttons */
    div.stButton > button {
        background: rgba(0, 255, 204, 0.15); color: #00ffcc; border: 2px solid #00ffcc;
        border-radius: 8px; font-weight: 700; padding: 12px 24px; transition: all 0.3s ease;
        text-transform: uppercase; letter-spacing: 2px; width: 100%; font-family: 'Orbitron', sans-serif;
    }
    div.stButton > button:hover { background: #00ffcc; color: #050914; box-shadow: 0 0 25px #00ffcc; transform: scale(1.03); }
    
    /* Footer */
    .developer-tag {
        position: fixed; bottom: 10px; right: 20px; font-family: 'Orbitron', sans-serif;
        font-size: 0.9rem; color: #00ffcc; text-align: right; text-shadow: 0 0 8px rgba(0,255,204,0.6);
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    """
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def render_top_header():
    st.markdown("""
    <div class="header-top">
        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg" width="65" style="filter: drop-shadow(0 0 8px rgba(255,255,255,0.4));">
        <div>
            <h1>ExoMapper</h1>
            <p>THE PLANET X HUNTER</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def init_state():
    if 'current_page' not in st.session_state: st.session_state.current_page = "login"
    if 'user_id' not in st.session_state: st.session_state.user_id = ""
    if 'current_score' not in st.session_state: st.session_state.current_score = 0
    if 'scientific_payload' not in st.session_state: st.session_state.scientific_payload = None
    if 'doppler_shift' not in st.session_state: st.session_state.doppler_shift = np.random.choice(["Redshift (Moving Away)", "Blueshift (Moving Towards)"])

def generate_scientific_payload():
    st.session_state.doppler_shift = np.random.choice(["Redshift (Moving Away)", "Blueshift (Moving Towards)"])
    return {
        "spectrum": {
            "Methane (CH4)": np.random.uniform(2.0, 15.0),
            "Water Ice (H2O)": np.random.uniform(40.0, 70.0),
            "Ammonia (NH3)": np.random.uniform(10.0, 25.0),
            "Silicate Dust": np.random.uniform(5.0, 20.0)
        },
        "stats": {
            "Estimated Radius": f"{np.random.uniform(2.5, 6.0):.2f} Earth Radii",
            "Albedo (Reflectivity)": f"{np.random.uniform(0.02, 0.15):.3f} (Extremely Dark)",
            "Orbital Eccentricity": f"{np.random.uniform(0.1, 0.4):.2f}",
            "Thermal Emission": f"{np.random.uniform(30, 60):.1f} Kelvin"
        }
    }

def synthesize_spectrum_audio(spectrum_data):
    try:
        sample_rate = 44100
        audio_frames = []
        for chemical, abundance in spectrum_data.items():
            freq = 250.0 + (abundance * 12.0) 
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
            st.markdown("<h4 style='text-align:center; color:#00ffcc; font-family:Orbitron; letter-spacing: 3px;'>ENTER HUNTER ID TO ACCESS TERMINAL</h4>", unsafe_allow_html=True)
            username = st.text_input("", placeholder="Assign your Space Hunter Name...", label_visibility="collapsed")
            
            st.write("") 
            btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
            with btn_col2:
                if st.button("INITIALIZE SECURE LINK 🚀"):
                    if username.strip():
                        st.session_state.user_id = username.strip()
                        change_page("home")
                        st.rerun()
                    else:
                        st.warning("Terminal access denied. Provide a valid Hunter Name.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= MODULE 2: COMMAND DASHBOARD =================
    elif st.session_state.current_page == "home":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        st.markdown(f"<h2 style='color:white; font-family:Orbitron;'>Welcome to Command <span style='color:#00ffcc;'>{st.session_state.user_id}</span>, The Dashboard</h2>", unsafe_allow_html=True)
        
        action1, action2, score_col = st.columns([1, 1, 2])
        with action1:
            if st.button("Start the Task 📡"):
                change_page("radar")
                st.rerun()
        with action2:
            if st.button("Disconnect (Logout)"):
                st.session_state.user_id = ""
                change_page("login")
                st.rerun()
        with score_col:
            st.markdown(f"""
            <div style="background: rgba(0, 255, 204, 0.15); border: 2px solid #00ffcc; padding: 12px 24px; border-radius: 10px; text-align: right; box-shadow: 0 0 15px rgba(0,255,204,0.3);">
                <h3 style="margin:0; color:#b388ff; font-family:Orbitron;">🏆 Hunter Record: <span style="color:#ffffff;">{st.session_state.current_score} Points</span></h3>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<hr style='border-color: rgba(255,255,255,0.2); margin-top:30px; margin-bottom:30px;'>", unsafe_allow_html=True)
        
        col_mission, col_team, col_rules = st.columns(3)
        
        with col_mission:
            st.markdown("""
            <div class="glass-card">
                <h3 style='color:#00ffcc; font-family:"Orbitron";'>🌍 The Mission Objective</h3>
                <p class='lore-text'><b>The Future of SPHEREx:</b> NASA is launching the SPHEREx Space Telescope to map the universe in infrared. It measures heat, not visible light.</p>
                <p class='lore-text'><b>Hunting Planet X:</b> Scientists believe a massive 9th planet is hiding in the dark, icy edges of our solar system. It is completely invisible to normal telescopes.</p>
                <p class='lore-text'><b>Your Role in the Game:</b> Before the real data arrives, you train on simulated thermal maps. Spot anomalies, lock onto them, and analyze their atmospheric spectrum.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_team:
            st.markdown("""
            <div class="glass-card">
                <h3 style='color:#00ffcc; font-family:"Orbitron";'>🧑‍🚀 About Team ExoMapper</h3>
                <p class='lore-text'>We are a dedicated two-person crew:</p>
                <ul class='lore-text'>
                    <li><span class='highlight'>Shikshita:</span> M.Sc. Astrophysics researcher mapping the stars.</li>
                    <li><span class='highlight'>Ayaan:</span> Technical specialist handling documentation and mission control.</li>
                </ul>
                <p class='lore-text'>We built ExoMapper to make complex deep-space astronomical data interactive, accessible, and fun for citizen scientists worldwide.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_rules:
            st.markdown("""
            <div class="glass-card">
                <h3 style='color:#00ffcc; font-family:"Orbitron";'>📜 Rules & Ranking</h3>
                <p class='lore-text'>Every hunter starts at the bottom. Prove your skills to rank up:</p>
                <ul class='lore-text'>
                    <li><b>Lock an Anomaly:</b> <span class='highlight'>+150 Points</span></li>
                    <li><b>Analyze Spectrum:</b> <span class='highlight'>+50 Points</span></li>
                </ul>
                <p class='lore-text'>Use the drawing tools in the radar scanner to circle or box the glowing thermal signatures. Lock the target to extract data.</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:white; font-family:Orbitron;'>🔗 Official Data Archives</h3>", unsafe_allow_html=True)
        st.markdown("""
        <a href="https://science.nasa.gov/mission/spherex/" target="_blank" style="color: #050914; background: #00ffcc; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; font-family: 'Space Grotesk'; margin-right: 15px;">Learn about SPHEREx</a>
        <a href="https://solarsystem.nasa.gov/planets/hypothetical-planet-x/in-depth/" target="_blank" style="color: #050914; background: #b388ff; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; font-family: 'Space Grotesk';">The Search for Planet X</a>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= MODULE 3: RADAR SCANNER =================
    elif st.session_state.current_page == "radar":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        top1, top2 = st.columns([4, 1])
        top1.markdown("<h2 style='color:#00ffcc; font-family:Orbitron;'>Live Optics: Sector Alpha</h2>", unsafe_allow_html=True)
        if top2.button("Abort Task"):
            change_page("home")
            st.rerun()

        base_flux = np.random.rand(400, 400)
        shift_flux = np.copy(base_flux)
        shift_flux[180:200, 260:280] = 3.5 
        
        st.markdown("<p style='color:#b388ff; font-family:Space Grotesk; font-size:1.1rem;'>Use the sidebar to select a drawing tool. Draw a shape over the bright anomaly to lock onto it. You can scroll to zoom in/out.</p>", unsafe_allow_html=True)
        
        st.sidebar.markdown("<h2 style='color:#00ffcc; font-family:Orbitron;'>🛠 Targeting System</h2>", unsafe_allow_html=True)
        st.sidebar.write("1. Scroll image to zoom in/out.")
        st.sidebar.write("2. Select a glowing capture shape below.")
        st.sidebar.write("3. Draw it over the heat signature.")
        
        tool = st.sidebar.radio("Select Capture Tool:", ["Circle Lock", "Square Box", "Freehand Polygon"])
        drag_dict = {"Circle Lock": "drawcircle", "Square Box": "drawrect", "Freehand Polygon": "drawclosedpath"}
        
        fig = go.Figure(data=go.Heatmap(z=shift_flux, colorscale="inferno", showscale=False))
        fig.update_layout(
            dragmode=drag_dict[tool],
            newshape=dict(line_color='#00ffcc', line_width=4, fillcolor='rgba(0, 255, 204, 0.2)'),
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            plot_bgcolor="#03050a", paper_bgcolor="#03050a",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True, config={
            'scrollZoom': True, 
            'displayModeBar': True,
            'modeBarButtonsToAdd': ['drawcircle', 'drawrect', 'drawclosedpath', 'eraseshape']
        })
        
        st.write("")
        col_lock1, col_lock2, col_lock3 = st.columns([1, 2, 1])
        with col_lock2:
            if st.button("🎯 LOCK TARGET & EXTRACT SPECTRUM", use_container_width=True):
                st.session_state.current_score += 150
                st.session_state.scientific_payload = generate_scientific_payload()
                change_page("analysis")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= MODULE 4: SCIENTIFIC ANALYSIS =================
    elif st.session_state.current_page == "analysis":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        st.markdown("<h2 style='color:#00ffcc; text-align:center; font-family:Orbitron;'>Target Locked. Extraction Complete.</h2>", unsafe_allow_html=True)
        st.success(f"Outstanding work, {st.session_state.user_id}. +150 Points awarded!")
        
        data = st.session_state.scientific_payload
        stat_col, graph_col = st.columns([1, 2])
        
        with stat_col:
            # Stats fixed inside the Glass Card using HTML formatting natively
            stats_html = "<div class='glass-card'><h3 style='color:#b388ff; font-family:Orbitron;'>🪐 Physical Configuration</h3>"
            for key, val in data["stats"].items():
                stats_html += f"<p class='lore-text'><b>{key}:</b> <span style='color:#00ffcc;'>{val}</span></p>"
            stats_html += "</div>"
            st.markdown(stats_html, unsafe_allow_html=True)
            
        with graph_col:
            # Atmospheric Spectrum with defined X/Y axis using Plotly (styled as a glass card)
            df = pd.DataFrame(list(data["spectrum"].items()), columns=["Molecule", "Percentage"])
            fig_bar = go.Figure(data=[go.Bar(
                x=df["Molecule"], y=df["Percentage"],
                marker_color='#00ffcc', marker_line_color='#ffffff', marker_line_width=1.5, opacity=0.9
            )])
            fig_bar.update_layout(
                title=dict(text="Atmospheric Spectrum", font=dict(color="#b388ff", size=22, family="Orbitron")),
                xaxis_title=dict(text="Chemical Composition", font=dict(color="#ffffff", size=14)),
                yaxis_title=dict(text="Abundance (%)", font=dict(color="#ffffff", size=14)),
                paper_bgcolor='rgba(10, 15, 30, 0.7)', plot_bgcolor='rgba(10, 15, 30, 0.7)',
                font=dict(color='#e0e0e0', family='Space Grotesk'),
                margin=dict(l=20, r=20, t=50, b=20),
                height=350,
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)')
            )
            # Add a CSS border to match glass card
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.2); margin-top:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
        
        # DOPPLER SHIFT & SONIFICATION MODULE
        dop_col, soni_col = st.columns([1, 1])
        
        with dop_col:
            st.markdown("<h3 style='color:#b388ff; font-family:Orbitron;'>📡 Doppler Shift Analysis</h3>", unsafe_allow_html=True)
            shift_type = st.session_state.doppler_shift
            wave_color = "#ff4444" if "Red" in shift_type else "#00ccff"
            
            # Dynamic Wave Animation via Plotly
            x_wave = np.linspace(0, 4 * np.pi, 100)
            freq_multiplier = 0.8 if "Red" in shift_type else 2.5
            y_wave = np.sin(x_wave * freq_multiplier)
            
            wave_fig = go.Figure(go.Scatter(x=x_wave, y=y_wave, mode='lines', line=dict(color=wave_color, width=4, shape='spline')))
            wave_fig.update_layout(
                paper_bgcolor='rgba(10, 15, 30, 0.7)', plot_bgcolor='rgba(10, 15, 30, 0.7)', 
                height=180, margin=dict(l=10,r=10,t=40,b=10),
                title=dict(text=f"Detected: {shift_type}", font=dict(color=wave_color, family="Orbitron", size=16)),
                xaxis=dict(visible=False), yaxis=dict(visible=False)
            )
            st.plotly_chart(wave_fig, use_container_width=True)
            
        with soni_col:
            st.markdown("<h3 style='color:#b388ff; font-family:Orbitron;'>🎧 Acoustic Telemetry</h3>", unsafe_allow_html=True)
            st.markdown("""
            <div style='background: rgba(255, 68, 68, 0.1); border-left: 4px solid #ff4444; padding: 10px; margin-bottom: 15px;'>
                <span style='color:#ff4444; font-weight:bold; font-size: 0.9rem;'>DISCLAIMER:</span> 
                <span style='font-size: 0.85rem; color:#e0e0e0;'>This audio is synthesized from high-frequency spectrum data, mapped to human-audible sine waves based on the Doppler shift. It is not actual recorded sound.</span>
            </div>
            """, unsafe_allow_html=True)
            
            audio_bytes = synthesize_spectrum_audio(data["spectrum"])
            if audio_bytes:
                st.audio(audio_bytes, format='audio/wav')
            else:
                st.error("Acoustic synthesis module offline.")
            
        st.markdown("<hr style='border-color: rgba(255,255,255,0.2); margin-top:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
        
        st.markdown("<h3 style='color:#ffffff; font-family:Orbitron;'>Does this match the Planet X theoretical profile? <span style='color:#00ffcc;'>YES (87.4% Match Probability)</span></h3>", unsafe_allow_html=True)
        
        designation = st.text_input("Assign a Catalog Name to your discovery:", placeholder="e.g. Kepler-452b")
        
        col_submit, col_home = st.columns(2)
        with col_submit:
            if st.button("Transmit Data to NASA"):
                if designation:
                    st.success(f"Transmission Successful! Object '{designation}' officially logged by Hunter {st.session_state.user_id}.")
                else:
                    st.warning("Please assign a name before transmitting to NASA servers.")
        with col_home:
            if st.button("Return to Command Dashboard"):
                change_page("home")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Universal Footer
    st.markdown("<div class='developer-tag'>Developed by: Team ExoMapper</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

import streamlit as st
import numpy as np
import pandas as pd
import time
import io
import wave
import struct

def inject_animations_and_styles():
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;600&display=swap');
    
    /* Deep Space Animated Background */
    .stApp {
        background-color: #050914;
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(20, 10, 40, 0.4), transparent 50%),
            radial-gradient(circle at 85% 30%, rgba(10, 30, 40, 0.5), transparent 50%),
            url("https://images.unsplash.com/photo-1506318137071-a8e063b4bec0?q=80&w=3000&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        color: #d1e8ff;
        font-family: 'Inter', sans-serif;
    }

    /* Page Transitions */
    .page-fade-in { animation: fadeIn 0.8s ease-out forwards; }
    @keyframes fadeIn { 0% { opacity: 0; transform: scale(0.98); } 100% { opacity: 1; transform: scale(1); } }
    
    /* ExoMapper Typography */
    .title-center {
        text-align: center; font-family: 'Orbitron', sans-serif; font-size: 5.5rem; 
        font-weight: 900; color: #ffffff; margin-top: 10vh;
        text-shadow: 0 0 20px #00ffcc, 0 0 40px rgba(0, 255, 204, 0.4);
        letter-spacing: 4px;
    }
    .subtitle-center {
        text-align: center; color: #b388ff; font-size: 1.5rem; 
        font-style: italic; letter-spacing: 4px; margin-top: -15px;
        text-shadow: 0 0 10px rgba(179, 136, 255, 0.5);
    }
    
    .header-top { display: flex; align-items: center; border-bottom: 1px solid rgba(0,255,204,0.2); padding-bottom: 15px; margin-bottom: 30px; }
    .header-top h1 { 
        font-family: 'Orbitron', sans-serif; font-size: 2.5rem; color: #ffffff; 
        text-shadow: 0 0 10px #00ffcc; margin: 0; padding: 0; margin-left: 15px;
    }
    .header-top p { 
        color: #b388ff; font-size: 1rem; font-style: italic; 
        letter-spacing: 2px; margin: 0; margin-left: 15px; margin-top: 5px;
    }

    /* Glass Cards */
    .glass-card {
        background: rgba(10, 15, 30, 0.65); border: 1px solid rgba(0, 255, 204, 0.2); 
        padding: 25px; border-radius: 12px; backdrop-filter: blur(12px); 
        -webkit-backdrop-filter: blur(12px); margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5); transition: all 0.3s ease;
    }
    .glass-card:hover { border-color: #00ffcc; box-shadow: 0 10px 30px rgba(0,255,204,0.15); transform: translateY(-3px); }
    
    .lore-text { font-size: 1.05rem; line-height: 1.6; color: #e0e0e0; }
    .highlight { color: #00ffcc; font-weight: 600; }
    
    /* Buttons */
    div.stButton > button {
        background: rgba(0, 255, 204, 0.1); color: #00ffcc; border: 1px solid #00ffcc;
        border-radius: 6px; font-weight: 600; padding: 10px 20px; transition: all 0.3s ease;
    }
    div.stButton > button:hover { background: #00ffcc; color: #050914; box-shadow: 0 0 15px #00ffcc; transform: scale(1.02); }
    
    /* Footer */
    .developer-tag {
        position: fixed; bottom: 10px; right: 20px; font-family: 'Inter', sans-serif;
        font-size: 0.85rem; color: rgba(255,255,255,0.5); text-align: right; line-height: 1.4;
    }
    """
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def render_top_header():
    st.markdown("""
    <div class="header-top">
        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg" width="60" style="filter: drop-shadow(0 0 5px rgba(255,255,255,0.3));">
        <div>
            <h1>ExoMapper</h1>
            <p>THE PLANET X HUNTER</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def init_state():
    if 'current_page' not in st.session_state: st.session_state.current_page = "login"
    if 'user_id' not in st.session_state: st.session_state.user_id = ""
    if 'last_score' not in st.session_state: st.session_state.last_score = 0
    if 'current_score' not in st.session_state: st.session_state.current_score = 0
    if 'scientific_payload' not in st.session_state: st.session_state.scientific_payload = None

def generate_scientific_payload():
    return {
        "spectrum": {
            "Methane (CH4)": np.random.uniform(2.0, 5.0),
            "Water Ice (H2O)": np.random.uniform(40.0, 60.0),
            "Ammonia (NH3)": np.random.uniform(10.0, 20.0),
            "Silicate Dust": np.random.uniform(5.0, 15.0)
        },
        "stats": {
            "Estimated Radius": f"{np.random.uniform(2.5, 6.0):.2f} Earth Radii",
            "Albedo (Reflectivity)": f"{np.random.uniform(0.02, 0.15):.3f} (Very Dark)",
            "Orbital Eccentricity": f"{np.random.uniform(0.1, 0.4):.2f}",
            "Thermal Emission": f"{np.random.uniform(30, 60):.1f} Kelvin"
        }
    }

def synthesize_spectrum_audio(spectrum_data):
    """Generates acoustic telemetry (pure sine waves) based on chemical abundance."""
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
    st.set_page_config(page_title="ExoMapper Workspace", layout="wide", initial_sidebar_state="collapsed")
    inject_animations_and_styles()
    init_state()

    # ================= PAGE 1: LOGIN =================
    if st.session_state.current_page == "login":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        st.markdown("<div class='title-center'>ExoMapper</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle-center'>THE PLANET X HUNTER</div>", unsafe_allow_html=True)
        
        st.write("\n\n")
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown('<div class="glass-card" style="text-align:center;">', unsafe_allow_html=True)
            username = st.text_input("ENTER HUNTER ID TO ACCESS TERMINAL:", placeholder="e.g. Commander Shikshita")
            if st.button("INITIALIZE SECURE LINK 🚀"):
                if username.strip():
                    st.session_state.user_id = username.strip()
                    change_page("home")
                    st.rerun()
                else:
                    st.warning("Please enter a valid Hunter ID.")
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= PAGE 2: HOME & LORE =================
    elif st.session_state.current_page == "home":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        nav1, nav2, nav3 = st.columns([3, 1, 1])
        nav1.markdown(f"<h3 style='color:white;'>Welcome to Command, <span style='color:#00ffcc;'>{st.session_state.user_id}</span></h3>", unsafe_allow_html=True)
        if nav2.button("Start Radar Scan 📡"):
            change_page("radar")
            st.rerun()
        if nav3.button("Disconnect (Logout)"):
            st.session_state.user_id = ""
            change_page("login")
            st.rerun()
            
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        
        col_lore, col_stats = st.columns([2, 1])
        with col_lore:
            st.markdown("""
            <div class="glass-card">
                <h3 style='color:#00ffcc; font-family:"Orbitron";'>📖 The Mission Directives</h3>
                <p class='lore-text'><b>The Mystery of Planet X:</b> Mathematical models suggest a massive 9th planet is hiding in the dark, icy outer edges of our solar system just beyond Neptune. Because it is so far away, it reflects almost zero visible sunlight.</p>
                <p class='lore-text'><b>The SPHEREx Solution:</b> NASA is deploying the <span class='highlight'>SPHEREx Space Telescope</span>. Instead of looking for visible light, it scans the universe in infrared (heat). If Planet X is out there, its faint thermal glow will be caught.</p>
                <p class='lore-text'><b>The Future & Your Role:</b> Before official SPHEREx data drops, we train hunters using simulated thermal proxy data. Analyze heat maps, detect anomalies, and extract their atmospheric spectrum using acoustic telemetry.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_stats:
            st.markdown(f"""
            <div class="glass-card">
                <h3 style='color:#b388ff; font-family:"Orbitron";'>📊 Hunter Record</h3>
                <p class='lore-text'><b>Previous Mission Score:</b> {st.session_state.last_score}</p>
                <p class='lore-text'><b>Current Session Score:</b> <span class='highlight'>{st.session_state.current_score}</span></p>
                <p class='lore-text'><i>Every confirmed anomaly boosts your rank. Initiate the scan.</i></p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= PAGE 3: RADAR SCANNER =================
    elif st.session_state.current_page == "radar":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        top1, top2 = st.columns([4, 1])
        top1.markdown("<h2 style='color:#00ffcc; font-family:Orbitron;'>Live Optics: Sector Alpha</h2>", unsafe_allow_html=True)
        if top2.button("Abort & Return"):
            change_page("home")
            st.rerun()
            
        st.markdown("<p style='color:#b388ff;'>Data Source: Simulated thermal proxy data (Calibrated for SPHEREx integration)</p>", unsafe_allow_html=True)
        
        base_flux = np.random.rand(400, 400)
        shift_flux = np.copy(base_flux)
        shift_flux[150, 250] = 3.8 
        
        scan_rate = st.slider("Interferometer Blink Rate (Slide to detect movement)", 0, 100, 0)
        view = (1 - (scan_rate/100)) * base_flux + ((scan_rate/100)) * shift_flux
        
        st.image(view, use_container_width=True, clamp=True)
        
        if st.button("🎯 ANOMALY DETECTED: LOCK TARGET & EXTRACT SPECTRUM"):
            st.session_state.current_score += 150
            st.session_state.scientific_payload = generate_scientific_payload()
            change_page("analysis")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= PAGE 4: SCIENTIFIC ANALYSIS =================
    elif st.session_state.current_page == "analysis":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        render_top_header()
        
        st.markdown("<h2 style='color:#00ffcc; text-align:center;'>Target Locked. Spectroscopic Extraction Complete.</h2>", unsafe_allow_html=True)
        st.success(f"Outstanding work, {st.session_state.user_id}. Your hunter score increased to {st.session_state.current_score}!")
        
        data = st.session_state.scientific_payload
        stat_col, graph_col = st.columns([1, 2])
        with stat_col:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<h3 style='color:#b388ff;'>🪐 Physical Configuration</h3>", unsafe_allow_html=True)
            for key, val in data["stats"].items():
                st.markdown(f"<p class='lore-text'><b>{key}:</b> {val}</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with graph_col:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<h3 style='color:#b388ff;'>📉 Atmospheric Spectrum (%)</h3>", unsafe_allow_html=True)
            df = pd.DataFrame(list(data["spectrum"].values()), index=list(data["spectrum"].keys()), columns=["Composition"])
            st.bar_chart(df, color="#00ffcc")
            st.markdown('</div>', unsafe_allow_html=True)
            
        # SONIFICATION UI
        st.markdown("<h3 style='color:#b388ff; font-family:Orbitron;'>🎧 Acoustic Telemetry (Sonification)</h3>", unsafe_allow_html=True)
        st.write("Listen to the atmospheric absorption spectrum. Higher pitches indicate higher molecular density.")
        audio_bytes = synthesize_spectrum_audio(data["spectrum"])
        if audio_bytes:
            st.audio(audio_bytes, format='audio/wav')
        else:
            st.error("Acoustic synthesis module currently offline.")
            
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        st.write("Does this match the Planet X theoretical profile? **YES (87.4% Match Probability)**")
        
        designation = st.text_input("Assign a Catalog Designation to this discovery:")
        col_submit, col_home = st.columns(2)
        with col_submit:
            if st.button("Transmit Data to NASA"):
                if designation:
                    st.success(f"Transmission Successful! Object '{designation}' discovered by {st.session_state.user_id} has been logged in the archives.")
                else:
                    st.warning("Enter a valid designation name before transmitting.")
        with col_home:
            if st.button("Return to Command Dashboard"):
                change_page("home")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("<div class='developer-tag'>Developed by: Shikshita<br>Project Guide: Dr. Hum Chand</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

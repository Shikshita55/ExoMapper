import streamlit as st
import numpy as np
import pandas as pd
import time

def inject_animations_and_styles():
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');
    
    .stApp { background-color: #03070f; color: #d1e8ff; font-family: 'Inter', sans-serif; overflow-x: hidden; }
    
    /* Page Transition Animations */
    .page-fade-in { animation: fadeIn 0.6s ease-out forwards; }
    @keyframes fadeIn { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
    
    /* Button Click Animations (Pulse & Lift) */
    div.stButton > button {
        background: rgba(0, 255, 204, 0.05); color: #00ffcc; border: 2px solid #00ffcc;
        border-radius: 8px; font-weight: 600; transition: all 0.3s ease; width: 100%;
        box-shadow: 0 0 10px rgba(0,255,204,0.1);
    }
    div.stButton > button:hover {
        background: #00ffcc; color: #03070f; transform: scale(1.03) translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,255,204,0.4);
    }
    div.stButton > button:active { transform: scale(0.95); } /* Click effect */

    /* Glass Cards */
    .glass-card {
        background: rgba(10, 25, 47, 0.6); border: 1px solid #1e2d4a; padding: 25px;
        border-radius: 15px; backdrop-filter: blur(10px); transition: all 0.3s ease; margin-bottom: 20px;
    }
    .glass-card:hover { border-color: #00ffcc; box-shadow: 0 10px 30px rgba(0,255,204,0.15); }
    
    h1, h2, h3 { font-family: 'Orbitron', sans-serif; color: #ffffff; }
    .neon-text { color: #00ffcc; text-shadow: 0 0 10px rgba(0,255,204,0.5); }
    """
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def init_state():
    # Managing smooth page jumps and user data
    if 'current_page' not in st.session_state: st.session_state.current_page = "login"
    if 'user_id' not in st.session_state: st.session_state.user_id = ""
    if 'last_score' not in st.session_state: st.session_state.last_score = 450
    if 'current_score' not in st.session_state: st.session_state.current_score = 0
    if 'scientific_payload' not in st.session_state: st.session_state.scientific_payload = None

def generate_scientific_payload():
    # Scientific proxy data ready for real NASA inputs
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

def change_page(page_name):
    st.session_state.current_page = page_name

def main():
    st.set_page_config(page_title="ExoMapper", layout="wide", initial_sidebar_state="collapsed")
    inject_animations_and_styles()
    init_state()

    # ================= PAGE 1: LOGIN =================
    if st.session_state.current_page == "login":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; font-size:4rem; margin-top:10vh;'><span class='neon-text'>ExoMapper</span></h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#8a2be2; letter-spacing:3px;'>THE PLANET X HUNTER</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            username = st.text_input("Enter Hunter ID to Access Terminal:")
            if st.button("Initialize Link"):
                if username.strip():
                    st.session_state.user_id = username.strip()
                    change_page("home")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= PAGE 2: HOME & HISTORY =================
    elif st.session_state.current_page == "home":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        
        # Navigation Bar
        nav1, nav2, nav3 = st.columns([3, 1, 1])
        nav1.markdown(f"### Welcome to Command, <span class='neon-text'>{st.session_state.user_id}</span>", unsafe_allow_html=True)
        if nav2.button("Start Radar Scan 🚀"):
            change_page("radar")
            st.rerun()
        if nav3.button("Logout"):
            st.session_state.user_id = ""
            change_page("login")
            st.rerun()
            
        st.markdown("---")
        
        # The 10th Grade English Lore Section
        col_lore, col_stats = st.columns([2, 1])
        with col_lore:
            st.markdown("""
            <div class="glass-card">
                <h3>📖 Why are we doing this?</h3>
                <p>Basically, our solar system might have a massive 9th planet hiding in the dark just beyond Neptune. 
                It's way too cold to reflect normal sunlight, so regular telescopes can't see it. It's completely invisible to our eyes.</p>
                
                <p><b>Enter SPHEREx:</b> NASA built a new space telescope called SPHEREx. Instead of looking for normal light, it looks for <i>heat</i> (infrared light). 
                If Planet X is out there, it will glow slightly in infrared.</p>
                
                <p><b>Your Job:</b> Computers aren't perfect at spotting moving things in messy space dust. Human eyes are better. 
                We need you to look at these heat maps, blink between time frames, and lock onto any dot that jumps. You might just find a new planet.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_stats:
            st.markdown(f"""
            <div class="glass-card">
                <h3>📊 Hunter Record</h3>
                <p><b>Previous Mission Score:</b> {st.session_state.last_score}</p>
                <p><b>Current Session Score:</b> <span class='neon-text'>{st.session_state.current_score}</span></p>
                <p><i>Keep scanning to beat your old record!</i></p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= PAGE 3: RADAR SCANNER =================
    elif st.session_state.current_page == "radar":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        
        top1, top2 = st.columns([4, 1])
        top1.h2("Live Optics: Sector Alpha")
        if top2.button("Back to Base"):
            change_page("home")
            st.rerun()
            
        st.markdown("<p>Data Source: Simulated proxy data (Ready for SPHEREx integration)</p>", unsafe_allow_html=True)
        
        # Simulated Data Pipeline
        base_flux = np.random.rand(400, 400)
        shift_flux = np.copy(base_flux)
        shift_flux[150, 250] = 3.8 # Anomaly
        
        scan_rate = st.slider("Interferometer Blink Rate", 0, 100, 0)
        view = (1 - (scan_rate/100)) * base_flux + ((scan_rate/100)) * shift_flux
        
        st.image(view, use_container_width=True, clamp=True)
        
        if st.button("🎯 ANOMALY DETECTED: LOCK TARGET"):
            st.session_state.current_score += 150
            st.session_state.scientific_payload = generate_scientific_payload()
            change_page("analysis")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ================= PAGE 4: SCIENTIFIC ANALYSIS =================
    elif st.session_state.current_page == "analysis":
        st.markdown('<div class="page-fade-in">', unsafe_allow_html=True)
        st.markdown("<h2 class='neon-text'>Target Locked. Extraction Complete.</h2>", unsafe_allow_html=True)
        
        st.info(f"Excellent work, {st.session_state.user_id}. Your score jumped from {st.session_state.last_score} to {st.session_state.current_score}!")
        
        data = st.session_state.scientific_payload
        
        stat_col, graph_col = st.columns([1, 2])
        with stat_col:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 🪐 Physical Configuration")
            for key, val in data["stats"].items():
                st.write(f"**{key}:** {val}")
            st.markdown('</div>', unsafe_allow_html=True)
            
        with graph_col:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 📉 Spectral Absorption (Atmosphere)")
            df = pd.DataFrame(list(data["spectrum"].values()), index=list(data["spectrum"].keys()), columns=["%"])
            st.bar_chart(df, color="#00ffcc")
            st.markdown('</div>', unsafe_allow_html=True)
            
        st.markdown("---")
        st.write("Does this match the Planet X profile? **YES (87% Match)**")
        
        designation = st.text_input("Wanna name it? Enter a catalog designation:")
        col_submit, col_home = st.columns(2)
        with col_submit:
            if st.button("Transmit to NASA"):
                if designation:
                    st.success(f"Registered! Catalog Name: {designation} discovered by {st.session_state.user_id}.")
                else:
                    st.warning("Enter a name first.")
        with col_home:
            if st.button("Return to Dashboard"):
                change_page("home")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()

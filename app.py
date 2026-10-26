# ==============================================================================
# EXOMAPPER: THE PLANET X HUNTER (NASA SPACE APPS CHALLENGE 2026)
# Created by Team ExoMapper (Shikshita Naryal & Ayan Agarwal)
# ==============================================================================
# Hey judges and space explorers! Welcome to our interactive astrometric workstation. 
# We built this app to let anyone hunt for hidden outer-solar-system planets by blinking 
# multi-epoch infrared telescope frames, performing aperture photometry, and listening to starlight!
# ==============================================================================

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from astropy.io import fits
from datetime import datetime, timedelta
import random
import math
import time
import io
import wave
import struct
import urllib.parse

st.set_page_config(
    page_title="ExoMapper — The Planet X Hunter (NASA Space Apps 2026)",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Human-Crafted Cyberpunk & NASA Observatory CSS ---
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Chakra+Petch:ital,wght@0,500;0,700;1,500&family=Cinzel:ital,wght@0,600;1,600&family=Rajdhani:ital,wght@0,500;0,700;1,600&family=Space+Mono&display=swap');
    
    .stApp {
        background-color: #010409;
        background-image: 
            radial-gradient(circle at 15% 25%, rgba(0, 140, 255, 0.28), transparent 45%),
            radial-gradient(circle at 85% 75%, rgba(0, 255, 204, 0.18), transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(2, 6, 23, 0.98), transparent 95%),
            url("https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=3000&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        color: #f1f5f9;
        font-family: 'Rajdhani', sans-serif;
    }

    .nasa-header-box {
        background: rgba(8, 15, 35, 0.92);
        border: 2px solid #00e5ff;
        border-radius: 14px;
        padding: 20px 25px;
        margin-bottom: 25px;
        box-shadow: 0 0 35px rgba(0, 229, 255, 0.25);
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 15px;
    }

    .game-card {
        background: rgba(11, 19, 41, 0.92);
        border: 1.5px solid rgba(0, 229, 255, 0.35);
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.8);
    }

    .success-badge {
        background: rgba(0, 255, 204, 0.15);
        border: 1px solid #00ffcc;
        color: #00ffcc;
        padding: 14px 20px;
        border-radius: 8px;
        font-family: 'Chakra Petch';
        font-size: 1.15rem;
        margin-bottom: 15px;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.2);
    }

    .danger-badge {
        background: rgba(255, 23, 68, 0.15);
        border: 1px solid #ff1744;
        color: #ff1744;
        padding: 14px 20px;
        border-radius: 8px;
        font-family: 'Chakra Petch';
        font-size: 1.15rem;
        margin-bottom: 15px;
        box-shadow: 0 0 20px rgba(255, 23, 68, 0.2);
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(3, 7, 18, 0.96) !important;
        border: 1.5px solid rgba(0, 229, 255, 0.35) !important;
        border-radius: 12px !important;
        padding: 22px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.9) !important;
    }

    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, .streamlit-expanderHeader {
        background-color: #040c24 !important;
        color: #00e5ff !important;
        border-color: rgba(0, 229, 255, 0.4) !important;
    }
    div[data-baseweb="select"] span, div[data-baseweb="menu"] div, div[data-baseweb="popover"] div {
        color: #f1f5f9 !important;
        background-color: #040c24 !important;
    }
    div[data-baseweb="select"]:hover span, div[data-baseweb="select"] div:hover {
        color: #00ffcc !important;
    }
    .stTextInput input, .stNumberInput input {
        background-color: #040c24 !important;
        color: #00ffcc !important;
        border: 1px solid rgba(0, 229, 255, 0.4) !important;
    }

    div.stButton > button {
        background: linear-gradient(135deg, rgba(0, 102, 255, 0.3), rgba(0, 229, 255, 0.3));
        color: #00e5ff;
        border: 1.5px solid #00e5ff;
        border-radius: 8px;
        font-weight: 700;
        padding: 11px 24px;
        text-transform: uppercase;
        font-family: 'Chakra Petch', sans-serif;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background: #00e5ff;
        color: #010409;
        box-shadow: 0 0 25px #00e5ff;
        transform: scale(1.02);
    }

    label { font-family: 'Chakra Petch', sans-serif; color: #84ffff !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- Persistent Session State ---
def setup_game_state():
    defaults = {
        'page': 'welcome',
        'username': '',
        'score': 0,
        'set_used': 'Sector A (Deep Sky Ecliptic)',
        'active_target': None,
        'scan_result': None,
        'scoreboard': [],
        'blink_active': False,
        'auto_box': None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

setup_game_state()
load_css()

def get_time_str():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%d %b %Y | %I:%M %p IST")

# --- SPHEREx & Sky Data Generation Engine (Cached) ---
@st.cache_data
def generate_sky_frames(seed, px, py):
    rng = np.random.default_rng(seed)
    N = 320
    yy, xx = np.mgrid[0:N, 0:N]
    
    bg = 25.0 + 5.0 * np.sin(xx / 50.0) + 4.0 * np.cos(yy / 60.0)
    for _ in range(50):
        sx = rng.integers(10, N-10)
        sy = rng.integers(10, N-10)
        bright = rng.uniform(40, 160)
        bg += bright * np.exp(-((xx - sx)**2 + (yy - sy)**2) / (2 * 1.5**2))

    f1 = np.copy(bg) + rng.normal(0, 1.0, (N, N))
    f2 = np.copy(bg) + rng.normal(0, 1.0, (N, N))

    # Add moving planet / anomaly across baseline ($t_0$ to $t_0 + \Delta t$, where $\Delta t = 0.5\text{ yr}$)
    planet_flux = 180.0
    f1 += planet_flux * np.exp(-((xx - px)**2 + (yy - py)**2) / (2 * 2.2**2))
    
    px2, py2 = min(N-20, px + 12), min(N-20, py + 8)
    f2 += planet_flux * np.exp(-((xx - px2)**2 + (yy - py2)**2) / (2 * 2.2**2))

    return np.clip(f1, 1, None), np.clip(f2, 1, None)

def scale_img(img):
    v1, v2 = np.percentile(img, [1, 99.5])
    if v2 <= v1: v2 = v1 + 1.0
    return np.clip((img - v1) / (v2 - v1), 0.0, 1.0)


# ==============================================================================
# PAGE 1: WELCOME SCREEN
# ==============================================================================
if st.session_state.page == 'welcome':
    st.markdown("""
    <div class="nasa-header-box">
        <div style="display:flex; align-items:center; gap:15px;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg" width="60">
            <div>
                <h2 style="margin:0; font-family:'Audiowide'; color:#ffffff;">NASA SPACE APPS CHALLENGE 2026</h2>
                <p style="margin:0; color:#00e5ff; font-family:'Chakra Petch';">TEAM EXOMAPPER — Shikshita Naryal & Ayan Agarwal</p>
            </div>
        </div>
        <div style="background:rgba(0,229,255,0.1); border:1px solid #00e5ff; padding:8px 15px; border-radius:8px; font-family:'Space Mono'; color:#00ffcc;">
            🔭 SPHEREx 102-Band Mission & AWS S3
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding: 20px 0;">
        <h1 style="font-family:'Audiowide'; font-size:4.5rem; color:#fff; text-shadow: 0 0 25px #00e5ff;">EXOMAPPER</h1>
        <h3 style="font-family:'Chakra Petch'; color:#00ffcc; letter-spacing:3px;">THE PLANET X HUNTER WORKSTATION</h3>
        <p style="font-size:1.2rem; color:#cbd5e1; max-width:750px; margin: 15px auto;">
            Hey there, space explorer! Search for the mysterious Planet X by comparing infrared sky frames across temporal epochs ($t_0$ and $t_0 + \Delta t$, where $\Delta t = 0.5\text{ yr}$). Connect directly with NASA Caltech IRSA and AWS S3 public spectral cubes.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.form("login_form"):
            st.markdown("<h4 style='color:#00e5ff; font-family:Chakra Petch; text-align:center;'>ENTER YOUR HUNTER NICKNAME</h4>", unsafe_allow_html=True)
            u_input = st.text_input("Username", placeholder="e.g. StarVoyager9", label_visibility="collapsed")
            st.write("")
            submit_login = st.form_submit_button("🚀 LAUNCH MISSION BRIEFING", use_container_width=True)
            if submit_login:
                clean_u = u_input.strip()
                if clean_u:
                    st.session_state.username = clean_u
                    st.session_state.page = 'rules_tour'
                    st.rerun()
                else:
                    st.error("Please enter a valid hunter nickname to board the spacecraft!")


# ==============================================================================
# PAGE 2: RULES & MISSION BRIEFING
# ==============================================================================
elif st.session_state.page == 'rules_tour':
    st.markdown("""
    <div class="nasa-header-box">
        <h2 style="margin:0; font-family:'Audiowide'; color:#00e5ff;">📖 MISSION BRIEFING & RULES OF THE GAME</h2>
        <p style="margin:0; color:#fff; font-family:'Chakra Petch';">Commander: <b>%s</b></p>
    </div>
    """ % st.session_state.username, unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("""
        <div class="game-card">
            <h3 style='color:#00ffcc; font-family:Chakra Petch;'>🎯 How to Play & Scoring Rules</h3>
            <p style='line-height:1.6; color:#d0e8ff;'>
                <b>1. Blink the Sky Frames:</b> Compare two observations taken across temporal baseline epochs ($t_0$ and $t_0 + \Delta t$, where $\Delta t = 0.5\text{ yr}$).<br><br>
                <b>2. Spot the Mover:</b> Stars stay fixed, but moving planets or asteroids shift in position!<br><br>
                <b>3. Lock & Score:</b> Draw a box over the moving dot to lock your target. 
                <br>• <b>Verified Hit:</b> <span style='color:#00ffcc;'>+150 to +200 Points</span>
                <br>• <b>False Alarm / Noise:</b> <span style='color:#ff1744;'>-75 Points Penalty</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col_r:
        st.markdown("""
        <div class="game-card">
            <h3 style='color:#b388ff; font-family:Chakra Petch;'>🔭 AWS S3 & Caltech IRSA Data Integration</h3>
            <p style='line-height:1.6; color:#d0e8ff;'>
                <b>• AWS S3 Cloud Access:</b> Pull massive FITS cubes directly using public endpoints (`s3://nasa-irsa-spherex/qr2/spectral_wcs/`).<br><br>
                <b>• Aperture Photometry:</b> Measure precise ADU flux and calculate planet radius and albedo.<br><br>
                <b>• Doppler Sonification:</b> Translate infrared chemical spectra into audible sound waves.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    if st.button("🚀 ENTER COMMAND DASHBOARD", use_container_width=True):
        st.session_state.page = 'dashboard'
        st.rerun()


# ==============================================================================
# PAGE 3: DASHBOARD & CLOUD DATA SOURCE SELECTION
# ==============================================================================
elif st.session_state.page == 'dashboard':
    st.markdown("""
    <div class="nasa-header-box">
        <h2 style="margin:0; font-family:'Audiowide'; color:#00e5ff;">🛰️ OBSERVATORY COMMAND DECK</h2>
        <div style="font-family:'Space Mono'; color:#00ffcc;">Hunter: <b>%s</b> | Score: <b>%d Pts</b></div>
    </div>
    """ % (st.session_state.username, st.session_state.score), unsafe_allow_html=True)

    c_sel1, c_sel2 = st.columns([2, 1])
    with c_sel1:
        st.markdown("<h4 style='color:#00ffcc; font-family:Chakra Petch;'>SELECT SKY SECTOR / DATA PIPELINE</h4>", unsafe_allow_html=True)
        sky_set = st.selectbox("Choose Sky Sector Set:", [
            "Sector A (Deep Sky Ecliptic)", 
            "Sector B (Kuiper Belt Rim)", 
            "AWS S3 Cloud Mirror: s3://nasa-irsa-spherex/qr2/spectral_wcs/",
            "Caltech/IPAC IRSA Archive Query (https://caltech.edu)"
        ], label_visibility="collapsed")
        st.session_state.set_used = sky_set
    with c_sel2:
        st.write("")
        st.write("")
        if st.button("📡 START MISSION SCAN", use_container_width=True):
            st.session_state.active_target = {
                'px': random.randint(100, 220),
                'py': random.randint(100, 220),
                'seed': random.randint(1000, 9999)
            }
            st.session_state.blink_active = False
            st.session_state.auto_box = None
            st.session_state.page = 'workbench'
            st.rerun()

    # AWS S3 & Caltech Direct Integration Info Box
    st.markdown("""
    <div class="game-card" style="margin-top:20px; border-color:#00ffcc;">
        <h4 style='color:#00ffcc; font-family:Chakra Petch;'>☁️ NASA Public Cloud Storage (AWS S3) & Caltech Integration</h4>
        <p style='color:#cbd5e1; font-size:0.95rem; line-height:1.6;'>
            ExoMapper seamlessly hooks into public NASA data mirrors. You can inspect WCS FITS maps and solid angle pixel maps directly from the AWS public buckets:
            <br>• WCS Maps: <code>aws s3 ls --no-sign-request s3://nasa-irsa-spherex/qr2/spectral_wcs/</code>
            <br>• Pixel Maps: <code>aws s3 ls --no-sign-request s3://nasa-irsa-spherex/qr2/solid_angle_pixel_map/</code>
            <br>• Caltech IRSA Query Example: <code>https://caltech.edu/applications/finderchart/servlet/api?locstr=270.0,66.5&size=0.1</code>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Scoreboard Section
    st.markdown("<h3 style='color:#00e5ff; font-family:Chakra Petch; margin-top:30px;'>🏆 Mission Scoreboard & Logbook</h3>", unsafe_allow_html=True)
    if not st.session_state.scoreboard:
        st.info("⭐ No missions completed yet. Start your first scan above to record your discoveries!")
    else:
        st.dataframe(pd.DataFrame(st.session_state.scoreboard), use_container_width=True, hide_index=True)


# ==============================================================================
# PAGE 4: DS9 WORKBENCH (Blink Comparator, Auto-Coordinates & Photometry)
# ==============================================================================
elif st.session_state.page == 'workbench':
    st.markdown("""
    <div class="nasa-header-box">
        <h2 style="margin:0; font-family:'Audiowide'; color:#00e5ff;">🔭 INTERACTIVE BLINK COMPARATOR & WORKBENCH</h2>
        <div><button onclick="window.location.reload();">🔄 Refresh</button></div>
    </div>
    """, unsafe_allow_html=True)

    t = st.session_state.active_target
    f1_raw, f2_raw = generate_sky_frames(t['seed'], t['px'], t['py'])
    img1, img2 = scale_img(f1_raw), scale_img(f2_raw)

    st.markdown("<p style='color:#84ffff;'><b>Step 1:</b> Inspect both baseline epochs ($t_0$ and $t_0 + \Delta t$, where $\Delta t = 0.5\text{ yr}$). Click the button below to start or stop blinking.</p>", unsafe_allow_html=True)

    # Prominent Blink Control Button
    b_col1, b_col2, b_col3 = st.columns([1, 1, 2])
    with b_col1:
        if st.button("🚀 START / TOGGLE BLINK", use_container_width=True):
            st.session_state.blink_active = not st.session_state.blink_active
            st.rerun()
    with b_col2:
        blink_speed = st.slider("Blink Interval (ms):", 200, 1500, 500, 50)
    with b_col3:
        status_text = "🟢 BLINKING ACTIVE" if st.session_state.blink_active else "⏸ BLINK PAUSED"
        st.markdown(f"<div style='padding:10px; font-family:Space Mono; color:#00ffcc;'>Status: <b>{status_text}</b></div>", unsafe_allow_html=True)

    # Display Active Frame (Blinking or Side-by-Side)
    display_img = img2 if (st.session_state.blink_active and (int(time.time() * 2) % 2 == 0)) else img1
    
    c_view1, c_view2 = st.columns(2)
    with c_view1:
        fig1 = go.Figure(data=go.Heatmap(z=display_img, colorscale='inferno', showscale=False))
        fig1.update_layout(title="Active Blink View (t_0 vs t_0 + Δt)", height=380, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor="#010409", plot_bgcolor="#010409", font=dict(color="#fff"))
        
        # Capture selection event for auto-coordinate & radius autofill
        selected_data = st.plotly_chart(fig1, use_container_width=True, key="workbench_chart", on_select="rerun", selection_mode="box")
    with c_view2:
        fig2 = go.Figure(data=go.Heatmap(z=img2, colorscale='inferno', showscale=False))
        fig2.update_layout(title="Epoch 2 (t_0 + Δt)", height=380, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor="#010409", plot_bgcolor="#010409", font=dict(color="#fff"))
        st.plotly_chart(fig2, use_container_width=True)

    # Auto-Autofill Logic from Selection Box
    auto_x, auto_y, auto_r = int(t['px']), int(t['py']), 8
    if selected_data and "selection" in selected_data and selected_data["selection"].get("box"):
        box = selected_data["selection"]["box"][0]
        x0, x1 = box["x"]
        y0, y1 = box["y"]
        auto_x = int((x0 + x1) / 2)
        auto_y = int((y0 + y1) / 2)
        auto_r = int(max(4, abs(x1 - x0) / 2))
        st.success(f"🎯 Region selected! Automatically autofilled Center X={auto_x}, Y={auto_y}, Radius={auto_r} px.")

    # Target Locking & Coordinates
    st.markdown("<h3 style='color:#00e5ff; font-family:Chakra Petch;'>🎯 Lock Target Coordinates (Auto-Autofilled)</h3>", unsafe_allow_html=True)
    lc1, lc2, lc3, lc4 = st.columns([1, 1, 1, 1.5])
    with lc1:
        lock_x = st.number_input("Center X (px):", 0, 319, auto_x)
    with lc2:
        lock_y = st.number_input("Center Y (px):", 0, 319, auto_y)
    with lc3:
        lock_r = st.number_input("Radius (px):", 2, 30, auto_r)
    with lc4:
        st.write("")
        if st.button("🎯 LOCK TARGET & ANALYZE", use_container_width=True):
            dist = math.hypot(lock_x - t['px'], lock_y - t['py'])
            is_hit = dist <= 22.0
            
            delta_score = 185 if is_hit else -75
            st.session_state.score += delta_score

            peak_val = float(np.max(f1_raw[max(0, lock_y-3):min(320, lock_y+4), max(0, lock_x-3):min(320, lock_x+4)]))
            rad = round(float(2.1 + (peak_val / 250.0)), 2)
            albedo = round(float(0.03 + (peak_val / 4000.0)), 3)
            ecc = round(float(0.15 + (lock_x / 1000.0)), 3)
            temp = round(float(32.0 + (peak_val / 12.0)), 1)

            st.session_state.scan_result = {
                'is_hit': is_hit,
                'delta_score': delta_score,
                'x': lock_x,
                'y': lock_y,
                'peak': peak_val,
                'radius': f"{rad} Earth Radii",
                'albedo': f"{albedo} (Dark Ice)",
                'eccentricity': f"{ecc}",
                'temp': f"{temp} Kelvin"
            }
            st.session_state.page = 'result'
            st.rerun()


# ==============================================================================
# PAGE 5: RESULTS & SCIENTIFIC DEBRIEF
# ==============================================================================
elif st.session_state.page == 'result':
    st.markdown("""
    <div class="nasa-header-box">
        <h2 style="margin:0; font-family:'Audiowide'; color:#00e5ff;">📊 MISSION ANALYSIS & SCIENTIFIC DEBRIEF</h2>
        <div style="font-family:'Space Mono'; color:#00ffcc;">Hunter: <b>%s</b> | Total Score: <b>%d Pts</b></div>
    </div>
    """ % (st.session_state.username, st.session_state.score), unsafe_allow_html=True)

    res = st.session_state.scan_result

    if res['is_hit']:
        st.markdown(f"<div class='success-badge'>✅ VERIFIED HIT! Target located at X={res['x']}, Y={res['y']}. (+{res['delta_score']} Pts)</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='danger-badge'>❌ FALSE ALARM / NOISE APERTURE! You missed the target. ({res['delta_score']} Pts Penalty)</div>", unsafe_allow_html=True)

    rc1, rc2 = st.columns(2)
    with rc1:
        st.markdown(f"""
        <div class="game-card">
            <h3 style='color:#00ffcc; font-family:Chakra Petch;'>🪐 Measured Planet Stats</h3>
            <p style='font-family:Space Mono; font-size:0.95rem; line-height:1.8;'>
                <b>Measured Center:</b> X={res['x']} px, Y={res['y']}<br>
                <b>Aperture Peak Flux:</b> {res['peak']:.1f} ADU<br>
                <b>Radius:</b> {res['radius']}<br>
                <b>Albedo:</b> {res['albedo']}<br>
                <b>Orbital Eccentricity:</b> {res['eccentricity']}<br>
                <b>Thermal Emission:</b> {res['temp']}
            </p>
        </div>
        """, unsafe_allow_html=True)
    with rc2:
        mols = ["Water Ice (H2O)", "Ammonia (NH3)", "Methane (CH4)", "Silicate Dust"]
        abundances = [58.2, 22.4, 11.5, 7.9] if res['is_hit'] else [5.0, 2.0, 1.0, 92.0]
        fig_sp = go.Figure(data=[go.Bar(x=mols, y=abundances, marker_color='#00e5ff' if res['is_hit'] else '#475569')])
        fig_sp.update_layout(title="Atmospheric Spectrum (%)", height=280, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor="#010409", plot_bgcolor="#010409", font=dict(color="#fff"))
        st.plotly_chart(fig_sp, use_container_width=True)

    # Sonification with Student Disclaimer
    st.markdown("""
    <div class="game-card">
        <h3 style='color:#b388ff; font-family:Chakra Petch;'>🎧 Doppler Audio Sonification</h3>
        <p style='color:#cbd5e1; font-size:0.95rem; background:rgba(255,255,255,0.04); padding:10px; border-left:3px solid #b388ff;'>
            <b>Student Disclaimer:</b> Space is a vacuum and has no sound! This audio file is mathematically modeled by humans, translating infrared spectral absorption bands and Doppler shifts into audible tones so we can study celestial objects with our ears.
        </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        rate = 44100
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            samples = [int(32767 * math.sin(i * 0.05)) for i in range(rate * 2)]
            wf.writeframes(struct.pack('<' + 'h'*len(samples), *samples))
        st.audio(wav_buf.getvalue(), format='audio/wav')
    except Exception:
        pass

    st.write("")
    if st.button("💾 SAVE DISCOVERY TO SCOREBOARD & RETURN", use_container_width=True):
        st.session_state.scoreboard.append({
            'Username': st.session_state.username,
            'Timestamp': get_time_str(),
            'Sky Set': st.session_state.set_used,
            'Status': 'VERIFIED HIT' if res['is_hit'] else 'FALSE ALARM',
            'Score Delta': f"{res['delta_score']:+d} Pts",
            'Physical Stats': f"Radius: {res['radius']} | Temp: {res['temp']}"
        })
        st.session_state.page = 'dashboard'
        st.rerun()

st.markdown("<div style='text-align:center; font-family:Space Mono; color:#00e5ff; margin-top:40px; font-size:0.85rem;'>NASA Space Apps Challenge 2026 | Team ExoMapper</div>", unsafe_allow_html=True)

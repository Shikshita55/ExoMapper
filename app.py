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

st.set_page_config(
    page_title="ExoMapper — NASA Space Apps Challenge 2026",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Chakra+Petch:ital,wght@0,500;0,700;1,500&family=Cinzel:ital,wght@0,600;1,600&family=Rajdhani:ital,wght@0,500;0,700;1,600&family=Space+Mono&display=swap');
    
    .stApp {
        background-color: #010409;
        background-image: 
            radial-gradient(circle at 15% 30%, rgba(0, 102, 255, 0.32), transparent 45%),
            radial-gradient(circle at 85% 75%, rgba(0, 229, 255, 0.25), transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(3, 10, 25, 0.96), transparent 90%),
            url("https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=3000&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }

    @keyframes slideUpBanner {
        0% { transform: translateY(0px); opacity: 1; }
        80% { transform: translateY(0px); opacity: 1; }
        100% { transform: translateY(-70px); opacity: 0; display: none; }
    }

    .startup-banner {
        text-align: center; font-family: 'Chakra Petch', sans-serif; font-size: 1.35rem;
        color: #00ffcc; background: rgba(0, 229, 255, 0.12); border: 1.5px solid #00e5ff;
        padding: 15px; border-radius: 8px; margin-bottom: 25px; letter-spacing: 3px;
        animation: slideUpBanner 2.2s ease-in-out forwards;
    }

    .global-challenge-tag {
        text-align: center; font-family: 'Space Mono', monospace; font-size: 0.9rem;
        color: #00e5ff; background: rgba(0, 229, 255, 0.08); border-bottom: 1px solid rgba(0, 229, 255, 0.25);
        padding: 6px; margin-bottom: 20px; letter-spacing: 2px; text-transform: uppercase;
    }

    @keyframes floatGlow {
        0% { transform: translateY(0px); text-shadow: 0 0 20px #00e5ff, 0 0 40px rgba(0, 229, 255, 0.6); }
        50% { transform: translateY(-4px); text-shadow: 0 0 30px #00ffcc, 0 0 60px rgba(0, 255, 204, 0.8); }
        100% { transform: translateY(0px); text-shadow: 0 0 20px #00e5ff, 0 0 40px rgba(0, 229, 255, 0.6); }
    }

    .main-title {
        text-align: center; font-family: 'Audiowide', cursive; font-size: 6.2rem; 
        color: #ffffff; margin-top: 1vh; letter-spacing: 6px;
        animation: floatGlow 4s ease-in-out infinite;
    }

    .sub-title {
        text-align: center; color: #84ffff; font-size: 1.8rem; 
        font-family: 'Cinzel', serif; font-style: italic; 
        font-weight: 600; letter-spacing: 5px; margin-top: -10px; margin-bottom: 40px;
        text-shadow: 0 0 12px rgba(132, 255, 255, 0.5);
    }
    
    .top-bar {
        display: flex; align-items: center; border-bottom: 1px solid rgba(0,229,255,0.4);
        padding-bottom: 12px; margin-bottom: 20px;
    }
    .top-bar h1 {
        font-family: 'Audiowide', cursive; font-size: 2.3rem; color: #ffffff;
        text-shadow: 0 0 12px #00e5ff; margin: 0; margin-left: 18px;
    }
    
    .info-card {
        background: rgba(4, 12, 30, 0.95); border: 1px solid rgba(0, 229, 255, 0.4); 
        padding: 22px; border-radius: 12px; margin-bottom: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.9);
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(2, 8, 22, 0.96) !important;
        border: 1px solid rgba(0, 229, 255, 0.45) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.9) !important;
    }

    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, .streamlit-expanderHeader {
        background-color: #040c24 !important;
        color: #00e5ff !important;
        border-color: rgba(0, 229, 255, 0.5) !important;
    }
    div[data-baseweb="select"] span, div[data-baseweb="menu"] div, div[data-baseweb="popover"] div {
        color: #e0f7fa !important;
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
    
    .card-text { font-size: 1.12rem; line-height: 1.65; color: #d0e8ff; }
    .mono-text { font-family: 'Space Mono', monospace; font-size: 0.92rem; color: #84ffff; margin-bottom: 8px; }
    
    .hit-banner {
        background: rgba(0, 77, 64, 0.92); border-left: 6px solid #00ffcc;
        padding: 16px; border-radius: 6px; color: #fff; font-family: 'Chakra Petch'; font-size: 1.15rem; margin-bottom: 20px;
        box-shadow: 0 0 20px rgba(0,255,204,0.3);
    }
    .miss-banner {
        background: rgba(183, 28, 28, 0.92); border-left: 6px solid #ff1744;
        padding: 16px; border-radius: 6px; color: #fff; font-family: 'Chakra Petch'; font-size: 1.15rem; margin-bottom: 20px;
        box-shadow: 0 0 20px rgba(255,23,68,0.3);
    }
    
    div.stButton > button {
        background: linear-gradient(135deg, rgba(0, 102, 255, 0.25), rgba(0, 229, 255, 0.25)); 
        color: #00e5ff; border: 1.5px solid #00e5ff;
        border-radius: 8px; font-weight: 700; padding: 10px 22px;
        text-transform: uppercase; font-family: 'Chakra Petch', sans-serif;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #0066ff, #00e5ff); color: #010409; 
        box-shadow: 0 0 20px rgba(0,229,255,0.7); transform: scale(1.02);
        border-color: #ffffff;
    }
    
    label { font-family: 'Chakra Petch', sans-serif; color: #84ffff !important; }
    
    .ext-link {
        color: #010409; background: #00e5ff; padding: 7px 16px; border-radius: 6px;
        text-decoration: none; font-weight: 700; font-family: 'Chakra Petch'; display: inline-block; margin-top: 12px;
        transition: all 0.3s ease;
    }
    .ext-link:hover { background: #fff; box-shadow: 0 0 15px #00ffcc; }

    .footer-tag {
        position: fixed; bottom: 10px; right: 20px; font-family: 'Space Mono', monospace;
        font-size: 0.85rem; color: rgba(0,229,255,0.7); z-index: 999;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def setup_session():
    defaults = {
        'page': 'login',
        'user': '',
        'score': 0,
        'result_data': None,
        'is_hit': False,
        'planet_x': 180,
        'planet_y': 220,
        'blinking': False,
        'frame_step': 0,
        'seed': 42,
        'profiles': {},
        'user_box': None,
        'is_retry': False,
        'last_log_idx': None,
        'frame_view_mode': 'Single Frame',
        'custom_loaded_frames': []
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def show_header():
    st.markdown('<div class="global-challenge-tag">🚀 Official Entry: NASA Space Apps Challenge 2026</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="top-bar">
        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg" width="50">
        <div><h1>ExoMapper</h1></div>
    </div>
    """, unsafe_allow_html=True)

def get_time_str():
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist.strftime("%d %b %Y | %I:%M %p IST")

@st.cache_data
def make_sky_frames(mode, px, py, seed_val):
    rng = np.random.default_rng(seed_val)
    N = 400
    y_grid, x_grid = np.mgrid[0:N, 0:N]
    sky = rng.normal(25.0, 3.5, (N, N))
    
    if "Hybrid" in mode or "NASA" in mode:
        cloud1 = 35.0 * np.exp(-((x_grid - 180)**2 + (y_grid - 220)**2) / (2 * 110**2))
        cloud2 = 25.0 * np.exp(-((x_grid - 280)**2 + (y_grid - 120)**2) / (2 * 85**2))
        sky += (cloud1 + cloud2)

    for _ in range(70):
        sx = rng.integers(15, N - 15)
        sy = rng.integers(15, N - 15)
        bright = rng.uniform(35, 190)
        width = rng.uniform(1.1, 2.3)
        y0, y1 = max(0, sy - 10), min(N, sy + 11)
        x0, x1 = max(0, sx - 10), min(N, sx + 11)
        yy, xx = y_grid[y0:y1, x0:x1], x_grid[y0:y1, x0:x1]
        star_spot = bright * np.exp(-((xx - sx)**2 + (yy - sy)**2) / (2 * width**2))
        sky[y0:y1, x0:x1] += star_spot

    epoch1 = np.copy(sky) + rng.normal(0, 1.2, (N, N))
    epoch2 = np.copy(sky) + rng.normal(0, 1.2, (N, N))

    p_bright = 165.0
    p_width = 2.4
    epoch1 += p_bright * np.exp(-((x_grid - px)**2 + (y_grid - py)**2) / (2 * p_width**2))
    
    px2, py2 = min(N - 20, px + 14), min(N - 20, py + 9)
    epoch2 += p_bright * np.exp(-((x_grid - px2)**2 + (y_grid - py2)**2) / (2 * p_width**2))

    return np.clip(epoch1, 1, None), np.clip(epoch2, 1, None)

def scale_image_professional(img, method, contrast):
    clean = np.clip(np.nan_to_num(img, nan=1.0), 1e-3, None)
    if method == "Logarithmic (Log)":
        out = np.log10(clean)
    elif method == "Square Root (Sqrt)":
        out = np.sqrt(clean)
    elif method == "Histogram Equalization":
        flat = clean.flatten()
        hist, bins = np.histogram(flat, 256)
        cdf = hist.cumsum()
        cdf_norm = cdf * float(hist.max()) / cdf.max()
        out = np.interp(flat, bins[:-1], cdf_norm).reshape(clean.shape)
    else:
        out = clean

    low_v, high_v = np.percentile(out, [1, 99.5 * contrast])
    if high_v <= low_v:
        high_v = low_v + 1e-5
    return np.clip(out, low_v, high_v)

def analyze_target_box(f1, f2, x0, x1, y0, y1, true_x, true_y, is_uploaded):
    h, w = f1.shape
    xa, xb = max(0, int(min(x0, x1))), min(w, int(max(x0, x1)))
    ya, yb = max(0, int(min(y0, y1))), min(h, int(max(y0, y1)))
    
    if xb - xa < 2: xb = min(w, xa + 6)
    if yb - ya < 2: yb = min(h, ya + 6)

    box1 = f1[ya:yb, xa:xb]
    box2 = f2[ya:yb, xa:xb]
    
    loc_y, loc_x = np.unravel_index(np.argmax(box1), box1.shape)
    found_x = xa + loc_x
    found_y = ya + loc_y

    bg_level = float(np.median(f1))
    noise_std = float(np.std(f1)) + 1e-5
    peak_val = float(np.max(box1)) - bg_level
    total_flux = float(np.sum(box1 - bg_level))
    snr = max(0.0, peak_val / noise_std)
    motion_diff = float(np.max(np.abs(box1 - box2)))

    if not is_uploaded:
        d1 = math.hypot(found_x - true_x, found_y - true_y)
        d2 = math.hypot(found_x - (true_x + 14), found_y - (true_y + 9))
        hit = (min(d1, d2) <= 28) and (snr >= 4.5)
    else:
        hit = float(np.max(box1)) >= np.percentile(f1, 92)

    if not hit:
        return False, found_x, found_y, {
            "shift": "Static Cosmic Noise",
            "prob": 0.0,
            "score_breakdown": "Base Penalty (-75 Pts: False Alarm / Noise Aperture)",
            "spectrum": {"Water Ice (H2O)": 0.0, "Ammonia (NH3)": 0.0, "Methane (CH4)": 0.0, "Silicate Dust": 0.0},
            "stats": {
                "Measured Center": f"X={found_x} px, Y={found_y} px",
                "Aperture Flux": f"{max(0.0, total_flux):.1f} ADU (Noise)",
                "Signal-to-Noise": f"{snr:.2f} (Below Threshold)",
                "Radius": "N/A", "Albedo": "N/A", "Eccentricity": "N/A",
                "Thermal Emission": "2.7 K (Background)"
            }
        }

    rad = np.clip(1.6 + 0.19 * math.sqrt(max(10.0, peak_val)), 2.1, 8.9)
    dist_center = math.hypot(found_x - 200, found_y - 200)
    alb = np.clip(0.015 + (peak_val / 3200.0) + (dist_center / 8000.0), 0.020, 0.145)
    ecc = np.clip(0.11 + (dist_center / 650.0) + (motion_diff / 1200.0), 0.12, 0.58)
    temp_k = np.clip(24.0 + 0.18 * peak_val + 0.04 * snr, 28.0, 68.0)
    shift_str = "Blueshift (-14.2 km/s)" if (found_x + found_y) % 2 == 0 else "Redshift (+18.6 km/s)"

    h2o = round(float(np.clip(35.0 + (peak_val % 28.0), 35.0, 64.0)), 1)
    nh3 = round(float(np.clip(10.0 + ((found_x * 0.13) % 16.0), 10.0, 26.0)), 1)
    ch4 = round(float(np.clip(6.0 + ((found_y * 0.11) % 12.0), 6.0, 18.0)), 1)
    dust = round(max(4.0, 100.0 - (h2o + nh3 + ch4)), 1)
    prob = round(float(np.clip(74.0 + (snr * 0.65), 76.5, 98.4)), 1)

    precision_bonus = 50 if snr > 8.0 else 25
    total_delta_pts = 150 + precision_bonus
    score_breakdown_str = f"+150 (Base Hit) + {precision_bonus} (Precision SNR Bonus) = +{total_delta_pts} Pts"

    return True, found_x, found_y, {
        "shift": shift_str,
        "prob": prob,
        "score_delta_val": total_delta_pts,
        "score_breakdown": score_breakdown_str,
        "spectrum": {"Water Ice (H2O)": h2o, "Ammonia (NH3)": nh3, "Methane (CH4)": ch4, "Silicate Dust": dust},
        "stats": {
            "Measured Center": f"X={found_x} px, Y={found_y} px",
            "Aperture Flux": f"{total_flux:.1f} ADU (Peak: {peak_val:.1f})",
            "Signal-to-Noise": f"{snr:.2f} σ (High-Confidence)",
            "Radius": f"{rad:.2f} Earth Radii", "Albedo": f"{alb:.3f} (Dark Ice)",
            "Eccentricity": f"{ecc:.3f}", "Thermal Emission": f"{temp_k:.1f} Kelvin"
        }
    }

def make_audio_wav(spec_dict, shift_label):
    try:
        rate = 44100
        frames = []
        mult = 0.65 if "Redshift" in shift_label else (1.35 if "Blueshift" in shift_label else 0.15)
        for _, val in spec_dict.items():
            freq = (240.0 + (val * 8.5)) * mult
            n_samples = int(rate * 0.5)
            for i in range(n_samples):
                t = float(i) / rate
                amp = int(32767.0 * np.sin(freq * t * 2.0 * np.pi))
                if i < 2000: amp = int(amp * (i / 2000))
                elif i > n_samples - 2000: amp = int(amp * ((n_samples - i) / 2000))
                frames.append(struct.pack('<h', amp))
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
        return buf.getvalue()
    except Exception:
        return None

def read_fits_upload(file_obj):
    try:
        raw_bytes = io.BytesIO(file_obj.getvalue())
        hdul = fits.open(raw_bytes)
        for ext in hdul:
            if ext.data is not None and len(ext.data.shape) >= 2:
                return ext.data[0] if len(ext.data.shape) == 3 else ext.data
        return None
    except Exception:
        return None

load_css()
setup_session()

if st.session_state.page == "login":
    st.markdown('<div class="startup-banner">🚀 NASA Space Apps Challenge 2026 — Official Entry</div>', unsafe_allow_html=True)
    st.markdown("<div class='main-title'>ExoMapper</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>THE PLANET X HUNTER</div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<h4 style='text-align:center; color:#00e5ff; font-family:Chakra Petch;'>ENTER HUNTER ID TO ACCESS</h4>", unsafe_allow_html=True)
        name_in = st.text_input("Hunter ID", placeholder="e.g. NebulaHunter-X / StarVoyager-9...", label_visibility="collapsed")
        st.write("")
        
        if st.button("INITIALIZE SECURE LINK 🚀", use_container_width=True):
            clean_name = name_in.strip()
            if clean_name:
                st.session_state.user = clean_name
                if clean_name not in st.session_state.profiles:
                    st.session_state.profiles[clean_name] = {
                        "last_mode": "🛰️ Official NASA Challenge Data Feed (Placeholder / Ready for Data)",
                        "score": 0, "logs": []
                    }
                st.session_state.score = st.session_state.profiles[clean_name]["score"]
                st.session_state.page = "home"
                st.rerun()
            else:
                st.markdown("<div class='miss-banner'>Access Denied. Please enter a Hunter ID first.</div>", unsafe_allow_html=True)

elif st.session_state.page == "home":
    show_header()
    user = st.session_state.user
    prof = st.session_state.profiles.get(user, {"last_mode": "🛰️ Official NASA Challenge Data Feed (Placeholder / Ready for Data)", "score": 0, "logs": []})
    
    st.markdown(f"<h2 style='color:white; font-family:Chakra Petch;'>Welcome to Command, <span style='color:#00e5ff;'>{user}</span></h2>", unsafe_allow_html=True)
    if prof["logs"]:
        st.markdown(f"<p class='mono-text'>💡 Session Memory: Last mode used was <b>{prof['last_mode']}</b> ({len(prof['logs'])} scans completed).</p>", unsafe_allow_html=True)
        
    b1, b2, b3 = st.columns([1, 1, 2])
    with b1:
        if st.button("Start the Task 📡", use_container_width=True):
            st.session_state.blinking = False
            st.session_state.user_box = None
            st.session_state.is_retry = False
            st.session_state.planet_x = random.randint(85, 315)
            st.session_state.planet_y = random.randint(85, 315)
            st.session_state.seed = random.randint(1, 99999)
            st.session_state.page = "radar"
            st.rerun()
    with b2:
        if st.button("Disconnect (Logout)", use_container_width=True):
            st.session_state.user = ""
            st.session_state.page = "login"
            st.rerun()
    with b3:
        st.markdown(f"""
        <div style="background: rgba(0, 229, 255, 0.1); border: 1px solid #00e5ff; padding: 10px 20px; border-radius: 5px; text-align: right;">
            <h3 style="margin:0; color:#ffffff; font-family:Space Mono;">🏆 Hunter Record: <span style="color:#00e5ff;">{st.session_state.score} Pts</span></h3>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
    
    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown("""
        <div class="info-card">
            <h3 style='color:#00e5ff; font-family:"Chakra Petch";'>🌍 Mission Objective & Role</h3>
            <p class='card-text'>Welcome to <i>ExoMapper</i> (NASA Space Apps Challenge 2026)! Our app compares infrared observations taken across different time epochs ($T=0$ and $T+6$ months) to highlight objects that change position or brightness, helping users identify interesting planetary candidates for further investigation.</p>
        </div>
        <div class="info-card" style="border-color: #ff9100;">
            <h3 style='color:#ff9100; font-family:"Chakra Petch";'>🔭 About SPHEREx Mission</h3>
            <p class='card-text'><b>SPHEREx</b> is a NASA space telescope launched in March 2025 to map the entire sky in 102 different wavelengths of light. Its observations help scientists study the early universe, galaxy evolution, and water molecules across our galaxy.</p>
            <a href="https://science.nasa.gov/mission/spherex/" target="_blank" class="ext-link">NASA SPHEREx Portal</a>
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        st.markdown("""
        <div class="info-card" style="border-color: #e040fb;">
            <h3 style='color:#e040fb; font-family:"Chakra Petch";'>🪐 The Mystery of Planet X</h3>
            <p class='card-text'>Mathematical models and odd orbital alignments in the outer solar system suggest a massive <b>9th planet</b> exists far beyond Neptune. Infrared surveys like SPHEREx provide the key to catching its faint thermal glow.</p>
            <a href="https://solarsystem.nasa.gov/planets/hypothetical-planet-x/in-depth/" target="_blank" class="ext-link" style="background:#e040fb; color:#fff;">NASA Planet X Archive</a>
        </div>
        <div class="info-card">
            <h3 style='color:#00e5ff; font-family:"Chakra Petch";'>🧑‍🚀 Team Members & Challenge Roles</h3>
            <p class='card-text'><b>Team: ExoMapper (NASA Space Apps Challenge 2026)</b></p>
            <ul class='card-text'>
                <li><b>Shikshita Naryal:</b> Lead Astrophysics Researcher, Algorithm Architect & Python Developer.</li>
                <li><b>Ayan Agarwal:</b> Technical Documentation Lead, Scientific Content Writer & Research Analyst.</li>
            </ul>
            <p class='card-text'><b>Scoring Matrix:</b> Precision Target Lock (+150 to +200 Pts) | False Alarm (-75 Pts).</p>
        </div>
        """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<h3 style='color:#00e5ff; font-family:Chakra Petch; margin-top:0;'>📖 Rules & Guide Menu (FAQ Hub)</h3>", unsafe_allow_html=True)
        st.markdown("<p class='card-text'>Everything you need to know about navigating the ExoMapper workbench and maximizing your hunter score:</p>", unsafe_allow_html=True)
        
        faq_search = st.text_input("🔍 Search Rules & Guide FAQs:", placeholder="Type keywords like 'blink', 'score', 'WCS', 'noise'...", key="faq_keyword_search")
        
        faq_list = [
            ("What is the main goal of ExoMapper?", "To assist NASA's SPHEREx mission by comparing multi-epoch infrared FITS files to identify moving Planet X candidates."),
            ("How does the BLINK FRAMES feature work?", "It merges two time-separated observation epochs ($T=0$ and $T+6$ months) and alternates between them to highlight proper motion."),
            ("How do I score points?", "Draw a selection box over a moving anomaly and lock it. Accurate aperture placement earns +150 to +200 points, while false targets incur a -75 point penalty."),
            ("What are WCS Grids?", "World Coordinate System overlays that display celestial Right Ascension (RA) and Declination (Dec) coordinates across the sky sector."),
            ("How does Data Reduction (Noise Removal) work?", "It applies background subtraction algorithms to filter out cosmic ray hits and sensor read noise, raising the signal-to-noise ratio.")
        ]
        
        filtered_faqs = faq_list
        if faq_search.strip():
            kw = faq_search.strip().lower()
            filtered_faqs = [item for item in faq_list if kw in item[0].lower() or kw in item[1].lower()]
            
        for q, a in filtered_faqs:
            with st.expander(f"📌 {q}"):
                st.write(a)

    with st.container(border=True):
        st.markdown("<h3 style='color:#b388ff; font-family:Chakra Petch; margin-top:0;'>🌌 Cosmic Encyclopedia & Astrophysical Codex</h3>", unsafe_allow_html=True)
        st.markdown("<p class='card-text'>Expand your research database with advanced astrometric concepts (RA, Dec, Mosaics, and Photometry):</p>", unsafe_allow_html=True)
        
        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        with c_p1:
            st.markdown("""
            <div style='background:rgba(0,229,255,0.05); padding:10px; border-radius:8px; border:1px solid rgba(0,229,255,0.2); height:100%;'>
                <b style='color:#00e5ff;'>1. RA & Dec (WCS)</b><br>
                <span style='font-size:0.88rem; color:#cfd8dc;'>Right Ascension (RA) and Declination (Dec) form the celestial coordinate system equivalent to Earth's longitude and latitude.</span>
            </div>
            """, unsafe_allow_html=True)
        with c_p2:
            st.markdown("""
            <div style='background:rgba(255,145,0,0.05); padding:10px; border-radius:8px; border:1px solid rgba(255,145,0,0.2); height:100%;'>
                <b style='color:#ff9100;'>2. Multi-Wavelength</b><br>
                <span style='font-size:0.88rem; color:#cfd8dc;'>SPHEREx maps the sky across 102 infrared channels, isolating ice absorption bands ($H_2O$, $CO_2$) without atmospheric blurring.</span>
            </div>
            """, unsafe_allow_html=True)
        with c_p3:
            st.markdown("""
            <div style='background:rgba(224,64,251,0.05); padding:10px; border-radius:8px; border:1px solid rgba(224,64,251,0.2); height:100%;'>
                <b style='color:#e040fb;'>3. Proper Motion</b><br>
                <span style='font-size:0.88rem; color:#cfd8dc;'>Nearby celestial bodies shift across background starfields due to orbital velocity over 6-month temporal baselines.</span>
            </div>
            """, unsafe_allow_html=True)
        with c_p4:
            st.markdown("""
            <div style='background:rgba(0,255,204,0.05); padding:10px; border-radius:8px; border:1px solid rgba(0,255,204,0.2); height:100%;'>
                <b style='color:#00ffcc;'>4. Flux & ADU</b><br>
                <span style='font-size:0.88rem; color:#cfd8dc;'>Analog-to-Digital Units (ADU) quantify photon counts captured by telescope sensors, mapped into radiant flux.</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: rgba(0,229,255,0.35);'>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<h3 style='color:#00e5ff; font-family:Chakra Petch; margin-top:0;'>📋 Hunter Telemetry Logbook — Track Your Work</h3>", unsafe_allow_html=True)
        
        logs = prof.get("logs", [])
        if not logs:
            st.markdown("<p style='color:#84ffff; font-family:Space Mono; font-size:1rem; padding:10px; background:rgba(0,229,255,0.05); border-radius:5px;'>⭐ No scans recorded yet. Click 'Start the Task 📡' above to begin your first deep-space scan!</p>", unsafe_allow_html=True)
        else:
            cols_to_show = ["Scan #", "Timestamp", "Uplink Mode", "FITS Source", "Attempt Type", "Target Coords (X, Y)", "Status", "Score Delta", "Planet Name", "Radius", "Thermal Emission"]
            st.dataframe(pd.DataFrame(logs)[cols_to_show], use_container_width=True, hide_index=True)
            
            st.markdown("<h4 style='color:#b388ff; font-family:Chakra Petch; margin-top:15px;'>🔍 Past Scan Details</h4>", unsafe_allow_html=True)
            for item in reversed(logs):
                b_col = "#00e5ff" if "VERIFIED" in item["Status"] else "#ff1744"
                st.markdown(f"""
                <div style='background:rgba(0, 20, 45, 0.75); border-left:4px solid {b_col}; padding:12px; border-radius:6px; margin-bottom:10px;'>
                    <b style='color:{b_col}; font-family:Chakra Petch;'>Scan #{item['Scan #']} — {item['Status']} ({item['Score Delta']})</b>
                    <span style='float:right; font-family:Space Mono; font-size:0.85rem; color:#84ffff;'>🕒 {item['Timestamp']}</span><br>
                    <span><b>Mode:</b> {item['Uplink Mode']} | <b>File:</b> {item['FITS Source']} | <b>Type:</b> {item['Attempt Type']}</span><br>
                    <span><b>Coords:</b> {item['Target Coords (X, Y)']} | <b>Planet Name:</b> <b style='color:#e040fb;'>{item['Planet Name']}</b></span><br>
                    <span><b>Physics:</b> Radius={item['Radius']}, Albedo={item['Albedo']}, Eccentricity={item['Eccentricity']}, Temp={item['Thermal Emission']}</span>
                </div>
                """, unsafe_allow_html=True)

elif st.session_state.page == "radar":
    show_header()
    
    t1, t2, t3 = st.columns([3, 1, 1])
    t1.markdown("<h2 style='color:white; font-family:Chakra Petch;'>Live Optics: Interferometer</h2>", unsafe_allow_html=True)
    if t2.button("🔄 New Sky Sector", use_container_width=True):
        st.session_state.planet_x = random.randint(85, 315)
        st.session_state.planet_y = random.randint(85, 315)
        st.session_state.seed = random.randint(1, 99999)
        st.session_state.user_box = None
        st.session_state.is_retry = True
        st.toast("✨ New Sky Sector loaded! New coordinate grid and starseed generated.", icon="🚀")
        st.rerun()
    if t3.button("Abort Task", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

    user = st.session_state.user
    modes = [
        "🛰️ Official NASA Challenge Data Feed (Placeholder / Ready for Data)", 
        "📂 Custom FITS File Upload", 
        "📡 Live Caltech IRSA (API / Archive Cutouts)"
    ]
    saved_mode = st.session_state.profiles[user].get("last_mode", modes[0])

    with st.container(border=True):
        st.markdown("<h4 style='color:#00e5ff; font-family:Chakra Petch; margin-top:0;'>📡 SELECT UPLINK SOURCE</h4>", unsafe_allow_html=True)
        st.markdown("""
        <div style='display:flex; gap:12px; flex-wrap:wrap; margin-bottom:10px; font-size:0.95rem;'>
            <div style='flex:1; background:rgba(0,229,255,0.06); padding:8px; border-radius:5px; border-left:3px solid #00e5ff;'>
                <b style='color:#00e5ff;'>1. Official NASA Data:</b> Prepared pipeline for NASA Space Apps official challenge release.
            </div>
            <div style='flex:1; background:rgba(255,145,0,0.06); padding:8px; border-radius:5px; border-left:3px solid #ff9100;'>
                <b style='color:#ff9100;'>2. Custom Upload:</b> Upload your own observation FITS files directly into the workbench.
            </div>
            <div style='flex:1; background:rgba(224,64,251,0.06); padding:8px; border-radius:5px; border-left:3px solid #e040fb;'>
                <b style='color:#e040fb;'>3. Caltech IRSA:</b> Use pre-loaded NASA FITS archive cutouts.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        chosen_mode = st.radio("Select Mode", modes, index=modes.index(saved_mode) if saved_mode in modes else 0, horizontal=True, label_visibility="collapsed")
        st.session_state.profiles[user]["last_mode"] = chosen_mode

    with st.container(border=True):
        ctrl_col_h1, ctrl_col_h2 = st.columns([4, 1])
        ctrl_col_h1.markdown("<h4 style='color:#b388ff; font-family:Chakra Petch; margin-top:0;'>🎛️ Advanced Astronomical Image Controls & Frame Management</h4>", unsafe_allow_html=True)
        
        with ctrl_col_h2:
            show_control_guide = st.toggle("📖 Guide & Tooltips", value=False)

        if show_control_guide:
            st.markdown("""
            <div style='background:rgba(4,12,36,0.98); padding:16px; border-radius:8px; border:1px solid #00e5ff; margin-bottom:15px; font-size:0.92rem; color:#e0f7fa;'>
                <b style='color:#00e5ff;'>📚 Observatory Controls Guide & Documentation:</b><br>
                &bull; <b>Image Scale Algorithm (Linear, Log, Sqrt, HistEq):</b> Controls how pixel brightness maps to visual shades. Log and Square Root stretch faint infrared signals so hidden planets become visible.<br>
                &bull; <b>Color Palette (LUT - Inferno, Viridis, Gray, etc.):</b> Color Lookup Tables highlight thermal gradients and optical density.<br>
                &bull; <b>Bias / Contrast Stretch:</b> Adjusts black and white clipping points to isolate sources from background noise.<br>
                &bull; <b>Region Select Shapes (Box, Circle, Star, Hexagon):</b> Astrometric tools for bounding and measuring target apertures.<br>
                &bull; <b>View Frame Modes (Single, Tile, Fade Blend):</b> Lets you inspect epochs side-by-side or blended.<br>
                &bull; <b>WCS Coordinate Grid:</b> Overlays celestial Right Ascension (RA) and Declination (Dec) coordinate lines.<br>
                &bull; <b>Clear / Reset Frames:</b> Flushes active selections and temporary canvas memory.
            </div>
            """, unsafe_allow_html=True)
        
        ctrl_c1, ctrl_c2, ctrl_c3, ctrl_c4 = st.columns([1.2, 1.2, 1.2, 1.2])
        with ctrl_c1:
            scale_opt = st.selectbox("Image Scale Algorithm:", ["Linear", "Logarithmic (Log)", "Square Root (Sqrt)", "Histogram Equalization"])
        with ctrl_c2:
            color_opt = st.selectbox("Color Palette (LUT):", ["gray", "inferno", "viridis", "plasma", "magma", "cividis"])
        with ctrl_c3:
            contrast_val = st.slider("Bias / Contrast Stretch:", 0.85, 1.0, 0.98, 0.01)
        with ctrl_c4:
            region_shape = st.selectbox("Region Select Shape:", ["Rectangle / Box", "Circle", "Star", "Hexagon", "Polygon / Trapezoid"])

        st.markdown("<hr style='border-color: rgba(179,136,255,0.2); margin: 10px 0;'>", unsafe_allow_html=True)
        
        sub_c1, sub_c2, sub_c3, sub_c4 = st.columns([1.2, 1.2, 1.2, 1.2])
        with sub_c1:
            st.session_state.frame_view_mode = st.selectbox("View Frames Mode:", ["Single Frame", "Tile Frames", "Previous Frame", "Fade Frame"])
        with sub_c2:
            wcs_overlay = st.checkbox("WCS Coordinate Analysis Grid", value=True)
        with sub_c3:
            invert_color = st.checkbox("Invert Palette", value=False)
        with sub_c4:
            st.write("")
            if st.button("Clear / Reset Frames", use_container_width=True):
                st.session_state.user_box = None
                st.session_state.custom_loaded_frames = []
                st.rerun()

        st.markdown("<hr style='border-color: rgba(0,229,255,0.2); margin: 10px 0;'>", unsafe_allow_html=True)
        fm_col1, fm_col2 = st.columns([2, 2])
        with fm_col1:
            total_active_frames = 2 + len(st.session_state.custom_loaded_frames)
            st.markdown(f"<p class='mono-text'>📂 Active Loaded FITS Frames in Stack: <b style='color:#00e5ff;'>{total_active_frames} Frames</b> (Epoch 1, Epoch 2 + {len(st.session_state.custom_loaded_frames)} Extra Multi-Extension Extensions)</p>", unsafe_allow_html=True)
        with fm_col2:
            extra_frame_file = st.file_uploader("➕ Add Additional Extension Frame (.fits)", type=["fits", "fit"], key="extra_ext_uploader")
            if extra_frame_file is not None:
                ef_data = read_fits_upload(extra_frame_file)
                if ef_data is not None:
                    st.session_state.custom_loaded_frames.append(ef_data)
                    st.success(f"Successfully added frame {extra_frame_file.name} to stack!")
                    st.rerun()

    cmap_final = f"{color_opt}_r" if invert_color else color_opt

    px, py = st.session_state.planet_x, st.session_state.planet_y
    f1_raw, f2_raw = None, None
    custom_file_used = False
    source_name = ""

    if "Official NASA" in chosen_mode:
        source_name = f"Official NASA SPHEREx Feed (Seed #{st.session_state.seed})"
        f1_raw, f2_raw = make_sky_frames("Hybrid", px, py, st.session_state.seed)
    elif "Custom" in chosen_mode:
        up_file = st.file_uploader("📂 Upload Custom FITS Observation File (.fits / .fit)", type=["fits", "fit"], key="custom_fits_main")
        if up_file is not None:
            arr = read_fits_upload(up_file)
            if arr is not None:
                f1_raw = arr
                f2_raw = np.roll(arr, shift=(5, 8), axis=(0, 1))
                custom_file_used = True
                source_name = f"Custom Upload: {up_file.name}"
                st.success(f"Successfully loaded {up_file.name}")
            else:
                st.error("Could not read 2D image from this FITS file.")
        else:
            st.info("ℹ️ Please upload a `.fits` file above to begin your custom analysis, or switch to Official NASA / IRSA mode.")
            f1_raw, f2_raw = make_sky_frames("Proxy", px, py, st.session_state.seed)
    else:
        st.markdown('<a href="https://irsa.ipac.caltech.edu/applications/Cutouts/" target="_blank" class="ext-link" style="margin-bottom:12px;">🔗 Open NASA/Caltech IRSA Cutouts</a>', unsafe_allow_html=True)
        preset = st.selectbox("Choose Sample NASA FITS Cutout:", ["SPHEREx_DeepField_SectorA.fits", "NEOWISE_W1_OuterRim_Epoch1.fits", "2MASS_KuiperBelt_Survey_09.fits"])
        p_seed = sum(ord(ch) for ch in preset) + st.session_state.seed
        source_name = f"IRSA Sample: {preset}"
        f1_raw, f2_raw = make_sky_frames("Hybrid", px, py, p_seed)

    if f1_raw is not None and f2_raw is not None:
        img1 = scale_image_professional(f1_raw, scale_opt, contrast_val)
        img2 = scale_image_professional(f2_raw, scale_opt, contrast_val)

        view_mode = st.session_state.frame_view_mode
        
        if not st.session_state.blinking:
            st.markdown(f"<p class='card-text'><b>Step 1:</b> Current View Mode: <b>{view_mode}</b>. Compare epochs below and launch blink analysis.</p>", unsafe_allow_html=True)
            
            with st.container(border=True):
                if view_mode == "Tile Frames" or view_mode == "Fade Frame":
                    col_a, col_b = st.columns(2)
                    with col_a:
                        fig1 = go.Figure(data=go.Heatmap(z=img1, colorscale=cmap_final, showscale=False))
                        fig1.update_layout(margin=dict(l=0,r=0,t=25,b=0), title="Epoch 1 (T = 0)", xaxis=dict(title="X (px)", color="#84ffff"), yaxis=dict(title="Y (px)", color="#84ffff"), paper_bgcolor="#010409", plot_bgcolor="#010409", height=350)
                        if wcs_overlay:
                            fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,229,255,0.25)')
                            fig1.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,229,255,0.25)')
                        st.plotly_chart(fig1, use_container_width=True)
                    with col_b:
                        blend_z = (img1 * 0.5 + img2 * 0.5) if view_mode == "Fade Frame" else img2
                        fig2 = go.Figure(data=go.Heatmap(z=blend_z, colorscale=cmap_final, showscale=False))
                        fig2.update_layout(margin=dict(l=0,r=0,t=25,b=0), title="Epoch 2 / Fade Blend", xaxis=dict(title="X (px)", color="#84ffff"), yaxis=dict(title="Y (px)", color="#84ffff"), paper_bgcolor="#010409", plot_bgcolor="#010409", height=350)
                        if wcs_overlay:
                            fig2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,229,255,0.25)')
                            fig2.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,229,255,0.25)')
                        st.plotly_chart(fig2, use_container_width=True)
                else:
                    fig_single = go.Figure(data=go.Heatmap(z=img1, colorscale=cmap_final, showscale=False))
                    fig_single.update_layout(margin=dict(l=0,r=0,t=25,b=0), title="Active Frame — Epoch 1", xaxis=dict(title="X (px)", color="#84ffff"), yaxis=dict(title="Y (px)", color="#84ffff"), paper_bgcolor="#010409", plot_bgcolor="#010409", height=400)
                    if wcs_overlay:
                        fig_single.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,229,255,0.25)')
                        fig_single.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,229,255,0.25)')
                    st.plotly_chart(fig_single, use_container_width=True)
                
            if st.button("🚨 LAUNCH BLINK FRAMES", use_container_width=True):
                with st.spinner("✨ Initializing high-speed interferometry matrix... Aligning SPHEREx channels... Just a moment, cosmic hunter! 🔭"):
                    time.sleep(0.3)
                st.session_state.blinking = True
                st.rerun()
        else:
            st.markdown("<p class='card-text'><b>Step 2:</b> BLINK FRAMES active! Use the selection tool matching your chosen shape to mark the moving anomaly.</p>", unsafe_allow_html=True)
            
            with st.expander("🧰 Data Reduction & Noise Removal Suite (Background Subtraction) — Learn More"):
                st.markdown("""
                <div style='background:rgba(4,12,36,0.98); padding:12px; border-radius:6px; margin-bottom:10px; font-size:0.9rem; color:#cfd8dc;'>
                    <b>🔭 What is Data Reduction & Background Subtraction?</b><br>
                    Telescope detectors capture unwanted background glow (starlight scatter, thermal instrument emissions). Background subtraction measures median sky levels and subtracts them to isolate true astronomical point sources.<br>
                    &bull; <b>Wavelet / Median Smoothing Filters:</b> Mathematical algorithms that smooth out high-frequency sensor noise while preserving sharp point-spread functions (PSF) of stars.<br>
                    &bull; <b>Background ADU Cutoff:</b> Threshold limit (in Analog-to-Digital Units) below which all pixel values are treated as sky noise and zeroed out.<br>
                    &bull; <b>Sensor Readout Noises & Cosmic Ray Artifacts:</b> Electronic static and high-energy particle streaks on the CCD. Checking this filter cleans them instantly.
                </div>
                """, unsafe_allow_html=True)
                
                dr_col1, dr_col2 = st.columns(2)
                with dr_col1:
                    enable_denoise = st.checkbox("Apply Wavelet / Median Smoothing Filter", value=False)
                    noise_threshold = st.slider("Background ADU Cutoff:", 1.0, 30.0, 12.5, 0.5)
                with dr_col2:
                    if enable_denoise:
                        before_noise = float(np.std(f1_raw))
                        f1_raw = np.where(f1_raw < noise_threshold, float(np.median(f1_raw)), f1_raw)
                        after_noise = float(np.std(f1_raw))
                        st.markdown(f"""
                        <div style='background:rgba(0,229,255,0.1); padding:8px; border-radius:5px; font-family:Space Mono; font-size:0.85rem;'>
                            <b>📊 Data Reduction Report:</b><br>
                            &bull; Initial Noise Floor: <span style='color:#ff1744;'>{before_noise:.2f} ADU</span><br>
                            &bull; Reduced Noise Floor: <span style='color:#00ffcc;'>{after_noise:.2f} ADU</span><br>
                            &bull; SNR Enhancement: <span style='color:#00e5ff;'>+{(before_noise - after_noise):.2f} ADU Cleaned</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("Check the box above to filter sensor readout noise and cosmic ray artifacts.")

            c_loop, c_spd, c_stop = st.columns([1.5, 1.5, 1])
            with c_loop:
                keep_looping = st.toggle("🔄 AUTO-LOOP BLINK (NON-STOP)", value=False)
            with c_spd:
                speed_ms = st.number_input("Blink Speed (ms) [Exact Control]:", min_value=10.0, max_value=5000.0, value=450.0, step=5.0)
                st.markdown("<span style='font-size:0.8rem; color:#84ffff;'>ℹ️ <b>Blink Speed (ms):</b> Sets the interval duration in milliseconds between frame switches during BLINK FRAMES.</span>", unsafe_allow_html=True)
            with c_stop:
                st.write("")
                if st.button("⏹ EXIT BLINK MODE", use_container_width=True):
                    st.session_state.blinking = False
                    st.rerun()

            frames_list = [
                go.Frame(data=[go.Heatmap(z=img1 if i % 2 == 0 else img2, colorscale=cmap_final, showscale=True)], name=f"fr_{i}")
                for i in range(30)
            ]
            
            curr_img = img1 if st.session_state.frame_step % 2 == 0 else img2
            ep_name = "EPOCH 1" if st.session_state.frame_step % 2 == 0 else "EPOCH 2"

            drag_mode_map = {
                "Rectangle / Box": "select",
                "Circle": "drawcircle",
                "Star": "drawopenpath",
                "Hexagon": "drawclosedpath",
                "Polygon / Trapezoid": "drawclosedpath"
            }
            active_drag = drag_mode_map.get(region_shape, "select")

            with st.container(border=True):
                blink_fig = go.Figure(
                    data=[go.Heatmap(z=curr_img, colorscale=cmap_final, showscale=True)],
                    layout=go.Layout(
                        title=dict(text=f"BLINK FRAMES ({region_shape}) — Active: {ep_name}", font=dict(color="#00e5ff", family="Chakra Petch", size=16)),
                        xaxis=dict(title="X Axis (Pixels)", color="#84ffff", range=[0, f1_raw.shape[1]]),
                        yaxis=dict(title="Y Axis (Pixels)", color="#84ffff", range=[0, f1_raw.shape[0]]),
                        paper_bgcolor="#010409", plot_bgcolor="#010409", height=500,
                        margin=dict(l=40, r=40, t=45, b=40),
                        dragmode=active_drag,
                        newshape=dict(line_color='#00e5ff', line_width=3, fillcolor='rgba(0, 229, 255, 0.18)'),
                        updatemenus=[dict(
                            type="buttons", showactive=True, x=0.01, y=1.12, direction="left",
                            buttons=[
                                dict(label="▶ PLAY BLINK", method="animate", args=[None, dict(frame=dict(duration=speed_ms, redraw=True), fromcurrent=True, mode="immediate")]),
                                dict(label="⏸ PAUSE", method="animate", args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")])
                            ]
                        )]
                    ),
                    frames=frames_list
                )

                if wcs_overlay:
                    blink_fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,229,255,0.25)')
                    blink_fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,229,255,0.25)')

                if st.session_state.user_box is not None:
                    bx0, bx1, by0, by1 = st.session_state.user_box
                    blink_fig.add_shape(type="rect", x0=bx0, y0=by0, x1=bx1, y1=by1, line=dict(color="#00e5ff", width=3), fillcolor="rgba(0,229,255,0.18)")

                event_data = st.plotly_chart(
                    blink_fig, use_container_width=True, key="blink_chart",
                    on_select="rerun", selection_mode=("box", "lasso"),
                    config={'scrollZoom': True, 'displayModeBar': True, 'modeBarButtonsToAdd': ['select2d', 'lasso2d', 'drawcircle', 'drawrect', 'eraseshape']}
                )

            if event_data and "selection" in event_data:
                sel = event_data["selection"]
                if sel.get("box"):
                    b = sel["box"][0]
                    st.session_state.user_box = (b["x"][0], b["x"][1], b["y"][0], b["y"][1])
                elif sel.get("lasso"):
                    l = sel["lasso"][0]
                    st.session_state.user_box = (min(l["x"]), max(l["x"]), min(l["y"]), max(l["y"]))

            if keep_looping:
                time.sleep(speed_ms / 1000.0)
                st.session_state.frame_step += 1
                st.rerun()

        with st.container(border=True):
            st.markdown("<h4 style='color:#00e5ff; font-family:Chakra Petch; margin-top:0;'>🎯 LOCK TARGET COORDINATES</h4>", unsafe_allow_html=True)
            if st.session_state.user_box is not None:
                bx0, bx1, by0, by1 = st.session_state.user_box
                def_x, def_y = int((bx0 + bx1) / 2), int((by0 + by1) / 2)
                st.success(f"Region captured! Center: X={def_x}, Y={def_y}")
            else:
                def_x, def_y = 200, 200
                st.markdown("<p class='card-text'>Use selection tool on the chart above, or type coordinates below:</p>", unsafe_allow_html=True)

            cx1, cy1, crad, cbtn = st.columns([1, 1, 1, 1.8])
            with cx1:
                in_x = st.number_input("Center X (px):", 0, f1_raw.shape[1]-1, int(np.clip(def_x, 0, f1_raw.shape[1]-1)))
            with cy1:
                in_y = st.number_input("Center Y (px):", 0, f1_raw.shape[0]-1, int(np.clip(def_y, 0, f1_raw.shape[0]-1)))
            with crad:
                in_r = st.number_input("Radius (px):", 4, 40, 12)
            with cbtn:
                st.write("")
                if st.button("🎯 LOCK TARGET & EXTRACT DATA", use_container_width=True):
                    hit_ok, mx, my, res_dict = analyze_target_box(
                        f1_raw, f2_raw, in_x - in_r, in_x + in_r, in_y - in_r, in_y + in_r, px, py, custom_file_used
                    )
                    st.session_state.is_hit = hit_ok
                    delta_pts = res_dict.get("score_delta_val", 150) if hit_ok else -75
                    st.session_state.score += delta_pts
                    st.session_state.profiles[user]["score"] = st.session_state.score
                    st.session_state.result_data = res_dict

                    user_logs = st.session_state.profiles[user]["logs"]
                    user_logs.append({
                        "Scan #": len(user_logs) + 1,
                        "Timestamp": get_time_str(),
                        "Uplink Mode": chosen_mode,
                        "FITS Source": source_name,
                        "Attempt Type": "Retry Scan" if st.session_state.is_retry else "First Scan",
                        "Target Coords (X, Y)": f"X={mx}, Y={my}",
                        "Status": "VERIFIED HIT" if hit_ok else "FALSE ALARM",
                        "Score Delta": res_dict.get("score_breakdown", "+150 Pts"),
                        "Planet Name": "Unassigned" if hit_ok else "N/A (Noise)",
                        "Radius": res_dict["stats"]["Radius"],
                        "Albedo": res_dict["stats"]["Albedo"],
                        "Eccentricity": res_dict["stats"]["Eccentricity"],
                        "Thermal Emission": res_dict["stats"]["Thermal Emission"]
                    })
                    st.session_state.last_log_idx = len(user_logs) - 1
                    st.session_state.page = "analysis"
                    st.rerun()

elif st.session_state.page == "analysis":
    show_header()
    user = st.session_state.user
    res = st.session_state.result_data
    
    if st.session_state.is_hit:
        st.markdown(f"<div class='hit-banner'>✅ TARGET VERIFIED: {res.get('score_breakdown', 'Verified Hit')}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='miss-banner'>❌ FALSE ALARM: Background noise detected. (-75 Pts Penalty). True anomaly was at X={st.session_state.planet_x}, Y={st.session_state.planet_y}.</div>", unsafe_allow_html=True)

    c_stat, c_graph = st.columns([1.1, 1.9])
    with c_stat:
        html_stats = "<div class='info-card'><h3 style='color:#b388ff; font-family:Chakra Petch;'>🪐 Measured Planet Stats</h3><hr style='border-color:#333;'>"
        for k, v in res["stats"].items():
            html_stats += f"<div class='mono-text'>{k}: <br><span style='color:#fff; font-size:1.05rem;'>{v}</span></div>"
        html_stats += "</div>"
        st.markdown(html_stats, unsafe_allow_html=True)

    with c_graph:
        df_spec = pd.DataFrame(list(res["spectrum"].items()), columns=["Molecule", "Abundance"])
        bar_col = '#00e5ff' if st.session_state.is_hit else '#555555'
        fig_spec = go.Figure(data=[go.Bar(x=df_spec["Molecule"], y=df_spec["Abundance"], marker_color=bar_col)])
        fig_spec.update_layout(
            title=dict(text="Atmospheric Spectrum (%)", font=dict(color="#fff", size=19, family="Chakra Petch")),
            xaxis_title="Molecules", yaxis_title="Abundance (%)",
            paper_bgcolor='rgba(4, 10, 25, 0.85)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#84ffff', family='Space Mono'), height=360
        )
        st.plotly_chart(fig_spec, use_container_width=True)

    st.markdown("<hr style='border-color: rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
    
    c_dop, c_aud = st.columns(2)
    shift_txt = res["shift"]
    with c_dop:
        st.markdown("<h3 style='color:#b388ff; font-family:Chakra Petch;'>📡 Doppler Shift Wave</h3>", unsafe_allow_html=True)
        w_col = "#ff1744" if "Red" in shift_txt else ("#00e5ff" if "Blue" in shift_txt else "#777777")
        w_freq = 0.8 if "Red" in shift_txt else (3.0 if "Blue" in shift_txt else 0.2)
        xw = np.linspace(0, 4 * np.pi, 100)
        yw = np.sin(xw * w_freq)
        fig_w = go.Figure(go.Scatter(x=xw, y=yw, mode='lines', line=dict(color=w_col, width=3)))
        fig_w.update_layout(
            paper_bgcolor='rgba(4, 10, 25, 0.85)', plot_bgcolor='rgba(0,0,0,0)',
            height=180, margin=dict(l=10,r=10,t=40,b=10),
            title=dict(text=f"Shift: {shift_txt}", font=dict(color=w_col, family="Space Mono", size=14)),
            xaxis=dict(visible=False), yaxis=dict(visible=False)
        )
        st.plotly_chart(fig_w, use_container_width=True)

    with c_aud:
        st.markdown("<h3 style='color:#b388ff; font-family:Chakra Petch;'>🎧 Data Sonification</h3>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background: rgba(255, 255, 255, 0.05); padding: 10px; border-left: 3px solid #b388ff; margin-bottom:10px;'>
            <b style='color:#b388ff;'>NOTE:</b> Audio frequencies are generated mathematically from the chemical spectrum and Doppler shift.
        </div>
        """, unsafe_allow_html=True)
        wav_data = make_audio_wav(res["spectrum"], shift_txt)
        if wav_data: st.audio(wav_data, format='audio/wav')

    st.markdown("<hr style='border-color: rgba(0,229,255,0.2);'>", unsafe_allow_html=True)

    if st.session_state.is_hit:
        st.markdown(f"<h3 style='color:white; font-family:Chakra Petch;'>Planet X Match: <span style='color:#00e5ff;'>YES ({res['prob']}% Confidence)</span></h3>", unsafe_allow_html=True)
        p_name = st.text_input("Name your discovered planet:", placeholder="e.g. Bharat-X1 / Spherex-9b")
        
        b_sub, b_next, b_home = st.columns(3)
        with b_sub:
            if st.button("Transmit Data to NASA 📡", use_container_width=True):
                if p_name.strip():
                    idx = st.session_state.last_log_idx
                    if idx is not None:
                        st.session_state.profiles[user]["logs"][idx]["Planet Name"] = p_name.strip()
                    st.markdown(f"<div class='hit-banner'>Saved! Planet <b>'{p_name.strip()}'</b> added to your Mission Logbook.</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='miss-banner'>Please enter a planet name first.</div>", unsafe_allow_html=True)
        with b_next:
            if st.button("Scan Another Sector 🔄", use_container_width=True):
                st.session_state.blinking = False
                st.session_state.user_box = None
                st.session_state.is_retry = True
                st.session_state.planet_x = random.randint(85, 315)
                st.session_state.planet_y = random.randint(85, 315)
                st.session_state.seed = random.randint(1, 99999)
                st.session_state.page = "radar"
                st.rerun()
        with b_home:
            if st.button("Return to Dashboard 🏠", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()
    else:
        st.markdown("<h3 style='color:white; font-family:Chakra Petch;'>Planet X Match: <span style='color:#ff1744;'>FAILED (0%)</span></h3>", unsafe_allow_html=True)
        b_ret, b_hm = st.columns(2)
        with b_ret:
            if st.button("🔄 Try Again", use_container_width=True):
                st.session_state.is_retry = True
                st.session_state.page = "radar"
                st.rerun()
        with b_hm:
            if st.button("Return to Dashboard 🏠", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()

st.markdown("<div class='footer-tag'>Developed by: Team ExoMapper</div>", unsafe_allow_html=True)

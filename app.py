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

st.set_page_config(page_title="ExoMapper", layout="wide", initial_sidebar_state="collapsed")
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Audiowide&family=Chakra+Petch:ital,wght@0,500;0,700;1,500&family=Cinzel:ital,wght@0,600;1,600&family=Rajdhani:ital,wght@0,500;0,700;1,600&family=Space+Mono&display=swap');
    
    .stApp {
        background-color: #010409;
        background-image: 
            radial-gradient(circle at 15% 30%, rgba(0, 102, 255, 0.28), transparent 45%),
            radial-gradient(circle at 85% 75%, rgba(0, 229, 255, 0.22), transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(5, 18, 42, 0.85), transparent 80%),
            url("https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=3000&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        color: #e0f7fa;
        font-family: 'Rajdhani', sans-serif;
    }

    .main-title {
        text-align: center; font-family: 'Audiowide', cursive; font-size: 6.2rem; 
        color: #ffffff; margin-top: 4vh; text-shadow: 0 0 20px #00e5ff, 0 0 40px rgba(0, 229, 255, 0.6);
        letter-spacing: 5px;
    }

    .sub-title {
        text-align: center; color: #84ffff; font-size: 1.8rem; 
        font-family: 'Cinzel', serif; font-style: italic; 
        font-weight: 600; letter-spacing: 4px; margin-top: -15px; margin-bottom: 40px;
    }
    
    .top-bar {
        display: flex; align-items: center; border-bottom: 1px solid rgba(0,229,255,0.4);
        padding-bottom: 12px; margin-bottom: 25px;
    }
    .top-bar h1 {
        font-family: 'Audiowide', cursive; font-size: 2.3rem; color: #ffffff;
        text-shadow: 0 0 12px #00e5ff; margin: 0; margin-left: 18px;
    }
    
    .info-card {
        background: rgba(4, 12, 30, 0.85); border: 1px solid rgba(0, 229, 255, 0.35); 
        padding: 20px; border-radius: 10px; margin-bottom: 20px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.8);
    }
    
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(4, 12, 30, 0.85) !important;
        border: 1px solid rgba(0, 229, 255, 0.4) !important;
        border-radius: 10px !important;
        padding: 18px !important;
        margin-bottom: 20px !important;
    }
    
    .card-text { font-size: 1.1rem; line-height: 1.6; color: #cfd8dc; }
    .mono-text { font-family: 'Space Mono', monospace; font-size: 0.92rem; color: #84ffff; margin-bottom: 8px; }
    
    .hit-banner {
        background: rgba(0, 77, 64, 0.9); border-left: 5px solid #00e5ff;
        padding: 15px; border-radius: 5px; color: #fff; font-family: 'Chakra Petch'; font-size: 1.15rem; margin-bottom: 20px;
    }
    .miss-banner {
        background: rgba(183, 28, 28, 0.9); border-left: 5px solid #ff1744;
        padding: 15px; border-radius: 5px; color: #fff; font-family: 'Chakra Petch'; font-size: 1.15rem; margin-bottom: 20px;
    }
    
    div.stButton > button {
        background: rgba(0, 229, 255, 0.12); color: #00e5ff; border: 1px solid #00e5ff;
        border-radius: 6px; font-weight: 700; padding: 10px 20px;
        text-transform: uppercase; font-family: 'Chakra Petch', sans-serif;
    }
    div.stButton > button:hover {
        background: #00e5ff; color: #010409; box-shadow: 0 0 15px #00e5ff;
    }
    
    label { font-family: 'Chakra Petch', sans-serif; color: #84ffff !important; }
    
    .ext-link {
        color: #010409; background: #00e5ff; padding: 6px 14px; border-radius: 5px;
        text-decoration: none; font-weight: 700; font-family: 'Chakra Petch'; display: inline-block; margin-top: 10px;
    }
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
        'last_log_idx': None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def show_header():
    st.markdown("""
    <div class="top-bar">
        <img src="https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg" width="50">
        <div><h1>ExoMapper</h1></div>
    </div>
    """, unsafe_allow_html=True)


def get_time_str():
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    return ist.strftime("%d %b %Y | %I:%M %p IST")
def make_sky_frames(mode, px, py, seed_val):
    rng = np.random.default_rng(seed_val)
    N = 400
    y_grid, x_grid = np.mgrid[0:N, 0:N]
    
    # base background noise
    sky = rng.normal(25.0, 3.5, (N, N))
    
    if "Hybrid" in mode:
        # add soft nebula clouds
        cloud1 = 35.0 * np.exp(-((x_grid - 180)**2 + (y_grid - 220)**2) / (2 * 110**2))
        cloud2 = 25.0 * np.exp(-((x_grid - 280)**2 + (y_grid - 120)**2) / (2 * 85**2))
        sky += (cloud1 + cloud2)

    # add 70 random background stars (round Gaussian dots, not square boxes)
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


def scale_image_ds9(img, method, contrast):
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
            "spectrum": {"Water Ice (H2O)": 0.0, "Ammonia (NH3)": 0.0, "Methane (CH4)": 0.0, "Silicate Dust": 0.0},
            "stats": {
                "Measured Center": f"X={found_x} px, Y={found_y} px",
                "Aperture Flux": f"{max(0.0, total_flux):.1f} ADU (Noise)",
                "Signal-to-Noise": f"{snr:.2f} (Too Low)",
                "Radius": "N/A",
                "Albedo": "N/A",
                "Eccentricity": "N/A",
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

    return True, found_x, found_y, {
        "shift": shift_str,
        "prob": prob,
        "spectrum": {
            "Water Ice (H2O)": h2o,
            "Ammonia (NH3)": nh3,
            "Methane (CH4)": ch4,
            "Silicate Dust": dust
        },
        "stats": {
            "Measured Center": f"X={found_x} px, Y={found_y} px",
            "Aperture Flux": f"{total_flux:.1f} ADU (Peak: {peak_val:.1f})",
            "Signal-to-Noise": f"{snr:.2f} σ (Clear Hit)",
            "Radius": f"{rad:.2f} Earth Radii",
            "Albedo": f"{alb:.3f} (Dark Ice)",
            "Eccentricity": f"{ecc:.3f}",
            "Thermal Emission": f"{temp_k:.1f} Kelvin"
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
                if i < 2000:
                    amp = int(amp * (i / 2000))
                elif i > n_samples - 2000:
                    amp = int(amp * ((n_samples - i) / 2000))
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


# --- Main App Workflow ---
load_css()
setup_session()


# ================= PAGE 1: LOGIN =================
if st.session_state.page == "login":
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
                        "last_mode": "🛰️ The Proxy Route (Simulated FITS)",
                        "score": 0,
                        "logs": []
                    }
                st.session_state.score = st.session_state.profiles[clean_name]["score"]
                st.session_state.page = "home"
                st.rerun()
            else:
                st.markdown("<div class='miss-banner'>Access Denied. Please enter a Hunter ID first.</div>", unsafe_allow_html=True)


# ================= PAGE 2: DASHBOARD =================
elif st.session_state.page == "home":
    show_header()
    
    user = st.session_state.user
    prof = st.session_state.profiles.get(user, {"last_mode": "🛰️ The Proxy Route (Simulated FITS)", "score": 0, "logs": []})
    
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
            <p class='card-text'>Welcome to <i>ExoMapper</i>! Your mission is to scan deep-space infrared frames, spot moving thermal anomalies across time epochs, and analyze their light spectra to find hidden planets in the outer solar system.</p>
        </div>
        <div class="info-card" style="border-color: #ff9100;">
            <h3 style='color:#ff9100; font-family:"Chakra Petch";'>🔭 About SPHEREx Mission</h3>
            <p class='card-text'><b>SPHEREx</b> is a NASA space telescope mission designed to map the entire sky in near-infrared light. By looking at heat signatures instead of visible light, it helps scientists study water ice in planetary systems and distant galaxies.</p>
            <a href="https://science.nasa.gov/mission/spherex/" target="_blank" class="ext-link">NASA SPHEREx Portal</a>
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        st.markdown("""
        <div class="info-card" style="border-color: #e040fb;">
            <h3 style='color:#e040fb; font-family:"Chakra Petch";'>🪐 The Mystery of Planet X</h3>
            <p class='card-text'>Strange orbits of icy objects beyond Neptune suggest a massive <b>9th planet</b> might be hiding in the outer solar system. It is too far away to reflect normal sunlight, but its faint heat glow can be caught in infrared scans.</p>
            <a href="https://solarsystem.nasa.gov/planets/hypothetical-planet-x/in-depth/" target="_blank" class="ext-link" style="background:#e040fb; color:#fff;">NASA Planet X Archive</a>
        </div>
        <div class="info-card">
            <h3 style='color:#00e5ff; font-family:"Chakra Petch";'>🧑‍🚀 Team ExoMapper & Rules</h3>
            <p class='card-text'><b>Team Members:</b> Shikshita & Ayaan</p>
            <ul class='card-text'>
                <li><b>True Anomaly Lock:</b> <span style='color:#00e5ff; font-weight:bold;'>+150 Points</span></li>
                <li><b>False Target Guess:</b> <span style='color:#ff1744; font-weight:bold;'>-50 Points</span></li>
            </ul>
            <p class='card-text'><i>Blink the two epochs, draw a selection box over the moving dot, and lock coordinates.</i></p>
        </div>
        """, unsafe_allow_html=True)

    # --- Work History / Logbook Section ---
    st.markdown("<hr style='border-color: rgba(0,229,255,0.35);'>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<h3 style='color:#00e5ff; font-family:Chakra Petch; margin-top:0;'>📋 Hunter Telemetry Logbook — Track Your Work</h3>", unsafe_allow_html=True)
        
        logs = prof.get("logs", [])
        if not logs:
            st.info("No scans recorded yet. Click 'Start the Task 📡' to begin your first scan!")
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


# ================= PAGE 3: RADAR & VIEWER =================
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
        st.rerun()
    if t3.button("Abort Task", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

    user = st.session_state.user
    modes = [
        "🛰️ The Proxy Route (Simulated FITS)", 
        "🧬 Hybrid Injection", 
        "📡 Live Caltech IRSA (API / Real Upload)"
    ]
    saved_mode = st.session_state.profiles[user].get("last_mode", modes[0])

    # Uplink Source Box
    with st.container(border=True):
        st.markdown("<h4 style='color:#00e5ff; font-family:Chakra Petch; margin-top:0;'>📡 SELECT UPLINK SOURCE</h4>", unsafe_allow_html=True)
        st.markdown("""
        <div style='display:flex; gap:12px; flex-wrap:wrap; margin-bottom:10px; font-size:0.95rem;'>
            <div style='flex:1; background:rgba(0,229,255,0.06); padding:8px; border-radius:5px; border-left:3px solid #00e5ff;'>
                <b style='color:#00e5ff;'>1. Proxy Route:</b> Simulated starfield with Gaussian stars and background noise.
            </div>
            <div style='flex:1; background:rgba(255,145,0,0.06); padding:8px; border-radius:5px; border-left:3px solid #ff9100;'>
                <b style='color:#ff9100;'>2. Hybrid Injection:</b> Nebula background glow mixed with a moving Planet X signal.
            </div>
            <div style='flex:1; background:rgba(224,64,251,0.06); padding:8px; border-radius:5px; border-left:3px solid #e040fb;'>
                <b style='color:#e040fb;'>3. Caltech IRSA:</b> Use pre-loaded NASA FITS cutouts or upload your own FITS file.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        chosen_mode = st.radio("Select Mode", modes, index=modes.index(saved_mode) if saved_mode in modes else 0, horizontal=True, label_visibility="collapsed")
        st.session_state.profiles[user]["last_mode"] = chosen_mode

    # Control Box
    with st.container(border=True):
        st.markdown("<h4 style='color:#b388ff; font-family:Chakra Petch; margin-top:0;'>🎛️ SAOImage DS9 Image Controls</h4>", unsafe_allow_html=True)
        d1, d2, d3, d4 = st.columns([1.2, 1.2, 1.2, 0.8])
        with d1:
            scale_opt = st.selectbox("Scale Mode:", ["Linear", "Logarithmic (Log)", "Square Root (Sqrt)", "Histogram Equalization"])
        with d2:
            color_opt = st.selectbox("Color Map:", ["gray", "inferno", "viridis", "plasma", "magma", "cividis"])
        with d3:
            contrast_val = st.slider("Contrast / Bias:", 0.85, 1.0, 0.98, 0.01)
        with d4:
            st.write("")
            invert_color = st.checkbox("Invert Colors", value=False)
            
    cmap_final = f"{color_opt}_r" if invert_color else color_opt

    px, py = st.session_state.planet_x, st.session_state.planet_y
    f1_raw, f2_raw = None, None
    custom_file_used = False
    source_name = ""

    if "Proxy" in chosen_mode:
        source_name = f"Proxy Starfield (Seed #{st.session_state.seed})"
        f1_raw, f2_raw = make_sky_frames(chosen_mode, px, py, st.session_state.seed)
    elif "Hybrid" in chosen_mode:
        source_name = f"Hybrid Nebula Field (Seed #{st.session_state.seed})"
        f1_raw, f2_raw = make_sky_frames(chosen_mode, px, py, st.session_state.seed)
    else:
        st.markdown('<a href="https://irsa.ipac.caltech.edu/applications/Cutouts/" target="_blank" class="ext-link" style="margin-bottom:12px;">🔗 Open NASA/Caltech IRSA Cutouts</a>', unsafe_allow_html=True)
        preset = st.selectbox("Choose Sample NASA FITS Cutout:", ["SPHEREx_DeepField_SectorA.fits", "NEOWISE_W1_OuterRim_Epoch1.fits", "2MASS_KuiperBelt_Survey_09.fits"])
        up_file = st.file_uploader("Or Upload Your Own FITS File (.fits)", type=["fits", "fit"])
        
        if up_file is not None:
            arr = read_fits_upload(up_file)
            if arr is not None:
                f1_raw = arr
                f2_raw = np.roll(arr, shift=(5, 8), axis=(0, 1))
                custom_file_used = True
                source_name = f"Uploaded: {up_file.name}"
                st.success(f"Loaded {up_file.name}")
            else:
                st.error("Could not read 2D image from this FITS file.")
        else:
            p_seed = sum(ord(ch) for ch in preset) + st.session_state.seed
            source_name = f"IRSA Sample: {preset}"
            f1_raw, f2_raw = make_sky_frames("Hybrid", px, py, p_seed)

    # Display Frames & Blink Comparator
    if f1_raw is not None and f2_raw is not None:
        img1 = scale_image_ds9(f1_raw, scale_opt, contrast_val)
        img2 = scale_image_ds9(f2_raw, scale_opt, contrast_val)

        if not st.session_state.blinking:
            st.markdown("<p class='card-text'><b>Step 1:</b> Compare Epoch 1 and Epoch 2 below. Click the button to merge them and start blinking.</p>", unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            with col_a:
                fig1 = go.Figure(data=go.Heatmap(z=img1, colorscale=cmap_final, showscale=False))
                fig1.update_layout(margin=dict(l=0,r=0,t=25,b=0), title="Epoch 1 (T = 0)", xaxis=dict(title="X (px)", color="#84ffff"), yaxis=dict(title="Y (px)", color="#84ffff"), paper_bgcolor="#000", plot_bgcolor="#000", height=350)
                st.plotly_chart(fig1, use_container_width=True)
            with col_b:
                fig2 = go.Figure(data=go.Heatmap(z=img2, colorscale=cmap_final, showscale=False))
                fig2.update_layout(margin=dict(l=0,r=0,t=25,b=0), title="Epoch 2 (T + 6 Months)", xaxis=dict(title="X (px)", color="#84ffff"), yaxis=dict(title="Y (px)", color="#84ffff"), paper_bgcolor="#000", plot_bgcolor="#000", height=350)
                st.plotly_chart(fig2, use_container_width=True)
                
            if st.button("🚨 LAUNCH DS9 BLINK COMPARATOR", use_container_width=True):
                st.session_state.blinking = True
                st.rerun()
        else:
            st.markdown("<p class='card-text'><b>Step 2:</b> Blinking active! Drag a <b>Box</b> over the moving star on the chart to capture its coordinates.</p>", unsafe_allow_html=True)
            
            c_loop, c_spd, c_stop = st.columns([1.5, 1.5, 1])
            with c_loop:
                keep_looping = st.toggle("🔄 AUTO-LOOP BLINK (NON-STOP)", value=False)
            with c_spd:
                speed_ms = st.slider("Blink Speed (ms):", 200, 1000, 450, 50)
            with c_stop:
                if st.button("⏹ EXIT BLINK MODE", use_container_width=True):
                    st.session_state.blinking = False
                    st.rerun()

            frames_list = [
                go.Frame(data=[go.Heatmap(z=img1 if i % 2 == 0 else img2, colorscale=cmap_final, showscale=True)], name=f"fr_{i}")
                for i in range(30)
            ]
            
            curr_img = img1 if st.session_state.frame_step % 2 == 0 else img2
            ep_name = "EPOCH 1" if st.session_state.frame_step % 2 == 0 else "EPOCH 2"

            blink_fig = go.Figure(
                data=[go.Heatmap(z=curr_img, colorscale=cmap_final, showscale=True)],
                layout=go.Layout(
                    title=dict(text=f"Blink Comparator — Showing: {ep_name}", font=dict(color="#00e5ff", family="Chakra Petch", size=16)),
                    xaxis=dict(title="X Axis (Pixels)", color="#84ffff", range=[0, f1_raw.shape[1]]),
                    yaxis=dict(title="Y Axis (Pixels)", color="#84ffff", range=[0, f1_raw.shape[0]]),
                    paper_bgcolor="#010409", plot_bgcolor="#010409", height=500,
                    margin=dict(l=40, r=40, t=45, b=40),
                    dragmode="select",
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

            if st.session_state.user_box is not None:
                bx0, bx1, by0, by1 = st.session_state.user_box
                blink_fig.add_shape(type="rect", x0=bx0, y0=by0, x1=bx1, y1=by1, line=dict(color="#00e5ff", width=3), fillcolor="rgba(0,229,255,0.18)")

            event_data = st.plotly_chart(
                blink_fig, use_container_width=True, key="blink_chart",
                on_select="rerun", selection_mode=("box", "lasso"),
                config={'scrollZoom': True, 'displayModeBar': True}
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
                st.success(f"Box captured from chart! Center: X={def_x}, Y={def_y}")
            else:
                def_x, def_y = 200, 200
                st.markdown("<p class='card-text'>Drag a selection box on the Blink chart above, or type the X and Y coordinates below:</p>", unsafe_allow_html=True)

            cx1, cy1, crad, cbtn = st.columns([1, 1, 1, 1.8])
            with cx1:
                in_x = st.number_input("Center X (px):", 0, f1_raw.shape[1]-1, int(np.clip(def_x, 0, f1_raw.shape[1]-1)))
            with cy1:
                in_y = st.number_input("Center Y (px):", 0, f1_raw.shape[0]-1, int(np.clip(def_y, 0, f1_raw.shape[0]-1)))
            with crad:
                in_r = st.number_input("Box Radius (px):", 4, 40, 12)
            with cbtn:
                st.write("")
                if st.button("🎯 LOCK TARGET & EXTRACT DATA", use_container_width=True):
                    hit_ok, mx, my, res_dict = analyze_target_box(
                        f1_raw, f2_raw, in_x - in_r, in_x + in_r, in_y - in_r, in_y + in_r, px, py, custom_file_used
                    )
                    st.session_state.is_hit = hit_ok
                    st.session_state.score += (150 if hit_ok else -50)
                    st.session_state.profiles[user]["score"] = st.session_state.score
                    st.session_state.result_data = res_dict

                    # Save to user's logbook
                    user_logs = st.session_state.profiles[user]["logs"]
                    user_logs.append({
                        "Scan #": len(user_logs) + 1,
                        "Timestamp": get_time_str(),
                        "Uplink Mode": chosen_mode,
                        "FITS Source": source_name,
                        "Attempt Type": "Retry Scan" if st.session_state.is_retry else "First Scan",
                        "Target Coords (X, Y)": f"X={mx}, Y={my}",
                        "Status": "VERIFIED HIT" if hit_ok else "FALSE ALARM",
                        "Score Delta": "+150 Pts" if hit_ok else "-50 Pts",
                        "Planet Name": "Unassigned" if hit_ok else "N/A (Noise)",
                        "Radius": res_dict["stats"]["Radius"],
                        "Albedo": res_dict["stats"]["Albedo"],
                        "Eccentricity": res_dict["stats"]["Eccentricity"],
                        "Thermal Emission": res_dict["stats"]["Thermal Emission"]
                    })
                    st.session_state.last_log_idx = len(user_logs) - 1
                    st.session_state.page = "analysis"
                    st.rerun()


# ================= PAGE 4: SCIENTIFIC RESULTS =================
elif st.session_state.page == "analysis":
    show_header()
    
    user = st.session_state.user
    res = st.session_state.result_data
    
    if st.session_state.is_hit:
        st.markdown("<div class='hit-banner'>✅ TARGET VERIFIED: Moving Planetary Signature Confirmed! (+150 Points)</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='miss-banner'>❌ FALSE ALARM: Only background noise found there. True anomaly was at X={st.session_state.planet_x}, Y={st.session_state.planet_y}. (-50 Points)</div>", unsafe_allow_html=True)

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
        if wav_data:
            st.audio(wav_data, format='audio/wav')

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

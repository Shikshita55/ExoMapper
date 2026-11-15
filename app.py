# ExoMapper: The Hunt for Planet X
# NASA Space Apps Challenge 2026 - Team ExoMapper
# Written in Python using Streamlit, NumPy, Pandas, and PIL
import base64
import io
import math
import wave
from datetime import datetime
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components
st.set_page_config(
    page_title="ExoMapper | The Hunt for Planet X",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# puts multiline html on one single line so streamlit never shows raw </div> tags
def put_html(raw_code):
    flat_line = " ".join(line.strip() for line in raw_code.splitlines() if line.strip())
    st.markdown(flat_line, unsafe_allow_html=True)

# official NASA meatball logo encoded as base64 svg
def nasa_logo_data():
    svg_text = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 200" width="110" height="92">'
        '<defs><radialGradient id="nb" cx="38%" cy="32%" r="68%">'
        '<stop offset="0%" stop-color="#1b56b3"/><stop offset="55%" stop-color="#0b3d91"/>'
        '<stop offset="100%" stop-color="#061f4a"/></radialGradient></defs>'
        '<circle cx="118" cy="100" r="82" fill="url(#nb)" stroke="#8cb8ff" stroke-width="1.5" stroke-opacity="0.45"/>'
        '<g fill="#ffffff"><circle cx="72" cy="48" r="1.7"/><circle cx="88" cy="36" r="1.2"/>'
        '<circle cx="105" cy="46" r="1.5"/><circle cx="145" cy="42" r="1.8"/><circle cx="164" cy="56" r="1.3"/>'
        '<circle cx="155" cy="72" r="1.4"/><circle cx="62" cy="132" r="1.6"/><circle cx="78" cy="148" r="1.2"/>'
        '<circle cx="96" cy="162" r="1.7"/><circle cx="148" cy="154" r="1.5"/><circle cx="168" cy="136" r="1.3"/>'
        '<circle cx="132" cy="166" r="1.2"/></g>'
        '<ellipse cx="118" cy="102" rx="74" ry="26" fill="none" stroke="#ffffff" stroke-width="2.6" '
        'stroke-dasharray="180 65" transform="rotate(-24 118 102)"/>'
        '<path d="M 30 136 Q 112 96 172 34 L 142 104 Q 176 74 214 60 Q 162 84 126 128 L 154 58 Q 104 106 30 136 Z" fill="#fc3d21"/>'
        '<text x="118" y="113" text-anchor="middle" fill="#ffffff" font-family="Georgia, serif" font-weight="900" font-size="44" letter-spacing="3">NASA</text>'
        '<ellipse cx="118" cy="102" rx="74" ry="26" fill="none" stroke="#ffffff" stroke-width="2.6" '
        'stroke-dasharray="55 200" stroke-dashoffset="-195" transform="rotate(-24 118 102)"/>'
        '<circle cx="184" cy="73" r="3.6" fill="#ffffff"/></svg>'
    )
    b64_str = base64.b64encode(svg_text.encode("utf-8")).decode("utf-8")
    return "data:image/svg+xml;base64," + b64_str

# dark space theme with moving stars across the whole screen
def apply_space_theme():
    css_block = """
    <style>
    @keyframes moveStars {
        from { background-position: 0px 0px, 0px 0px, 0px 0px; }
        to { background-position: 1000px 600px, -800px 900px, 500px -700px; }
    }
    @keyframes glowPulse {
        0%, 100% { box-shadow: 0 0 18px rgba(0, 212, 255, 0.22); }
        50% { box-shadow: 0 0 30px rgba(252, 61, 33, 0.36); }
    }
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #040711 !important;
        color: #f2f6ff !important;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    .stApp {
        background-image:
            radial-gradient(2px 2px at 40px 60px, #ffffff, rgba(0,0,0,0)),
            radial-gradient(1.8px 1.8px at 190px 140px, #9be2ff, rgba(0,0,0,0)),
            radial-gradient(2.2px 2.2px at 340px 270px, #ffd59e, rgba(0,0,0,0)),
            radial-gradient(1.5px 1.5px at 520px 90px, #ffffff, rgba(0,0,0,0)),
            radial-gradient(2px 2px at 680px 320px, #b8d8ff, rgba(0,0,0,0)),
            radial-gradient(circle at 18% 22%, rgba(11, 61, 145, 0.30) 0%, transparent 48%),
            radial-gradient(circle at 82% 76%, rgba(252, 61, 33, 0.16) 0%, transparent 45%);
        background-size: 550px 420px, 470px 490px, 620px 510px, 710px 640px, 530px 580px, 100% 100%, 100% 100%;
        animation: moveStars 95s linear infinite;
        background-attachment: fixed;
    }
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background: linear-gradient(180deg, #060b19 0%, #0a142d 100%) !important;
        border-right: 1px solid rgba(0, 212, 255, 0.25) !important;
        color: #f2f6ff !important;
    }
    div[data-baseweb="input"],
    div[data-baseweb="base-input"],
    div[data-baseweb="select"] > div,
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div[role="button"] {
        background-color: #0c1938 !important;
        color: #ffffff !important;
        border: 1.5px solid #1e4b8f !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    .stTextInput input::placeholder {
        color: #8ab4f8 !important;
        opacity: 0.85 !important;
    }
    div[data-baseweb="popover"], ul[role="listbox"], li[role="option"] {
        background-color: #0c1938 !important;
        color: #ffffff !important;
    }
    div[data-testid="stExpander"] {
        background-color: #081126 !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 12px !important;
    }
    label, .stMarkdown p, .stRadio label, .stCheckbox label {
        color: #e8f1ff !important;
    }
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #0b3d91 0%, #1458c8 100%) !important;
        color: #ffffff !important;
        border: 1.5px solid #00d4ff !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        padding: 0.55rem 1.1rem !important;
        box-shadow: 0 4px 14px rgba(0, 212, 255, 0.22) !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #fc3d21 0%, #c8230c 100%) !important;
        border-color: #ffd166 !important;
    }
    .exo-card {
        background: linear-gradient(145deg, rgba(10, 21, 48, 0.92), rgba(7, 13, 30, 0.95));
        border: 1.5px solid rgba(0, 212, 255, 0.32);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 8px 26px rgba(0, 0, 0, 0.55);
    }
    .exo-badge {
        display: inline-block;
        background: #fc3d21;
        color: #ffffff;
        font-weight: 800;
        font-size: 11.5px;
        padding: 4px 14px;
        border-radius: 99px;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    .exo-sim-pill {
        display: inline-block;
        background: rgba(255, 209, 102, 0.16);
        border: 1px solid #ffd166;
        color: #ffd166;
        font-weight: 800;
        font-size: 11.5px;
        padding: 4px 12px;
        border-radius: 99px;
    }
    .exo-real-pill {
        display: inline-block;
        background: rgba(0, 255, 157, 0.16);
        border: 1px solid #00ff9d;
        color: #00ff9d;
        font-weight: 800;
        font-size: 11.5px;
        padding: 4px 12px;
        border-radius: 99px;
    }
    .exo-link-btn {
        display: inline-block;
        margin-top: 6px;
        margin-right: 6px;
        padding: 6px 12px;
        background: rgba(11, 61, 145, 0.78);
        border: 1px solid #00d4ff;
        border-radius: 8px;
        color: #7ce8ff !important;
        text-decoration: none !important;
        font-size: 12.5px;
        font-weight: 700;
    }
    .exo-link-btn:hover {
        background: #fc3d21;
        color: #ffffff !important;
        border-color: #ffffff;
    }
    </style>
    """
    put_html(css_block)

# SPHEREx detector resolution is 6.2 arcseconds per pixel
ARCSEC_PER_PX = 6.2

# sky sectors with 3 observation passes each
skyData = {
    "Sector 1: Orion Outer Rim (Deep Infrared Survey)": {
        "seed": 104,
        "ra_center": 83.8221,
        "dec_center": -5.3911,
        "constellation": "Orion",
        "band": "SPHEREx Band 4 (3.82 um Near-IR)",
        "epochs": {
            "Pass 1 (2026-03-14 04:12 UTC)": {"step": 0.0, "days": 0, "label": "2026-03-14 04:12 UTC"},
            "Pass 2 (2026-09-18 11:45 UTC)": {"step": 1.0, "days": 188, "label": "2026-09-18 11:45 UTC"},
            "Pass 3 (2027-03-22 08:30 UTC)": {"step": 2.0, "days": 373, "label": "2027-03-22 08:30 UTC"}
        },
        "objects": [
            {
                "name": "Unconfirmed Trans-Neptunian Candidate (TNO-Orion-1)",
                "kind": "Planet X Candidate",
                "status": "UNCONFIRMED CANDIDATE (Needs 3rd-Epoch Orbit Check)",
                "x1": 96, "y1": 112, "dx": 14, "dy": -8,
                "flux_e1": 14.2, "flux_e2": 14.4, "amp": 0.96, "points": 150,
                "distance": "~620 AU (From Parallax Shift)",
                "temp": "~48 K (-225 C)",
                "mass": "~6.2 Earth Masses (Model Estimate)",
                "wavelength": "3.82 um Methane & Water Ice Band",
                "freq": 540,
                "note": "Moved slowly across pixels with steady ~14.3 mJy brightness! Logged as an Unconfirmed Planet X Candidate for follow-up."
            },
            {
                "name": "Nearby Cool Brown Dwarf Candidate (BD-Orion-04)",
                "kind": "Brown Dwarf Candidate",
                "status": "PROPER-MOTION CANDIDATE (Needs Spectrum Check)",
                "x1": 218, "y1": 74, "dx": 7, "dy": 6,
                "flux_e1": 9.8, "flux_e2": 9.6, "amp": 0.82, "points": 80,
                "distance": "~24 Light-Years",
                "temp": "~410 K (Cool Y-Dwarf)",
                "mass": "~18 Jupiter Masses",
                "wavelength": "4.50 um Thermal Glow",
                "freq": 420,
                "note": "Small proper-motion shift at steady ~9.7 mJy brightness. Matches a nearby cool brown dwarf."
            },
            {
                "name": "Distant Supernova Transient Candidate (SN-2026or)",
                "kind": "Transient Candidate",
                "status": "PHOTOMETRIC TRANSIENT CANDIDATE (Fixed Position, Bright Flash)",
                "x1": 64, "y1": 228, "dx": 0, "dy": 0,
                "flux_e1": 2.4, "flux_e2": 13.8, "amp": 0.93, "points": 85,
                "distance": "~140 Million Light-Years",
                "temp": "~11,500 K",
                "mass": "~1.4 Solar Masses",
                "wavelength": "1.65 um Near-IR Peak",
                "freq": 660,
                "note": "Stayed at the exact same pixel (0.0 px shift) but brightened from 2.4 mJy to 13.8 mJy!"
            }
        ]
    },
    "Sector 2: Taurus Kuiper Belt Corridor": {
        "seed": 209,
        "ra_center": 68.9800,
        "dec_center": 16.5092,
        "constellation": "Taurus",
        "band": "SPHEREx Band 3 (3.40 um Near-IR)",
        "epochs": {
            "Pass 1 (2026-02-20 02:30 UTC)": {"step": 0.0, "days": 0, "label": "2026-02-20 02:30 UTC"},
            "Pass 2 (2026-08-25 09:15 UTC)": {"step": 1.0, "days": 186, "label": "2026-08-25 09:15 UTC"},
            "Pass 3 (2027-02-24 14:10 UTC)": {"step": 2.0, "days": 369, "label": "2027-02-24 14:10 UTC"}
        },
        "objects": [
            {
                "name": "Unconfirmed Distant Kuiper Candidate (TNO-Tauri-7)",
                "kind": "Planet X Candidate",
                "status": "UNCONFIRMED CANDIDATE (Needs 3rd-Epoch Orbit Check)",
                "x1": 188, "y1": 176, "dx": -15, "dy": -10,
                "flux_e1": 13.5, "flux_e2": 13.7, "amp": 0.95, "points": 150,
                "distance": "~540 AU (From Parallax Shift)",
                "temp": "~52 K (-221 C)",
                "mass": "~7.5 Earth Masses",
                "wavelength": "3.40 um Infrared Band",
                "freq": 560,
                "note": "Clear shift across the star field with steady ~13.6 mJy brightness. Logged as an unconfirmed Planet X candidate!"
            },
            {
                "name": "Variable M-Dwarf Flare Star Candidate (TV-Tauri-9)",
                "kind": "Transient Candidate",
                "status": "VARIABLE STAR CANDIDATE (Fixed Position, Flux Jump)",
                "x1": 82, "y1": 90, "dx": 0, "dy": 0,
                "flux_e1": 3.1, "flux_e2": 12.6, "amp": 0.89, "points": 70,
                "distance": "~68 Light-Years",
                "temp": "~3,100 K (Flare Event)",
                "mass": "~0.35 Solar Masses",
                "wavelength": "2.20 um Continuum",
                "freq": 490,
                "note": "Did not move in position, but flared brightly between the two dates."
            }
        ]
    },
    "Sector 3: Cygnus Ecliptic Deep Field": {
        "seed": 317,
        "ra_center": 305.5570,
        "dec_center": 40.2567,
        "constellation": "Cygnus",
        "band": "SPHEREx Band 4 (4.10 um Thermal IR)",
        "epochs": {
            "Pass 1 (2026-04-02 07:50 UTC)": {"step": 0.0, "days": 0, "label": "2026-04-02 07:50 UTC"},
            "Pass 2 (2026-10-06 16:20 UTC)": {"step": 1.0, "days": 187, "label": "2026-10-06 16:20 UTC"},
            "Pass 3 (2027-04-09 19:05 UTC)": {"step": 2.0, "days": 372, "label": "2027-04-09 19:05 UTC"}
        },
        "objects": [
            {
                "name": "Unconfirmed Outer Solar System Candidate (TNO-Cyg-3)",
                "kind": "Planet X Candidate",
                "status": "UNCONFIRMED CANDIDATE (Needs 3rd-Epoch Orbit Check)",
                "x1": 134, "y1": 84, "dx": 16, "dy": 8,
                "flux_e1": 15.1, "flux_e2": 14.9, "amp": 0.98, "points": 150,
                "distance": "~480 AU (From Parallax Shift)",
                "temp": "~56 K (-217 C)",
                "mass": "~8.1 Earth Masses",
                "wavelength": "4.10 um Thermal IR Peak",
                "freq": 585,
                "note": "Shifted cleanly across epochs with constant ~15.0 mJy infrared brightness."
            },
            {
                "name": "Free-Floating Methane Dwarf Candidate (CFBDS-Cyg-2)",
                "kind": "Brown Dwarf Candidate",
                "status": "PROPER-MOTION CANDIDATE (Needs Spectrum Check)",
                "x1": 236, "y1": 212, "dx": -7, "dy": 7,
                "flux_e1": 10.4, "flux_e2": 10.2, "amp": 0.84, "points": 80,
                "distance": "~39 Light-Years",
                "temp": "~680 K (T-Dwarf)",
                "mass": "~13 Jupiter Masses",
                "wavelength": "3.30 um Methane Band",
                "freq": 445,
                "note": "Moderate proper motion across the sky at steady ~10.3 mJy brightness."
            }
        ]
    },
    "Sector 4: Carina High-Density Star Field": {
        "seed": 422,
        "ra_center": 161.2650,
        "dec_center": -59.6844,
        "constellation": "Carina",
        "band": "SPHEREx Band 4 (3.90 um Near-IR)",
        "epochs": {
            "Pass 1 (2026-01-19 01:05 UTC)": {"step": 0.0, "days": 0, "label": "2026-01-19 01:05 UTC"},
            "Pass 2 (2026-07-24 13:40 UTC)": {"step": 1.0, "days": 186, "label": "2026-07-24 13:40 UTC"},
            "Pass 3 (2027-01-25 06:15 UTC)": {"step": 2.0, "days": 371, "label": "2027-01-25 06:15 UTC"}
        },
        "objects": [
            {
                "name": "Unconfirmed Southern Ecliptic Candidate (TNO-Car-5)",
                "kind": "Planet X Candidate",
                "status": "UNCONFIRMED CANDIDATE (Needs 3rd-Epoch Orbit Check)",
                "x1": 74, "y1": 164, "dx": 16, "dy": -10,
                "flux_e1": 14.6, "flux_e2": 14.5, "amp": 0.97, "points": 150,
                "distance": "~590 AU (From Parallax Shift)",
                "temp": "~49 K (-224 C)",
                "mass": "~6.8 Earth Masses",
                "wavelength": "3.90 um SPHEREx Band 4",
                "freq": 550,
                "note": "Moved 18.9 pixels against stationary Carina background stars. Logged as an unconfirmed candidate!"
            },
            {
                "name": "Pulsating Mira Giant Candidate (Carina-V12)",
                "kind": "Transient Candidate",
                "status": "VARIABLE STAR CANDIDATE (Fixed Position, Pulsating Brightness)",
                "x1": 198, "y1": 118, "dx": 0, "dy": 0,
                "flux_e1": 3.0, "flux_e2": 13.2, "amp": 0.91, "points": 70,
                "distance": "~1,200 Light-Years",
                "temp": "~2,600 K",
                "mass": "~1.8 Solar Masses",
                "wavelength": "2.40 um Water Band",
                "freq": 470,
                "note": "Zero position shift, but brightened strongly between observation dates."
            }
        ]
    }
}

# converts pixel (x, y) to J2000 Right Ascension and Declination
def calc_sky_coords(px, py, ra0, dec0):
    dx_arc = (150.0 - float(px)) * ARCSEC_PER_PX
    dy_arc = (150.0 - float(py)) * ARCSEC_PER_PX
    cos_dec = max(0.1, abs(math.cos(math.radians(dec0))))
    ra_val = (ra0 + (dx_arc / 3600.0) / cos_dec) % 360.0
    dec_val = max(-89.99, min(89.99, dec0 + (dy_arc / 3600.0)))
    hrs = ra_val / 15.0
    rh = int(hrs)
    rm = int((hrs - rh) * 60.0)
    rs = ((hrs - rh) * 60.0 - rm) * 60.0
    ra_txt = f"{rh:02d}h {rm:02d}m {rs:04.1f}s ({ra_val:.4f} deg)"
    sign = "+" if dec_val >= 0 else "-"
    ad = abs(dec_val)
    dd = int(ad)
    dm = int((ad - dd) * 60.0)
    ds = ((ad - dd) * 60.0 - dm) * 60.0
    dec_txt = f"{sign}{dd:02d}d {dm:02d}m {ds:04.1f}s ({dec_val:+.4f} deg)"
    return ra_val, dec_val, ra_txt, dec_txt

# adds a glowing star spot onto a 2D numpy grid
def put_star(grid, cx, cy, bright, spread=2.1):
    h, w = grid.shape
    rad = int(max(6, spread * 4))
    x0, x1 = max(0, int(cx) - rad), min(w, int(cx) + rad + 1)
    y0, y1 = max(0, int(cy) - rad), min(h, int(cy) + rad + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.ogrid[y0:y1, x0:x1]
    d2 = (xx - cx) ** 2 + (yy - cy) ** 2
    grid[y0:y1, x0:x1] += bright * np.exp(-d2 / (2.0 * spread ** 2))

@st.cache_data(show_spinner=False)
def build_sector_pair(sector_name, pass_a, pass_b, clean_flag=False):
    sec = skyData[sector_name]
    rng = np.random.default_rng(sec["seed"])
    n_side = 300
    step_a = sec["epochs"][pass_a]["step"]
    step_b = sec["epochs"][pass_b]["step"]
    yy, xx = np.mgrid[0:n_side, 0:n_side]
    sensor_glow = 0.04 * np.sin(xx / 38.0) * np.cos(yy / 44.0) + 0.05
    pic_a = np.zeros((n_side, n_side), dtype=np.float32)
    pic_b = np.zeros((n_side, n_side), dtype=np.float32)
    # 170 fixed background stars
    sx_list = rng.uniform(8, n_side - 8, 170)
    sy_list = rng.uniform(8, n_side - 8, 170)
    sf_list = rng.uniform(0.18, 0.85, 170)
    ss_list = rng.uniform(1.3, 2.2, 170)
    for sx, sy, sf, ss in zip(sx_list, sy_list, sf_list, ss_list):
        put_star(pic_a, sx, sy, sf, ss)
        put_star(pic_b, sx, sy, sf, ss)
    for obj in sec["objects"]:
        xa = obj["x1"] + obj["dx"] * step_a
        ya = obj["y1"] + obj["dy"] * step_a
        xb = obj["x1"] + obj["dx"] * step_b
        yb = obj["y1"] + obj["dy"] * step_b
        if "Planet X" in obj["kind"] or "Brown Dwarf" in obj["kind"]:
            put_star(pic_a, xa, ya, obj["amp"], 2.5)
            put_star(pic_b, xb, yb, obj["amp"], 2.5)
        else:
            amp_a = obj["amp"] * (0.22 if step_a == 0 else 0.65)
            amp_b = obj["amp"] * (1.0 if step_b >= 1.0 else 0.25)
            put_star(pic_a, xa, ya, amp_a, 2.0)
            put_star(pic_b, xb, yb, amp_b, 2.7)
    noise_a = rng.normal(0.0, 0.028, (n_side, n_side)).astype(np.float32)
    noise_b = rng.normal(0.0, 0.028, (n_side, n_side)).astype(np.float32)
    if not clean_flag:
        pic_a = pic_a + sensor_glow + noise_a
        pic_b = pic_b + sensor_glow + noise_b
    else:
        pic_a = pic_a + noise_a * 0.30
        pic_b = pic_b + noise_b * 0.30
    return np.clip(pic_a, 0.0, 1.35), np.clip(pic_b, 0.0, 1.35)

# exports a 300x300 numpy sky image into standard FITS file bytes
def make_fits_bytes(arr, obs_date):
    cards = [
        f"{'SIMPLE':<8}= {'T':>20} / Standard FITS file",
        f"{'BITPIX':<8}= {-32:>20} / 32-bit float data",
        f"{'NAXIS':<8}= {2:>20} / 2D sky grid",
        f"{'NAXIS1':<8}= {300:>20} / Width in pixels",
        f"{'NAXIS2':<8}= {300:>20} / Height in pixels",
        f"{'DATE-OBS':<8}= '{obs_date:<18}' / Observation UTC",
        f"{'TELESCOP':<8}= '{'NASA-SPHEREx-Sim':<18}' / Telescope model",
        f"{'END':<80}"
    ]
    hdr_txt = "".join(f"{c:<80}" for c in cards)
    rem = (2880 - (len(hdr_txt) % 2880)) % 2880
    hdr_bytes = (hdr_txt + (" " * rem)).encode("ascii")
    raw_data = np.asarray(arr, dtype=">f4").tobytes()
    pad_data = (2880 - (len(raw_data) % 2880)) % 2880
    return hdr_bytes + raw_data + (b"\x00" * pad_data)

# loads an uploaded .fits or .png/.jpg file safely
def read_uploaded_sky(up_file):
    try:
        raw = up_file.read()
        if not raw:
            return None, f"File '{up_file.name}' is empty."
        fname = up_file.name.lower()
        if fname.endswith(".fits") or fname.endswith(".fit"):
            end_pos = raw.find(b"END     ")
            if end_pos != -1:
                start_byte = ((end_pos // 2880) + 1) * 2880
                vals = np.frombuffer(raw[start_byte:], dtype=">f4")
                if vals.size >= 2500:
                    side = int(math.isqrt(vals.size))
                    grid = vals[:side * side].reshape((side, side)).astype(np.float32)
                    grid = np.nan_to_num(grid, nan=0.0, posinf=0.0, neginf=0.0)
                    p2, p99 = np.percentile(grid, [2, 99.5])
                    scaled = np.clip((grid - p2) / max(1e-5, p99 - p2), 0.0, 1.0)
                    im = Image.fromarray((scaled * 255).astype(np.uint8)).resize((300, 300))
                    return np.asarray(im, dtype=np.float32) / 255.0, None
            return None, f"Could not read 2D FITS array from '{up_file.name}'."
        im = Image.open(io.BytesIO(raw)).convert("L").resize((300, 300))
        return np.asarray(im, dtype=np.float32) / 255.0, None
    except Exception as err:
        return None, f"Could not load '{up_file.name}': {err}"

# builds two sky images from an uploaded CSV star catalog
def read_uploaded_csv(csv_file):
    try:
        df = pd.read_csv(csv_file)
        if df.empty:
            return None, None, None, "Uploaded CSV is empty."
        col_map = {c.lower().strip(): c for c in df.columns}
        if "x1" not in col_map and "x" not in col_map:
            return None, None, None, "CSV needs 'x' and 'y' (or 'x1', 'y1', 'x2', 'y2') columns."
        pic_a = np.zeros((300, 300), dtype=np.float32) + 0.04
        pic_b = np.zeros((300, 300), dtype=np.float32) + 0.04
        for _, row in df.iterrows():
            x1 = float(row[col_map.get("x1", col_map.get("x"))])
            y1 = float(row[col_map.get("y1", col_map.get("y"))])
            x2 = float(row[col_map.get("x2", col_map.get("x1", col_map.get("x")))])
            y2 = float(row[col_map.get("y2", col_map.get("y1", col_map.get("y")))])
            f1 = float(row[col_map["flux_e1"]]) if "flux_e1" in col_map else 0.75
            f2 = float(row[col_map["flux_e2"]]) if "flux_e2" in col_map else f1
            a1 = min(1.1, f1 / 15.0) if f1 > 1.5 else f1
            a2 = min(1.1, f2 / 15.0) if f2 > 1.5 else f2
            put_star(pic_a, x1, y1, a1, 2.3)
            put_star(pic_b, x2, y2, a2, 2.3)
        rng = np.random.default_rng(77)
        pic_a += rng.normal(0.0, 0.015, (300, 300)).astype(np.float32)
        pic_b += rng.normal(0.0, 0.015, (300, 300)).astype(np.float32)
        return np.clip(pic_a, 0.0, 1.3), np.clip(pic_b, 0.0, 1.3), df, None
    except Exception as err:
        return None, None, None, f"CSV error: {err}"

def sample_csv_bytes():
    lines = [
        "object_id,label,x1,y1,x2,y2,flux_e1,flux_e2,ra_deg,dec_deg,obs_time_1,obs_time_2",
        "OBJ-01,Planet X Candidate,102,118,118,108,14.3,14.4,83.9012,-5.3210,2026-03-14T04:12Z,2026-09-18T11:45Z",
        "OBJ-02,Brown Dwarf Candidate,214,82,222,89,9.6,9.5,83.6940,-5.2650,2026-03-14T04:12Z,2026-09-18T11:45Z",
        "OBJ-03,Supernova Candidate,68,220,68,220,2.2,13.9,83.9580,-5.5110,2026-03-14T04:12Z,2026-09-18T11:45Z",
        "STAR-04,Fixed Field Star,150,150,150,150,8.5,8.5,83.8221,-5.3911,2026-03-14T04:12Z,2026-09-18T11:45Z",
        "STAR-05,Fixed Field Star,45,60,45,60,6.2,6.2,84.0010,-5.2360,2026-03-14T04:12Z,2026-09-18T11:45Z",
        "STAR-06,Fixed Field Star,245,240,245,240,7.4,7.4,83.6580,-5.5460,2026-03-14T04:12Z,2026-09-18T11:45Z"
    ]
    return "\n".join(lines).encode("utf-8")

# turns a 2D float grid into a colored PIL picture
def paint_sky(arr, theme_name="Deep Space Cyan", bright=1.0, contrast=1.0, is_diff=False):
    if is_diff:
        d = arr * contrast * 2.4
        pos = np.clip(d, 0.0, 1.0)
        neg = np.clip(-d, 0.0, 1.0)
        r = np.clip(6 + pos * 249, 0, 255).astype(np.uint8)
        g = np.clip(10 + pos * 165 + neg * 210, 0, 255).astype(np.uint8)
        b = np.clip(22 + pos * 30 + neg * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")
    adj = np.clip((arr - 0.15) * contrast + 0.15, 0.0, 1.2) * bright
    v = np.clip(adj, 0.0, 1.0)
    if theme_name == "Infrared Heat (SPHEREx)":
        r = np.clip(8 + (v ** 0.75) * 247, 0, 255).astype(np.uint8)
        g = np.clip(10 + (v ** 1.35) * 195, 0, 255).astype(np.uint8)
        b = np.clip(26 + (v ** 2.2) * 140, 0, 255).astype(np.uint8)
    elif theme_name == "Emerald Nebula":
        r = np.clip(6 + (v ** 1.7) * 150, 0, 255).astype(np.uint8)
        g = np.clip(14 + (v ** 0.8) * 240, 0, 255).astype(np.uint8)
        b = np.clip(24 + (v ** 1.2) * 195, 0, 255).astype(np.uint8)
    else:
        r = np.clip(6 + (v ** 1.5) * 225, 0, 255).astype(np.uint8)
        g = np.clip(12 + (v ** 0.95) * 238, 0, 255).astype(np.uint8)
        b = np.clip(28 + (v ** 0.70) * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")

# creates a 2-second WAV sound clip for the selected sky object
def create_doppler_wav(freq_hz, flux_val, is_planet_x):
    rate = 22050
    secs = 2.0
    n_tot = int(rate * secs)
    mem = io.BytesIO()
    with wave.open(mem, "wb") as wav_out:
        wav_out.setnchannels(1)
        wav_out.setsampwidth(2)
        wav_out.setframerate(rate)
        raw_pcm = bytearray()
        for i in range(n_tot):
            t = i / rate
            env = math.sin(math.pi * t / secs) ** 0.45
            if is_planet_x:
                f = freq_hz + 140.0 * math.sin(2.0 * math.pi * 1.5 * t) + 85.0 * t
                tone2 = 0.35 * math.sin(2.0 * math.pi * (f * 1.5) * t)
            else:
                f = freq_hz + 35.0 * math.cos(2.0 * math.pi * 3.0 * t)
                tone2 = 0.20 * math.sin(2.0 * math.pi * (f * 2.0) * t)
            sig = env * min(1.0, max(0.35, flux_val)) * (0.65 * math.sin(2.0 * math.pi * f * t) + tone2)
            val = int(max(-32767, min(32767, sig * 26000)))
            raw_pcm += val.to_bytes(2, byteorder="little", signed=True)
        wav_out.writeframes(bytes(raw_pcm))
    return mem.getvalue()

# checks the pixels inside the user's manually selected sky area
def analyze_sky_pick(sector_name, pass_a, pass_b, cx, cy, rad_px, shape_used, pic_a, pic_b, custom_mode=False):
    sec = skyData[sector_name]
    _, _, ra_txt, dec_txt = calc_sky_coords(cx, cy, sec["ra_center"], sec["dec_center"])
    ep_a = sec["epochs"][pass_a]
    ep_b = sec["epochs"][pass_b]
    day_gap = max(1, abs(ep_b["days"] - ep_a["days"]))
    r = max(5, int(rad_px))
    x0, x1 = max(0, cx - r), min(299, cx + r)
    y0, y1 = max(0, cy - r), min(299, cy + r)
    sub_a = pic_a[y0:y1 + 1, x0:x1 + 1]
    sub_b = pic_b[y0:y1 + 1, x0:x1 + 1]
    pk_a = float(np.max(sub_a))
    pk_b = float(np.max(sub_b))
    top_pk = max(pk_a, pk_b)
    bg_noise = float(max(0.015, np.std(pic_a)))
    snr_val = round(float(np.max(np.abs(sub_b - sub_a))) / bg_noise, 1)
    mjy_a = round(pk_a * 15.0, 2)
    mjy_b = round(pk_b * 15.0, 2)
    best_mjy = max(0.05, mjy_a, mjy_b)
    ab_mag = round(-2.5 * math.log10(best_mjy / 3631000.0), 2)
    hit = None
    best_dist = 999.0
    if not custom_mode:
        for obj in sec["objects"]:
            xa = obj["x1"] + obj["dx"] * ep_a["step"]
            ya = obj["y1"] + obj["dy"] * ep_a["step"]
            xb = obj["x1"] + obj["dx"] * ep_b["step"]
            yb = obj["y1"] + obj["dy"] * ep_b["step"]
            d_min = min(math.hypot(cx - xa, cy - ya), math.hypot(cx - xb, cy - yb))
            if d_min <= max(18.0, rad_px * 1.15) and d_min < best_dist:
                best_dist = d_min
                hit = (obj, xa, ya, xb, yb)
    if hit is not None:
        obj, xa, ya, xb, yb = hit
        px_move = round(math.hypot(xb - xa, yb - ya), 1)
        arc_move = round(px_move * ARCSEC_PER_PX, 1)
        daily_rate = round(arc_move / day_gap, 3)
        f1 = obj["flux_e1"]
        f2 = obj["flux_e2"] if ep_b["step"] != ep_a["step"] else obj["flux_e1"]
        pct = round(((f2 - f1) / max(0.1, f1)) * 100.0, 1)
        mag_cat = round(-2.5 * math.log10(max(f1, f2) / 3631000.0), 2)
        return {
            "found_flag": "YES (Candidate Anomaly Logged)",
            "title": obj["name"],
            "kind": obj["kind"],
            "status": obj["status"],
            "points": obj["points"],
            "ra_str": ra_txt,
            "dec_str": dec_txt,
            "date_a": ep_a["label"],
            "date_b": ep_b["label"],
            "distance": obj["distance"],
            "temp": obj["temp"],
            "mass": obj["mass"],
            "wavelength": obj["wavelength"],
            "shift_text": f"{px_move} px ({arc_move} arcsec | {daily_rate} arcsec/day over {day_gap}d)",
            "flux_text": f"Image A: {f1} mJy -> Image B: {f2} mJy ({pct:+.1f}%) | Mag: {mag_cat} AB | SNR: {max(snr_val, 14.0)} sigma",
            "peak_flux": round(top_pk, 3),
            "freq": obj["freq"],
            "note": obj["note"]
        }
    if custom_mode and snr_val >= 5.0:
        pct = round(((mjy_b - mjy_a) / max(0.1, mjy_a)) * 100.0, 1)
        return {
            "found_flag": "YES (Custom File Candidate)",
            "title": "Unconfirmed Moving / Variable Candidate (Uploaded Data)",
            "kind": "Planet X Candidate",
            "status": "UNCONFIRMED CANDIDATE (Needs Follow-Up Observation)",
            "points": 120,
            "ra_str": ra_txt,
            "dec_str": dec_txt,
            "date_a": "Custom File Epoch 1",
            "date_b": "Custom File Epoch 2",
            "distance": "Requires 3rd-Epoch Parallax Fit",
            "temp": "Pending Multi-Band IR Check",
            "mass": "Pending Thermal Model",
            "wavelength": "Uploaded Survey Band",
            "shift_text": f"Detected {snr_val} sigma change inside selected area",
            "flux_text": f"Image A: {mjy_a} mJy -> Image B: {mjy_b} mJy ({pct:+.1f}%) | Mag: {ab_mag} AB | SNR: {snr_val} sigma",
            "peak_flux": round(top_pk, 3),
            "freq": 520,
            "note": f"Your selected region shows a strong ({snr_val} sigma) change between Image A and Image B! Logged as an unconfirmed candidate."
        }
    return {
        "found_flag": "NO (Fixed Star or Noise)",
        "title": "False Alarm (Stationary Star or Background Noise)",
        "kind": "False Alarm",
        "status": "REJECTED (Fixed Background Star / Sensor Noise)",
        "points": -20,
        "ra_str": ra_txt,
        "dec_str": dec_txt,
        "date_a": ep_a["label"],
        "date_b": ep_b["label"],
        "distance": ">1,000 Light-Years (Background Star)",
        "temp": "~4,800 K (Normal Star)",
        "mass": "~1.0 Solar Mass",
        "wavelength": sec["band"],
        "shift_text": "0.0 px (0.0 arcsec shift - Did not move)",
        "flux_text": f"Image A: {mjy_a} mJy -> Image B: {mjy_b} mJy (Steady) | Mag: {ab_mag} AB | SNR: {snr_val} sigma",
        "peak_flux": round(top_pk, 3),
        "freq": 240,
        "note": "The pixels inside your selected area stayed in the same place and brightness. Blink the images manually or pause to spot a moving dot!"
    }

def to_b64_png(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# interactive HTML5 sky canvas with manual blink button, pause button, and mouse drag area selector
def make_canvas_widget(b64_a, b64_b, b64_sub, mode_name, shape_name, blink_ms, mx, my, mr, ra0, dec0, label_a, label_b, start_frame):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 6px;
            background: #060c1d;
            color: #eaf2ff;
            font-family: 'Segoe UI', Arial, sans-serif;
            text-align: center;
        }}
        .sky-box {{
            display: inline-block;
            background: #040814;
            border: 2px solid #00d4ff;
            border-radius: 14px;
            padding: 10px;
            box-shadow: 0 0 24px rgba(0, 212, 255, 0.25);
        }}
        canvas {{
            border-radius: 8px;
            cursor: crosshair;
            display: block;
            margin: 0 auto;
            background: #040814;
        }}
        .ctrl-row {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px;
            margin-top: 8px;
        }}
        .canvas-btn {{
            background: linear-gradient(135deg, #0b3d91, #1458c8);
            color: #ffffff;
            border: 1px solid #00d4ff;
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
        }}
        .canvas-btn:hover {{
            background: #fc3d21;
            border-color: #ffd166;
        }}
        .hud-row {{
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 6px;
            margin-top: 7px;
            padding: 6px 10px;
            background: #0b1736;
            border: 1px solid rgba(0, 212, 255, 0.35);
            border-radius: 8px;
            font-size: 12px;
            font-weight: 700;
        }}
        .pill-gold {{
            color: #ffd166;
            background: rgba(252, 61, 33, 0.22);
            border: 1px solid #fc3d21;
            padding: 3px 9px;
            border-radius: 99px;
        }}
        .pill-green {{
            color: #00ff9d;
            background: rgba(0, 255, 157, 0.14);
            border: 1px solid #00ff9d;
            padding: 3px 9px;
            border-radius: 99px;
        }}
        .pill-blue {{
            color: #7ce8ff;
            background: rgba(11, 61, 145, 0.55);
            border: 1px solid #00d4ff;
            padding: 3px 9px;
            border-radius: 99px;
        }}
    </style>
    </head>
    <body>
        <div class="sky-box" title="Click and drag on the sky image to manually select any area!">
            <canvas id="skyCanvas" width="460" height="460"></canvas>
            <div class="ctrl-row">
                <button class="canvas-btn" id="btnManualFlip" title="Flip between Image A and Image B manually">⚡ Blink Manually (Flip A ↔ B)</button>
                <button class="canvas-btn" id="btnPauseResume" title="Pause or resume blinking so you can select an area carefully">⏸️ Pause / ▶️ Resume Blink</button>
                <button class="canvas-btn" id="btnShowSub" title="Show or hide the Dark Subtraction Map">🌗 Toggle Subtraction View</button>
            </div>
            <div class="hud-row">
                <span id="frameInfo" class="pill-blue">Loading Sky Image...</span>
                <span id="pixelInfo" class="pill-gold">Selected Area: X={mx}, Y={my} (Size={mr}px)</span>
            </div>
            <div class="hud-row" style="margin-top:5px;">
                <span id="radecInfo" class="pill-green">J2000 Sky Coords: RA / Dec</span>
                <span style="color:#9ec5ff; font-size:11.5px;">Drag mouse on image to move & resize selection</span>
            </div>
        </div>
        <script>
        const canvas = document.getElementById('skyCanvas');
        const ctx = canvas.getContext('2d');
        const frameInfo = document.getElementById('frameInfo');
        const pixelInfo = document.getElementById('pixelInfo');
        const radecInfo = document.getElementById('radecInfo');
        const imgA = new Image();
        const imgB = new Image();
        const imgSub = new Image();
        imgA.src = "data:image/png;base64,{b64_a}";
        imgB.src = "data:image/png;base64,{b64_b}";
        imgSub.src = "data:image/png;base64,{b64_sub}";
        let curFrame = {start_frame};
        let activeMode = "{mode_name}";
        const shapeMode = "{shape_name}";
        const blinkMs = {blink_ms};
        const ra0 = {ra0};
        const dec0 = {dec0};
        const labelA = "{label_a}";
        const labelB = "{label_b}";
        let isPaused = (activeMode !== "Auto Blink Images");
        const scale = 460 / 300;
        let selX = {mx};
        let selY = {my};
        let selR = {mr};
        let dragging = false;
        function calcRaDec(px, py) {{
            const dxArc = (150.0 - px) * 6.2;
            const dyArc = (150.0 - py) * 6.2;
            const cosD = Math.max(0.1, Math.abs(Math.cos(dec0 * Math.PI / 180.0)));
            const ra = ((ra0 + (dxArc / 3600.0) / cosD) % 360.0 + 360.0) % 360.0;
            const dec = Math.max(-89.99, Math.min(89.99, dec0 + (dyArc / 3600.0)));
            return `RA: ${{ra.toFixed(4)}} deg | Dec: ${{dec >= 0 ? '+' : ''}}${{dec.toFixed(4)}} deg (J2000)`;
        }}
        function updateText() {{
            pixelInfo.textContent = `Selected Area: X=${{selX}}, Y=${{selY}} | Size=${{selR}}px (Type X, Y on right to scan)`;
            radecInfo.textContent = calcRaDec(selX, selY);
        }}
        function renderCanvas() {{
            ctx.clearRect(0, 0, 460, 460);
            if (activeMode === "Subtraction Map (Image B - Image A)") {{
                ctx.drawImage(imgSub, 0, 0, 460, 460);
                frameInfo.textContent = "Subtraction Map: Cyan = Image A | Gold = Image B";
            }} else if (activeMode === "Pause on Image A") {{
                ctx.drawImage(imgA, 0, 0, 460, 460);
                frameInfo.textContent = "Paused Image A: " + labelA;
            }} else if (activeMode === "Pause on Image B") {{
                ctx.drawImage(imgB, 0, 0, 460, 460);
                frameInfo.textContent = "Paused Image B: " + labelB;
            }} else {{
                if (curFrame === 1) {{
                    ctx.drawImage(imgA, 0, 0, 460, 460);
                    frameInfo.textContent = (isPaused ? "Manual/Paused A: " : "Blinking A: ") + labelA;
                }} else {{
                    ctx.drawImage(imgB, 0, 0, 460, 460);
                    frameInfo.textContent = (isPaused ? "Manual/Paused B: " : "Blinking B: ") + labelB;
                }}
            }}
            ctx.strokeStyle = "rgba(0, 212, 255, 0.14)";
            ctx.lineWidth = 1;
            for (let g = 57; g < 460; g += 57) {{
                ctx.beginPath(); ctx.moveTo(g, 0); ctx.lineTo(g, 460); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(0, g); ctx.lineTo(460, g); ctx.stroke();
            }}
            const cx = selX * scale;
            const cy = selY * scale;
            const cr = selR * scale;
            ctx.strokeStyle = "#ffd166";
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            if (shapeMode === "Draw Circle") {{
                ctx.arc(cx, cy, cr, 0, Math.PI * 2);
            }} else if (shapeMode === "Draw Square") {{
                ctx.rect(cx - cr, cy - cr, cr * 2, cr * 2);
            }} else {{
                ctx.rect(cx - cr * 1.35, cy - cr * 0.85, cr * 2.7, cr * 1.7);
            }}
            ctx.stroke();
            ctx.strokeStyle = "#fc3d21";
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(cx - 8, cy); ctx.lineTo(cx + 8, cy);
            ctx.moveTo(cx, cy - 8); ctx.lineTo(cx, cy + 8);
            ctx.stroke();
        }}
        document.getElementById('btnManualFlip').addEventListener('click', () => {{
            isPaused = true;
            if (activeMode === "Subtraction Map (Image B - Image A)" || activeMode === "Pause on Image A" || activeMode === "Pause on Image B") {{
                activeMode = "Manual Blink (Step-by-Step)";
            }}
            curFrame = (curFrame === 1) ? 2 : 1;
            renderCanvas();
        }});
        document.getElementById('btnPauseResume').addEventListener('click', () => {{
            if (activeMode === "Subtraction Map (Image B - Image A)") {{
                activeMode = "Auto Blink Images";
                isPaused = false;
            }} else {{
                isPaused = !isPaused;
                if (!isPaused) activeMode = "Auto Blink Images";
            }}
            renderCanvas();
        }});
        document.getElementById('btnShowSub').addEventListener('click', () => {{
            if (activeMode === "Subtraction Map (Image B - Image A)") {{
                activeMode = "Manual Blink (Step-by-Step)";
                isPaused = true;
            }} else {{
                activeMode = "Subtraction Map (Image B - Image A)";
                isPaused = true;
            }}
            renderCanvas();
        }});
        canvas.addEventListener('mousedown', (e) => {{
            const rect = canvas.getBoundingClientRect();
            selX = Math.max(0, Math.min(299, Math.round((e.clientX - rect.left) / scale)));
            selY = Math.max(0, Math.min(299, Math.round((e.clientY - rect.top) / scale)));
            dragging = true;
            updateText();
            renderCanvas();
        }});
        canvas.addEventListener('mousemove', (e) => {{
            if (!dragging) return;
            const rect = canvas.getBoundingClientRect();
            const curX = Math.round((e.clientX - rect.left) / scale);
            const curY = Math.round((e.clientY - rect.top) / scale);
            const dist = Math.round(Math.hypot(curX - selX, curY - selY));
            selR = Math.max(8, Math.min(60, dist));
            updateText();
            renderCanvas();
        }});
        window.addEventListener('mouseup', () => {{
            dragging = false;
        }});
        updateText();
        imgA.onload = renderCanvas;
        imgB.onload = renderCanvas;
        setInterval(() => {{
            if (!isPaused && activeMode === "Auto Blink Images") {{
                curFrame = (curFrame === 1) ? 2 : 1;
                renderCanvas();
            }}
        }}, blinkMs);
        </script>
    </body>
    </html>
    """

# session variables (scoreboard starts empty and only fills as players scan!)
if "page_step" not in st.session_state:
    st.session_state.page_step = "welcome"
if "explorerName" not in st.session_state:
    st.session_state.explorerName = ""
if "total_score" not in st.session_state:
    st.session_state.total_score = 0
if "x_pick" not in st.session_state:
    st.session_state.x_pick = 150
if "y_pick" not in st.session_state:
    st.session_state.y_pick = 150
if "r_pick" not in st.session_state:
    st.session_state.r_pick = 20
if "manual_frame" not in st.session_state:
    st.session_state.manual_frame = 1
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "score_table" not in st.session_state:
    st.session_state.score_table = []
if "saved_scores" not in st.session_state:
    st.session_state.saved_scores = {}

# Page 1: Welcome & Login Page
def show_welcome_screen():
    logo_b64 = nasa_logo_data()
    st.write("")
    st.write("")
    c1, c2, c3 = st.columns([1.1, 2.2, 1.1])
    with c2:
        put_html(f"""
        <div class="exo-card" style="text-align:center; padding:32px 26px; animation: glowPulse 4s infinite;" title="Welcome to ExoMapper! Enter your Space Explorer Name below.">
            <img src="{logo_b64}" alt="Official NASA Logo" style="width:112px; height:auto; margin-bottom:10px; filter: drop-shadow(0 4px 12px rgba(0, 212, 255, 0.45));"/>
            <div>
                <span class="exo-badge">NASA SPACE APPS CHALLENGE 2026 • TEAM EXOMAPPER</span>
            </div>
            <h1 style="margin:8px 0 4px 0; font-size:32px; font-weight:900; color:#ffffff; letter-spacing:0.4px;">
                Welcome to ExoMapper: The Hunt for Planet X
            </h1>
        </div>
        """)
        user_in = st.text_input(
            "Enter Your Space Explorer Name",
            value=st.session_state.explorerName,
            placeholder="Type a cute explorer name (e.g., Nova, Sky, Riley, or Alex)...",
            help="Enter your explorer username. If you log in again after playing, your score and scans are remembered!"
        )
        if st.button("🚀 Enter", use_container_width=True, help="Open the ExoMapper User Manual & Science Briefing!"):
            clean_u = user_in.strip()
            if not clean_u:
                st.warning("Please enter a Space Explorer Name first!")
            else:
                st.session_state.explorerName = clean_u
                st.session_state.total_score = st.session_state.saved_scores.get(clean_u, 0)
                st.session_state.last_result = None
                st.session_state.page_step = "manual"
                st.rerun()

# Page 2: User Manual & Briefing Page
def show_manual_screen():
    logo_b64 = nasa_logo_data()
    t1, t2, t3 = st.columns([3.4, 1.3, 1.0])
    with t1:
        put_html(f"""
        <div class="exo-card" style="display:flex; align-items:center; gap:16px; padding:16px 20px;">
            <img src="{logo_b64}" alt="NASA Logo" style="width:70px; height:auto;"/>
            <div>
                <span class="exo-badge" style="margin-bottom:4px;">STEP 1 OF 2 • EXOMAPPER USER MANUAL & BRIEFING</span>
                <h2 style="margin:2px 0 0 0; color:#ffffff; font-size:24px; font-weight:900;">
                    Welcome, {st.session_state.explorerName}! 📖 Read the Guide & Begin Your Hunt
                </h2>
            </div>
        </div>
        """)
    with t2:
        st.write("")
        if st.button("🎮 Begin the Game ➔", use_container_width=True):
            st.session_state.page_step = "game"
            st.rerun()
    with t3:
        st.write("")
        if st.button("🔄 Switch User", use_container_width=True):
            st.session_state.page_step = "welcome"
            st.rerun()
    b1, b2, b3 = st.columns(3)
    with b1:
        put_html("""
        <div class="exo-card" title="Planet X is a hypothetical world beyond Neptune. Moving dots in sky surveys are logged as unconfirmed candidates.">
            <div style="color:#ffd166; font-weight:800; font-size:16px; margin-bottom:6px;">🪐 About Planet X</div>
            <p style="font-size:13.5px; line-height:1.5; color:#d8e6ff; margin:0;">
                Beyond Pluto, icy Kuiper Belt objects follow clustered paths that suggest a hidden giant world (<b>Planet X</b>) may be pulling on them. Because it orbits hundreds of AU away, it glows faintly in infrared light and shifts slowly across pixels over months!
            </p>
            <a class="exo-link-btn" href="https://science.nasa.gov/solar-system/planet-x/" target="_blank">🔗 Official NASA Planet X Page</a>
        </div>
        """)
    with b2:
        put_html("""
        <div class="exo-card" title="SPHEREx maps the whole sky in 102 infrared bands every 6 months.">
            <div style="color:#7ce8ff; font-weight:800; font-size:16px; margin-bottom:6px;">🛰️ About SPHEREx</div>
            <p style="font-size:13.5px; line-height:1.5; color:#d8e6ff; margin:0;">
                <b>SPHEREx</b> is NASA's all-sky infrared space telescope. By comparing two pictures of the exact same sky coordinates (<b>RA and Dec</b>) taken 6 months apart, we can spot objects that moved or changed brightness!
            </p>
            <a class="exo-link-btn" href="https://science.nasa.gov/mission/spherex/" target="_blank">🔗 Official NASA SPHEREx Mission</a>
        </div>
        """)
    with b3:
        put_html("""
        <div class="exo-card" title="NASA shares public FITS files and catalogs so students can help discover new worlds.">
            <div style="color:#ff8a75; font-weight:800; font-size:16px; margin-bottom:6px;">🚀 About NASA Open Data</div>
            <p style="font-size:13.5px; line-height:1.5; color:#d8e6ff; margin:0;">
                <b>NASA</b> shares space telescope observations openly with students and citizen scientists. Every moving dot you find in two images is logged as an <b>Unconfirmed Candidate</b> awaiting a 3rd observation to confirm its orbit.
            </p>
            <a class="exo-link-btn" href="https://www.nasa.gov/" target="_blank">🔗 Visit Official NASA Portal</a>
        </div>
        """)
    g1, g2, g3 = st.columns(3)
    with g1:
        put_html("""
        <div class="exo-card">
            <div style="color:#00d4ff; font-weight:800; font-size:15.5px; margin-bottom:6px;">1. Pick Images, FITS or CSV Files</div>
            <p style="font-size:13.5px; line-height:1.5; color:#d8e6ff; margin:0;">
                On the next page, choose any <b>Sky Sector</b> and pick which two observation dates (Pass 1, Pass 2, or Pass 3) to compare, or upload your own <b>.FITS files</b>, <b>.CSV star catalogs</b>, or sky pictures!
            </p>
        </div>
        """)
    with g2:
        put_html("""
        <div class="exo-card">
            <div style="color:#ffd166; font-weight:800; font-size:15.5px; margin-bottom:6px;">2. Manual Blink, Pause & Select Area</div>
            <p style="font-size:13.5px; line-height:1.5; color:#d8e6ff; margin:0;">
                Click <b>⚡ Blink Manually (Flip A ↔ B)</b> to flip pictures at your own speed, or click <b>⏸️ Pause</b> anytime. Then drag your mouse directly on the sky to encircle the moving dot with a Circle, Square, or Rectangle!
            </p>
        </div>
        """)
    with g3:
        put_html("""
        <div class="exo-card">
            <div style="color:#7ce8ff; font-weight:800; font-size:15.5px; margin-bottom:6px;">3. Points, Flux & Scoreboard Rules</div>
            <p style="font-size:13.5px; line-height:1.5; color:#d8e6ff; margin:0;">
                • <b>Unconfirmed Planet X Candidate:</b> +150 pts<br/>
                • <b>Brown Dwarf / Supernova / Flare Star:</b> +70 to +85 pts<br/>
                • <b>False Alarm (Fixed Star / Noise):</b> -20 pts<br/>
                Your scoreboard updates live after your first scan!
            </p>
        </div>
        """)
    put_html("""
    <div class="exo-card">
        <div style="color:#00ff9d; font-weight:800; font-size:16px; margin-bottom:6px;">📂 Direct Links to Official NASA SPHEREx & Planet X Survey FITS Files (With Observation Times)</div>
        <p style="font-size:13.5px; color:#d8e6ff; margin:0 0 8px 0;">
            Click any link below to download real calibrated FITS files or open the NASA/IPAC Infrared Science Archive:
        </p>
        <a class="exo-link-btn" href="https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W18_1B/l2b-v27-2026-196/1/level2_2025W18_1B_0074_2D1_spx_l2b-v27-2026-196.fits" target="_blank">
            ⬇️ Direct SPHEREx DR1 Level-2 FITS (Obs Week: 2025W18_1B | Day: 2026-196 UTC)
        </a>
        <a class="exo-link-btn" href="https://irsa.ipac.caltech.edu/ibe/cutouts.html" target="_blank">
            🛰️ NASA/IPAC IRSA FITS Cutouts Server (SPHEREx & WISE Multi-Epoch Sky Cutouts)
        </a>
        <a class="exo-link-btn" href="https://skyview.gsfc.nasa.gov/cgi-bin/images?Survey=digitized+sky+survey&position=14.5,36.5&Return=FITS" target="_blank">
            ⬇️ Direct NASA SkyView 300x300 FITS Cutout (RA=14.5 deg, Dec=+36.5 deg J2000)
        </a>
        <a class="exo-link-btn" href="https://irsa.ipac.caltech.edu/" target="_blank">
            🌌 NASA/IPAC Infrared Science Archive Portal
        </a>
    </div>
    """)
    bc1, bc2, bc3 = st.columns([1.2, 2.0, 1.2])
    with bc2:
        if st.button("🚀 Begin the Game Now (Launch Interactive Sky Workbench)", use_container_width=True):
            st.session_state.page_step = "game"
            st.rerun()

# Page 3: Main Game & Astrometric Workbench
def show_game_screen():
    logo_b64 = nasa_logo_data()
    h1, h2, h3 = st.columns([3.6, 1.1, 1.0])
    with h1:
        put_html(f"""
        <div class="exo-card" style="display:flex; align-items:center; justify-content:space-between; gap:14px; padding:14px 20px;">
            <div style="display:flex; align-items:center; gap:14px;">
                <img src="{logo_b64}" alt="NASA Logo" style="width:66px; height:auto;"/>
                <div>
                    <span class="exo-badge" style="margin-bottom:4px;">EXOMAPPER SKY WORKBENCH • ACTIVE MISSION</span>
                    <h2 style="margin:2px 0 0 0; color:#ffffff; font-size:23px; font-weight:900;">
                        Explorer: {st.session_state.explorerName} 🪐 Select Sky Area & Hunt for Planet X
                    </h2>
                </div>
            </div>
            <div style="text-align:right; background:#0b1c40; border:1.5px solid #00d4ff; border-radius:12px; padding:6px 14px;">
                <div style="font-size:11px; color:#8ab4f8; font-weight:700;">CURRENT SCORE</div>
                <div style="font-size:22px; color:#ffd166; font-weight:900;">{st.session_state.total_score} pts</div>
            </div>
        </div>
        """)
    with h2:
        st.write("")
        if st.button("📖 User Manual", use_container_width=True):
            st.session_state.page_step = "manual"
            st.rerun()
    with h3:
        st.write("")
        if st.button("🔄 Switch User", use_container_width=True):
            st.session_state.page_step = "welcome"
            st.rerun()
    with st.sidebar:
        put_html("""
        <div class="exo-card" style="padding:12px 14px;">
            <div style="color:#00d4ff; font-weight:800; font-size:16px;">🔭 Image & Blink Settings</div>
            <div style="font-size:12.5px; color:#b8d4ff;">Tune color theme, brightness, contrast, and noise cleaning.</div>
        </div>
        """)
        color_theme = st.selectbox("Sky Color Theme", ["Deep Space Cyan", "Infrared Heat (SPHEREx)", "Emerald Nebula"])
        bright_val = st.slider("Star Brightness", 0.6, 2.0, 1.15, 0.05)
        contrast_val = st.slider("Sky Contrast", 0.6, 2.2, 1.20, 0.05)
        blink_ms = st.slider("Auto-Blink Speed (ms)", 250, 1200, 550, 50)
        clean_flag = st.checkbox("✨ Apply Dark & Bias Clean", value=False)
        put_html("""
        <div class="exo-card" style="padding:12px 14px; margin-top:10px;">
            <div style="color:#ffd166; font-weight:800; font-size:14.5px;">🔗 Direct FITS Links (With Time)</div>
            <a class="exo-link-btn" style="display:block; text-align:center;" href="https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W18_1B/l2b-v27-2026-196/1/level2_2025W18_1B_0074_2D1_spx_l2b-v27-2026-196.fits" target="_blank">⬇️ SPHEREx FITS (2025W18_1B)</a>
            <a class="exo-link-btn" style="display:block; text-align:center;" href="https://irsa.ipac.caltech.edu/ibe/cutouts.html" target="_blank">🛰️ IRSA Multi-Epoch Cutouts</a>
            <a class="exo-link-btn" style="display:block; text-align:center;" href="https://skyview.gsfc.nasa.gov/cgi-bin/images?Survey=digitized+sky+survey&position=14.5,36.5&Return=FITS" target="_blank">⬇️ SkyView 300x300 FITS</a>
        </div>
        """)
    s1, s2, s3, s4 = st.columns([1.45, 1.55, 1.35, 1.05])
    with s1:
        source_mode = st.selectbox(
            "📡 Data Source Option",
            ["Simulated SPHEREx Survey Sectors", "Upload Custom FITS / Sky Images", "Upload Custom CSV Star Catalog"]
        )
    with s2:
        picked_sector = st.selectbox("🌌 Sky Sector (J2000 Region)", list(skyData.keys()))
    with s3:
        view_mode = st.selectbox(
            "👁️ Blink / Pause / View Mode",
            [
                "Auto Blink Images",
                "Manual Blink (Step-by-Step)",
                "Pause on Image A",
                "Pause on Image B",
                "Subtraction Map (Image B - Image A)",
                "Side-by-Side 3-Panel View"
            ]
        )
    with s4:
        shape_mode = st.selectbox("✏️ Selection Shape", ["Draw Circle", "Draw Square", "Draw Rectangle"])
    sec_info = skyData[picked_sector]
    pass_list = list(sec_info["epochs"].keys())
    e1, e2, e3 = st.columns([1.6, 1.6, 1.2])
    with e1:
        pass_a = st.selectbox("🗓️ Select First Observation Image (Image A)", pass_list, index=0)
    with e2:
        pass_b = st.selectbox("🗓️ Select Second Observation Image (Image B)", pass_list, index=1)
    with e3:
        st.write("")
        if st.button("⚡ Flip Image A ↔ B Manually", use_container_width=True):
            st.session_state.manual_frame = 2 if st.session_state.manual_frame == 1 else 1
    custom_active = False
    pic_a, pic_b = build_sector_pair(picked_sector, pass_a, pass_b, clean_flag=clean_flag)
    label_a = sec_info["epochs"][pass_a]["label"]
    label_b = sec_info["epochs"][pass_b]["label"]
    if source_mode == "Upload Custom FITS / Sky Images":
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "⬇️ Download Sample FITS Image A (2026-03-14 UTC)",
                data=make_fits_bytes(pic_a, "2026-03-14T04:12:00"),
                file_name="spherex_sample_pass1_20260314.fits",
                mime="application/octet-stream"
            )
        with d2:
            st.download_button(
                "⬇️ Download Sample FITS Image B (2026-09-18 UTC)",
                data=make_fits_bytes(pic_b, "2026-09-18T11:45:00"),
                file_name="spherex_sample_pass2_20260918.fits",
                mime="application/octet-stream"
            )
        u1, u2 = st.columns(2)
        with u1:
            f_up1 = st.file_uploader("Upload First FITS / Sky Image (Image A)", type=["fits", "fit", "png", "jpg", "jpeg"])
        with u2:
            f_up2 = st.file_uploader("Upload Second FITS / Sky Image (Image B)", type=["fits", "fit", "png", "jpg", "jpeg"])
        if f_up1 is not None and f_up2 is not None:
            arr1, err1 = read_uploaded_sky(f_up1)
            arr2, err2 = read_uploaded_sky(f_up2)
            if err1 or err2:
                st.error(f"⚠️ {err1 or ''} {err2 or ''}")
            else:
                pic_a, pic_b = arr1, arr2
                custom_active = True
                label_a = f"Uploaded: {f_up1.name}"
                label_b = f"Uploaded: {f_up2.name}"
                st.success(f"✅ Loaded custom FITS/Image pair: '{f_up1.name}' & '{f_up2.name}'")
        else:
            st.info("ℹ️ Upload two .fits, .png, or .jpg files above (or download the sample FITS files to test!).")
    elif source_mode == "Upload Custom CSV Star Catalog":
        st.download_button(
            "⬇️ Download Sample Planet X & SPHEREx CSV Catalog Template",
            data=sample_csv_bytes(),
            file_name="spherex_planetx_sample_catalog.csv",
            mime="text/csv"
        )
        csv_up = st.file_uploader("Upload Custom CSV Catalog (columns: x1, y1, x2, y2, flux_e1, flux_e2)", type=["csv"])
        if csv_up is not None:
            ca, cb, cdf, cerr = read_uploaded_csv(csv_up)
            if cerr:
                st.error(f"⚠️ {cerr}")
            else:
                pic_a, pic_b = ca, cb
                custom_active = True
                label_a = f"CSV Epoch 1 ({csv_up.name})"
                label_b = f"CSV Epoch 2 ({csv_up.name})"
                st.success(f"✅ Built sky images from CSV catalog '{csv_up.name}' ({len(cdf)} rows)!")
                with st.expander("📋 View Uploaded CSV Catalog Table"):
                    st.dataframe(cdf, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Upload a .csv catalog file above (or download the sample CSV template to test!).")
    _, _, c_ra, c_dec = calc_sky_coords(150, 150, sec_info["ra_center"], sec_info["dec_center"])
    mode_pill = (
        '<span class="exo-real-pill">🛰️ CUSTOM UPLOADED FITS / CSV DATA ACTIVE</span>'
        if custom_active
        else '<span class="exo-sim-pill">🧪 SIMULATED SPHEREx DEMO DATA (6.2"/px)</span>'
    )
    put_html(f"""
    <div class="exo-card" style="padding:10px 16px;">
        <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px;">
            <span style="font-weight:800; font-size:14.5px; color:#ffffff;">📍 Field Center (J2000): RA {c_ra} | Dec {c_dec} ({sec_info['constellation']})</span>
            {mode_pill}
        </div>
        <div style="display:flex; flex-wrap:wrap; justify-content:space-between; gap:10px; font-size:12.5px; color:#b8d8ff; margin-top:4px;">
            <span>🖼️ <b>Image A:</b> {label_a}</span>
            <span>🖼️ <b>Image B:</b> {label_b}</span>
            <span>🌈 <b>Band:</b> {sec_info['band']}</span>
        </div>
    </div>
    """)
    diff_arr = pic_b - pic_a
    img_a = paint_sky(pic_a, color_theme, bright_val, contrast_val, is_diff=False)
    img_b = paint_sky(pic_b, color_theme, bright_val, contrast_val, is_diff=False)
    img_sub = paint_sky(diff_arr, color_theme, bright_val, contrast_val, is_diff=True)
    left_col, right_col = st.columns([1.42, 1.18])
    with left_col:
        if view_mode == "Side-by-Side 3-Panel View":
            p1, p2, p3 = st.columns(3)
            with p1:
                st.image(img_a, caption=f"Image A: {label_a}", use_container_width=True)
            with p2:
                st.image(img_b, caption=f"Image B: {label_b}", use_container_width=True)
            with p3:
                st.image(img_sub, caption="Subtraction (Cyan=A, Gold=B)", use_container_width=True)
        else:
            canvas_code = make_canvas_widget(
                b64_a=to_b64_png(img_a),
                b64_b=to_b64_png(img_b),
                b64_sub=to_b64_png(img_sub),
                mode_name=view_mode,
                shape_name=shape_mode,
                blink_ms=blink_ms,
                mx=st.session_state.x_pick,
                my=st.session_state.y_pick,
                mr=st.session_state.r_pick,
                ra0=sec_info["ra_center"],
                dec0=sec_info["dec_center"],
                label_a=label_a,
                label_b=label_b,
                start_frame=st.session_state.manual_frame
            )
            components.html(canvas_code, height=585, scrolling=False)
    with right_col:
        put_html("""
        <div class="exo-card" style="padding:14px 16px;">
            <div style="color:#ffd166; font-weight:800; font-size:16px; margin-bottom:4px;">🎯 Manual Area Selection & Candidate Scanner</div>
            <p style="font-size:13px; color:#d8e6ff; margin:0;">
                <b>How to select manually:</b> Click <b>⏸️ Pause</b> or <b>⚡ Blink Manually</b> under the sky picture, drag your mouse on the sky to draw your shape around a moving dot, and enter its <b>X, Y</b> numbers below to check what you found!
            </p>
        </div>
        """)
        nx, ny, nr = st.columns(3)
        with nx:
            st.session_state.x_pick = st.number_input("Manual Pixel X (0-299)", 0, 299, int(st.session_state.x_pick))
        with ny:
            st.session_state.y_pick = st.number_input("Manual Pixel Y (0-299)", 0, 299, int(st.session_state.y_pick))
        with nr:
            st.session_state.r_pick = st.number_input("Selection Size (px)", 8, 60, int(st.session_state.r_pick))
        with st.expander("💡 Need a Hint? Optional Quick-Snap Helpers"):
            hc1, hc2, hc3 = st.columns(3)
            objs = sec_info["objects"]
            with hc1:
                if st.button("Snap to Hint A", use_container_width=True):
                    st.session_state.x_pick = int(objs[0]["x1"] + objs[0]["dx"] * 0.5)
                    st.session_state.y_pick = int(objs[0]["y1"] + objs[0]["dy"] * 0.5)
                    st.rerun()
            with hc2:
                if st.button("Snap to Hint B", use_container_width=True):
                    st.session_state.x_pick = int(objs[1]["x1"] + objs[1]["dx"] * 0.5)
                    st.session_state.y_pick = int(objs[1]["y1"] + objs[1]["dy"] * 0.5)
                    st.rerun()
            with hc3:
                if st.button("Test Fixed Star", use_container_width=True):
                    st.session_state.x_pick = 150
                    st.session_state.y_pick = 150
                    st.rerun()
        _, _, live_ra, live_dec = calc_sky_coords(
            st.session_state.x_pick, st.session_state.y_pick, sec_info["ra_center"], sec_info["dec_center"]
        )
        put_html(f"""
        <div style="background:#091530; border:1px solid rgba(0, 255, 157, 0.4); border-radius:10px; padding:8px 12px; margin-bottom:10px; font-size:12.5px; color:#d8f8e8;">
            🧭 <b>Selected Area Sky Coordinates (J2000):</b><br/>
            • <b>Right Ascension (RA):</b> {live_ra}<br/>
            • <b>Declination (Dec):</b> {live_dec}
        </div>
        """)
        if st.button("🔍 Check Selected Area, Measure Flux & Play Sound", use_container_width=True):
            res = analyze_sky_pick(
                sector_name=picked_sector,
                pass_a=pass_a,
                pass_b=pass_b,
                cx=int(st.session_state.x_pick),
                cy=int(st.session_state.y_pick),
                rad_px=int(st.session_state.r_pick),
                shape_used=shape_mode,
                pic_a=pic_a,
                pic_b=pic_b,
                custom_mode=custom_active
            )
            st.session_state.last_result = res
            st.session_state.total_score += res["points"]
            st.session_state.saved_scores[st.session_state.explorerName] = st.session_state.total_score
            pts_txt = f"+{res['points']}" if res["points"] > 0 else f"{res['points']}"
            st.session_state.score_table.insert(0, {
                "Username": st.session_state.explorerName,
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Data Source": source_mode if custom_active else "Simulated SPHEREx Demo",
                "Set Used": picked_sector,
                "Observation Dates": f"{res['date_a']} vs {res['date_b']}",
                "Pixels (X, Y)": f"({st.session_state.x_pick}, {st.session_state.y_pick}) | {shape_mode} r={st.session_state.r_pick}px",
                "Celestial Coords (RA, Dec J2000)": f"RA: {res['ra_str']} | Dec: {res['dec_str']}",
                "Found Anomaly or Not": res["found_flag"],
                "Candidate Status": res["status"],
                "Found What": res["title"],
                "Brightness & Flux": res["flux_text"],
                "Points": pts_txt,
                "Total Score": st.session_state.total_score,
                "Physical Properties": f"{res['distance']} | {res['temp']} | {res['shift_text']}",
                "Sonification": f"{res['freq']} Hz Doppler Sound (Flux {res['peak_flux']})"
            })
        if st.session_state.last_result is not None:
            r = st.session_state.last_result
            b_col = "#00ff9d" if r["points"] > 0 else "#fc3d21"
            p_tag = f"+{r['points']} Points!" if r["points"] > 0 else f"{r['points']} Points"
            put_html(f"""
            <div class="exo-card" style="border-color:{b_col}; padding:14px 16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                    <span style="font-weight:900; font-size:15.5px; color:{b_col};">{r['title']}</span>
                    <span class="exo-badge" style="background:{b_col}; color:#040814; margin-bottom:0;">{p_tag}</span>
                </div>
                <div style="margin-top:6px; padding:4px 10px; background:rgba(255, 209, 102, 0.14); border-left:3px solid #ffd166; font-size:12px; color:#ffd166; font-weight:700;">
                    📋 Status: {r['status']}
                </div>
                <p style="font-size:13px; color:#e2eeff; margin:8px 0;">{r['note']}</p>
                <div style="font-size:12.5px; color:#b8d8ff; line-height:1.6;">
                    • <b>J2000 Sky Coords:</b> RA {r['ra_str']} | Dec {r['dec_str']}<br/>
                    • <b>Observation Times:</b> {r['date_a']} -> {r['date_b']}<br/>
                    • <b>Brightness / Flux:</b> {r['flux_text']}<br/>
                    • <b>Measured Shift:</b> {r['shift_text']}<br/>
                    • <b>Physical Properties:</b> {r['distance']} | {r['temp']} | {r['mass']}
                </div>
            </div>
            """)
            wav_clip = create_doppler_wav(
                freq_hz=float(r["freq"]),
                flux_val=float(r["peak_flux"]),
                is_planet_x=("Planet X" in r["kind"])
            )
            st.audio(wav_clip, format="audio/wav")
    st.write("")
    put_html("""
    <div class="exo-card" style="padding:14px 18px;">
        <div style="color:#ffd166; font-weight:900; font-size:18px;">🏆 Live Explorer Scoreboard & Discovery Log</div>
        <div style="font-size:13px; color:#c8dcff;">Records your scans once you start playing! If you switch users and log back in, your previous discoveries stay saved here.</div>
    </div>
    """)
    if len(st.session_state.score_table) == 0:
        st.info("🌌 No scans recorded yet in this session! Select an area on the sky image above and click 'Check Selected Area, Measure Flux & Play Sound' to add your first entry to the scoreboard.")
    else:
        df_out = pd.DataFrame(st.session_state.score_table)
        st.dataframe(df_out, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Download Scoreboard Log (CSV)",
            data=df_out.to_csv(index=False).encode("utf-8"),
            file_name="exomapper_scoreboard.csv",
            mime="text/csv"
        )
apply_space_theme()
if st.session_state.page_step == "welcome":
    show_welcome_screen()
elif st.session_state.page_step == "manual":
    show_manual_screen()
else:
    show_game_screen()

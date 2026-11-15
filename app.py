# ExoMapper: The Hunt for Planet X & SPHEREx Observatory
# NASA Space Apps Challenge 2026 | Team ExoMapper
# Coded by Shikshita Naryal, Ayan Agarwal & Mahesh Nayak

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

# puts multiline html on one single line so streamlit never renders raw </div> tags
def render_html_snippet(html_text):
    clean_line = " ".join(line.strip() for line in html_text.splitlines() if line.strip())
    st.markdown(clean_line, unsafe_allow_html=True)

# official NASA meatball logo as base64 svg
def get_nasa_logo_svg():
    svg_data = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 200" width="110" height="92">'
        '<defs><radialGradient id="nb" cx="38%" cy="32%" r="68%">'
        '<stop offset="0%" stop-color="#1b56b3"/><stop offset="55%" stop-color="#0b3d91"/>'
        '<stop offset="100%" stop-color="#061f4a"/></radialGradient></defs>'
        '<circle cx="118" cy="100" r="82" fill="url(#nb)" stroke="#60a5fa" stroke-width="2" stroke-opacity="0.6"/>'
        '<g fill="#ffffff"><circle cx="72" cy="48" r="1.8"/><circle cx="88" cy="36" r="1.4"/>'
        '<circle cx="105" cy="46" r="1.6"/><circle cx="145" cy="42" r="1.9"/><circle cx="164" cy="56" r="1.4"/>'
        '<circle cx="155" cy="72" r="1.5"/><circle cx="62" cy="132" r="1.7"/><circle cx="78" cy="148" r="1.3"/>'
        '<circle cx="96" cy="162" r="1.8"/><circle cx="148" cy="154" r="1.6"/><circle cx="168" cy="136" r="1.4"/>'
        '<circle cx="132" cy="166" r="1.3"/></g>'
        '<ellipse cx="118" cy="102" rx="74" ry="26" fill="none" stroke="#ffffff" stroke-width="2.8" '
        'stroke-dasharray="180 65" transform="rotate(-24 118 102)"/>'
        '<path d="M 30 136 Q 112 96 172 34 L 142 104 Q 176 74 214 60 Q 162 84 126 128 L 154 58 Q 104 106 30 136 Z" fill="#fc3d21"/>'
        '<text x="118" y="113" text-anchor="middle" fill="#ffffff" font-family="Georgia, serif" font-weight="900" font-size="44" letter-spacing="3">NASA</text>'
        '<ellipse cx="118" cy="102" rx="74" ry="26" fill="none" stroke="#ffffff" stroke-width="2.8" '
        'stroke-dasharray="55 200" stroke-dashoffset="-195" transform="rotate(-24 118 102)"/>'
        '<circle cx="184" cy="73" r="3.8" fill="#ffffff"/></svg>'
    )
    encoded_svg = base64.b64encode(svg_data.encode("utf-8")).decode("utf-8")
    return "data:image/svg+xml;base64," + encoded_svg

def apply_custom_space_styling():
    stylesheet = """
    <style>
    @keyframes starfieldDrift {
        from { background-position: 0px 0px, 0px 0px, 0px 0px; }
        to { background-position: 1200px 700px, -900px 1000px, 600px -800px; }
    }
    @keyframes floatAnimation {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-8px) rotate(3deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }
    @keyframes borderGlow {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.25); border-color: rgba(0, 212, 255, 0.45); }
        50% { box-shadow: 0 0 34px rgba(252, 61, 33, 0.42); border-color: rgba(252, 61, 33, 0.72); }
    }
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #030611 !important;
        color: #f2f6ff !important;
        font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    }
    .stApp {
        background-image:
            radial-gradient(2px 2px at 40px 60px, #ffffff, rgba(0,0,0,0)),
            radial-gradient(1.8px 1.8px at 190px 140px, #9be2ff, rgba(0,0,0,0)),
            radial-gradient(2.2px 2.2px at 340px 270px, #ffd59e, rgba(0,0,0,0)),
            radial-gradient(1.5px 1.5px at 520px 90px, #ffffff, rgba(0,0,0,0)),
            radial-gradient(2px 2px at 680px 320px, #b8d8ff, rgba(0,0,0,0)),
            radial-gradient(circle at 18% 22%, rgba(11, 61, 145, 0.30) 0%, transparent 48%),
            radial-gradient(circle at 82% 76%, rgba(252, 61, 33, 0.18) 0%, transparent 45%);
        background-size: 550px 420px, 470px 490px, 620px 510px, 710px 640px, 530px 580px, 100% 100%, 100% 100%;
        animation: starfieldDrift 90s linear infinite;
        background-attachment: fixed;
    }
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background: linear-gradient(180deg, #050a18 0%, #0a142d 100%) !important;
        border-right: 1px solid rgba(56, 189, 248, 0.35) !important;
        color: #ffffff !important;
    }
    div[data-baseweb="input"],
    div[data-baseweb="base-input"],
    div[data-baseweb="select"] > div,
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div[role="button"] {
        background-color: #0b1632 !important;
        color: #ffffff !important;
        border: 1.5px solid #38bdf8 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }
    .stTextInput input::placeholder {
        color: #8ab4f8 !important;
        opacity: 0.85 !important;
    }
    div[data-baseweb="popover"], ul[role="listbox"], li[role="option"] {
        background-color: #0b1632 !important;
        color: #ffffff !important;
    }
    div[data-testid="stExpander"] {
        background-color: #081126 !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        border-radius: 12px !important;
    }
    label, .stMarkdown p, .stRadio label, .stCheckbox label {
        color: #eef5ff !important;
    }
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #0b3d91 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: 1.5px solid #38bdf8 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        padding: 0.58rem 1.15rem !important;
        box-shadow: 0 4px 16px rgba(56, 189, 248, 0.28) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #fc3d21 0%, #e11d48 100%) !important;
        border-color: #facc15 !important;
        transform: translateY(-1px) !important;
    }
    .space-panel, .exo-card {
        background: linear-gradient(145deg, rgba(10, 21, 48, 0.94), rgba(6, 12, 28, 0.97));
        border: 1.5px solid rgba(56, 189, 248, 0.38);
        border-radius: 15px;
        padding: 16px 18px;
        margin-bottom: 14px;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.65);
    }
    .space-panel:hover, .exo-card:hover {
        border-color: #38bdf8;
    }
    .space-tag, .exo-badge {
        display: inline-block;
        background: #fc3d21;
        color: #ffffff;
        font-weight: 800;
        font-size: 11.5px;
        padding: 4px 14px;
        border-radius: 99px;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .exo-sim-pill {
        display: inline-block;
        background: rgba(250, 204, 21, 0.16);
        border: 1px solid #facc15;
        color: #facc15;
        font-weight: 800;
        font-size: 11.5px;
        padding: 4px 12px;
        border-radius: 99px;
    }
    .exo-real-pill {
        display: inline-block;
        background: rgba(52, 211, 153, 0.16);
        border: 1px solid #34d399;
        color: #34d399;
        font-weight: 800;
        font-size: 11.5px;
        padding: 4px 12px;
        border-radius: 99px;
    }
    .floating-celebration {
        animation: floatAnimation 3s ease-in-out infinite;
        display: inline-block;
        font-size: 26px;
    }
    .resource-link, .exo-link-btn {
        display: inline-block;
        margin-top: 6px;
        margin-right: 6px;
        padding: 6px 12px;
        background: rgba(11, 61, 145, 0.78);
        border: 1.5px solid #38bdf8;
        border-radius: 8px;
        color: #7ce8ff !important;
        text-decoration: none !important;
        font-size: 12.5px;
        font-weight: 700;
    }
    .resource-link:hover, .exo-link-btn:hover {
        background: #fc3d21;
        color: #ffffff !important;
        border-color: #facc15;
    }
    @media (max-width: 768px) {
        .space-panel, .exo-card { padding: 12px; }
        h1 { font-size: 23px !important; }
        h2 { font-size: 17px !important; }
    }
    </style>
    """
    render_html_snippet(stylesheet)

ARCSEC_PER_PIXEL = 6.2

# All 4 sky sectors with 3 observation passes each
celestialSectors = {
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

def get_preloaded_archive_dataframe():
    data = [
        {"Dataset_ID": "SPX-DR1-074", "Survey": "SPHEREx Level-2 All-Sky", "Target": "WISE 0855-0714", "RA_J2000": "08h 55m 10.8s", "Dec_J2000": "-07d 14m 42s", "Wavelength": "4.52 um", "Format": "FITS", "Status": "Calibrated & Ready"},
        {"Dataset_ID": "SPX-DR1-089", "Survey": "SPHEREx Level-2 All-Sky", "Target": "Barnard's Star", "RA_J2000": "17h 57m 48.5s", "Dec_J2000": "+04d 41m 36s", "Wavelength": "3.82 um", "Format": "FITS", "Status": "Calibrated & Ready"}
    ]
    return pd.DataFrame(data)

def calculate_sky_coordinates(px, py, ra_center, dec_center):
    dx_arcsec = (150.0 - float(px)) * ARCSEC_PER_PIXEL
    dy_arcsec = (150.0 - float(py)) * ARCSEC_PER_PIXEL
    cos_declination = max(0.1, abs(math.cos(math.radians(dec_center))))
    ra_val = (ra_center + (dx_arcsec / 3600.0) / cos_declination) % 360.0
    dec_val = max(-89.99, min(89.99, dec_center + (dy_arcsec / 3600.0)))

    hours = ra_val / 15.0
    rh = int(hours)
    rm = int((hours - rh) * 60.0)
    rs = ((hours - rh) * 60.0 - rm) * 60.0
    ra_str = f"{rh:02d}h {rm:02d}m {rs:04.1f}s ({ra_val:.4f} deg)"

    sign = "+" if dec_val >= 0 else "-"
    abs_dec = abs(dec_val)
    dd = int(abs_dec)
    dm = int((abs_dec - dd) * 60.0)
    ds = ((abs_dec - dd) * 60.0 - dm) * 60.0
    dec_str = f"{sign}{dd:02d}d {dm:02d}m {ds:04.1f}s ({dec_val:+.4f} deg)"
    return ra_val, dec_val, ra_str, dec_str

def draw_star_gaussian(grid, cx, cy, intensity, spread=2.1):
    h, w = grid.shape
    radius = int(max(6, spread * 4))
    x_min, x_max = max(0, int(cx) - radius), min(w, int(cx) + radius + 1)
    y_min, y_max = max(0, int(cy) - radius), min(h, int(cy) + radius + 1)
    if x_min >= x_max or y_min >= y_max:
        return
    yy, xx = np.ogrid[y_min:y_max, x_min:x_max]
    dist_sq = (xx - cx) ** 2 + (yy - cy) ** 2
    grid[y_min:y_max, x_min:x_max] += intensity * np.exp(-dist_sq / (2.0 * spread ** 2))

@st.cache_data(show_spinner=False)
def generate_sky_grid_pair(sector_name, epoch_a_key, epoch_b_key, clean_enabled=False):
    sector = celestialSectors[sector_name]
    rng_generator = np.random.default_rng(sector["seed"])
    grid_size = 300
    step_a = sector["epochs"][epoch_a_key]["step"]
    step_b = sector["epochs"][epoch_b_key]["step"]

    yy, xx = np.mgrid[0:grid_size, 0:grid_size]
    ambient_glow = 0.04 * np.sin(xx / 38.0) * np.cos(yy / 44.0) + 0.05

    grid_a = np.zeros((grid_size, grid_size), dtype=np.float32)
    grid_b = np.zeros((grid_size, grid_size), dtype=np.float32)

    star_x = rng_generator.uniform(8, grid_size - 8, 170)
    star_y = rng_generator.uniform(8, grid_size - 8, 170)
    star_flux = rng_generator.uniform(0.18, 0.85, 170)
    star_spread = rng_generator.uniform(1.3, 2.2, 170)
    for sx, sy, sf, ss in zip(star_x, star_y, star_flux, star_spread):
        draw_star_gaussian(grid_a, sx, sy, sf, ss)
        draw_star_gaussian(grid_b, sx, sy, sf, ss)

    for obj in sector["objects"]:
        xa = obj["x1"] + obj["dx"] * step_a
        ya = obj["y1"] + obj["dy"] * step_a
        xb = obj["x1"] + obj["dx"] * step_b
        yb = obj["y1"] + obj["dy"] * step_b
        if "Planet X" in obj["kind"] or "Brown Dwarf" in obj["kind"]:
            draw_star_gaussian(grid_a, xa, ya, obj["amp"], 2.5)
            draw_star_gaussian(grid_b, xb, yb, obj["amp"], 2.5)
        else:
            amp_a = obj["amp"] * (0.22 if step_a == 0 else 0.65)
            amp_b = obj["amp"] * (1.0 if step_b >= 1.0 else 0.25)
            draw_star_gaussian(grid_a, xa, ya, amp_a, 2.0)
            draw_star_gaussian(grid_b, xb, yb, amp_b, 2.7)

    noise_a = rng_generator.normal(0.0, 0.028, (grid_size, grid_size)).astype(np.float32)
    noise_b = rng_generator.normal(0.0, 0.028, (grid_size, grid_size)).astype(np.float32)
    if not clean_enabled:
        grid_a = grid_a + ambient_glow + noise_a
        grid_b = grid_b + ambient_glow + noise_b
    else:
        grid_a = grid_a + noise_a * 0.30
        grid_b = grid_b + noise_b * 0.30
    return np.clip(grid_a, 0.0, 1.35), np.clip(grid_b, 0.0, 1.35)

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
    return hdr_bytes + raw_data + bytes(pad_data)

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
            draw_star_gaussian(pic_a, x1, y1, a1, 2.3)
            draw_star_gaussian(pic_b, x2, y2, a2, 2.3)

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

def colorize_sky_image(array_grid, palette="Deep Space Cyan", brightness=1.0, contrast=1.0, is_difference=False):
    if is_difference:
        diff_scaled = array_grid * contrast * 2.4
        pos_channel = np.clip(diff_scaled, 0.0, 1.0)
        neg_channel = np.clip(-diff_scaled, 0.0, 1.0)
        r = np.clip(6 + pos_channel * 249, 0, 255).astype(np.uint8)
        g = np.clip(10 + pos_channel * 165 + neg_channel * 210, 0, 255).astype(np.uint8)
        b = np.clip(22 + pos_channel * 30 + neg_channel * 255, 0, 255).astype(np.uint8)
        return Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")
    adjusted = np.clip((array_grid - 0.15) * contrast + 0.15, 0.0, 1.2) * brightness
    val = np.clip(adjusted, 0.0, 1.0)
    if palette == "Infrared Heat (SPHEREx)":
        r = np.clip(8 + (val ** 0.75) * 247, 0, 255).astype(np.uint8)
        g = np.clip(10 + (val ** 1.35) * 195, 0, 255).astype(np.uint8)
        b = np.clip(26 + (val ** 2.2) * 140, 0, 255).astype(np.uint8)
    elif palette == "Emerald Nebula":
        r = np.clip(6 + (val ** 1.7) * 150, 0, 255).astype(np.uint8)
        g = np.clip(14 + (val ** 0.8) * 240, 0, 255).astype(np.uint8)
        b = np.clip(24 + (val ** 1.2) * 195, 0, 255).astype(np.uint8)
    else:
        r = np.clip(6 + (val ** 1.5) * 225, 0, 255).astype(np.uint8)
        g = np.clip(12 + (val ** 0.95) * 238, 0, 255).astype(np.uint8)
        b = np.clip(28 + (val ** 0.70) * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode="RGB")

def generate_doppler_audio(freq_hz, flux_value, is_planet_x=False):
    sample_rate = 22050
    duration_secs = 2.0
    total_samples = int(sample_rate * duration_secs)
    buffer_io = io.BytesIO()
    with wave.open(buffer_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        pcm_bytes = bytearray()
        for i in range(total_samples):
            t = i / sample_rate
            envelope = math.sin(math.pi * t / duration_secs) ** 0.45
            if is_planet_x:
                f = freq_hz + 140.0 * math.sin(2.0 * math.pi * 1.5 * t) + 85.0 * t
                tone2 = 0.35 * math.sin(2.0 * math.pi * (f * 1.5) * t)
            else:
                f = freq_hz + 35.0 * math.cos(2.0 * math.pi * 3.0 * t)
                tone2 = 0.20 * math.sin(2.0 * math.pi * (f * 2.0) * t)
            signal = envelope * min(1.0, max(0.35, flux_value)) * (0.65 * math.sin(2.0 * math.pi * f * t) + tone2)
            sample_val = int(max(-32767, min(32767, signal * 26000)))
            pcm_bytes += sample_val.to_bytes(2, byteorder="little", signed=True)
        wav_file.writeframes(bytes(pcm_bytes))
    return buffer_io.getvalue()

def evaluate_user_sky_pick(sector_name, pass_a, pass_b, cx, cy, radius_px, grid_a, grid_b, custom_mode=False):
    sector = celestialSectors[sector_name]
    _, _, ra_str, dec_str = calculate_sky_coordinates(cx, cy, sector["ra_center"], sector["dec_center"])
    ep_a = sector["epochs"][pass_a]
    ep_b = sector["epochs"][pass_b]
    time_gap_days = max(1, abs(ep_b["days"] - ep_a["days"]))
    r = max(5, int(radius_px))
    x0, x1 = max(0, cx - r), min(299, cx + r)
    y0, y1 = max(0, cy - r), min(299, cy + r)
    sub_a = grid_a[y0:y1 + 1, x0:x1 + 1]
    sub_b = grid_b[y0:y1 + 1, x0:x1 + 1]
    peak_a = float(np.max(sub_a))
    peak_b = float(np.max(sub_b))
    max_peak = max(peak_a, peak_b)
    noise_level = float(max(0.015, np.std(grid_a)))
    snr = round(float(np.max(np.abs(sub_b - sub_a))) / noise_level, 1)
    mjy_a = round(peak_a * 15.0, 2)
    mjy_b = round(peak_b * 15.0, 2)
    best_mjy = max(0.05, mjy_a, mjy_b)
    ab_magnitude = round(-2.5 * math.log10(best_mjy / 3631000.0), 2)

    matched_object = None
    min_distance = 999.0
    if not custom_mode:
        for obj in sector["objects"]:
            xa = obj["x1"] + obj["dx"] * ep_a["step"]
            ya = obj["y1"] + obj["dy"] * ep_a["step"]
            xb = obj["x1"] + obj["dx"] * ep_b["step"]
            yb = obj["y1"] + obj["dy"] * ep_b["step"]
            dist = min(math.hypot(cx - xa, cy - ya), math.hypot(cx - xb, cy - yb))
            if dist <= max(18.0, radius_px * 1.15) and dist < min_distance:
                min_distance = dist
                matched_object = (obj, xa, ya, xb, yb)

    if matched_object is not None:
        obj, xa, ya, xb, yb = matched_object
        pixel_shift = round(math.hypot(xb - xa, yb - ya), 1)
        arcsec_shift = round(pixel_shift * ARCSEC_PER_PIXEL, 1)
        daily_motion = round(arcsec_shift / time_gap_days, 3)
        f1 = obj["flux_e1"]
        f2 = obj["flux_e2"] if ep_b["step"] != ep_a["step"] else obj["flux_e1"]
        pct_change = round(((f2 - f1) / max(0.1, f1)) * 100.0, 1)
        return {
            "found_flag": "YES (Candidate Anomaly Logged)",
            "title": obj["name"],
            "kind": obj["kind"],
            "status": obj["status"],
            "points": obj["points"],
            "ra_str": ra_str,
            "dec_str": dec_str,
            "date_a": ep_a["label"],
            "date_b": ep_b["label"],
            "distance": obj["distance"],
            "temp": obj["temp"],
            "mass": obj["mass"],
            "wavelength": obj["wavelength"],
            "shift_text": f"{pixel_shift} px ({arcsec_shift} arcsec | {daily_motion} arcsec/day over {time_gap_days}d)",
            "flux_text": f"Image A: {f1} mJy -> Image B: {f2} mJy ({pct_change:+.1f}%) | Mag: {ab_magnitude} AB | SNR: {max(snr, 14.0)} sigma",
            "peak_flux": round(max_peak, 3),
            "freq": obj["freq"],
            "note": obj["note"],
            "snr_val": max(snr, 14.0),
            "arcsec_val": arcsec_shift
        }

    if custom_mode and snr >= 5.0:
        pct_change = round(((mjy_b - mjy_a) / max(0.1, mjy_a)) * 100.0, 1)
        return {
            "found_flag": "YES (Custom File Candidate)",
            "title": "Unconfirmed Moving / Variable Candidate (Uploaded Data)",
            "kind": "Planet X Candidate",
            "status": "UNCONFIRMED CANDIDATE (Needs Follow-Up Observation)",
            "points": 120,
            "ra_str": ra_str,
            "dec_str": dec_str,
            "date_a": "Custom File Epoch 1",
            "date_b": "Custom File Epoch 2",
            "distance": "Requires 3rd-Epoch Parallax Fit",
            "temp": "Pending Multi-Band IR Check",
            "mass": "Pending Thermal Model",
            "wavelength": "Uploaded Survey Band",
            "shift_text": f"Detected {snr} sigma change inside selected area",
            "flux_text": f"Image A: {mjy_a} mJy -> Image B: {mjy_b} mJy ({pct_change:+.1f}%) | Mag: {ab_magnitude} AB | SNR: {snr} sigma",
            "peak_flux": round(max_peak, 3),
            "freq": 520,
            "note": f"Your selected region shows a strong ({snr} sigma) change between Image A and Image B! Logged as an unconfirmed candidate.",
            "snr_val": snr,
            "arcsec_val": round(r * 0.8 * ARCSEC_PER_PIXEL, 1)
        }

    return {
        "found_flag": "NO (Fixed Star or Noise)",
        "title": "False Alarm (Stationary Star or Background Noise)",
        "kind": "False Alarm",
        "status": "REJECTED (Fixed Background Star / Sensor Noise)",
        "points": -20,
        "ra_str": ra_str,
        "dec_str": dec_str,
        "date_a": ep_a["label"],
        "date_b": ep_b["label"],
        "distance": ">1,000 Light-Years (Background Star)",
        "temp": "~4,800 K (Normal Star)",
        "mass": "~1.0 Solar Mass",
        "wavelength": sector["band"],
        "shift_text": "0.0 px (0.0 arcsec shift)",
        "flux_text": f"Image A: {mjy_a} mJy -> Image B: {mjy_b} mJy (Steady) | Mag: {ab_magnitude} AB | SNR: {snr} sigma",
        "peak_flux": round(max_peak, 3),
        "freq": 240,
        "note": "Better luck next time! The pixels inside your selected area stayed in the same place. Keep scanning!",
        "snr_val": snr,
        "arcsec_val": 0.0
    }

def image_to_base64_string(pil_image):
    stream = io.BytesIO()
    pil_image.save(stream, format="PNG")
    return base64.b64encode(stream.getvalue()).decode("utf-8")

def render_interactive_canvas(b64_a, b64_b, b64_sub, mode_name, shape_name, blink_ms, mx, my, mr, ra_center, dec_center, label_a, label_b, active_frame):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            margin: 0;
            padding: 4px;
            background: #030611;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            text-align: center;
        }}
        .observatory-box {{
            display: inline-block;
            width: 100%;
            max-width: 480px;
            background: #040816;
            border: 2px solid #38bdf8;
            border-radius: 14px;
            padding: 8px;
            box-sizing: border-box;
            box-shadow: 0 0 25px rgba(56, 189, 248, 0.3);
        }}
        canvas {{
            width: 100% !important;
            height: auto !important;
            max-width: 460px;
            max-height: 460px;
            border-radius: 8px;
            cursor: crosshair;
            display: block;
            margin: 0 auto;
            background: #040816;
            touch-action: none;
        }}
        .toolbar-row {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 6px;
            margin-top: 8px;
        }}
        .tool-btn {{
            background: linear-gradient(135deg, #0b3d91, #1d4ed8);
            color: #ffffff;
            border: 1px solid #38bdf8;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 11.5px;
            font-weight: 700;
            cursor: pointer;
        }}
        .tool-btn:hover {{
            background: #fc3d21;
            border-color: #facc15;
        }}
        .status-row {{
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 4px;
            margin-top: 6px;
            padding: 5px 8px;
            background: #0b132b;
            border: 1px solid rgba(56, 189, 248, 0.4);
            border-radius: 6px;
            font-size: 11.5px;
            font-weight: 700;
            color: #ffffff;
        }}
    </style>
    </head>
    <body>
        <div class="observatory-box" title="Click or touch and drag on the sky image to manually select any area!">
            <canvas id="skyCanvas" width="460" height="460"></canvas>
            <div class="toolbar-row">
                <button class="tool-btn" id="btnManualFlip">⚡ Blink Manually (Flip A ↔ B)</button>
                <button class="tool-btn" id="btnPauseResume">⏸️ Pause / ▶️ Resume Blink</button>
                <button class="tool-btn" id="btnShowSub">🌗 Toggle Subtraction View</button>
            </div>
            <div class="status-row">
                <span id="frameInfo" style="color: #38bdf8;">Loading Sky...</span>
                <span id="pixelInfo" style="color: #facc15;">Area: X={mx}, Y={my} (Size={mr}px)</span>
            </div>
            <div class="status-row" style="margin-top:4px;">
                <span id="radecInfo" style="color: #34d399;">J2000 RA / Dec</span>
                <span style="color:#b8d8ff; font-size:10.5px;">Touch or drag on image to select area</span>
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
        let currentFrame = {active_frame};
        let currentMode = "{mode_name}";
        const currentShape = "{shape_name}";
        const blinkInterval = {blink_ms};
        const raCenter = {ra_center};
        const decCenter = {dec_center};
        const labelA = "{label_a}";
        const labelB = "{label_b}";
        let pausedState = (currentMode !== "Auto Blink Images");
        let canvasScale = 460 / 300;
        let selectedX = {mx};
        let selectedY = {my};
        let selectedRadius = {mr};
        let isDragging = false;

        function computeRaDec(px, py) {{
            const dxArc = (150.0 - px) * 6.2;
            const dyArc = (150.0 - py) * 6.2;
            const cosD = Math.max(0.1, Math.abs(Math.cos(decCenter * Math.PI / 180.0)));
            const ra = ((raCenter + (dxArc / 3600.0) / cosD) % 360.0 + 360.0) % 360.0;
            const dec = Math.max(-89.99, Math.min(89.99, decCenter + (dyArc / 3600.0)));
            return "RA: " + ra.toFixed(4) + " deg | Dec: " + (dec >= 0 ? "+" : "") + dec.toFixed(4) + " deg";
        }}
        function updateParentInputs(x, y, r) {{
            try {{
                const doc = window.parent.document;
                const inputs = doc.querySelectorAll('input[type="number"]');
                if (inputs.length >= 3) {{
                    inputs[0].value = x; inputs[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[1].value = y; inputs[1].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    inputs[2].value = r; inputs[2].dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }} catch(err) {{}}
        }}
        function refreshLabels() {{
            pixelInfo.textContent = "Area: X=" + selectedX + ", Y=" + selectedY + " | Size=" + selectedRadius + "px";
            radecInfo.textContent = computeRaDec(selectedX, selectedY);
        }}
        function redrawCanvas() {{
            ctx.clearRect(0, 0, 460, 460);
            if (currentMode === "Subtraction Map (Image B - Image A)") {{
                ctx.drawImage(imgSub, 0, 0, 460, 460);
                frameInfo.textContent = "Subtraction Map (Cyan=A, Gold=B)";
            }} else if (currentMode === "Pause on Image A") {{
                ctx.drawImage(imgA, 0, 0, 460, 460);
                frameInfo.textContent = "Paused A: " + labelA;
            }} else if (currentMode === "Pause on Image B") {{
                ctx.drawImage(imgB, 0, 0, 460, 460);
                frameInfo.textContent = "Paused B: " + labelB;
            }} else {{
                if (currentFrame === 1) {{
                    ctx.drawImage(imgA, 0, 0, 460, 460);
                    frameInfo.textContent = (pausedState ? "Paused A: " : "Blinking A: ") + labelA;
                }} else {{
                    ctx.drawImage(imgB, 0, 0, 460, 460);
                    frameInfo.textContent = (pausedState ? "Paused B: " : "Blinking B: ") + labelB;
                }}
            }}
            ctx.strokeStyle = "rgba(56, 189, 248, 0.15)";
            ctx.lineWidth = 1;
            for (let g = 57; g < 460; g += 57) {{
                ctx.beginPath(); ctx.moveTo(g, 0); ctx.lineTo(g, 460); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(0, g); ctx.lineTo(460, g); ctx.stroke();
            }}
            const s = 460 / 300;
            const cx = selectedX * s;
            const cy = selectedY * s;
            const cr = selectedRadius * s;
            ctx.strokeStyle = "#facc15";
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            if (currentShape === "Draw Circle") {{
                ctx.arc(cx, cy, cr, 0, Math.PI * 2);
            }} else if (currentShape === "Draw Square") {{
                ctx.rect(cx - cr, cy - cr, cr * 2, cr * 2);
            }} else {{
                ctx.rect(cx - cr * 1.35, cy - cr * 0.85, cr * 2.7, cr * 1.7);
            }}
            ctx.stroke();
            ctx.strokeStyle = "#f43f5e";
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(cx - 8, cy); ctx.lineTo(cx + 8, cy);
            ctx.moveTo(cx, cy - 8); ctx.lineTo(cx, cy + 8);
            ctx.stroke();
        }}
        document.getElementById('btnManualFlip').addEventListener('click', () => {{
            pausedState = true;
            if (currentMode === "Subtraction Map (Image B - Image A)" || currentMode === "Pause on Image A" || currentMode === "Pause on Image B") {{
                currentMode = "Manual Blink (Step-by-Step)";
            }}
            currentFrame = (currentFrame === 1) ? 2 : 1;
            redrawCanvas();
        }});
        document.getElementById('btnPauseResume').addEventListener('click', () => {{
            if (currentMode === "Subtraction Map (Image B - Image A)") {{
                currentMode = "Auto Blink Images";
                pausedState = false;
            }} else {{
                pausedState = !pausedState;
                if (!pausedState) currentMode = "Auto Blink Images";
            }}
            redrawCanvas();
        }});
        document.getElementById('btnShowSub').addEventListener('click', () => {{
            if (currentMode === "Subtraction Map (Image B - Image A)") {{
                currentMode = "Manual Blink (Step-by-Step)";
                pausedState = true;
            }} else {{
                currentMode = "Subtraction Map (Image B - Image A)";
                pausedState = true;
            }}
            redrawCanvas();
        }});

        function getClientPos(e) {{
            const rect = canvas.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            return {{
                x: Math.max(0, Math.min(299, Math.round((clientX - rect.left) * (300 / rect.width)))),
                y: Math.max(0, Math.min(299, Math.round((clientY - rect.top) * (300 / rect.height))))
            }};
        }}

        canvas.addEventListener('mousedown', (e) => {{
            const pt = getClientPos(e);
            selectedX = pt.x; selectedY = pt.y;
            isDragging = true;
            refreshLabels(); redrawCanvas();
        }});
        canvas.addEventListener('mousemove', (e) => {{
            if (!isDragging) return;
            const pt = getClientPos(e);
            const dist = Math.round(Math.hypot(pt.x - selectedX, pt.y - selectedY));
            selectedRadius = Math.max(8, Math.min(60, dist));
            refreshLabels(); redrawCanvas();
        }});
        window.addEventListener('mouseup', () => {{
            if (isDragging) {{ isDragging = false; updateParentInputs(selectedX, selectedY, selectedRadius); }}
        }});

        canvas.addEventListener('touchstart', (e) => {{
            const pt = getClientPos(e);
            selectedX = pt.x; selectedY = pt.y;
            isDragging = true;
            refreshLabels(); redrawCanvas();
            e.preventDefault();
        }}, {{ passive: false }});
        canvas.addEventListener('touchmove', (e) => {{
            if (!isDragging) return;
            const pt = getClientPos(e);
            const dist = Math.round(Math.hypot(pt.x - selectedX, pt.y - selectedY));
            selectedRadius = Math.max(8, Math.min(60, dist));
            refreshLabels(); redrawCanvas();
            e.preventDefault();
        }}, {{ passive: false }});
        window.addEventListener('touchend', () => {{
            if (isDragging) {{ isDragging = false; updateParentInputs(selectedX, selectedY, selectedRadius); }}
        }});

        refreshLabels();
        imgA.onload = redrawCanvas;
        imgB.onload = redrawCanvas;
        setInterval(() => {{
            if (!pausedState && currentMode === "Auto Blink Images") {{
                currentFrame = (currentFrame === 1) ? 2 : 1;
                redrawCanvas();
            }}
        }}, blinkInterval);
        </script>
    </body>
    </html>
    """

# Session state setup (Scoreboard starts empty and only fills when playing!)
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

# SCREEN 1: WELCOME PAGE
def show_welcome_screen():
    logo_uri = get_nasa_logo_svg()
    st.write("")
    st.write("")
    col1, col2, col3 = st.columns([1.0, 2.3, 1.0])
    with col2:
        render_html_snippet(f"""
        <div class="space-panel" style="text-align:center; padding:32px 24px;" title="Welcome to ExoMapper! Enter your Space Explorer Name below.">
            <img src="{logo_uri}" alt="Official NASA Logo" style="width:110px; height:auto; margin-bottom:10px; filter: drop-shadow(0 4px 14px rgba(56,189,248,0.5));"/>
            <div>
                <span class="space-tag">NASA SPACE APPS CHALLENGE 2026 • TEAM EXOMAPPER</span>
            </div>
            <h1 style="margin:8px 0 4px 0; font-size:31px; font-weight:900; color:#ffffff;">
                Welcome to ExoMapper: The Hunt for Planet X
            </h1>
        </div>
        """)
        username_input = st.text_input(
            "Enter Your Space Explorer Name",
            value=st.session_state.explorerName,
            placeholder="Type a cute explorer name (e.g., Nova, Sky, Riley, or Alex)...",
            help="Enter your explorer username. If you log in again after playing, your score and scans are remembered!"
        )
        if st.button("🚀 Enter", use_container_width=True, help="Open the ExoMapper User Manual & Science Briefing!"):
            cleaned_name = username_input.strip()
            if not cleaned_name:
                st.warning("Please enter your Space Explorer Name first!")
            else:
                st.session_state.explorerName = cleaned_name
                st.session_state.total_score = st.session_state.saved_scores.get(cleaned_name, 0)
                st.session_state.last_result = None
                st.session_state.page_step = "manual"
                st.rerun()

# SCREEN 2: USER MANUAL, TEAM MANIFEST & OFFICIAL LINKS
def show_manual_screen():
    logo_uri = get_nasa_logo_svg()
    top_a, top_b, top_c = st.columns([3.3, 1.3, 1.0])
    with top_a:
        render_html_snippet(f"""
        <div class="space-panel" style="display:flex; flex-wrap:wrap; align-items:center; gap:14px; padding:14px 18px;">
            <img src="{logo_uri}" alt="NASA Logo" style="width:64px; height:auto;"/>
            <div>
                <span class="space-tag" style="margin-bottom:4px;">STEP 1 OF 2 • EXOMAPPER USER MANUAL &amp; BRIEFING</span>
                <h2 style="margin:2px 0 0 0; color:#ffffff; font-size:22px; font-weight:900;">
                    Welcome, {st.session_state.explorerName}! 📖 Read the Guide &amp; Begin Your Hunt
                </h2>
            </div>
        </div>
        """)
    with top_b:
        st.write("")
        if st.button("🎮 Begin the Game ➔", use_container_width=True):
            st.session_state.page_step = "game"
            st.rerun()
    with top_c:
        st.write("")
        if st.button("🔄 Switch User", use_container_width=True):
            st.session_state.page_step = "welcome"
            st.rerun()

    # 3 Official NASA Info Cards
    c1, c2, c3 = st.columns(3)
    with c1:
        render_html_snippet("""
        <div class="space-panel" title="Planet X is a hypothetical giant world beyond Neptune. Moving dots in sky surveys are logged as unconfirmed candidates.">
            <div style="color:#facc15; font-weight:800; font-size:16px; margin-bottom:6px;">🪐 About Planet X</div>
            <p style="font-size:13px; line-height:1.5; color:#d8e6ff; margin:0;">
                Beyond Pluto, icy Kuiper Belt objects follow clustered paths that suggest a hidden giant world (<b>Planet X</b>) may be pulling on them. Because it orbits hundreds of AU away, it glows faintly in infrared light and shifts slowly across pixels over months!
            </p>
            <a class="resource-link" href="https://science.nasa.gov/solar-system/planet-x/" target="_blank">🔗 Official NASA Planet X Page</a>
        </div>
        """)
    with c2:
        render_html_snippet("""
        <div class="space-panel" title="SPHEREx maps the entire sky in 102 infrared bands every 6 months.">
            <div style="color:#38bdf8; font-weight:800; font-size:16px; margin-bottom:6px;">🛰️ About SPHEREx</div>
            <p style="font-size:13px; line-height:1.5; color:#d8e6ff; margin:0;">
                <b>SPHEREx</b> is NASA's all-sky infrared space telescope. By comparing two pictures of the exact same sky coordinates (<b>RA and Dec</b>) taken 6 months apart, we can spot objects that moved or changed brightness!
            </p>
            <a class="resource-link" href="https://science.nasa.gov/mission/spherex/" target="_blank">🔗 Official NASA SPHEREx Mission</a>
        </div>
        """)
    with c3:
        render_html_snippet("""
        <div class="space-panel" title="NASA shares public FITS files and catalogs so students can help discover new worlds.">
            <div style="color:#f43f5e; font-weight:800; font-size:16px; margin-bottom:6px;">🚀 About NASA Open Data</div>
            <p style="font-size:13px; line-height:1.5; color:#d8e6ff; margin:0;">
                <b>NASA</b> shares space telescope observations openly with students and citizen scientists. Every moving dot you find in two images is logged as an <b>Unconfirmed Candidate</b> awaiting a 3rd observation to confirm its orbit.
            </p>
            <a class="resource-link" href="https://www.nasa.gov/" target="_blank">🔗 Visit Official NASA Portal</a>
        </div>
        """)

    # 3 Game Guide Cards
    g1, g2, g3 = st.columns(3)
    with g1:
        render_html_snippet("""
        <div class="space-panel">
            <div style="color:#38bdf8; font-weight:800; font-size:15px; margin-bottom:6px;">1. Pick Images, FITS or CSV Files</div>
            <p style="font-size:13px; line-height:1.5; color:#d8e6ff; margin:0;">
                On the next page, choose any of the <b>4 Sky Sectors</b> and pick which two observation dates (Pass 1, Pass 2, or Pass 3) to compare, or upload your own <b>.FITS files</b>, <b>.CSV star catalogs</b>, or sky pictures!
            </p>
        </div>
        """)
    with g2:
        render_html_snippet("""
        <div class="space-panel">
            <div style="color:#facc15; font-weight:800; font-size:15px; margin-bottom:6px;">2. Manual Blink, Pause &amp; Select Area</div>
            <p style="font-size:13px; line-height:1.5; color:#d8e6ff; margin:0;">
                Click <b>⚡ Blink Manually (Flip A ↔ B)</b> to flip pictures at your own speed, or click <b>⏸️ Pause</b> anytime. Then drag your mouse/finger directly on the sky to encircle the moving dot!
            </p>
        </div>
        """)
    with g3:
        render_html_snippet("""
        <div class="space-panel">
            <div style="color:#34d399; font-weight:800; font-size:15px; margin-bottom:6px;">3. Points, Checklist &amp; Scoreboard</div>
            <p style="font-size:13px; line-height:1.5; color:#d8e6ff; margin:0;">
                • <b>Unconfirmed Planet X Candidate:</b> +150 pts<br/>
                • <b>Brown Dwarf / Supernova / Flare Star:</b> +70 to +85 pts<br/>
                • <b>False Alarm (Fixed Star / Noise):</b> -20 pts<br/>
                Your scoreboard updates live after your first scan!
            </p>
        </div>
        """)

    # Team Manifest Card
    render_html_snippet("""
    <div class="space-panel">
        <div style="color:#facc15; font-weight:900; font-size:16px; margin-bottom:8px;">👥 Team ExoMapper Crew Manifest</div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:10px;">
            <div style="background:#050816; border:1px solid #38bdf8; border-radius:10px; padding:10px 12px;">
                <div style="color:#38bdf8; font-weight:800; font-size:14px;">Shikshita Naryal</div>
                <div style="font-size:11.5px; color:#facc15;">Team Owner &amp; Lead Architect</div>
            </div>
            <div style="background:#050816; border:1px solid #34d399; border-radius:10px; padding:10px 12px;">
                <div style="color:#34d399; font-weight:800; font-size:14px;">Ayan Agarwal</div>
                <div style="font-size:11.5px; color:#facc15;">11th Grade // Docs &amp; UI</div>
            </div>
            <div style="background:#050816; border:1px solid #f43f5e; border-radius:10px; padding:10px 12px;">
                <div style="color:#f43f5e; font-weight:800; font-size:14px;">Mahesh Nayak</div>
                <div style="font-size:11.5px; color:#facc15;">M.Sc. Physics // Science Validation</div>
            </div>
        </div>
    </div>
    """)

    # Direct Official FITS & Archive Links
    render_html_snippet("""
    <div class="space-panel">
        <div style="color:#34d399; font-weight:900; font-size:16px; margin-bottom:6px;">📂 Direct Links to Official NASA SPHEREx &amp; Planet X Survey FITS Files (With Observation Times)</div>
        <p style="font-size:13px; color:#ffffff; margin:0 0 8px 0;">
            Click any link below to download calibrated FITS observations or open the NASA/IPAC Infrared Science Archive:
        </p>
        <a class="resource-link" href="https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W18_1B/l2b-v27-2026-196/1/level2_2025W18_1B_0074_2D1_spx_l2b-v27-2026-196.fits" target="_blank">⬇️ Direct SPHEREx DR1 Level-2 FITS (Obs Week: 2025W18_1B | Day: 2026-196 UTC)</a>
        <a class="resource-link" href="https://irsa.ipac.caltech.edu/ibe/cutouts.html" target="_blank">🛰️ NASA/IPAC IRSA FITS Cutouts Server</a>
        <a class="resource-link" href="https://skyview.gsfc.nasa.gov/cgi-bin/images?Survey=digitized+sky+survey&position=14.5,36.5&Return=FITS" target="_blank">⬇️ Direct NASA SkyView 300x300 FITS Cutout (RA=14.5 deg, Dec=+36.5 deg)</a>
        <a class="resource-link" href="https://irsa.ipac.caltech.edu/" target="_blank">🌌 NASA/IPAC Infrared Science Archive Portal</a>
    </div>
    """)

    with st.expander("📋 View Reference SPHEREx Level-2 Calibration Targets"):
        st.dataframe(get_preloaded_archive_dataframe(), use_container_width=True, hide_index=True)

    col_btn1, col_btn2, col_btn3 = st.columns([1.1, 2.0, 1.1])
    with col_btn2:
        if st.button("🚀 Begin the Game Now (Launch Interactive Sky Workbench)", use_container_width=True):
            st.session_state.page_step = "game"
            st.rerun()

# SCREEN 3: MAIN GAME & ASTROMETRIC WORKBENCH
def show_game_screen():
    logo_uri = get_nasa_logo_svg()
    h1, h2, h3 = st.columns([3.5, 1.1, 1.0])
    with h1:
        render_html_snippet(f"""
        <div class="space-panel" style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px; padding:12px 18px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="{logo_uri}" alt="NASA Logo" style="width:58px; height:auto;"/>
                <div>
                    <span class="space-tag" style="margin-bottom:2px;">EXOMAPPER SKY WORKBENCH • ACTIVE MISSION</span>
                    <h2 style="margin:2px 0 0 0; color:#ffffff; font-size:21px; font-weight:900;">
                        Explorer: {st.session_state.explorerName} 🪐 Select Sky Area &amp; Hunt for Planet X
                    </h2>
                </div>
            </div>
            <div style="text-align:right; background:#081128; border:1.5px solid #38bdf8; border-radius:10px; padding:6px 14px;">
                <div style="font-size:10.5px; color:#93c5fd; font-weight:800;">CURRENT SCORE</div>
                <div style="font-size:20px; color:#facc15; font-weight:900;">{st.session_state.total_score} PTS</div>
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
        render_html_snippet("""
        <div class="space-panel" style="padding:12px 14px;">
            <div style="color:#38bdf8; font-weight:900; font-size:15px;">🔭 Image &amp; Blink Settings</div>
            <div style="font-size:12px; color:#ffffff;">Adjust color palettes, brightness, contrast, and noise cleaning.</div>
        </div>
        """)
        color_theme = st.selectbox("Sky Color Theme", ["Deep Space Cyan", "Infrared Heat (SPHEREx)", "Emerald Nebula"])
        bright_val = st.slider("Star Brightness", 0.6, 2.0, 1.15, 0.05)
        contrast_val = st.slider("Sky Contrast", 0.6, 2.2, 1.20, 0.05)
        blink_ms = st.slider("Auto-Blink Speed (ms)", 250, 1200, 550, 50)
        clean_flag = st.checkbox("✨ Apply Dark & Bias Clean", value=False)

        render_html_snippet("""
        <div class="space-panel" style="padding:12px 14px; margin-top:10px;">
            <div style="color:#facc15; font-weight:800; font-size:14px;">🔗 Direct FITS Links (With Time)</div>
            <a class="resource-link" style="display:block; text-align:center;" href="https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W18_1B/l2b-v27-2026-196/1/level2_2025W18_1B_0074_2D1_spx_l2b-v27-2026-196.fits" target="_blank">⬇️ SPHEREx FITS (2025W18_1B)</a>
            <a class="resource-link" style="display:block; text-align:center;" href="https://irsa.ipac.caltech.edu/ibe/cutouts.html" target="_blank">🛰️ IRSA Multi-Epoch Cutouts</a>
            <a class="resource-link" style="display:block; text-align:center;" href="https://skyview.gsfc.nasa.gov/cgi-bin/images?Survey=digitized+sky+survey&position=14.5,36.5&Return=FITS" target="_blank">⬇️ SkyView 300x300 FITS</a>
        </div>
        """)

    s1, s2, s3, s4 = st.columns([1.45, 1.55, 1.35, 1.05])
    with s1:
        source_mode = st.selectbox(
            "📡 Data Source Option",
            ["Simulated SPHEREx Survey Sectors", "Upload Custom FITS / Sky Images", "Upload Custom CSV Star Catalog"]
        )
    with s2:
        picked_sector = st.selectbox("🌌 Sky Sector (J2000 Region)", list(celestialSectors.keys()))
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

    sector_info = celestialSectors[picked_sector]
    epoch_list = list(sector_info["epochs"].keys())

    e1, e2, e3 = st.columns([1.6, 1.6, 1.2])
    with e1:
        pass_a = st.selectbox("🗓️ Select First Observation Image (Image A)", epoch_list, index=0)
    with e2:
        pass_b = st.selectbox("🗓️ Select Second Observation Image (Image B)", epoch_list, index=1)
    with e3:
        st.write("")
        if st.button("⚡ Flip Image A ↔ B Manually", use_container_width=True):
            st.session_state.manual_frame = 2 if st.session_state.manual_frame == 1 else 1

    custom_active = False
    grid_a, grid_b = generate_sky_grid_pair(picked_sector, pass_a, pass_b, clean_enabled=clean_flag)
    label_a = sector_info["epochs"][pass_a]["label"]
    label_b = sector_info["epochs"][pass_b]["label"]

    if source_mode == "Upload Custom FITS / Sky Images":
        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "⬇️ Download Sample FITS Image A (2026-03-14 UTC)",
                data=make_fits_bytes(grid_a, "2026-03-14T04:12:00"),
                file_name="spherex_sample_pass1_20260314.fits",
                mime="application/octet-stream"
            )
        with d2:
            st.download_button(
                "⬇️ Download Sample FITS Image B (2026-09-18 UTC)",
                data=make_fits_bytes(grid_b, "2026-09-18T11:45:00"),
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
                grid_a, grid_b = arr1, arr2
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
                grid_a, grid_b = ca, cb
                custom_active = True
                label_a = f"CSV Epoch 1 ({csv_up.name})"
                label_b = f"CSV Epoch 2 ({csv_up.name})"
                st.success(f"✅ Built sky images from CSV catalog '{csv_up.name}' ({len(cdf)} rows)!")
                with st.expander("📋 View Uploaded CSV Catalog Table"):
                    st.dataframe(cdf, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Upload a .csv catalog file above (or download the sample CSV template to test!).")

    _, _, c_ra, c_dec = calculate_sky_coordinates(150, 150, sector_info["ra_center"], sector_info["dec_center"])
    mode_pill = (
        '<span class="exo-real-pill">🛰️ CUSTOM UPLOADED FITS / CSV DATA ACTIVE</span>'
        if custom_active
        else '<span class="exo-sim-pill">🧪 SIMULATED SPHEREx DEMO DATA (6.2"/px)</span>'
    )
    render_html_snippet(f"""
    <div class="space-panel" style="padding:10px 16px;">
        <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px;">
            <span style="font-weight:800; font-size:14.5px; color:#ffffff;">📍 Field Center (J2000): RA {c_ra} | Dec {c_dec} ({sector_info['constellation']})</span>
            {mode_pill}
        </div>
        <div style="display:flex; flex-wrap:wrap; justify-content:space-between; gap:10px; font-size:12.5px; color:#b8d8ff; margin-top:4px;">
            <span>🖼️ <b>Image A:</b> {label_a}</span>
            <span>🖼️ <b>Image B:</b> {label_b}</span>
            <span>🌈 <b>Band:</b> {sector_info['band']}</span>
        </div>
    </div>
    """)

    difference_grid = grid_b - grid_a
    img_a = colorize_sky_image(grid_a, color_theme, bright_val, contrast_val, is_difference=False)
    img_b = colorize_sky_image(grid_b, color_theme, bright_val, contrast_val, is_difference=False)
    img_sub = colorize_sky_image(difference_grid, color_theme, bright_val, contrast_val, is_difference=True)

    col_left, col_right = st.columns([1.35, 1.15])
    with col_left:
        if view_mode == "Side-by-Side 3-Panel View":
            p1, p2, p3 = st.columns(3)
            with p1:
                st.image(img_a, caption=f"Image A: {label_a}", use_container_width=True)
            with p2:
                st.image(img_b, caption=f"Image B: {label_b}", use_container_width=True)
            with p3:
                st.image(img_sub, caption="Subtraction (Cyan=A, Gold=B)", use_container_width=True)
        else:
            canvas_html = render_interactive_canvas(
                b64_a=image_to_base64_string(img_a),
                b64_b=image_to_base64_string(img_b),
                b64_sub=image_to_base64_string(img_sub),
                mode_name=view_mode,
                shape_name=shape_mode,
                blink_ms=blink_ms,
                mx=st.session_state.x_pick,
                my=st.session_state.y_pick,
                mr=st.session_state.r_pick,
                ra_center=sector_info["ra_center"],
                dec_center=sector_info["dec_center"],
                label_a=label_a,
                label_b=label_b,
                active_frame=st.session_state.manual_frame
            )
            components.html(canvas_html, height=585, scrolling=False)

    with col_right:
        render_html_snippet("""
        <div class="space-panel" style="padding:14px 16px;">
            <div style="color:#facc15; font-weight:900; font-size:15px; margin-bottom:4px;">🎯 Automatic &amp; Manual Area Selection</div>
            <p style="font-size:12.5px; color:#ffffff; margin:0;">
                <b>How to select:</b> Click <b>⏸️ Pause</b> or <b>⚡ Blink Manually</b> under the sky picture, drag your mouse/finger on the sky to encircle a moving dot, or adjust <b>Pixel X, Pixel Y, and Radius</b> below!
            </p>
        </div>
        """)

        nx, ny, nr = st.columns(3)
        with nx:
            st.session_state.x_pick = st.number_input("Pixel X (0-299)", 0, 299, int(st.session_state.x_pick))
        with ny:
            st.session_state.y_pick = st.number_input("Pixel Y (0-299)", 0, 299, int(st.session_state.y_pick))
        with nr:
            st.session_state.r_pick = st.number_input("Radius (px)", 8, 60, int(st.session_state.r_pick))

        with st.expander("💡 Need a Hint? Optional Quick-Snap Helpers"):
            hc1, hc2, hc3 = st.columns(3)
            objs = sector_info["objects"]
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

        _, _, live_ra, live_dec = calculate_sky_coordinates(
            st.session_state.x_pick, st.session_state.y_pick, sector_info["ra_center"], sector_info["dec_center"]
        )
        render_html_snippet(f"""
        <div style="background:#091530; border:1px solid rgba(52, 211, 153, 0.45); border-radius:10px; padding:8px 12px; margin-bottom:10px; font-size:12px; color:#d8f8e8;">
            🧭 <b>Selected Area Sky Coordinates (J2000):</b><br/>
            • <b>Right Ascension (RA):</b> {live_ra}<br/>
            • <b>Declination (Dec):</b> {live_dec}
        </div>
        """)

        with st.expander("🔬 Scientific Verification Checklist (Optional Filter)", expanded=True):
            check_dir = st.checkbox("Did it move or change brightness across epochs?", value=True)
            check_hot = st.checkbox("Confirmed not a camera artifact?", value=True)
            check_snr = st.checkbox("Ready to check SNR & flux photometry?", value=True)

        if st.button("🔍 Analyze Selected Area, Measure Flux & Play Sound", use_container_width=True):
            if not (check_dir and check_hot and check_snr):
                st.warning("⚠️ Please tick the Scientific Verification Checklist boxes above before analyzing your candidate!")
            else:
                scan_result = evaluate_user_sky_pick(
                    sector_name=picked_sector,
                    pass_a=pass_a,
                    pass_b=pass_b,
                    cx=int(st.session_state.x_pick),
                    cy=int(st.session_state.y_pick),
                    radius_px=int(st.session_state.r_pick),
                    grid_a=grid_a,
                    grid_b=grid_b,
                    custom_mode=custom_active
                )
                st.session_state.last_result = scan_result
                st.session_state.total_score += scan_result["points"]
                st.session_state.saved_scores[st.session_state.explorerName] = st.session_state.total_score
                points_display = f"+{scan_result['points']}" if scan_result["points"] > 0 else f"{scan_result['points']}"

                st.session_state.score_table.insert(0, {
                    "Username": st.session_state.explorerName,
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Data Source": source_mode if custom_active else "Simulated SPHEREx Demo",
                    "Set Used": picked_sector,
                    "Observation Dates": f"{scan_result['date_a']} vs {scan_result['date_b']}",
                    "Pixels (X, Y)": f"({st.session_state.x_pick}, {st.session_state.y_pick}) | {shape_mode} r={st.session_state.r_pick}px",
                    "Celestial Coords (RA, Dec J2000)": f"RA: {scan_result['ra_str']} | Dec: {scan_result['dec_str']}",
                    "Found Anomaly or Not": scan_result["found_flag"],
                    "Candidate Status": scan_result["status"],
                    "Found What": scan_result["title"],
                    "Brightness & Flux": scan_result["flux_text"],
                    "Points": points_display,
                    "Total Score": st.session_state.total_score,
                    "Physical Properties": f"{scan_result['distance']} | {scan_result['temp']} | {scan_result['shift_text']}",
                    "Sonification": f"{scan_result['freq']} Hz Doppler Sound (Flux {scan_result['peak_flux']})"
                })

        if st.session_state.last_result is not None:
            res = st.session_state.last_result
            is_success = res["points"] > 0
            badge_color = "#34d399" if is_success else "#f43f5e"
            score_tag = f"+{res['points']} pts" if is_success else f"{res['points']} pts"

            if is_success:
                render_html_snippet("""
                <div style="background:rgba(52, 211, 153, 0.18); border:1.5px solid #34d399; border-radius:10px; text-align:center; padding: 10px; margin-bottom:10px;">
                    <span class="floating-celebration">🪐</span>
                    <span class="floating-celebration" style="animation-delay: 0.3s;">🚀</span>
                    <span class="floating-celebration" style="animation-delay: 0.6s;">🌟</span>
                    <span style="color:#34d399; font-weight:900; font-size:15px; margin-left:8px;">SUCCESS! Candidate Anomaly Logged!</span>
                </div>
                """)
            else:
                render_html_snippet("""
                <div style="background:rgba(244, 63, 94, 0.18); border:1.5px solid #f43f5e; border-radius:10px; text-align:center; padding: 10px; margin-bottom:10px; color:#f87171; font-weight:800; font-size:14px;">
                    💫 Better luck next time! Keep scanning the star fields. (-20 pts)
                </div>
                """)

            render_html_snippet(f"""
            <div class="space-panel" style="border-color:{badge_color}; padding:14px 16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                    <span style="font-weight:900; font-size:15.5px; color:{badge_color};">{res['title']}</span>
                    <span style="background:{badge_color}; color:#010309; font-weight:900; font-size:11px; padding:3px 12px; border-radius:99px;">{score_tag}</span>
                </div>
                <div style="margin-top:6px; padding:4px 10px; background:rgba(250, 204, 21, 0.14); border-left:3px solid #facc15; font-size:12px; color:#facc15; font-weight:700;">
                    📋 Status: {res['status']}
                </div>
                <p style="font-size:13px; color:#ffffff; margin:8px 0;">{res['note']}</p>
                <div style="font-size:12.5px; color:#b8d8ff; line-height:1.6;">
                    • <b>J2000 Sky Coords:</b> RA {res['ra_str']} | Dec {res['dec_str']}<br/>
                    • <b>Observation Times:</b> {res['date_a']} -> {res['date_b']}<br/>
                    • <b>Brightness / Flux:</b> {res['flux_text']}<br/>
                    • <b>Measured Shift:</b> {res['shift_text']}<br/>
                    • <b>Physical Properties:</b> {res['distance']} | {res['temp']} | {res['mass']}
                </div>
            </div>
            """)

            st.write("🔊 **Hear the Candidate** (Stronger signal = clearer sound)")
            st.caption("⚠️ **Disclaimer:** Space is a vacuum and has no sound. This audio feature uses scientific sonification to translate infrared flux intensity and motion shifts into acoustic frequencies for data accessibility.")

            audio_bytes = generate_doppler_audio(
                freq_hz=float(res["freq"]),
                flux_value=float(res["peak_flux"]),
                is_planet_x=("Planet X" in res["kind"])
            )
            st.audio(audio_bytes, format="audio/wav")

    st.write("")
    render_html_snippet("""
    <div class="space-panel" style="padding:14px 18px;">
        <div style="color:#facc15; font-weight:900; font-size:18px;">🏆 Live Candidate Log &amp; Discovery Scoreboard</div>
        <div style="font-size:13px; color:#c8dcff;">Records your scans once you start playing! If you switch users and log back in, your previous discoveries stay saved here.</div>
    </div>
    """)
    if len(st.session_state.score_table) == 0:
        st.info("🌌 No candidate logs yet! Select an area on the sky image above and click 'Analyze Selected Area, Measure Flux & Play Sound'.")
    else:
        score_df = pd.DataFrame(st.session_state.score_table)
        st.dataframe(score_df, use_container_width=True, hide_index=True)
        st.download_button(
            "📥 Download Candidate Log (CSV)",
            data=score_df.to_csv(index=False).encode("utf-8"),
            file_name="exomapper_candidate_log.csv",
            mime="text/csv"
        )

apply_custom_space_styling()
if st.session_state.page_step == "welcome":
    show_welcome_screen()
elif st.session_state.page_step == "manual":
    show_manual_screen()
else:
    show_game_screen()

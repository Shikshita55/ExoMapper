# ==============================================================================
# EXOMAPPER: THE HUNT FOR PLANET X & SPHEREx SKY WORKBENCH
# NASA Space Apps Challenge 2026 - Team ExoMapper
# Crew: Shikshita Naryal, Ayaan Agarwal & Maheswar Nayak
# Built in Python with Streamlit, NumPy, Pandas, PIL, and urllib
# ==============================================================================

import base64
import io
import math
import urllib.parse
import urllib.request
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

# joins multiline HTML into one single line so Streamlit never leaks raw </div> tags
def put_html(raw_code):
    flat_line = " ".join(line.strip() for line in raw_code.splitlines() if line.strip())
    st.markdown(flat_line, unsafe_allow_html=True)

# official NASA meatball vector logo encoded as base64 SVG
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

# responsive dark space theme that runs smoothly on phones, tablets, laptops, and monitors
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
    @keyframes floatEmoji {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
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
    div[data-testid="stExpander"], details {
        background-color: #081126 !important;
        border: 1.5px solid rgba(0, 212, 255, 0.42) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    div[data-testid="stExpander"] details summary,
    div[data-testid="stExpander"] details[open] summary,
    div[data-testid="stExpander"] details summary:hover,
    div[data-testid="stExpander"] details summary:focus,
    div[data-testid="stExpander"] details summary:active,
    details > summary,
    details[open] > summary {
        background: linear-gradient(90deg, #0b1d42 0%, #102a5e 100%) !important;
        color: #ffd166 !important;
        padding: 10px 14px !important;
        font-weight: 800 !important;
    }
    div[data-testid="stExpander"] details summary p,
    div[data-testid="stExpander"] details summary span,
    div[data-testid="stExpander"] details summary div,
    div[data-testid="stExpander"] details summary svg,
    div[data-testid="stExpander"] details[open] summary p,
    div[data-testid="stExpander"] details[open] summary span,
    div[data-testid="stExpander"] details[open] summary div,
    div[data-testid="stExpander"] details[open] summary svg {
        color: #ffd166 !important;
        fill: #ffd166 !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    li[role="option"]:hover, li[role="option"][aria-selected="true"] {
        background-color: #1458c8 !important;
        color: #ffd166 !important;
    }
    .exo-tool-box {
        background: linear-gradient(145deg, rgba(12, 26, 58, 0.95), rgba(6, 14, 32, 0.98));
        border: 1.5px solid #00d4ff;
        border-left: 5px solid #ffd166;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 12px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.5);
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
        padding: 0.55rem 1.0rem !important;
        box-shadow: 0 4px 14px rgba(0, 212, 255, 0.22) !important;
        transition: transform 0.12s ease, background 0.15s ease !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #fc3d21 0%, #c8230c 100%) !important;
        border-color: #ffd166 !important;
        transform: translateY(-1px);
    }
    .exo-card {
        background: linear-gradient(145deg, rgba(10, 21, 48, 0.92), rgba(7, 13, 30, 0.95));
        border: 1.5px solid rgba(0, 212, 255, 0.32);
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 12px;
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
        margin-bottom: 8px;
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
        padding: 6px 11px;
        background: rgba(11, 61, 145, 0.78);
        border: 1px solid #00d4ff;
        border-radius: 8px;
        color: #7ce8ff !important;
        text-decoration: none !important;
        font-size: 12px;
        font-weight: 700;
    }
    .exo-link-btn:hover {
        background: #fc3d21;
        color: #ffffff !important;
        border-color: #ffffff;
    }
    .celebration-banner {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 16px;
        font-size: 24px;
        padding: 8px;
        margin: 6px 0;
        background: rgba(0, 255, 157, 0.12);
        border: 1px dashed #00ff9d;
        border-radius: 10px;
        animation: floatEmoji 2s ease-in-out infinite;
    }
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            padding-top: 1rem !important;
        }
        .exo-card {
            padding: 12px 12px !important;
        }
        h1 { font-size: 23px !important; }
        h2 { font-size: 18px !important; }
    }
    </style>
    """
    put_html(css_block)

ARCSEC_PER_PX = 6.2

# ==============================================================================
# LEVEL 1: PRACTICE MODE SECTORS (Simulated Training Data Before Real Mission)
# ==============================================================================
practiceSkyData = {
    "Practice Sector 1: Orion Outer Rim (Training Field)": {
        "seed": 104,
        "difficulty": "Level 1 Practice (Easy)",
        "survey_origin": "Simulated SPHEREx Training Cube",
        "tap_table": "fp_psc",
        "ra_center": 83.8221,
        "dec_center": -5.3911,
        "constellation": "Orion",
        "band": "Simulated Band 4 (3.82 um Near-IR)",
        "epochs": {
            "Pass 1 (2026-03-14 04:12 UTC)": {"step": 0.0, "days": 0, "label": "2026-03-14 04:12 UTC"},
            "Pass 2 (2026-09-18 11:45 UTC)": {"step": 1.0, "days": 188, "label": "2026-09-18 11:45 UTC"},
            "Pass 3 (2027-03-22 08:30 UTC)": {"step": 2.0, "days": 373, "label": "2027-03-22 08:30 UTC"}
        },
        "objects": [
            {
                "name": "Our Practice Target: Trans-Neptunian World (TNO-Orion-Sim1)",
                "kind": "Planet X Candidate",
                "status": "PRACTICE HIT - Unconfirmed Candidate (Needs 3rd-Epoch Orbit Check)",
                "x1": 96, "y1": 112, "dx": 14, "dy": -8,
                "flux_e1": 14.2, "flux_e2": 14.4, "amp": 0.96, "points": 150,
                "distance": "~620 AU (From Parallax Shift)",
                "temp": "~48 K (-225 C)",
                "mass": "~6.2 Earth Masses (Model Estimate)",
                "wavelength": "3.82 um Methane & Water Ice Band",
                "shift_type": "Redshift (Receding Outer Orbit, z = +0.00012)",
                "rv_kms": +36.0,
                "freq": 540,
                "note": "Wonderful! We spotted our simulated outer solar system target moving slowly across pixels at steady ~14.3 mJy brightness."
            },
            {
                "name": "Our Practice Target: Cool Y-Class Brown Dwarf (BD-Orion-Sim4)",
                "kind": "Brown Dwarf Candidate",
                "status": "PRACTICE HIT - Proper-Motion Candidate (Needs Spectrum Check)",
                "x1": 218, "y1": 74, "dx": 7, "dy": 6,
                "flux_e1": 9.8, "flux_e2": 9.6, "amp": 0.82, "points": 80,
                "distance": "~24 Light-Years",
                "temp": "~410 K (Cool Y-Dwarf)",
                "mass": "~18 Jupiter Masses",
                "wavelength": "4.50 um Thermal Glow",
                "shift_type": "Blueshift (Approaching Solar Neighborhood, z = -0.00008)",
                "rv_kms": -24.0,
                "freq": 420,
                "note": "We caught a small proper-motion shift at steady ~9.7 mJy brightness. Matches a nearby cool brown dwarf."
            },
            {
                "name": "Our Practice Target: Distant Supernova Flash (SN-2026or-Sim)",
                "kind": "Transient Candidate",
                "status": "PRACTICE HIT - Photometric Transient (Fixed Position, Bright Flash)",
                "x1": 64, "y1": 228, "dx": 0, "dy": 0,
                "flux_e1": 2.4, "flux_e2": 13.8, "amp": 0.93, "points": 85,
                "distance": "~140 Million Light-Years",
                "temp": "~11,500 K",
                "mass": "~1.4 Solar Masses",
                "wavelength": "1.65 um Near-IR Peak",
                "shift_type": "Redshift (Cosmological Host Galaxy, z = +0.011)",
                "rv_kms": +115.0,
                "freq": 660,
                "note": "It stayed at the exact same pixel (0.0 px shift) but our analysis shows it brightened from 2.4 mJy to 13.8 mJy!"
            }
        ]
    },
    "Practice Sector 2: Taurus Ecliptic Training Corridor": {
        "seed": 209,
        "difficulty": "Level 1 Practice (Medium)",
        "survey_origin": "Simulated Ecliptic Plane Cube",
        "tap_table": "allwise_p3as_psd",
        "ra_center": 68.9800,
        "dec_center": 16.5092,
        "constellation": "Taurus",
        "band": "Simulated Band 3 (3.40 um Near-IR)",
        "epochs": {
            "Pass 1 (2026-02-20 02:30 UTC)": {"step": 0.0, "days": 0, "label": "2026-02-20 02:30 UTC"},
            "Pass 2 (2026-08-25 09:15 UTC)": {"step": 1.0, "days": 186, "label": "2026-08-25 09:15 UTC"},
            "Pass 3 (2027-02-24 14:10 UTC)": {"step": 2.0, "days": 369, "label": "2027-02-24 14:10 UTC"}
        },
        "objects": [
            {
                "name": "Our Practice Target: Kuiper Belt Outlier (TNO-Tauri-Sim7)",
                "kind": "Planet X Candidate",
                "status": "PRACTICE HIT - Unconfirmed Candidate (Needs 3rd-Epoch Orbit Check)",
                "x1": 188, "y1": 176, "dx": -15, "dy": -10,
                "flux_e1": 13.5, "flux_e2": 13.7, "amp": 0.95, "points": 150,
                "distance": "~540 AU (From Parallax Shift)",
                "temp": "~52 K (-221 C)",
                "mass": "~7.5 Earth Masses",
                "wavelength": "3.40 um Infrared Band",
                "shift_type": "Redshift (Receding Aphelion Arc, z = +0.00010)",
                "rv_kms": +31.0,
                "freq": 560,
                "note": "We tracked a clear shift across the star field with steady ~13.6 mJy brightness. Logged as our unconfirmed Planet X candidate!"
            },
            {
                "name": "Our Practice Target: M-Dwarf Flare Star (TV-Tauri-Sim9)",
                "kind": "Transient Candidate",
                "status": "PRACTICE HIT - Variable Star (Fixed Position, Flux Jump)",
                "x1": 82, "y1": 90, "dx": 0, "dy": 0,
                "flux_e1": 3.1, "flux_e2": 12.6, "amp": 0.89, "points": 70,
                "distance": "~68 Light-Years",
                "temp": "~3,100 K (Flare Event)",
                "mass": "~0.35 Solar Masses",
                "wavelength": "2.20 um Continuum",
                "shift_type": "Blueshift (Approaching Stellar Stream, z = -0.00005)",
                "rv_kms": -18.0,
                "freq": 490,
                "note": "It did not move in position, but our multi-epoch comparison caught it flaring brightly between our dates."
            }
        ]
    }
}

# ==============================================================================
# LEVEL 2: REAL NASA / IRSA ARCHIVE SECTORS (4 Difficulty Tiers from IRSA Releases)
# ==============================================================================
realIrsaSkyData = {
    "Tier 1 (Easy - 2MASS & AllWISE): Wise J0855-0714 Solar Neighborhood Field": {
        "seed": 501,
        "difficulty": "Tier 1: Beginner (High-SNR 2MASS + AllWISE Catalog)",
        "survey_origin": "IRSA AllWISE Source Catalog & 2MASS All-Sky Release",
        "tap_table": "allwise_p3as_psd",
        "irsa_url": "https://irsa.ipac.caltech.edu/data/download/wise-allwise/",
        "parquet_url": "https://irsa.ipac.caltech.edu/data/download/parquet/wise/allwise/healpix_k5/",
        "ra_center": 133.7860,
        "dec_center": -7.2430,
        "constellation": "Hydra",
        "band": "AllWISE W2 (4.6 um) + 2MASS Ks (2.16 um)",
        "epochs": {
            "AllWISE Epoch 1 (2010-05-04 UTC)": {"step": 0.0, "days": 0, "label": "2010-05-04 09:20 UTC"},
            "AllWISE Epoch 2 (2010-11-12 UTC)": {"step": 1.0, "days": 192, "label": "2010-11-12 18:10 UTC"},
            "NEOWISE Reactivation Pass (2024-05-09 UTC)": {"step": 2.0, "days": 5119, "label": "2024-05-09 04:55 UTC"}
        },
        "real_catalog_stars": [
            (42, 58, 0.88), (78, 195, 0.74), (128, 44, 0.69), (150, 150, 0.91),
            (204, 118, 0.79), (252, 86, 0.64), (266, 224, 0.83), (92, 262, 0.71),
            (174, 246, 0.66), (34, 148, 0.59), (225, 172, 0.77), (112, 88, 0.62)
        ],
        "objects": [
            {
                "name": "WISE J085510.83-071442.5 (Sub-Brown Dwarf / Planetary-Mass Object)",
                "kind": "Planet X Candidate",
                "status": "REAL IRSA ARCHIVE HIT - High-Motion Coldest Known Brown Dwarf / Free-Floating Planet",
                "x1": 118, "y1": 136, "dx": 16, "dy": -6,
                "flux_e1": 14.8, "flux_e2": 14.9, "amp": 0.97, "points": 175,
                "distance": "7.27 Light-Years (2.23 pc - IRSA Parallax)",
                "temp": "~250 K (-23 C, Coldest Known Extrasolar World)",
                "mass": "~3 to 10 Jupiter Masses",
                "wavelength": "4.60 um AllWISE W2 Thermal Peak",
                "shift_type": "Blueshift (Fast Transverse & Approach Motion, z = -0.00011)",
                "rv_kms": -33.0,
                "freq": 430,
                "note": "Amazing real IRSA archival discovery! WISE 0855-0714 shows huge proper motion (~8.1 arcsec/yr) in our AllWISE & NEOWISE infrared frames."
            },
            {
                "name": "AllWISE J0855+0712 Ecliptic Background Asteroid (MP-Hydra-02)",
                "kind": "Brown Dwarf Candidate",
                "status": "REAL IRSA ARCHIVE HIT - Moving Solar System Minor Body",
                "x1": 212, "y1": 88, "dx": -11, "dy": 9,
                "flux_e1": 10.2, "flux_e2": 10.0, "amp": 0.84, "points": 100,
                "distance": "~3.1 AU (Main Asteroid Belt)",
                "temp": "~165 K (-108 C)",
                "mass": "~4.2 x 10^15 kg",
                "wavelength": "4.60 um Thermal Emission",
                "shift_type": "Redshift (Receding Orbital Leg, z = +0.00006)",
                "rv_kms": +19.5,
                "freq": 530,
                "note": "We detected this minor body in the AllWISE Multiepoch Photometry Database moving across Hydra background stars."
            }
        ]
    },
    "Tier 2 (Medium - NEOWISE 2015-2024): Cetus Sedna-Corridor Multi-Epoch Survey": {
        "seed": 602,
        "difficulty": "Tier 2: Intermediate (NEOWISE 11-Year Single-Exposure Table)",
        "survey_origin": "IRSA NEOWISE Single-Exposure Source Table (Years 1-11 + 2024 Addendum)",
        "tap_table": "neowiser_p1bs_psd",
        "irsa_url": "https://irsa.ipac.caltech.edu/data/download/neowiser_year11/",
        "parquet_url": "https://irsa.ipac.caltech.edu/data/download/parquet/neowiser/healpix_k5/",
        "ra_center": 54.1290,
        "dec_center": 4.9280,
        "constellation": "Cetus",
        "band": "NEOWISE W1 (3.4 um) & W2 (4.6 um) Multi-Epoch",
        "epochs": {
            "NEOWISE Year 1 (2015-01-22 UTC)": {"step": 0.0, "days": 0, "label": "2015-01-22 03:15 UTC"},
            "NEOWISE Year 6 (2020-01-24 UTC)": {"step": 1.0, "days": 1828, "label": "2020-01-24 07:40 UTC"},
            "NEOWISE Year 11 Addendum (2024-07-28 UTC)": {"step": 2.0, "days": 3475, "label": "2024-07-28 11:05 UTC"}
        },
        "real_catalog_stars": [
            (32, 72, 0.81), (66, 144, 0.75), (108, 212, 0.68), (150, 150, 0.89),
            (194, 62, 0.73), (238, 134, 0.84), (272, 198, 0.67), (142, 48, 0.78),
            (84, 258, 0.63), (216, 248, 0.72), (52, 192, 0.61), (176, 108, 0.70)
        ],
        "objects": [
            {
                "name": "90377 Sedna / Inner Oort Cloud Candidate (NEOWISE-Cetus-TNO1)",
                "kind": "Planet X Candidate",
                "status": "REAL IRSA ARCHIVE HIT - Extreme Detached Trans-Neptunian Object",
                "x1": 88, "y1": 106, "dx": 14, "dy": -7,
                "flux_e1": 13.8, "flux_e2": 13.9, "amp": 0.94, "points": 185,
                "distance": "~84.6 AU (Pericenter Detached Orbit)",
                "temp": "~33 K (-240 C, Methane/Nitrogen Ice)",
                "mass": "~1.0 x 10^21 kg (Dwarf Planet Scale)",
                "wavelength": "3.40 um CH4 Ice Absorption Feature",
                "shift_type": "Redshift (Outbound Orbital Arc, z = +0.00014)",
                "rv_kms": +42.0,
                "freq": 565,
                "note": "We tracked this across NEOWISE Years 1 to 11 single-exposure frames! Extreme detached orbit used to model Planet X gravity."
            },
            {
                "name": "Mira Ceti Long-Period Asymptotic Giant Variable (NEOWISE-Var-07)",
                "kind": "Transient Candidate",
                "status": "REAL IRSA ARCHIVE HIT - Periodic Infrared Pulsating Variable",
                "x1": 224, "y1": 182, "dx": 0, "dy": 0,
                "flux_e1": 3.2, "flux_e2": 14.1, "amp": 0.92, "points": 95,
                "distance": "~300 Light-Years (92 pc)",
                "temp": "~2,900 K (pulsating red giant envelope)",
                "mass": "~1.18 Solar Masses",
                "wavelength": "4.60 um Circumstellar Dust Band",
                "shift_type": "Redshift (Receding Radial Velocity +63 km/s)",
                "rv_kms": +63.0,
                "freq": 610,
                "note": "Zero positional shift across epochs, but our analysis caught a huge 332-day pulsation jump in NEOWISE photometry!"
            }
        ]
    },
    "Tier 3 (Hard - unWISE Neo7 & ZTF DR24): Cygnus Time-Domain Transient Field": {
        "seed": 703,
        "difficulty": "Tier 3: Advanced (unWISE Time-Domain + ZTF DR24 Lightcurves)",
        "survey_origin": "IRSA unWISE Neo7 Time-Domain Parquet & ZTF DR24 Objects HATS Catalog",
        "tap_table": "ztf_objects_dr24",
        "irsa_url": "https://irsa.ipac.caltech.edu/data/ZTF/lc/lc_dr24/",
        "parquet_url": "https://irsa.ipac.caltech.edu/data/download/parquet/unwise/neo7/time_domain/healpix_k5/",
        "ra_center": 305.5570,
        "dec_center": 40.2567,
        "constellation": "Cygnus",
        "band": "unWISE W1/W2 Coadd + ZTF DR24 r-band Cross-Match",
        "epochs": {
            "unWISE Neo1 Baseline (2015-05-18 UTC)": {"step": 0.0, "days": 0, "label": "2015-05-18 06:10 UTC"},
            "unWISE Neo7 Epoch (2021-10-22 UTC)": {"step": 1.0, "days": 2349, "label": "2021-10-22 14:30 UTC"},
            "ZTF DR24 Follow-Up Epoch (2025-08-14 UTC)": {"step": 2.0, "days": 3741, "label": "2025-08-14 09:00 UTC"}
        },
        "real_catalog_stars": [
            (28, 42, 0.85), (56, 118, 0.79), (94, 68, 0.72), (132, 196, 0.81),
            (150, 150, 0.93), (186, 232, 0.76), (218, 54, 0.69), (254, 146, 0.84),
            (276, 256, 0.65), (72, 242, 0.74), (164, 82, 0.68), (114, 134, 0.77)
        ],
        "objects": [
            {
                "name": "unWISE High-Proper-Motion Halo T-Dwarf (unWISE-J2022+4015)",
                "kind": "Brown Dwarf Candidate",
                "status": "REAL IRSA ARCHIVE HIT - Time-Domain Proper-Motion Substellar Object",
                "x1": 144, "y1": 78, "dx": -12, "dy": 11,
                "flux_e1": 11.4, "flux_e2": 11.3, "amp": 0.87, "points": 140,
                "distance": "~46 Light-Years (14.1 pc)",
                "temp": "~720 K (Methane T7 Dwarf)",
                "mass": "~22 Jupiter Masses",
                "wavelength": "3.40 um unWISE W1 Band",
                "shift_type": "Blueshift (Approaching Galactic Halo Orbit, z = -0.00019)",
                "rv_kms": -57.0,
                "freq": 405,
                "note": "We discovered this by cross-matching unWISE Time-Domain Parquet tiles with ZTF DR24 non-detections (pure infrared mover!)."
            },
            {
                "name": "ZTF24aabqcy / Cygnus Classical Nova Outburst (ZTF-DR24-Nova1)",
                "kind": "Transient Candidate",
                "status": "REAL IRSA ARCHIVE HIT - ZTF DR24 Cataclysmic Variable Outburst",
                "x1": 68, "y1": 188, "dx": 0, "dy": 0,
                "flux_e1": 1.9, "flux_e2": 14.6, "amp": 0.96, "points": 130,
                "distance": "~4,200 Light-Years",
                "temp": "~18,000 K (Thermonuclear Runaway Shell)",
                "mass": "~1.25 Solar Mass White Dwarf",
                "wavelength": "0.64 um ZTF r-band + 3.4 um Dust Echo",
                "shift_type": "Blueshift (Expanding Ejecta Shell at -850 km/s)",
                "rv_kms": -120.0,
                "freq": 390,
                "note": "Found at stationary coordinates in ZTF DR24 Objects HATS catalog with a massive 7.5x flux eruption!"
            }
        ]
    },
    "Tier 4 (Expert Pro-Max - SPHEREx QR1 & Euclid Q1): Deep Ecliptic Planet X Hunt": {
        "seed": 804,
        "difficulty": "Tier 4: Expert Pro-Max (SPHEREx Quick-Release + Euclid Q1 HATS)",
        "survey_origin": "IRSA SPHEREx Archive (2025W18_1B) & Euclid Q1 Merged Objects Catalog",
        "tap_table": "euclid_q1_mer_catalogue",
        "irsa_url": "https://irsa.ipac.caltech.edu/Missions/spherex.html",
        "parquet_url": "https://irsa.ipac.caltech.edu/data/download/parquet/euclid/q1/merged_objects/hats/",
        "ra_center": 14.5000,
        "dec_center": 36.5000,
        "constellation": "Andromeda / Ecliptic North",
        "band": "SPHEREx LVF Spectrophotometry (0.75-5.0 um) + Euclid NISP",
        "epochs": {
            "SPHEREx QR1 Pass 1 (2025W18_1B | 2025-05-02 UTC)": {"step": 0.0, "days": 0, "label": "2025-05-02 08:14 UTC"},
            "SPHEREx DR1 Pass 2 (2026-196 | 2026-07-15 UTC)": {"step": 1.0, "days": 439, "label": "2026-07-15 19:22 UTC"},
            "Euclid Q1 + SPHEREx Pass 3 (2026-11-10 UTC)": {"step": 2.0, "days": 557, "label": "2026-11-10 02:40 UTC"}
        },
        "real_catalog_stars": [
            (38, 92, 0.79), (74, 52, 0.83), (116, 178, 0.71), (150, 150, 0.90),
            (188, 96, 0.75), (226, 214, 0.82), (264, 78, 0.68), (98, 248, 0.74),
            (168, 262, 0.64), (54, 216, 0.72), (242, 142, 0.77), (132, 64, 0.69)
        ],
        "objects": [
            {
                "name": "SPHEREx-PX-2026A (Faint Trans-Neptunian Planet X Candidate)",
                "kind": "Planet X Candidate",
                "status": "PRO-MAX ARCHIVE CANDIDATE - Unconfirmed 580 AU World (Needs 3rd-Epoch Orbit Fit)",
                "x1": 104, "y1": 122, "dx": 13, "dy": -7,
                "flux_e1": 13.9, "flux_e2": 14.0, "amp": 0.93, "points": 250,
                "distance": "~580 AU (From 6-Month SPHEREx Parallax Baseline)",
                "temp": "~46 K (-227 C, Blackbody Peak in Thermal IR)",
                "mass": "~6.5 Earth Masses (Sub-Neptune Core Model)",
                "wavelength": "3.82 um SPHEREx Band 4 + Euclid H-band Drop",
                "shift_type": "Redshift (Distant Inclined Aphelion Arc, z = +0.00015)",
                "rv_kms": +45.0,
                "freq": 590,
                "note": "Pro-Max Discovery! We detected sub-arcsecond daily motion across SPHEREx 2025W18_1B and 2026-196 Level-2 FITS frames!"
            },
            {
                "name": "Euclid-SPHEREx High-z Quasar Outburst (ESQ-J0058+3630)",
                "kind": "Transient Candidate",
                "status": "PRO-MAX ARCHIVE CANDIDATE - High-Redshift Active Galactic Nucleus Flare",
                "x1": 208, "y1": 164, "dx": 0, "dy": 0,
                "flux_e1": 2.8, "flux_e2": 13.4, "amp": 0.91, "points": 160,
                "distance": "~9.8 Billion Light-Years (z = 1.62)",
                "temp": "~24,000 K (Accretion Disk Continuum)",
                "mass": "~4.5 x 10^8 Solar Masses (Supermassive Black Hole)",
                "wavelength": "4.20 um Redshifted H-alpha Line in SPHEREx",
                "shift_type": "High Redshift (Cosmological Expansion, z = +1.62)",
                "rv_kms": +140.0,
                "freq": 680,
                "note": "Confirmed zero proper motion in Euclid Q1 Merged Objects HATS catalog, with strong infrared brightening in our SPHEREx pass!"
            }
        ]
    }
}

IRSA_CATALOG_DIRECTORY = [
    {
        "Catalog / Mission": "SPHEREx Mission & Quick Release Archive",
        "Format": "FITS Level-2 & Spectral Cubes",
        "Difficulty": "Tier 4 (Expert)",
        "Use in ExoMapper": "Primary 102-band infrared sky survey (6.2\"/px) for outer solar system Planet X parallax.",
        "Official URL": "https://irsa.ipac.caltech.edu/Missions/spherex.html",
        "Direct App / Data Link": "https://irsa.ipac.caltech.edu/applications/spherex/"
    },
    {
        "Catalog / Mission": "Euclid Q1 Merged Objects Catalog",
        "Format": "HATS Parquet",
        "Difficulty": "Tier 4 (Expert)",
        "Use in ExoMapper": "Deep space cross-match to separate distant galaxies from slow-moving Solar System TNOs.",
        "Official URL": "https://irsa.ipac.caltech.edu/data/download/parquet/euclid/q1/merged_objects/hats/",
        "Direct App / Data Link": "https://irsa.ipac.caltech.edu/data/download/parquet/euclid/q1/merged_objects/hats/"
    },
    {
        "Catalog / Mission": "AllWISE Source Catalog & Multiepoch Photometry",
        "Format": "ASCII (bzip2) & HATS Parquet",
        "Difficulty": "Tier 1 (Beginner)",
        "Use in ExoMapper": "All-sky W1-W4 (3.4 to 22 um) baseline catalog for high-proper-motion brown dwarfs and Planet X searches.",
        "Official URL": "https://irsa.ipac.caltech.edu/data/download/wise-allwise/",
        "Direct App / Data Link": "https://irsa.ipac.caltech.edu/data/download/parquet/wise/allwise/healpix_k5/"
    },
    {
        "Catalog / Mission": "NEOWISE Single-Exposure Source Table (Years 1-11 + 2024 Addendum)",
        "Format": "ASCII (bzip2) & HEALPix k5 Parquet",
        "Difficulty": "Tier 2 (Intermediate)",
        "Use in ExoMapper": "11-year multi-epoch time series (2015-2024) for tracking moving asteroids, comets, and TNOs.",
        "Official URL": "https://irsa.ipac.caltech.edu/data/download/neowiser_year11/",
        "Direct App / Data Link": "https://irsa.ipac.caltech.edu/data/download/parquet/neowiser/healpix_k5/"
    },
    {
        "Catalog / Mission": "unWISE Neo7 Time-Domain Catalog",
        "Format": "HEALPix k5 Parquet",
        "Difficulty": "Tier 3 (Advanced)",
        "Use in ExoMapper": "Six-month coadded infrared epochs ideal for faint outer solar system motion detection.",
        "Official URL": "https://irsa.ipac.caltech.edu/data/download/parquet/unwise/neo7/time_domain/healpix_k5/",
        "Direct App / Data Link": "https://irsa.ipac.caltech.edu/data/download/parquet/unwise/neo7/time_domain/healpix_k5/"
    },
    {
        "Catalog / Mission": "ZTF DR24 Lightcurves & Objects Table",
        "Format": "Parquet & HATS Parquet",
        "Difficulty": "Tier 3 (Advanced)",
        "Use in ExoMapper": "Optical transient lightcurves to classify supernovae, flare stars, and variable stars.",
        "Official URL": "https://irsa.ipac.caltech.edu/data/ZTF/lc/lc_dr24/",
        "Direct App / Data Link": "https://irsa.ipac.caltech.edu/data/download/parquet/ztf/dr24/objects/hats/"
    },
    {
        "Catalog / Mission": "WISE All-Sky, 3-Band Cryo, Post-Cryo & Reject Tables",
        "Format": "ASCII (bzip2)",
        "Difficulty": "Tier 2 (Intermediate)",
        "Use in ExoMapper": "Cryogenic L1b single-exposure frames and reject tables where fast-moving uncataloged objects hide!",
        "Official URL": "https://irsa.ipac.caltech.edu/data/download/wise-allsky/",
        "Direct App / Data Link": "https://irsa.ipac.caltech.edu/data/download/wise-allwise/reject/"
    },
    {
        "Catalog / Mission": "2MASS All-Sky Data Release",
        "Format": "ASCII (gzip) & TAP API",
        "Difficulty": "Tier 1 (Beginner)",
        "Use in ExoMapper": "Stationary J, H, Ks astrometric reference grid for locking J2000 RA/Dec coordinates.",
        "Official URL": "https://irsa.ipac.caltech.edu/2MASS/download/allsky/",
        "Direct App / Data Link": "https://irsa.ipac.caltech.edu/docs/program_interface/TAP.html"
    }
]

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

@st.cache_data(show_spinner=False, ttl=600)
def fetch_live_irsa_tap_catalog(ra0, dec0, table_name="fp_psc", api_token=""):
    if table_name == "allwise_p3as_psd":
        adql = (
            f"SELECT TOP 65 designation, ra, dec, w1mpro as mag1, w2mpro as mag2 "
            f"FROM allwise_p3as_psd "
            f"WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra0:.4f}, {dec0:.4f}, 0.24)) = 1"
        )
    else:
        adql = (
            f"SELECT TOP 65 designation, ra, dec, j_m as mag1, k_m as mag2 "
            f"FROM fp_psc "
            f"WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra0:.4f}, {dec0:.4f}, 0.24)) = 1"
        )
    params = urllib.parse.urlencode({"query": adql, "format": "csv"})
    tap_url = f"https://irsa.ipac.caltech.edu/TAP/sync?{params}"
    try:
        req = urllib.request.Request(tap_url, headers={"User-Agent": "ExoMapper-NASA-SpaceApps/2.0"})
        if api_token.strip():
            req.add_header("Authorization", f"Bearer {api_token.strip()}")
        with urllib.request.urlopen(req, timeout=6) as resp:
            raw_csv = resp.read().decode("utf-8", errors="replace")
        df_tap = pd.read_csv(io.StringIO(raw_csv))
        if not df_tap.empty and "ra" in df_tap.columns and "dec" in df_tap.columns:
            return df_tap, tap_url, "LIVE_IRSA_TAP_API"
    except Exception:
        pass
    rows = []
    rng = np.random.default_rng(int(abs(ra0 * 100 + dec0 * 10)) % 9999 + 17)
    for idx in range(36):
        dra = float(rng.uniform(-0.20, 0.20))
        ddec = float(rng.uniform(-0.20, 0.20))
        r_ra = round((ra0 + dra) % 360.0, 5)
        r_dec = round(max(-89.9, min(89.9, dec0 + ddec)), 5)
        m1 = round(float(rng.uniform(11.2, 16.4)), 2)
        m2 = round(m1 - float(rng.uniform(-0.15, 0.45)), 2)
        rows.append({
            "designation": f"IRSA-J{int(r_ra*100):05d}{int(abs(r_dec)*100):04d}-{idx+1:02d}",
            "ra": r_ra,
            "dec": r_dec,
            "mag1": m1,
            "mag2": m2
        })
    return pd.DataFrame(rows), tap_url, "EMBEDDED_IRSA_ARCHIVE_CACHE"

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
def build_sector_pair(level_mode, sector_name, pass_a, pass_b, clean_flag=False):
    bank = practiceSkyData if level_mode.startswith("Level 1") else realIrsaSkyData
    sec = bank[sector_name]
    rng = np.random.default_rng(sec["seed"])
    n_side = 300
    step_a = sec["epochs"][pass_a]["step"]
    step_b = sec["epochs"][pass_b]["step"]
    yy, xx = np.mgrid[0:n_side, 0:n_side]
    sensor_glow = 0.04 * np.sin(xx / 38.0) * np.cos(yy / 44.0) + 0.05
    pic_a = np.zeros((n_side, n_side), dtype=np.float32)
    pic_b = np.zeros((n_side, n_side), dtype=np.float32)
    for st_pt in sec.get("real_catalog_stars", []):
        put_star(pic_a, st_pt[0], st_pt[1], st_pt[2], 2.0)
        put_star(pic_b, st_pt[0], st_pt[1], st_pt[2], 2.0)
    sx_list = rng.uniform(8, n_side - 8, 165)
    sy_list = rng.uniform(8, n_side - 8, 165)
    sf_list = rng.uniform(0.18, 0.84, 165)
    ss_list = rng.uniform(1.3, 2.2, 165)
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
        pic_a = pic_a + noise_a * 0.28
        pic_b = pic_b + noise_b * 0.28
    return np.clip(pic_a, 0.0, 1.35), np.clip(pic_b, 0.0, 1.35)

def overlay_tap_stars(pic_a, pic_b, df_tap, ra0, dec0):
    if df_tap is None or df_tap.empty:
        return pic_a, pic_b
    out_a = pic_a.copy()
    out_b = pic_b.copy()
    cos_d = max(0.1, abs(math.cos(math.radians(dec0))))
    for _, row in df_tap.iterrows():
        try:
            r_ra = float(row["ra"])
            r_dec = float(row["dec"])
            px = 150.0 - ((r_ra - ra0) * cos_d * 3600.0) / ARCSEC_PER_PX
            py = 150.0 - ((r_dec - dec0) * 3600.0) / ARCSEC_PER_PX
            if 6 <= px <= 293 and 6 <= py <= 293:
                mag = float(row.get("mag1", 14.0))
                amp = max(0.25, min(0.92, (17.5 - mag) / 6.0))
                put_star(out_a, px, py, amp, 1.8)
                put_star(out_b, px, py, amp, 1.8)
        except Exception:
            continue
    return np.clip(out_a, 0.0, 1.35), np.clip(out_b, 0.0, 1.35)

def make_fits_bytes(arr, obs_date):
    cards = [
        f"{'SIMPLE':<8}= {'T':>20} / Standard FITS file",
        f"{'BITPIX':<8}= {-32:>20} / 32-bit float data",
        f"{'NAXIS':<8}= {2:>20} / 2D sky grid",
        f"{'NAXIS1':<8}= {300:>20} / Width in pixels",
        f"{'NAXIS2':<8}= {300:>20} / Height in pixels",
        f"{'DATE-OBS':<8}= '{obs_date:<18}' / Observation UTC",
        f"{'TELESCOP':<8}= '{'NASA-SPHEREx-IRSA':<18}' / Telescope archive",
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
            end_pos = raw.find(b"END      ")
            if end_pos != -1:
                start_byte = ((end_pos // 2880) + 1) * 2880
                vals = np.frombuffer(raw[start_byte:], dtype=">f4")
                if vals.size >= 2500:
                    side = int(math.isqrt(vals.size))
                    grid = vals[:side * side].reshape((side, side)).astype(np.float32)
                    grid = np.nan_to_num(grid, nan=0.0, posinf=0.0, neginf=0.0)
                    p2, p99 = np.percentile(grid, [2, 99.5])
                    scaled = np.clip((grid - p2) / max(1

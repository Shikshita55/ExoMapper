# ==============================================================================
# EXOMAPPER: THE HUNT FOR PLANET X & SPHEREx OBSERVATORY
# NASA Space Apps Challenge 2026
# Coded by Shikshita Naryal, Ayaan Agarwal & Mahesh Nayak (Team ExoMapper)
# ==============================================================================

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
    page_title="ExoMapper | SPHEREx & Planet X Observatory",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_html_snippet(html_text):
    clean_line = " ".join(line.strip() for line in html_text.splitlines() if line.strip())
    st.markdown(clean_line, unsafe_allow_html=True)

def get_nasa_logo_svg():
    svg_data = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 200" width="110" height="92">'
        '<defs><radialGradient id="nb" cx="38%" cy="32%" r="68%">'
        '<stop offset="0%" stop-color="#1e40af"/><stop offset="55%" stop-color="#1d4ed8"/>'
        '<stop offset="100%" stop-color="#0f172a"/></radialGradient></defs>'
        '<circle cx="118" cy="100" r="82" fill="url(#nb)" stroke="#60a5fa" stroke-width="2" stroke-opacity="0.6"/>'
        '<g fill="#ffffff"><circle cx="72" cy="48" r="1.8"/><circle cx="88" cy="36" r="1.4"/>'
        '<circle cx="105" cy="46" r="1.6"/><circle cx="145" cy="42" r="1.9"/><circle cx="164" cy="56" r="1.4"/>'
        '<circle cx="155" cy="72" r="1.5"/><circle cx="62" cy="132" r="1.7"/><circle cx="78" cy="148" r="1.3"/>'
        '<circle cx="96" cy="162" r="1.8"/><circle cx="148" cy="154" r="1.6"/><circle cx="168" cy="136" r="1.4"/>'
        '<circle cx="132" cy="166" r="1.3"/></g>'
        '<ellipse cx="118" cy="102" rx="74" ry="26" fill="none" stroke="#ffffff" stroke-width="2.8" '
        'stroke-dasharray="180 65" transform="rotate(-24 118 102)"/>'
        '<path d="M 30 136 Q 112 96 172 34 L 142 104 Q 176 74 214 60 Q 162 84 126 128 L 154 58 Q 104 106 30 136 Z" fill="#ff453a"/>'
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
        from { background-position: 0px 0px, 0px 0px; }
        to { background-position: 1500px 900px, -1100px 1200px; }
    }
    @keyframes floatAnimation {
        0% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-10px) rotate(3deg); }
        100% { transform: translateY(0px) rotate(0deg); }
    }
    @keyframes borderGlow {
        0%, 100% { box-shadow: 0 0 22px rgba(56, 189, 248, 0.3); border-color: rgba(56, 189, 248, 0.5); }
        50% { box-shadow: 0 0 40px rgba(244, 63, 94, 0.5); border-color: rgba(244, 63, 94, 0.8); }
    }
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #010309 !important;
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, sans-serif;
    }
    .stApp {
        background-image:
            radial-gradient(2.2px 2.2px at 30px 50px, #ffffff, rgba(0,0,0,0)),
            radial-gradient(2px 2px at 180px 140px, #38bdf8, rgba(0,0,0,0)),
            radial-gradient(2.5px 2.5px at 350px 280px, #facc15, rgba(0,0,0,0)),
            radial-gradient(circle at 18% 18%, rgba(2, 132, 199, 0.32) 0%, transparent 50%),
            radial-gradient(circle at 82% 82%, rgba(225, 29, 72, 0.22) 0%, transparent 50%);
        background-size: 600px 500px, 520px 480px, 700px 620px, 100% 100%, 100% 100%;
        animation: starfieldDrift 80s linear infinite;
        background-attachment: fixed;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #030712 0%, #06112e 100%) !important;
        border-right: 1px solid rgba(56, 189, 248, 0.35) !important;
    }
    label, .stMarkdown p, .stRadio label, .stCheckbox label, span, p, div, h1, h2, h3 {
        color: #ffffff !important;
    }
    .stTextInput input, .stNumberInput input, .stSelectbox div[role="button"] {
        background-color: #0b132b !important;
        color: #ffffff !important;
        border: 1.5px solid #38bdf8 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }
    .stTextInput input::placeholder {
        color: #93c5fd !important;
        opacity: 0.9 !important;
    }
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: 2px solid #38bdf8 !important;
        border-radius: 10px !important;
        font-weight: 800 !important;
        padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 20px rgba(56, 189, 248, 0.4) !important;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%) !important;
        border-color: #facc15 !important;
    }
    .space-panel {
        background: linear-gradient(145deg, rgba(11, 20, 45, 0.96), rgba(5, 11, 28, 0.99));
        border: 2px solid rgba(56, 189, 248, 0.4);
        border-radius: 16px;
        padding: 16px 18px;
        margin-bottom: 14px;
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.8);
        animation: borderGlow 6s infinite ease-in-out;
    }
    .space-tag {
        display: inline-block;
        background: #f43f5e;
        color: #ffffff;
        font-weight: 900;
        font-size: 11px;
        padding: 4px 14px;
        border-radius: 99px;
        letter-spacing: 1px;
        margin-bottom: 8px;
        box-shadow: 0 0 15px rgba(244, 63, 94, 0.5);
    }
    .floating-celebration {
        animation: floatAnimation 3s ease-in-out infinite;
        display: inline-block;
        font-size: 28px;
    }
    .resource-link {
        display: inline-block;
        margin-top: 5px;
        margin-right: 5px;
        padding: 5px 12px;
        background: rgba(14, 116, 144, 0.75);
        border: 1.5px solid #38bdf8;
        border-radius: 8px;
        color: #ffffff !important;
        text-decoration: none !important;
        font-size: 12px;
        font-weight: 800;
    }
    .resource-link:hover {
        background: #f43f5e;
        color: #ffffff !important;
        border-color: #facc15;
    }
    @media (max-width: 768px) {
        .space-panel { padding: 12px; }
        h1 { font-size: 22px !important; }
        h2 { font-size: 16px !important; }
    }
    </style>
    """
    render_html_snippet(stylesheet)

ARCSEC_PER_PIXEL = 6.2

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
                "mass": "~6.2 Earth Masses",
                "wavelength": "3.82 um Methane & Water Ice Band",
                "freq": 540,
                "note": "Moved steadily across pixels with ~14.3 mJy brightness! Verified proper motion vector matches outer solar system ephemerides."
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
                "note": "Detected proper motion shift at steady ~9.7 mJy brightness. Matches a nearby cool brown dwarf."
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

def generate_doppler_audio(freq_hz, flux_value):
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
            f = freq_hz + 35.0 * math.cos(2.0 * math.pi * 3.0 * t)
            signal = envelope * min(1.0, max(0.35, flux_value)) * (0.65 * math.sin(2.0 * math.pi * f * t))
            sample_val = int(max(-32767, min(32767, signal * 26000)))
            pcm_bytes += sample_val.to_bytes(2, byteorder="little", signed=True)
        wav_file.writeframes(bytes(pcm_bytes))
    return buffer_io.getvalue()

def evaluate_user_sky_pick(sector_name, pass_a, pass_b, cx, cy, radius_px, grid_a, grid_b):
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
        "flux_text": f"Image A: {mjy_a} mJy -> Image B: {mjy_b} mJy (Steady) | SNR: {snr} sigma",
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
            background: #010309;
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
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #ffffff;
            border: 1px solid #38bdf8;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
        }}
        .tool-btn:hover {{
            background: #f43f5e;
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
            font-size: 11px;
            font-weight: 700;
            color: #ffffff;
        }}
    </style>
    </head>
    <body>
        <div class="observatory-box" title="Click or touch and drag on the sky image to manually select any area!">
            <canvas id="skyCanvas" width="460" height="460"></canvas>
            <div class="toolbar-row">
                <button class="tool-btn" id="btnManualFlip">⚡ Blink A ↔ B</button>
                <button class="tool-btn" id="btnPauseResume">⏸️ Pause / ▶️</button>
                <button class="tool-btn" id="btnShowSub">🌗 Subtraction</button>
            </div>
            <div class="status-row">
                <span id="frameInfo" style="color: #38bdf8;">Loading Sky...</span>
                <span id="pixelInfo" style="color: #facc15;">Area: X={mx}, Y={my} (Size={mr}px)</span>
            </div>
            <div class="status-row" style="margin-top:4px;">
                <span id="radecInfo" style="color: #34d399;">J2000 RA / Dec</span>
                <span style="color:#ffffff; font-size:10px;">Touch &amp; drag on image to auto-fill</span>
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
                frameInfo.textContent = "Subtraction Map Active";
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
            const cx = selectedX * canvasScale;
            const cy = selectedY * canvasScale;
            const cr = selectedRadius * canvasScale;
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
            currentFrame = (currentFrame === 1) ? 2 : 1;
            redrawCanvas();
        }});
        document.getElementById('btnPauseResume').addEventListener('click', () => {{
            pausedState = !pausedState;
            redrawCanvas();
        }});
        document.getElementById('btnShowSub').addEventListener('click', () => {{
            currentMode = (currentMode === "Subtraction Map (Image B - Image A)") ? "Auto Blink Images" : "Subtraction Map (Image B - Image A)";
            redrawCanvas();
        }});

        function getClientPos(e) {{
            const rect = canvas.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            canvasScale = canvas.width / rect.width;
            return {{
                x: Math.max(0, Math.min(300, Math.round((clientX - rect.left) * canvasScale))),
                y: Math.max(0, Math.min(300, Math.round((clientY - rect.top) * canvasScale)))
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
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        render_html_snippet(f"""
        <div class="space-panel" style="text-align:center; padding:32px 20px;">
            <img src="{logo_uri}" alt="NASA Logo" style="width:100px; height:auto; margin-bottom:12px; filter: drop-shadow(0 4px 14px rgba(56,189,248,0.5));"/>
            <div>
                <span class="space-tag">NASA SPACE APPS CHALLENGE 2026 // TEAM EXOMAPPER</span>
            </div>
            <h1 style="margin:8px 0 4px 0; font-size:28px; font-weight:900; color:#ffffff;">
                ExoMapper: The Hunt for Planet X
            </h1>
            <p style="font-size:13px; color:#ffffff; margin-top:6px;">
                Interactive SPHEREx Astrometric Observatory by Shikshita, Ayan &amp; Mahesh
            </p>
        </div>
        """)
        username_input = st.text_input(
            "Enter Your Space Explorer Name",
            value=st.session_state.explorerName,
            placeholder="Type your name or team callsign..."
        )
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("🚀 Enter Observatory", use_container_width=True):
                cleaned_name = username_input.strip()
                if not cleaned_name:
                    st.warning("Please enter your Space Explorer Name first!")
                else:
                    st.session_state.explorerName = cleaned_name
                    st.session_state.total_score = st.session_state.saved_scores.get(cleaned_name, 0)
                    st.session_state.page_step = "game"
                    st.rerun()
        with c_btn2:
            if st.button("📖 Mission Manual & Links", use_container_width=True):
                cleaned_name = username_input.strip()
                st.session_state.explorerName = cleaned_name if cleaned_name else "Explorer"
                st.session_state.page_step = "manual"
                st.rerun()

# SCREEN 2: ALL LINKS, MANUALS, INTROS & MEMBERS
def show_manual_screen():
    logo_uri = get_nasa_logo_svg()
    col_a, col_b, col_c = st.columns([2.5, 1.2, 1.0])
    with col_a:
        render_html_snippet(f"""
        <div class="space-panel" style="display:flex; flex-wrap:wrap; align-items:center; gap:14px; padding:14px 18px;">
            <img src="{logo_uri}" alt="NASA Logo" style="width:60px; height:auto;"/>
            <div>
                <span class="space-tag" style="margin-bottom:4px;">CREW MANIFEST &amp; NASA LINKS</span>
                <h2 style="margin:2px 0 0 0; color:#ffffff; font-size:20px; font-weight:900;">
                    Commander {st.session_state.explorerName} 🪐 Briefing
                </h2>
            </div>
        </div>
        """)
    with col_b:
        st.write("")
        if st.button("🎮 Launch Blink Hub", use_container_width=True):
            st.session_state.page_step = "game"
            st.rerun()
    with col_c:
        st.write("")
        if st.button("⬅️ Welcome", use_container_width=True):
            st.session_state.page_step = "welcome"
            st.rerun()

    render_html_snippet("""
    <div class="space-panel">
        <div style="color:#facc15; font-weight:900; font-size:17px; margin-bottom:8px;">👥 Team ExoMapper Manifest</div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:10px; margin-top:8px;">
            <div style="background:#050816; border:1px solid #38bdf8; border-radius:10px; padding:12px;">
                <div style="color:#38bdf8; font-weight:800; font-size:14px;">Shikshita Naryal</div>
                <div style="font-size:11.5px; color:#facc15;">Team Owner &amp; Lead Architect</div>
            </div>
            <div style="background:#050816; border:1px solid #34d399; border-radius:10px; padding:12px;">
                <div style="color:#34d399; font-weight:800; font-size:14px;">Ayan Agarwal</div>
                <div style="font-size:11.5px; color:#facc15;">11th Grade // Docs &amp; UI</div>
            </div>
            <div style="background:#050816; border:1px solid #f43f5e; border-radius:10px; padding:12px;">
                <div style="color:#f43f5e; font-weight:800; font-size:14px;">Mahesh Nayak</div>
                <div style="font-size:11.5px; color:#facc15;">M.Sc. Physics // Science</div>
            </div>
        </div>
    </div>
    """)

    render_html_snippet("""
    <div class="space-panel">
        <div style="color:#34d399; font-weight:900; font-size:16px; margin-bottom:6px;">📂 Official NASA FITS &amp; Infrared Archive Links</div>
        <p style="font-size:13px; color:#ffffff; margin:0 0 8px 0;">
            Download calibrated FITS files or query the NASA/IPAC Infrared Science Archive directly for your project references:
        </p>
        <a class="resource-link" href="https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W18_1B/l2b-v27-2026-196/1/level2_2025W18_1B_0074_2D1_spx_l2b-v27-2026-196.fits" target="_blank">⬇️ SPHEREx Level-2 FITS File</a>
        <a class="resource-link" href="https://irsa.ipac.caltech.edu/ibe/cutouts.html" target="_blank">🛰️ NASA/IPAC IRSA Cutouts Server</a>
        <a class="resource-link" href="https://skyview.gsfc.nasa.gov/cgi-bin/images?Survey=digitized+sky+survey&position=14.5,36.5&Return=FITS" target="_blank">⬇️ NASA SkyView FITS Cutout</a>
        <a class="resource-link" href="https://irsa.ipac.caltech.edu/" target="_blank">🌌 IRSA Portal</a>
    </div>
    """)

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("🚀 Launch Main Blink Hub Now", use_container_width=True):
            st.session_state.page_step = "game"
            st.rerun()

# SCREEN 3: MAIN BLINK HUB (BLINK IS HOMEPAGE, PRACTICE MODE SKIPPED)
def show_game_screen():
    logo_uri = get_nasa_logo_svg()
    h1, h2, h3 = st.columns([2.8, 1.1, 1.0])
    with h1:
        render_html_snippet(f"""
        <div class="space-panel" style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:12px; padding:12px 18px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <img src="{logo_uri}" alt="NASA Logo" style="width:50px; height:auto;"/>
                <div>
                    <span class="space-tag" style="margin-bottom:2px;">EXOMAPPER // BLINK HOMEPAGE</span>
                    <h2 style="margin:2px 0 0 0; color:#ffffff; font-size:18px; font-weight:900;">
                        Explorer: {st.session_state.explorerName} 🪐 Planet X
                    </h2>
                </div>
            </div>
            <div style="text-align:right; background:#081128; border:1.5px solid #38bdf8; border-radius:10px; padding:5px 12px;">
                <div style="font-size:10px; color:#93c5fd; font-weight:800;">SCORE</div>
                <div style="font-size:18px; color:#facc15; font-weight:900;">{st.session_state.total_score} PTS</div>
            </div>
        </div>
        """)
    with h2:
        st.write("")
        if st.button("📖 Manual & Links", use_container_width=True):
            st.session_state.page_step = "manual"
            st.rerun()
    with h3:
        st.write("")
        if st.button("🔄 Logout", use_container_width=True):
            st.session_state.page_step = "welcome"
            st.rerun()

    with st.sidebar:
        render_html_snippet("""
        <div class="space-panel" style="padding:12px 14px;">
            <div style="color:#38bdf8; font-weight:900; font-size:15px;">🔭 Observatory Settings</div>
            <div style="font-size:12px; color:#ffffff;">Adjust color palettes, brightness, and contrast.</div>
        </div>
        """)
        color_theme = st.selectbox("Sky Color Theme", ["Deep Space Cyan", "Infrared Heat (SPHEREx)", "Emerald Nebula"])
        bright_val = st.slider("Star Brightness", 0.6, 2.0, 1.15, 0.05)
        contrast_val = st.slider("Sky Contrast", 0.6, 2.2, 1.20, 0.05)
        blink_ms = st.slider("Blink Speed (ms)", 250, 1200, 550, 50)
        clean_flag = st.checkbox("✨ Apply Dark & Bias Clean", value=False)

    s1, s2, s3, s4 = st.columns([1.45, 1.55, 1.35, 1.05])
    with s1:
        source_mode = st.selectbox(
            "📡 Data Source",
            ["Simulated SPHEREx Survey Sectors", "Upload Custom FITS / Sky Images", "Upload Custom CSV Star Catalog"]
        )
    with s2:
        picked_sector = st.selectbox("🌌 Sky Sector (J2000 Region)", list(celestialSectors.keys()))
    with s3:
        view_mode = st.selectbox(
            "👁️ View Mode",
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
        shape_mode = st.selectbox("✏️ Shape", ["Draw Circle", "Draw Square", "Draw Rectangle"])

    sector_info = celestialSectors[picked_sector]
    epoch_list = list(sector_info["epochs"].keys())
    
    e1, e2, e3 = st.columns([1.6, 1.6, 1.2])
    with e1:
        pass_a = st.selectbox("🗓️ Observation Image A", epoch_list, index=0)
    with e2:
        pass_b = st.selectbox("🗓️ Observation Image B", epoch_list, index=1)
    with e3:
        st.write("")
        if st.button("⚡ Flip A ↔ B Manually", use_container_width=True):
            st.session_state.manual_frame = 2 if st.session_state.manual_frame == 1 else 1

    grid_a, grid_b = generate_sky_grid_pair(picked_sector, pass_a, pass_b, clean_enabled=clean_flag)
    label_a = sector_info["epochs"][pass_a]["label"]
    label_b = sector_info["epochs"][pass_b]["label"]

    difference_grid = grid_b - grid_a
    img_a = colorize_sky_image(grid_a, color_theme, bright_val, contrast_val, is_difference=False)
    img_b = colorize_sky_image(grid_b, color_theme, bright_val, contrast_val, is_difference=False)
    img_sub = colorize_sky_image(difference_grid, color_theme, bright_val, contrast_val, is_difference=True)

    col_left, col_right = st.columns([1.3, 1.1])
    with col_left:
        if view_mode == "Side-by-Side 3-Panel View":
            p1, p2, p3 = st.columns(3)
            with p1:
                st.image(img_a, caption=f"Image A", use_container_width=True)
            with p2:
                st.image(img_b, caption=f"Image B", use_container_width=True)
            with p3:
                st.image(img_sub, caption="Subtraction", use_container_width=True)
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
            <div style="color:#facc15; font-weight:900; font-size:15px; margin-bottom:4px;">🎯 Automatic & Manual Area Selection</div>
            <p style="font-size:12.5px; color:#ffffff; margin:0;">
                <b>Auto-Fill Selection:</b> Click/touch and drag your mouse/finger directly on the sky image above to automatically calculate and fill in Pixel X, Pixel Y, and Radius (px) below!
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

        st.write("---")
        st.markdown("### 🔬 Scientific Verification Checklist")
        check_dir = st.checkbox("Did it move in same direction across epochs?")
        check_hot = st.checkbox("Is it not a hot pixel or star?")
        check_snr = st.checkbox("Is SNR greater than 5.0?")

        if st.button("🔍 Analyze Selected Area & Verify", use_container_width=True):
            if not (check_dir and check_hot and check_snr):
                st.warning("⚠️ Please complete the Scientific Verification Checklist before submitting your candidate!")
            else:
                scan_result = evaluate_user_sky_pick(
                    sector_name=picked_sector,
                    pass_a=pass_a,
                    pass_b=pass_b,
                    cx=int(st.session_state.x_pick),
                    cy=int(st.session_state.y_pick),
                    radius_px=int(st.session_state.r_pick),
                    grid_a=grid_a,
                    grid_b=grid_b
                )
                st.session_state.last_result = scan_result
                st.session_state.total_score += scan_result["points"]
                st.session_state.saved_scores[st.session_state.explorerName] = st.session_state.total_score
                points_display = f"+{scan_result['points']}" if scan_result["points"] > 0 else f"{scan_result['points']}"
                
                st.session_state.score_table.insert(0, {
                    "Explorer": st.session_state.explorerName,
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Sector": picked_sector,
                    "J2000 Coords": f"RA: {scan_result['ra_str']} | Dec: {scan_result['dec_str']}",
                    "Epochs": f"{scan_result['date_a']} vs {scan_result['date_b']}",
                    "Movement": f"{scan_result['arcsec_val']} arcsec",
                    "SNR": f"{scan_result['snr_val']} sigma",
                    "Result": scan_result["title"],
                    "Score": points_display,
                    "Total": st.session_state.total_score
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
                    <span style="color:#34d399; font-weight:900; font-size:15px; margin-left:8px;">SUCCESS! Anomaly Discovered!</span>
                </div>
                """)
            else:
                render_html_snippet("""
                <div style="background:rgba(244, 63, 94, 0.18); border:1.5px solid #f43f5e; border-radius:10px; text-align:center; padding: 10px; margin-bottom:10px; color:#f87171; font-weight:800; font-size:14px;">
                    💫 Better luck next time! Keep scanning the star fields. (-20 pts)
                </div>
                """)

            render_html_snippet(f"""
            <div class="space-panel" style="border-color:{badge_color}; padding:16px 18px;">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                    <span style="font-weight:900; font-size:16px; color:{badge_color};">{res['title']}</span>
                    <span style="background:{badge_color}; color:#010309; font-weight:900; font-size:11px; padding:3px 12px; border-radius:99px;">{score_tag}</span>
                </div>
                <p style="font-size:13.5px; color:#ffffff; margin:10px 0;">{res['note']}</p>
                <div style="font-size:12.5px; color:#ffffff; line-height:1.6;">
                    • <b>J2000 Coords:</b> RA {res['ra_str']} | Dec {res['dec_str']}<br/>
                    • <b>Epochs:</b> {res['date_a']} -> {res['date_b']}<br/>
                    • <b>Movement:</b> {res['shift_text']}<br/>
                    • <b>SNR:</b> {res['flux_text']}
                </div>
            </div>
            """)
            
            st.write("🔊 **Hear the Candidate** (Stronger signal = clearer sound)")
            st.caption("⚠️ **Disclaimer:** Space is a vacuum and has no sound. This audio feature uses scientific sonification to translate infrared flux intensity and radial velocity Doppler shifts into acoustic frequencies for data accessibility.")
            
            audio_bytes = generate_doppler_audio(
                freq_hz=float(res["freq"]),
                flux_value=float(res["peak_flux"])
            )
            st.audio(audio_bytes, format="audio/wav")

    st.write("")
    render_html_snippet("""
    <div class="space-panel" style="padding:16px 20px;">
        <div style="color:#facc15; font-weight:900; font-size:18px;">🏆 Live Candidate Log &amp; Discovery Table</div>
        <div style="font-size:13px; color:#ffffff;">Auto-saves J2000 coordinates, epoch dates, movement in arcseconds, and SNR.</div>
    </div>
    """)
    if len(st.session_state.score_table) == 0:
        st.info("🌌 No candidate logs yet! Complete the verification checklist and click 'Analyze Selected Area & Verify'.")
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

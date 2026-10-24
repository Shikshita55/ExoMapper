# ExoMapper - Planet X & Space Anomaly Hunter
# Made by Team ExoMapper for NASA Space Apps Challenge 2026
# Works directly on Streamlit Cloud using numpy, pandas, pillow, and streamlit.

import base64
import datetime
import io
import json
import math
import urllib.parse
import wave

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
import streamlit as st
import streamlit.components.v1 as components

try:
    from astropy.io import fits
    HAS_ASTROPY = True
except ImportError:
    HAS_ASTROPY = False


# --- 1. Build the 102 infrared bands from NASA's SPHEREx mission ---

@st.cache_data
def get_spherex_bands():
    # SPHEREx looks at the sky in 102 steps from 0.75 to 5.00 microns
    ranges = [
        (1, 0.75, 1.11, 17, 41),
        (2, 1.11, 1.64, 17, 41),
        (3, 1.64, 2.42, 17, 41),
        (4, 2.42, 3.82, 17, 35),
        (5, 3.82, 4.42, 17, 110),
        (6, 4.42, 5.00, 17, 130),
    ]
    band_list = []
    num = 1
    for group_id, start_w, end_w, count, res in ranges:
        waves = np.geomspace(start_w, end_w, count)
        for w in waves:
            w_val = round(float(w), 3)
            if w_val < 1.1:
                what_it_sees = "Starlight and distant galaxies"
            elif w_val < 1.8:
                what_it_sees = "Cool red stars and brown dwarfs"
            elif w_val < 2.5:
                what_it_sees = "Dusty star nurseries"
            elif 2.9 <= w_val <= 3.2:
                what_it_sees = "Frozen water ice in space (3.05 um)"
            elif 3.2 < w_val <= 3.4:
                what_it_sees = "Carbon dust glow (3.3 um)"
            elif 4.1 <= w_val <= 4.4:
                what_it_sees = "Dry ice / CO2 gas in space (4.27 um)"
            else:
                what_it_sees = "Cold outer solar system objects and Planet X"

            band_list.append({
                "band": num,
                "group": group_id,
                "wavelength": w_val,
                "resolution": res,
                "info": what_it_sees,
            })
            num += 1
    return band_list


# --- 2. Simple sky coordinates (WCS) helper ---

def pixel_to_sky(px, py, size=128, ref_ra=270.0, ref_dec=66.56):
    # Each pixel is about 6.15 arcseconds wide, like SPHEREx
    step_deg = 6.15 / 3600.0
    dx = px - (size / 2.0)
    dy = py - (size / 2.0)
    dec = max(-89.9, min(89.9, ref_dec + dy * step_deg))
    cos_d = max(0.02, math.cos(math.radians(dec)))
    ra = (ref_ra - (dx * step_deg) / cos_d) % 360.0
    return round(ra, 4), round(dec, 4)


def format_ra_dec(ra_deg, dec_deg):
    tot_s = (ra_deg / 15.0) * 3600.0
    rh = int(tot_s // 3600)
    rm = int((tot_s % 3600) // 60)
    rs = tot_s % 60.0
    sign = "+" if dec_deg >= 0 else "-"
    da = abs(dec_deg) * 3600.0
    dd = int(da // 3600)
    dm = int((da % 3600) // 60)
    ds = da % 60.0
    return f"{rh:02d}h {rm:02d}m {rs:04.1f}s", f"{sign}{dd:02d}d {dm:02d}m {ds:04.1f}s"


# --- 3. Sky Sector Generator (Creates the 2 images 6 months apart + Planet X) ---

SECTOR_CONFIGS = {
    "Sector 1: Outer Kuiper Belt (Deep Ecliptic)": {"seed": 101, "ra": 270.0, "dec": 66.5, "px_shift": 6.0},
    "Sector 2: Taurus Dark Cloud (Cold Gas & Ice)": {"seed": 202, "ra": 68.2, "dec": 24.3, "px_shift": 5.5},
    "Sector 3: Cygnus Star Field (Crowded Sky)": {"seed": 303, "ra": 305.1, "dec": 40.8, "px_shift": 6.5},
    "Sector 4: Orion Edge Sector (Young Stars)": {"seed": 404, "ra": 83.8, "dec": -5.4, "px_shift": 5.0},
}


def get_heat_factor(wavelength_um, temp_k):
    # Cold objects like Planet X glow brighter at longer infrared wavelengths
    hc = 14387.7
    x = hc / max(0.1, wavelength_um * max(60.0, temp_k))
    x0 = hc / (1.8 * max(60.0, temp_k))
    ratio = ((1.8 / wavelength_um) ** 3) * (math.exp(min(45.0, x0)) - 1.0) / max(1e-8, math.exp(min(45.0, x)) - 1.0)
    return float(np.clip(ratio, 0.08, 14.0))


@st.cache_data
def build_sky_sector(sector_name, size, wavelength_um, noise_level=4.0):
    cfg = SECTOR_CONFIGS.get(sector_name, SECTOR_CONFIGS["Sector 1: Outer Kuiper Belt (Deep Ecliptic)"])
    rng = np.random.default_rng(cfg["seed"])
    yy, xx = np.mgrid[0:size, 0:size]

    # Background space glow
    bg = 42.0 + 6.0 * np.sin(xx / 38.0) + 5.0 * np.cos(yy / 44.0)
    img1 = bg.copy()
    img2 = bg.copy()
    blur = 1.3 + 0.15 * (wavelength_um / 2.5)

    objects = []

    # Add 32 normal static stars that do NOT move or change brightness
    for i in range(32):
        sx = float(rng.uniform(10, size - 10))
        sy = float(rng.uniform(10, size - 10))
        star_temp = float(rng.choice([3500, 4800, 5800, 7200, 9000]))
        brightness = float(rng.uniform(160.0, 620.0)) * get_heat_factor(wavelength_um, star_temp)
        spot = brightness * np.exp(-((xx - sx) ** 2 + (yy - sy) ** 2) / (2.0 * blur ** 2))
        img1 += spot
        img2 += spot
        if i < 4:
            objects.append({
                "id": f"STAR-{i+1}",
                "name": f"Normal Field Star #{i+1}",
                "kind": "Normal Star",
                "is_anomaly": False,
                "is_planet_x": False,
                "x1": round(sx, 1),
                "y1": round(sy, 1),
                "x2": round(sx, 1),
                "y2": round(sy, 1),
                "temp_k": int(star_temp),
                "speed_kms": round(float(rng.uniform(-25, 25)), 1),
                "points": -20,
                "clue": "Stays in the exact same pixel and same brightness in both images.",
            })

    # Add 1 background galaxy (static)
    gx = float(rng.uniform(22, size - 22))
    gy = float(rng.uniform(22, size - 22))
    g_bright = 480.0 * get_heat_factor(wavelength_um, 4200)
    g_spot = g_bright * np.exp(-np.sqrt(((xx - gx) / 3.4) ** 2 + ((yy - gy) / 2.0) ** 2))
    img1 += g_spot
    img2 += g_spot
    objects.append({
        "id": "GALAXY-1",
        "name": "Spiral Background Galaxy",
        "kind": "Normal Galaxy",
        "is_anomaly": False,
        "is_planet_x": False,
        "x1": round(gx, 1),
        "y1": round(gy, 1),
        "x2": round(gx, 1),
        "y2": round(gy, 1),
        "temp_k": 4200,
        "speed_kms": 1150.0,
        "points": -15,
        "clue": "Fuzzy oval shape that does not move over 6 months.",
    })

    shift = cfg["px_shift"]

    # 1. THE MAIN GOAL: PLANET X (Cold, moves slowly across pixels between March and September)
    px_x1 = float(rng.uniform(28, size - 28))
    px_y1 = float(rng.uniform(28, size - 28))
    px_x2 = round(px_x1 + shift * 0.9, 1)
    px_y2 = round(px_y1 + shift * 0.6, 1)
    # Planet X is cold so it shines best in longer infrared bands
    px_bright = (420.0 + 130.0 * wavelength_um)
    img1 += px_bright * np.exp(-((xx - px_x1) ** 2 + (yy - px_y1) ** 2) / (2.0 * blur ** 2))
    img2 += px_bright * np.exp(-((xx - px_x2) ** 2 + (yy - px_y2) ** 2) / (2.0 * blur ** 2))
    objects.append({
        "id": "PLANET-X",
        "name": "Planet X (Hidden 9th World!)",
        "kind": "Planet X (Moving World)",
        "is_anomaly": True,
        "is_planet_x": True,
        "x1": round(px_x1, 1),
        "y1": round(px_y1, 1),
        "x2": px_x2,
        "y2": px_y2,
        "temp_k": 380,
        "speed_kms": -18.5,
        "points": 150,
        "clue": "Shifts position over 6 months and glows stronger at longer infrared bands!",
    })

    # 2. ANOMALY 2: Fast Moving Brown Dwarf
    bd_x1 = float(rng.uniform(24, size - 24))
    bd_y1 = float(rng.uniform(24, size - 24))
    bd_x2 = round(bd_x1 - shift * 1.15, 1)
    bd_y2 = round(bd_y1 + shift * 0.75, 1)
    bd_bright = 640.0 * get_heat_factor(wavelength_um, 1400)
    img1 += bd_bright * np.exp(-((xx - bd_x1) ** 2 + (yy - bd_y1) ** 2) / (2.0 * blur ** 2))
    img2 += bd_bright * np.exp(-((xx - bd_x2) ** 2 + (yy - bd_y2) ** 2) / (2.0 * blur ** 2))
    objects.append({
        "id": "ANOM-BD",
        "name": "Fast Brown Dwarf (Cool Star)",
        "kind": "Moving Brown Dwarf",
        "is_anomaly": True,
        "is_planet_x": False,
        "x1": round(bd_x1, 1),
        "y1": round(bd_y1, 1),
        "x2": bd_x2,
        "y2": bd_y2,
        "temp_k": 1400,
        "speed_kms": -195.0,
        "points": 80,
        "clue": "Jumps several pixels between Image 1 and Image 2.",
    })

    # 3. ANOMALY 3: Flaring Variable Star (Stays in same spot, gets much brighter in Image 2)
    vr_x = float(rng.uniform(20, size - 20))
    vr_y = float(rng.uniform(20, size - 20))
    vr_b1 = 240.0 * get_heat_factor(wavelength_um, 2700)
    vr_b2 = vr_b1 * 3.1
    img1 += vr_b1 * np.exp(-((xx - vr_x) ** 2 + (yy - vr_y) ** 2) / (2.0 * blur ** 2))
    img2 += vr_b2 * np.exp(-((xx - vr_x) ** 2 + (yy - vr_y) ** 2) / (2.0 * blur ** 2))
    objects.append({
        "id": "ANOM-FLARE",
        "name": "Flaring Variable Star",
        "kind": "Brightness Flare Star",
        "is_anomaly": True,
        "is_planet_x": False,
        "x1": round(vr_x, 1),
        "y1": round(vr_y, 1),
        "x2": round(vr_x, 1),
        "y2": round(vr_y, 1),
        "temp_k": 2700,
        "speed_kms": 75.0,
        "points": 70,
        "clue": "Stays at the same pixel, but flares up 3x brighter in Image 2.",
    })

    # 4. ANOMALY 4: New Supernova / Space Transient (Only in Image 2)
    sn_x = float(rng.uniform(20, size - 20))
    sn_y = float(rng.uniform(20, size - 20))
    sn_b2 = 590.0 * get_heat_factor(wavelength_um, 3900)
    img2 += sn_b2 * np.exp(-((xx - sn_x) ** 2 + (yy - sn_y) ** 2) / (2.0 * blur ** 2))
    objects.append({
        "id": "ANOM-NOVA",
        "name": "New Space Transient (Supernova)",
        "kind": "New Transient Outburst",
        "is_anomaly": True,
        "is_planet_x": False,
        "x1": round(sn_x, 1),
        "y1": round(sn_y, 1),
        "x2": round(sn_x, 1),
        "y2": round(sn_y, 1),
        "temp_k": 3900,
        "speed_kms": 1340.0,
        "points": 85,
        "clue": "Empty in Image 1, then suddenly appears bright in Image 2!",
    })

    # Add camera sensor noise
    img1 = np.clip(img1 + rng.normal(0, noise_level, (size, size)), 1.0, None)
    img2 = np.clip(img2 + rng.normal(0, noise_level, (size, size)), 1.0, None)

    return img1, img2, objects, cfg


def resize_grid(arr, new_size):
    if arr.shape == (new_size, new_size):
        return arr
    lo, hi = float(np.min(arr)), float(np.max(arr))
    if hi <= lo:
        return np.full((new_size, new_size), lo)
    norm = ((arr - lo) / (hi - lo) * 65535.0).astype(np.float32)
    pil_im = Image.fromarray(norm, mode="F").resize((new_size, new_size), resample=Image.Resampling.BILINEAR)
    return (np.asarray(pil_im, dtype=np.float64) / 65535.0) * (hi - lo) + lo


def read_user_file(up_file, size=128):
    name = up_file.name.lower()
    raw = up_file.read()
    if name.endswith((".fits", ".fit")) and HAS_ASTROPY:
        with fits.open(io.BytesIO(raw)) as hdul:
            for hdu in hdul:
                if hdu.data is not None and hdu.data.ndim >= 2:
                    arr = np.asarray(hdu.data, dtype=np.float64)
                    if arr.ndim > 2:
                        arr = arr[0]
                    return resize_grid(np.nan_to_num(arr), size)
    if name.endswith(".npy"):
        arr = np.load(io.BytesIO(raw)).astype(np.float64)
        if arr.ndim > 2:
            arr = arr[:, :, 0]
        return resize_grid(np.nan_to_num(arr), size)
    pil_im = Image.open(io.BytesIO(raw)).convert("L")
    return resize_grid(np.asarray(pil_im, dtype=np.float64), size)


# --- 4. SAOImage DS9 Scaling, Bias/Contrast & Colormaps ---

DS9_COLORS = {
    "Heat (DS9 Infrared)": [(0.0, 0, 0, 0), (0.35, 175, 0, 0), (0.7, 255, 170, 0), (1.0, 255, 255, 255)],
    "Inferno": [(0.0, 0, 0, 4), (0.25, 87, 16, 110), (0.5, 188, 55, 84), (0.75, 249, 142, 9), (1.0, 252, 255, 164)],
    "Cool (DS9 Cyan-Magenta)": [(0.0, 0, 0, 0), (0.5, 0, 210, 255), (1.0, 255, 80, 255)],
    "BB (DS9 Blackbody)": [(0.0, 0, 0, 0), (0.3, 140, 20, 40), (0.65, 245, 140, 20), (1.0, 255, 255, 210)],
    "Rainbow (DS9 Jet)": [(0.0, 0, 0, 130), (0.25, 0, 180, 255), (0.5, 40, 255, 80), (0.75, 255, 220, 0), (1.0, 255, 20, 20)],
    "Viridis": [(0.0, 68, 1, 84), (0.25, 59, 82, 139), (0.5, 33, 145, 140), (0.75, 94, 201, 98), (1.0, 253, 231, 37)],
    "Grey (Standard DS9)": [(0.0, 0, 0, 0), (1.0, 255, 255, 255)],
    "Invert Grey (Negative Sky)": [(0.0, 255, 255, 255), (1.0, 0, 0, 0)],
    "DiffMap": [(0.0, 50, 75, 200), (0.25, 140, 175, 254), (0.5, 220, 220, 220), (0.75, 245, 150, 120), (1.0, 190, 10, 40)],
}


def apply_ds9_scale(img, scale_mode="ZScale", bias=0.5, contrast=1.0):
    arr = np.asarray(img, dtype=np.float64)
    if scale_mode == "ZScale":
        med = np.median(arr)
        mad = np.median(np.abs(arr - med))
        sig = 1.4826 * mad if mad > 0 else np.std(arr)
        lo = max(float(np.min(arr)), float(med - 1.5 * sig))
        hi = min(float(np.max(arr)), float(med + 6.5 * sig))
    elif scale_mode == "Histogram Equalization":
        flat = arr.ravel()
        order = np.argsort(flat)
        ranks = np.empty_like(order, dtype=np.float64)
        ranks[order] = np.linspace(0.0, 1.0, len(flat))
        norm = ranks.reshape(arr.shape)
        return np.clip((norm - bias) * contrast + 0.5, 0.0, 1.0)
    else:
        lo = float(np.percentile(arr, 1.0))
        hi = float(np.percentile(arr, 99.6))

    if hi <= lo:
        hi = lo + 1e-6
    cut = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)

    if scale_mode == "Log":
        out = np.log10(1.0 + 100.0 * cut) / 2.0
    elif scale_mode == "Sqrt":
        out = np.sqrt(cut)
    elif scale_mode == "Squared":
        out = cut ** 2
    elif scale_mode == "Power":
        out = (np.power(100.0, cut) - 1.0) / 99.0
    elif scale_mode == "Asinh":
        out = np.arcsinh(cut * 12.0) / np.arcsinh(12.0)
    else:
        out = cut

    # Apply DS9 Bias & Contrast stretch
    stretched = (out - (1.0 - bias)) * contrast + 0.5
    return np.clip(stretched, 0.0, 1.0)


def colorize_array(norm_arr, palette_name="Heat (DS9 Infrared)"):
    stops = DS9_COLORS.get(palette_name, DS9_COLORS["Heat (DS9 Infrared)"])
    pos = np.array([s[0] for s in stops], dtype=np.float64)
    rc = np.array([s[1] for s in stops], dtype=np.float64)
    gc = np.array([s[2] for s in stops], dtype=np.float64)
    bc = np.array([s[3] for s in stops], dtype=np.float64)

    flat = np.clip(norm_arr.ravel(), 0.0, 1.0)
    r = np.interp(flat, pos, rc).astype(np.uint8)
    g = np.interp(flat, pos, gc).astype(np.uint8)
    b = np.interp(flat, pos, bc).astype(np.uint8)
    return np.stack([r, g, b], axis=-1).reshape(norm_arr.shape[0], norm_arr.shape[1], 3)


def find_auto_peaks(img1, img2, threshold=4.5):
    diff = img2 - img1
    med = float(np.median(diff))
    mad = float(np.median(np.abs(diff - med)))
    sig = 1.4826 * mad if mad > 1e-6 else float(np.std(diff))
    snr = (diff - med) / max(1e-6, sig)
    abs_s = np.abs(snr)

    # 7x7 sliding window max filter in pure numpy
    pad = 3
    padded = np.pad(abs_s, pad_width=pad, mode="edge")
    h, w = abs_s.shape
    loc_max = np.full_like(abs_s, -np.inf)
    for dy in range(7):
        for dx in range(7):
            loc_max = np.maximum(loc_max, padded[dy : dy + h, dx : dx + w])

    mask = (abs_s == loc_max) & (abs_s >= threshold)
    mask[:5, :] = False
    mask[-5:, :] = False
    mask[:, :5] = False
    mask[:, -5:] = False

    py, px = np.where(mask)
    items = []
    for x, y in zip(px, py):
        items.append({
            "Pixel X": int(x),
            "Pixel Y": int(y),
            "Image 1 Brightness": round(float(img1[y, x]), 1),
            "Image 2 Brightness": round(float(img2[y, x]), 1),
            "Change": round(float(img2[y, x] - img1[y, x]), 1),
            "Signal Strength (SNR)": round(float(snr[y, x]), 2),
        })
    df = pd.DataFrame(items)
    if not df.empty:
        df["abs_s"] = df["Signal Strength (SNR)"].abs()
        df = df.sort_values("abs_s", ascending=False).drop(columns=["abs_s"]).head(8).reset_index(drop=True)
    return df


# --- 5. Aperture Photometry & Game Verification Math ---

def measure_spot_photometry(img, cx, cy, r_ap=4.5, r_in=7.0, r_out=11.0):
    h, w = img.shape
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)

    inside = img[dist <= r_ap]
    ring = img[(dist >= r_in) & (dist <= r_out)]

    n_pix = int(inside.size)
    raw_total = float(np.sum(inside))
    sky_bg = float(np.median(ring)) if ring.size > 0 else float(np.median(img))
    sky_noise = float(np.std(ring)) if ring.size > 0 else float(np.std(img))

    clean_flux = max(0.01, raw_total - sky_bg * n_pix)
    err = math.sqrt((clean_flux / 2.5) + max(1, n_pix) * (sky_noise ** 2))
    snr = clean_flux / max(1e-5, err)
    mag_ab = -2.5 * math.log10(clean_flux) + 23.90

    return {
        "n_pixels": n_pix,
        "raw_sum": round(raw_total, 1),
        "sky_bg": round(sky_bg, 2),
        "net_flux": round(clean_flux, 1),
        "snr": round(snr, 1),
        "mag": round(mag_ab, 2),
        "peak_px": round(float(img[int(np.clip(round(cy), 0, h - 1)), int(np.clip(round(cx), 0, w - 1))]), 1),
    }


def check_player_mark(cx, cy, objects, max_dist=5.5):
    # Checks if the player's (cx, cy) mark hits any real object in Epoch 1 or Epoch 2
    best_obj = None
    best_dist = 999.0
    for obj in objects:
        d1 = math.hypot(cx - obj["x1"], cy - obj["y1"])
        d2 = math.hypot(cx - obj["x2"], cy - obj["y2"])
        d = min(d1, d2)
        if d < best_dist:
            best_dist = d
            best_obj = obj

    if best_obj is not None and best_dist <= max_dist:
        return best_obj, round(best_dist, 2)
    return None, round(best_dist, 2)


# --- 6. Sound (Sonification) Maker ---

def make_space_sound(slice1, slice2, base_hz=440.0, speed_kms=-18.5, seconds=3.0):
    c_light = 299792.458
    # Boost small speeds by 60x for human ears while keeping true speed in table
    beta_ear = np.clip((speed_kms * 60.0) / c_light, -0.65, 0.65)
    shift_ratio = math.sqrt((1.0 - beta_ear) / (1.0 + beta_ear))
    new_hz = round(base_hz * shift_ratio, 2)
    diff_hz = round(new_hz - base_hz, 2)

    rate = 44100
    total = int(seconds * rate)
    t = np.linspace(0.0, seconds, total, endpoint=False)

    s1 = np.asarray(slice1, dtype=np.float64).ravel()
    s2 = np.asarray(slice2, dtype=np.float64).ravel()
    n1 = (s1 - np.min(s1)) / max(1e-5, np.max(s1) - np.min(s1))
    n2 = (s2 - np.min(s2)) / max(1e-5, np.max(s2) - np.min(s2))

    x_time = np.linspace(0.0, seconds, len(n1))
    e1 = np.interp(t, x_time, n1)
    e2 = np.interp(t, x_time, n2)

    half = total // 2
    freq_line = np.empty(total)
    freq_line[:half] = base_hz * (1.0 + 0.25 * e1[:half])
    freq_line[half:] = new_hz * (1.0 + 0.35 * e2[half:])
    vol = np.concatenate([0.3 + 0.7 * e1[:half], 0.3 + 0.7 * e2[half:]])

    phase = 2.0 * np.pi * np.cumsum(freq_line) / rate
    wave_shifted = vol * (0.75 * np.sin(phase) + 0.25 * np.sin(2.0 * phase))
    wave_rest = (0.3 + 0.7 * e1) * np.sin(2.0 * np.pi * base_hz * t)

    fade = min(int(0.04 * rate), total // 10)
    win = np.ones(total)
    win[:fade] = np.linspace(0.0, 1.0, fade)
    win[-fade:] = np.linspace(1.0, 0.0, fade)
    wave_shifted *= win

    peak = max(1e-5, float(np.max(np.abs(wave_shifted))))
    pcm = np.int16((wave_shifted / peak) * 30000)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm.tobytes())

    return buf.getvalue(), t, wave_rest, wave_shifted, new_hz, diff_hz


# --- 7. DS9 Image & Plot Renderers (Pure Pillow + NumPy) ---

def draw_ds9_sky_frame(
    scaled_img,
    title,
    palette,
    show_grid,
    cx,
    cy,
    r_ap,
    r_in,
    r_out,
    region_shape="Circle + Annulus",
    show_hints=False,
    hints_df=None,
    found_marks=None,
    ref_ra=270.0,
    ref_dec=66.5,
):
    h, w = scaled_img.shape
    rgb = colorize_array(np.flipud(scaled_img), palette)
    sky_im = Image.fromarray(rgb, mode="RGB").resize((420, 420), resample=Image.Resampling.NEAREST)

    canvas = Image.new("RGB", (560, 495), (9, 13, 24))
    pad_l, pad_t = 62, 36
    canvas.paste(sky_im, (pad_l, pad_t))
    draw = ImageDraw.Draw(canvas)
    scale = 420.0 / float(w)

    def to_xy(px, py):
        return pad_l + (px + 0.5) * scale, pad_t + (float(h - 1 - py) + 0.5) * scale

    draw.text((pad_l, 11), title, fill=(245, 248, 255))

    for tick in np.linspace(0, w - 1, 5):
        tx, ty = to_xy(tick, tick)
        if show_grid:
            for y_s in range(pad_t, pad_t + 420, 10):
                draw.line([(tx, y_s), (tx, min(pad_t + 420, y_s + 5))], fill=(56, 189, 248), width=1)
            for x_s in range(pad_l, pad_l + 420, 10):
                draw.line([(x_s, ty), (min(pad_l + 420, x_s + 5), ty)], fill=(56, 189, 248), width=1)
            ra_v, _ = pixel_to_sky(tick, h / 2.0, w, ref_ra, ref_dec)
            _, dec_v = pixel_to_sky(w / 2.0, tick, w, ref_ra, ref_dec)
            xlbl, ylbl = f"{ra_v:.1f}d", f"{dec_v:.1f}d"
        else:
            xlbl, ylbl = f"{int(round(tick))}", f"{int(round(tick))}"
        draw.text((tx - 14, pad_t + 426), xlbl, fill=(200, 212, 226))
        draw.text((8, ty - 6), ylbl, fill=(200, 212, 226))

    draw.rectangle([pad_l, pad_t, pad_l + 420, pad_t + 420], outline=(80, 95, 120), width=1)

    # Draw DS9 Region around player cursor (cx, cy)
    scx, scy = to_xy(cx, cy)
    rap_s = r_ap * scale
    rin_s = r_in * scale
    rout_s = r_out * scale

    if region_shape == "Box Region":
        draw.rectangle([scx - rap_s, scy - rap_s, scx + rap_s, scy + rap_s], outline=(0, 255, 180), width=2)
    elif region_shape == "Crosshair Only":
        draw.line([(scx - 14, scy), (scx + 14, scy)], fill=(0, 255, 180), width=2)
        draw.line([(scx, scy - 14), (scx, scy + 14)], fill=(0, 255, 180), width=2)
    else:
        draw.ellipse([scx - rap_s, scy - rap_s, scx + rap_s, scy + rap_s], outline=(34, 211, 238), width=2)
        draw.ellipse([scx - rin_s, scy - rin_s, scx + rin_s, scy + rin_s], outline=(250, 204, 21), width=1)
        draw.ellipse([scx - rout_s, scy - rout_s, scx + rout_s, scy + rout_s], outline=(250, 204, 21), width=1)
        draw.line([(scx - 5, scy), (scx + 5, scy)], fill=(34, 211, 238), width=2)
        draw.line([(scx, scy - 5), (scx, scy + 5)], fill=(34, 211, 238), width=2)

    # Show player's previously marked spots in green/red
    if found_marks:
        for mk in found_marks:
            mx, my = to_xy(mk["x"], mk["y"])
            col = (52, 211, 153) if mk["hit"] else (248, 113, 113)
            draw.ellipse([mx - 9, my - 9, mx + 9, my + 9], outline=col, width=2)

    # Optional scanner hints
    if show_hints and hints_df is not None and not hints_df.empty:
        for _, r in hints_df.iterrows():
            hx, hy = to_xy(float(r["Pixel X"]), float(r["Pixel Y"]))
            draw.ellipse([hx - 12, hy - 12, hx + 12, hy + 12], outline=(244, 63, 94), width=2)

    # Colorbar
    cb_x = pad_l + 434
    grad = np.linspace(1.0, 0.0, 420).reshape(420, 1)
    cb_im = Image.fromarray(colorize_array(np.repeat(grad, 14, axis=1), palette), mode="RGB")
    canvas.paste(cb_im, (cb_x, pad_t))
    draw.rectangle([cb_x, pad_t, cb_x + 14, pad_t + 420], outline=(80, 95, 120), width=1)
    draw.text((cb_x + 18, pad_t), "Max", fill=(160, 175, 195))
    draw.text((cb_x + 18, pad_t + 204), "Mid", fill=(160, 175, 195))
    draw.text((cb_x + 18, pad_t + 408), "Min", fill=(160, 175, 195))

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def draw_simple_plot(x_arr, y1_arr, y2_arr, title, x_name, y_name, leg1, leg2, vline=None, width=600, height=240):
    canvas = Image.new("RGB", (width, height), (9, 13, 24))
    draw = ImageDraw.Draw(canvas)
    pl, pr, pt, pb = 58, 20, 32, 36
    pw, ph = width - pl - pr, height - pt - pb

    xmin, xmax = float(np.min(x_arr)), float(np.max(x_arr))
    if xmax <= xmin:
        xmax = xmin + 1.0
    both = np.concatenate([y1_arr.ravel(), y2_arr.ravel()])
    ymin, ymax = float(np.min(both)), float(np.max(both))
    pad_y = 0.08 * max(1e-4, ymax - ymin)
    ymin -= pad_y
    ymax += pad_y

    def pt_xy(xv, yv):
        return pl + ((xv - xmin) / (xmax - xmin)) * pw, pt + ph - ((yv - ymin) / (ymax - ymin)) * ph

    for i in range(5):
        f = i / 4.0
        gx = pl + f * pw
        gy = pt + (1.0 - f) * ph
        draw.line([(gx, pt), (gx, pt + ph)], fill=(28, 38, 56), width=1)
        draw.line([(pl, gy), (pl + pw, gy)], fill=(28, 38, 56), width=1)
        draw.text((gx - 10, pt + ph + 5), f"{xmin + f * (xmax - xmin):.1f}", fill=(150, 165, 185))
        yv = ymin + f * (ymax - ymin)
        draw.text((6, gy - 6), f"{yv:.0f}" if abs(ymax - ymin) > 10 else f"{yv:.2f}", fill=(150, 165, 185))

    draw.rectangle([pl, pt, pl + pw, pt + ph], outline=(75, 90, 115), width=1)

    if vline is not None and xmin <= vline <= xmax:
        vx, _ = pt_xy(vline, ymin)
        draw.line([(vx, pt), (vx, pt + ph)], fill=(250, 204, 21), width=2)

    p1 = [pt_xy(float(x), float(y)) for x, y in zip(x_arr, y1_arr)]
    p2 = [pt_xy(float(x), float(y)) for x, y in zip(x_arr, y2_arr)]
    if len(p1) > 1:
        draw.line(p1, fill=(56, 189, 248), width=2)
    if len(p2) > 1:
        draw.line(p2, fill=(244, 63, 94), width=2)

    draw.text((pl, 9), title, fill=(245, 248, 255))
    draw.text((pl + pw // 2 - 55, height - 15), x_name, fill=(200, 212, 226))
    draw.text((6, 9), y_name, fill=(150, 165, 185))

    draw.line([(pl + 10, pt + 12), (pl + 26, pt + 12)], fill=(56, 189, 248), width=2)
    draw.text((pl + 32, pt + 6), leg1, fill=(230, 238, 248))
    draw.line([(pl + 190, pt + 12), (pl + 206, pt + 12)], fill=(244, 63, 94), width=2)
    draw.text((pl + 212, pt + 6), leg2, fill=(230, 238, 248))

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


# --- 8. Space Theme CSS, NASA Logo Banner & Interactive Blink Widget ---

NASA_SVG_BADGE = """
<svg width="68" height="68" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
  <circle cx="60" cy="60" r="56" fill="#0b3d91" stroke="#38bdf8" stroke-width="2.5"/>
  <circle cx="32" cy="30" r="1.5" fill="#ffffff"/>
  <circle cx="88" cy="26" r="1.8" fill="#ffffff"/>
  <circle cx="95" cy="78" r="1.4" fill="#ffffff"/>
  <circle cx="25" cy="84" r="1.6" fill="#ffffff"/>
  <ellipse cx="60" cy="60" rx="48" ry="18" fill="none" stroke="#ffffff" stroke-width="2" transform="rotate(-22 60 60)"/>
  <path d="M 18 76 L 56 26 L 62 56 L 102 36 L 58 68 L 52 44 Z" fill="#fc3d21"/>
  <text x="60" y="68" text-anchor="middle" fill="#ffffff" font-family="Arial Black, Impact, sans-serif" font-size="26" font-weight="900" letter-spacing="2">NASA</text>
</svg>
"""


def add_space_theme_css():
    st.markdown(
        """
        <style>
        @keyframes floatSlow {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
        }
        @keyframes borderGlow {
            0%, 100% { border-color: #38bdf8; box-shadow: 0 0 15px rgba(56, 189, 248, 0.25); }
            50% { border-color: #f43f5e; box-shadow: 0 0 22px rgba(244, 63, 94, 0.35); }
        }
        .stApp {
            background: radial-gradient(ellipse at top, #0d1b3a 0%, #050814 55%, #02040a 100%);
            color: #f1f5f9;
        }
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2.5rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(11, 19, 40, 0.88);
            border: 1px solid #1e3a8a;
            padding: 12px 14px;
            border-radius: 12px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            border-color: #38bdf8;
        }
        .space-box {
            background: linear-gradient(145deg, rgba(13, 25, 54, 0.92), rgba(7, 12, 26, 0.95));
            border: 1px solid #1e3a8a;
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 14px;
        }
        .step-strip {
            background: linear-gradient(90deg, #0b152e, #172554, #0b152e);
            border-left: 4px solid #38bdf8;
            border-right: 4px solid #fc3d21;
            border-radius: 10px;
            padding: 10px 16px;
            margin: 14px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        .welcome-card {
            background: radial-gradient(circle at center, #11224d 0%, #060b19 75%);
            border: 2px solid #38bdf8;
            border-radius: 18px;
            padding: 28px;
            text-align: center;
            animation: borderGlow 4s infinite ease-in-out;
            margin-bottom: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_top_nasa_banner(player_name, score, sector_name):
    banner_html = f"""
    <div style="position:relative; overflow:hidden; border-radius:16px; border:1px solid #1e3a8a; background:#050917; padding:18px 24px; font-family:'Segoe UI', sans-serif; color:#ffffff; box-shadow:0 10px 30px rgba(0,0,0,0.5);">
        <canvas id="bgStars" style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:0; opacity:0.75;"></canvas>
        <div style="position:relative; z-index:1; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:14px;">
            <div style="display:flex; align-items:center; gap:16px;">
                {NASA_SVG_BADGE}
                <div>
                    <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-bottom:4px;">
                        <span style="background:#fc3d21; color:#fff; font-size:11px; font-weight:800; padding:3px 10px; border-radius:99px; letter-spacing:0.8px;">
                            NASA SPACE APPS CHALLENGE 2026
                        </span>
                        <span style="background:#0b3d91; border:1px solid #38bdf8; color:#bae6fd; font-size:11px; font-weight:800; padding:3px 10px; border-radius:99px;">
                            TEAM ExoMapper
                        </span>
                    </div>
                    <h1 style="margin:2px 0; font-size:26px; font-weight:800; color:#f8fafc;">
                        🪐 ExoMapper: Hunt for Planet X & Space Anomalies
                    </h1>
                    <div style="font-size:13.5px; color:#cbd5e1;">
                        Compare two infrared sky photos taken 6 months apart, use DS9 tools & space sound, and spot moving worlds!
                    </div>
                </div>
            </div>
            <div style="background:rgba(11, 25, 58, 0.9); border:1px solid #38bdf8; border-radius:12px; padding:10px 16px; text-align:right;">
                <div style="font-size:11.5px; color:#93c5fd; font-weight:700;">EXPLORER: {player_name.upper()}</div>
                <div style="font-size:22px; font-weight:900; color:#facc15;">🏆 {score} PTS</div>
                <div style="font-size:11px; color:#cbd5e1;">{sector_name}</div>
            </div>
        </div>
    </div>
    <script>
        const cv = document.getElementById("bgStars");
        if (cv) {{
            const ctx = cv.getContext("2d");
            cv.width = cv.offsetWidth || 900;
            cv.height = cv.offsetHeight || 130;
            const pts = Array.from({{length: 70}}, () => ({{
                x: Math.random() * cv.width,
                y: Math.random() * cv.height,
                r: Math.random() * 1.7 + 0.4,
                dx: (Math.random() - 0.5) * 0.35
            }}));
            function loop() {{
                ctx.clearRect(0, 0, cv.width, cv.height);
                for (const p of pts) {{
                    p.x = (p.x + p.dx + cv.width) % cv.width;
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                    ctx.fillStyle = "rgba(224, 242, 254, 0.8)";
                    ctx.fill();
                }}
                requestAnimationFrame(loop);
            }}
            loop();
        }}
    </script>
    """
    components.html(banner_html, height=145)


def show_blink_player(b64_1, b64_2, speed_ms=600, auto_start=True):
    html = f"""
    <div style="background:#080e20; border:1px solid #1e3a8a; border-radius:14px; padding:12px; text-align:center; font-family:'Segoe UI', sans-serif; color:#fff;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:6px;">
            <div>
                <span style="font-size:12px; color:#93c5fd; font-weight:700;">NOW SHOWING:</span>
                <span id="epTag" style="background:#0284c7; padding:4px 10px; border-radius:6px; font-size:12px; font-weight:800; margin-left:6px;">
                    IMAGE 1 (March 2026)
                </span>
            </div>
            <div style="display:flex; gap:5px; flex-wrap:wrap;">
                <button id="playBtn" onclick="flipPlay()" style="background:#2563eb; color:#fff; border:none; border-radius:6px; padding:5px 11px; cursor:pointer; font-weight:700; font-size:12px;">
                    {"⏸ Pause Blink" if auto_start else "▶ Start Blink"}
                </button>
                <button id="fadeBtn" onclick="flipFade()" style="background:#334155; color:#fff; border:none; border-radius:6px; padding:5px 10px; cursor:pointer; font-size:12px;">
                    🌊 Smooth Fade: OFF
                </button>
                <button onclick="lockImg(1)" style="background:#1e293b; color:#e2e8f0; border:1px solid #475569; border-radius:6px; padding:5px 9px; cursor:pointer; font-size:11.5px;">
                    Hold Image 1
                </button>
                <button onclick="lockImg(2)" style="background:#1e293b; color:#e2e8f0; border:1px solid #475569; border-radius:6px; padding:5px 9px; cursor:pointer; font-size:11.5px;">
                    Hold Image 2 (+6 Months)
                </button>
            </div>
        </div>
        <div style="position:relative; width:100%; height:430px; display:flex; justify-content:center; align-items:center; background:#030611; border-radius:10px; border:1px solid #1e293b; overflow:hidden;">
            <img id="im1" src="data:image/png;base64,{b64_1}" style="position:absolute; max-width:100%; max-height:425px; object-fit:contain;" />
            <img id="im2" src="data:image/png;base64,{b64_2}" style="position:absolute; max-width:100%; max-height:425px; object-fit:contain; opacity:0;" />
        </div>
        <div style="margin-top:8px; display:flex; align-items:center; justify-content:center; gap:10px; font-size:12px; color:#94a3b8;">
            <span>Image 1</span>
            <input id="mixBar" type="range" min="0" max="100" value="0" oninput="slideMix(this.value)" style="width:200px; accent-color:#38bdf8; cursor:pointer;" />
            <span>Image 2</span>
        </div>
    </div>
    <script>
        let ep = 1;
        let run = {str(auto_start).lower()};
        let fade = false;
        const im2 = document.getElementById("im2");
        const tag = document.getElementById("epTag");
        const bar = document.getElementById("mixBar");

        function redraw() {{
            im2.style.transition = fade ? "opacity 0.4s ease-in-out" : "none";
            if (ep === 1) {{
                im2.style.opacity = "0";
                bar.value = 0;
                tag.innerText = "IMAGE 1 (March 2026)";
                tag.style.background = "#0284c7";
            }} else {{
                im2.style.opacity = "1";
                bar.value = 100;
                tag.innerText = "IMAGE 2 (September 2026 - 6 Months Later)";
                tag.style.background = "#e11d48";
            }}
        }}
        setInterval(() => {{
            if (run) {{
                ep = (ep === 1) ? 2 : 1;
                redraw();
            }}
        }}, {speed_ms});

        function flipPlay() {{
            run = !run;
            const b = document.getElementById("playBtn");
            b.innerText = run ? "⏸ Pause Blink" : "▶ Start Blink";
            b.style.background = run ? "#2563eb" : "#16a34a";
        }}
        function flipFade() {{
            fade = !fade;
            const b = document.getElementById("fadeBtn");
            b.innerText = fade ? "🌊 Smooth Fade: ON" : "🌊 Smooth Fade: OFF";
            b.style.background = fade ? "#7c3aed" : "#334155";
        }}
        function lockImg(n) {{
            run = false;
            document.getElementById("playBtn").innerText = "▶ Start Blink";
            ep = n;
            redraw();
        }}
        function slideMix(v) {{
            run = false;
            document.getElementById("playBtn").innerText = "▶ Start Blink";
            im2.style.transition = "none";
            im2.style.opacity = (v / 100.0).toString();
            tag.innerText = "MIXING (" + v + "% Image 2)";
            tag.style.background = "#7c3aed";
        }}
    </script>
    """
    components.html(html, height=530)


# --- 9. Session Memory Setup ---

def setup_game_state():
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "game_started" not in st.session_state:
        st.session_state.game_started = False
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "pick_x" not in st.session_state:
        st.session_state.pick_x = 64.0
    if "pick_y" not in st.session_state:
        st.session_state.pick_y = 64.0
    if "found_ids" not in st.session_state:
        st.session_state.found_ids = set()
    if "canvas_marks" not in st.session_state:
        st.session_state.canvas_marks = []
    if "scoreboard" not in st.session_state:
        # Pre-fill with 2 sample entries so the scoreboard looks clear right away
        st.session_state.scoreboard = [
            {
                "Username": "Aarav_Space99",
                "Time": "2026-10-24 19:40:12",
                "Set Used": "Sector 1: Outer Kuiper Belt (Band #88 - 4.42 um)",
                "Pixels (X, Y)": "(71.2, 65.4) | 17h 59m 56.4s, +66d 30m 05.8s",
                "Found Anomaly or Not": "YES - PLANET X FOUND!",
                "Found What": "Planet X (Hidden 9th World!)",
                "Points": +175,
                "Total Score": 175,
                "Physical Properties": "Flux E1: 11.2 uJy -> E2: 3890.4 uJy | Mag: 14.92 | Temp: 380 K | Speed: -18.5 km/s",
                "Sonification": "Pitch: 456.6 Hz (Shift: +16.6 Hz, Blueshift)",
            },
            {
                "Username": "Meera_Astro",
                "Time": "2026-10-24 19:45:05",
                "Set Used": "Sector 2: Taurus Dark Cloud (Band #42 - 2.15 um)",
                "Pixels (X, Y)": "(44.0, 82.0) | 04h 32m 51.0s, +24d 19m 49.3s",
                "Found Anomaly or Not": "NO - False Alarm",
                "Found What": "Normal Static Star / Sky Noise",
                "Points": -20,
                "Total Score": 60,
                "Physical Properties": "Flux E1: 1420.0 uJy -> E2: 1418.5 uJy | Mag: 16.02 | Temp: 5800 K | Speed: 0.0 km/s",
                "Sonification": "Pitch: 440.0 Hz (Shift: +0.0 Hz, No Shift)",
            },
        ]


# --- 10. Main App Flow ---

def main():
    st.set_page_config(
        page_title="ExoMapper | NASA Space Apps Challenge 2026",
        page_icon="🪐",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    setup_game_state()
    add_space_theme_css()

    bands = get_spherex_bands()

    # =========================================================
    # STEP 1: IMAGINATIVE WELCOME SCREEN (IF NOT LOGGED IN YET)
    # =========================================================
    if not st.session_state.game_started:
        welcome_anim = f"""
        <div style="position:relative; overflow:hidden; border-radius:20px; border:2px solid #38bdf8; background:radial-gradient(circle at center, #0f2454 0%, #040814 80%); padding:34px 28px; text-align:center; font-family:'Segoe UI', sans-serif; color:#fff; box-shadow:0 15px 40px rgba(0,0,0,0.65);">
            <canvas id="welcomeStars" style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:0;"></canvas>
            <div style="position:relative; z-index:1;">
                <div style="display:flex; justify-content:center; margin-bottom:10px;">
                    {NASA_SVG_BADGE}
                </div>
                <div style="display:inline-block; background:#fc3d21; color:#fff; font-weight:800; font-size:12px; padding:4px 14px; border-radius:99px; letter-spacing:1px; margin-bottom:8px;">
                    NASA SPACE APPS CHALLENGE 2026 • OFFICIAL ENTRY BY TEAM EXOMAPPER
                </div>
                <h1 style="margin:6px 0 10px 0; font-size:34px; font-weight:900; color:#f8fafc;">
                    🪐 Welcome to ExoMapper: The Hunt for Planet X
                </h1>
                <p style="max-width:760px; margin:0 auto 14px auto; font-size:15.5px; color:#cbd5e1; line-height:1.6;">
                    Far out past Neptune, where sunlight is super faint, a hidden world called <b>Planet X</b> and strange space objects are moving through the dark.
                    Normal telescopes miss them. But NASA's <b>SPHEREx</b> mission scans the sky in <b>102 infrared colors</b>!
                    Your mission is to blink two sky photos taken 6 months apart, use real <b>DS9 astronomy tools</b>, listen to <b>space sounds</b>, and catch Planet X!
                </p>
            </div>
        </div>
        <script>
            const c = document.getElementById("welcomeStars");
            if (c) {{
                const ctx = c.getContext("2d");
                c.width = c.offsetWidth || 900;
                c.height = c.offsetHeight || 280;
                const stars = Array.from({{length: 110}}, () => ({{
                    x: Math.random() * c.width,
                    y: Math.random() * c.height,
                    r: Math.random() * 2.0 + 0.5,
                    s: Math.random() * 0.5 + 0.15
                }}));
                function draw() {{
                    ctx.clearRect(0, 0, c.width, c.height);
                    for (const st of stars) {{
                        st.x = (st.x + st.s) % c.width;
                        ctx.beginPath();
                        ctx.arc(st.x, st.y, st.r, 0, Math.PI * 2);
                        ctx.fillStyle = "rgba(186, 230, 253, 0.85)";
                        ctx.fill();
                    }}
                    requestAnimationFrame(draw);
                }}
                draw();
            }}
        </script>
        """
        components.html(welcome_anim, height=310)

        c_left, c_mid, c_right = st.columns([1.0, 1.6, 1.0])
        with c_mid:
            st.markdown("<div class='space-box'>", unsafe_allow_html=True)
            st.subheader("🚀 Enter Your Space Explorer Name to Begin")
            name_in = st.text_input("Type your Username / Callsign:", placeholder="e.g., StarHunter_Rohan")
            start_sector = st.selectbox("Choose Your Starting Sky Sector:", list(SECTOR_CONFIGS.keys()))
            if st.button("🪐 Launch Mission & Enter Observatory!", use_container_width=True):
                clean_name = name_in.strip() if name_in.strip() else "Explorer_01"
                st.session_state.username = clean_name
                st.session_state.active_sector = start_sector
                st.session_state.game_started = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # Show game rules preview right on the welcome screen too
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(
                """
                <div class="space-box">
                    <h4 style="color:#38bdf8; margin-top:0;">1. How the Blink Game Works</h4>
                    <p style="font-size:13.5px; color:#cbd5e1;">
                        We give you two infrared pictures of the same sky patch taken <b>6 months apart</b> (March and September).
                        Normal stars stay still. <b>Planet X</b> and <b>Brown Dwarfs</b> jump to a new pixel! <b>Variable stars</b> flare up brighter!
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r2:
            st.markdown(
                """
                <div class="space-box">
                    <h4 style="color:#facc15; margin-top:0;">2. DS9 Tools & Space Sound</h4>
                    <p style="font-size:13.5px; color:#cbd5e1;">
                        Use real <b>SAOImage DS9</b> controls (ZScale, Log, Heat/Cool colorbars, Bias & Contrast sliders, and zoom)
                        plus <b>Doppler Sound</b> to hear if the object is moving toward us or away from us.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with r3:
            st.markdown(
                """
                <div class="space-box">
                    <h4 style="color:#34d399; margin-top:0;">3. Positive & Negative Points</h4>
                    <p style="font-size:13.5px; color:#cbd5e1;">
                        • Find <b>Planet X</b>: <b>+150 pts</b> (+25 bonus for right type!)<br/>
                        • Find a <b>Brown Dwarf / Supernova / Flare</b>: <b>+70 to +85 pts</b><br/>
                        • Mark a normal star or empty noise: <b>-20 pts (False Alarm!)</b>
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        return

    # =========================================================
    # STEP 2: SIDEBAR - DS9 CONTROLS, DATASET & USER SWITCHER
    # =========================================================
    with st.sidebar:
        st.markdown("### 👨‍🚀 Explorer Profile")
        st.write(f"**Player:** `{st.session_state.username}`")
        st.write(f"**Score:** `{st.session_state.score} points`")
        if st.button("🔄 Change Username / Welcome Screen", use_container_width=True):
            st.session_state.game_started = False
            st.rerun()

        st.markdown("### 1. Choose Sky Set (Dataset)")
        feed_mode = st.selectbox(
            "Data Source",
            [
                "Game Sector (SPHEREx 102-Band Sky)",
                "Hybrid Set (Upload Photo + Hidden Planet X)",
                "Upload Custom 2-Epoch FITS / Images",
                "Caltech/IPAC IRSA Live Archive",
            ],
        )

        sector_choice = st.selectbox(
            "Select Sky Sector to Hunt In",
            list(SECTOR_CONFIGS.keys()),
            index=0,
        )

        st.markdown("### 2. SPHEREx 102-Band Tuner")
        band_num = st.slider("Infrared Band (1 to 102)", 1, 102, 85, help="Planet X is cold (380 K), so higher band numbers (longer wavelengths) make it shine brighter!")
        cur_band = bands[band_num - 1]
        st.info(
            f"**Band #{cur_band['band']} ({cur_band['wavelength']} μm)**\n\n"
            f"- **Sees:** {cur_band['info']}\n"
            f"- **Tip:** Cold worlds like Planet X glow strongest above 3.5 μm!"
        )

        st.markdown("### 3. SAOImage DS9 Display Controls")
        ds9_scale = st.selectbox(
            "DS9 Scale Mode",
            ["ZScale", "Asinh", "Log", "Sqrt", "Linear", "Squared", "Power", "Histogram Equalization"],
            index=0,
        )
        ds9_cmap = st.selectbox(
            "DS9 Colorbar (LUT)",
            list(DS9_COLORS.keys())[:-1],
            index=0,
        )
        ds9_bias = st.slider("DS9 Bias (Brightness Shift)", 0.1, 0.9, 0.5, 0.05)
        ds9_contrast = st.slider("DS9 Contrast (Stretch)", 0.3, 3.5, 1.0, 0.1)
        ds9_region = st.selectbox("DS9 Region Marker Shape", ["Circle + Annulus", "Box Region", "Crosshair Only"])
        show_grid = st.checkbox("Show WCS Sky Grid (RA/Dec)", value=True)
        show_scanner_hints = st.checkbox("Turn On Computer Hint Circles (-25 pt penalty on finds)", value=False)

    # Generate the sky sector images and hidden objects
    grid_size = 128
    img1, img2, sector_objects, sec_cfg = build_sky_sector(
        sector_choice, grid_size, cur_band["wavelength"], noise_level=4.0
    )

    if feed_mode == "Upload Custom 2-Epoch FITS / Images":
        with st.sidebar:
            u1 = st.file_uploader("Upload Image 1 (.fits, .png, .jpg, .npy)", type=["fits", "fit", "png", "jpg", "jpeg", "npy"])
            u2 = st.file_uploader("Upload Image 2 (.fits, .png, .jpg, .npy)", type=["fits", "fit", "png", "jpg", "jpeg", "npy"])
            if u1 and u2:
                img1 = read_user_file(u1, grid_size)
                img2 = read_user_file(u2, grid_size)
                st.success("Loaded your custom images!")
    elif feed_mode == "Hybrid Set (Upload Photo + Hidden Planet X)":
        with st.sidebar:
            ub = st.file_uploader("Upload Background Sky Photo", type=["fits", "fit", "png", "jpg", "jpeg"])
            if ub:
                base_im = read_user_file(ub, grid_size)
                img1 = base_im + (img1 - np.median(img1)) * 0.6
                img2 = base_im + (img2 - np.median(img1)) * 0.6
                st.success("Mixed your photo with hidden Planet X & anomalies!")

    # Apply DS9 scaling
    sc1 = apply_ds9_scale(img1, ds9_scale, ds9_bias, ds9_contrast)
    sc2 = apply_ds9_scale(img2, ds9_scale, ds9_bias, ds9_contrast)
    auto_hints_df = find_auto_peaks(img1, img2, threshold=4.5)

    # =========================================================
    # STEP 3: TOP NASA BANNER, PERSONAL WELCOME & RULES GUIDE
    # =========================================================
    show_top_nasa_banner(st.session_state.username, st.session_state.score, sector_choice)

    st.markdown(
        f"""
        <div class="step-strip">
            <div>
                <span style="background:#22c55e; color:#042f2e; font-weight:800; font-size:11.5px; padding:3px 10px; border-radius:99px;">
                    WELCOME ABOARD, {st.session_state.username.upper()}!
                </span>
                <span style="margin-left:10px; font-weight:700; font-size:14.5px; color:#f8fafc;">
                    Mission Goal: Find Planet X and the 3 other anomalies hidden in {sector_choice}!
                </span>
            </div>
            <div style="font-size:12.5px; color:#93c5fd;">
                Spots Found So Far: <b>{len(st.session_state.found_ids)}</b> / 4 in this sector
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("📘 Game Rules, How to Mark Anomalies & Points System (Click to Read)", expanded=False):
        st.markdown(
            f"""
            **Hey {st.session_state.username}! Here is how you play and win in ExoMapper:**
            1. **Watch the Blink Comparator below:** It flips between **Image 1 (March 2026)** and **Image 2 (September 2026)**. Look closely for any bright dot that **jumps to a nearby spot** or **gets much brighter**.
            2. **Check the Subtraction Map (Right Side):** We subtract Image 1 from Image 2.
               - If an object **moved** (like **Planet X** or a **Brown Dwarf**), it leaves a **Blue dot** where it used to be and a **Red dot** where it moved to!
               - If an object **flared up or appeared**, it leaves a **bright Red spot**!
            3. **Aim Your Crosshair `(X, Y)`:** Use the **Pixel X** and **Pixel Y** boxes (or pick a candidate from the quick-jump list) to put your cyan circle right over the suspicious object.
            4. **Check DS9 Tools & Listen to the Sound:** Check its brightness in the DS9 Inspector and listen to its Doppler sound wave.
            5. **Mark It & Score Points (100% Real Check — No Fake Results):**
               - **Planet X Found (within 5.5 pixels):** **+150 Points** (+25 bonus if you guess *"Planet X (Moving World)"*!)
               - **Brown Dwarf / Flare Star / Supernova Found:** **+70 to +85 Points** (+25 bonus for right guess!)
               - **False Alarm (Marking a normal star or empty sky noise):** **-20 Points!**
            """
        )

    # =========================================================
    # STEP 4: CROSSHAIR AIMING & ANOMALY MARKING CONSOLE
    # =========================================================
    st.markdown(
        """
        <div class="step-strip">
            <span style="font-weight:800; color:#38bdf8;">🎯 STEP 1: AIM YOUR TELESCOPE CROSSHAIR & MARK ANOMALIES</span>
            <span style="font-size:12px; color:#cbd5e1;">Move Pixel X and Pixel Y onto any moving or brightening dot, choose what it is, and click Mark!</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_jump, c_px, c_py, c_ap = st.columns([2.1, 1.0, 1.0, 1.2])
    with c_jump:
        # Let player either dial coordinates manually OR jump to one of the computer-detected peaks
        jump_choices = ["Manual Aim (Use Pixel X & Y boxes)"]
        for idx_row, r in auto_hints_df.iterrows():
            jump_choices.append(f"Suspicious Spot #{idx_row+1} at Pixel ({int(r['Pixel X'])}, {int(r['Pixel Y'])}) [SNR {r['Signal Strength (SNR)']}]")
        picked_jump = st.selectbox("🔍 Quick-Jump to a Suspicious Spot (or Aim by Hand):", jump_choices)
        if picked_jump != "Manual Aim (Use Pixel X & Y boxes)":
            coords_part = picked_jump.split("Pixel (")[1].split(")")[0].split(",")
            st.session_state.pick_x = float(coords_part[0].strip())
            st.session_state.pick_y = float(coords_part[1].strip())

    with c_px:
        px_val = st.number_input("Crosshair Pixel X", 4.0, float(grid_size - 5), float(st.session_state.pick_x), 0.5)
        st.session_state.pick_x = px_val
    with c_py:
        py_val = st.number_input("Crosshair Pixel Y", 4.0, float(grid_size - 5), float(st.session_state.pick_y), 0.5)
        st.session_state.pick_y = py_val
    with c_ap:
        r_ap = st.slider("Aperture Circle Size (px)", 2.0, 10.0, 4.5, 0.5)
        r_in, r_out = r_ap + 2.5, r_ap + 6.0

    # Measure real photometry and sound at (px_val, py_val) right now
    phot1 = measure_spot_photometry(img1, px_val, py_val, r_ap, r_in, r_out)
    phot2 = measure_spot_photometry(img2, px_val, py_val, r_ap, r_in, r_out)
    ra_deg, dec_deg = pixel_to_sky(px_val, py_val, grid_size, sec_cfg["ra"], sec_cfg["dec"])
    ra_txt, dec_txt = format_ra_dec(ra_deg, dec_deg)

    # Check if there is a true object at (px_val, py_val) to get its real radial speed for Doppler sound
    matched_obj, dist_px = check_player_mark(px_val, py_val, sector_objects, max_dist=5.5)
    true_speed = matched_obj["speed_kms"] if matched_obj else 0.0
    true_temp = matched_obj["temp_k"] if matched_obj else 5500

    row_slice = int(np.clip(round(py_val), 0, grid_size - 1))
    wav_data, t_arr, w_rest, w_shift, pitch_hz, shift_hz = make_space_sound(
        img1[row_slice, :], img2[row_slice, :], base_hz=440.0, speed_kms=true_speed, seconds=3.0
    )

    # Anomaly Classification & Submit Bar
    g_col1, g_col2, g_col3 = st.columns([1.8, 1.3, 1.5])
    with g_col1:
        player_guess = st.selectbox(
            "🪐 What do you think is at this `(X, Y)` spot?",
            [
                "Planet X (Moving World)",
                "Moving Brown Dwarf",
                "Brightness Flare Star",
                "New Transient Outburst",
                "Normal Star / Sky Noise",
            ],
        )
    with g_col2:
        st.write("")
        mark_clicked = st.button("🎯 Mark This Spot & Check Result!", use_container_width=True)
    with g_col3:
        st.caption("🎧 Instant Sound of Your Selected `(X, Y)` Spot:")
        st.audio(wav_data, format="audio/wav")

    if mark_clicked:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        set_label = f"{sector_choice} (Band #{cur_band['band']} - {cur_band['wavelength']} um)"
        px_label = f"({px_val:.1f}, {py_val:.1f}) | {ra_txt}, {dec_txt}"
        sound_dir = "Blueshift" if shift_hz > 0 else ("Redshift" if shift_hz < 0 else "No Shift")
        sound_summary = f"Pitch: {pitch_hz:.1f} Hz (Shift: {shift_hz:+.1f} Hz, {sound_dir})"
        prop_summary = (
            f"Flux E1: {phot1['net_flux']} uJy -> E2: {phot2['net_flux']} uJy | "
            f"Mag E2: {phot2['mag']} | Temp: {true_temp} K | Speed: {true_speed:+.1f} km/s | SNR: {phot2['snr']}"
        )

        if matched_obj is not None and matched_obj["is_anomaly"]:
            obj_key = f"{sector_choice}_{matched_obj['id']}"
            if obj_key in st.session_state.found_ids:
                st.warning(f"You already found **{matched_obj['name']}** in this sector! Try hunting for the other anomalies.")
            else:
                st.session_state.found_ids.add(obj_key)
                pts = matched_obj["points"]
                bonus_msg = ""
                if player_guess == matched_obj["kind"]:
                    pts += 25
                    bonus_msg = " (+25 Bonus for guessing the exact right type!)"
                if show_scanner_hints:
                    pts -= 25
                    bonus_msg += " (-25 for using computer hint circles)"

                st.session_state.score += pts
                st.session_state.canvas_marks.append({"x": px_val, "y": py_val, "hit": True})

                status_str = "YES - PLANET X FOUND!" if matched_obj["is_planet_x"] else "YES - True Anomaly Found"
                st.session_state.scoreboard.insert(0, {
                    "Username": st.session_state.username,
                    "Time": now_str,
                    "Set Used": set_label,
                    "Pixels (X, Y)": px_label,
                    "Found Anomaly or Not": status_str,
                    "Found What": f"{matched_obj['name']} ({matched_obj['kind']})",
                    "Points": pts,
                    "Total Score": st.session_state.score,
                    "Physical Properties": prop_summary,
                    "Sonification": sound_summary,
                })

                if matched_obj["is_planet_x"]:
                    st.balloons()
                    st.success(
                        f"🎉 **INCREDIBLE FIND, {st.session_state.username.upper()}! YOU FOUND PLANET X!** "
                        f"It moved from `({matched_obj['x1']}, {matched_obj['y1']})` to `({matched_obj['x2']}, {matched_obj['y2']})`! "
                        f"You earned **+{pts} points**{bonus_msg}!"
                    )
                else:
                    st.success(
                        f"✅ **Great eye, {st.session_state.username}!** You found a real anomaly: **{matched_obj['name']}** "
                        f"(distance `{dist_px} px` from center)! Earned **+{pts} points**{bonus_msg}!"
                    )
        else:
            # False alarm -> Negative points!
            penalty = -20
            st.session_state.score += penalty
            st.session_state.canvas_marks.append({"x": px_val, "y": py_val, "hit": False})
            what_was_it = matched_obj["name"] if matched_obj is not None else "Empty Sky Background Noise"

            st.session_state.scoreboard.insert(0, {
                "Username": st.session_state.username,
                "Time": now_str,
                "Set Used": set_label,
                "Pixels (X, Y)": px_label,
                "Found Anomaly or Not": "NO - False Alarm",
                "Found What": what_was_it,
                "Points": penalty,
                "Total Score": st.session_state.score,
                "Physical Properties": prop_summary,
                "Sonification": sound_summary,
            })
            st.error(
                f"❌ **False Alarm (-20 Points)!** At pixel `({px_val:.1f}, {py_val:.1f})`, that is just **{what_was_it}**. "
                f"It did not move or change brightness between March and September. Look at the red/blue spots on the Subtraction Map to find moving objects!"
            )

    # Quick Live Readout Bar
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Your Total Score", f"{st.session_state.score} pts", f"{len(st.session_state.found_ids)}/4 Found in Sector")
    k2.metric("Crosshair Sky Pos", ra_txt, dec_txt)
    k3.metric("Image 1 Flux (March)", f"{phot1['net_flux']} μJy", f"Mag: {phot1['mag']}")
    k4.metric("Image 2 Flux (Sept)", f"{phot2['net_flux']} μJy", f"Change: {phot2['net_flux'] - phot1['net_flux']:+.1f} μJy")
    k5.metric("Spot Sound Pitch", f"{pitch_hz:.1f} Hz", f"Doppler Shift: {shift_hz:+.1f} Hz")

    # =========================================================
    # STEP 5: GAME & DS9 WORKSPACE TABS
    # =========================================================
    t_hunt, t_ds9, t_sound, t_board = st.tabs([
        "🔭 1. Blink Comparator & Planet X Hunt",
        "🛠️ 2. SAOImage DS9 Inspector & Properties",
        "🔊 3. Doppler Sound Lab (Selected Spot)",
        "🏆 4. Full Game Scoreboard & Discovery Log",
    ])

    # --- TAB 1: BLINK COMPARATOR & DIFFERENCE MAP ---
    with t_hunt:
        col_b1, col_b2 = st.columns([1.15, 1.0])
        with col_b1:
            sc_a, sc_b = st.columns(2)
            with sc_a:
                blink_ms = st.slider("Blink Speed (ms)", 200, 1400, 550, 50)
            with sc_b:
                auto_on = st.checkbox("Auto-Blink On", value=True)

            b64_1 = draw_ds9_sky_frame(
                sc1,
                f"Image 1 (March 2026) | {cur_band['wavelength']} um ({ds9_scale})",
                ds9_cmap,
                show_grid,
                px_val,
                py_val,
                r_ap,
                r_in,
                r_out,
                ds9_region,
                show_scanner_hints,
                auto_hints_df,
                st.session_state.canvas_marks,
                sec_cfg["ra"],
                sec_cfg["dec"],
            )
            b64_2 = draw_ds9_sky_frame(
                sc2,
                f"Image 2 (Sept 2026) | {cur_band['wavelength']} um ({ds9_scale})",
                ds9_cmap,
                show_grid,
                px_val,
                py_val,
                r_ap,
                r_in,
                r_out,
                ds9_region,
                show_scanner_hints,
                auto_hints_df,
                st.session_state.canvas_marks,
                sec_cfg["ra"],
                sec_cfg["dec"],
            )
            show_blink_player(b64_1, b64_2, speed_ms=blink_ms, auto_start=auto_on)

        with col_b2:
            st.markdown("#### Subtraction Map (Image 2 minus Image 1)")
            st.caption("Red = New/Brighter in Sept 2026 • Blue = Was there in March 2026 and moved away!")
            diff = img2 - img1
            max_d = max(1.0, float(np.percentile(np.abs(diff), 99.6)))
            norm_d = np.clip((diff + max_d) / (2.0 * max_d), 0.0, 1.0)
            b64_diff = draw_ds9_sky_frame(
                norm_d,
                "Change Map (Red = +Image 2, Blue = +Image 1)",
                "DiffMap",
                show_grid,
                px_val,
                py_val,
                r_ap,
                r_in,
                r_out,
                ds9_region,
                show_scanner_hints,
                auto_hints_df,
                st.session_state.canvas_marks,
                sec_cfg["ra"],
                sec_cfg["dec"],
            )
            st.image(f"data:image/png;base64,{b64_diff}", use_container_width=True)

            st.markdown("#### Computer Scanner Table (Top Changing Pixels)")
            st.dataframe(auto_hints_df, use_container_width=True, hide_index=True)

    # --- TAB 2: SAOIMAGE DS9 INSPECTOR & PHYSICAL PROPERTIES ---
    with t_ds9:
        st.subheader("🛠️ SAOImage DS9 Pixel Magnifier, Cuts & Physical Properties")
        st.caption(
            f"Inspecting your selected spot `({px_val:.1f}, {py_val:.1f})` with DS9 Scale `{ds9_scale}`, "
            f"Bias `{ds9_bias}`, Contrast `{ds9_contrast}`, and Colorbar `{ds9_cmap}`."
        )

        d_col1, d_col2 = st.columns([1.05, 1.15])
        with d_col1:
            st.markdown("#### Physical Properties of Selected Spot")
            props_table = pd.DataFrame([
                {"Property": "Pixel Coordinates (X, Y)", "Image 1 (March 2026)": f"({px_val:.1f}, {py_val:.1f})", "Image 2 (Sept 2026)": f"({px_val:.1f}, {py_val:.1f})"},
                {"Property": "Sky Coordinates (RA, Dec)", "Image 1 (March 2026)": f"{ra_txt}", "Image 2 (Sept 2026)": f"{dec_txt}"},
                {"Property": "Peak Pixel Value (μJy)", "Image 1 (March 2026)": f"{phot1['peak_px']}", "Image 2 (Sept 2026)": f"{phot2['peak_px']}"},
                {"Property": "Net Brightness inside Circle (μJy)", "Image 1 (March 2026)": f"{phot1['net_flux']}", "Image 2 (Sept 2026)": f"{phot2['net_flux']}"},
                {"Property": "Sky Background per Pixel (μJy)", "Image 1 (March 2026)": f"{phot1['sky_bg']}", "Image 2 (Sept 2026)": f"{phot2['sky_bg']}"},
                {"Property": "Brightness Magnitude (m_AB)", "Image 1 (March 2026)": f"{phot1['mag']} mag", "Image 2 (Sept 2026)": f"{phot2['mag']} mag"},
                {"Property": "Signal-to-Noise Ratio (SNR)", "Image 1 (March 2026)": f"{phot1['snr']}", "Image 2 (Sept 2026)": f"{phot2['snr']}"},
                {"Property": "Estimated Surface Temp & Speed", "Image 1 (March 2026)": f"{true_temp} K", "Image 2 (Sept 2026)": f"{true_speed:+.1f} km/s"},
            ])
            st.dataframe(props_table, use_container_width=True, hide_index=True)

            # DS9 Zoomed Magnifier Box (15x15 pixels)
            ix, iy = int(round(px_val)), int(round(py_val))
            y0, y1 = max(0, iy - 7), min(grid_size, iy + 8)
            x0, x1 = max(0, ix - 7), min(grid_size, ix + 8)
            z1 = sc1[y0:y1, x0:x1]
            z2 = sc2[y0:y1, x0:x1]

            im_z1 = Image.fromarray(colorize_array(np.flipud(z1), ds9_cmap)).resize((200, 200), Image.Resampling.NEAREST)
            im_z2 = Image.fromarray(colorize_array(np.flipud(z2), ds9_cmap)).resize((200, 200), Image.Resampling.NEAREST)
            zoom_box = Image.new("RGB", (450, 240), (9, 13, 24))
            zoom_box.paste(im_z1, (15, 30))
            zoom_box.paste(im_z2, (235, 30))
            dz = ImageDraw.Draw(zoom_box)
            dz.text((15, 8), "DS9 Zoom: Image 1 (15x15 px)", fill=(240, 248, 255))
            dz.text((235, 8), "DS9 Zoom: Image 2 (15x15 px)", fill=(240, 248, 255))
            for ox in (15, 235):
                dz.rectangle([ox, 30, ox + 200, 230], outline=(56, 189, 248), width=1)
                dz.line([(ox + 92, 130), (ox + 108, 130)], fill=(34, 211, 238), width=2)
                dz.line([(ox + 100, 122), (ox + 100, 138)], fill=(34, 211, 238), width=2)
            buf_z = io.BytesIO()
            zoom_box.save(buf_z, format="PNG")
            st.image(buf_z.getvalue(), use_container_width=True)

        with d_col2:
            # DS9 Horizontal & Vertical Pixel Cut Profiles
            st.markdown("#### DS9 Horizontal Pixel Cut (Across Row Y)")
            cut_h_png = draw_simple_plot(
                np.arange(grid_size, dtype=np.float64),
                img1[row_slice, :],
                img2[row_slice, :],
                f"DS9 Horizontal Brightness Cut along Y = {row_slice}",
                "Pixel X",
                "uJy",
                "Image 1 (March)",
                "Image 2 (Sept)",
                vline=px_val,
            )
            st.image(cut_h_png, use_container_width=True)

            st.markdown("#### 102-Band SPHEREx Infrared Spectrum of Selected Spot")
            waves_all = np.array([b["wavelength"] for b in bands])
            heat_curve = np.array([get_heat_factor(w, true_temp) for w in waves_all])
            ref_h = max(1e-5, get_heat_factor(cur_band["wavelength"], true_temp))
            spec1 = phot1["net_flux"] * (heat_curve / ref_h)
            spec2 = phot2["net_flux"] * (heat_curve / ref_h)
            spec_png = draw_simple_plot(
                waves_all,
                spec1,
                spec2,
                f"Brightness across all 102 SPHEREx Bands (Estimated Temp: {true_temp} K)",
                "Wavelength (microns)",
                "uJy",
                "Image 1 Spectrum",
                "Image 2 Spectrum",
                vline=cur_band["wavelength"],
            )
            st.image(spec_png, use_container_width=True)

        with st.expander("🔢 View Raw DS9 Pixel Number Table (15x15 Grid Around Crosshair)", expanded=False):
            t1, t2 = st.columns(2)
            with t1:
                st.write("**Image 1 Pixel Numbers (μJy):**")
                st.dataframe(pd.DataFrame(np.round(img1[y0:y1, x0:x1], 1)), use_container_width=True)
            with t2:
                st.write("**Image 2 Pixel Numbers (μJy):**")
                st.dataframe(pd.DataFrame(np.round(img2[y0:y1, x0:x1], 1)), use_container_width=True)

    # --- TAB 3: DOPPLER SOUND LAB ---
    with t_sound:
        st.subheader("🔊 Space Sound (Sonification) for Your Selected Spot")
        st.write(
            "When a space object moves toward Earth, its waves get squeezed together (**Blueshift** = higher pitch). "
            "When it moves away from Earth, its waves stretch out (**Redshift** = lower pitch)."
        )
        s_col1, s_col2 = st.columns([1.0, 1.35])
        with s_col1:
            base_note = st.slider("Base Note Frequency (Hz)", 220.0, 880.0, 440.0, 10.0)
            custom_speed = st.slider("Test Radial Speed (km/s)", -1500.0, 1500.0, float(true_speed), 5.0)
            wav_custom, t_c, wr_c, ws_c, pitch_c, shift_c = make_space_sound(
                img1[row_slice, :], img2[row_slice, :], base_hz=base_note, speed_kms=custom_speed, seconds=3.5
            )
            st.audio(wav_custom, format="audio/wav")
            st.download_button(
                "⬇️ Download This Space Sound (.wav)",
                data=wav_custom,
                file_name=f"exomapper_sound_X{int(px_val)}_Y{int(py_val)}.wav",
                mime="audio/wav",
            )
            st.info(
                f"**Sound Details for Pixel ({px_val:.1f}, {py_val:.1f}):**\n"
                f"- **Base Pitch:** `{base_note:.1f} Hz`\n"
                f"- **Shifted Pitch:** `{pitch_c:.1f} Hz` (`{shift_c:+.1f} Hz`)\n"
                f"- **Object Speed:** `{custom_speed:+.1f} km/s`"
            )
        with s_col2:
            n_show = int(0.025 * 44100)
            wave_png = draw_simple_plot(
                t_c[:n_show] * 1000.0,
                ws_c[:n_show],
                wr_c[:n_show],
                "Doppler Sound Wave (First 25 Milliseconds)",
                "Time (ms)",
                "Wave",
                f"Shifted ({pitch_c:.1f} Hz)",
                f"Rest ({base_note:.0f} Hz)",
                height=260,
            )
            st.image(wave_png, use_container_width=True)

    # --- TAB 4: FULL SCOREBOARD & DISCOVERY LOG ---
    with t_board:
        st.subheader("🏆 ExoMapper Player Scoreboard & Complete Discovery Log")
        st.write(
            "Every spot you mark is recorded here with your **Username, Time, Set Used, Pixels, "
            "Found Anomaly or Not, Found What, Points, Physical Properties, and Sonification**."
        )

        board_df = pd.DataFrame(st.session_state.scoreboard)

        # Player Rankings Summary Table
        if not board_df.empty:
            st.markdown("#### 🥇 Top Planet X Hunters Leaderboard")
            summary_rows = []
            for uname, grp in board_df.groupby("Username", sort=False):
                tot_pts = int(grp["Points"].sum())
                px_hits = int((grp["Found Anomaly or Not"] == "YES - PLANET X FOUND!").sum())
                anom_hits = int(grp["Found Anomaly or Not"].str.startswith("YES").sum())
                false_alarms = int((grp["Found Anomaly or Not"] == "NO - False Alarm").sum())
                summary_rows.append({
                    "Player Username": uname,
                    "Total Points": tot_pts,
                    "Planet X Found": px_hits,
                    "True Anomalies Found": anom_hits,
                    "False Alarms (-20 pts)": false_alarms,
                    "Total Attempts": len(grp),
                })
            rank_df = pd.DataFrame(summary_rows).sort_values("Total Points", ascending=False).reset_index(drop=True)
            st.dataframe(rank_df, use_container_width=True, hide_index=True)

        st.markdown("#### 📋 Detailed Scan-by-Scan Scoreboard Table")
        st.dataframe(board_df, use_container_width=True, hide_index=True)

        dl1, dl2, _ = st.columns([1.1, 1.1, 1.8])
        with dl1:
            st.download_button(
                "⬇️ Download Full Scoreboard (.csv)",
                data=board_df.to_csv(index=False).encode("utf-8"),
                file_name="exomapper_scoreboard.csv",
                mime="text/csv",
            )
        with dl2:
            st.download_button(
                "⬇️ Download Full Scoreboard (.json)",
                data=json.dumps(st.session_state.scoreboard, indent=2).encode("utf-8"),
                file_name="exomapper_scoreboard.json",
                mime="application/json",
            )

    # =========================================================
    # STEP 6: ENDING FOOTER (TEAM EXOMAPPER & NASA 2026)
    # =========================================================
    st.markdown(
        f"""
        <div class="welcome-card" style="margin-top:26px; padding:22px;">
            <div style="font-size:12px; font-weight:800; color:#38bdf8; letter-spacing:1px;">
                NASA SPACE APPS CHALLENGE 2026 • TEAM EXOMAPPER
            </div>
            <h3 style="margin:6px 0; color:#fff;">
                Thanks for exploring the infrared sky with us, {st.session_state.username}!
            </h3>
            <p style="font-size:13.5px; color:#cbd5e1; max-width:760px; margin:0 auto;">
                By combining multi-epoch image blinking, SAOImage DS9 scaling tools, aperture brightness math, and space sound waves,
                ExoMapper makes hunting for Planet X and cosmic changes fun and simple for everyone.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

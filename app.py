# ==============================================================================
# EXOMAPPER: INFRARED SKY EXPLORATION, MULTI-EPOCH BLINK COMPARATOR,
# APERTURE PHOTOMETRY & DOPPLER AUDIO SONIFICATION SUITE
# ==============================================================================
# Official Entry: NASA Space Apps Challenge 2026 (Inspired by NASA's SPHEREx Mission)
# Team: Shikshita Naryal & Ayan Agarwal
# ==============================================================================

from __future__ import annotations

import base64
import datetime
import io
import json
import math
import urllib.parse
import urllib.request
import wave
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage

import streamlit as st
import streamlit.components.v1 as components

# Optional Matplotlib support with graceful fallback
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Optional Astropy FITS/WCS support
try:
    from astropy.io import fits
    from astropy.wcs import WCS as AstropyWCS
    ASTROPY_AVAILABLE = True
except ImportError:
    ASTROPY_AVAILABLE = False


# =====================================================================
# 1. SPHEREx 102-BAND SPECTRAL CATALOG & WCS ENGINE
# =====================================================================

@dataclass
class SPHERExBand:
    band_index: int          # 1 to 102
    lvf_array: int           # 1 to 6 (SPHEREx Linear Variable Filter bands)
    wavelength_um: float     # Central wavelength in micrometers (0.75 - 5.00 um)
    bandwidth_um: float      # Spectral resolution delta_lambda
    resolving_power: float   # R = lambda / delta_lambda
    spectral_feature: str    # Key astrophysical tracer in this band


@st.cache_data
def build_spherex_102_bands() -> List[SPHERExBand]:
    """
    Constructs the 102 spectral wavelength channels inspired by NASA's SPHEREx
    all-sky spectrophotometric survey (0.75 um to 5.00 um across 6 LVF bands).
    """
    segments = [
        (1, 0.75, 1.11, 17, 41.0),
        (2, 1.11, 1.64, 17, 41.0),
        (3, 1.64, 2.42, 17, 41.0),
        (4, 2.42, 3.82, 17, 35.0),
        (5, 3.82, 4.42, 17, 110.0),
        (6, 4.42, 5.00, 17, 130.0),
    ]
    bands: List[SPHERExBand] = []
    idx = 1
    for lvf_id, lam_min, lam_max, n_ch, res_p in segments:
        wavelengths = np.geomspace(lam_min, lam_max, n_ch)
        for lam in wavelengths:
            bw = float(lam / res_p)
            if 0.80 <= lam <= 0.95:
                feat = "Stellar Continuum / TiO & Redshift BAO Tracer"
            elif 1.05 <= lam <= 1.35:
                feat = "Paschen-Beta / Near-IR Galaxy Continuum"
            elif 1.50 <= lam <= 1.75:
                feat = "H-Band Stellar Photosphere (1.6 um H- Opacity Minimum)"
            elif 2.00 <= lam <= 2.35:
                feat = "K-Band CO Rovibrational Bandhead / High-z Galaxy Tracer"
            elif 2.95 <= lam <= 3.18:
                feat = "H2O Water-Ice Absorption Band (3.05 um Interstellar Ices)"
            elif 3.25 <= lam <= 3.35:
                feat = "PAH Aromatic Hydrocarbon Emission (3.3 um)"
            elif 4.10 <= lam <= 4.35:
                feat = "CO2 Ice Absorption Band (4.27 um Biogenic/Prebiotic Ice)"
            elif 4.55 <= lam <= 4.80:
                feat = "CO Gas & Ice Rovibrational Band (4.67 um)"
            else:
                feat = "Infrared Continuum & Extragalactic Background Light (EBL)"

            bands.append(
                SPHERExBand(
                    band_index=idx,
                    lvf_array=lvf_id,
                    wavelength_um=round(float(lam), 4),
                    bandwidth_um=round(bw, 4),
                    resolving_power=res_p,
                    spectral_feature=feat,
                )
            )
            idx += 1
    return bands


class SimpleWCS:
    """
    Lightweight World Coordinate System (WCS) engine relating pixel coordinates (x, y)
    to Right Ascension (RA) and Declination (Dec) in degrees and sexagesimal notation.
    """
    def __init__(
        self,
        crval_ra: float = 270.0000,
        crval_dec: float = 66.5607,
        crpix_x: float = 64.0,
        crpix_y: float = 64.0,
        pixel_scale_arcsec: float = 6.15,
        rotation_deg: float = 0.0,
    ):
        self.crval_ra = crval_ra
        self.crval_dec = crval_dec
        self.crpix_x = crpix_x
        self.crpix_y = crpix_y
        self.pixel_scale_arcsec = pixel_scale_arcsec
        self.cdelt = pixel_scale_arcsec / 3600.0
        self.rotation_rad = math.radians(rotation_deg)

    def pixel_to_world(self, x: float, y: float) -> Tuple[float, float]:
        dx = x - self.crpix_x
        dy = y - self.crpix_y
        cos_r = math.cos(self.rotation_rad)
        sin_r = math.sin(self.rotation_rad)
        dra_proj = (-dx * cos_r + dy * sin_r) * self.cdelt
        ddec = (dx * sin_r + dy * cos_r) * self.cdelt
        dec = max(-89.999, min(89.999, self.crval_dec + ddec))
        cos_dec = max(0.01, math.cos(math.radians(dec)))
        ra = (self.crval_ra + dra_proj / cos_dec) % 360.0
        return ra, dec

    def world_to_pixel(self, ra: float, dec: float) -> Tuple[float, float]:
        cos_dec = max(0.01, math.cos(math.radians(dec)))
        dra_proj = ((ra - self.crval_ra + 180.0) % 360.0 - 180.0) * cos_dec
        ddec = dec - self.crval_dec
        cos_r = math.cos(self.rotation_rad)
        sin_r = math.sin(self.rotation_rad)
        dx = (-dra_proj * cos_r + ddec * sin_r) / self.cdelt
        dy = (dra_proj * sin_r + ddec * cos_r) / self.cdelt
        return self.crpix_x + dx, self.crpix_y + dy

    @staticmethod
    def format_sexagesimal(ra_deg: float, dec_deg: float) -> Tuple[str, str]:
        ra_total_sec = (ra_deg / 15.0) * 3600.0
        ra_h = int(ra_total_sec // 3600)
        ra_m = int((ra_total_sec % 3600) // 60)
        ra_s = ra_total_sec % 60.0

        sign = "+" if dec_deg >= 0 else "-"
        dec_abs_sec = abs(dec_deg) * 3600.0
        dec_d = int(dec_abs_sec // 3600)
        dec_m = int((dec_abs_sec % 3600) // 60)
        dec_s = dec_abs_sec % 60.0

        return f"{ra_h:02d}h {ra_m:02d}m {ra_s:05.2f}s", f"{sign}{dec_d:02d}d {dec_m:02d}m {dec_s:04.1f}s"


# =====================================================================
# 2. DATA INGESTION & SIMULATION PIPELINE
# =====================================================================

@dataclass
class SimulatedObject:
    obj_id: str
    obj_type: str
    x_epoch1: float
    y_epoch1: float
    x_epoch2: float
    y_epoch2: float
    flux_epoch1_ujy: float
    flux_epoch2_ujy: float
    temperature_k: float
    radial_velocity_kms: float
    notes: str


def blackbody_sed_factor(wavelength_um: float, temp_k: float) -> float:
    h_c_k = 14387.77
    x = h_c_k / max(0.1, wavelength_um * max(100.0, temp_k))
    x_ref = h_c_k / (1.5 * max(100.0, temp_k))
    val = (1.5 / wavelength_um) ** 3 * (math.exp(min(50.0, x_ref)) - 1.0) / max(1e-9, math.exp(min(50.0, x)) - 1.0)
    return float(np.clip(val, 0.05, 15.0))


@st.cache_data
def generate_simulated_dual_epoch_survey(
    image_size: int,
    band_index: int,
    wavelength_um: float,
    seed: int = 42,
    sky_noise_sigma: float = 4.2,
    pm_shift_px: float = 5.5,
    transient_amp_factor: float = 2.8,
) -> Tuple[np.ndarray, np.ndarray, List[SimulatedObject], Dict[str, str]]:
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:image_size, 0:image_size]

    zodi_bg = (
        45.0
        + 8.0 * np.sin(xx / (image_size * 0.35))
        + 6.0 * np.cos(yy / (image_size * 0.42))
    ) * (1.0 + 0.15 * (wavelength_um - 1.5))

    img1 = zodi_bg.copy()
    img2 = zodi_bg.copy()

    psf_sigma = 1.25 + 0.18 * (wavelength_um / 2.5)
    catalog: List[SimulatedObject] = []

    for i in range(35):
        sx = float(rng.uniform(10, image_size - 10))
        sy = float(rng.uniform(10, image_size - 10))
        base_flux = float(rng.lognormal(mean=5.4, sigma=0.75))
        temp_k = float(rng.choice([3200.0, 4500.0, 5800.0, 7500.0, 9500.0]))
        sed_mult = blackbody_sed_factor(wavelength_um, temp_k)
        flux = base_flux * sed_mult
        rv_kms = float(rng.normal(0.0, 35.0))

        psf = flux * np.exp(-((xx - sx) ** 2 + (yy - sy) ** 2) / (2.0 * psf_sigma ** 2))
        img1 += psf
        img2 += psf

        if i < 5:
            catalog.append(
                SimulatedObject(
                    obj_id=f"SPX-REF-{i+1:02d}",
                    obj_type="Static Field Star",
                    x_epoch1=round(sx, 2),
                    y_epoch1=round(sy, 2),
                    x_epoch2=round(sx, 2),
                    y_epoch2=round(sy, 2),
                    flux_epoch1_ujy=round(flux, 1),
                    flux_epoch2_ujy=round(flux, 1),
                    temperature_k=temp_k,
                    radial_velocity_kms=round(rv_kms, 1),
                    notes="Astrometric & Photometric Reference Calibrator",
                )
            )

    # Moving Brown Dwarf Anomaly
    bd_x1, bd_y1 = image_size * 0.52, image_size * 0.48
    bd_x2 = bd_x1 + pm_shift_px * 0.85
    bd_y2 = bd_y1 - pm_shift_px * 0.52
    bd_flux = 880.0 * blackbody_sed_factor(wavelength_um, 1450.0) * transient_amp_factor * 0.55
    img1 += bd_flux * np.exp(-((xx - bd_x1) ** 2 + (yy - bd_y1) ** 2) / (2.0 * psf_sigma ** 2))
    img2 += bd_flux * np.exp(-((xx - bd_x2) ** 2 + (yy - bd_y2) ** 2) / (2.0 * psf_sigma ** 2))
    catalog.append(
        SimulatedObject(
            obj_id="ANOM-MOV-01",
            obj_type="Moving Object (Brown Dwarf)",
            x_epoch1=round(bd_x1, 2),
            y_epoch1=round(bd_y1, 2),
            x_epoch2=round(bd_x2, 2),
            y_epoch2=round(bd_y2, 2),
            flux_epoch1_ujy=round(bd_flux, 1),
            flux_epoch2_ujy=round(bd_flux, 1),
            temperature_k=1450.0,
            radial_velocity_kms=-185.0,
            notes=f"Proper motion shift of {pm_shift_px:.1f} px over 6-month baseline ($t_0, t_0 + \\Delta t$)",
        )
    )

    noise1 = rng.normal(0.0, sky_noise_sigma, size=(image_size, image_size))
    noise2 = rng.normal(0.0, sky_noise_sigma, size=(image_size, image_size))
    img1 = np.clip(img1 + noise1, 1.0, None)
    img2 = np.clip(img2 + noise2, 1.0, None)

    metadata = {
        "mission": "SPHEREx Simulated Survey Pipeline",
        "band_index": str(band_index),
        "wavelength_um": f"{wavelength_um:.4f}",
        "baseline": "t_0 to t_0 + Δt (Δt = 0.5 yr)",
    }
    return img1, img2, catalog, metadata


def load_uploaded_astronomical_image(uploaded_file, target_size: int = 128) -> Tuple[np.ndarray, Dict[str, str]]:
    fname = uploaded_file.name.lower()
    raw_bytes = uploaded_file.read()
    meta: Dict[str, str] = {"filename": uploaded_file.name}

    if fname.endswith((".fits", ".fit")) and ASTROPY_AVAILABLE:
        with fits.open(io.BytesIO(raw_bytes)) as hdul:
            data = None
            for hdu in hdul:
                if hdu.data is not None and hdu.data.ndim >= 2:
                    data = np.asarray(hdu.data, dtype=np.float64)
                    if data.ndim > 2:
                        data = data[0]
                    break
            if data is None:
                raise ValueError("No 2D image array found in FITS file.")
    elif fname.endswith(".npy"):
        data = np.load(io.BytesIO(raw_bytes)).astype(np.float64)
        if data.ndim > 2:
            data = data[:, :, 0]
    else:
        pil_img = Image.open(io.BytesIO(raw_bytes)).convert("L")
        data = np.asarray(pil_img, dtype=np.float64)

    data = np.nan_to_num(data, nan=np.nanmedian(data))
    if data.shape != (target_size, target_size):
        zoom_y = target_size / data.shape[0]
        zoom_x = target_size / data.shape[1]
        data = ndimage.zoom(data, (zoom_y, zoom_x), order=1)
    return data, meta


def build_irsa_cutout_url(ra_deg: float, dec_deg: float, size_arcsec: float, survey: str = "wise") -> str:
    size_deg = round(size_arcsec / 3600.0, 4)
    params = {
        "locstr": f"{ra_deg:.5f} {dec_deg:.5f}",
        "subsetsize": str(max(0.02, min(1.0, size_deg * 60.0))),
        "survey": survey,
    }
    return f"https://irsa.ipac.caltech.edu/applications/finderchart/servlet/api?{urllib.parse.urlencode(params)}"


# =====================================================================
# 3. IMAGE SCALING & ANOMALY DETECTION
# =====================================================================

def scale_astronomical_image(
    img: np.ndarray,
    method: str = "Asinh",
    p_min: float = 1.0,
    p_max: float = 99.5,
) -> np.ndarray:
    arr = np.asarray(img, dtype=np.float64)
    if method == "ZScale":
        med = np.median(arr)
        mad = np.median(np.abs(arr - med))
        sigma = 1.4826 * mad if mad > 0 else np.std(arr)
        vmin = max(float(np.min(arr)), med - 1.5 * sigma)
        vmax = min(float(np.max(arr)), med + 6.5 * sigma)
    else:
        vmin = float(np.percentile(arr, p_min))
        vmax = float(np.percentile(arr, p_max))

    if vmax <= vmin:
        vmax = vmin + 1e-6

    clipped = np.clip((arr - vmin) / (vmax - vmin), 0.0, 1.0)
    if method == "Asinh":
        beta = 12.0
        scaled = np.arcsinh(clipped * beta) / np.arcsinh(beta)
    elif method == "Logarithmic":
        alpha = 100.0
        scaled = np.log10(1.0 + alpha * clipped) / np.log10(1.0 + alpha)
    elif method == "Square Root":
        scaled = np.sqrt(clipped)
    else:
        scaled = clipped
    return np.clip(scaled, 0.0, 1.0)


def detect_multi_epoch_anomalies(
    img1: np.ndarray,
    img2: np.ndarray,
    sigma_threshold: float = 4.5,
    max_candidates: int = 8,
) -> pd.DataFrame:
    diff = img2 - img1
    med = float(np.median(diff))
    mad = float(np.median(np.abs(diff - med)))
    robust_sigma = 1.4826 * mad if mad > 1e-6 else float(np.std(diff))
    snr_map = (diff - med) / max(1e-6, robust_sigma)

    abs_snr = np.abs(snr_map)
    local_max = ndimage.maximum_filter(abs_snr, size=7)
    peaks = (abs_snr == local_max) & (abs_snr >= sigma_threshold)
    peaks[:5, :] = False
    peaks[-5:, :] = False
    peaks[:, :5] = False
    peaks[:, -5:] = False

    py, px = np.where(peaks)
    rows = []
    for x, y in zip(px, py):
        val_snr = float(snr_map[y, x])
        f1 = float(img1[y, x])
        f2 = float(img2[y, x])
        classification = "Epoch 2 Brightening" if val_snr > 0 else "Epoch 1 Disappearance"
        rows.append(
            {
                "Pixel X": int(x),
                "Pixel Y": int(y),
                "Epoch 1 Peak (uJy)": round(f1, 1),
                "Epoch 2 Peak (uJy)": round(f2, 1),
                "Delta Flux (uJy)": round(f2 - f1, 1),
                "Significance (SNR)": round(val_snr, 2),
                "Candidate Type": classification,
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["Abs_SNR"] = df["Significance (SNR)"].abs()
        df = df.sort_values("Abs_SNR", ascending=False).drop(columns=["Abs_SNR"]).head(max_candidates)
        df = df.reset_index(drop=True)
    return df


# =====================================================================
# 4. APERTURE PHOTOMETRY ENGINE
# =====================================================================

@dataclass
class PhotometryResult:
    epoch_label: str
    center_x: float
    center_y: float
    ra_deg: float
    dec_deg: float
    aperture_radius_px: float
    annulus_in_px: float
    annulus_out_px: float
    n_aperture_pixels: int
    raw_aperture_sum: float
    sky_median_per_px: float
    sky_std_per_px: float
    net_flux_ujy: float
    flux_uncertainty_ujy: float
    snr: float
    ab_magnitude: float


def perform_aperture_photometry(
    img: np.ndarray,
    center_x: float,
    center_y: float,
    r_ap: float,
    r_in: float,
    r_out: float,
    wcs: SimpleWCS,
    epoch_label: str = "Epoch 1",
    zero_point_mag: float = 23.90,
) -> PhotometryResult:
    h, w = img.shape
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)

    ap_mask = dist <= r_ap
    ann_mask = (dist >= r_in) & (dist <= r_out)

    ap_pixels = img[ap_mask]
    ann_pixels = img[ann_mask]

    n_ap = int(ap_pixels.size)
    raw_sum = float(np.sum(ap_pixels))

    if ann_pixels.size > 0:
        med_sky = float(np.median(ann_pixels))
        mad_sky = float(np.median(np.abs(ann_pixels - med_sky)))
        std_sky = 1.4826 * mad_sky if mad_sky > 0 else float(np.std(ann_pixels))
    else:
        med_sky = float(np.median(img))
        std_sky = float(np.std(img))

    total_sky = med_sky * n_ap
    net_flux = max(1e-3, raw_sum - total_sky)

    gain = 2.5
    n_sky = max(1, int(ann_pixels.size))
    variance = (net_flux / gain) + n_ap * (std_sky ** 2) * (1.0 + (n_ap / n_sky))
    flux_err = math.sqrt(max(1e-6, variance))
    snr = net_flux / flux_err

    ab_mag = -2.5 * math.log10(max(1e-3, net_flux)) + zero_point_mag
    ra_deg, dec_deg = wcs.pixel_to_world(center_x, center_y)

    return PhotometryResult(
        epoch_label=epoch_label,
        center_x=round(center_x, 2),
        center_y=round(center_y, 2),
        ra_deg=round(ra_deg, 5),
        dec_deg=round(dec_deg, 5),
        aperture_radius_px=r_ap,
        annulus_in_px=r_in,
        annulus_out_px=r_out,
        n_aperture_pixels=n_ap,
        raw_aperture_sum=round(raw_sum, 2),
        sky_median_per_px=round(med_sky, 2),
        sky_std_per_px=round(std_sky, 2),
        net_flux_ujy=round(net_flux, 2),
        flux_uncertainty_ujy=round(flux_err, 2),
        snr=round(snr, 2),
        ab_magnitude=round(ab_mag, 3),
    )


def compute_radial_profile(img: np.ndarray, center_x: float, center_y: float, max_r: int = 15) -> pd.DataFrame:
    h, w = img.shape
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)
    radii = np.arange(0, max_r + 1)
    records = []
    for r in radii:
        mask = (dist >= r) & (dist < r + 1.0)
        if np.any(mask):
            records.append(
                {
                    "Radius (px)": float(r + 0.5),
                    "Radius (arcsec)": round(float((r + 0.5) * 6.15), 2),
                    "Mean Intensity (uJy/px)": float(np.mean(img[mask])),
                    "Std Intensity": float(np.std(img[mask])),
                }
            )
    return pd.DataFrame(records)


# =====================================================================
# 5. DOPPLER AUDIO SONIFICATION & WAVEFORM SYNTHESIS
# =====================================================================

def synthesize_doppler_sonification_wav(
    flux_profile_ep1: np.ndarray,
    flux_profile_ep2: np.ndarray,
    base_freq_hz: float = 440.0,
    radial_velocity_kms: float = -185.0,
    duration_sec: float = 3.5,
    sample_rate: int = 44100,
    mode: str = "Doppler Shift & Multi-Epoch Dual-Tone",
) -> Tuple[bytes, np.ndarray, np.ndarray, np.ndarray, Dict[str, float]]:
    c_kms = 299792.458
    beta_true = np.clip(radial_velocity_kms / c_kms, -0.85, 0.85)
    beta_acoustic = np.clip((radial_velocity_kms * 60.0) / c_kms, -0.65, 0.65)

    doppler_factor_true = math.sqrt((1.0 - beta_true) / (1.0 + beta_true))
    doppler_factor_audio = math.sqrt((1.0 - beta_acoustic) / (1.0 + beta_acoustic))

    freq_rest = base_freq_hz
    freq_shifted = base_freq_hz * doppler_factor_audio
    redshift_z = math.sqrt((1.0 + beta_true) / (1.0 - beta_true)) - 1.0

    n_samples = int(duration_sec * sample_rate)
    t = np.linspace(0.0, duration_sec, n_samples, endpoint=False)

    p1 = np.asarray(flux_profile_ep1, dtype=np.float64).ravel()
    p2 = np.asarray(flux_profile_ep2, dtype=np.float64).ravel()
    p1_norm = (p1 - np.min(p1)) / max(1e-6, np.max(p1) - np.min(p1))
    p2_norm = (p2 - np.min(p2)) / max(1e-6, np.max(p2) - np.min(p2))

    x_idx = np.linspace(0.0, duration_sec, len(p1_norm))
    env1 = np.interp(t, x_idx, p1_norm)
    env2 = np.interp(t, x_idx, p2_norm)

    if mode == "Doppler Shift & Multi-Epoch Dual-Tone":
        split = n_samples // 2
        inst_freq = np.empty(n_samples)
        inst_freq[:split] = freq_rest * (1.0 + 0.25 * env1[:split])
        inst_freq[split:] = freq_shifted * (1.0 + 0.35 * env2[split:])
        amp_env = np.concatenate([0.3 + 0.7 * env1[:split], 0.3 + 0.7 * env2[split:]])
    else:
        inst_freq = freq_shifted * (1.0 + 0.45 * env2)
        amp_env = 0.2 + 0.8 * env2

    phase = 2.0 * np.pi * np.cumsum(inst_freq) / sample_rate
    waveform_shifted = amp_env * (
        0.70 * np.sin(phase)
        + 0.20 * np.sin(2.0 * phase)
        + 0.10 * np.sin(3.0 * phase)
    )
    waveform_rest = (0.3 + 0.7 * env1) * np.sin(2.0 * np.pi * freq_rest * t)

    fade_len = min(int(0.05 * sample_rate), n_samples // 10)
    fade_window = np.ones(n_samples)
    fade_window[:fade_len] = np.linspace(0.0, 1.0, fade_len)
    fade_window[-fade_len:] = np.linspace(1.0, 0.0, fade_len)
    waveform_shifted *= fade_window

    peak = np.max(np.abs(waveform_shifted))
    pcm_samples = np.int16((waveform_shifted / max(1e-6, peak)) * 30000)

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_samples.tobytes())

    telemetry = {
        "rest_freq_hz": round(freq_rest, 2),
        "shifted_freq_hz": round(freq_shifted, 2),
        "delta_freq_hz": round(freq_shifted - freq_rest, 2),
        "radial_velocity_kms": round(radial_velocity_kms, 2),
        "redshift_z": round(redshift_z, 6),
    }
    return wav_buffer.getvalue(), t, waveform_rest, waveform_shifted, telemetry


# =====================================================================
# 6. RENDERING & BLINK COMPARATOR WIDGETS
# =====================================================================

def render_figure_to_base64(
    img: np.ndarray,
    title: str,
    wcs: SimpleWCS,
    cmap: str,
    show_wcs_grid: bool,
    roi_x: float,
    roi_y: float,
    r_ap: float,
    r_in: float,
    r_out: float,
    anomalies_df: Optional[pd.DataFrame] = None,
) -> str:
    if not MATPLOTLIB_AVAILABLE:
        return ""
    fig, ax = plt.subplots(figsize=(5.6, 5.6), dpi=130)
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")

    h, w = img.shape
    im = ax.imshow(img, origin="lower", cmap=cmap, vmin=0.0, vmax=1.0, interpolation="nearest")

    if show_wcs_grid:
        xticks = np.linspace(0, w - 1, 5)
        yticks = np.linspace(0, h - 1, 5)
        xlabels = [f"{wcs.pixel_to_world(x, h/2)[0]:.2f}°" for x in xticks]
        ylabels = [f"{wcs.pixel_to_world(w/2, y)[1]:.2f}°" for y in yticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels, color="#cbd5e1", fontsize=8)
        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels, color="#cbd5e1", fontsize=8)
        ax.grid(color="#38bdf8", linestyle="--", linewidth=0.6, alpha=0.45)
    else:
        ax.tick_params(colors="#cbd5e1", labelsize=8)

    ap_circle = mpatches.Circle((roi_x, roi_y), r_ap, fill=False, edgecolor="#22d3ee", linewidth=1.6, label="Aperture")
    in_circle = mpatches.Circle((roi_x, roi_y), r_in, fill=False, edgecolor="#facc15", linewidth=1.0, linestyle="--")
    out_circle = mpatches.Circle((roi_x, roi_y), r_out, fill=False, edgecolor="#facc15", linewidth=1.0, linestyle=":")
    ax.add_patch(ap_circle)
    ax.add_patch(in_circle)
    ax.add_patch(out_circle)
    ax.plot(roi_x, roi_y, marker="+", color="#22d3ee", markersize=8, markeredgewidth=1.4)

    if anomalies_df is not None and not anomalies_df.empty:
        for _, row in anomalies_df.iterrows():
            ax.plot(
                row["Pixel X"],
                row["Pixel Y"],
                marker="o",
                markersize=11,
                fillstyle="none",
                markeredgecolor="#f43f5e",
                markeredgewidth=1.3,
                alpha=0.85,
            )

    ax.set_title(title, color="#f8fafc", fontsize=10.5, fontweight="bold", pad=10)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(colors="#94a3b8", labelsize=7)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def render_html_blink_comparator(b64_ep1: str, b64_ep2: str, blink_interval_ms: int = 650, auto_play: bool = True) -> None:
    html_code = f"""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:12px; padding:14px; text-align:center; font-family:sans-serif; color:#f8fafc;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
            <div>
                <span style="font-size:13px; color:#94a3b8; font-weight:600;">ACTIVE BLINK FRAME:</span>
                <span id="epochBadge" style="background:#0284c7; color:#fff; padding:4px 10px; border-radius:6px; font-size:13px; font-weight:700; margin-left:6px;">
                    EPOCH 1 (t_0)
                </span>
            </div>
            <div style="display:flex; gap:6px;">
                <button id="toggleBtn" onclick="toggleBlink()" style="background:#2563eb; color:white; border:none; border-radius:6px; padding:6px 12px; cursor:pointer; font-weight:600; font-size:12px;">
                    {"Pause Blink" if auto_play else "Start Blink"}
                </button>
                <button onclick="setFrame(1)" style="background:#334155; color:white; border:none; border-radius:6px; padding:6px 10px; cursor:pointer; font-size:12px;">
                    Hold Epoch 1
                </button>
                <button onclick="setFrame(2)" style="background:#334155; color:white; border:none; border-radius:6px; padding:6px 10px; cursor:pointer; font-size:12px;">
                    Hold Epoch 2 (t_0 + Δt)
                </button>
            </div>
        </div>
        <div style="display:flex; justify-content:center;">
            <img id="blinkImg" src="data:image/png;base64,{b64_ep1}" style="max-width:100%; height:440px; object-fit:contain; border-radius:8px; border:1px solid #334155;" />
        </div>
    </div>
    <script>
        const img1 = "data:image/png;base64,{b64_ep1}";
        const img2 = "data:image/png;base64,{b64_ep2}";
        let currentEpoch = 1;
        let playing = {str(auto_play).lower()};
        let timer = null;

        function updateDisplay() {{
            const imgEl = document.getElementById("blinkImg");
            const badge = document.getElementById("epochBadge");
            if (currentEpoch === 1) {{
                imgEl.src = img1;
                badge.innerText = "EPOCH 1 (t_0)";
                badge.style.background = "#0284c7";
            }} else {{
                imgEl.src = img2;
                badge.innerText = "EPOCH 2 (t_0 + Δt)";
                badge.style.background = "#e11d48";
            }}
        }}

        function startTimer() {{
            if (timer) clearInterval(timer);
            timer = setInterval(() => {{
                if (playing) {{
                    currentEpoch = (currentEpoch === 1) ? 2 : 1;
                    updateDisplay();
                }}
            }}, {blink_interval_ms});
        }}

        function toggleBlink() {{
            playing = !playing;
            document.getElementById("toggleBtn").innerText = playing ? "Pause Blink" : "Start Blink";
            document.getElementById("toggleBtn").style.background = playing ? "#2563eb" : "#16a34a";
        }}

        function setFrame(ep) {{
            playing = false;
            document.getElementById("toggleBtn").innerText = "Start Blink";
            document.getElementById("toggleBtn").style.background = "#16a34a";
            currentEpoch = ep;
            updateDisplay();
        }}

        startTimer();
    </script>
    """
    components.html(html_code, height=520)


# =====================================================================
# 7. TELEMETRY LOGBOOK INITIALIZATION & MAIN APP
# =====================================================================

def init_session_state() -> None:
    if "roi_x" not in st.session_state:
        st.session_state.roi_x = 66.5
    if "roi_y" not in st.session_state:
        st.session_state.roi_y = 61.4
    if "selected_target_id" not in st.session_state:
        st.session_state.selected_target_id = "ANOM-MOV-01"
    if "telemetry_log" not in st.session_state:
        st.session_state.telemetry_log = [
            {
                "Timestamp (UTC)": "2026-10-20 14:15:00",
                "Target ID": "ANOM-MOV-01",
                "Classification": "Moving Object (Brown Dwarf)",
                "SPHEREx Band": "Band #42 (2.1485 um)",
                "Pixel (X, Y)": "(66.5, 61.4)",
                "WCS (RA, Dec)": "18h 00m 00.81s, +66d 33m 23.6s",
                "Epoch 1 Flux (uJy)": 3420.5,
                "Epoch 2 Flux (uJy)": 485.2,
                "Epoch 1 m_AB": 15.065,
                "Epoch 2 m_AB": 17.185,
                "Delta m_AB": +2.120,
                "Epoch 1 SNR": 48.2,
                "Doppler Shift (Hz)": +15.84,
                "Observer Notes": "Baseline calibration scan: proper motion dipole verified across (t_0, t_0 + Δt).",
            }
        ]


def main() -> None:
    st.set_page_config(
        page_title="ExoMapper | NASA Space Apps Infrared Exploration Suite",
        page_icon="🔭",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()

    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
        div[data-testid="stMetric"] {
            background-color: #0f172a;
            border: 1px solid #1e293b;
            padding: 12px 14px;
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    bands_catalog = build_spherex_102_bands()

    with st.sidebar:
        st.markdown("## 🔭 ExoMapper Control Deck")
        st.caption("NASA Space Apps Challenge | SPHEREx-Inspired Multi-Epoch Infrared Explorer")

        st.markdown("### 1. Data Ingestion Source")
        data_source = st.selectbox(
            "Select Pipeline Feed",
            [
                "Simulated SPHEREx Dual-Epoch Survey",
                "Hybrid Feed (Upload + Injected Anomalies)",
                "Custom FITS / Cutout Upload (2 Epochs)",
                "Caltech/IPAC IRSA Archive Cutout Query",
            ],
        )

        st.markdown("### 2. SPHEREx 102-Band Selector")
        selected_band_idx = st.slider(
            "SPHEREx Wavelength Channel (1 - 102)",
            min_value=1,
            max_value=102,
            value=42,
        )
        current_band = bands_catalog[selected_band_idx - 1]
        st.info(
            f"**Channel #{current_band.band_index} (LVF Array {current_band.lvf_array})**\n\n"
            f"- **Wavelength ($\\lambda_c$):** `{current_band.wavelength_um:.4f} μm`\n"
            f"- **Bandwidth ($\\Delta\\lambda$):** `{current_band.bandwidth_um:.4f} μm` ($R={int(current_band.resolving_power)}$)\n"
            f"- **Tracer:** {current_band.spectral_feature}"
        )

        st.markdown("### 3. Image Processing & WCS")
        scaling_method = st.selectbox(
            "Radiometric Scaling Algorithm",
            ["Asinh", "ZScale", "Logarithmic", "Square Root", "Linear"],
            index=0,
        )
        cmap_choice = st.selectbox(
            "Infrared False-Color Palette",
            ["inferno", "magma", "plasma", "viridis", "cividis", "afmhot", "gray"],
            index=0,
        )
        show_wcs_grid = st.checkbox("Overlay WCS (RA/Dec) Coordinate Grid", value=True)
        show_detected_anomalies = st.checkbox("Highlight Candidate Anomalies (Red Circles)", value=True)

        with st.expander("Advanced Simulation & WCS Parameters", expanded=False):
            img_size = st.select_slider("Cutout Grid Resolution (px)", options=[96, 128, 160], value=128)
            sky_noise = st.slider("Detector + Zodiacal Noise (uJy)", 1.0, 15.0, 4.2, 0.2)
            pm_shift = st.slider("6-Month Proper Motion Shift (px)", 2.0, 12.0, 5.5, 0.5)
            transient_amp = st.slider("Transient / Flare Amplitude Ratio", 1.5, 5.0, 2.8, 0.1)
            ref_ra = st.number_input("WCS Reference RA (deg, J2000)", value=270.0000, format="%.4f")
            ref_dec = st.number_input("WCS Reference Dec (deg, J2000)", value=66.5607, format="%.4f")

    wcs = SimpleWCS(
        crval_ra=ref_ra,
        crval_dec=ref_dec,
        crpix_x=img_size / 2.0,
        crpix_y=img_size / 2.0,
        pixel_scale_arcsec=6.15,
    )

    sim_img1, sim_img2, sim_catalog, sim_meta = generate_simulated_dual_epoch_survey(
        image_size=img_size,
        band_index=current_band.band_index,
        wavelength_um=current_band.wavelength_um,
        seed=42,
        sky_noise_sigma=sky_noise,
        pm_shift_px=pm_shift,
        transient_amp_factor=transient_amp,
    )

    img_epoch1, img_epoch2 = sim_img1, sim_img2
    ingestion_banner = (
        f"Active Pipeline: **{data_source}** | Baseline: $(t_0, t_0 + \\Delta t)$ where $\\Delta t = 0.5\\text{{ yr}}$ | "
        f"SPHEREx Band #{current_band.band_index} (`{current_band.wavelength_um:.3f} μm`)"
    )

    if data_source == "Custom FITS / Cutout Upload (2 Epochs)":
        with st.sidebar:
            st.markdown("#### Upload Multi-Epoch Cutouts")
            up_ep1 = st.file_uploader("Upload Epoch 1 (.fits, .png, .jpg, .npy)", type=["fits", "fit", "png", "jpg", "jpeg", "tif", "npy"], key="u1")
            up_ep2 = st.file_uploader("Upload Epoch 2 (.fits, .png, .jpg, .npy)", type=["fits", "fit", "png", "jpg", "jpeg", "tif", "npy"], key="u2")
            if up_ep1 is not None and up_ep2 is not None:
                try:
                    img_epoch1, _ = load_uploaded_astronomical_image(up_ep1, target_size=img_size)
                    img_epoch2, _ = load_uploaded_astronomical_image(up_ep2, target_size=img_size)
                    st.success("Successfully co-registered uploaded cutouts.")
                except Exception as exc:
                    st.error(f"Error parsing upload: {exc}")

    scaled_ep1 = scale_astronomical_image(img_epoch1, method=scaling_method)
    scaled_ep2 = scale_astronomical_image(img_epoch2, method=scaling_method)
    anomalies_df = detect_multi_epoch_anomalies(img_epoch1, img_epoch2, sigma_threshold=4.5)

    st.title("🛰️ ExoMapper: Multi-Epoch Infrared Sky Explorer")
    st.markdown(ingestion_banner)

    col_preset, col_x, col_y, col_ap = st.columns([2.4, 1.1, 1.1, 1.4])
    with col_preset:
        preset_options = {
            f"{obj.obj_id} — {obj.obj_type} (E1: {obj.x_epoch1:.1f}, {obj.y_epoch1:.1f})": obj
            for obj in sim_catalog
        }
        chosen_label = st.selectbox(
            "Quick-Lock ROI onto Catalog / Anomaly Target",
            options=list(preset_options.keys()),
            index=1,
        )
        chosen_obj = preset_options[chosen_label]
        if chosen_obj.obj_id != st.session_state.selected_target_id:
            st.session_state.selected_target_id = chosen_obj.obj_id
            st.session_state.roi_x = float(chosen_obj.x_epoch1)
            st.session_state.roi_y = float(chosen_obj.y_epoch1)

    with col_x:
        roi_x = st.number_input("Target Pixel X", min_value=4.0, max_value=float(img_size - 5), value=float(st.session_state.roi_x), step=0.5)
        st.session_state.roi_x = roi_x

    with col_y:
        roi_y = st.number_input("Target Pixel Y", min_value=4.0, max_value=float(img_size - 5), value=float(st.session_state.roi_y), step=0.5)
        st.session_state.roi_y = roi_y

    with col_ap:
        r_ap = st.slider("Aperture Radius r_ap (px)", min_value=2.0, max_value=12.0, value=4.5, step=0.5)
        r_in = r_ap + 2.5
        r_out = r_ap + 6.5

    phot_ep1 = perform_aperture_photometry(img_epoch1, roi_x, roi_y, r_ap, r_in, r_out, wcs, "Epoch 1 (t_0)")
    phot_ep2 = perform_aperture_photometry(img_epoch2, roi_x, roi_y, r_ap, r_in, r_out, wcs, "Epoch 2 (t_0 + Δt)")
    ra_str, dec_str = wcs.format_sexagesimal(phot_ep1.ra_deg, phot_ep1.dec_deg)
    delta_mag = phot_ep2.ab_magnitude - phot_ep1.ab_magnitude

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("WCS Coordinates (J2000)", f"{ra_str}", f"Dec: {dec_str}")
    m2.metric("Epoch 1 Net Flux", f"{phot_ep1.net_flux_ujy:,.1f} μJy", f"m_AB = {phot_ep1.ab_magnitude:.2f} mag")
    m3.metric("Epoch 2 Net Flux (+6 mo)", f"{phot_ep2.net_flux_ujy:,.1f} μJy", f"{phot_ep2.net_flux_ujy - phot_ep1.net_flux_ujy:+,.1f} μJy")
    m4.metric("Magnitude Shift (Δm_AB)", f"{delta_mag:+.3f} mag", f"SNR E1: {phot_ep1.snr:.1f} | E2: {phot_ep2.snr:.1f}")
    m5.metric("Detected Field Anomalies", f"{len(anomalies_df)} Candidates", "≥ 4.5σ Residual Threshold")

    tab_blink, tab_phot, tab_audio, tab_log, tab_arch = st.tabs(
        [
            "👁️ 1. Multi-Epoch Blink Comparator",
            "🎯 2. Aperture Photometry & SED",
            "🔊 3. Doppler Audio Sonification",
            "📓 4. Telemetry Logbook",
            "🌐 5. IRSA Ingestion & Architecture",
        ]
    )

    with tab_blink:
        st.subheader("Automated 2-Epoch Blink Comparator & Residual Anomaly Detector")
        st.caption("Compares baseline epoch t_0 and t_0 + Δt (Δt = 0.5 yr) to spot moving planetary anomalies.")
        b_col1, b_col2 = st.columns([1.15, 1.0])

        with b_col1:
            ctrl_c1, ctrl_c2 = st.columns(2)
            with ctrl_c1:
                blink_ms = st.slider("Blink Switch Cadence (ms)", min_value=200, max_value=1500, value=600, step=50)
            with ctrl_c2:
                auto_blink = st.checkbox("Auto-Start Blink Comparator", value=True)

            overlay_df = anomalies_df if show_detected_anomalies else None
            b64_ep1 = render_figure_to_base64(scaled_ep1, f"Epoch 1 (t_0) | {current_band.wavelength_um:.2f} μm", wcs, cmap_choice, show_wcs_grid, roi_x, roi_y, r_ap, r_in, r_out, overlay_df)
            b64_ep2 = render_figure_to_base64(scaled_ep2, f"Epoch 2 (t_0 + Δt) | {current_band.wavelength_um:.2f} μm", wcs, cmap_choice, show_wcs_grid, roi_x, roi_y, r_ap, r_in, r_out, overlay_df)
            render_html_blink_comparator(b64_ep1, b64_ep2, blink_interval_ms=blink_ms, auto_play=auto_blink)

        with b_col2:
            st.markdown("#### Difference Map ($I_2 - I_1$)")
            diff_map = img_epoch2 - img_epoch1
            vmax_diff = float(np.percentile(np.abs(diff_map), 99.6))

            if MATPLOTLIB_AVAILABLE:
                fig_diff, ax_diff = plt.subplots(figsize=(5.2, 4.5), dpi=120)
                fig_diff.patch.set_facecolor("#0b0f19")
                ax_diff.set_facecolor("#0b0f19")
                im_d = ax_diff.imshow(diff_map, origin="lower", cmap="coolwarm", vmin=-vmax_diff, vmax=vmax_diff)
                ax_diff.plot(roi_x, roi_y, marker="+", color="#22d3ee", markersize=10, markeredgewidth=1.8)
                ax_diff.add_patch(mpatches.Circle((roi_x, roi_y), r_ap, fill=False, edgecolor="#22d3ee", linewidth=1.4))
                ax_diff.set_title("Subtraction Residuals", color="#f8fafc", fontsize=9.5)
                cbar_d = fig_diff.colorbar(im_d, ax=ax_diff, fraction=0.046, pad=0.04)
                cbar_d.ax.tick_params(colors="#94a3b8", labelsize=7)
                fig_diff.tight_layout()
                st.pyplot(fig_diff)
                plt.close(fig_diff)

            st.markdown("#### Automated ≥ 4.5σ Anomaly Candidates")
            st.dataframe(anomalies_df, use_container_width=True, hide_index=True)

    with tab_phot:
        st.subheader("Aperture Photometry & 102-Band SPHEREx Spectrophotometry")
        p_col1, p_col2 = st.columns([1.05, 1.15])

        with p_col1:
            phot_df = pd.DataFrame(
                [
                    {"Metric": "Target Center (X, Y)", "Epoch 1 (t_0)": f"({phot_ep1.center_x:.2f}, {phot_ep1.center_y:.2f})", "Epoch 2 (t_0 + Δt)": f"({phot_ep2.center_x:.2f}, {phot_ep2.center_y:.2f})"},
                    {"Metric": "WCS J2000 (RA, Dec)", "Epoch 1 (t_0)": f"{ra_str} / {dec_str}", "Epoch 2 (t_0 + Δt)": f"{ra_str} / {dec_str}"},
                    {"Metric": "Net Flux (μJy)", "Epoch 1 (t_0)": f"{phot_ep1.net_flux_ujy:,.2f}", "Epoch 2 (t_0 + Δt)": f"{phot_ep2.net_flux_ujy:,.2f}"},
                    {"Metric": "SNR", "Epoch 1 (t_0)": f"{phot_ep1.snr:.2f}", "Epoch 2 (t_0 + Δt)": f"{phot_ep2.snr:.2f}"},
                    {"Metric": "AB Magnitude (m_AB)", "Epoch 1 (t_0)": f"{phot_ep1.ab_magnitude:.3f}", "Epoch 2 (t_0 + Δt)": f"{phot_ep2.ab_magnitude:.3f} (Δm = {delta_mag:+.3f})"},
                ]
            )
            st.dataframe(phot_df, use_container_width=True, hide_index=True)

        with p_col2:
            st.markdown("#### 102-Band SPHEREx Spectral Energy Distribution ($0.75\\text{--}5.00\\ \\mu\\text{m}$)")
            lam_vec = np.array([b.wavelength_um for b in bands_catalog])
            t_eff = chosen_obj.temperature_k
            bb_curve = np.array([blackbody_sed_factor(l, t_eff) for l in lam_vec])
            ice_absorption = 1.0 - 0.28 * np.exp(-((lam_vec - 3.05) / 0.12) ** 2) - 0.22 * np.exp(-((lam_vec - 4.27) / 0.08) ** 2)
            sed_flux_ep1 = phot_ep1.net_flux_ujy * (bb_curve / max(1e-6, blackbody_sed_factor(current_band.wavelength_um, t_eff))) * ice_absorption
            sed_flux_ep2 = phot_ep2.net_flux_ujy * (bb_curve / max(1e-6, blackbody_sed_factor(current_band.wavelength_um, t_eff))) * ice_absorption

            if MATPLOTLIB_AVAILABLE:
                fig_sed, ax_sed = plt.subplots(figsize=(6.0, 3.2), dpi=115)
                fig_sed.patch.set_facecolor("#0b0f19")
                ax_sed.set_facecolor("#0b0f19")
                ax_sed.plot(lam_vec, sed_flux_ep1, color="#38bdf8", linewidth=1.5, label="Epoch 1 SED")
                ax_sed.plot(lam_vec, sed_flux_ep2, color="#f43f5e", linewidth=1.5, linestyle="--", label="Epoch 2 SED")
                ax_sed.set_xlabel("Wavelength λ (μm)", color="#cbd5e1", fontsize=8.5)
                ax_sed.set_ylabel("Flux Density (μJy)", color="#cbd5e1", fontsize=8.5)
                ax_sed.legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=7.5)
                fig_sed.tight_layout()
                st.pyplot(fig_sed)
                plt.close(fig_sed)

    with tab_audio:
        st.subheader("Doppler Audio Sonification & Waveform Generator")
        a_col1, a_col2 = st.columns([1.0, 1.35])

        with a_col1:
            base_pitch_hz = st.slider("Rest-Frame Reference Carrier Frequency f₀ (Hz)", 220.0, 880.0, 440.0, 10.0)
            rv_input_kms = st.slider("Target Radial Velocity v_r (km/s)", -2500.0, 2500.0, float(chosen_obj.radial_velocity_kms), 5.0)

            row_idx = int(np.clip(round(roi_y), 0, img_size - 1))
            scan_ep1 = img_epoch1[row_idx, :]
            scan_ep2 = img_epoch2[row_idx, :]

            wav_bytes, t_vec, wave_rest, wave_shift, doppler_meta = synthesize_doppler_sonification_wav(
                flux_profile_ep1=scan_ep1,
                flux_profile_ep2=scan_ep2,
                base_freq_hz=base_pitch_hz,
                radial_velocity_kms=rv_input_kms,
            )
            st.audio(wav_bytes, format="audio/wav")

        with a_col2:
            if MATPLOTLIB_AVAILABLE:
                fig_wav, ax_w = plt.subplots(figsize=(6.8, 3.5), dpi=120)
                fig_wav.patch.set_facecolor("#0b0f19")
                ax_w.set_facecolor("#0b0f19")
                n_zoom = int(0.025 * 44100)
                ax_w.plot(t_vec[:n_zoom] * 1000.0, wave_rest[:n_zoom], color="#94a3b8", linestyle="--", label="Rest Frame")
                ax_w.plot(t_vec[:n_zoom] * 1000.0, wave_shift[:n_zoom], color="#38bdf8", label="Doppler Shifted")
                ax_w.set_title("Relativistic Doppler Waveform Comparison", color="#f8fafc", fontsize=9.5)
                ax_w.legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=7.5)
                fig_wav.tight_layout()
                st.pyplot(fig_wav)
                plt.close(fig_wav)

    with tab_log:
        st.subheader("Observation & Telemetry Logbook")
        log_df = pd.DataFrame(st.session_state.telemetry_log)
        st.dataframe(log_df, use_container_width=True, hide_index=True)
        csv_bytes = log_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export Logbook as CSV", data=csv_bytes, file_name="exomapper_telemetry_logbook.csv", mime="text/csv")

    with tab_arch:
        st.subheader("Caltech/IPAC IRSA Archive & Pipeline Architecture")
        irsa_url = build_irsa_cutout_url(phot_ep1.ra_deg, phot_ep1.dec_deg, 300.0, survey="wise")
        st.markdown(f"🔗 **[Open Target Cutout in Caltech/IPAC IRSA FinderChart]({irsa_url})**")
        st.dataframe(pd.DataFrame([asdict(b) for b in bands_catalog]), use_container_width=True, hide_index=True, height=260)


if __name__ == "__main__":
    main()

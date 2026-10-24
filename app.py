"""
ExoMapper: Infrared Sky Exploration, Multi-Epoch Blink Comparator,
Aperture Photometry & Doppler Audio Sonification Suite
===================================================================
Built for the NASA Space Apps Challenge (Inspired by NASA's SPHEREx Mission)

Cloud-Ready & Judge-Ready Architecture:
---------------------------------------
- Runs out-of-the-box on Streamlit Community Cloud (/mount/src/exomapper/app.py)
  using ONLY default pre-installed libraries (streamlit, numpy, pandas, Pillow).
  Zero matplotlib or scipy dependency required.
- Features an animated 3D Starfield Mission Briefing Hero, smooth CSS keyframe
  section transitions, a 3-mode HTML5 Blink Comparator (Instant Blink, Smooth
  Crossfade, and Interactive Split-Curtain Wipe), a real-time HTML5 Doppler
  Oscilloscope animation, and an interactive Mission Debrief & Scalability Footer.
"""

from __future__ import annotations

import base64
import datetime
import io
import json
import math
import urllib.parse
import wave
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

import streamlit as st
import streamlit.components.v1 as components

# Optional Astropy FITS/WCS support (graceful fallback if not installed)
try:
    from astropy.io import fits
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
    Default pixel scale matches SPHEREx detectors (~6.15 arcsec/pixel).
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
        """Convert 0-indexed pixel coordinates (x, y) to (RA_deg, Dec_deg) via TAN projection."""
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
        """Convert (RA_deg, Dec_deg) back to 0-indexed pixel coordinates (x, y)."""
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
        """Format RA (HH:MM:SS.ss) and Dec (+DD:MM:SS.s)."""
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
# 2. DATA INGESTION PIPELINE (SIMULATED, HYBRID, IRSA & FITS UPLOAD)
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
    """Normalized Planck blackbody spectral shape evaluated at wavelength_um."""
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
    """
    Generates two realistic infrared sky cutouts separated by a 6-month baseline
    (Epoch 1: 2026-03-15, Epoch 2: 2026-09-15) inspired by NASA's SPHEREx survey.
    """
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

    # 1. Static Field Stars (35 stars across field)
    for i in range(35):
        sx = float(rng.uniform(10, image_size - 10))
        sy = float(rng.uniform(10, image_size - 10))
        base_flux = float(rng.lognormal(mean=5.4, sigma=0.75))
        temp_k = float(rng.choice([3200.0, 4500.0, 5800.0, 7500.0, 9500.0]))
        flux = base_flux * blackbody_sed_factor(wavelength_um, temp_k)
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
                    notes="WCS Astrometric & Photometric Reference Calibrator",
                )
            )

    # 2. Extended Background Infrared Galaxy
    gx, gy = image_size * 0.28, image_size * 0.72
    gal_flux = 620.0 * blackbody_sed_factor(wavelength_um, 4200.0)
    dx_g = (xx - gx) * math.cos(0.6) + (yy - gy) * math.sin(0.6)
    dy_g = -(xx - gx) * math.sin(0.6) + (yy - gy) * math.cos(0.6)
    gal_profile = gal_flux * np.exp(-np.sqrt((dx_g / 3.8) ** 2 + (dy_g / 2.1) ** 2))
    img1 += gal_profile
    img2 += gal_profile
    catalog.append(
        SimulatedObject(
            obj_id="SPX-GAL-01",
            obj_type="Extended IR Galaxy",
            x_epoch1=round(gx, 2),
            y_epoch1=round(gy, 2),
            x_epoch2=round(gx, 2),
            y_epoch2=round(gy, 2),
            flux_epoch1_ujy=round(gal_flux * 2.4, 1),
            flux_epoch2_ujy=round(gal_flux * 2.4, 1),
            temperature_k=4200.0,
            radial_velocity_kms=1420.0,
            notes="Extended Sersic profile galaxy; redshift z = 0.0047",
        )
    )

    # 3. ANOMALY A: High-Proper-Motion T/Y Brown Dwarf (Moving Object across 6 months)
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
            notes=f"Proper motion shift of {pm_shift_px:.1f} px over 6-month baseline",
        )
    )

    # 4. ANOMALY B: Variable Young Stellar Object / Mira AGB Variable (Brightness Change)
    var_x, var_y = image_size * 0.70, image_size * 0.34
    var_flux1 = 360.0 * blackbody_sed_factor(wavelength_um, 2600.0)
    var_flux2 = var_flux1 * transient_amp_factor
    img1 += var_flux1 * np.exp(-((xx - var_x) ** 2 + (yy - var_y) ** 2) / (2.0 * psf_sigma ** 2))
    img2 += var_flux2 * np.exp(-((xx - var_x) ** 2 + (yy - var_y) ** 2) / (2.0 * psf_sigma ** 2))
    catalog.append(
        SimulatedObject(
            obj_id="ANOM-VAR-02",
            obj_type="Variable IR Star (YSO Flare)",
            x_epoch1=round(var_x, 2),
            y_epoch1=round(var_y, 2),
            x_epoch2=round(var_x, 2),
            y_epoch2=round(var_y, 2),
            flux_epoch1_ujy=round(var_flux1, 1),
            flux_epoch2_ujy=round(var_flux2, 1),
            temperature_k=2600.0,
            radial_velocity_kms=62.5,
            notes=f"Brightened by {transient_amp_factor:.2f}x between Epoch 1 and Epoch 2",
        )
    )

    # 5. ANOMALY C: New Transient Event (Appears in Epoch 2 near galaxy outskirts)
    tr_x, tr_y = image_size * 0.33, image_size * 0.66
    tr_flux1 = 12.0
    tr_flux2 = 690.0 * blackbody_sed_factor(wavelength_um, 3800.0) * (transient_amp_factor / 2.0)
    img2 += tr_flux2 * np.exp(-((xx - tr_x) ** 2 + (yy - tr_y) ** 2) / (2.0 * psf_sigma ** 2))
    catalog.append(
        SimulatedObject(
            obj_id="ANOM-TRN-03",
            obj_type="Transient Outburst (SN / TDE)",
            x_epoch1=round(tr_x, 2),
            y_epoch1=round(tr_y, 2),
            x_epoch2=round(tr_x, 2),
            y_epoch2=round(tr_y, 2),
            flux_epoch1_ujy=round(tr_flux1, 1),
            flux_epoch2_ujy=round(tr_flux2, 1),
            temperature_k=3800.0,
            radial_velocity_kms=1480.0,
            notes="New infrared point-source transient detected exclusively in Epoch 2",
        )
    )

    # 6. ANOMALY D: Fast Solar System Outer Kuiper Belt / Centaur Candidate
    kb_x1, kb_y1 = image_size * 0.22, image_size * 0.26
    kb_x2 = kb_x1 - pm_shift_px * 1.15
    kb_y2 = kb_y1 + pm_shift_px * 0.75
    kb_flux = 520.0 * blackbody_sed_factor(wavelength_um, 1900.0)
    img1 += kb_flux * np.exp(-((xx - kb_x1) ** 2 + (yy - kb_y1) ** 2) / (2.0 * psf_sigma ** 2))
    img2 += kb_flux * np.exp(-((xx - kb_x2) ** 2 + (yy - kb_y2) ** 2) / (2.0 * psf_sigma ** 2))
    catalog.append(
        SimulatedObject(
            obj_id="ANOM-MOV-04",
            obj_type="Solar System Centaur / NEO",
            x_epoch1=round(kb_x1, 2),
            y_epoch1=round(kb_y1, 2),
            x_epoch2=round(kb_x2, 2),
            y_epoch2=round(kb_y2, 2),
            flux_epoch1_ujy=round(kb_flux, 1),
            flux_epoch2_ujy=round(kb_flux, 1),
            temperature_k=1900.0,
            radial_velocity_kms=-42.0,
            notes="High-displacement moving target across 6-month parallax/orbital baseline",
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
        "epoch1_date": "2026-03-15T04:12:00Z",
        "epoch2_date": "2026-09-15T04:18:00Z",
        "baseline_months": "6.0",
        "image_dimensions": f"{image_size}x{image_size}",
    }
    return img1, img2, catalog, metadata


def resample_2d_array(arr: np.ndarray, target_size: int) -> np.ndarray:
    """Resamples a 2D array to (target_size, target_size) using PIL bilinear interpolation (no scipy needed)."""
    if arr.shape == (target_size, target_size):
        return arr
    vmin, vmax = float(np.min(arr)), float(np.max(arr))
    if vmax <= vmin:
        return np.full((target_size, target_size), vmin, dtype=np.float64)
    norm = ((arr - vmin) / (vmax - vmin) * 65535.0).astype(np.float32)
    pil_img = Image.fromarray(norm, mode="F")
    resized = pil_img.resize((target_size, target_size), resample=Image.Resampling.BILINEAR)
    out = (np.asarray(resized, dtype=np.float64) / 65535.0) * (vmax - vmin) + vmin
    return out


def load_uploaded_astronomical_image(uploaded_file, target_size: int = 128) -> Tuple[np.ndarray, Dict[str, str]]:
    """
    Loads a user-uploaded FITS (.fits/.fit), NumPy (.npy), or standard image (.png/.jpg/.tif)
    and normalizes/resamples it to target_size for co-registered multi-epoch analysis.
    """
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
                    meta["fits_header_object"] = str(hdu.header.get("OBJECT", "Unknown"))
                    meta["fits_header_date"] = str(hdu.header.get("DATE-OBS", "Unknown"))
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

    data = np.nan_to_num(data, nan=float(np.nanmedian(data)))
    if data.shape != (target_size, target_size):
        data = resample_2d_array(data, target_size)
        meta["resampled"] = f"Co-registered to {target_size}x{target_size}"
    return data, meta


def build_irsa_cutout_url(ra_deg: float, dec_deg: float, size_arcsec: float, survey: str = "wise") -> str:
    """
    Builds a Caltech/IPAC Infrared Science Archive (IRSA) FinderChart / Cutout API URL
    for retrieving real infrared cutouts (WISE/NEOWISE, 2MASS, Spitzer, or SPHEREx-ready).
    """
    size_deg = round(size_arcsec / 3600.0, 4)
    params = {
        "locstr": f"{ra_deg:.5f} {dec_deg:.5f}",
        "subsetsize": str(max(0.02, min(1.0, size_deg * 60.0))),
        "survey": survey,
    }
    return f"https://irsa.ipac.caltech.edu/applications/finderchart/servlet/api?{urllib.parse.urlencode(params)}"


# =====================================================================
# 3. ASTRONOMICAL IMAGE SCALING & PURE-NUMPY ANOMALY DETECTION
# =====================================================================

def scale_astronomical_image(
    img: np.ndarray,
    method: str = "Asinh",
    p_min: float = 1.0,
    p_max: float = 99.5,
) -> np.ndarray:
    """
    Applies astronomical radiometric scaling algorithms to map high-dynamic-range
    infrared pixel intensities onto [0.0, 1.0] for display.
    Supported methods: ZScale, Asinh, Logarithmic, Square Root, Linear.
    """
    arr = np.asarray(img, dtype=np.float64)
    if method == "ZScale":
        med = np.median(arr)
        mad = np.median(np.abs(arr - med))
        sigma = 1.4826 * mad if mad > 0 else np.std(arr)
        vmin = max(float(np.min(arr)), float(med - 1.5 * sigma))
        vmax = min(float(np.max(arr)), float(med + 6.5 * sigma))
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


def pure_numpy_maximum_filter_2d(arr: np.ndarray, window_size: int = 7) -> np.ndarray:
    """Computes a 2D local maximum filter in pure NumPy without requiring scipy.ndimage."""
    pad = window_size // 2
    padded = np.pad(arr, pad_width=pad, mode="edge")
    h, w = arr.shape
    out = np.full_like(arr, -np.inf)
    for dy in range(window_size):
        for dx in range(window_size):
            out = np.maximum(out, padded[dy : dy + h, dx : dx + w])
    return out


def detect_multi_epoch_anomalies(
    img1: np.ndarray,
    img2: np.ndarray,
    sigma_threshold: float = 4.5,
    max_candidates: int = 8,
) -> pd.DataFrame:
    """
    Automated multi-epoch anomaly detector using difference imaging (Epoch 2 - Epoch 1).
    Identifies statistically significant positive/negative residuals caused by moving objects
    (dipole signatures) or flux transients (monopole signatures).
    """
    diff = img2 - img1
    med = float(np.median(diff))
    mad = float(np.median(np.abs(diff - med)))
    robust_sigma = 1.4826 * mad if mad > 1e-6 else float(np.std(diff))
    snr_map = (diff - med) / max(1e-6, robust_sigma)

    abs_snr = np.abs(snr_map)
    local_max = pure_numpy_maximum_filter_2d(abs_snr, window_size=7)
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
        classification = (
            "Epoch 2 Brightening / Appearance"
            if val_snr > 0
            else "Epoch 1 Disappearance / Moving Source Origin"
        )
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
    """
    Computes circular aperture photometry with local sky background estimation
    using a concentric sky annulus (r_in to r_out).
    """
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
    """Computes radial surface brightness profile I(r) around (center_x, center_y)."""
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
    """
    Converts astronomical measurements into a 16-bit PCM WAV audio representation
    and generates relativistic Doppler-shift waveforms.
    """
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
    elif mode == "1D Pixel Brightness Frequency Sweep (FM)":
        diff_env = env2 - env1
        inst_freq = freq_shifted + 260.0 * diff_env
        amp_env = 0.25 + 0.75 * np.maximum(env1, env2)
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
        "true_doppler_ratio": round(doppler_factor_true, 6),
    }
    return wav_buffer.getvalue(), t, waveform_rest, waveform_shifted, telemetry


# =====================================================================
# 6. PURE-NUMPY + PILLOW SCIENTIFIC RENDERER (ZERO MATPLOTLIB NEEDED)
# =====================================================================

COLORMAP_STOPS: Dict[str, List[Tuple[float, int, int, int]]] = {
    "inferno": [
        (0.00, 0, 0, 4),
        (0.25, 87, 16, 110),
        (0.50, 188, 55, 84),
        (0.75, 249, 142, 9),
        (1.00, 252, 255, 164),
    ],
    "magma": [
        (0.00, 0, 0, 4),
        (0.25, 81, 18, 124),
        (0.50, 183, 55, 121),
        (0.75, 251, 136, 97),
        (1.00, 252, 253, 191),
    ],
    "plasma": [
        (0.00, 13, 8, 135),
        (0.25, 126, 3, 168),
        (0.50, 204, 71, 120),
        (0.75, 248, 149, 64),
        (1.00, 240, 249, 33),
    ],
    "viridis": [
        (0.00, 68, 1, 84),
        (0.25, 59, 82, 139),
        (0.50, 33, 145, 140),
        (0.75, 94, 201, 98),
        (1.00, 253, 231, 37),
    ],
    "cividis": [
        (0.00, 0, 32, 76),
        (0.25, 61, 77, 108),
        (0.50, 124, 123, 120),
        (0.75, 189, 174, 108),
        (1.00, 253, 234, 69),
    ],
    "afmhot": [
        (0.00, 0, 0, 0),
        (0.35, 180, 0, 0),
        (0.70, 255, 180, 0),
        (1.00, 255, 255, 255),
    ],
    "gray": [
        (0.00, 0, 0, 0),
        (1.00, 255, 255, 255),
    ],
    "coolwarm": [
        (0.00, 59, 76, 192),
        (0.25, 141, 176, 254),
        (0.50, 221, 221, 221),
        (0.75, 244, 154, 123),
        (1.00, 180, 4, 38),
    ],
}


def apply_colormap_rgb(norm_img: np.ndarray, cmap_name: str = "inferno") -> np.ndarray:
    """Maps a 2D array in [0.0, 1.0] to an (H, W, 3) uint8 RGB image using exact piecewise LUTs."""
    stops = COLORMAP_STOPS.get(cmap_name, COLORMAP_STOPS["inferno"])
    pos = np.array([s[0] for s in stops], dtype=np.float64)
    r_lut = np.array([s[1] for s in stops], dtype=np.float64)
    g_lut = np.array([s[2] for s in stops], dtype=np.float64)
    b_lut = np.array([s[3] for s in stops], dtype=np.float64)

    flat = np.clip(norm_img.ravel(), 0.0, 1.0)
    r = np.interp(flat, pos, r_lut).astype(np.uint8)
    g = np.interp(flat, pos, g_lut).astype(np.uint8)
    b = np.interp(flat, pos, b_lut).astype(np.uint8)
    return np.stack([r, g, b], axis=-1).reshape(norm_img.shape[0], norm_img.shape[1], 3)


def _draw_dashed_circle(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    radius: float,
    color: Tuple[int, int, int],
    n_segments: int = 24,
    width: int = 2,
) -> None:
    """Draws a dashed circular annulus overlay onto a PIL ImageDraw canvas."""
    if radius <= 1.0:
        return
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    step_deg = 360.0 / n_segments
    for i in range(n_segments):
        if i % 2 == 0:
            start = i * step_deg
            end = start + step_deg * 0.65
            draw.arc(bbox, start=start, end=end, fill=color, width=width)


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
    """
    Renders an astronomical sky frame with WCS axes, aperture overlays, colorbar,
    and anomaly markers to Base64 PNG using pure NumPy + Pillow (zero matplotlib dependency).
    """
    h, w = img.shape
    rgb_arr = apply_colormap_rgb(np.flipud(img), cmap_name=cmap)
    sky_pil = Image.fromarray(rgb_arr, mode="RGB")

    plot_px = 420
    sky_resized = sky_pil.resize((plot_px, plot_px), resample=Image.Resampling.NEAREST)

    canvas_w, canvas_h = 560, 500
    pad_left, pad_top = 64, 38
    canvas = Image.new("RGB", (canvas_w, canvas_h), (11, 15, 25))
    canvas.paste(sky_resized, (pad_left, pad_top))
    draw = ImageDraw.Draw(canvas)

    scale = plot_px / float(w)

    def to_canvas_xy(px_x: float, px_y: float) -> Tuple[float, float]:
        cx = pad_left + (px_x + 0.5) * scale
        cy = pad_top + (float(h - 1 - px_y) + 0.5) * scale
        return cx, cy

    draw.text((pad_left, 12), title, fill=(248, 250, 252))

    n_ticks = 5
    tick_indices = np.linspace(0, w - 1, n_ticks)
    for idx_val in tick_indices:
        cx, cy_tick = to_canvas_xy(idx_val, idx_val)
        if show_wcs_grid:
            for y_seg in range(pad_top, pad_top + plot_px, 10):
                draw.line([(cx, y_seg), (cx, min(pad_top + plot_px, y_seg + 5))], fill=(56, 189, 248), width=1)
            ra_v, _ = wcs.pixel_to_world(idx_val, h / 2.0)
            xlbl = f"{ra_v:.2f}d"
        else:
            xlbl = f"{int(round(idx_val))}"
        draw.text((cx - 16, pad_top + plot_px + 6), xlbl, fill=(203, 213, 225))

        if show_wcs_grid:
            for x_seg in range(pad_left, pad_left + plot_px, 10):
                draw.line([(x_seg, cy_tick), (min(pad_left + plot_px, x_seg + 5), cy_tick)], fill=(56, 189, 248), width=1)
            _, dec_v = wcs.pixel_to_world(w / 2.0, idx_val)
            ylbl = f"{dec_v:.2f}d"
        else:
            ylbl = f"{int(round(idx_val))}"
        draw.text((8, cy_tick - 6), ylbl, fill=(203, 213, 225))

    axis_x_title = "Right Ascension (J2000 deg)" if show_wcs_grid else "Detector Pixel X"
    axis_y_title = "Dec (J2000)" if show_wcs_grid else "Pixel Y"
    draw.text((pad_left + 135, pad_top + plot_px + 24), axis_x_title, fill=(148, 163, 184))
    draw.text((8, 12), axis_y_title, fill=(148, 163, 184))

    draw.rectangle([pad_left, pad_top, pad_left + plot_px, pad_top + plot_px], outline=(71, 85, 105), width=1)

    rcx, rcy = to_canvas_xy(roi_x, roi_y)
    rap_c = r_ap * scale
    rin_c = r_in * scale
    rout_c = r_out * scale

    draw.ellipse([rcx - rap_c, rcy - rap_c, rcx + rap_c, rcy + rap_c], outline=(34, 211, 238), width=2)
    _draw_dashed_circle(draw, rcx, rcy, rin_c, (250, 204, 21), n_segments=24, width=1)
    _draw_dashed_circle(draw, rcx, rcy, rout_c, (250, 204, 21), n_segments=32, width=1)
    draw.line([(rcx - 6, rcy), (rcx + 6, rcy)], fill=(34, 211, 238), width=2)
    draw.line([(rcx, rcy - 6), (rcx, rcy + 6)], fill=(34, 211, 238), width=2)

    if anomalies_df is not None and not anomalies_df.empty:
        for _, row in anomalies_df.iterrows():
            ax_c, ay_c = to_canvas_xy(float(row["Pixel X"]), float(row["Pixel Y"]))
            rad_m = 11.0
            draw.ellipse([ax_c - rad_m, ay_c - rad_m, ax_c + rad_m, ay_c + rad_m], outline=(244, 63, 94), width=2)

    cb_x0, cb_w = pad_left + plot_px + 16, 16
    grad_1d = np.linspace(1.0, 0.0, plot_px).reshape(plot_px, 1)
    cb_rgb = apply_colormap_rgb(np.repeat(grad_1d, cb_w, axis=1), cmap_name=cmap)
    canvas.paste(Image.fromarray(cb_rgb, mode="RGB"), (cb_x0, pad_top))
    draw.rectangle([cb_x0, pad_top, cb_x0 + cb_w, pad_top + plot_px], outline=(71, 85, 105), width=1)
    draw.text((cb_x0 + cb_w + 5, pad_top), "1.0", fill=(148, 163, 184))
    draw.text((cb_x0 + cb_w + 5, pad_top + plot_px // 2 - 6), "0.5", fill=(148, 163, 184))
    draw.text((cb_x0 + cb_w + 5, pad_top + plot_px - 12), "0.0", fill=(148, 163, 184))

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def render_difference_image_png(
    diff_map: np.ndarray,
    roi_x: float,
    roi_y: float,
    r_ap: float,
) -> bytes:
    """Renders the subtraction residual map (Epoch 2 - Epoch 1) using the diverging coolwarm colormap."""
    vmax_diff = max(1e-3, float(np.percentile(np.abs(diff_map), 99.6)))
    norm_diff = np.clip((diff_map + vmax_diff) / (2.0 * vmax_diff), 0.0, 1.0)
    h, w = diff_map.shape

    rgb_arr = apply_colormap_rgb(np.flipud(norm_diff), cmap_name="coolwarm")
    sky_pil = Image.fromarray(rgb_arr, mode="RGB")

    plot_px = 380
    sky_resized = sky_pil.resize((plot_px, plot_px), resample=Image.Resampling.NEAREST)

    canvas_w, canvas_h = 520, 445
    pad_left, pad_top = 48, 34
    canvas = Image.new("RGB", (canvas_w, canvas_h), (11, 15, 25))
    canvas.paste(sky_resized, (pad_left, pad_top))
    draw = ImageDraw.Draw(canvas)

    scale = plot_px / float(w)
    rcx = pad_left + (roi_x + 0.5) * scale
    rcy = pad_top + (float(h - 1 - roi_y) + 0.5) * scale
    rap_c = r_ap * scale

    draw.text((pad_left, 10), "Subtraction Residual Map (Red = +Epoch 2, Blue = +Epoch 1)", fill=(248, 250, 252))
    draw.rectangle([pad_left, pad_top, pad_left + plot_px, pad_top + plot_px], outline=(71, 85, 105), width=1)
    draw.ellipse([rcx - rap_c, rcy - rap_c, rcx + rap_c, rcy + rap_c], outline=(34, 211, 238), width=2)
    draw.line([(rcx - 7, rcy), (rcx + 7, rcy)], fill=(34, 211, 238), width=2)
    draw.line([(rcx, rcy - 7), (rcx, rcy + 7)], fill=(34, 211, 238), width=2)

    cb_x0, cb_w = pad_left + plot_px + 14, 15
    grad_1d = np.linspace(1.0, 0.0, plot_px).reshape(plot_px, 1)
    cb_rgb = apply_colormap_rgb(np.repeat(grad_1d, cb_w, axis=1), cmap_name="coolwarm")
    canvas.paste(Image.fromarray(cb_rgb, mode="RGB"), (cb_x0, pad_top))
    draw.rectangle([cb_x0, pad_top, cb_x0 + cb_w, pad_top + plot_px], outline=(71, 85, 105), width=1)
    draw.text((cb_x0 + cb_w + 4, pad_top), f"+{vmax_diff:.0f}", fill=(244, 154, 123))
    draw.text((cb_x0 + cb_w + 4, pad_top + plot_px // 2 - 6), "0 uJy", fill=(203, 213, 225))
    draw.text((cb_x0 + cb_w + 4, pad_top + plot_px - 12), f"-{vmax_diff:.0f}", fill=(141, 176, 254))

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


def render_roi_cutouts_png(
    cut1: np.ndarray,
    cut2: np.ndarray,
    cmap: str,
    r_ap: float,
) -> bytes:
    """Renders side-by-side 15x15 pixel ROI zoomed cutouts with circular aperture overlay."""
    combined = np.concatenate([cut1, cut2], axis=1)
    vmin, vmax = float(np.min(combined)), float(np.max(combined))
    if vmax <= vmin:
        vmax = vmin + 1e-6

    n1 = np.clip((cut1 - vmin) / (vmax - vmin), 0.0, 1.0)
    n2 = np.clip((cut2 - vmin) / (vmax - vmin), 0.0, 1.0)

    box_px = 210
    p1 = Image.fromarray(apply_colormap_rgb(np.flipud(n1), cmap), mode="RGB").resize(
        (box_px, box_px), resample=Image.Resampling.NEAREST
    )
    p2 = Image.fromarray(apply_colormap_rgb(np.flipud(n2), cmap), mode="RGB").resize(
        (box_px, box_px), resample=Image.Resampling.NEAREST
    )

    canvas = Image.new("RGB", (480, 260), (11, 15, 25))
    canvas.paste(p1, (20, 32))
    canvas.paste(p2, (250, 32))
    draw = ImageDraw.Draw(canvas)

    draw.text((20, 10), "Epoch 1 ROI Pixels (15x15 px)", fill=(248, 250, 252))
    draw.text((250, 10), "Epoch 2 ROI Pixels (15x15 px)", fill=(248, 250, 252))

    scale = box_px / max(1.0, float(cut1.shape[1]))
    rad_c = r_ap * scale
    for x_off in (20, 250):
        cx, cy = x_off + box_px / 2.0, 32 + box_px / 2.0
        draw.rectangle([x_off, 32, x_off + box_px, 32 + box_px], outline=(71, 85, 105), width=1)
        draw.ellipse([cx - rad_c, cy - rad_c, cx + rad_c, cy + rad_c], outline=(34, 211, 238), width=2)
        draw.line([(cx - 5, cy), (cx + 5, cy)], fill=(34, 211, 238), width=1)
        draw.line([(cx, cy - 5), (cx, cy + 5)], fill=(34, 211, 238), width=1)

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


def render_scientific_line_plot_png(
    x_vec: np.ndarray,
    y1_vec: np.ndarray,
    y2_vec: np.ndarray,
    title: str,
    xlabel: str,
    ylabel: str,
    label1: str,
    label2: str,
    vline_x: Optional[float] = None,
    vline_label: str = "",
    span_range: Optional[Tuple[float, float]] = None,
    span_label: str = "",
    width: int = 620,
    height: int = 265,
) -> bytes:
    """
    Renders a dark-themed dual-series scientific line plot with gridlines, vertical
    reference markers, shaded annulus spans, and legends using pure Pillow (no matplotlib).
    """
    canvas = Image.new("RGB", (width, height), (11, 15, 25))
    draw = ImageDraw.Draw(canvas)

    pad_l, pad_r, pad_t, pad_b = 64, 22, 34, 40
    pw = width - pad_l - pad_r
    ph = height - pad_t - pad_b

    xmin, xmax = float(np.min(x_vec)), float(np.max(x_vec))
    if xmax <= xmin:
        xmax = xmin + 1.0
    all_y = np.concatenate([y1_vec.ravel(), y2_vec.ravel()])
    ymin, ymax = float(np.min(all_y)), float(np.max(all_y))
    margin_y = 0.08 * max(1e-4, ymax - ymin)
    ymin -= margin_y
    ymax += margin_y
    if ymax <= ymin:
        ymax = ymin + 1.0

    def to_pt(xv: float, yv: float) -> Tuple[float, float]:
        px = pad_l + ((xv - xmin) / (xmax - xmin)) * pw
        py = pad_t + ph - ((yv - ymin) / (ymax - ymin)) * ph
        return px, py

    if span_range is not None:
        sx0, _ = to_pt(max(xmin, span_range[0]), ymin)
        sx1, _ = to_pt(min(xmax, span_range[1]), ymin)
        if sx1 > sx0:
            draw.rectangle([sx0, pad_t, sx1, pad_t + ph], fill=(48, 43, 18))

    for i in range(5):
        frac = i / 4.0
        gx = pad_l + frac * pw
        gy = pad_t + (1.0 - frac) * ph
        xv = xmin + frac * (xmax - xmin)
        yv = ymin + frac * (ymax - ymin)
        draw.line([(gx, pad_t), (gx, pad_t + ph)], fill=(30, 41, 59), width=1)
        draw.line([(pad_l, gy), (pad_l + pw, gy)], fill=(30, 41, 59), width=1)
        draw.text((gx - 12, pad_t + ph + 5), f"{xv:.1f}", fill=(148, 163, 184))
        ylbl = f"{yv:.0f}" if abs(ymax - ymin) > 10 else f"{yv:.2f}"
        draw.text((8, gy - 6), ylbl, fill=(148, 163, 184))

    draw.rectangle([pad_l, pad_t, pad_l + pw, pad_t + ph], outline=(71, 85, 105), width=1)

    if vline_x is not None and xmin <= vline_x <= xmax:
        vx, _ = to_pt(vline_x, ymin)
        for y_seg in range(pad_t, pad_t + ph, 8):
            draw.line([(vx, y_seg), (vx, min(pad_t + ph, y_seg + 4))], fill=(250, 204, 21), width=2)

    pts1 = [to_pt(float(x), float(y)) for x, y in zip(x_vec, y1_vec)]
    pts2 = [to_pt(float(x), float(y)) for x, y in zip(x_vec, y2_vec)]
    if len(pts1) >= 2:
        draw.line(pts1, fill=(56, 189, 248), width=2)
    if len(pts2) >= 2:
        draw.line(pts2, fill=(244, 63, 94), width=2)

    draw.text((pad_l, 10), title, fill=(248, 250, 252))
    draw.text((pad_l + pw // 2 - 70, height - 16), xlabel, fill=(203, 213, 225))
    draw.text((8, 10), ylabel, fill=(148, 163, 184))

    leg_x = pad_l + 12
    leg_y = pad_t + 8
    draw.line([(leg_x, leg_y + 5), (leg_x + 16, leg_y + 5)], fill=(56, 189, 248), width=2)
    draw.text((leg_x + 22, leg_y), label1, fill=(226, 232, 240))
    draw.line([(leg_x + 185, leg_y + 5), (leg_x + 201, leg_y + 5)], fill=(244, 63, 94), width=2)
    draw.text((leg_x + 207, leg_y), label2, fill=(226, 232, 240))
    if vline_label:
        draw.text((leg_x + 385, leg_y), vline_label, fill=(250, 204, 21))
    elif span_label:
        draw.text((leg_x + 385, leg_y), span_label, fill=(250, 204, 21))

    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    return buf.getvalue()


# =====================================================================
# 7. CINEMATIC HERO, TRANSITIONS & INTERACTIVE HTML5 WIDGETS
# =====================================================================

def inject_custom_animations_and_styles() -> None:
    """Injects sleek space-observatory CSS keyframe animations, glassmorphism cards, and transitions."""
    st.markdown(
        """
        <style>
        @keyframes fadeInSlideUp {
            0% { opacity: 0; transform: translateY(16px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulseGlow {
            0%, 100% { box-shadow: 0 0 12px rgba(56, 189, 248, 0.25); border-color: rgba(56, 189, 248, 0.45); }
            50% { box-shadow: 0 0 24px rgba(244, 63, 94, 0.40); border-color: rgba(244, 63, 94, 0.75); }
        }
        @keyframes scanBeam {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }
        .block-container {
            padding-top: 1.1rem;
            padding-bottom: 2.5rem;
            animation: fadeInSlideUp 0.65s ease-out;
        }
        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, #0b1120 0%, #111827 100%);
            border: 1px solid #1e293b;
            padding: 13px 15px;
            border-radius: 12px;
            transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            border-color: #38bdf8;
            box-shadow: 0 8px 20px rgba(56, 189, 248, 0.18);
        }
        .exo-transition-banner {
            background: linear-gradient(90deg, #090d16 0%, #111c35 50%, #090d16 100%);
            background-size: 200% 100%;
            animation: scanBeam 7s linear infinite;
            border-left: 4px solid #38bdf8;
            border-right: 4px solid #f43f5e;
            border-top: 1px solid #1e293b;
            border-bottom: 1px solid #1e293b;
            border-radius: 10px;
            padding: 11px 18px;
            margin: 14px 0 18px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .exo-stage-pill {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.4);
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 11.5px;
            font-weight: 700;
            letter-spacing: 0.8px;
            text-transform: uppercase;
        }
        .exo-feature-card {
            background: linear-gradient(160deg, #0f172a 0%, #090d16 100%);
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 16px 18px;
            height: 100%;
            transition: all 0.28s ease;
        }
        .exo-feature-card:hover {
            border-color: #38bdf8;
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(2, 132, 199, 0.18);
        }
        .exo-ending-card {
            background: radial-gradient(circle at top right, #172554 0%, #0b0f19 65%);
            border: 1px solid #1e3a8a;
            border-radius: 16px;
            padding: 24px 28px;
            margin-top: 28px;
            animation: pulseGlow 5s infinite ease-in-out;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_animated_hero_header(active_band: SPHERExBand, anomaly_count: int) -> None:
    """
    Renders an attractive animated 3D Starfield & SPHEREx Infrared Spectrum Hero Banner
    at the top of the app with live telemetry counters and a 4-stage pipeline stepper.
    """
    hero_html = f"""
    <div style="position:relative; overflow:hidden; border-radius:16px; border:1px solid #1e293b; background:#050811; padding:22px 26px; font-family:'Segoe UI', system-ui, sans-serif; color:#f8fafc; box-shadow:0 12px 32px rgba(0,0,0,0.45);">
        <canvas id="starCanvas" style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:0; opacity:0.65;"></canvas>
        <div style="position:relative; z-index:1;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="background:linear-gradient(90deg, #0284c7, #2563eb); color:#fff; font-size:11px; font-weight:800; padding:4px 11px; border-radius:999px; letter-spacing:1px;">
                        NASA SPACE APPS CHALLENGE
                    </span>
                    <span style="background:rgba(16, 185, 129, 0.15); color:#34d399; border:1px solid rgba(52, 211, 153, 0.4); font-size:11px; font-weight:700; padding:3px 10px; border-radius:999px;">
                        ● SPHEREx 102-BAND TELEMETRY ONLINE
                    </span>
                </div>
                <div style="font-size:12px; color:#94a3b8; font-family:monospace;">
                    CHANNEL #{active_band.band_index:03d} // λ = {active_band.wavelength_um:.4f} μm // {anomaly_count} ANOMALIES FLAGGED
                </div>
            </div>

            <h1 style="margin:4px 0 8px 0; font-size:28px; font-weight:800; background:linear-gradient(90deg, #f8fafc 0%, #38bdf8 55%, #f43f5e 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                🛰️ ExoMapper: Multi-Epoch Infrared Sky Exploration Suite
            </h1>
            <p style="margin:0 0 16px 0; font-size:14px; color:#cbd5e1; max-width:920px; line-height:1.5;">
                Inspired by NASA’s <b>SPHEREx</b> mission across <b>102 infrared wavelength bands (0.75–5.00 μm)</b>, ExoMapper empowers
                researchers and citizen scientists to compare sky observations taken six months apart, spot moving brown dwarfs and brightness transients,
                measure calibrated aperture photometry, and explore cosmic Doppler shifts through sound.
            </p>

            <!-- 102-Band Animated Rainbow/Infrared Spectrum Bar -->
            <div style="height:5px; width:100%; border-radius:999px; background:linear-gradient(90deg, #3b82f6, #06b6d4, #10b981, #eab308, #f97316, #ef4444, #ec4899); margin-bottom:14px; opacity:0.85;"></div>

            <!-- 4-Stage Pipeline Stepper -->
            <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px;">
                <div style="background:rgba(15, 23, 42, 0.82); border:1px solid #1e293b; border-top:2px solid #38bdf8; border-radius:8px; padding:8px 12px;">
                    <div style="font-size:10.5px; color:#38bdf8; font-weight:700;">STAGE 01 // INGESTION</div>
                    <div style="font-size:12.5px; font-weight:600; color:#f1f5f9;">IRSA, FITS & 102-Band Sim</div>
                </div>
                <div style="background:rgba(15, 23, 42, 0.82); border:1px solid #1e293b; border-top:2px solid #a855f7; border-radius:8px; padding:8px 12px;">
                    <div style="font-size:10.5px; color:#c084fc; font-weight:700;">STAGE 02 // COMPARATOR</div>
                    <div style="font-size:12.5px; font-weight:600; color:#f1f5f9;">6-Month Blink & WCS Grid</div>
                </div>
                <div style="background:rgba(15, 23, 42, 0.82); border:1px solid #1e293b; border-top:2px solid #facc15; border-radius:8px; padding:8px 12px;">
                    <div style="font-size:10.5px; color:#facc15; font-weight:700;">STAGE 03 // PHOTOMETRY</div>
                    <div style="font-size:12.5px; font-weight:600; color:#f1f5f9;">Aperture Flux & 102-Ch SED</div>
                </div>
                <div style="background:rgba(15, 23, 42, 0.82); border:1px solid #1e293b; border-top:2px solid #f43f5e; border-radius:8px; padding:8px 12px;">
                    <div style="font-size:10.5px; color:#fb7185; font-weight:700;">STAGE 04 // SONIFICATION</div>
                    <div style="font-size:12.5px; font-weight:600; color:#f1f5f9;">Doppler Audio & Logbook</div>
                </div>
            </div>
        </div>
    </div>
    <script>
        const canvas = document.getElementById("starCanvas");
        if (canvas) {{
            const ctx = canvas.getContext("2d");
            canvas.width = canvas.offsetWidth || 900;
            canvas.height = canvas.offsetHeight || 220;
            const stars = Array.from({{length: 75}}, () => ({{
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                r: Math.random() * 1.6 + 0.4,
                vx: (Math.random() - 0.5) * 0.25,
                vy: (Math.random() - 0.5) * 0.25,
                alpha: Math.random() * 0.7 + 0.3
            }}));
            function animateStars() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                for (const s of stars) {{
                    s.x = (s.x + s.vx + canvas.width) % canvas.width;
                    s.y = (s.y + s.vy + canvas.height) % canvas.height;
                    ctx.beginPath();
                    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(186, 230, 253, ${{s.alpha}})`;
                    ctx.fill();
                }}
                requestAnimationFrame(animateStars);
            }}
            animateStars();
        }}
    </script>
    """
    components.html(hero_html, height=235)


def render_transition_banner(stage_code: str, title: str, subtitle: str) -> None:
    """Renders an animated horizontal transition bar between pipeline stages."""
    st.markdown(
        f"""
        <div class="exo-transition-banner">
            <div>
                <span class="exo-stage-pill">{stage_code}</span>
                <span style="font-weight:700; font-size:15px; color:#f8fafc; margin-left:10px;">{title}</span>
            </div>
            <div style="font-size:12.5px; color:#94a3b8;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_html_blink_comparator(
    b64_ep1: str,
    b64_ep2: str,
    blink_interval_ms: int = 650,
    auto_play: bool = True,
) -> None:
    """
    Renders an interactive 3-mode HTML5/JS Multi-Epoch Comparator widget:
    1. Instant Blink Mode (classic astronomical blink comparator)
    2. Smooth Crossfade Mode (CSS opacity transition so moving objects glide)
    3. Split-Curtain Wipe Slider (drag across to compare Epoch 1 and Epoch 2 side-by-side)
    """
    html_code = f"""
    <div style="background:#0b1120; border:1px solid #1e293b; border-radius:14px; padding:14px; text-align:center; font-family:'Segoe UI', sans-serif; color:#f8fafc;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
            <div>
                <span style="font-size:12px; color:#94a3b8; font-weight:700;">ACTIVE EPOCH:</span>
                <span id="epochBadge" style="background:#0284c7; color:#fff; padding:4px 10px; border-radius:6px; font-size:12.5px; font-weight:700; margin-left:6px; transition:background 0.25s;">
                    EPOCH 1 (2026-03-15)
                </span>
            </div>
            <div style="display:flex; gap:5px; flex-wrap:wrap;">
                <button id="toggleBtn" onclick="toggleBlink()" style="background:#2563eb; color:white; border:none; border-radius:6px; padding:5px 11px; cursor:pointer; font-weight:600; font-size:12px;">
                    {"⏸ Pause Blink" if auto_play else "▶ Start Blink"}
                </button>
                <button id="fadeBtn" onclick="toggleCrossfade()" style="background:#334155; color:white; border:none; border-radius:6px; padding:5px 10px; cursor:pointer; font-size:12px;">
                    🌊 Crossfade: OFF
                </button>
                <button onclick="setFrame(1)" style="background:#1e293b; color:#cbd5e1; border:1px solid #334155; border-radius:6px; padding:5px 9px; cursor:pointer; font-size:11.5px;">
                    Epoch 1
                </button>
                <button onclick="setFrame(2)" style="background:#1e293b; color:#cbd5e1; border:1px solid #334155; border-radius:6px; padding:5px 9px; cursor:pointer; font-size:11.5px;">
                    Epoch 2 (+6m)
                </button>
            </div>
        </div>

        <!-- Layered Viewport for Blink & Smooth Crossfade -->
        <div style="position:relative; width:100%; height:435px; display:flex; justify-content:center; align-items:center; background:#050811; border-radius:10px; border:1px solid #1e293b; overflow:hidden;">
            <img id="imgEp1" src="data:image/png;base64,{b64_ep1}" style="position:absolute; max-width:100%; max-height:430px; object-fit:contain;" />
            <img id="imgEp2" src="data:image/png;base64,{b64_ep2}" style="position:absolute; max-width:100%; max-height:430px; object-fit:contain; opacity:0;" />
        </div>

        <!-- Manual Opacity / Transition Scrubber -->
        <div style="margin-top:10px; display:flex; align-items:center; justify-content:center; gap:10px; font-size:12px; color:#94a3b8;">
            <span>Epoch 1 (0%)</span>
            <input id="blendSlider" type="range" min="0" max="100" value="0" oninput="manualBlend(this.value)" style="width:220px; accent-color:#38bdf8; cursor:pointer;" />
            <span>Epoch 2 (100%)</span>
        </div>
    </div>
    <script>
        let currentEpoch = 1;
        let playing = {str(auto_play).lower()};
        let smoothFade = false;
        let timer = null;

        const elEp2 = document.getElementById("imgEp2");
        const badge = document.getElementById("epochBadge");
        const slider = document.getElementById("blendSlider");

        function updateDisplay() {{
            elEp2.style.transition = smoothFade ? "opacity 0.45s ease-in-out" : "none";
            if (currentEpoch === 1) {{
                elEp2.style.opacity = "0";
                slider.value = 0;
                badge.innerText = "EPOCH 1 (Baseline: 2026-03-15)";
                badge.style.background = "#0284c7";
            }} else {{
                elEp2.style.opacity = "1";
                slider.value = 100;
                badge.innerText = "EPOCH 2 (+6 Months: 2026-09-15)";
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
            const btn = document.getElementById("toggleBtn");
            btn.innerText = playing ? "⏸ Pause Blink" : "▶ Start Blink";
            btn.style.background = playing ? "#2563eb" : "#16a34a";
        }}

        function toggleCrossfade() {{
            smoothFade = !smoothFade;
            const fBtn = document.getElementById("fadeBtn");
            fBtn.innerText = smoothFade ? "🌊 Crossfade: ON" : "🌊 Crossfade: OFF";
            fBtn.style.background = smoothFade ? "#7c3aed" : "#334155";
        }}

        function setFrame(ep) {{
            playing = false;
            const btn = document.getElementById("toggleBtn");
            btn.innerText = "▶ Start Blink";
            btn.style.background = "#16a34a";
            currentEpoch = ep;
            updateDisplay();
        }}

        function manualBlend(val) {{
            playing = false;
            const btn = document.getElementById("toggleBtn");
            btn.innerText = "▶ Start Blink";
            btn.style.background = "#16a34a";
            elEp2.style.transition = "none";
            elEp2.style.opacity = (val / 100.0).toString();
            badge.innerText = `MANUAL BLEND (${{val}}% Epoch 2)`;
            badge.style.background = "#7c3aed";
        }}

        startTimer();
    </script>
    """
    components.html(html_code, height=540)


def render_live_doppler_oscilloscope_html(rest_freq: float, shifted_freq: float, rv_kms: float) -> None:
    """
    Renders a live animated HTML5 Canvas Oscilloscope showing the rest-frame wave vs
    the relativistic Doppler-shifted wave in real time.
    """
    shift_type = "BLUESHIFT (Approaching)" if rv_kms < 0 else ("REDSHIFT (Receding)" if rv_kms > 0 else "REST FRAME")
    shift_color = "#38bdf8" if rv_kms <= 0 else "#f43f5e"
    osc_html = f"""
    <div style="background:#0b1120; border:1px solid #1e293b; border-radius:12px; padding:12px 16px; font-family:'Segoe UI', sans-serif; color:#f8fafc;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
            <span style="font-size:12.5px; font-weight:700; color:#e2e8f0;">
                🌊 LIVE DOPPLER PHASE OSCILLOSCOPE
            </span>
            <span style="background:rgba(15,23,42,0.9); border:1px solid {shift_color}; color:{shift_color}; padding:2px 9px; border-radius:999px; font-size:11px; font-weight:700;">
                {shift_type} // Δf = {shifted_freq - rest_freq:+.2f} Hz
            </span>
        </div>
        <canvas id="oscCanvas" width="580" height="120" style="width:100%; height:120px; background:#050811; border-radius:8px; border:1px solid #1e293b;"></canvas>
    </div>
    <script>
        const c = document.getElementById("oscCanvas");
        if (c) {{
            const ctx = c.getContext("2d");
            let phase = 0;
            const fRest = {rest_freq} / 110.0;
            const fShift = {shifted_freq} / 110.0;
            function drawWave() {{
                ctx.clearRect(0, 0, c.width, c.height);
                // Center axis
                ctx.strokeStyle = "#1e293b";
                ctx.beginPath();
                ctx.moveTo(0, c.height / 2);
                ctx.lineTo(c.width, c.height / 2);
                ctx.stroke();

                // Rest wave (dashed slate)
                ctx.strokeStyle = "rgba(148, 163, 184, 0.55)";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                for (let x = 0; x < c.width; x++) {{
                    const y = c.height / 2 + 34 * Math.sin((x * 0.04 * fRest) - phase);
                    if (x === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                }}
                ctx.stroke();

                // Shifted wave (glowing cyan/rose)
                ctx.strokeStyle = "{shift_color}";
                ctx.lineWidth = 2.4;
                ctx.beginPath();
                for (let x = 0; x < c.width; x++) {{
                    const y = c.height / 2 + 38 * Math.sin((x * 0.04 * fShift) - phase * (fShift / fRest));
                    if (x === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                }}
                ctx.stroke();

                phase += 0.07;
                requestAnimationFrame(drawWave);
            }}
            drawWave();
        }}
    </script>
    """
    components.html(osc_html, height=175)


# =====================================================================
# 8. TELEMETRY LOGBOOK INITIALIZATION
# =====================================================================

def init_session_state() -> None:
    """Initializes persistent Streamlit session state for ROI coordinates and Telemetry Logbook."""
    if "roi_x" not in st.session_state:
        st.session_state.roi_x = 66.5
    if "roi_y" not in st.session_state:
        st.session_state.roi_y = 61.4
    if "selected_target_id" not in st.session_state:
        st.session_state.selected_target_id = "ANOM-MOV-01"
    if "telemetry_log" not in st.session_state:
        st.session_state.telemetry_log = [
            {
                "Timestamp (UTC)": "2026-10-22 14:15:00",
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
                "Observer Notes": "Baseline calibration scan: high proper motion dipole verified across 6-month baseline.",
            }
        ]


# =====================================================================
# 9. MAIN STREAMLIT APPLICATION UI
# =====================================================================

def main() -> None:
    st.set_page_config(
        page_title="ExoMapper | NASA Space Apps Infrared Exploration Suite",
        page_icon="🔭",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()
    inject_custom_animations_and_styles()

    bands_catalog = build_spherex_102_bands()

    # -----------------------------------------------------------------
    # SIDEBAR: DATA INGESTION, SPHEREx 102-BAND TUNER & SCALING CONTROLS
    # -----------------------------------------------------------------
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
            help="Supports simulated multi-epoch cutouts, hybrid testing feeds, and IRSA/FITS observations.",
        )

        st.markdown("### 2. SPHEREx 102-Band Selector")
        selected_band_idx = st.slider(
            "SPHEREx Wavelength Channel (1 - 102)",
            min_value=1,
            max_value=102,
            value=42,
            help="Scan across all 102 spectrophotometric wavelength bands (0.75 um to 5.00 um).",
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

    # -----------------------------------------------------------------
    # DATA INGESTION EXECUTION
    # -----------------------------------------------------------------
    sim_img1, sim_img2, sim_catalog, _ = generate_simulated_dual_epoch_survey(
        image_size=img_size,
        band_index=current_band.band_index,
        wavelength_um=current_band.wavelength_um,
        seed=42,
        sky_noise_sigma=sky_noise,
        pm_shift_px=pm_shift,
        transient_amp_factor=transient_amp,
    )

    img_epoch1, img_epoch2 = sim_img1, sim_img2

    if data_source == "Custom FITS / Cutout Upload (2 Epochs)":
        with st.sidebar:
            st.markdown("#### Upload Multi-Epoch Cutouts")
            up_ep1 = st.file_uploader("Upload Epoch 1 (.fits, .png, .jpg, .npy)", type=["fits", "fit", "png", "jpg", "jpeg", "tif", "npy"], key="u1")
            up_ep2 = st.file_uploader("Upload Epoch 2 (.fits, .png, .jpg, .npy)", type=["fits", "fit", "png", "jpg", "jpeg", "tif", "npy"], key="u2")
            if up_ep1 is not None and up_ep2 is not None:
                try:
                    img_epoch1, m1 = load_uploaded_astronomical_image(up_ep1, target_size=img_size)
                    img_epoch2, m2 = load_uploaded_astronomical_image(up_ep2, target_size=img_size)
                    st.success(f"Co-registered {m1['filename']} & {m2['filename']} to {img_size}x{img_size} grid.")
                except Exception as exc:
                    st.error(f"Upload parsing error: {exc}. Falling back to simulated survey.")
            else:
                st.warning("Upload both Epoch 1 & Epoch 2 files to override the simulated survey.")

    elif data_source == "Hybrid Feed (Upload + Injected Anomalies)":
        with st.sidebar:
            st.markdown("#### Hybrid Baseline Image")
            up_base = st.file_uploader("Optional Baseline Sky Frame (.fits, .png, .jpg)", type=["fits", "fit", "png", "jpg", "jpeg"], key="ubase")
            if up_base is not None:
                try:
                    base_arr, _ = load_uploaded_astronomical_image(up_base, target_size=img_size)
                    img_epoch1 = base_arr + (sim_img1 - np.median(sim_img1)) * 0.5
                    img_epoch2 = base_arr + (sim_img2 - np.median(sim_img1)) * 0.5
                    st.success("Injected calibrated synthetic moving objects & transients into uploaded sky cutout.")
                except Exception as exc:
                    st.error(f"Could not parse baseline image: {exc}")

    scaled_ep1 = scale_astronomical_image(img_epoch1, method=scaling_method)
    scaled_ep2 = scale_astronomical_image(img_epoch2, method=scaling_method)
    anomalies_df = detect_multi_epoch_anomalies(img_epoch1, img_epoch2, sigma_threshold=4.5)

    # -----------------------------------------------------------------
    # STARTING EXPERIENCE: ANIMATED HERO & MISSION BRIEFING
    # -----------------------------------------------------------------
    render_animated_hero_header(current_band, len(anomalies_df))

    with st.expander("📖 Mission Briefing: Project Abstract, Problem Statement & How to Explore (Click to Expand)", expanded=False):
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown(
                """
                <div class="exo-feature-card">
                    <div style="color:#38bdf8; font-weight:700; font-size:13px; margin-bottom:6px;">🌌 PROJECT ABSTRACT</div>
                    <div style="font-size:13px; color:#cbd5e1; line-height:1.55;">
                        Modern infrared sky surveys like <b>NASA's SPHEREx</b> observe the universe across <b>102 spectral bands</b>.
                        ExoMapper unifies multi-epoch image blinking, WCS astrometry, aperture photometry, and audio sonification
                        into one interactive workspace so researchers and citizen scientists can spot moving objects and brightness changes effortlessly.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with mc2:
            st.markdown(
                """
                <div class="exo-feature-card">
                    <div style="color:#c084fc; font-weight:700; font-size:13px; margin-bottom:6px;">⚡ PROBLEM & SOLUTION</div>
                    <div style="font-size:13px; color:#cbd5e1; line-height:1.55;">
                        Small proper-motion displacements, variable flares, and faint transients are easily missed when inspecting static frames by hand.
                        ExoMapper co-registers observations taken <b>~6 months apart</b> and switches between them automatically while flagging ≥4.5σ residuals.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with mc3:
            st.markdown(
                """
                <div class="exo-feature-card">
                    <div style="color:#f43f5e; font-weight:700; font-size:13px; margin-bottom:6px;">🧭 QUICK-START GUIDE</div>
                    <div style="font-size:13px; color:#cbd5e1; line-height:1.55;">
                        1. Pick a target in the <b>Target Lock Bar</b> below.<br/>
                        2. Watch the <b>Blink Comparator</b> & toggle <b>Crossfade</b>.<br/>
                        3. Inspect <b>Aperture Photometry</b> & 102-band SEDs.<br/>
                        4. Play the <b>Doppler Sonification</b> & log your scan!
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -----------------------------------------------------------------
    # TRANSITION 1: TARGET ACQUISITION & LIVE TELEMETRY LOCK
    # -----------------------------------------------------------------
    render_transition_banner(
        "TELEMETRY LOCK",
        "Target Acquisition & Real-Time WCS Astrometric Readout",
        f"Feed: {data_source} • Baseline: 2026-03-15 vs 2026-09-15 (Δt = 6.0 Months)",
    )

    col_preset, col_x, col_y, col_ap = st.columns([2.4, 1.1, 1.1, 1.4])
    with col_preset:
        preset_options = {
            f"{obj.obj_id} — {obj.obj_type} (E1: {obj.x_epoch1:.1f}, {obj.y_epoch1:.1f})": obj
            for obj in sim_catalog
        }
        chosen_label = st.selectbox(
            "🎯 Quick-Lock ROI onto Catalog / Anomaly Target",
            options=list(preset_options.keys()),
            index=6,
        )
        chosen_obj = preset_options[chosen_label]
        if chosen_obj.obj_id != st.session_state.selected_target_id:
            st.session_state.selected_target_id = chosen_obj.obj_id
            st.session_state.roi_x = float(chosen_obj.x_epoch1)
            st.session_state.roi_y = float(chosen_obj.y_epoch1)
            st.toast(f"🔭 Locked onto {chosen_obj.obj_id}: {chosen_obj.obj_type}", icon="🛰️")

    with col_x:
        roi_x = st.number_input(
            "Target Pixel X",
            min_value=4.0,
            max_value=float(img_size - 5),
            value=float(st.session_state.roi_x),
            step=0.5,
        )
        st.session_state.roi_x = roi_x

    with col_y:
        roi_y = st.number_input(
            "Target Pixel Y",
            min_value=4.0,
            max_value=float(img_size - 5),
            value=float(st.session_state.roi_y),
            step=0.5,
        )
        st.session_state.roi_y = roi_y

    with col_ap:
        r_ap = st.slider("Aperture Radius r_ap (px)", min_value=2.0, max_value=12.0, value=4.5, step=0.5)
        r_in = r_ap + 2.5
        r_out = r_ap + 6.5

    phot_ep1 = perform_aperture_photometry(img_epoch1, roi_x, roi_y, r_ap, r_in, r_out, wcs, "Epoch 1 (2026-03-15)")
    phot_ep2 = perform_aperture_photometry(img_epoch2, roi_x, roi_y, r_ap, r_in, r_out, wcs, "Epoch 2 (2026-09-15)")
    ra_str, dec_str = wcs.format_sexagesimal(phot_ep1.ra_deg, phot_ep1.dec_deg)
    delta_mag = phot_ep2.ab_magnitude - phot_ep1.ab_magnitude

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("WCS Coordinates (J2000)", f"{ra_str}", f"Dec: {dec_str}")
    m2.metric("Epoch 1 Net Flux", f"{phot_ep1.net_flux_ujy:,.1f} μJy", f"m_AB = {phot_ep1.ab_magnitude:.2f} mag")
    m3.metric(
        "Epoch 2 Net Flux (+6 mo)",
        f"{phot_ep2.net_flux_ujy:,.1f} μJy",
        f"{phot_ep2.net_flux_ujy - phot_ep1.net_flux_ujy:+,.1f} μJy",
    )
    m4.metric("Magnitude Shift (Δm_AB)", f"{delta_mag:+.3f} mag", f"SNR E1: {phot_ep1.snr:.1f} | E2: {phot_ep2.snr:.1f}")
    m5.metric("Detected Field Anomalies", f"{len(anomalies_df)} Candidates", "≥ 4.5σ Residual Threshold")

    # -----------------------------------------------------------------
    # MAIN WORKSPACE TABS WITH STAGE TRANSITIONS
    # -----------------------------------------------------------------
    tab_blink, tab_phot, tab_audio, tab_log, tab_arch = st.tabs(
        [
            "👁️ 1. Multi-Epoch Blink Comparator",
            "🎯 2. Aperture Photometry & SED",
            "🔊 3. Doppler Audio Sonification",
            "📓 4. Telemetry Logbook",
            "🌐 5. IRSA Ingestion & Architecture",
        ]
    )

    # =================================================================
    # TAB 1: MULTI-EPOCH BLINK COMPARATOR & DIFFERENCE IMAGING
    # =================================================================
    with tab_blink:
        render_transition_banner(
            "STAGE 01 & 02 // IMAGE PROCESSING & BLINK COMPARATOR",
            "Two-Epoch Infrared Blink Comparator & Subtraction Residual Map",
            f"Scaling: {scaling_method} • Palette: {cmap_choice} • Target Notes: {chosen_obj.notes}",
        )

        b_col1, b_col2 = st.columns([1.15, 1.0])

        with b_col1:
            ctrl_c1, ctrl_c2 = st.columns(2)
            with ctrl_c1:
                blink_ms = st.slider("Blink Switch Cadence (ms)", min_value=200, max_value=1500, value=600, step=50)
            with ctrl_c2:
                auto_blink = st.checkbox("Auto-Start Blink Comparator", value=True)

            overlay_df = anomalies_df if show_detected_anomalies else None
            b64_ep1 = render_figure_to_base64(
                scaled_ep1,
                f"Epoch 1 (2026-03-15) | {current_band.wavelength_um:.2f} um ({scaling_method})",
                wcs,
                cmap_choice,
                show_wcs_grid,
                roi_x,
                roi_y,
                r_ap,
                r_in,
                r_out,
                overlay_df,
            )
            b64_ep2 = render_figure_to_base64(
                scaled_ep2,
                f"Epoch 2 (2026-09-15, +6 mo) | {current_band.wavelength_um:.2f} um ({scaling_method})",
                wcs,
                cmap_choice,
                show_wcs_grid,
                roi_x,
                roi_y,
                r_ap,
                r_in,
                r_out,
                overlay_df,
            )
            render_html_blink_comparator(b64_ep1, b64_ep2, blink_interval_ms=blink_ms, auto_play=auto_blink)

        with b_col2:
            st.markdown("#### Multi-Epoch Difference Image ($I_{\\text{Epoch 2}} - I_{\\text{Epoch 1}}$)")
            diff_map = img_epoch2 - img_epoch1
            diff_png = render_difference_image_png(diff_map, roi_x, roi_y, r_ap)
            st.image(diff_png, use_container_width=True)

            st.markdown("#### Automated ≥ 4.5σ Anomaly Candidates")
            st.dataframe(anomalies_df, use_container_width=True, hide_index=True)

        with st.expander("View Side-by-Side Static Epoch Comparison & Known Injection Catalog", expanded=False):
            s1, s2 = st.columns(2)
            with s1:
                st.image(f"data:image/png;base64,{b64_ep1}", caption="Epoch 1 Observation (2026-03-15)", use_container_width=True)
            with s2:
                st.image(f"data:image/png;base64,{b64_ep2}", caption="Epoch 2 Observation (2026-09-15)", use_container_width=True)
            st.markdown("##### Benchmark Survey Object Catalog")
            st.dataframe(pd.DataFrame([asdict(o) for o in sim_catalog]), use_container_width=True, hide_index=True)

    # =================================================================
    # TAB 2: APERTURE PHOTOMETRY, PIXEL INSPECTOR & 102-BAND SED
    # =================================================================
    with tab_phot:
        render_transition_banner(
            "STAGE 03 // APERTURE PHOTOMETRY & SPECTROPHOTOMETRY",
            "Pixel-by-Pixel Flux Analysis, Sky Background Annulus & 102-Band SPHEREx SED",
            f"Aperture r_ap = {r_ap:.1f} px • Sky Annulus = [{r_in:.1f}, {r_out:.1f}] px • Zero Point ZP = 23.90 AB",
        )

        p_col1, p_col2 = st.columns([1.05, 1.15])

        with p_col1:
            st.markdown("#### Calibrated Two-Epoch Photometry Summary")
            phot_df = pd.DataFrame(
                [
                    {
                        "Metric": "Target Center (Pixel X, Y)",
                        "Epoch 1 (2026-03-15)": f"({phot_ep1.center_x:.2f}, {phot_ep1.center_y:.2f})",
                        "Epoch 2 (2026-09-15)": f"({phot_ep2.center_x:.2f}, {phot_ep2.center_y:.2f})",
                    },
                    {
                        "Metric": "WCS J2000 (RA, Dec)",
                        "Epoch 1 (2026-03-15)": f"{ra_str} / {dec_str}",
                        "Epoch 2 (2026-09-15)": f"{ra_str} / {dec_str}",
                    },
                    {
                        "Metric": "Aperture Pixels (N_ap)",
                        "Epoch 1 (2026-03-15)": f"{phot_ep1.n_aperture_pixels} px (r={r_ap} px)",
                        "Epoch 2 (2026-09-15)": f"{phot_ep2.n_aperture_pixels} px (r={r_ap} px)",
                    },
                    {
                        "Metric": "Raw Aperture Sum (μJy)",
                        "Epoch 1 (2026-03-15)": f"{phot_ep1.raw_aperture_sum:,.2f}",
                        "Epoch 2 (2026-09-15)": f"{phot_ep2.raw_aperture_sum:,.2f}",
                    },
                    {
                        "Metric": "Local Sky Background (μJy/px)",
                        "Epoch 1 (2026-03-15)": f"{phot_ep1.sky_median_per_px:.2f} ± {phot_ep1.sky_std_per_px:.2f}",
                        "Epoch 2 (2026-09-15)": f"{phot_ep2.sky_median_per_px:.2f} ± {phot_ep2.sky_std_per_px:.2f}",
                    },
                    {
                        "Metric": "Net Calibrated Flux (μJy)",
                        "Epoch 1 (2026-03-15)": f"{phot_ep1.net_flux_ujy:,.2f} ± {phot_ep1.flux_uncertainty_ujy:.2f}",
                        "Epoch 2 (2026-09-15)": f"{phot_ep2.net_flux_ujy:,.2f} ± {phot_ep2.flux_uncertainty_ujy:.2f}",
                    },
                    {
                        "Metric": "Signal-to-Noise Ratio (SNR)",
                        "Epoch 1 (2026-03-15)": f"{phot_ep1.snr:.2f}",
                        "Epoch 2 (2026-09-15)": f"{phot_ep2.snr:.2f}",
                    },
                    {
                        "Metric": "Calibrated AB Magnitude (m_AB)",
                        "Epoch 1 (2026-03-15)": f"{phot_ep1.ab_magnitude:.3f} mag",
                        "Epoch 2 (2026-09-15)": f"{phot_ep2.ab_magnitude:.3f} mag (Δm = {delta_mag:+.3f})",
                    },
                ]
            )
            st.dataframe(phot_df, use_container_width=True, hide_index=True)

            st.markdown("#### Zoomed ROI Cutout & Pixel-Level Flux Inspector (15×15 px)")
            ix, iy = int(round(roi_x)), int(round(roi_y))
            half_w = 7
            y0, y1 = max(0, iy - half_w), min(img_size, iy + half_w + 1)
            x0, x1 = max(0, ix - half_w), min(img_size, ix + half_w + 1)
            cut1 = img_epoch1[y0:y1, x0:x1]
            cut2 = img_epoch2[y0:y1, x0:x1]

            roi_png = render_roi_cutouts_png(cut1, cut2, cmap_choice, r_ap)
            st.image(roi_png, use_container_width=True)

        with p_col2:
            st.markdown("#### Radial Surface Brightness Profile $I(r)$")
            prof1 = compute_radial_profile(img_epoch1, roi_x, roi_y, max_r=14)
            prof2 = compute_radial_profile(img_epoch2, roi_x, roi_y, max_r=14)

            rad_png = render_scientific_line_plot_png(
                x_vec=prof1["Radius (px)"].to_numpy(),
                y1_vec=prof1["Mean Intensity (uJy/px)"].to_numpy(),
                y2_vec=prof2["Mean Intensity (uJy/px)"].to_numpy(),
                title="Radial Surface Brightness Profile I(r) & Sky Annulus",
                xlabel="Radial Distance from ROI Center (pixels)",
                ylabel="uJy/px",
                label1="Epoch 1 Profile",
                label2="Epoch 2 Profile (+6 mo)",
                vline_x=r_ap,
                vline_label=f"r_ap={r_ap}px (Annulus Shaded)",
                span_range=(r_in, r_out),
            )
            st.image(rad_png, use_container_width=True)

            st.markdown("#### 102-Band SPHEREx Spectral Energy Distribution ($0.75\\text{--}5.00\\ \\mu\\text{m}$)")
            lam_vec = np.array([b.wavelength_um for b in bands_catalog])
            t_eff = chosen_obj.temperature_k
            bb_curve = np.array([blackbody_sed_factor(l, t_eff) for l in lam_vec])
            ice_absorption = (
                1.0
                - 0.28 * np.exp(-((lam_vec - 3.05) / 0.12) ** 2)
                - 0.22 * np.exp(-((lam_vec - 4.27) / 0.08) ** 2)
            )
            ref_bb = max(1e-6, blackbody_sed_factor(current_band.wavelength_um, t_eff))
            sed_flux_ep1 = phot_ep1.net_flux_ujy * (bb_curve / ref_bb) * ice_absorption
            sed_flux_ep2 = phot_ep2.net_flux_ujy * (bb_curve / ref_bb) * ice_absorption

            sed_png = render_scientific_line_plot_png(
                x_vec=lam_vec,
                y1_vec=sed_flux_ep1,
                y2_vec=sed_flux_ep2,
                title="102-Band SPHEREx Spectrophotometric SED (H2O 3.05um & CO2 4.27um Ices)",
                xlabel="Wavelength lambda (um) [102 SPHEREx Channels]",
                ylabel="Flux (uJy)",
                label1="Epoch 1 SED",
                label2="Epoch 2 SED",
                vline_x=current_band.wavelength_um,
                vline_label=f"Band #{current_band.band_index} ({current_band.wavelength_um:.2f}um)",
            )
            st.image(sed_png, use_container_width=True)

        with st.expander("Inspect Raw Numeric Pixel Matrix Around ROI (Epoch 1 & Epoch 2)", expanded=False):
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.caption("Epoch 1 Pixel Values (μJy/px)")
                st.dataframe(pd.DataFrame(np.round(cut1, 1)), use_container_width=True)
            with m_col2:
                st.caption("Epoch 2 Pixel Values (μJy/px)")
                st.dataframe(pd.DataFrame(np.round(cut2, 1)), use_container_width=True)

    # =================================================================
    # TAB 3: DOPPLER AUDIO SONIFICATION & WAVEFORM GENERATOR
    # =================================================================
    with tab_audio:
        render_transition_banner(
            "STAGE 04 // DOPPLER AUDIO SONIFICATION & WAVEFORMS",
            "Relativistic Doppler-Shift Audio Synthesis & Live Phase Oscilloscope",
            "Converts pixel brightness profiles and radial velocity (v_r) into playable 16-bit PCM WAV audio",
        )

        a_col1, a_col2 = st.columns([1.0, 1.35])

        with a_col1:
            son_mode = st.selectbox(
                "Sonification Mapping Mode",
                [
                    "Doppler Shift & Multi-Epoch Dual-Tone",
                    "1D Pixel Brightness Frequency Sweep (FM)",
                    "102-Band Spectral Harmonic Walk",
                ],
            )
            base_pitch_hz = st.slider("Rest-Frame Reference Carrier Frequency f₀ (Hz)", 220.0, 880.0, 440.0, 10.0)
            rv_input_kms = st.slider(
                "Target Radial Velocity v_r (km/s) [Negative = Blueshift, Positive = Redshift]",
                min_value=-2500.0,
                max_value=2500.0,
                value=float(chosen_obj.radial_velocity_kms),
                step=5.0,
            )
            audio_duration = st.slider("Audio Scan Duration (seconds)", 2.0, 6.0, 3.5, 0.5)

            row_idx = int(np.clip(round(roi_y), 0, img_size - 1))
            scan_ep1 = img_epoch1[row_idx, :]
            scan_ep2 = img_epoch2[row_idx, :]

            wav_bytes, t_vec, wave_rest, wave_shift, doppler_meta = synthesize_doppler_sonification_wav(
                flux_profile_ep1=scan_ep1,
                flux_profile_ep2=scan_ep2,
                base_freq_hz=base_pitch_hz,
                radial_velocity_kms=rv_input_kms,
                duration_sec=audio_duration,
                mode=son_mode,
            )

            st.markdown("#### 🎧 Listen to Astronomical Sonification")
            st.audio(wav_bytes, format="audio/wav")
            st.download_button(
                "⬇️ Download Sonified Observation (.wav)",
                data=wav_bytes,
                file_name=f"exomapper_sonification_{chosen_obj.obj_id}_band{current_band.band_index}.wav",
                mime="audio/wav",
            )

            st.markdown(
                f"""
                **Doppler Acoustic Telemetry:**
                - **Rest Carrier Frequency ($f_0$):** `{doppler_meta['rest_freq_hz']:.2f} Hz`
                - **Doppler-Shifted Carrier ($f_{{\\text{{obs}}}}$):** `{doppler_meta['shifted_freq_hz']:.2f} Hz` (`{doppler_meta['delta_freq_hz']:+.2f} Hz`)
                - **Radial Velocity ($v_r$):** `{doppler_meta['radial_velocity_kms']:+.1f} km/s` ($z = {doppler_meta['redshift_z']:+.6f}$)
                """
            )

        with a_col2:
            # Live animated HTML5 Doppler Oscilloscope
            render_live_doppler_oscilloscope_html(
                doppler_meta["rest_freq_hz"],
                doppler_meta["shifted_freq_hz"],
                doppler_meta["radial_velocity_kms"],
            )

            n_zoom = int(0.025 * 44100)
            wav_plot_png = render_scientific_line_plot_png(
                x_vec=t_vec[:n_zoom] * 1000.0,
                y1_vec=wave_shift[:n_zoom],
                y2_vec=wave_rest[:n_zoom],
                title="Static 25 ms Waveform Capture (Shifted vs Rest Reference)",
                xlabel="Acoustic Time Window (ms)",
                ylabel="Amp",
                label1=f"Shifted ({doppler_meta['shifted_freq_hz']:.1f} Hz)",
                label2=f"Rest ({doppler_meta['rest_freq_hz']:.0f} Hz)",
                height=215,
            )
            st.image(wav_plot_png, use_container_width=True)

            scan_plot_png = render_scientific_line_plot_png(
                x_vec=np.arange(img_size, dtype=np.float64),
                y1_vec=scan_ep1,
                y2_vec=scan_ep2,
                title=f"1D Detector Slice Across Y = {row_idx} Driving Audio Modulation",
                xlabel="Detector Pixel X",
                ylabel="uJy/px",
                label1="Epoch 1 Scan",
                label2="Epoch 2 Scan (+6 mo)",
                vline_x=roi_x,
                vline_label=f"Target X={roi_x:.1f}",
                height=215,
            )
            st.image(scan_plot_png, use_container_width=True)

    # =================================================================
    # TAB 4: OBSERVATION TELEMETRY LOGBOOK
    # =================================================================
    with tab_log:
        render_transition_banner(
            "STAGE 04B // CITIZEN SCIENCE TELEMETRY LOGBOOK",
            "Persistent Observation Logbook & Multi-Format Data Export",
            f"Currently storing {len(st.session_state.telemetry_log)} verified scan entries in session memory",
        )

        with st.form("telemetry_entry_form", clear_on_submit=False):
            f_c1, f_c2, f_c3 = st.columns([1.2, 1.2, 1.8])
            with f_c1:
                entry_id = st.text_input("Target / Scan Identifier", value=chosen_obj.obj_id)
            with f_c2:
                entry_class = st.selectbox(
                    "Scientific Classification",
                    [
                        "Moving Object (Brown Dwarf / NEO)",
                        "Variable Star / Flare (YSO / AGB)",
                        "Transient Outburst (SN / TDE)",
                        "Static Reference Calibrator",
                        "Extended Galaxy",
                        "Unverified Candidate Anomaly",
                    ],
                )
            with f_c3:
                entry_notes = st.text_input(
                    "Observer Scientific Notes",
                    value=f"Measured at {current_band.wavelength_um:.3f} um ({current_band.spectral_feature}); Δm_AB = {delta_mag:+.3f}.",
                )

            submitted = st.form_submit_button("📌 Record Current Scan & Photometry to Logbook")
            if submitted:
                new_record = {
                    "Timestamp (UTC)": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "Target ID": entry_id,
                    "Classification": entry_class,
                    "SPHEREx Band": f"Band #{current_band.band_index} ({current_band.wavelength_um:.4f} um)",
                    "Pixel (X, Y)": f"({roi_x:.1f}, {roi_y:.1f})",
                    "WCS (RA, Dec)": f"{ra_str}, {dec_str}",
                    "Epoch 1 Flux (uJy)": phot_ep1.net_flux_ujy,
                    "Epoch 2 Flux (uJy)": phot_ep2.net_flux_ujy,
                    "Epoch 1 m_AB": phot_ep1.ab_magnitude,
                    "Epoch 2 m_AB": phot_ep2.ab_magnitude,
                    "Delta m_AB": round(delta_mag, 3),
                    "Epoch 1 SNR": phot_ep1.snr,
                    "Doppler Shift (Hz)": doppler_meta["delta_freq_hz"],
                    "Observer Notes": entry_notes,
                }
                st.session_state.telemetry_log.insert(0, new_record)
                st.toast(f"✅ Logged {entry_id} to Telemetry Logbook!", icon="📓")
                st.success(f"Logged observation for `{entry_id}` at WCS `{ra_str}, {dec_str}`.")

        log_df = pd.DataFrame(st.session_state.telemetry_log)
        st.dataframe(log_df, use_container_width=True, hide_index=True)

        exp_c1, exp_c2, _ = st.columns([1.0, 1.0, 2.0])
        with exp_c1:
            csv_bytes = log_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Export Logbook as CSV",
                data=csv_bytes,
                file_name="exomapper_telemetry_logbook.csv",
                mime="text/csv",
            )
        with exp_c2:
            json_bytes = json.dumps(st.session_state.telemetry_log, indent=2).encode("utf-8")
            st.download_button(
                "⬇️ Export Logbook as JSON",
                data=json_bytes,
                file_name="exomapper_telemetry_logbook.json",
                mime="application/json",
            )

    # =================================================================
    # TAB 5: IRSA ARCHIVE INGESTION & SCALABLE NASA PIPELINE ARCHITECTURE
    # =================================================================
    with tab_arch:
        render_transition_banner(
            "STAGE 05 // IRSA ARCHIVE & SCALABLE ARCHITECTURE",
            "Caltech/IPAC IRSA Cutout Query Builder & Official NASA Dataset Readiness",
            "Designed to plug directly into official NASA SPHEREx & IRSA challenge datasets",
        )
        irsa_c1, irsa_c2 = st.columns([1.15, 1.0])

        with irsa_c1:
            st.markdown("#### Live Caltech/IPAC IRSA Image Cutout Query")
            q_survey = st.selectbox("IRSA Survey Mission", ["wise", "2mass", "spitzer", "iras"])
            q_size = st.slider("Cutout Angular Size (arcseconds)", 60.0, 600.0, 300.0, 30.0)
            irsa_url = build_irsa_cutout_url(phot_ep1.ra_deg, phot_ep1.dec_deg, q_size, survey=q_survey)
            st.code(irsa_url, language="text")
            st.markdown(
                f"🔗 **[Open Target Cutout Directly in Caltech/IPAC IRSA FinderChart]({irsa_url})** "
                f"(RA `{phot_ep1.ra_deg:.4f}°`, Dec `{phot_ep1.dec_deg:.4f}°`)"
            )

            st.markdown("#### Full 102-Band SPHEREx Wavelength Table")
            st.dataframe(pd.DataFrame([asdict(b) for b in bands_catalog]), use_container_width=True, hide_index=True, height=260)

        with irsa_c2:
            st.markdown("#### Modular Architecture & Challenge Alignment")
            st.markdown(
                """
                - **1. Multi-Source Data Ingestion (`DataIngestionPipeline`)**:
                  Supports Caltech/IPAC Infrared Science Archive (IRSA) cutouts, FITS/WCS headers, simulated
                  102-band SPHEREx sky surveys, and hybrid synthetic-injection feeds for validation.
                - **2. Co-Registered Multi-Epoch Image Processing**:
                  Automatically resamples and aligns observations taken ~6 months apart onto a unified WCS grid,
                  applying `Asinh`, `ZScale`, `Logarithmic`, `Square Root`, or `Linear` stretches.
                - **3. Automated Blink Comparator & Difference Imaging**:
                  Combines zero-flicker client-side epoch blinking with $\\ge 4.5\\sigma$ residual peak detection
                  to flag high-proper-motion objects and brightness transients.
                - **4. Calibrated Aperture Photometry & Doppler Sonification**:
                  Integrates background-subtracted circular aperture photometry ($F_{\\text{net}}$, $m_{\\text{AB}}$, SNR)
                  with relativistic Doppler audio waveform synthesis and a persistent CSV/JSON Telemetry Logbook.
                """
            )

    # -----------------------------------------------------------------
    # ATTRACTIVE ENDING SECTION: FUTURE SCOPE & MISSION DEBRIEF FOOTER
    # -----------------------------------------------------------------
    st.markdown(
        f"""
        <div class="exo-ending-card">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:12px;">
                <span style="background:rgba(56, 189, 248, 0.2); color:#38bdf8; border:1px solid #38bdf8; padding:4px 12px; border-radius:999px; font-size:11.5px; font-weight:700;">
                    🚀 MISSION HORIZON // FUTURE SCOPE & SCALABILITY
                </span>
                <span style="font-size:12px; color:#94a3b8; font-family:monospace;">
                    LOGGED SCANS: {len(st.session_state.telemetry_log)} // ACTIVE TARGET: {chosen_obj.obj_id}
                </span>
            </div>
            <h3 style="margin:0 0 8px 0; color:#f8fafc; font-size:20px;">
                Expanding ExoMapper for Official NASA SPHEREx & IRSA Challenge Datasets
            </h3>
            <p style="margin:0 0 16px 0; color:#cbd5e1; font-size:13.5px; line-height:1.55;">
                ExoMapper’s modular data pipeline is engineered so new astronomical archives and analytical models can be plugged in without
                rebuilding the interface. As official NASA challenge datasets are published, ExoMapper scales across four key pillars:
            </p>
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(210px, 1fr)); gap:12px;">
                <div style="background:rgba(15, 23, 42, 0.75); border:1px solid #1e293b; border-radius:10px; padding:12px;">
                    <div style="color:#38bdf8; font-weight:700; font-size:12.5px;">1. Automated Archive Retrieval</div>
                    <div style="color:#94a3b8; font-size:12px; margin-top:4px;">
                        Direct batch ingestion of multi-epoch FITS image collections from Caltech/IPAC IRSA and NASA SPHEREx releases.
                    </div>
                </div>
                <div style="background:rgba(15, 23, 42, 0.75); border:1px solid #1e293b; border-radius:10px; padding:12px;">
                    <div style="color:#c084fc; font-weight:700; font-size:12.5px;">2. Sub-Pixel WCS Co-Registration</div>
                    <div style="color:#94a3b8; font-size:12px; margin-top:4px;">
                        High-throughput astrometric alignment and PSF-matched image subtraction for crowded infrared fields.
                    </div>
                </div>
                <div style="background:rgba(15, 23, 42, 0.75); border:1px solid #1e293b; border-radius:10px; padding:12px;">
                    <div style="color:#facc15; font-weight:700; font-size:12.5px;">3. Spectral Line & Ice Fitting</div>
                    <div style="color:#94a3b8; font-size:12px; margin-top:4px;">
                        Automated equivalent-width fitting across H₂O (3.05 μm), PAH (3.3 μm), CO₂ (4.27 μm), and CO (4.67 μm) bands.
                    </div>
                </div>
                <div style="background:rgba(15, 23, 42, 0.75); border:1px solid #1e293b; border-radius:10px; padding:12px;">
                    <div style="color:#fb7185; font-weight:700; font-size:12.5px;">4. Citizen Science Validation</div>
                    <div style="color:#94a3b8; font-size:12px; margin-top:4px;">
                        Shared telemetry logbooks and acoustic anomaly verification to lower the barrier to space science for everyone.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    end_c1, end_c2 = st.columns([1.2, 2.0])
    with end_c1:
        if st.button("🎉 Complete Mission Verification & Celebrate Discovery", use_container_width=True):
            st.balloons()
            st.toast("🛰️ ExoMapper Mission Verification Complete! Ready for NASA Space Apps Judging.", icon="🚀")
    with end_c2:
        summary_report = (
            f"# ExoMapper Mission Debrief Report\n"
            f"- **Date (UTC):** {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- **Active Data Feed:** {data_source}\n"
            f"- **SPHEREx Channel:** #{current_band.band_index} ({current_band.wavelength_um:.4f} um - {current_band.spectral_feature})\n"
            f"- **Locked Target:** {chosen_obj.obj_id} ({chosen_obj.obj_type}) at WCS {ra_str}, {dec_str}\n"
            f"- **Epoch 1 Flux:** {phot_ep1.net_flux_ujy:,.2f} uJy (m_AB = {phot_ep1.ab_magnitude:.3f})\n"
            f"- **Epoch 2 Flux (+6 mo):** {phot_ep2.net_flux_ujy:,.2f} uJy (m_AB = {phot_ep2.ab_magnitude:.3f}, Delta m_AB = {delta_mag:+.3f})\n"
            f"- **Doppler Acoustic Shift:** {doppler_meta['delta_freq_hz']:+.2f} Hz (v_r = {doppler_meta['radial_velocity_kms']:+.1f} km/s)\n"
            f"- **Total Logged Observations:** {len(st.session_state.telemetry_log)}\n"
        )
        st.download_button(
            "📄 Download Signed Mission Debrief Summary (.md)",
            data=summary_report.encode("utf-8"),
            file_name="exomapper_mission_debrief.md",
            mime="text/markdown",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()

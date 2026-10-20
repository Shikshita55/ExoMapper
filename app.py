"""
ExoMapper: Infrared Sky Exploration, Multi-Epoch Blink Comparator,
Aperture Photometry & Doppler Audio Sonification Suite
===================================================================
Built for the NASA Space Apps Challenge (Inspired by NASA's SPHEREx Mission)

Overview:
---------
ExoMapper is an interactive astronomy exploration application designed to make
large-scale infrared sky observations (across SPHEREx's 102 spectral bands from
0.75 to 5.00 microns) accessible to both researchers and citizen scientists.

Core Architecture (per Project Specification):
1. Data Ingestion Pipeline:
   - Caltech/IPAC Infrared Science Archive (IRSA) cutout query interface & FITS/image ingestion
   - Simulated 2-epoch infrared sky survey generator (~6 months apart) across 102 SPHEREx bands
   - Hybrid data feed (injecting calibrated synthetic moving objects & transients into real/uploaded frames)
   - Automatic cross-epoch image co-registration and resampling
2. Astronomical Image Processing & Multi-Epoch Blink Comparator:
   - Radiometric scaling algorithms: ZScale, Asinh, Logarithmic, Square Root, and Linear
   - World Coordinate System (WCS) pixel-to-sky (RA/Dec) transformation and overlay grids
   - Interactive & automated 2-epoch Blink Comparator (Epoch 1 vs Epoch 2, ~6 months baseline)
     with HTML5/JS zero-flicker client-side blink engine + Difference Imaging (Epoch 2 - Epoch 1)
3. Aperture Photometry & Pixel-Level Analysis:
   - Region of Interest (ROI) selection with circular target aperture and sky background annulus
   - Pixel-by-pixel matrix inspection, radial surface brightness profile, net calibrated flux (uJy),
     AB magnitude (m_AB), delta-magnitude, SNR, and 102-band SPHEREx SED preview
4. Doppler Audio Sonification & Telemetry Logbook:
   - Converts pixel scans, multi-epoch flux changes, and 102-band spectra into playable WAV audio
   - Generates relativistic/classical Doppler-shift waveforms from radial velocity (v_r) & redshift (z)
   - Persistent Telemetry Logbook to record, filter, and export (CSV/JSON) citizen-science scans

Run Instructions:
-----------------
    pip install streamlit numpy pandas matplotlib scipy pillow astropy requests
    streamlit run exomapper_app.py
"""

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

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage

import streamlit as st
import streamlit.components.v1 as components

# Optional Astropy FITS/WCS support (graceful fallback if not installed)
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
    # SPHEREx 6 LVF segments: (start_um, end_um, n_channels, resolving_power)
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
            # Tag notable infrared astrophysics features
            if 0.80 <= lam <= 0.95:
                feat = "Stellar Continuum / TiO & Redshift BAO Tracer"
            elif 1.05 <= lam <= 1.35:
                feat = "Paschen-Beta / Near-IR Galaxy Continuum"
            elif 1.50 <= lam <= 1.75:
                feat = "H-Band Stellar Photosphere (1.6 um H- Opacity Minimum)"
            elif 2.00 <= lam <= 2.35:
                feat = "K-Band CO Rvibrational Bandhead / High-z Galaxy Tracer"
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
        crval_ra: float = 270.0000,   # Reference RA in degrees (e.g. North Ecliptic / Deep Field)
        crval_dec: float = 66.5607,   # Reference Dec in degrees
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
        self.cdelt = pixel_scale_arcsec / 3600.0  # deg/pixel
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
    h_c_k = 14387.77  # um * K
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
    Includes static stars, an extended spiral/elliptical galaxy, zodiacal infrared background,
    and three benchmark anomalies:
      1. High-Proper-Motion Brown Dwarf (shifts position across the 6-month baseline)
      2. Variable AGB / Young Stellar Object (changes brightness across epochs)
      3. Extragalactic Infrared Transient / Supernova (appears in Epoch 2)
    """
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:image_size, 0:image_size]

    # Smooth zodiacal light + diffuse galactic cirrus gradient
    zodi_bg = (
        45.0
        + 8.0 * np.sin(xx / (image_size * 0.35))
        + 6.0 * np.cos(yy / (image_size * 0.42))
    ) * (1.0 + 0.15 * (wavelength_um - 1.5))

    img1 = zodi_bg.copy()
    img2 = zodi_bg.copy()

    # Wavelength-dependent PSF FWHM (diffraction limit scales with wavelength)
    psf_sigma = 1.25 + 0.18 * (wavelength_um / 2.5)

    catalog: List[SimulatedObject] = []

    # 1. Static Field Stars (35 stars across field)
    n_stars = 35
    for i in range(n_stars):
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

        if i < 5:  # Keep top reference stars in catalog
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

    # Add realistic detector readout + Poisson sky noise
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

    data = np.nan_to_num(data, nan=np.nanmedian(data))
    # Resample to common target_size grid if dimensions differ
    if data.shape != (target_size, target_size):
        zoom_y = target_size / data.shape[0]
        zoom_x = target_size / data.shape[1]
        data = ndimage.zoom(data, (zoom_y, zoom_x), order=1)
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
        "subsetsize": str(max(0.02, min(1.0, size_deg * 60.0))),  # arcmin
        "survey": survey,
    }
    return f"https://irsa.ipac.caltech.edu/applications/finderchart/servlet/api?{urllib.parse.urlencode(params)}"


# =====================================================================
# 3. ASTRONOMICAL IMAGE SCALING & ANOMALY DETECTION
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
        # Robust IRAF-inspired median +/- sigma clipping
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
    else:  # Linear or post-ZScale linear
        scaled = clipped

    return np.clip(scaled, 0.0, 1.0)


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
    local_max = ndimage.maximum_filter(abs_snr, size=7)
    peaks = (abs_snr == local_max) & (abs_snr >= sigma_threshold)

    # Exclude 5-pixel border
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
    zero_point_mag: float = 23.90,  # Standard AB magnitude zero point for uJy (m_AB = -2.5 log10(F_uJy) + 23.9)
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
        # Sigma-clipped sky background estimate
        med_sky = float(np.median(ann_pixels))
        mad_sky = float(np.median(np.abs(ann_pixels - med_sky)))
        std_sky = 1.4826 * mad_sky if mad_sky > 0 else float(np.std(ann_pixels))
    else:
        med_sky = float(np.median(img))
        std_sky = float(np.std(img))

    total_sky = med_sky * n_ap
    net_flux = max(1e-3, raw_sum - total_sky)

    # CCD / Infrared detector noise equation (source shot noise + sky background + annulus uncertainty)
    gain = 2.5  # e-/uJy effective conversion
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
    - Relativistic Doppler equation: f_obs = f_0 * sqrt((1 - beta) / (1 + beta)),
      where beta = v_r / c (positive v_r = recession/redshift -> lower pitch;
      negative v_r = approach/blueshift -> higher pitch).
    """
    c_kms = 299792.458
    # Amplify radial velocity perceptual scaling option for subtle galactic velocities while keeping exact physics telemetry
    beta_true = np.clip(radial_velocity_kms / c_kms, -0.85, 0.85)
    # Perceptually enhanced acoustic scaling (100x acoustic magnification when |v_r| < 2000 km/s so human ear hears clear pitch shift)
    beta_acoustic = np.clip((radial_velocity_kms * 60.0) / c_kms, -0.65, 0.65)

    doppler_factor_true = math.sqrt((1.0 - beta_true) / (1.0 + beta_true))
    doppler_factor_audio = math.sqrt((1.0 - beta_acoustic) / (1.0 + beta_acoustic))

    freq_rest = base_freq_hz
    freq_shifted = base_freq_hz * doppler_factor_audio
    redshift_z = math.sqrt((1.0 + beta_true) / (1.0 - beta_true)) - 1.0

    n_samples = int(duration_sec * sample_rate)
    t = np.linspace(0.0, duration_sec, n_samples, endpoint=False)

    # Normalize flux profiles onto [0.1, 1.0]
    p1 = np.asarray(flux_profile_ep1, dtype=np.float64).ravel()
    p2 = np.asarray(flux_profile_ep2, dtype=np.float64).ravel()
    p1_norm = (p1 - np.min(p1)) / max(1e-6, np.max(p1) - np.min(p1))
    p2_norm = (p2 - np.min(p2)) / max(1e-6, np.max(p2) - np.min(p2))

    # Interpolate profiles across time vector t
    x_idx = np.linspace(0.0, duration_sec, len(p1_norm))
    env1 = np.interp(t, x_idx, p1_norm)
    env2 = np.interp(t, x_idx, p2_norm)

    if mode == "Doppler Shift & Multi-Epoch Dual-Tone":
        # First half plays Epoch 1 rest reference modulated by Epoch 1 scan;
        # Second half plays Doppler-shifted carrier modulated by Epoch 2 scan
        split = n_samples // 2
        inst_freq = np.empty(n_samples)
        inst_freq[:split] = freq_rest * (1.0 + 0.25 * env1[:split])
        inst_freq[split:] = freq_shifted * (1.0 + 0.35 * env2[split:])
        amp_env = np.concatenate([0.3 + 0.7 * env1[:split], 0.3 + 0.7 * env2[split:]])
    elif mode == "1D Pixel Brightness Frequency Sweep (FM)":
        # Frequency sweeps linearly with flux difference between Epoch 2 and Epoch 1
        diff_env = env2 - env1
        inst_freq = freq_shifted + 260.0 * diff_env
        amp_env = 0.25 + 0.75 * np.maximum(env1, env2)
    else:  # Spectral / Harmonic Chord Sonification
        inst_freq = freq_shifted * (1.0 + 0.45 * env2)
        amp_env = 0.2 + 0.8 * env2

    phase = 2.0 * np.pi * np.cumsum(inst_freq) / sample_rate
    # Fundamental + 2nd & 3rd astronomical harmonics
    waveform_shifted = amp_env * (
        0.70 * np.sin(phase)
        + 0.20 * np.sin(2.0 * phase)
        + 0.10 * np.sin(3.0 * phase)
    )
    waveform_rest = (0.3 + 0.7 * env1) * np.sin(2.0 * np.pi * freq_rest * t)

    # Apply smooth fade-in / fade-out envelope to prevent clicks
    fade_len = min(int(0.05 * sample_rate), n_samples // 10)
    fade_window = np.ones(n_samples)
    fade_window[:fade_len] = np.linspace(0.0, 1.0, fade_len)
    fade_window[-fade_len:] = np.linspace(1.0, 0.0, fade_len)
    waveform_shifted *= fade_window

    # Normalize to 16-bit signed PCM
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
# 6. CLIENT-SIDE ZERO-FLICKER BLINK COMPARATOR COMPONENT
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
    """Renders an astronomical sky frame with WCS axes, aperture overlays, and anomaly markers to Base64 PNG."""
    fig, ax = plt.subplots(figsize=(5.6, 5.6), dpi=130)
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")

    h, w = img.shape
    im = ax.imshow(img, origin="lower", cmap=cmap, vmin=0.0, vmax=1.0, interpolation="nearest")

    # WCS Grid Overlay
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
        ax.set_xlabel("Right Ascension (J2000)", color="#94a3b8", fontsize=9)
        ax.set_ylabel("Declination (J2000)", color="#94a3b8", fontsize=9)
    else:
        ax.tick_params(colors="#cbd5e1", labelsize=8)
        ax.set_xlabel("Detector Pixel X", color="#94a3b8", fontsize=9)
        ax.set_ylabel("Detector Pixel Y", color="#94a3b8", fontsize=9)

    # Target Aperture & Background Annulus Overlays
    ap_circle = mpatches.Circle((roi_x, roi_y), r_ap, fill=False, edgecolor="#22d3ee", linewidth=1.6, label="Aperture")
    in_circle = mpatches.Circle((roi_x, roi_y), r_in, fill=False, edgecolor="#facc15", linewidth=1.0, linestyle="--")
    out_circle = mpatches.Circle((roi_x, roi_y), r_out, fill=False, edgecolor="#facc15", linewidth=1.0, linestyle=":")
    ax.add_patch(ap_circle)
    ax.add_patch(in_circle)
    ax.add_patch(out_circle)
    ax.plot(roi_x, roi_y, marker="+", color="#22d3ee", markersize=8, markeredgewidth=1.4)

    # Optional candidate anomaly markers
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
    cbar.set_label("Scaled Surface Brightness", color="#94a3b8", fontsize=8)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def render_html_blink_comparator(
    b64_ep1: str,
    b64_ep2: str,
    blink_interval_ms: int = 650,
    auto_play: bool = True,
) -> None:
    """
    Renders an interactive, zero-flicker HTML5/JS automated Blink Comparator widget
    allowing users to toggle seamlessly between Epoch 1 and Epoch 2 (~6 months apart),
    adjust blink cadence, or step manually.
    """
    html_code = f"""
    <div style="background:#0f172a; border:1px solid #1e293b; border-radius:12px; padding:14px; text-align:center; font-family:sans-serif; color:#f8fafc;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
            <div>
                <span style="font-size:13px; color:#94a3b8; font-weight:600;">ACTIVE BLINK FRAME:</span>
                <span id="epochBadge" style="background:#0284c7; color:#fff; padding:4px 10px; border-radius:6px; font-size:13px; font-weight:700; margin-left:6px;">
                    EPOCH 1 (2026-03-15)
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
                    Hold Epoch 2 (+6 mo)
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
                badge.innerText = "EPOCH 1 (Baseline: 2026-03-15)";
                badge.style.background = "#0284c7";
            }} else {{
                imgEl.src = img2;
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
# 7. TELEMETRY LOGBOOK INITIALIZATION
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
                "Observer Notes": "Baseline calibration scan: high proper motion dipole verified across 6-month baseline.",
            }
        ]


# =====================================================================
# 8. MAIN STREAMLIT APPLICATION UI
# =====================================================================

def main() -> None:
    st.set_page_config(
        page_title="ExoMapper | NASA Space Apps Infrared Exploration Suite",
        page_icon="🔭",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()

    # Custom dark-sky observatory styling
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

    # Initialize WCS
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
        f"Active Pipeline: **{data_source}** | Epoch 1 (`2026-03-15`) vs Epoch 2 (`2026-09-15`, Δt = 6.0 months) | "
        f"SPHEREx Band #{current_band.band_index} (`{current_band.wavelength_um:.3f} μm`)"
    )

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
                    # Blend uploaded background with synthetic multi-epoch transient deltas
                    img_epoch1 = base_arr + (sim_img1 - np.median(sim_img1)) * 0.5
                    img_epoch2 = base_arr + (sim_img2 - np.median(sim_img1)) * 0.5
                    st.success("Injected calibrated synthetic moving objects & transients into uploaded sky cutout.")
                except Exception as exc:
                    st.error(f"Could not parse baseline image: {exc}")

    # Scale images for visualization
    scaled_ep1 = scale_astronomical_image(img_epoch1, method=scaling_method)
    scaled_ep2 = scale_astronomical_image(img_epoch2, method=scaling_method)
    anomalies_df = detect_multi_epoch_anomalies(img_epoch1, img_epoch2, sigma_threshold=4.5)

    # -----------------------------------------------------------------
    # TOP HEADER & TELEMETRY OVERVIEW
    # -----------------------------------------------------------------
    st.title("🛰️ ExoMapper: Multi-Epoch Infrared Sky Explorer")
    st.markdown(ingestion_banner)

    # Quick Target Preset Selector Bar
    col_preset, col_x, col_y, col_ap = st.columns([2.4, 1.1, 1.1, 1.4])
    with col_preset:
        preset_options = {
            f"{obj.obj_id} — {obj.obj_type} (E1: {obj.x_epoch1:.1f}, {obj.y_epoch1:.1f})": obj
            for obj in sim_catalog
        }
        chosen_label = st.selectbox(
            "Quick-Lock ROI onto Catalog / Anomaly Target",
            options=list(preset_options.keys()),
            index=6,  # Default to ANOM-MOV-01 (Brown Dwarf Moving Object)
        )
        chosen_obj = preset_options[chosen_label]
        if chosen_obj.obj_id != st.session_state.selected_target_id:
            st.session_state.selected_target_id = chosen_obj.obj_id
            # For Epoch 2 transients, lock onto Epoch 2 position; otherwise Epoch 1 position
            st.session_state.roi_x = float(chosen_obj.x_epoch1)
            st.session_state.roi_y = float(chosen_obj.y_epoch1)

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

    # Compute real-time photometry at selected ROI for both epochs
    phot_ep1 = perform_aperture_photometry(img_epoch1, roi_x, roi_y, r_ap, r_in, r_out, wcs, "Epoch 1 (2026-03-15)")
    phot_ep2 = perform_aperture_photometry(img_epoch2, roi_x, roi_y, r_ap, r_in, r_out, wcs, "Epoch 2 (2026-09-15)")
    ra_str, dec_str = wcs.format_sexagesimal(phot_ep1.ra_deg, phot_ep1.dec_deg)
    delta_mag = phot_ep2.ab_magnitude - phot_ep1.ab_magnitude

    # Top KPI Metrics Row
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
    # MAIN WORKSPACE TABS
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
        st.subheader("Automated 2-Epoch Blink Comparator & Residual Anomaly Detector")
        st.caption(
            "Switches rapidly between Epoch 1 (2026-03-15) and Epoch 2 (2026-09-15, ~6 months apart) so proper-motion "
            "shifts and brightness transients stand out clearly. Cyan circles mark your active photometry aperture; "
            "red circles highlight automated ≥4.5σ difference residuals."
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
                f"Epoch 1 (2026-03-15) | {current_band.wavelength_um:.2f} μm ({scaling_method})",
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
                f"Epoch 2 (2026-09-15, +6 mo) | {current_band.wavelength_um:.2f} μm ({scaling_method})",
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
            vmax_diff = float(np.percentile(np.abs(diff_map), 99.6))

            fig_diff, ax_diff = plt.subplots(figsize=(5.2, 4.5), dpi=120)
            fig_diff.patch.set_facecolor("#0b0f19")
            ax_diff.set_facecolor("#0b0f19")
            im_d = ax_diff.imshow(
                diff_map,
                origin="lower",
                cmap="coolwarm",
                vmin=-vmax_diff,
                vmax=vmax_diff,
                interpolation="nearest",
            )
            ax_diff.plot(roi_x, roi_y, marker="+", color="#22d3ee", markersize=10, markeredgewidth=1.8)
            ax_diff.add_patch(mpatches.Circle((roi_x, roi_y), r_ap, fill=False, edgecolor="#22d3ee", linewidth=1.4))
            ax_diff.set_title("Subtraction Residual Map (Red = +Epoch 2, Blue = +Epoch 1)", color="#f8fafc", fontsize=9.5)
            ax_diff.tick_params(colors="#cbd5e1", labelsize=8)
            cbar_d = fig_diff.colorbar(im_d, ax=ax_diff, fraction=0.046, pad=0.04)
            cbar_d.ax.tick_params(colors="#94a3b8", labelsize=7)
            cbar_d.set_label("Δ Flux (μJy/px)", color="#94a3b8", fontsize=8)
            fig_diff.tight_layout()
            st.pyplot(fig_diff)
            plt.close(fig_diff)

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
        st.subheader("Aperture Photometry, Pixel-by-Pixel Matrix & 102-Band SPHEREx Spectrophotometry")

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

            # Zoomed ROI Cutout & Pixel-Level Heatmap
            st.markdown("#### Zoomed ROI Cutout & Pixel-Level Flux Inspector (15×15 px)")
            ix, iy = int(round(roi_x)), int(round(roi_y))
            half_w = 7
            y0, y1 = max(0, iy - half_w), min(img_size, iy + half_w + 1)
            x0, x1 = max(0, ix - half_w), min(img_size, ix + half_w + 1)
            cut1 = img_epoch1[y0:y1, x0:x1]
            cut2 = img_epoch2[y0:y1, x0:x1]

            fig_cut, (ax_c1, ax_c2) = plt.subplots(1, 2, figsize=(6.2, 3.0), dpi=115)
            fig_cut.patch.set_facecolor("#0b0f19")
            for ax_c, cut_arr, lbl in [(ax_c1, cut1, "Epoch 1 ROI Pixels"), (ax_c2, cut2, "Epoch 2 ROI Pixels")]:
                ax_c.set_facecolor("#0b0f19")
                ax_c.imshow(cut_arr, origin="lower", cmap=cmap_choice, extent=[x0 - 0.5, x1 - 0.5, y0 - 0.5, y1 - 0.5])
                ax_c.add_patch(mpatches.Circle((roi_x, roi_y), r_ap, fill=False, edgecolor="#22d3ee", linewidth=1.5))
                ax_c.set_title(lbl, color="#f8fafc", fontsize=9)
                ax_c.tick_params(colors="#cbd5e1", labelsize=7)
            fig_cut.tight_layout()
            st.pyplot(fig_cut)
            plt.close(fig_cut)

        with p_col2:
            # Radial Surface Brightness Profile
            st.markdown("#### Radial Surface Brightness Profile $I(r)$")
            prof1 = compute_radial_profile(img_epoch1, roi_x, roi_y, max_r=14)
            prof2 = compute_radial_profile(img_epoch2, roi_x, roi_y, max_r=14)

            fig_rad, ax_rad = plt.subplots(figsize=(6.0, 2.8), dpi=115)
            fig_rad.patch.set_facecolor("#0b0f19")
            ax_rad.set_facecolor("#0b0f19")
            ax_rad.plot(prof1["Radius (px)"], prof1["Mean Intensity (uJy/px)"], "-o", color="#38bdf8", markersize=4, label="Epoch 1")
            ax_rad.plot(prof2["Radius (px)"], prof2["Mean Intensity (uJy/px)"], "-s", color="#f43f5e", markersize=4, label="Epoch 2 (+6 mo)")
            ax_rad.axvline(r_ap, color="#22d3ee", linestyle="--", linewidth=1.1, label=f"Aperture r_ap={r_ap}px")
            ax_rad.axvspan(r_in, r_out, color="#facc15", alpha=0.15, label="Sky Annulus")
            ax_rad.set_xlabel("Radial Distance from ROI Center (pixels)", color="#cbd5e1", fontsize=8.5)
            ax_rad.set_ylabel("Mean Flux (μJy/px)", color="#cbd5e1", fontsize=8.5)
            ax_rad.tick_params(colors="#cbd5e1", labelsize=8)
            ax_rad.grid(color="#1e293b", linestyle="--", linewidth=0.6)
            ax_rad.legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=7.5)
            fig_rad.tight_layout()
            st.pyplot(fig_rad)
            plt.close(fig_rad)

            # SPHEREx 102-Band Spectral Energy Distribution (SED) for Target
            st.markdown("#### 102-Band SPHEREx Spectral Energy Distribution ($0.75\\text{--}5.00\\ \\mu\\text{m}$)")
            lam_vec = np.array([b.wavelength_um for b in bands_catalog])
            # Reconstruct spectral shape based on selected target temperature + H2O / CO2 ice absorption troughs
            t_eff = chosen_obj.temperature_k
            bb_curve = np.array([blackbody_sed_factor(l, t_eff) for l in lam_vec])
            ice_absorption = 1.0 - 0.28 * np.exp(-((lam_vec - 3.05) / 0.12) ** 2) - 0.22 * np.exp(-((lam_vec - 4.27) / 0.08) ** 2)
            sed_flux_ep1 = phot_ep1.net_flux_ujy * (bb_curve / max(1e-6, blackbody_sed_factor(current_band.wavelength_um, t_eff))) * ice_absorption
            sed_flux_ep2 = phot_ep2.net_flux_ujy * (bb_curve / max(1e-6, blackbody_sed_factor(current_band.wavelength_um, t_eff))) * ice_absorption

            fig_sed, ax_sed = plt.subplots(figsize=(6.0, 2.9), dpi=115)
            fig_sed.patch.set_facecolor("#0b0f19")
            ax_sed.set_facecolor("#0b0f19")
            ax_sed.plot(lam_vec, sed_flux_ep1, color="#38bdf8", linewidth=1.5, label="Epoch 1 102-Band SED")
            ax_sed.plot(lam_vec, sed_flux_ep2, color="#f43f5e", linewidth=1.5, linestyle="--", label="Epoch 2 102-Band SED")
            ax_sed.axvline(current_band.wavelength_um, color="#facc15", linestyle=":", linewidth=1.4, label=f"Active Band #{current_band.band_index} ({current_band.wavelength_um:.2f} μm)")
            ax_sed.set_xlabel("Wavelength λ (μm) [SPHEREx 102 Channels]", color="#cbd5e1", fontsize=8.5)
            ax_sed.set_ylabel("Aperture Flux Density (μJy)", color="#cbd5e1", fontsize=8.5)
            ax_sed.tick_params(colors="#cbd5e1", labelsize=8)
            ax_sed.grid(color="#1e293b", linestyle="--", linewidth=0.6)
            ax_sed.legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=7.5)
            fig_sed.tight_layout()
            st.pyplot(fig_sed)
            plt.close(fig_sed)

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
        st.subheader("Doppler Audio Sonification & Waveform Generator")
        st.caption(
            "Converts astronomical brightness profiles and multi-epoch changes into audible frequencies and "
            "synthesizes Doppler-shift waveforms from target radial velocity ($v_r$)."
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

            # Extract 1D horizontal pixel scan through (roi_x, roi_y)
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
            # Plot Doppler-shift waveform comparison (zoomed 35 ms window) and full scan envelope
            fig_wav, (ax_w1, ax_w2) = plt.subplots(2, 1, figsize=(6.8, 4.8), dpi=120)
            fig_wav.patch.set_facecolor("#0b0f19")

            # Top panel: Rest vs Doppler-shifted carrier phase waveform (first 25 ms)
            n_zoom = int(0.025 * 44100)
            ax_w1.set_facecolor("#0b0f19")
            ax_w1.plot(t_vec[:n_zoom] * 1000.0, wave_rest[:n_zoom], color="#94a3b8", linestyle="--", linewidth=1.2, label=f"Rest Frame ({doppler_meta['rest_freq_hz']:.0f} Hz)")
            ax_w1.plot(t_vec[:n_zoom] * 1000.0, wave_shift[:n_zoom], color="#38bdf8", linewidth=1.5, label=f"Doppler Shifted ({doppler_meta['shifted_freq_hz']:.1f} Hz, v_r={rv_input_kms:+.0f} km/s)")
            ax_w1.set_title("Relativistic Doppler-Shift Waveform Comparison (25 ms Acoustic Window)", color="#f8fafc", fontsize=9.5)
            ax_w1.set_xlabel("Time (ms)", color="#cbd5e1", fontsize=8)
            ax_w1.set_ylabel("Normalized Amplitude", color="#cbd5e1", fontsize=8)
            ax_w1.tick_params(colors="#cbd5e1", labelsize=7.5)
            ax_w1.grid(color="#1e293b", linestyle="--", linewidth=0.5)
            ax_w1.legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=7.5, loc="upper right")

            # Bottom panel: Full multi-epoch scan intensity envelope
            ax_w2.set_facecolor("#0b0f19")
            px_axis = np.arange(img_size)
            ax_w2.plot(px_axis, scan_ep1, color="#38bdf8", linewidth=1.4, label="Epoch 1 Intensity Scan (Left Half)")
            ax_w2.plot(px_axis, scan_ep2, color="#f43f5e", linewidth=1.4, label="Epoch 2 Intensity Scan (Right Half)")
            ax_w2.axvline(roi_x, color="#facc15", linestyle=":", linewidth=1.3, label=f"Selected Target X={roi_x:.1f}")
            ax_w2.set_title(f"1D Detector Slice Across Y = {row_idx} Driving Audio Modulation", color="#f8fafc", fontsize=9.5)
            ax_w2.set_xlabel("Detector Pixel X", color="#cbd5e1", fontsize=8)
            ax_w2.set_ylabel("Flux (μJy/px)", color="#cbd5e1", fontsize=8)
            ax_w2.tick_params(colors="#cbd5e1", labelsize=7.5)
            ax_w2.grid(color="#1e293b", linestyle="--", linewidth=0.5)
            ax_w2.legend(facecolor="#0f172a", edgecolor="#334155", labelcolor="#f8fafc", fontsize=7.5, loc="upper right")

            fig_wav.tight_layout()
            st.pyplot(fig_wav)
            plt.close(fig_wav)

    # =================================================================
    # TAB 4: OBSERVATION TELEMETRY LOGBOOK
    # =================================================================
    with tab_log:
        st.subheader("Observation & Telemetry Logbook")
        st.caption(
            "Record multi-epoch scans, photometric measurements, and Doppler sonification telemetry into a structured "
            "scientific logbook ready for export and citizen-science collaboration."
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
                st.success(f"Logged observation for `{entry_id}` at WCS `{ra_str}, {dec_str}`.")

        log_df = pd.DataFrame(st.session_state.telemetry_log)
        st.dataframe(log_df, use_container_width=True, hide_index=True)

        exp_c1, exp_c2, exp_c3 = st.columns([1.0, 1.0, 2.0])
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
        st.subheader("Caltech/IPAC IRSA Archive Cutout Builder & NASA Challenge Dataset Pipeline")
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


if __name__ == "__main__":
    main()

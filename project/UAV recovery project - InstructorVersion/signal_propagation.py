import numpy as np
from geopy.distance import geodesic
import rasterio

def get_elevation(lat, lon, dem_path):
    """Return elevation in meters for a given lat/lon using rasterio."""
    with rasterio.open(dem_path) as src:
        for val in src.sample([(lon, lat)]):
            return float(val[0])

def line_of_sight_blockage(tx_lat, tx_lon, tx_elev, rx_lat, rx_lon, rx_elev, dem_path, num=100):
    """
    Determine if line of sight exists and compute total blockage (meters) between two points using DEM data.
    Returns (los_clear: bool, blockage_m: float)
    """
    lats = np.linspace(tx_lat, rx_lat, num)
    lons = np.linspace(tx_lon, rx_lon, num)
    elevs = np.linspace(tx_elev, rx_elev, num)
    with rasterio.open(dem_path) as src:
        terrain_elevs = np.array([float(val[0]) for val in src.sample(zip(lons, lats))])
    blockage = np.max(np.maximum(terrain_elevs - elevs, 0))
    los_clear = blockage == 0
    return los_clear, blockage

def compute_rss(tx_lat, tx_lon, tx_elev, rx_lat, rx_lon, rx_elev, dem_path, base_strength=0, k=5, noise_floor=-120):
    """
    Compute received signal strength (dBm) from transmitter to receiver, including LOS blockage penalty.
    Returns (signal_strength, blockage_m, snr)
    """
    distance = geodesic((tx_lat, tx_lon), (rx_lat, rx_lon)).meters
    los_clear, blockage_m = line_of_sight_blockage(tx_lat, tx_lon, tx_elev, rx_lat, rx_lon, rx_elev, dem_path)
    Path_Loss = 20 * np.log10(distance)
    LOS_Penalty = 0 if los_clear else -k * blockage_m
    Noise = np.random.normal(0, 2)
    signal_strength = base_strength - Path_Loss + LOS_Penalty + Noise
    snr = signal_strength - noise_floor
    if snr < 0:
        signal_strength = np.nan
    return signal_strength, blockage_m, snr

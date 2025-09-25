"""
Script: generate_historical_data.py
Purpose: Generate a clean historical_mission_data.csv for a previous successful UAV beacon search mission in the Sierra National Forest, CA.
"""

import numpy as np
import pandas as pd
import py3dep
import rioxarray
import random
import os
from signal_propagation import get_elevation, compute_rss

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Define bounding box for Sierra National Forest
LAT_MIN, LAT_MAX = 37.1, 37.6
LON_MIN, LON_MAX = -119.4, -118.8

# Define a fixed historical beacon location within the bounding box
beacon_lat = 37.35
beacon_lon = -119.1


# Download DEM data for the bounding box using py3dep (if not already present)
DATA_DIR = 'data'
dem_file = os.path.join(DATA_DIR, 'sierra_dem.tif')
os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(dem_file):
    print('Downloading DEM data with py3dep...')
    dem = py3dep.get_dem(
        (LON_MIN, LAT_MIN, LON_MAX, LAT_MAX),
        resolution=30,
        crs="EPSG:4326"
    )
    # Save as GeoTIFF using rioxarray
    dem.rio.to_raster(dem_file)



from geopy.distance import geodesic
# Generate 400 random team locations within the bounding box, enforcing distance constraints
num_points = 400
# min_dist_to_beacon_m = 1609.34  # 1 mile in meters
# min_dist_between_teams_m = 2011.68  # 1.25 miles in meters

min_dist_to_beacon_m = 800  # 0.5 miles in meters
min_dist_between_teams_m = 500  # 0.31 miles in meters


team_coords = []
team_callsigns = []
attempts = 0
max_attempts = 10000
while len(team_coords) < num_points and attempts < max_attempts:
    lat = np.random.uniform(LAT_MIN, LAT_MAX)
    lon = np.random.uniform(LON_MIN, LON_MAX)
    # Check distance to beacon
    dist_to_beacon = geodesic((lat, lon), (beacon_lat, beacon_lon)).meters
    if dist_to_beacon < min_dist_to_beacon_m:
        attempts += 1
        continue
    # Check distance to all other teams
    too_close = False
    for (other_lat, other_lon) in team_coords:
        if geodesic((lat, lon), (other_lat, other_lon)).meters < min_dist_between_teams_m:
            too_close = True
            break
    if too_close:
        attempts += 1
        continue
    team_coords.append((lat, lon))
    team_callsigns.append(f"TEAM{str(len(team_coords)).zfill(3)}")
    attempts += 1
if len(team_coords) < num_points:
    raise RuntimeError(f"Could not place {num_points} teams with the given constraints after {max_attempts} attempts.")


# Prepare data storage
records = []

for i, ((team_lat, team_lon), team_call_sign) in enumerate(zip(team_coords, team_callsigns)):
    # Get elevation for team and beacon
    # Assume teams are UAVs flying at 120m (approx. 400ft) Above Ground Level (AGL)
    team_elev = get_elevation(team_lat, team_lon, dem_file) + 120
    # Enforce operational ceiling of 4000m due to air density
    team_elev = min(team_elev, 4000)
    beacon_elev = get_elevation(beacon_lat, beacon_lon, dem_file)
    # Compute received signal strength and blockage
    signal_strength, blockage_m, snr = compute_rss(
        beacon_lat, beacon_lon, beacon_elev,
        team_lat, team_lon, team_elev,
        dem_file,
        base_strength=-30, k=0.2, noise_floor=-120
    )
    # # Store record
    # records.append({
    #     'report_id': i+1,
    #     'team_callsign': team_call_sign,
    #     'team_lat': team_lat,
    #     'team_lon': team_lon,
    #     'beacon_lat': beacon_lat,
    #     'beacon_lon': beacon_lon,
    #     'signal_strength': signal_strength,
    #     'blockage_m': blockage_m
    # })
    # Store record
    records.append({
        'report_id': i+1,
        'team_callsign': team_call_sign,
        'team_lat': team_lat,
        'team_lon': team_lon,
        'beacon_lat': beacon_lat,
        'beacon_lon': beacon_lon,
        'signal_strength': signal_strength
    })
# Create DataFrame and save to CSV
df = pd.DataFrame(records)
output_path = os.path.join(DATA_DIR, 'historical_mission_data.csv')
df.to_csv(output_path, index=False)
print(f"'{output_path}' generated successfully.")

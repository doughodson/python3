"""
Script: generate_field_reports_batch_2.py
Purpose: Generate a second, more focused batch of simulated field reports
         (field_reports_batch_2.csv) for a UAV beacon search mission.
"""

import numpy as np
import pandas as pd
import rasterio
from geopy.distance import geodesic
import random
import datetime
from signal_propagation import get_elevation, compute_rss
import os

# Set random seed for reproducibility
np.random.seed(202)
random.seed(202)

# Define the "true" beacon location (same as batch 1)
beacon_lat = 37.42
beacon_lon = -119.05

# Define a tighter bounding box around the beacon for a focused search
LAT_SPREAD = 0.1
LON_SPREAD = 0.15
LAT_MIN, LAT_MAX = beacon_lat - LAT_SPREAD, beacon_lat + LAT_SPREAD
LON_MIN, LON_MAX = beacon_lon - LON_SPREAD, beacon_lon + LON_SPREAD

# Define data directory and DEM file path
DATA_DIR = 'data'
dem_file = os.path.join(DATA_DIR, 'sierra_dem.tif')

# Generate 200 random team locations within the focused bounding box
num_points = 200
min_dist_to_beacon_m = 400  # 400 meters
min_dist_between_teams_m = 500  # Reduced distance for a denser search pattern

team_coords = []
team_callsigns = []
attempts = 0
max_attempts = 20000  # Increased attempts for denser packing
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
    # Use a different naming scheme for batch 2 teams for clarity
    team_callsigns.append(f"GRID{str(len(team_coords)).zfill(3)}")
    attempts += 1
if len(team_coords) < num_points:
    raise RuntimeError(f"Could not place {num_points} teams with the given constraints after {max_attempts} attempts.")

# Prepare data storage
records = []

# Generate plausible, sequential timestamps for the second day of the mission
start_time = datetime.datetime(2025, 8, 22, 6, 0, 0)  # Mission day 2 starts at 6 AM
time_increment = datetime.timedelta(minutes=random.randint(1, 5))  # Shorter interval for focused search

for i, ((team_lat, team_lon), team_callsign) in enumerate(zip(team_coords, team_callsigns)):
    # Get elevation for team and beacon
    # Assume teams are UAVs flying at 120m (approx. 400ft) Above Ground Level (AGL)
    team_elev = get_elevation(team_lat, team_lon, dem_file) + 120
    # Enforce operational ceiling of 4000m due to air density
    team_elev = min(team_elev, 4000)
    beacon_elev = get_elevation(beacon_lat, beacon_lon, dem_file)

    # Use the centralized compute_rss function for consistent physics
    # Parameters are the same as batch 1 for consistency
    signal_strength, blockage_m, _ = compute_rss(
        tx_lat=beacon_lat, tx_lon=beacon_lon, tx_elev=beacon_elev,
        rx_lat=team_lat, rx_lon=team_lon, rx_elev=team_elev,
        dem_path=dem_file,
        base_strength=-30, k=0.15, noise_floor=-120
    )

    # Other sensor data (with some realistic variation)
    wind_direction_deg = np.random.uniform(0, 360)
    ambient_temp_c = np.random.normal(25, 5)  # Average 25C, std dev 5C
    battery_level_percent = np.random.uniform(20, 100)  # Ensure it's not critically low

    # Introduce general messiness (no solar storm in this batch)
    current_time = start_time + i * time_increment
    timestamp = current_time.isoformat()

    if random.random() < 0.1:
        team_callsign = random.choice(['Alpha', 'alfa', 'bravo'])  # Typos
    if random.random() < 0.05:
        signal_strength = np.nan
    if random.random() < 0.05:
        wind_direction_deg = random.choice(['?', "N/A", ""])
    if random.random() < 0.05:
        battery_level_percent = np.nan

    # # Store record, continuing report_id from the first batch (starts at 201)
    # records.append({
    #     'report_id': i + 201,
    #     'timestamp': timestamp,
    #     'team_callsign': team_callsign,
    #     'latitude': team_lat,
    #     'longitude': team_lon,
    #     'elevation_m': team_elev,
    #     'wind_direction_deg': wind_direction_deg,
    #     'ambient_temp_c': ambient_temp_c,
    #     'battery_level_percent': battery_level_percent,
    #     'signal_strength': signal_strength,
    #     'blockage_m': blockage_m
    # })

    # Store record, continuing report_id from the first batch (starts at 201)
    records.append({
        'report_id': i + 201,
        'timestamp': timestamp,
        'team_callsign': team_callsign,
        'latitude': team_lat,
        'longitude': team_lon,
        'elevation_m': team_elev,
        'wind_direction_deg': wind_direction_deg,
        'ambient_temp_c': ambient_temp_c,
        'battery_level_percent': battery_level_percent,
        'signal_strength': signal_strength
    })
# Create DataFrame and save to CSV
df = pd.DataFrame(records)
os.makedirs(DATA_DIR, exist_ok=True)
output_path = os.path.join(DATA_DIR, 'field_reports_batch_2.csv')
df.to_csv(output_path, index=False)
print(f"'{output_path}' generated successfully.")
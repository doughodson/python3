import os
import folium
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import base64
from io import BytesIO
from IPython.display import IFrame
from geopy.distance import geodesic

def EDA_makeMap(df, cache_path="map.html", force_regenerate=False):
    """
    Generates an interactive Folium map of data points, with caching.
    This function creates a map with multiple tile layers and markers for each
    data point, colored by signal strength. It includes a caching mechanism:
    1. If a cached map exists at `cache_path` and `force_regenerate` is False,
       it will display the local HTML file in an IFrame, avoiding network requests.
    2. Otherwise, it generates a new map, saves it to `cache_path`, and returns
       the Folium map object for display.
    Args:
        df (pd.DataFrame): DataFrame with 'latitude', 'longitude', 'signal_strength'.
        cache_path (str, optional): The file path to save/load the map.
                                    Defaults to "map.html".
        force_regenerate (bool, optional): If True, a new map is generated
                                           even if a cache exists. Defaults to False.
    Returns:
        folium.Map or IPython.display.IFrame: The map object to be displayed.
    """
    # 1. Check for a cached map and return it if appropriate
    if os.path.exists(cache_path) and not force_regenerate:
        print(f"Displaying cached map from: {cache_path}")
        # Return an IFrame to display the local HTML file, which works offline
        return IFrame(src=cache_path, width='100%', height=600)

    # 2. If no cache or force_regenerate is True, generate a new map
    print(f"Generating new map and caching to: {cache_path}")

    if 'latitude' in df.columns and 'longitude' in df.columns and 'signal_strength' in df.columns:
        # Normalize signal strength for colormap
        signal = df['signal_strength']
        norm = mcolors.Normalize(vmin=signal.min(), vmax=signal.max())
        cmap = plt.get_cmap('plasma')  # Changed from 'viridis' to 'plasma'
        
        # Create map centered on the data, with no default tiles initially
        m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=12, tiles=None, control_scale=True)

        # Add a plugin to show coordinates on click, for student analysis
        folium.LatLngPopup().add_to(m)

        # Add multiple, robust tile layers for flexibility and resilience
        folium.TileLayer(
            tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            attr='&copy; <a href="https://opentopomap.org">OpenTopoMap</a> contributors',
            name='Topographic'
        ).add_to(m)
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='Street Map'
        ).add_to(m)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite'
        ).add_to(m)

        for idx, row in df.iterrows():
            # Get color from colormap for fill
            fill_color = mcolors.to_hex(cmap(norm(row['signal_strength'])))
            popup_text = (
                f"<b>Report ID:</b> {row.get('report_id', 'N/A')}<br>"
                f"<b>Team:</b> {row.get('team_callsign', 'N/A')}<br>"
                f"<b>Signal Strength:</b> {row.get('signal_strength', 'N/A')}<br>"
                f"<b>Timestamp:</b> {row.get('timestamp', 'N/A')}<br>"
                f"<b>Lat:</b> {row['latitude']:.5f}, <b>Lon:</b> {row['longitude']:.5f}"
            )
            folium.CircleMarker(
                location=(row['latitude'], row['longitude']),
                radius=7,
                color='red',  # Red outline
                weight=3,
                fill=True,
                fill_color=fill_color,  # Signal strength color
                fill_opacity=0.85,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"Report {row.get('report_id', 'N/A')}"
            ).add_to(m)

        # Add a colorbar legend as an image overlay
        fig, ax = plt.subplots(figsize=(4, 0.5))
        fig.subplots_adjust(bottom=0.5)
        cb1 = plt.colorbar(
            plt.cm.ScalarMappable(norm=norm, cmap=cmap),
            cax=ax, orientation='horizontal',
            label='Signal Strength'
        )
        ax.set_title('Signal Strength Color Legend', fontsize=10)
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        data = base64.b64encode(buf.getbuffer()).decode('ascii')
        legend_html = f'<img src="data:image/png;base64,{data}" style="width:250px; margin: 10px; border:1px solid #888; background:white;">'
        legend = folium.map.Marker(
            [df['latitude'].max(), df['longitude'].min()],
            icon=folium.DivIcon(html=legend_html)
        )
        m.add_child(legend)

        # Add a layer control to switch between map types
        folium.LayerControl().add_to(m)

        # 3. Save the newly generated map to the cache path
        m.save(cache_path)

        return m
    else:
        print("DataFrame is missing required columns: 'latitude', 'longitude', 'signal_strength'")
        return None

def create_triangulation_map(df, line_length_km=10, cache_path="triangulation_map.html", force_regenerate=False):
    """
    Generates an interactive map with bearing lines for triangulation.
    This function plots each UAV report and draws a line from it along the
    estimated signal direction. The opacity and color of the line are scaled
    by the 'confidence' score of the bearing.
    Args:
        df (pd.DataFrame): DataFrame with 'latitude', 'longitude',
                           'signal_direction_deg', and 'confidence'.
        line_length_km (int, optional): The length of the bearing lines in km.
                                        Defaults to 10.
        cache_path (str, optional): The file path to save/load the map.
                                    Defaults to "triangulation_map.html".
        force_regenerate (bool, optional): If True, a new map is generated
                                           even if a cache exists. Defaults to False.
    Returns:
        folium.Map or IPython.display.IFrame: The map object to be displayed.
    """
    # 1. Caching logic
    if os.path.exists(cache_path) and not force_regenerate:
        print(f"Displaying cached map from: {cache_path}")
        return IFrame(src=cache_path, width='100%', height=600)

    print(f"Generating new triangulation map and caching to: {cache_path}")

    # 2. Check for required columns
    required_cols = ['latitude', 'longitude', 'signal_direction_deg', 'confidence']
    if not all(col in df.columns for col in required_cols):
        print(f"DataFrame is missing one or more required columns: {required_cols}")
        return None

    # 3. Create map centered on the data
    m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=12, tiles=None, control_scale=True)

    # Add a plugin to show coordinates on click, for student analysis
    folium.LatLngPopup().add_to(m)

    # Add tile layers
    folium.TileLayer(tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attr='OpenTopoMap', name='Topographic').add_to(m)
    folium.TileLayer(tiles='OpenStreetMap', name='Street Map').add_to(m)
    folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satellite').add_to(m)

    # 4. Loop and draw markers and bearing lines
    for _, row in df.iterrows():
        start_point = (row['latitude'], row['longitude'])
        
        # Draw the bearing line only if the data is valid
        if pd.notna(row['signal_direction_deg']) and pd.notna(row['confidence']) and row['confidence'] > 0:
            confidence = row['confidence']
            end_point = geodesic(kilometers=line_length_km).destination(start_point, row['signal_direction_deg'])
            
            # Use a single color (red) and vary opacity based on confidence
            line_color = 'red'
            line_opacity = max(0.15, confidence * 0.9) # Ensure even low confidence lines are faintly visible
            line_weight = 1 + (confidence * 2.5) # Make higher confidence lines thicker
            
            folium.PolyLine(
                locations=[start_point, (end_point.latitude, end_point.longitude)],
                color=line_color,
                weight=line_weight,
                opacity=line_opacity,
                tooltip=f"Report {row.get('report_id', 'N/A')}: Confidence {confidence:.0%}"
            ).add_to(m)

    # 5. Add layer control, save, and return
    folium.LayerControl().add_to(m)
    m.save(cache_path)
    return m
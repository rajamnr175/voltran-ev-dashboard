import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

st.set_page_config(page_title="Voltran EV Network Dashboard", layout="wide")

# --- Distance Calculation (Haversine formula in km) ---
def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0 # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * r * asin(sqrt(a))

# --- Sample Data Loading ---
@st.cache_data
def load_data():
    return pd.DataFrame([
        {"name": "Suryapet Charge Hub", "status": "Operational", "lat": 17.1438, "lon": 79.6238, "corridor": "NH65 (Hyd - Vja)"},
        {"name": "Shamshabad Charge Hub", "status": "Operational", "lat": 17.2543, "lon": 78.4312, "corridor": "NH44 / ORR"},
        {"name": "Nizamabad Charge Hub", "status": "Operational", "lat": 18.6725, "lon": 78.0941, "corridor": "NH44 North"},
        {"name": "Aziz Nagar Hub", "status": "Coming Soon", "lat": 17.3481, "lon": 78.2519, "corridor": "NH65 West"},
        {"name": "Tirupati Charge Hub", "status": "Operational", "lat": 13.6288, "lon": 79.4192, "corridor": "NH71 / Rayalaseema"},
        {"name": "Srikakulam Charge Hub", "status": "Operational", "lat": 18.2969, "lon": 83.8968, "corridor": "NH16 North Coast"},
        {"name": "Rajahmundry Charge Hub", "status": "Operational", "lat": 17.0005, "lon": 81.7800, "corridor": "NH16 Mid Coast"},
        {"name": "Ongole Charge Hub", "status": "Operational", "lat": 15.5057, "lon": 80.0499, "corridor": "NH16 South Coast"},
        {"name": "Nellore Charge Hub", "status": "Operational", "lat": 14.4426, "lon": 79.9865, "corridor": "NH16 South Coast"},
        {"name": "Mydukur Charge Hub", "status": "Operational", "lat": 14.7833, "lon": 78.6000, "corridor": "NH40 (Kurnool-Kadapa)"},
        {"name": "Beechupalli Charge Hub", "status": "Operational", "lat": 16.1423, "lon": 77.9256, "corridor": "NH44 South"},
        {"name": "Anantapur Charge Hub", "status": "Operational", "lat": 14.6819, "lon": 77.6006, "corridor": "NH44 South"},
        {"name": "Anakapalle Charge Hub", "status": "Operational", "lat": 17.6913, "lon": 83.0039, "corridor": "NH16 North Coast"},
        {"name": "Amaravati Charge Hub", "status": "Operational", "lat": 16.3520, "lon": 80.5283, "corridor": "Capital Region / NH65"}
    ])

df = load_data()

# --- Calculations ---
def compute_nearest_neighbors(df):
    results = []
    coords = df[['lat', 'lon']].values
    for i, row in df.iterrows():
        distances = []
        for j, target in df.iterrows():
            if i != j:
                dist = haversine(row['lat'], row['lon'], target['lat'], target['lon'])
                distances.append((target['name'], dist))
        distances.sort(key=lambda x: x[1])
        results.append({
            "Station": row['name'],
            "Status": row['status'],
            "Nearest Station": distances[0][0],
            "Distance (km)": round(distances[0][1], 1),
            "Second Nearest": distances[1][0],
            "Distance 2 (km)": round(distances[1][1], 1)
        })
    return pd.DataFrame(results)

def recommend_new_locations(df, min_gap_km=80):
    recommendations = []
    # Identify key gaps between pairs that are distant from each other along primary highway corridors
    op_df = df[df['status'] == 'Operational'].reset_index(drop=True)
    for i in range(len(op_df)):
        for j in range(i + 1, len(op_df)):
            s1 = op_df.iloc[i]
            s2 = op_df.iloc[j]
            dist = haversine(s1['lat'], s1['lon'], s2['lat'], s2['lon'])
            
            # Highlight gaps on the same major transport corridors (e.g. between 80km and 220km)
            if min_gap_km <= dist <= 220 and s1['corridor'] == s2['corridor']:
                mid_lat = (s1['lat'] + s2['lat']) / 2
                mid_lon = (s1['lon'] + s2['lon']) / 2
                recommendations.append({
                    "Corridor": s1['corridor'],
                    "Between Station A": s1['name'],
                    "Between Station B": s2['name'],
                    "Current Gap (km)": round(dist, 1),
                    "Recommended Station Midpoint": f"{round(mid_lat, 4)}, {round(mid_lon, 4)}",
                    "Target Lat": mid_lat,
                    "Target Lon": mid_lon
                })
    return pd.DataFrame(recommendations)

# --- UI Header ---
st.title("⚡ Voltran EV Network Analytics Dashboard")
st.markdown("Track active charge hubs, analyze station-to-station distances, and identify network coverage gaps.")

col1, col2, col3 = st.columns(3)
col1.metric("Total Stations Tracked", len(df))
col2.metric("Operational Hubs", len(df[df['status'] == 'Operational']))
col3.metric("Coming Soon Hubs", len(df[df['status'] == 'Coming Soon']))

# --- Map Rendering ---
st.subheader("📍 Station Map & Network Coverage")

m = folium.Map(location=[16.5, 79.5], zoom_start=7, tiles="OpenStreetMap")

# Render stations
for _, row in df.iterrows():
    color = "green" if row['status'] == "Operational" else "orange"
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=f"<b>{row['name']}</b><br>Status: {row['status']}<br>Corridor: {row['corridor']}",
        tooltip=row['name'],
        icon=folium.Icon(color=color, icon="bolt", prefix="fa")
    ).add_to(m)

# Render proposed gap fill locations
rec_df = recommend_new_locations(df)
for _, rec in rec_df.iterrows():
    folium.Marker(
        location=[rec['Target Lat'], rec['Target Lon']],
        popup=f"<b>PROPOSED LOCATION</b><br>Corridor: {rec['Corridor']}<br>Fills gap between {rec['Between Station A']} & {rec['Between Station B']} ({rec['Current Gap (km)']} km gap)",
        tooltip="⚡ Proposed New Location",
        icon=folium.Icon(color="red", icon="star", prefix="fa")
    ).add_to(m)

st_folium(m, width=1200, height=500)

# --- Analysis Tabs ---
tab1, tab2 = st.tabs(["📏 Nearest Neighbor & Distance Matrix", "🎯 Recommended New Locations"])

with tab1:
    st.subheader("Nearest Station Proximity Analysis")
    nn_df = compute_nearest_neighbors(df)
    st.dataframe(nn_df, use_container_width=True)

with tab2:
    st.subheader("Identified Network Gaps & Installation Candidates")
    st.markdown("Below are suggested midpoint locations along primary transit corridors where inter-station gaps exceed target charging thresholds (80+ km):")
    st.dataframe(rec_df.drop(columns=['Target Lat', 'Target Lon']), use_container_width=True)
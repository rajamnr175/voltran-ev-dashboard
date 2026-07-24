import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

st.set_page_config(page_title="Multi-Provider EV Network Dashboard", layout="wide")

# --- Distance Calculation (Haversine formula in km) ---
def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0 # Earth's radius in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * r * asin(sqrt(a))

# --- Dataset Loading ---
@st.cache_data
def load_data():
    return pd.DataFrame([
        # Voltran Stations
        {"name": "Voltran - Suryapet Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 17.1438, "lon": 79.6238, "corridor": "NH65 (Hyd - Vja)"},
        {"name": "Voltran - Shamshabad Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 17.2543, "lon": 78.4312, "corridor": "NH44 / ORR"},
        {"name": "Voltran - Nizamabad Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 18.6725, "lon": 78.0941, "corridor": "NH44 North"},
        {"name": "Voltran - Aziz Nagar Hub", "provider": "Voltran", "status": "Coming Soon", "lat": 17.3481, "lon": 78.2519, "corridor": "NH65 West"},
        {"name": "Voltran - Tirupati Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 13.6288, "lon": 79.4192, "corridor": "NH71 / Rayalaseema"},
        {"name": "Voltran - Srikakulam Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 18.2969, "lon": 83.8968, "corridor": "NH16 North Coast"},
        {"name": "Voltran - Rajahmundry Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 17.0005, "lon": 81.7800, "corridor": "NH16 Mid Coast"},
        {"name": "Voltran - Ongole Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 15.5057, "lon": 80.0499, "corridor": "NH16 South Coast"},
        {"name": "Voltran - Nellore Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 14.4426, "lon": 79.9865, "corridor": "NH16 South Coast"},
        {"name": "Voltran - Mydukur Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 14.7833, "lon": 78.6000, "corridor": "NH40 (Kurnool-Kadapa)"},
        {"name": "Voltran - Beechupalli Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 16.1423, "lon": 77.9256, "corridor": "NH44 South"},
        {"name": "Voltran - Anantapur Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 14.6819, "lon": 77.6006, "corridor": "NH44 South"},
        {"name": "Voltran - Anakapalle Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 17.6913, "lon": 83.0039, "corridor": "NH16 North Coast"},
        {"name": "Voltran - Amaravati Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 16.3520, "lon": 80.5283, "corridor": "Capital Region / NH65"},

        # Tata Power EZ Charge
        {"name": "Tata Power - Somajiguda Greenlands", "provider": "Tata Power", "status": "Operational", "lat": 17.4328, "lon": 78.4583, "corridor": "Hyderabad Urban"},
        {"name": "Tata Power - LB Nagar", "provider": "Tata Power", "status": "Operational", "lat": 17.3512, "lon": 78.5521, "corridor": "NH65 Exit"},
        {"name": "Tata Power - Banjara Hills", "provider": "Tata Power", "status": "Operational", "lat": 17.4185, "lon": 78.4390, "corridor": "Hyderabad Urban"},
        {"name": "Tata Power - Tadepalle (Vijayawada)", "provider": "Tata Power", "status": "Operational", "lat": 16.4821, "lon": 80.6012, "corridor": "NH16 Mid Coast"},
        {"name": "Tata Power - Visakhapatnam Vempadu", "provider": "Tata Power", "status": "Operational", "lat": 17.5510, "lon": 82.8800, "corridor": "NH16 North Coast"},
        {"name": "Tata Power - Kadapa Apparajupet", "provider": "Tata Power", "status": "Operational", "lat": 14.4715, "lon": 78.8210, "corridor": "NH40 Rayalaseema"},

        # ChargeZone
        {"name": "ChargeZone - RTC X Road (Azamabad)", "provider": "ChargeZone", "status": "Operational", "lat": 17.4045, "lon": 78.4920, "corridor": "Hyderabad Central"},
        {"name": "ChargeZone - Medak Rimmanguda (NH44 Hwy)", "provider": "ChargeZone", "status": "Operational", "lat": 17.8420, "lon": 78.4610, "corridor": "NH44 North"},

        # Jio-bp pulse
        {"name": "Jio-bp pulse - Singarayakonda / Tanguturu", "provider": "Jio-bp pulse", "status": "Operational", "lat": 15.3420, "lon": 80.0210, "corridor": "NH16 South Coast"},

        # GLIDA (Fortum)
        {"name": "GLIDA - Musarambagh Metro Station", "provider": "GLIDA", "status": "Operational", "lat": 17.3710, "lon": 78.5130, "corridor": "Hyderabad East"}
    ])

df = load_data()

# --- Provider Color Mapping ---
PROVIDER_COLORS = {
    "Voltran": "green",
    "Tata Power": "blue",
    "ChargeZone": "purple",
    "Jio-bp pulse": "red",
    "GLIDA": "orange"
}

# --- Sidebar Controls ---
st.sidebar.title("🔍 Filter Network")
st.sidebar.markdown("Toggle networks to visualize charging infrastructure in AP & Telangana.")

selected_providers = st.sidebar.multiselect(
    "Select EV Charging Networks:",
    options=list(PROVIDER_COLORS.keys()),
    default=list(PROVIDER_COLORS.keys())
)

show_recommendations = st.sidebar.checkbox("Show Recommended Gap Fill Locations", value=True)

# Filter DataFrame
filtered_df = df[df['provider'].isin(selected_providers)].reset_index(drop=True)

# --- Calculation Functions ---
def compute_nearest_neighbors(df):
    if len(df) < 2:
        return pd.DataFrame()
    results = []
    for i, row in df.iterrows():
        distances = []
        for j, target in df.iterrows():
            if i != j:
                dist = haversine(row['lat'], row['lon'], target['lat'], target['lon'])
                distances.append((target['name'], target['provider'], dist))
        distances.sort(key=lambda x: x[2])
        results.append({
            "Station": row['name'],
            "Provider": row['provider'],
            "Nearest Station": distances[0][0],
            "Nearest Provider": distances[0][1],
            "Distance (km)": round(distances[0][2], 1)
        })
    return pd.DataFrame(results)

def recommend_new_locations(full_df, min_gap_km=90):
    recommendations = []
    # Analyze coverage gaps along major highways across ALL active stations
    op_df = full_df[full_df['status'] == 'Operational'].reset_index(drop=True)
    for i in range(len(op_df)):
        for j in range(i + 1, len(op_df)):
            s1 = op_df.iloc[i]
            s2 = op_df.iloc[j]
            dist = haversine(s1['lat'], s1['lon'], s2['lat'], s2['lon'])
            
            if min_gap_km <= dist <= 220 and s1['corridor'] == s2['corridor']:
                mid_lat = (s1['lat'] + s2['lat']) / 2
                mid_lon = (s1['lon'] + s2['lon']) / 2
                recommendations.append({
                    "Corridor": s1['corridor'],
                    "Station A": f"{s1['provider']} - {s1['name']}",
                    "Station B": f"{s2['provider']} - {s2['name']}",
                    "Current Gap (km)": round(dist, 1),
                    "Proposed Midpoint Lat/Lon": f"{round(mid_lat, 4)}, {round(mid_lon, 4)}",
                    "Target Lat": mid_lat,
                    "Target Lon": mid_lon
                })
    return pd.DataFrame(recommendations)

# --- Header & Metrics ---
st.title("⚡ AP & Telangana Multi-Provider EV Network Dashboard")
st.markdown("Analyze charging coverage across Voltran, Tata Power, ChargeZone, Jio-bp, and GLIDA.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Visible Stations", len(filtered_df))
col2.metric("Voltran Hubs", len(filtered_df[filtered_df['provider'] == 'Voltran']))
col3.metric("Tata Power Stations", len(filtered_df[filtered_df['provider'] == 'Tata Power']))
col4.metric("Other Providers", len(filtered_df[~filtered_df['provider'].isin(['Voltran', 'Tata Power'])]))

# --- Interactive Map ---
st.subheader("📍 Station Map & Network Legend")

# Legend HTML
legend_html = """
<div style="margin-bottom: 10px;">
    <b>Legend:</b> 
    <span style="color:green; font-weight:bold;">🟢 Voltran</span> &nbsp;|&nbsp;
    <span style="color:blue; font-weight:bold;">🔵 Tata Power</span> &nbsp;|&nbsp;
    <span style="color:purple; font-weight:bold;">🟣 ChargeZone</span> &nbsp;|&nbsp;
    <span style="color:red; font-weight:bold;">🔴 Jio-bp pulse</span> &nbsp;|&nbsp;
    <span style="color:orange; font-weight:bold;">🟠 GLIDA</span>
</div>
"""
st.markdown(legend_html, unsafe_allow_html=True)

m = folium.Map(location=[16.5, 79.5], zoom_start=7, tiles="OpenStreetMap")

# Render Stations
for _, row in filtered_df.iterrows():
    icon_color = PROVIDER_COLORS.get(row['provider'], 'gray')
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=f"<b>{row['name']}</b><br>Provider: {row['provider']}<br>Status: {row['status']}<br>Corridor: {row['corridor']}",
        tooltip=f"{row['provider']}: {row['name']}",
        icon=folium.Icon(color=icon_color, icon="bolt", prefix="fa")
    ).add_to(m)

# Render Gap Recommendations if checked
if show_recommendations:
    rec_df = recommend_new_locations(df)
    for _, rec in rec_df.iterrows():
        folium.Marker(
            location=[rec['Target Lat'], rec['Target Lon']],
            popup=f"<b>PROPOSED LOCATION</b><br>Corridor: {rec['Corridor']}<br>Fills gap between {rec['Station A']} & {rec['Station B']} ({rec['Current Gap (km)']} km gap)",
            tooltip="⭐ Target Expansion Location",
            icon=folium.Icon(color="red", icon="star", prefix="fa")
        ).add_to(m)

st_folium(m, width=1200, height=500)

# --- Analysis Tabs ---
tab1, tab2 = st.tabs(["📏 Pairwise Distance Analysis", "🎯 Strategic Expansion Recommendations"])

with tab1:
    st.subheader("Nearest Station Distance Breakdown")
    nn_df = compute_nearest_neighbors(filtered_df)
    if not nn_df.empty:
        st.dataframe(nn_df, use_container_width=True)
    else:
        st.info("Select at least 2 stations to calculate inter-station distances.")

with tab2:
    st.subheader("High-Priority Expansion Targets")
    st.markdown("Identified major corridor gaps (>90 km) across the combined EV network:")
    rec_display = recommend_new_locations(df)
    if not rec_display.empty:
        st.dataframe(rec_display.drop(columns=['Target Lat', 'Target Lon']), use_container_width=True)
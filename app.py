import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

# --- Page Setup & Voltran Branding ---
st.set_page_config(
    page_title="Voltran EV Network Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling mirroring Voltran.in (Dark Navy #0B0F19, Electric Green #10B981)
st.markdown("""
    <style>
    .main {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    .stMetric {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .stMetric label {
        color: #94A3B8 !important;
        font-weight: 600;
    }
    .stMetric div[data-testid="stMetricValue"] {
        color: #10B981 !important;
        font-weight: 700;
    }
    .badge {
        background-color: #10B981;
        color: #000000;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Distance Calculation (Haversine Formula) ---
def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0 # Radius of earth in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * r * asin(sqrt(a))

# --- Comprehensive Voltran + Partner Dataset ---
@st.cache_data
def load_data():
    return pd.DataFrame([
        # Voltran Official Hubs
        {"name": "Voltran - Suryapet 2 Hub", "provider": "Voltran", "status": "Operational", "lat": 17.1438, "lon": 79.6238, "corridor": "NH65 (Hyd-Vja)", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food | 🚻 Restroom"},
        {"name": "Voltran - Shamshabad Hub", "provider": "Voltran", "status": "Operational", "lat": 17.2543, "lon": 78.4312, "corridor": "NH44 / ORR", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Nizamabad Hub", "provider": "Voltran", "status": "Operational", "lat": 18.6725, "lon": 78.0941, "corridor": "NH44 North", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🅿️ Parking | 🚻 Restroom"},
        {"name": "Voltran - Aziz Nagar Hub", "provider": "Voltran", "status": "Coming Soon", "lat": 17.3481, "lon": 78.2519, "corridor": "NH65 West", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food | 🚻 Restroom"},
        {"name": "Voltran - Tirupati Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 13.6288, "lon": 79.4192, "corridor": "NH71 / Rayalaseema", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Srikakulam Hub", "provider": "Voltran", "status": "Operational", "lat": 18.2969, "lon": 83.8968, "corridor": "NH16 North Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food | 🚻 Restroom"},
        {"name": "Voltran - Rajahmundry Hub", "provider": "Voltran", "status": "Operational", "lat": 17.0005, "lon": 81.7800, "corridor": "NH16 Mid Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🅿️ Parking | 🍔 Food"},
        {"name": "Voltran - Ongole Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 15.5057, "lon": 80.0499, "corridor": "NH16 South Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Nellore Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 14.4426, "lon": 79.9865, "corridor": "NH16 South Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🍔 Food"},
        {"name": "Voltran - Mydukur Charge Hub", "provider": "Voltran", "status": "Operational", "lat": 14.7833, "lon": 78.6000, "corridor": "NH40 (Kurnool-Kadapa)", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍽️ Restaurant | 🚻 Restroom"},
        {"name": "Voltran - Beechupalli Hub", "provider": "Voltran", "status": "Operational", "lat": 16.1423, "lon": 77.9256, "corridor": "NH44 South", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food | 🚻 Restroom"},
        {"name": "Voltran - Anantapur Hub", "provider": "Voltran", "status": "Operational", "lat": 14.6819, "lon": 77.6006, "corridor": "NH44 South", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🍔 Food"},
        {"name": "Voltran - Madhapur Hub (Hyd)", "provider": "Voltran", "status": "Operational", "lat": 17.4461, "lon": 78.3983, "corridor": "Hyderabad Urban", "kw": "60kW DC (6 Guns)", "amenities": "⚡ 24/7 | ☕ Cafe | 📶 Wi-Fi"},
        
        # Partner / Competitor Infrastructure
        {"name": "Tata Power - Somajiguda", "provider": "Tata Power", "status": "Operational", "lat": 17.4328, "lon": 78.4583, "corridor": "Hyderabad Urban", "kw": "30kW DC", "amenities": "⚡ Standard Fast Charge"},
        {"name": "Tata Power - Tadepalle (Vja)", "provider": "Tata Power", "status": "Operational", "lat": 16.4821, "lon": 80.6012, "corridor": "NH16 Mid Coast", "kw": "50kW DC", "amenities": "⚡ Fast Charge"},
        {"name": "ChargeZone - Medak NH44", "provider": "ChargeZone", "status": "Operational", "lat": 17.8420, "lon": 78.4610, "corridor": "NH44 North", "kw": "60kW DC", "amenities": "⚡ Highway Hub"},
        {"name": "Jio-bp pulse - Tanguturu", "provider": "Jio-bp pulse", "status": "Operational", "lat": 15.3420, "lon": 80.0210, "corridor": "NH16 South Coast", "kw": "60kW DC", "amenities": "⚡ Fuel Station Hub"}
    ])

df = load_data()

PROVIDER_COLORS = {
    "Voltran": "green",
    "Tata Power": "blue",
    "ChargeZone": "purple",
    "Jio-bp pulse": "red"
}

# --- Sidebar Configuration ---
st.sidebar.image("https://www.voltran.in/assets/img/logo.png", width=180)
st.sidebar.markdown("---")

st.sidebar.title("🎛️ Control Panel")

# Map Theme Selector
map_theme = st.sidebar.selectbox(
    "Map Visual Style:",
    options=["Dark Canvas (CartoDB Dark)", "Light / Clean (CartoDB Voyager)", "OpenStreetMap"],
    index=0
)

# Search Filter
search_query = st.sidebar.text_input("🔎 Search Station or City:", "")

# Provider Filter
selected_providers = st.sidebar.multiselect(
    "Filter Networks:",
    options=list(PROVIDER_COLORS.keys()),
    default=list(PROVIDER_COLORS.keys())
)

show_gaps = st.sidebar.checkbox("Highlight Network Expansion Gaps (>90 km)", value=True)

# Apply Filters
filtered_df = df[df['provider'].isin(selected_providers)]
if search_query:
    filtered_df = filtered_df[
        filtered_df['name'].str.contains(search_query, case=False) | 
        filtered_df['corridor'].str.contains(search_query, case=False)
    ]

# --- Main Header ---
st.title("⚡ VOLTRAN EV Charging Network Dashboard")
st.markdown("Real-time coverage analytics, inter-hub distance analysis, and AI location planner for AP & Telangana.")

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Active Voltran Hubs", len(df[df['provider'] == 'Voltran']))
m2.metric("Total Tracked Stations", len(filtered_df))
m3.metric("Fast Chargers Available", f"{len(df[df['provider'] == 'Voltran']) * 4}+ Guns")
m4.metric("Network Coverage", "AP & Telangana")

# --- Interactive Map ---
st.subheader("📍 Interactive EV Infrastructure Map")

# Map Tile Logic
tile_provider = "CartoDB dark_matter"
if "Voyager" in map_theme:
    tile_provider = "CartoDB voyager"
elif "OpenStreetMap" in map_theme:
    tile_provider = "OpenStreetMap"

m = folium.Map(location=[16.5, 79.5], zoom_start=7, tiles=tile_provider)

# Plot Stations
for _, row in filtered_df.iterrows():
    icon_color = PROVIDER_COLORS.get(row['provider'], 'gray')
    
    popup_content = f"""
    <div style='font-family: Arial, sans-serif; width: 200px;'>
        <h4 style='margin-bottom: 5px; color: #10B981;'>{row['name']}</h4>
        <b>Network:</b> {row['provider']}<br>
        <b>Capacity:</b> {row['kw']}<br>
        <b>Corridor:</b> {row['corridor']}<br>
        <hr style='margin: 8px 0;'>
        <small>{row['amenities']}</small>
    </div>
    """
    
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(popup_content, max_width=250),
        tooltip=f"{row['provider']}: {row['name']}",
        icon=folium.Icon(color=icon_color, icon="bolt", prefix="fa")
    ).add_to(m)

# Highlight Gap Recommendations
if show_gaps:
    # Midpoint Gap Algorithm
    op_voltran = df[df['provider'] == 'Voltran'].reset_index(drop=True)
    for i in range(len(op_voltran)):
        for j in range(i + 1, len(op_voltran)):
            s1 = op_voltran.iloc[i]
            s2 = op_voltran.iloc[j]
            dist = haversine(s1['lat'], s1['lon'], s2['lat'], s2['lon'])
            
            if 90 <= dist <= 220 and s1['corridor'] == s2['corridor']:
                mid_lat = (s1['lat'] + s2['lat']) / 2
                mid_lon = (s1['lon'] + s2['lon']) / 2
                
                folium.Marker(
                    location=[mid_lat, mid_lon],
                    popup=f"<b>TARGET EXPANSION SITE</b><br>Fills {round(dist,1)} km gap between {s1['name']} & {s2['name']}",
                    tooltip="⭐ Recommended New Hub Location",
                    icon=folium.Icon(color="red", icon="star", prefix="fa")
                ).add_to(m)

st_folium(m, width=1300, height=520)

# --- Dynamic Distance & Route Calculator ---
st.markdown("---")
st.subheader("🛣️ Point-to-Point Distance & Charging Time Estimator")

c1, c2, c3 = st.columns(3)

station_list = df['name'].tolist()
start_station = c1.selectbox("Select Origin Hub:", station_list, index=0)
end_station = c2.selectbox("Select Destination Hub:", station_list, index=12)

if start_station and end_station and start_station != end_station:
    s_row = df[df['name'] == start_station].iloc[0]
    e_row = df[df['name'] == end_station].iloc[0]
    
    dist_km = round(haversine(s_row['lat'], s_row['lon'], e_row['lat'], e_row['lon']), 1)
    est_drive_min = int((dist_km / 60) * 60) # Avg 60 km/h
    est_charge_min = 35 # Avg 10-80% on 60kW DC fast charger
    
    c3.markdown(f"### 📏 **{dist_km} km**")
    c3.caption(f"Estimated Drive: ~{est_drive_min} mins | Est. 60kW Fast Charge: ~{est_charge_min} mins")

# Data Table View
with st.expander("📊 View Complete Hub Directory & Raw Coordinates"):
    st.dataframe(filtered_df[['name', 'provider', 'corridor', 'kw', 'amenities', 'status', 'lat', 'lon']], use_container_width=True)

import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

# --- Page Setup & Theme Branding ---
st.set_page_config(
    page_title="South India EV Charging Network Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Navy #0B0F19, Voltran Electric Green #10B981, Glassmorphic Cards)
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

# --- Verified Official Voltran Network Directory ---
@st.cache_data
def load_verified_voltran_data():
    return pd.DataFrame([
        # Telangana Official Voltran Hubs
        {"name": "Voltran - Madhapur Charge Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.44610, "lon": 78.39830, "corridor": "Hyderabad Urban", "kw": "60kW DC (6 Guns)", "amenities": "⚡ 24/7 | ☕ Cafe | 📶 Wi-Fi"},
        {"name": "Voltran - Suryapet Hub (NH65)", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.14380, "lon": 79.62380, "corridor": "NH65 (Hyd-Vja)", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food | 🚻 Restroom"},
        {"name": "Voltran - Suryapet 2 Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.15100, "lon": 79.63500, "corridor": "NH65 (Hyd-Vja)", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food Court | 🚻 Restroom"},
        {"name": "Voltran - Shamshabad Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.25430, "lon": 78.43120, "corridor": "NH44 / ORR", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Nizamabad Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 18.67250, "lon": 78.09410, "corridor": "NH44 North", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🅿️ Parking | 🚻 Restroom"},
        {"name": "Voltran - Beechupalli Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 16.14230, "lon": 77.92560, "corridor": "NH44 South", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food | 🚻 Restroom"},
        {"name": "Voltran - Miryalaguda Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 16.87600, "lon": 79.56300, "corridor": "Miryalaguda Bypass", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food | 🚻 Restroom"},
        {"name": "Voltran - Nallagandla Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.48510, "lon": 78.30900, "corridor": "Hyderabad West", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🅿️ Parking"},
        {"name": "Voltran - Aushapur Hub", "provider": "Voltran", "state": "Telangana", "status": "Coming Soon", "lat": 17.34810, "lon": 78.25190, "corridor": "Warangal Highway", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food"},

        # Andhra Pradesh Official Voltran Hubs
        {"name": "Voltran - Tirupati Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 13.62880, "lon": 79.41920, "corridor": "NH71 / Rayalaseema", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Srikakulam Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 18.29690, "lon": 83.89680, "corridor": "NH16 North Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food | 🚻 Restroom"},
        {"name": "Voltran - Rajahmundry Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 17.00050, "lon": 81.78000, "corridor": "NH16 Mid Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🅿️ Parking | 🍔 Food"},
        {"name": "Voltran - Ongole Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 15.50570, "lon": 80.04990, "corridor": "NH16 South Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Nellore Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 14.44260, "lon": 79.98650, "corridor": "NH16 South Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🍔 Food"},
        {"name": "Voltran - Mydukur Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 14.78330, "lon": 78.60000, "corridor": "NH40 (Kurnool-Kadapa)", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍽️ Restaurant | 🚻 Restroom"},
        {"name": "Voltran - Kakinada Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.98910, "lon": 82.24750, "corridor": "Kakinada Port Belt", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🍔 Food"},
        {"name": "Voltran - Gannavaram Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.53880, "lon": 80.79610, "corridor": "NH16 Vijayawada Airport", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Gollapudi Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.54120, "lon": 80.57800, "corridor": "NH65 Vijayawada", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi"},
        {"name": "Voltran - Amaravati Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.35200, "lon": 80.52830, "corridor": "Capital Region / NH65", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Anantapur Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 14.68190, "lon": 77.60060, "corridor": "NH44 South", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🍔 Food"},
        {"name": "Voltran - Machilipatnam Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.18120, "lon": 81.13200, "corridor": "Machilipatnam Highway", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi"}
    ])

# --- Fetch Live Geotagged Stations for Other CPOs (Open Charge Map API) ---
@st.cache_data(ttl=3600)
def fetch_live_partner_stations():
    # Regional centers for South/West India: Bengaluru, Chennai, Mumbai/Pune, Hyderabad
    centers = [
        {"lat": 12.9716, "lon": 77.5946, "state": "Karnataka"},
        {"lat": 13.0827, "lon": 80.2707, "state": "Tamil Nadu"},
        {"lat": 18.5204, "lon": 73.8567, "state": "Maharashtra"},
        {"lat": 17.3850, "lon": 78.4867, "state": "Telangana"}
    ]
    
    url = "https://api.openchargemap.io/v3/poi/"
    all_stations = []
    
    headers = {"User-Agent": "VoltranEVAnalytics/1.0"}
    
    for c in centers:
        params = {
            "output": "json",
            "countrycode": "IN",
            "latitude": c["lat"],
            "longitude": c["lon"],
            "distance": 350,
            "distanceunit": "KM",
            "maxresults": 60,
            "compact": "true",
            "key": "8647c0b0-27bb-4e2a-a2db-6447cbe60144"
        }
        try:
            res = requests.get(url, params=params, headers=headers, timeout=4)
            if res.status_code == 200:
                for item in res.json():
                    addr = item.get("AddressInfo", {})
                    operator = item.get("OperatorInfo", {}).get("Title", "")
                    
                    provider = "Other CPO"
                    if "Tata" in operator or "Tata" in addr.get("Title", ""): provider = "Tata Power"
                    elif "Zeon" in operator or "Zeon" in addr.get("Title", ""): provider = "Zeon Charging"
                    elif "ChargeZone" in operator: provider = "ChargeZone"
                    elif "Jio" in operator or "bp" in operator: provider = "Jio-bp pulse"
                    elif "Statiq" in operator: provider = "Statiq"
                    elif "Ather" in operator: provider = "Ather Grid"
                    elif "Fortum" in operator or "GLIDA" in operator: provider = "GLIDA"
                    
                    if provider != "Other CPO" and addr.get("Latitude") and addr.get("Longitude"):
                        all_stations.append({
                            "name": f"{provider} - {addr.get('Title', 'Charge Point')}",
                            "provider": provider,
                            "state": addr.get("StateOrProvince") if addr.get("StateOrProvince") in ["Karnataka", "Maharashtra", "Tamil Nadu", "Andhra Pradesh", "Telangana"] else c["state"],
                            "status": "Operational",
                            "lat": addr.get("Latitude"),
                            "lon": addr.get("Longitude"),
                            "corridor": addr.get("AddressLine1", "Highway Transit Axis"),
                            "kw": "DC Fast Charger",
                            "amenities": "⚡ Fast Charging | 24/7 Access"
                        })
        except Exception:
            continue
            
    if all_stations:
        return pd.DataFrame(all_stations).drop_duplicates(subset=['lat', 'lon'])
    return pd.DataFrame()

# --- Load & Combine Datasets ---
voltran_df = load_verified_voltran_data()
partner_df = fetch_live_partner_stations()

if not partner_df.empty:
    df = pd.concat([voltran_df, partner_df], ignore_index=True)
else:
    df = voltran_df

# --- Provider Color Palette ---
PROVIDER_COLORS = {
    "Voltran": "green",
    "Tata Power": "blue",
    "Zeon Charging": "cadetblue",
    "ChargeZone": "purple",
    "Statiq": "darkgreen",
    "Jio-bp pulse": "red",
    "GLIDA": "orange",
    "Ather Grid": "darkred",
    "Other CPO": "gray"
}

# --- Sidebar Controls ---
st.sidebar.image("https://www.voltran.in/assets/img/logo.png", width=180)
st.sidebar.markdown("---")
st.sidebar.title("🎛️ Regional Filters")

# State Multi-Select
available_states = ["Andhra Pradesh", "Telangana", "Karnataka", "Maharashtra", "Tamil Nadu"]
selected_states = st.sidebar.multiselect("Select States:", options=available_states, default=available_states)

# Provider Multi-Select
available_providers = list(df['provider'].unique())
selected_providers = st.sidebar.multiselect("Select EV Networks:", options=available_providers, default=available_providers)

# Map Style Selector
map_theme = st.sidebar.selectbox(
    "Map Visual Style:",
    options=["Dark Canvas (CartoDB Dark)", "Light / Clean (CartoDB Voyager)", "OpenStreetMap"],
    index=0
)

show_gaps = st.sidebar.checkbox("Highlight Highway Network Gaps (>100 km)", value=True)

# Apply Filters
filtered_df = df[(df['state'].isin(selected_states)) & (df['provider'].isin(selected_providers))].reset_index(drop=True)

# --- Header & High Level Metrics ---
st.title("⚡ South India EV Infrastructure Dashboard")
st.markdown("Coverage map tracking verified **Voltran** hubs alongside **Tata Power, Zeon, Statiq, ChargeZone, Jio-bp, GLIDA, and Ather** across 5 states.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Active Stations On Map", len(filtered_df))
m2.metric("Voltran Active Hubs", len(filtered_df[filtered_df['provider'] == 'Voltran']))
m3.metric("States Filtered", len(selected_states))
m4.metric("Estimated Fast Guns", f"{len(filtered_df) * 3}+ Guns")

# --- Interactive Map ---
st.subheader("📍 Multi-State EV Charging Network Map")

# Map Tile Selection
tile_provider = "CartoDB dark_matter"
if "Voyager" in map_theme:
    tile_provider = "CartoDB voyager"
elif "OpenStreetMap" in map_theme:
    tile_provider = "OpenStreetMap"

# Centering map on Southern Peninsula
m = folium.Map(location=[15.2, 77.5], zoom_start=6, tiles=tile_provider)

# Render Markers
for _, row in filtered_df.iterrows():
    icon_color = PROVIDER_COLORS.get(row['provider'], 'gray')
    
    popup_content = f"""
    <div style='font-family: Arial, sans-serif; width: 220px;'>
        <h4 style='margin-bottom: 5px; color: #10B981;'>{row['name']}</h4>
        <b>Network:</b> {row['provider']}<br>
        <b>State:</b> {row['state']}<br>
        <b>Capacity:</b> {row['kw']}<br>
        <b>Location/Corridor:</b> {row['corridor']}<br>
        <hr style='margin: 8px 0;'>
        <small>{row['amenities']}</small>
    </div>
    """
    
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(popup_content, max_width=260),
        tooltip=f"{row['provider']}: {row['name']} ({row['state']})",
        icon=folium.Icon(color=icon_color, icon="bolt", prefix="fa")
    ).add_to(m)

# Highlight Gap Fill Recommendations
if show_gaps and len(filtered_df) > 1:
    op_df = filtered_df[filtered_df['status'] == 'Operational'].reset_index(drop=True)
    for i in range(min(len(op_df), 40)):
        for j in range(i + 1, min(len(op_df), 40)):
            s1 = op_df.iloc[i]
            s2 = op_df.iloc[j]
            dist = haversine(s1['lat'], s1['lon'], s2['lat'], s2['lon'])
            
            # Show gaps on same corridor between 100km and 220km
            if 100 <= dist <= 220 and s1['corridor'] == s2['corridor']:
                mid_lat = (s1['lat'] + s2['lat']) / 2
                mid_lon = (s1['lon'] + s2['lon']) / 2
                
                folium.Marker(
                    location=[mid_lat, mid_lon],
                    popup=f"<b>PROPOSED EXPANSION TARGET</b><br>Corridor: {s1['corridor']}<br>Gap: {round(dist,1)} km between {s1['name']} & {s2['name']}",
                    tooltip="⭐ Recommended New Station Location",
                    icon=folium.Icon(color="red", icon="star", prefix="fa")
                ).add_to(m)

st_folium(m, width=1300, height=550)

# --- Point-to-Point Highway Route & Distance Estimator ---
st.markdown("---")
st.subheader("🛣️ Inter-State Highway Distance & Charging Estimator")

c1, c2, c3 = st.columns(3)

station_list = filtered_df['name'].tolist()
if len(station_list) >= 2:
    start_station = c1.selectbox("Select Origin Hub:", station_list, index=0)
    end_station = c2.selectbox("Select Destination Hub:", station_list, index=min(4, len(station_list)-1))

    if start_station and end_station and start_station != end_station:
        s_row = filtered_df[filtered_df['name'] == start_station].iloc[0]
        e_row = filtered_df[filtered_df['name'] == end_station].iloc[0]
        
        dist_km = round(haversine(s_row['lat'], s_row['lon'], e_row['lat'], e_row['lon']), 1)
        est_drive_min = int((dist_km / 65) * 60) # Avg highway speed 65 km/h
        est_charge_stops = int(dist_km // 220) # Stopping every ~220 km
        
        c3.markdown(f"### 📏 **{dist_km} km**")
        c3.caption(f"Estimated Drive Time: ~{est_drive_min // 60}h {est_drive_min % 60}m | Suggested Fast Charging Stops: {est_charge_stops}")

# Directory View
with st.expander("📊 Explore Complete Multi-State Charging Station Directory"):
    st.dataframe(filtered_df[['name', 'provider', 'state', 'corridor', 'kw', 'amenities', 'status', 'lat', 'lon']], use_container_width=True)

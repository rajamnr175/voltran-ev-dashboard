import streamlit as st
import pandas as pd
import numpy as np
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

# --- Comprehensive 5-State Charging Station Dataset ---
@st.cache_data
def load_data():
    return pd.DataFrame([
        # --- TELANGANA & ANDHRA PRADESH (Voltran + Partners) ---
        {"name": "Voltran - Suryapet 2 Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.1438, "lon": 79.6238, "corridor": "NH65 (Hyd-Vja)", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Cafeteria | 🚻 Restroom"},
        {"name": "Voltran - Shamshabad Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.2543, "lon": 78.4312, "corridor": "NH44 / ORR", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Nizamabad Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 18.6725, "lon": 78.0941, "corridor": "NH44 North", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🅿️ Parking | 🚻 Restroom"},
        {"name": "Voltran - Madhapur Hub (Hyd)", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.4461, "lon": 78.3983, "corridor": "Hyderabad Urban", "kw": "60kW DC (6 Guns)", "amenities": "⚡ 24/7 | ☕ Cafe | 📶 Wi-Fi"},
        {"name": "Voltran - Beechupalli Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 16.1423, "lon": 77.9256, "corridor": "NH44 South", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food | 🚻 Restroom"},
        {"name": "Voltran - Tirupati Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 13.6288, "lon": 79.4192, "corridor": "NH71 / Rayalaseema", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Srikakulam Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 18.2969, "lon": 83.8968, "corridor": "NH16 North Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food | 🚻 Restroom"},
        {"name": "Voltran - Rajahmundry Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 17.0005, "lon": 81.7800, "corridor": "NH16 Mid Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🅿️ Parking | 🍔 Food"},
        {"name": "Voltran - Ongole Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 15.5057, "lon": 80.0499, "corridor": "NH16 South Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},
        {"name": "Voltran - Nellore Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 14.4426, "lon": 79.9865, "corridor": "NH16 South Coast", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🍔 Food"},
        {"name": "Voltran - Anantapur Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 14.6819, "lon": 77.6006, "corridor": "NH44 South", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🍔 Food"},
        {"name": "Voltran - Amaravati Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.3520, "lon": 80.5283, "corridor": "Capital Region / NH65", "kw": "60kW DC", "amenities": "⚡ 24/7 | 📶 Wi-Fi | 🚻 Restroom"},

        # --- KARNATAKA ---
        {"name": "Zeon - Hosur Road (Bengaluru)", "provider": "Zeon Charging", "state": "Karnataka", "status": "Operational", "lat": 12.8920, "lon": 77.6410, "corridor": "NH44 (Blr-Tn Boundary)", "kw": "120kW Dual DC", "amenities": "⚡ Superfast | ☕ Lounge | 🚻 Restroom"},
        {"name": "Tata Power - Electronic City", "provider": "Tata Power", "state": "Karnataka", "status": "Operational", "lat": 12.8452, "lon": 77.6602, "corridor": "Bengaluru IT Corridor", "kw": "50kW DC", "amenities": "⚡ Fast Charge"},
        {"name": "Statiq - Indiranagar Mall", "provider": "Statiq", "state": "Karnataka", "status": "Operational", "lat": 12.9784, "lon": 77.6408, "corridor": "Bengaluru Central", "kw": "60kW DC", "amenities": "🛍️ Mall Parking | ☕ Cafe"},
        {"name": "Ather Grid - Hebbal Flyover", "provider": "Ather Grid", "state": "Karnataka", "status": "Operational", "lat": 13.0358, "lon": 77.5970, "corridor": "NH44 Airport Expressway", "kw": "Fast DC Grid", "amenities": "⚡ Quick Charge"},
        {"name": "Zeon - Mysuru Highway Expressway", "provider": "Zeon Charging", "state": "Karnataka", "status": "Operational", "lat": 12.4200, "lon": 76.8120, "corridor": "Blr-Mysuru Exp", "kw": "60kW DC", "amenities": "⚡ Highway Hub | 🍽️ Food Court"},
        {"name": "ChargeZone - Hubballi Bypass", "provider": "ChargeZone", "state": "Karnataka", "status": "Operational", "lat": 15.3647, "lon": 75.1240, "corridor": "NH48 (Blr-Pune)", "kw": "60kW DC", "amenities": "⚡ Highway Hub"},

        # --- MAHARASHTRA ---
        {"name": "ChargeZone - BKC Financial Hub", "provider": "ChargeZone", "state": "Maharashtra", "status": "Operational", "lat": 19.0657, "lon": 72.8686, "corridor": "Mumbai Central", "kw": "120kW Fast DC", "amenities": "⚡ Ultra Fast | 🅿️ Secure Parking"},
        {"name": "Tata Power - Vashi Sector 17", "provider": "Tata Power", "state": "Maharashtra", "status": "Operational", "lat": 19.0770, "lon": 72.9980, "corridor": "Navi Mumbai / M-P Exp", "kw": "50kW DC", "amenities": "⚡ City Fast Hub"},
        {"name": "Statiq - Expressway Food Plaza (Lonavala)", "provider": "Statiq", "state": "Maharashtra", "status": "Operational", "lat": 18.7557, "lon": 73.4091, "corridor": "Mumbai-Pune Exp", "kw": "60kW DC", "amenities": "⚡ 24/7 | 🍔 Food Court | 🚻 Restroom"},
        {"name": "GLIDA - Hinjewadi IT Park (Pune)", "provider": "GLIDA", "state": "Maharashtra", "status": "Operational", "lat": 18.5912, "lon": 73.7389, "corridor": "Pune Tech Hub", "kw": "60kW DC", "amenities": "⚡ Fast Charge"},
        {"name": "Jio-bp pulse - Kolhapur Highway", "provider": "Jio-bp pulse", "state": "Maharashtra", "status": "Operational", "lat": 16.7050, "lon": 74.2433, "corridor": "NH48 (Pune-Blr)", "kw": "60kW DC", "amenities": "⚡ 24/7 | ⛽ Fuel & Restroom"},
        {"name": "Tata Power - Nagpur Wardha Road", "provider": "Tata Power", "state": "Maharashtra", "status": "Operational", "lat": 21.1140, "lon": 79.0520, "corridor": "NH44 Central Axis", "kw": "50kW DC", "amenities": "⚡ Transit Hub"},

        # --- TAMIL NADU ---
        {"name": "Zeon - Sriperumbudur Highway", "provider": "Zeon Charging", "state": "Tamil Nadu", "status": "Operational", "lat": 12.9690, "lon": 79.9410, "corridor": "NH48 (Blr-Chennai)", "kw": "120kW Dual DC", "amenities": "⚡ Superfast | 🍔 Food Court"},
        {"name": "Tata Power - Guindy Metro Station", "provider": "Tata Power", "state": "Tamil Nadu", "status": "Operational", "lat": 13.0067, "lon": 80.2020, "corridor": "Chennai City Hub", "kw": "50kW DC", "amenities": "⚡ Transit Station"},
        {"name": "Zeon - Ulundurpet Highway Hub", "provider": "Zeon Charging", "state": "Tamil Nadu", "status": "Operational", "lat": 11.6912, "lon": 79.2900, "corridor": "NH45 (Chennai-Trichy)", "kw": "60kW DC", "amenities": "⚡ 24/7 | ☕ Coffee Day"},
        {"name": "ChargeZone - Coimbatore Avinashi Rd", "provider": "ChargeZone", "state": "Tamil Nadu", "status": "Operational", "lat": 11.0280, "lon": 77.0120, "corridor": "Coimbatore Hub", "kw": "60kW DC", "amenities": "⚡ Fast Charging"},
        {"name": "Ather Grid - Madurai Bypass", "provider": "Ather Grid", "state": "Tamil Nadu", "status": "Operational", "lat": 9.9252, "lon": 78.1198, "corridor": "NH44 South Corridor", "kw": "Fast DC Grid", "amenities": "⚡ Highway Stop"}
    ])

df = load_data()

# --- Provider Color Palette ---
PROVIDER_COLORS = {
    "Voltran": "green",
    "Tata Power": "blue",
    "Zeon Charging": "cadetblue",
    "ChargeZone": "purple",
    "Statiq": "darkgreen",
    "Jio-bp pulse": "red",
    "GLIDA": "orange",
    "Ather Grid": "darkred"
}

# --- Sidebar Controls ---
st.sidebar.image("https://www.voltran.in/assets/img/logo.png", width=180)
st.sidebar.markdown("---")
st.sidebar.title("🎛️ Regional Filters")

# State Multi-Select
available_states = list(df['state'].unique())
selected_states = st.sidebar.multiselect("Select States:", options=available_states, default=available_states)

# Provider Multi-Select
available_providers = list(PROVIDER_COLORS.keys())
selected_providers = st.sidebar.multiselect("Select EV Networks:", options=available_providers, default=available_providers)

# Map Style Selector
map_theme = st.sidebar.selectbox(
    "Map Visual Style:",
    options=["Dark Canvas (CartoDB Dark)", "Light / Clean (CartoDB Voyager)", "OpenStreetMap"],
    index=0
)

show_gaps = st.sidebar.checkbox("Highlight Highway Network Gaps (>100 km)", value=True)

# Apply Filters
filtered_df = df[(df['state'].isin(selected_states)) & (df['provider'].isin(selected_providers))]

# --- Header & High Level Metrics ---
st.title("⚡ South India EV Infrastructure Dashboard")
st.markdown("Coverage map tracking **Voltran, Tata Power, Zeon, Statiq, ChargeZone, Jio-bp, and Ather** across Southern & Western India.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Active Stations", len(filtered_df))
m2.metric("Voltran Hubs", len(filtered_df[filtered_df['provider'] == 'Voltran']))
m3.metric("States Covered", len(selected_states))
m4.metric("DC Fast Gun Count", f"{len(filtered_df) * 3}+ Guns")

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
        <b>Corridor:</b> {row['corridor']}<br>
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
    for i in range(len(op_df)):
        for j in range(i + 1, len(op_df)):
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

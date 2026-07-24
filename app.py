import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

# --- Page Setup & Theme Branding ---
st.set_page_config(
    page_title="South & West India EV Network Dashboard",
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

# --- Distance Calculation (Haversine Formula in km) ---
def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0 # Radius of earth in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * r * asin(sqrt(a))

# --- Comprehensive 5-State Dataset Across All Providers ---
@st.cache_data
def load_data():
    return pd.DataFrame([
        # ==========================================
        # 1. TELANGANA
        # ==========================================
        {"name": "Voltran - Madhapur Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.4461, "lon": 78.3983, "corridor": "Hyderabad Urban", "kw": "60kW DC", "address": "Road No. 9, Kakatiya Hills, Madhapur, Hyderabad"},
        {"name": "Voltran - Suryapet Hub (NH65)", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.1438, "lon": 79.6238, "corridor": "NH65 (Hyd-Vja)", "kw": "60kW DC", "address": "Rayangudem, Suryapet, Telangana"},
        {"name": "Voltran - Shamshabad Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.2543, "lon": 78.4312, "corridor": "NH44 / ORR", "kw": "60kW DC", "address": "Shamshabad Junction, Hyderabad"},
        {"name": "Voltran - Nizamabad Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 18.6725, "lon": 78.0941, "corridor": "NH44 North", "kw": "60kW DC", "address": "Nizamabad NH44 Bypass, Telangana"},
        {"name": "Voltran - Beechupalli Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 16.1423, "lon": 77.9256, "corridor": "NH44 South", "kw": "60kW DC", "address": "Near Beechupalli Temple, NH44"},
        {"name": "Voltran - Miryalaguda Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 16.8760, "lon": 79.5630, "corridor": "Miryalaguda Bypass", "kw": "60kW DC", "address": "Miryalaguda Bypass Rd, Telangana"},
        
        {"name": "Tata Power - Somajiguda Greenlands", "provider": "Tata Power", "state": "Telangana", "status": "Operational", "lat": 17.4328, "lon": 78.4583, "corridor": "Hyderabad Urban", "kw": "30kW DC", "address": "Begumpet Rd, Somajiguda, Hyderabad"},
        {"name": "Tata Power - LB Nagar Metro", "provider": "Tata Power", "state": "Telangana", "status": "Operational", "lat": 17.3512, "lon": 78.5521, "corridor": "NH65 Exit", "kw": "50kW DC", "address": "LB Nagar Ring Rd, Hyderabad"},
        {"name": "Tata Power - Gachibowli Stadium", "provider": "Tata Power", "state": "Telangana", "status": "Operational", "lat": 17.4435, "lon": 78.3490, "corridor": "Hyderabad Tech Hub", "kw": "60kW DC", "address": "Gachibowli, Hyderabad"},
        
        {"name": "Statiq - Courtyard Marriott (Tankbund)", "provider": "Statiq", "state": "Telangana", "status": "Operational", "lat": 17.4180, "lon": 78.4810, "corridor": "Hyderabad Central", "kw": "60kW DC", "address": "Lower Tank Bund Rd, Hyderabad"},
        {"name": "Statiq - Basheerbagh Liberty", "provider": "Statiq", "state": "Telangana", "status": "Operational", "lat": 17.3990, "lon": 78.4770, "corridor": "Hyderabad Central", "kw": "60kW DC", "address": "Beside Liberty Bus Stop, Basheerbagh"},
        
        {"name": "ChargeZone - Medak Rimmanguda", "provider": "ChargeZone", "state": "Telangana", "status": "Operational", "lat": 17.8420, "lon": 78.4610, "corridor": "NH44 North", "kw": "60kW DC", "address": "Rimmanguda NH44, Medak District"},
        {"name": "Jio-bp pulse - ORR Ghatkesar", "provider": "Jio-bp pulse", "state": "Telangana", "status": "Operational", "lat": 17.4520, "lon": 78.6810, "corridor": "Outer Ring Road", "kw": "60kW DC", "address": "Ghatkesar Toll Plaza Exit, Hyderabad"},

        # ==========================================
        # 2. ANDHRA PRADESH
        # ==========================================
        {"name": "Voltran - Tirupati Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 13.6288, "lon": 79.4192, "corridor": "NH71 / Rayalaseema", "kw": "60kW DC", "address": "Tirumala Bypass Rd, Srinivasa Nagar, Tirupati"},
        {"name": "Voltran - Srikakulam Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 18.2969, "lon": 83.8968, "corridor": "NH16 North Coast", "kw": "60kW DC", "address": "NH16 Service Rd, Kushalapuram, Srikakulam"},
        {"name": "Voltran - Rajahmundry Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 17.0005, "lon": 81.7800, "corridor": "NH16 Mid Coast", "kw": "60kW DC", "address": "Samalkota Rd Junction, Rajanagaram"},
        {"name": "Voltran - Ongole Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 15.5057, "lon": 80.0499, "corridor": "NH16 South Coast", "kw": "60kW DC", "address": "Mukthinutala Padu Rural, Ongole"},
        {"name": "Voltran - Nellore Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "state_name": "Andhra Pradesh", "status": "Operational", "lat": 14.4426, "lon": 79.9865, "corridor": "NH16 South Coast", "kw": "60kW DC", "address": "Chowtapalem, Kanupur Bit-II, Nellore"},
        {"name": "Voltran - Mydukur Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 14.7833, "lon": 78.6000, "corridor": "NH40 Rayalaseema", "kw": "60kW DC", "address": "Mydukur Bypass Rd, Bhumayapalle"},
        {"name": "Voltran - Anantapur Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 14.6819, "lon": 77.6006, "corridor": "NH44 South", "kw": "60kW DC", "address": "Rudrampeta NH44 Bypass, Anantapur"},
        
        {"name": "Tata Power - Tadepalle (Vijayawada)", "provider": "Tata Power", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.4821, "lon": 80.6012, "corridor": "NH16 Mid Coast", "kw": "50kW DC", "address": "Tadepalle Bypass, Vijayawada"},
        {"name": "Tata Power - Vempadu (Visakhapatnam)", "provider": "Tata Power", "state": "Andhra Pradesh", "status": "Operational", "lat": 17.5510, "lon": 82.8800, "corridor": "NH16 North Coast", "kw": "60kW DC", "address": "Vempadu Highway Plaza, Vizag"},
        {"name": "Jio-bp pulse - Tanguturu (Ongole)", "provider": "Jio-bp pulse", "state": "Andhra Pradesh", "status": "Operational", "lat": 15.3420, "lon": 80.0210, "corridor": "NH16 South Coast", "kw": "60kW DC", "address": "Tanguturu Toll Plaza NH16"},

        # ==========================================
        # 3. KARNATAKA
        # ==========================================
        {"name": "Zeon - Hosur Road (Bengaluru)", "provider": "Zeon Charging", "state": "Karnataka", "status": "Operational", "lat": 12.8920, "lon": 77.6410, "corridor": "NH44 (Blr-TN Border)", "kw": "120kW Dual DC", "address": "Hosur Main Rd, Bommanahalli, Bengaluru"},
        {"name": "Zeon - Mysuru Expressway Hub", "provider": "Zeon Charging", "state": "Karnataka", "status": "Operational", "lat": 12.4200, "lon": 76.8120, "corridor": "Blr-Mysuru Exp", "kw": "60kW DC", "address": "Bidadi Plaza, Mysuru Highway"},
        
        {"name": "Tata Power - Electronic City Phase 1", "provider": "Tata Power", "state": "Karnataka", "status": "Operational", "lat": 12.8452, "lon": 77.6602, "corridor": "Bengaluru IT Belt", "kw": "50kW DC", "address": "Electronic City, Hosur Rd, Bengaluru"},
        {"name": "Tata Power - Kasturba Road", "provider": "Tata Power", "state": "Karnataka", "status": "Operational", "lat": 12.9720, "lon": 77.5930, "corridor": "Bengaluru Central", "kw": "60kW DC", "address": "Kasturba Rd, Opp UB City, Bengaluru"},
        
        {"name": "Statiq - UB City (JW Marriott)", "provider": "Statiq", "state": "Karnataka", "status": "Operational", "lat": 12.9712, "lon": 77.5955, "corridor": "Bengaluru Central", "kw": "60kW DC", "address": "Vittal Mallya Rd, Ashok Nagar, Bengaluru"},
        {"name": "Statiq - Indiranagar Mall", "provider": "Statiq", "state": "Karnataka", "status": "Operational", "lat": 12.9784, "lon": 77.6408, "corridor": "Bengaluru Central", "kw": "60kW DC", "address": "100 Feet Rd, Indiranagar, Bengaluru"},
        
        {"name": "Ather Grid - Hebbal Expressway", "provider": "Ather Grid", "state": "Karnataka", "status": "Operational", "lat": 13.0358, "lon": 77.5970, "corridor": "NH44 Airport Line", "kw": "Fast DC Grid", "address": "Hebbal Flyover Junction, Bengaluru"},
        {"name": "ChargeZone - Hubballi Bypass", "provider": "ChargeZone", "state": "Karnataka", "status": "Operational", "lat": 15.3647, "lon": 75.1240, "corridor": "NH48 (Blr-Pune)", "kw": "60kW DC", "address": "Hubballi NH48 Bypass, Karnataka"},

        # ==========================================
        # 4. MAHARASHTRA
        # ==========================================
        {"name": "ChargeZone - BKC Financial Center", "provider": "ChargeZone", "state": "Maharashtra", "status": "Operational", "lat": 19.0657, "lon": 72.8686, "corridor": "Mumbai Central", "kw": "120kW Fast DC", "address": "Bandra Kurla Complex, Mumbai"},
        {"name": "Tata Power - Vashi Sector 17", "provider": "Tata Power", "state": "Maharashtra", "status": "Operational", "lat": 19.0770, "lon": 72.9980, "corridor": "Navi Mumbai", "kw": "50kW DC", "address": "Sector 17, Vashi, Navi Mumbai"},
        {"name": "Statiq - Lonavala Expressway Food Plaza", "provider": "Statiq", "state": "Maharashtra", "status": "Operational", "lat": 18.7557, "lon": 73.4091, "corridor": "Mumbai-Pune Exp", "kw": "60kW DC", "address": "Mumbai-Pune Expressway, Lonavala"},
        {"name": "GLIDA - Hinjewadi IT Park", "provider": "GLIDA", "state": "Maharashtra", "status": "Operational", "lat": 18.5912, "lon": 73.7389, "corridor": "Pune Tech Corridor", "kw": "60kW DC", "address": "Phase 1, Hinjewadi, Pune"},
        {"name": "Jio-bp pulse - Kolhapur NH48", "provider": "Jio-bp pulse", "state": "Maharashtra", "status": "Operational", "lat": 16.7050, "lon": 74.2433, "corridor": "NH48 (Pune-Blr)", "kw": "60kW DC", "address": "Kolhapur Highway Plaza, NH48"},
        {"name": "Tata Power - Wardha Road (Nagpur)", "provider": "Tata Power", "state": "Maharashtra", "status": "Operational", "lat": 21.1140, "lon": 79.0520, "corridor": "NH44 Axis", "kw": "50kW DC", "address": "Wardha Rd, Near Airport, Nagpur"},

        # ==========================================
        # 5. TAMIL NADU
        # ==========================================
        {"name": "Zeon - Sriperumbudur Highway", "provider": "Zeon Charging", "state": "Tamil Nadu", "status": "Operational", "lat": 12.9690, "lon": 79.9410, "corridor": "NH48 (Blr-Chennai)", "kw": "120kW Dual DC", "address": "Sriperumbudur NH48 Plaza, Tamil Nadu"},
        {"name": "Zeon - Ulundurpet Highway Hub", "provider": "Zeon Charging", "state": "Tamil Nadu", "status": "Operational", "lat": 11.6912, "lon": 79.2900, "corridor": "NH45 (Chennai-Trichy)", "kw": "60kW DC", "address": "Ulundurpet Toll Plaza, NH45"},
        {"name": "Tata Power - Guindy Metro", "provider": "Tata Power", "state": "Tamil Nadu", "status": "Operational", "lat": 13.0067, "lon": 80.2020, "corridor": "Chennai South", "kw": "50kW DC", "address": "Guindy Metro Parking, Chennai"},
        {"name": "Statiq - Shenoy Nagar Metro", "provider": "Statiq", "state": "Tamil Nadu", "status": "Operational", "lat": 13.0780, "lon": 80.2250, "corridor": "Chennai Central", "kw": "60kW DC", "address": "Shenoy Nagar Metro Station, Chennai"},
        {"name": "ChargeZone - Avinashi Road (Coimbatore)", "provider": "ChargeZone", "state": "Tamil Nadu", "status": "Operational", "lat": 11.0280, "lon": 77.0120, "corridor": "Coimbatore Axis", "kw": "60kW DC", "address": "Avinashi Rd, Peelamedu, Coimbatore"},
        {"name": "Ather Grid - Madurai Highway Hub", "provider": "Ather Grid", "state": "Tamil Nadu", "status": "Operational", "lat": 9.9252, "lon": 78.1198, "corridor": "NH44 South", "kw": "Fast DC Grid", "address": "Madurai Ring Road Bypass, Tamil Nadu"}
    ])

df = load_data()

# --- Provider Color Palette ---
PROVIDER_COLORS = {
    "Voltran": "green",
    "Tata Power": "blue",
    "Statiq": "darkgreen",
    "Zeon Charging": "cadetblue",
    "ChargeZone": "purple",
    "Jio-bp pulse": "red",
    "GLIDA": "orange",
    "Ather Grid": "darkred"
}

# --- Distance Calculation Matrix ---
def compute_nearest_neighbors(dataset):
    if len(dataset) < 2:
        return pd.DataFrame()
    results = []
    for i, row in dataset.iterrows():
        distances = []
        for j, target in dataset.iterrows():
            if i != j:
                dist = haversine(row['lat'], row['lon'], target['lat'], target['lon'])
                distances.append((target['name'], target['provider'], target['state'], dist))
        distances.sort(key=lambda x: x[3])
        results.append({
            "Station": row['name'],
            "Provider": row['provider'],
            "State": row['state'],
            "Nearest Neighbor": distances[0][0],
            "Nearest Provider": distances[0][1],
            "Distance to Next Station (km)": round(distances[0][3], 1)
        })
    return pd.DataFrame(results)

# --- Sidebar Controls ---
st.sidebar.image("https://www.voltran.in/assets/img/logo.png", width=180)
st.sidebar.markdown("---")
st.sidebar.title("🎛️ Search & Filters")

# Search Bar
search_query = st.sidebar.text_input("🔎 Search by City, Station, or Address:", "")

# State Multi-Select
all_states = sorted(list(df['state'].unique()))
selected_states = st.sidebar.multiselect("Filter by State:", options=all_states, default=all_states)

# Provider Multi-Select
all_providers = sorted(list(PROVIDER_COLORS.keys()))
selected_providers = st.sidebar.multiselect("Filter by EV Provider:", options=all_providers, default=all_providers)

# Map Style Selector
map_theme = st.sidebar.selectbox(
    "Map Visual Theme:",
    options=["Dark Canvas (CartoDB Dark)", "Light / Clean (CartoDB Voyager)", "OpenStreetMap"],
    index=0
)

# Filtering Data
filtered_df = df[(df['state'].isin(selected_states)) & (df['provider'].isin(selected_providers))].reset_index(drop=True)

if search_query:
    filtered_df = filtered_df[
        filtered_df['name'].str.contains(search_query, case=False) | 
        filtered_df['address'].str.contains(search_query, case=False) |
        filtered_df['corridor'].str.contains(search_query, case=False)
    ].reset_index(drop=True)

# --- Header & Metrics ---
st.title("⚡ Multi-Provider EV Network Dashboard")
st.markdown("Track station locations, verify state coverage, and calculate inter-station distances across **Voltran, Tata Power, Statiq, Zeon, ChargeZone, Jio-bp, and Ather**.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Visible Stations", len(filtered_df))
m2.metric("Voltran Active Hubs", len(filtered_df[filtered_df['provider'] == 'Voltran']))
m3.metric("Tata Power Stations", len(filtered_df[filtered_df['provider'] == 'Tata Power']))
m4.metric("Statiq & Other CPOs", len(filtered_df[~filtered_df['provider'].isin(['Voltran', 'Tata Power'])]))

# --- Interactive Map ---
st.subheader("📍 Interactive EV Charging Station Map")

# Map Tile Selection
tile_provider = "CartoDB dark_matter"
if "Voyager" in map_theme:
    tile_provider = "CartoDB voyager"
elif "OpenStreetMap" in map_theme:
    tile_provider = "OpenStreetMap"

m = folium.Map(location=[15.2, 77.5], zoom_start=6, tiles=tile_provider)

for _, row in filtered_df.iterrows():
    icon_color = PROVIDER_COLORS.get(row['provider'], 'gray')
    
    popup_content = f"""
    <div style='font-family: Arial, sans-serif; width: 220px;'>
        <h4 style='margin-bottom: 5px; color: #10B981;'>{row['name']}</h4>
        <b>Provider:</b> {row['provider']}<br>
        <b>State:</b> {row['state']}<br>
        <b>Capacity:</b> {row['kw']}<br>
        <b>Address:</b> {row['address']}<br>
    </div>
    """
    
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(popup_content, max_width=250),
        tooltip=f"{row['provider']} ({row['state']}): {row['name']}",
        icon=folium.Icon(color=icon_color, icon="bolt", prefix="fa")
    ).add_to(m)

st_folium(m, width=1300, height=520)

# --- Analysis Tabs ---
tab1, tab2 = st.tabs(["📏 Distance to Next Charging Station", "📋 Full Searchable Directory"])

with tab1:
    st.subheader("Inter-Station Proximity & Next Station Distance Analysis")
    st.markdown("Calculates the exact distance (in km) from every selected station to its nearest neighboring charger.")
    nn_df = compute_nearest_neighbors(filtered_df)
    if not nn_df.empty:
        st.dataframe(nn_df, use_container_width=True)
    else:
        st.info("Select at least 2 stations to calculate distances.")

with tab2:
    st.subheader("Searchable Station Directory by State & Network")
    st.dataframe(filtered_df[['name', 'provider', 'state', 'corridor', 'kw', 'address', 'lat', 'lon']], use_container_width=True)
